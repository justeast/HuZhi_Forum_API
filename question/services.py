from django.db import transaction
from django.db.models import BooleanField, Exists, OuterRef, Prefetch, Value
from question.models import Question
from topic.models import Topic
from question import constants as c


def build_question_list_queryset(user, queryset):
    """
    构造问题列表查询集（用于列表类接口的统一预取/排序）
    - 为 topics 预取注解 is_following，避免序列化时 N+1
    - 统一按 -modified、-created 排序
    """
    if user and getattr(user, 'is_authenticated', False):
        topic_is_following_expr = Exists(
            Topic.objects.filter(pk=OuterRef("pk"), followers=user)
        )
    else:
        topic_is_following_expr = Value(False, output_field=BooleanField())

    topics_qs = Topic.objects.annotate(is_following=topic_is_following_expr)

    return (
        queryset
        .select_related('questioner')
        .prefetch_related(Prefetch('topics', queryset=topics_qs), 'followers')
        .order_by('-modified', '-created')
    )


def create_question(user, validated_data: dict) -> Question:
    """
    创建问题
    创建后自动让作者关注该问题
    """
    topic_ids = validated_data.pop('topic_ids', [])

    with transaction.atomic():
        # 创建问题
        question = Question.objects.create(
            questioner=user,
            **validated_data
        )

        # 关联话题
        if topic_ids:
            topics = Topic.objects.filter(id__in=topic_ids)
            question.topics.set(topics)

        # 作者自动关注问题
        question.followers.add(user)

    return question


def update_question(question: Question, validated_data: dict) -> Question:
    """
    更新问题
    """
    topic_ids = validated_data.pop('topic_ids', None)

    with transaction.atomic():
        # 更新基本字段
        for key, value in validated_data.items():
            setattr(question, key, value)
        question.save()

        # 更新话题关联
        if topic_ids is not None:
            topics = Topic.objects.filter(id__in=topic_ids)
            question.topics.set(topics)

    return question


def toggle_follow_question(user, question: Question, action_type: int) -> None:
    """
    关注/取消关注问题
    """
    if action_type == c.QUESTION_FOLLOW_ACTION:
        question.followers.add(user)
    else:
        question.followers.remove(user)


def increment_view_count(question: Question) -> None:
    """
    增加问题浏览量
    """
    question.view_count += 1
    question.save(update_fields=['view_count'])
