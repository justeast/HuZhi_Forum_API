import uuid
from django.db import models
from django.conf import settings
from model_utils.models import TimeStampedModel


class Comment(TimeStampedModel):
    """
    评论模型
    支持一级评论（针对回答）和二级评论（针对其他评论的回复）
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    content = models.TextField(max_length=2000, verbose_name="评论内容")

    like_count = models.PositiveIntegerField(default=0, verbose_name="点赞数")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="评论者"
    )

    answer = models.ForeignKey(
        'answer.Answer',
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="所属回答"
    )

    # 父评论自关联，patent为空 -> 一级评论；parent不为空 -> 回复(二级评论)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies',
        verbose_name="父评论"
    )

    # 冗余存储，记录该评论具体是回复给哪个用户的（方便前端显示 "A 回复 B"）
    reply_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,  # 如果被回复的人注销了，名字变空，但不删评论
        related_name='replies_received',
        verbose_name="回复给谁"
    )

    class Meta:
        db_table = "comment"
        verbose_name = "评论"
        verbose_name_plural = verbose_name
        ordering = ['created']

    def __str__(self):
        # 简略显示：某人评论了某回答
        return f"{self.user} 评论了回答： {self.answer}"
