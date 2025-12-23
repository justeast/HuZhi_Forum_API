from answer.models import Answer
from question.models import Question


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
    
    return answer


def update_answer(answer: Answer, validated_data: dict) -> Answer:
    """
    更新回答（仅更新 content）
    """
    for key, value in validated_data.items():
        setattr(answer, key, value)
    answer.save()
    
    return answer
