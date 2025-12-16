import uuid
from django.db import models
from django.conf import settings
from model_utils.models import TimeStampedModel
from chat import constants as c


class PrivateChat(TimeStampedModel):
    """
    私信会话模型
    代表两个用户之间的聊天室
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chats_as_user1',
        verbose_name="用户1(ID较小)"
    )

    user2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chats_as_user2',
        verbose_name="用户2(ID较大)"
    )

    class Meta:
        db_table = "private_chat"
        verbose_name = "私信会话"
        verbose_name_plural = verbose_name
        unique_together = ('user1', 'user2')
        # 按更新时间倒序，使最近聊天的会话排在前面
        ordering = ['-modified']

    @classmethod
    def get_or_create_chat(cls, user_a, user_b):
        """
        根据两个用户获取或创建会话：
        始终确保 ID 小的用户在 user1，ID 大的用户在 user2
        """
        # 暂时排除自己跟自己聊天的情况
        if user_a.id == user_b.id:
            raise ValueError("不能自己跟自己私信")

        # UUID 支持直接比较大小
        if user_a.id < user_b.id:
            u1, u2 = user_a, user_b
        else:
            u1, u2 = user_b, user_a

        # 查找或创建
        chat, created = cls.objects.get_or_create(user1=u1, user2=u2)
        return chat, created


class Message(TimeStampedModel):
    """
    具体的聊天消息记录
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    chat = models.ForeignKey(
        PrivateChat,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name="所属会话"
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name="发送者"
    )

    content = models.TextField(verbose_name="内容")

    is_read = models.BooleanField(default=False, verbose_name="是否已读")

    msg_type = models.SmallIntegerField(
        choices=c.MSG_TYPE_CHOICES,
        default=c.TEXT,
        verbose_name="消息类型"
    )

    class Meta:
        db_table = "chat_message"
        verbose_name = "聊天消息"
        verbose_name_plural = verbose_name
        ordering = ['created']

    def save(self, *args, **kwargs):
        # 重写 save 方法：每当发送新消息时，自动更新所属会话的 modified 时间
        # 这样会话列表就能自动把有新消息的会话顶到最前面
        super().save(*args, **kwargs)
        # 更新 PrivateChat 的 modified 字段
        self.chat.save(update_fields=['modified'])
