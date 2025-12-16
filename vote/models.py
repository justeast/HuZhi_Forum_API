import uuid
from django.db import models
from django.conf import settings
from model_utils.models import TimeStampedModel
from vote import constants as c


class VoteBase(TimeStampedModel):
    """
    投票抽象基类
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="投票用户"
    )

    vote_type = models.SmallIntegerField(
        choices=c.VOTE_TYPE_CHOICES,
        default=c.UPVOTE,
        verbose_name="投票类型"
    )

    class Meta:
        abstract = True
        ordering = ['-created']


class QuestionVote(VoteBase):
    """
    针对问题的投票（通常是“好问题”投票）
    """
    question = models.ForeignKey(
        'question.Question',
        on_delete=models.CASCADE,
        related_name='votes',
        verbose_name="所属问题"
    )

    class Meta:
        db_table = "vote_question"
        verbose_name = "问题投票"
        verbose_name_plural = verbose_name
        unique_together = ('user', 'question')


class AnswerVote(VoteBase):
    """
    针对回答的投票（赞同/反对）
    """
    answer = models.ForeignKey(
        'answer.Answer',
        on_delete=models.CASCADE,
        related_name='votes',
        verbose_name="所属回答"
    )

    class Meta:
        db_table = "vote_answer"
        verbose_name = "回答投票"
        verbose_name_plural = verbose_name
        unique_together = ('user', 'answer')
