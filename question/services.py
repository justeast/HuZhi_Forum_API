from datetime import timedelta
from django.db import transaction
from django.db.models import BooleanField, Case, Count, Exists, IntegerField, OuterRef, Prefetch, Q, Value, When
from django.utils import timezone
from answer.models import Answer
from base.models import UserFollow
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


def build_answer_recommend_queryset(user):
    """
    构造“写回答”场景的问题推荐查询集
    - 排除当前用户自己的问题
    - 默认排除当前用户已回答过的问题
    - 相关性优先：关注的人 > 关注的话题 > 历史活跃话题
    - 在同等相关性下，优先推荐回答更少的问题
    - 若候选集为空，则放宽“排除已回答问题”的限制，避免前端列表空白
    """
    answered_question_ids = Answer.objects.filter(respondent=user).values_list('question_id', flat=True)
    history_since = timezone.now() - timedelta(days=c.ANSWER_RECOMMEND_HISTORY_WINDOW_DAYS)
    history_topic_ids = Topic.objects.filter(
        Q(questions__questioner=user, questions__created__gte=history_since)
        | Q(questions__answers__respondent=user, questions__answers__created__gte=history_since)
    ).values_list('id', flat=True).distinct()

    if user and getattr(user, 'is_authenticated', False):
        topic_is_following_expr = Exists(
            Topic.objects.filter(pk=OuterRef("pk"), followers=user)
        )
        is_from_followed_user_expr = Exists(
            UserFollow.objects.filter(
                follower=user,
                following_id=OuterRef('questioner_id'),
            )
        )
        is_in_followed_topic_expr = Exists(
            Topic.objects.filter(
                followers=user,
                questions=OuterRef('pk'),
            )
        )
        is_in_history_topic_expr = Exists(
            Topic.objects.filter(
                id__in=history_topic_ids,
                questions=OuterRef('pk'),
            )
        )
    else:
        topic_is_following_expr = Value(False, output_field=BooleanField())
        is_from_followed_user_expr = Value(False, output_field=BooleanField())
        is_in_followed_topic_expr = Value(False, output_field=BooleanField())
        is_in_history_topic_expr = Value(False, output_field=BooleanField())

    topics_qs = Topic.objects.annotate(is_following=topic_is_following_expr)

    def build_queryset(exclude_answered=True):
        queryset = Question.objects.exclude(questioner=user)
        if exclude_answered:
            queryset = queryset.exclude(id__in=answered_question_ids)

        return (
            queryset
            .select_related('questioner')
            .prefetch_related(Prefetch('topics', queryset=topics_qs))
            .annotate(
                follower_count=Count('followers', distinct=True),
                answer_count=Count('answers', distinct=True),
                is_from_followed_user=is_from_followed_user_expr,
                is_in_followed_topic=is_in_followed_topic_expr,
                is_in_history_topic=is_in_history_topic_expr,
            ).annotate(
                relevance_score=Case(
                    When(is_from_followed_user=True, then=Value(c.ANSWER_RECOMMEND_FOLLOWED_USER_SCORE)),
                    When(is_in_followed_topic=True, then=Value(c.ANSWER_RECOMMEND_FOLLOWED_TOPIC_SCORE)),
                    When(is_in_history_topic=True, then=Value(c.ANSWER_RECOMMEND_HISTORY_TOPIC_SCORE)),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            ).order_by('-relevance_score', 'answer_count', '-follower_count', '-view_count', '-created')
        )

    queryset = build_queryset()
    if not queryset.exists():
        queryset = build_queryset(exclude_answered=False)
    return queryset


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
