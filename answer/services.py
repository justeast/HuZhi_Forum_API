from answer.models import Answer
from question.models import Question
from base import services as base_services
from base import constants as base_c


def create_answer(user, validated_data: dict) -> Answer:
    """
    创建回答
    """
    question_id = validated_data.pop('question_id')
    question = Question.objects.get(id=question_id)
    
    answer = Answer.objects.create(
        respondent=user,
        question=question,
        **validated_data
    )

    base_services.create_notification(
        recipient=question.questioner,
        actor=user,
        notification_type=base_c.NOTIFICATION_TYPE_QUESTION_ANSWERED,
        title='我的提问有人回答了',
        content=f'{user.username} 回答了你的问题《{question.title}》',
        payload={
            'question_id': str(question.id),
            'question_title': question.title,
            'answer_id': str(answer.id),
        },
    )

    return answer


def update_answer(answer: Answer, validated_data: dict) -> Answer:
    """
    更新回答（仅更新 content）
    """
    for key, value in validated_data.items():
        setattr(answer, key, value)
    answer.save()
    
    return answer
