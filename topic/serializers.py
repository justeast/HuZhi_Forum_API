from rest_framework import serializers
from topic.models import Topic


class TopicSimpleSerializer(serializers.ModelSerializer):
    """
    话题简单序列化器
    """
    class Meta:
        model = Topic
        fields = ['id', 'name', 'icon', 'introduction']
