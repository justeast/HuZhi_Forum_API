from rest_framework import serializers
from answer.models import Answer
from question.models import Question
from question.serializers import QuestionSimpleSerializer
from vote.models import AnswerVote
from vote import constants as vote_c
from base.serializers import UserSimpleSerializer
from common.exceptions import BusinessException
from question import constants as question_c


class AnswerSimpleSerializer(serializers.ModelSerializer):
    """
    回答简单序列化器（用于问题列表中的 top_answer 字段）
    """
    respondent = UserSimpleSerializer(read_only=True)
    upvote_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    user_vote_status = serializers.SerializerMethodField()
    is_collected = serializers.SerializerMethodField()
    
    class Meta:
        model = Answer
        fields = [
            'id', 'content', 'respondent',
            'upvote_count', 'comment_count', 'user_vote_status',
            'is_collected',
        ]
    
    def get_upvote_count(self, obj):
        """
        获取赞同票数量
        """
        return AnswerVote.objects.filter(answer=obj, vote_type=vote_c.UPVOTE).count()
    
    def get_comment_count(self, obj):
        """
        获取评论数量
        """
        return obj.comments.count()
    
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
                return vote_c.CANCEL_VOTE
        return vote_c.CANCEL_VOTE
    
    def get_is_collected(self, obj):
        """
        当前用户是否已收藏该回答

        说明：在回答列表（尤其是问题详情页回答列表）场景下，推荐在 queryset 中通过 Exists annotate 注入
        is_collected 字段，以避免逐条回答触发 exists() 带来的 N+1 查询。
        """
        annotated = getattr(obj, 'is_collected', None)
        if isinstance(annotated, bool):
            return annotated

        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return False

        # 兜底逻辑：当未通过 annotate 注入 is_collected 时，回退到 exists() 判断
        return obj.collections.filter(owner=request.user).exists()


class AnswerListSerializer(AnswerSimpleSerializer):
    """
    回答列表序列化器（继承简单序列化器，新增时间字段）
    """
    class Meta(AnswerSimpleSerializer.Meta):
        fields = AnswerSimpleSerializer.Meta.fields + ['created', 'modified']


class AnswerListForQuestionSerializer(AnswerListSerializer):
    """
    问题详情页的回答列表序列化器
    补充回答“被收藏次数”（按用户去重）
    """
    collected_count = serializers.IntegerField(read_only=True)

    class Meta(AnswerListSerializer.Meta):
        fields = AnswerListSerializer.Meta.fields + ['collected_count']


class AnswerWithQuestionSerializer(AnswerListSerializer):
    """
    回答列表（携带所属问题简要信息）
    用于“我的回答”等需要展示问题标题的场景
    """
    question = QuestionSimpleSerializer(read_only=True)

    class Meta(AnswerListSerializer.Meta):
        fields = AnswerListSerializer.Meta.fields + ['question']


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
