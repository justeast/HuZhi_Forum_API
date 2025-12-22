from rest_framework import serializers
from question.models import Question
from topic.models import Topic
from topic.serializers import TopicSimpleSerializer
from question import constants as c
from topic import constants as topic_c
from common.exceptions import BusinessException


class QuestionerSimpleSerializer(serializers.Serializer):
    """
    提问者简单信息序列化器
    """
    id = serializers.UUIDField()
    username = serializers.CharField()
    avatar = serializers.URLField()


class QuestionListSerializer(serializers.ModelSerializer):
    """
    问题列表序列化器
    """
    questioner = QuestionerSimpleSerializer(read_only=True)
    topics = TopicSimpleSerializer(many=True, read_only=True)
    follower_count = serializers.SerializerMethodField()
    answer_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Question
        fields = [
            'id', 'title', 'content', 'questioner', 
            'view_count', 'follower_count', 'answer_count',
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


class QuestionDetailSerializer(QuestionListSerializer):
    """
    问题详情序列化器（继承列表序列化器，新增 is_following 字段）
    """
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
        choices=c.FOLLOW_ACTION_CHOICES,
        required=True
    )
