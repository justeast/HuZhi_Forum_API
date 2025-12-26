from rest_framework import serializers
from collection.models import Collection
from answer.models import Answer
from answer.serializers import AnswerListSerializer
from base.serializers import UserSimpleSerializer
from answer import constants as answer_c
from common.exceptions import BusinessException


class CollectionListSerializer(serializers.ModelSerializer):
    """
    收藏夹列表序列化器
    """
    owner = UserSimpleSerializer(read_only=True)
    answer_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Collection
        fields = [
            'id', 'title', 'description', 'is_public',
            'owner', 'answer_count', 'created', 'modified'
        ]
    
    def get_answer_count(self, obj):
        """
        获取收藏夹内回答数量
        """
        return obj.answers.count()


class CollectionDetailSerializer(CollectionListSerializer):
    """
    收藏夹详情序列化器（继承列表序列化器，字段相同）
    """
    class Meta(CollectionListSerializer.Meta):
        fields = CollectionListSerializer.Meta.fields


class CollectionWriteSerializer(serializers.ModelSerializer):
    """
    收藏夹写入序列化器（用于创建和更新）
    """
    class Meta:
        model = Collection
        fields = ['title', 'description', 'is_public']


class CollectAnswerReqSerializer(serializers.Serializer):
    """
    收藏回答请求序列化器
    """
    answer_id = serializers.UUIDField(required=True)
    
    def validate_answer_id(self, value):
        """
        校验回答是否存在
        """
        if not Answer.objects.filter(id=value).exists():
            raise BusinessException(code=answer_c.ANSWER_NOT_FOUND, msg=answer_c.ANSWER_NOT_FOUND_MSG)
        return value


class CollectAnswerRespSerializer(serializers.Serializer):
    """
    收藏回答响应序列化器
    """
    collected = serializers.BooleanField()
    answer_count = serializers.IntegerField()


class CollectionAnswerListSerializer(AnswerListSerializer):
    """
    收藏夹内回答列表序列化器（复用 AnswerListSerializer）
    """
    class Meta(AnswerListSerializer.Meta):
        fields = AnswerListSerializer.Meta.fields
