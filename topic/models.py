import uuid
from django.db import models
from django.conf import settings
from model_utils.models import TimeStampedModel


class Topic(TimeStampedModel):
    """
    话题/标签模型
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=50, unique=True, verbose_name="话题名称")

    introduction = models.TextField(max_length=500, blank=True, null=True, verbose_name="话题简介")

    icon = models.URLField(max_length=500, blank=True, null=True, verbose_name="话题图标URL")

    followers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='followed_topics',
        blank=True,
        verbose_name="关注者"
    )

    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_topics',
        verbose_name="创建者"
    )

    class Meta:
        db_table = "topic"
        verbose_name = "话题"
        verbose_name_plural = verbose_name
        ordering = ['-created']

    def __str__(self):
        return self.name
