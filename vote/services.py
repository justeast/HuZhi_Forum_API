from django.db import transaction
from vote.models import QuestionVote, AnswerVote
from vote import constants as c


def vote_question(user, question, vote_type):
    """
    对问题进行投票
    """
    with transaction.atomic():
        if vote_type == c.CANCEL_VOTE:
            # 取消投票
            QuestionVote.objects.filter(user=user, question=question).delete()
        else:
            # 赞同或反对，使用update_or_create确保唯一性
            QuestionVote.objects.update_or_create(
                user=user,
                question=question,
                defaults={'vote_type': vote_type}
            )


def vote_answer(user, answer, vote_type):
    """
    对回答进行投票
    """
    with transaction.atomic():
        if vote_type == c.CANCEL_VOTE:
            # 取消投票
            AnswerVote.objects.filter(user=user, answer=answer).delete()
        else:
            # 赞同或反对，使用update_or_create确保唯一性
            AnswerVote.objects.update_or_create(
                user=user,
                answer=answer,
                defaults={'vote_type': vote_type}
            )
