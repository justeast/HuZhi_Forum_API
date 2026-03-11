from django.db.models import BooleanField, Count, Exists, OuterRef, Q, Value
from rest_framework import serializers
from question.models import Question
from topic.models import Topic
from vote.models import QuestionVote
from vote import constants as vote_c
from topic.serializers import TopicHoverSerializer, TopicSimpleSerializer
from base.serializers import UserSimpleSerializer
from question import constants as c
from topic import constants as topic_c
from common.exceptions import BusinessException


class QuestionSimpleSerializer(serializers.ModelSerializer):
    """
    问题简单序列化器
    用于在其他模块中展示问题基础信息（例如：回答列表展示所属问题标题）
    """

    class Meta:
        model = Question
        fields = ['id', 'title']


class QuestionListSerializer(serializers.ModelSerializer):
    """
    问题列表序列化器
    """
    questioner = UserSimpleSerializer(read_only=True)
    topics = TopicSimpleSerializer(many=True, read_only=True)
    follower_count = serializers.SerializerMethodField()
    answer_count = serializers.SerializerMethodField()
    upvote_count = serializers.SerializerMethodField()
    user_vote_status = serializers.SerializerMethodField()
    top_answer = serializers.SerializerMethodField()
    
    class Meta:
        model = Question
        fields = [
            'id', 'title', 'content', 'questioner', 
            'view_count', 'follower_count', 'answer_count',
            'upvote_count', 'user_vote_status', 'top_answer',
            'topics', 'created', 'modified'
        ]
    
    def get_follower_count(self, obj):
        """
        获取关注者数量
        """
        return obj.followers.count()
    
    def get_answer_count(self, obj):
        """
        获取回答数量
        """
        return obj.answers.count()
    
    def get_upvote_count(self, obj):
        """
        获取赞同票数量
        """
        return QuestionVote.objects.filter(question=obj, vote_type=vote_c.UPVOTE).count()
    
    def get_user_vote_status(self, obj):
        """
        获取当前用户对该问题的投票状态
        返回: 1=赞同, -1=反对, 0=未投票
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                vote = QuestionVote.objects.get(user=request.user, question=obj)
                return vote.vote_type
            except QuestionVote.DoesNotExist:
                return vote_c.CANCEL_VOTE
        return vote_c.CANCEL_VOTE
    
    def get_top_answer(self, obj):
        """
        获取该问题下最热门的一个回答（按赞同数排序）
        """
        # 这里使用局部导入，避免与 question/answer 序列化器之间形成循环依赖
        from answer.serializers import AnswerSimpleSerializer
        from collection.models import Collection

        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            is_collected_expr = Exists(
                Collection.objects.filter(owner=request.user, answers=OuterRef('pk'))
            )
        else:
            is_collected_expr = Value(False, output_field=BooleanField())

        top = obj.answers.annotate(
            upvotes=Count('votes', filter=Q(votes__vote_type=vote_c.UPVOTE)),
            # 当前用户是否已收藏该回答：用于问题列表 top_answer 的收藏按钮状态
            is_collected=is_collected_expr,
        ).order_by('-upvotes').first()
        
        if top:
            return AnswerSimpleSerializer(top, context=self.context).data
        return None


class QuestionDetailSerializer(QuestionListSerializer):
    """
    问题详情序列化器（继承列表序列化器，新增 is_following 字段）
    """
    # 仅问题详情页需要悬浮卡片展示统计信息，因此这里覆写 topics 的序列化器
    topics = TopicHoverSerializer(many=True, read_only=True)
    is_following = serializers.SerializerMethodField()
    
    class Meta(QuestionListSerializer.Meta):
        fields = QuestionListSerializer.Meta.fields + ['is_following']
    
    def get_is_following(self, obj):
        """
        当前用户是否关注该问题
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.followers.filter(id=request.user.id).exists()
        return False


class QuestionRecommendSerializer(serializers.ModelSerializer):
    """
    “写回答”场景的问题推荐序列化器
    """
    questioner = UserSimpleSerializer(read_only=True)
    topics = TopicSimpleSerializer(many=True, read_only=True)
    follower_count = serializers.IntegerField(read_only=True)
    answer_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Question
        fields = [
            'id', 'title', 'questioner', 'topics',
            'follower_count', 'answer_count', 'created'
        ]


class QuestionWriteSerializer(serializers.ModelSerializer):
    """
    问题写入序列化器（用于创建和更新）
    """
    topic_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
        write_only=True
    )
    
    class Meta:
        model = Question
        fields = ['title', 'content', 'topic_ids']
    
    def validate_topic_ids(self, value):
        """
        校验话题ID是否存在
        """
        if value:
            existing_topics = Topic.objects.filter(id__in=value)
            if existing_topics.count() != len(value):
                raise BusinessException(code=topic_c.TOPIC_NOT_FOUND, msg=topic_c.TOPIC_NOT_FOUND_MSG)
        return value


class QuestionFollowSerializer(serializers.Serializer):
    """
    问题关注操作序列化器
    """
    action = serializers.ChoiceField(
        choices=c.QUESTION_FOLLOW_ACTION_CHOICES,
        required=True
    )
