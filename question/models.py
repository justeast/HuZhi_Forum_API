import uuid
from django.db import models
from django.conf import settings
from model_utils.models import TimeStampedModel


class Question(TimeStampedModel):
    """
    提问模型
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    title = models.CharField(max_length=200, verbose_name="问题标题")

    # 支持 Markdown，允许为空（有些问题可能只有标题）
    content = models.TextField(
        blank=True,
        null=True,
        verbose_name="问题内容"
    )

    questioner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name="提问者"
    )

    view_count = models.PositiveIntegerField(default=0, verbose_name="浏览量")

    followers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='followed_questions',
        blank=True,  # 允许问题刚创建时没人关注
        verbose_name="关注者"
    )

    topics = models.ManyToManyField(
        'topic.Topic',
        related_name='questions',
        blank=True,  # 允许暂时不关联话题
        verbose_name="关联话题"
    )

    class Meta:
        db_table = "question"
        verbose_name = "问题"
        verbose_name_plural = verbose_name
        ordering = ['-created']

    def __str__(self):
        return self.title
