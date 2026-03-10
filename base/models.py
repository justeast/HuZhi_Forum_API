import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from model_utils.models import TimeStampedModel
from base import constants as c


class User(AbstractUser, TimeStampedModel):
    """
    自定义用户模型
    """
    id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)

    email = models.EmailField(unique=True,blank=False,null=False,
        error_messages={
            'unique': "该邮箱已被注册。",
            'blank': "邮箱不能为空。",
            'null': "邮箱不能为空。",
        },
        verbose_name="邮箱"
    )

    phone = models.CharField(max_length=11,unique=True,null=True,blank=True,verbose_name="手机号")

    avatar = models.URLField(max_length=500,blank=True,null=True,verbose_name="头像URL")

    cover_image = models.URLField(max_length=500, blank=True, null=True, verbose_name="封面背景图URL")

    bio = models.TextField(max_length=500,blank=True,null=True,verbose_name="个人简介")

    following = models.ManyToManyField(
        'self',
        through='UserFollow',
        symmetrical=False,
        through_fields=('follower', 'following'),
        related_name='followers',
        blank=True,
        verbose_name="关注的用户",
    )

    class Meta:
        db_table = "base_user"
        verbose_name = "用户"
        verbose_name_plural = verbose_name
        ordering = ['-created']

    def __str__(self):
        return self.username


class UserFollow(TimeStampedModel):
    """
    用户关注关系（through表）
    follower 关注 following
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='following_relations',
        verbose_name="关注者",
    )

    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='follower_relations',
        verbose_name="被关注者",
    )

    class Meta:
        db_table = "base_user_follow"
        verbose_name = "用户关注关系"
        verbose_name_plural = verbose_name
        ordering = ['-created']
        constraints = [
            models.UniqueConstraint(fields=['follower', 'following'], name='uniq_user_follow'),
            models.CheckConstraint(
                check=~models.Q(follower=models.F('following')),
                name='chk_user_follow_not_self',
            ),
        ]


class Notification(TimeStampedModel):
    """
    系统通知模型
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="接收者",
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='sent_notifications',
        null=True,
        blank=True,
        verbose_name="触发者",
    )

    type = models.SmallIntegerField(
        choices=c.NOTIFICATION_TYPE_CHOICES,
        verbose_name="通知类型",
    )

    title = models.CharField(max_length=200, verbose_name="通知标题")

    content = models.CharField(max_length=500, verbose_name="通知内容")

    payload = models.JSONField(default=dict, blank=True, verbose_name="附加数据")

    is_read = models.BooleanField(default=False, verbose_name="是否已读")

    read_at = models.DateTimeField(null=True, blank=True, verbose_name="已读时间")

    class Meta:
        db_table = "base_notification"
        verbose_name = "系统通知"
        verbose_name_plural = verbose_name
        ordering = ['-created']
