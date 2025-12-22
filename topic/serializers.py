from rest_framework import serializers
from topic.models import Topic
from topic import constants as c
from common.exceptions import BusinessException


class TopicSimpleSerializer(serializers.ModelSerializer):
    """
    话题简单序列化器
    """
    class Meta:
        model = Topic
        fields = ['id', 'name', 'icon', 'introduction']


class CreatorSimpleSerializer(serializers.Serializer):
    """
    创建者简单信息序列化器
    """
    id = serializers.UUIDField()
    username = serializers.CharField()
    avatar = serializers.URLField()


class TopicListSerializer(serializers.ModelSerializer):
    """
    话题列表序列化器
    """
    creator = CreatorSimpleSerializer(read_only=True)
    follower_count = serializers.SerializerMethodField()
    question_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Topic
        fields = [
            'id', 'name', 'introduction', 'icon', 'creator',
            'follower_count', 'question_count', 'created', 'modified'
        ]
    
    def get_follower_count(self, obj):
        """
        获取关注者数量
        """
        return obj.followers.count()
    
    def get_question_count(self, obj):
        """
        获取该话题下的问题数量
        """
        return obj.questions.count()


class TopicDetailSerializer(TopicListSerializer):
    """
    话题详情序列化器（继承列表序列化器，新增 is_following 字段）
    """
    is_following = serializers.SerializerMethodField()
    
    class Meta(TopicListSerializer.Meta):
        fields = TopicListSerializer.Meta.fields + ['is_following']
    
    def get_is_following(self, obj):
        """
        当前用户是否关注该话题
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.followers.filter(id=request.user.id).exists()
        return False


class TopicUpdateSerializer(serializers.ModelSerializer):
    """
    话题更新序列化器（不包含 name 字段，name 不可修改）
    """
    class Meta:
        model = Topic
        fields = ['introduction', 'icon']


class TopicCreateSerializer(TopicUpdateSerializer):
    """
    话题创建序列化器（继承更新序列化器，新增 name 字段）
    """
    class Meta(TopicUpdateSerializer.Meta):
        fields = TopicUpdateSerializer.Meta.fields + ['name']
    
    def validate_name(self, value):
        """
        校验话题名称唯一性
        """
        if Topic.objects.filter(name=value).exists():
            raise BusinessException(code=c.TOPIC_NAME_EXISTS, msg=c.TOPIC_NAME_EXISTS_MSG)
        return value


class TopicFollowSerializer(serializers.Serializer):
    """
    话题关注操作序列化器
    """
    action = serializers.ChoiceField(
        choices=c.TOPIC_FOLLOW_ACTION_CHOICES,
        required=True
    )
