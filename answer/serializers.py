from rest_framework import serializers
from answer.models import Answer
from question.models import Question
from vote.models import AnswerVote
from base.serializers import UserSimpleSerializer
from common.exceptions import BusinessException
from question import constants as question_c


class AnswerListSerializer(serializers.ModelSerializer):
    """
    回答列表序列化器
    """
    respondent = UserSimpleSerializer(read_only=True)
    comment_count = serializers.SerializerMethodField()
    upvote_count = serializers.SerializerMethodField()
    user_vote_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Answer
        fields = [
            'id', 'content', 'respondent',
            'comment_count', 'upvote_count', 'user_vote_status',
            'created', 'modified'
        ]
    
    def get_comment_count(self, obj):
        """
        获取评论数量
        """
        return obj.comments.count()
    
    def get_upvote_count(self, obj):
        """
        获取赞同票数量
        """
        return AnswerVote.objects.filter(answer=obj, vote_type=1).count()
    
    def get_user_vote_status(self, obj):
        """
        获取当前用户对该回答的投票状态
        返回: 1=赞同, -1=反对, 0=未投票
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                vote = AnswerVote.objects.get(user=request.user, answer=obj)
                return vote.vote_type
            except AnswerVote.DoesNotExist:
                return 0
        return 0


class AnswerDetailSerializer(AnswerListSerializer):
    """
    回答详情序列化器（继承列表序列化器，可扩展更多字段）
    """
    class Meta(AnswerListSerializer.Meta):
        fields = AnswerListSerializer.Meta.fields


class AnswerUpdateSerializer(serializers.ModelSerializer):
    """
    回答更新序列化器（仅更新 content）
    """
    class Meta:
        model = Answer
        fields = ['content']


class AnswerCreateSerializer(AnswerUpdateSerializer):
    """
    回答创建序列化器（继承更新序列化器，新增 question_id 字段）
    """
    question_id = serializers.UUIDField(write_only=True, required=True)
    
    class Meta(AnswerUpdateSerializer.Meta):
        fields = AnswerUpdateSerializer.Meta.fields + ['question_id']
    
    def validate_question_id(self, value):
        """
        校验问题是否存在
        """
        if not Question.objects.filter(id=value).exists():
            raise BusinessException(code=question_c.QUESTION_NOT_FOUND, msg=question_c.QUESTION_NOT_FOUND_MSG)
        return value
