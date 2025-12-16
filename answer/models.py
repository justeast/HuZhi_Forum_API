import uuid
from django.db import models
from django.conf import settings
from model_utils.models import TimeStampedModel


class Answer(TimeStampedModel):
    """
    回答模型
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # 回答通常不能为空，所以保持默认 (blank=False, null=False)
    content = models.TextField(
        verbose_name="回答内容"
    )

    question = models.ForeignKey(
        'question.Question',
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name="所属问题"
    )

    respondent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name="回答者"
    )

    class Meta:
        db_table = "answer"
        verbose_name = "回答"
        verbose_name_plural = verbose_name
        ordering = ['-created']

    def __str__(self):
        # 显示简略信息：谁回答了哪个问题
        return f"{self.respondent} 回答了: {self.question}"
