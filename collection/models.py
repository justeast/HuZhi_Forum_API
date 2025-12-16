import uuid
from django.db import models
from django.conf import settings
from model_utils.models import TimeStampedModel


class Collection(TimeStampedModel):
    """
    收藏夹模型
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    title = models.CharField(max_length=50, verbose_name="收藏夹标题")

    description = models.TextField(blank=True, null=True, verbose_name="收藏夹简介")

    is_public = models.BooleanField(default=True, verbose_name="收藏夹是否公开")

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_collections',
        verbose_name="收藏夹创建者"
    )

    answers = models.ManyToManyField(
        'answer.Answer',
        related_name='collections',
        blank=True,  # 允许收藏夹为空
        verbose_name="收藏的内容(回答)"
    )

    class Meta:
        db_table = "collection"
        verbose_name = "收藏夹"
        verbose_name_plural = verbose_name
        ordering = ['-created']

    def __str__(self):
        return f"{self.owner.username} 的收藏夹: {self.title}"
