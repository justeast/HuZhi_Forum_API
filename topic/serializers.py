from rest_framework import serializers
from topic.models import Topic
from topic import constants as c
from common.exceptions import BusinessException
from base.serializers import UserSimpleSerializer


class TopicFollowStateSerializer(serializers.ModelSerializer):
    """
    话题关注态序列化器基类
    提供 is_following 字段，供列表/嵌套场景复用
    """
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = ['id', 'name', 'icon', 'introduction', 'is_following']

    def get_is_following(self, obj):
        """
        当前用户是否关注该话题
        """
        # 优先读取视图层 queryset 中 annotate 注入的 is_following 字段：
        # - 该方式通过 Exists 在数据库层计算布尔值，避免 N+1
        # - 且不会像 prefetch followers 那样加载大量无关用户数据
        annotated = getattr(obj, 'is_following', None)
        if isinstance(annotated, bool):
            return annotated

        # 兜底逻辑：
        # 并非所有序列化场景都一定来自带注解的 queryset，例如：
        # - create/update 中手动构造 serializer 时传入的实例（不一定带注解）
        # - 其他模块/其他查询路径复用该序列化器但未做 annotate
        # - 单元测试或脚本中直接序列化模型实例
        # 此时退回到最朴素的 exists() 查询，保证字段始终可用
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return False

        return obj.followers.filter(id=request.user.id).exists()


class TopicSimpleSerializer(TopicFollowStateSerializer):
    """
    话题简单序列化器
    """
    class Meta(TopicFollowStateSerializer.Meta):
        fields = TopicFollowStateSerializer.Meta.fields


class TopicListSerializer(TopicFollowStateSerializer):
    """
    话题列表序列化器
    """
    creator = UserSimpleSerializer(read_only=True)
    follower_count = serializers.SerializerMethodField()
    question_count = serializers.SerializerMethodField()
    
    class Meta(TopicFollowStateSerializer.Meta):
        fields = TopicFollowStateSerializer.Meta.fields + [
            'creator', 'follower_count', 'question_count', 'created', 'modified'
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
    话题详情序列化器（继承列表序列化器）
    """


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
