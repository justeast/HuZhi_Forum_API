from django.db import transaction
from chat.models import PrivateChat, Message
from base.models import User
from chat import constants as chat_c


def get_or_create_chat(user, receiver_id):
    """
    获取或创建会话
    """
    receiver = User.objects.get(id=receiver_id)
    chat, created = PrivateChat.get_or_create_chat(user, receiver)
    return chat, created


def get_chat_messages(chat, limit=50):
    """
    获取会话的历史消息（最近N条，按时间正序）
    """
    messages = chat.messages.select_related('sender').order_by('-created')[:limit]
    # 反转使其按时间正序
    return list(reversed(messages))


def send_message(chat, sender, content, msg_type=chat_c.TEXT):
    """
    发送消息
    """
    with transaction.atomic():
        message = Message.objects.create(
            chat=chat,
            sender=sender,
            content=content,
            msg_type=msg_type
        )
    return message


def mark_messages_read(chat, user, message_ids=None):
    """
    标记消息为已读
    - 如果提供 message_ids，则标记指定消息
    - 如果不提供，则标记该会话中对方发给我的所有未读消息
    """
    with transaction.atomic():
        # 基础查询：该会话中对方发给我的未读消息
        queryset = chat.messages.filter(
            is_read=False
        ).exclude(
            sender=user
        )

        # 如果指定了消息ID，进一步过滤
        if message_ids:
            queryset = queryset.filter(id__in=message_ids)

        # 批量更新
        updated_count = queryset.update(is_read=True)

    return updated_count


def check_chat_permission(chat, user):
    """
    检查用户是否有权限访问该会话
    
    注意：虽然 common.permissions.IsChatParticipant 权限类有相同逻辑，
    但该函数用于 WebSocket Consumer 中（非 DRF 视图环境），
    需要通过 @database_sync_to_async 装饰器在异步环境中调用。
    """
    return chat.user1 == user or chat.user2 == user


def get_other_user(chat, current_user):
    """
    获取会话中的对方用户
    """
    if chat.user1 == current_user:
        return chat.user2
    else:
        return chat.user1
