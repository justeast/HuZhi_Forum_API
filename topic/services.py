from django.db import transaction
from topic.models import Topic
from topic import constants as c


def create_topic(user, validated_data: dict) -> Topic:
    """
    创建话题
    创建后自动让创建者关注该话题
    """
    with transaction.atomic():
        # 创建话题
        topic = Topic.objects.create(
            creator=user,
            **validated_data
        )
        
        # 创建者自动关注话题
        topic.followers.add(user)
    
    return topic


def update_topic(topic: Topic, validated_data: dict) -> Topic:
    """
    更新话题（仅更新 introduction 和 icon）
    """
    for key, value in validated_data.items():
        setattr(topic, key, value)
    topic.save()
    
    return topic


def toggle_follow_topic(user, topic: Topic, action_type: int) -> None:
    """
    关注/取消关注话题
    """
    if action_type == c.TOPIC_FOLLOW_ACTION:
        topic.followers.add(user)
    else:
        topic.followers.remove(user)
