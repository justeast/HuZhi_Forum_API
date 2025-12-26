from rest_framework import serializers
from comment.models import Comment
from answer.models import Answer
from vote.models import CommentVote
from vote import constants as vote_c
from base.models import User
from base.serializers import UserSimpleSerializer
from comment import constants as c
from answer import constants as answer_c
from common.exceptions import BusinessException


class CommentListSerializer(serializers.ModelSerializer):
    """
    评论列表序列化器
    """
    user = UserSimpleSerializer(read_only=True)
    reply_to = UserSimpleSerializer(read_only=True)
    user_has_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'content', 'user', 'parent', 'reply_to',
            'like_count', 'user_has_liked',
            'created'
        ]
    
    def get_user_has_liked(self, obj):
        """
        当前用户是否点赞了该评论
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return CommentVote.objects.filter(
                user=request.user,
                comment=obj,
                vote_type=vote_c.UPVOTE
            ).exists()
        return False


class CommentDetailSerializer(CommentListSerializer):
    """
    评论详情序列化器（继承列表序列化器，可扩展更多字段）
    """
    class Meta(CommentListSerializer.Meta):
        fields = CommentListSerializer.Meta.fields


class CommentCreateSerializer(serializers.ModelSerializer):
    """
    评论创建序列化器
    """
    answer_id = serializers.UUIDField(write_only=True, required=True)
    parent_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    reply_to_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = Comment
        fields = ['content', 'answer_id', 'parent_id', 'reply_to_id']
    
    def validate_answer_id(self, value):
        """
        校验回答是否存在
        """
        if not Answer.objects.filter(id=value).exists():
            raise BusinessException(code=answer_c.ANSWER_NOT_FOUND, msg=answer_c.ANSWER_NOT_FOUND_MSG)
        return value
    
    def validate(self, attrs):
        """
        校验评论数据的完整性
        """
        parent_id = attrs.get('parent_id')
        reply_to_id = attrs.get('reply_to_id')
        answer_id = attrs.get('answer_id')
        
        # 二级评论必须同时指定parent和reply_to
        if (parent_id and not reply_to_id) or (reply_to_id and not parent_id):
            raise BusinessException(code=c.INVALID_COMMENT_REPLY, msg=c.INVALID_COMMENT_REPLY_MSG)
        
        # 如果是二级评论，校验parent是否存在
        if parent_id:
            try:
                parent = Comment.objects.get(id=parent_id)
                # 校验parent必须属于同一个回答
                if str(parent.answer_id) != str(answer_id):
                    raise BusinessException(code=c.INVALID_PARENT_COMMENT, msg=c.INVALID_PARENT_COMMENT_MSG)
            except Comment.DoesNotExist:
                raise BusinessException(code=c.PARENT_COMMENT_NOT_FOUND, msg=c.PARENT_COMMENT_NOT_FOUND_MSG)
        
        # 如果指定了reply_to，校验用户是否存在
        if reply_to_id:
            if not User.objects.filter(id=reply_to_id).exists():
                raise BusinessException(code=c.REPLY_TO_USER_NOT_FOUND, msg=c.REPLY_TO_USER_NOT_FOUND_MSG)
        
        return attrs
