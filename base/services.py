from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from base.models import User, UserFollow, Notification
from base.serializers import NotificationListSerializer
from base import constants as c
from answer.models import Answer
from question.models import Question
from vote import constants as vote_c
from vote.models import QuestionVote, AnswerVote
from common.exceptions import BusinessException
from common.redis_client import get_redis_client
from common.utils import generate_verify_code


def create_user(validated_data: dict) -> User:
    """
    创建用户
    """
    # 提取密码，其余字段直接传入
    password = validated_data.pop('password')
    user = User.objects.create_user(password=password, **validated_data)
    return user


def authenticate_user(account: str, password: str) -> dict:
    """
    用户登录认证
    支持用户名或邮箱登录
    返回token和用户信息
    """
    # 根据用户名或邮箱查找用户
    user = User.objects.filter(Q(username=account) | Q(email=account)).first()
    if not user:
        raise BusinessException(code=c.USER_NOT_FOUND, msg=c.USER_NOT_FOUND_MSG)

    # 验证密码
    if not user.check_password(password):
        raise BusinessException(code=c.PASSWORD_INCORRECT, msg=c.PASSWORD_INCORRECT_MSG)

    # 生成JWT token
    refresh = RefreshToken.for_user(user)

    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'id': str(user.id),
        'username': user.username,
        'avatar': user.avatar,
    }


def logout_user(refresh_token: str) -> None:
    """
    用户登出
    将refresh token加入黑名单
    """
    try:
        token = RefreshToken(refresh_token)  # type:ignore
        token.blacklist()
    except TokenError:
        raise BusinessException(code=c.INVALID_TOKEN, msg=c.INVALID_TOKEN_MSG)


def send_pwd_reset_code(email: str) -> None:
    """
    发送密码重置验证码
    """
    # 检查用户是否存在
    user = User.objects.filter(email=email).first()
    if not user:
        raise BusinessException(code=c.USER_NOT_FOUND, msg=c.USER_NOT_FOUND_MSG)

    redis_client = get_redis_client()
    limit_key = f"{c.REDIS_KEY_PWD_RESET_LIMIT}{email}"
    code_key = f"{c.REDIS_KEY_PWD_RESET_CODE}{email}"

    # 检查发送频率限制
    if redis_client.exists(limit_key):
        raise BusinessException(code=c.CODE_SEND_TOO_FREQUENT, msg=c.CODE_SEND_TOO_FREQUENT_MSG)

    # 生成验证码
    code = generate_verify_code()

    # 发送邮件
    try:
        send_mail(
            subject='【乎知论坛】密码重置验证码',
            message=f'您的密码重置验证码是：{code}，有效期{settings.VERIFY_CODE_EXPIRE // 60}分钟，请勿泄露给他人。',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception:
        raise BusinessException(code=c.EMAIL_SEND_FAILED, msg=c.EMAIL_SEND_FAILED_MSG)

    # 存储验证码到Redis
    redis_client.setex(code_key, settings.VERIFY_CODE_EXPIRE, code)
    # 设置发送频率限制
    redis_client.setex(limit_key, settings.VERIFY_CODE_INTERVAL, "1")


def reset_password(email: str, code: str, new_password: str) -> None:
    """
    重置密码
    """
    redis_client = get_redis_client()
    code_key = f"{c.REDIS_KEY_PWD_RESET_CODE}{email}"

    # 验证验证码
    stored_code = redis_client.get(code_key)
    if not stored_code or stored_code != code:
        raise BusinessException(code=c.INVALID_VERIFY_CODE, msg=c.INVALID_VERIFY_CODE_MSG)

    # 查找用户
    user = User.objects.filter(email=email).first()
    if not user:
        raise BusinessException(code=c.USER_NOT_FOUND, msg=c.USER_NOT_FOUND_MSG)

    # 更新密码
    user.set_password(new_password)
    user.save()

    # 删除验证码
    redis_client.delete(code_key)


def change_password(user: User, old_password: str, new_password: str) -> None:
    """
    修改密码（已登录用户）
    """
    # 验证旧密码
    if not user.check_password(old_password):
        raise BusinessException(code=c.PASSWORD_INCORRECT, msg=c.PASSWORD_INCORRECT_MSG)

    # 更新密码
    user.set_password(new_password)
    user.save()


def get_user_achievements(user: User) -> dict:
    """
    统计用户个人成就
    - 获得赞同：只统计 UPVOTE（包含对问题和回答的赞同）
    - 作出：回答数量
    - 关注：被多少人关注
    """
    answer_count = Answer.objects.filter(respondent=user).count()
    follower_count = UserFollow.objects.filter(following=user).count()

    question_upvote_count = QuestionVote.objects.filter(
        vote_type=vote_c.UPVOTE,
        question__questioner=user,
    ).count()
    answer_upvote_count = AnswerVote.objects.filter(
        vote_type=vote_c.UPVOTE,
        answer__respondent=user,
    ).count()

    return {
        'agree_count': question_upvote_count + answer_upvote_count,
        'answer_count': answer_count,
        'follower_count': follower_count,
    }


def toggle_follow_user(user: User, target_user_id, action: int) -> None:
    """
    关注/取消关注用户
    :param user: 当前登录用户
    :param target_user_id: 目标用户ID（被关注/取关的人）
    :param action: 1=关注，2=取消关注
    """
    target_user = User.objects.filter(id=target_user_id).first()
    if not target_user:
        raise BusinessException(code=c.USER_NOT_FOUND, msg=c.USER_NOT_FOUND_MSG)

    if user.id == target_user.id:
        raise BusinessException(code=c.CANNOT_FOLLOW_SELF, msg=c.CANNOT_FOLLOW_SELF_MSG)

    if action == c.USER_FOLLOW_ACTION:
        _, created = UserFollow.objects.get_or_create(follower=user, following=target_user)
        if created:
            create_notification(
                recipient=target_user,
                actor=user,
                notification_type=c.NOTIFICATION_TYPE_USER_FOLLOWED,
                title='有人关注了你',
                content=f'{user.username} 关注了你',
                payload={
                    'user_id': str(user.id),
                },
            )
    else:
        UserFollow.objects.filter(follower=user, following=target_user).delete()


def get_user_card(current_user: User, target_user_id) -> dict:
    """
    获取用户卡片统计信息（用于“关于作者”卡片）
    - 包含用户基础信息、提问/回答/粉丝统计、关注态与互关态
    """
    target_user = User.objects.filter(id=target_user_id).first()
    if not target_user:
        raise BusinessException(code=c.USER_NOT_FOUND, msg=c.USER_NOT_FOUND_MSG)

    question_count = Question.objects.filter(questioner=target_user).count()
    answer_count = Answer.objects.filter(respondent=target_user).count()
    follower_count = UserFollow.objects.filter(following=target_user).count()

    # 自己查看自己的卡片时，关注态与互关态固定为 False
    if current_user.id == target_user.id:
        is_following = False
        is_mutual = False
    else:
        is_following = UserFollow.objects.filter(
            follower=current_user,
            following=target_user,
        ).exists()
        is_followed_by = UserFollow.objects.filter(
            follower=target_user,
            following=current_user,
        ).exists()
        is_mutual = is_following and is_followed_by

    return {
        'id': target_user.id,
        'username': target_user.username,
        'avatar': target_user.avatar,
        'bio': target_user.bio,
        'question_count': question_count,
        'answer_count': answer_count,
        'follower_count': follower_count,
        'is_following': is_following,
        'is_mutual': is_mutual,
    }


def create_notification(recipient: User, actor: User | None, notification_type: int, title: str, content: str, payload: dict | None = None) -> Notification | None:
    """
    创建系统通知，并在事务提交后推送到当前用户的 WebSocket 连接
    """
    if actor and recipient.id == actor.id:
        return None

    notification = Notification.objects.create(
        recipient=recipient,
        actor=actor,
        type=notification_type,
        title=title,
        content=content,
        payload=payload or {},
    )

    transaction.on_commit(lambda: push_notification(notification))
    return notification


def push_notification(notification: Notification) -> None:
    """
    推送单条系统通知
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    data = NotificationListSerializer(notification).data
    async_to_sync(channel_layer.group_send)(
        f'user_{notification.recipient_id}',
        {
            'type': 'system_notification',
            'data': data,
        },
    )


def get_user_notifications(user: User):
    """
    获取当前用户的系统通知列表
    """
    return Notification.objects.filter(recipient=user).select_related('actor').order_by('-created')


def get_user_unread_notification_count(user: User) -> int:
    """
    获取当前用户未读通知数
    """
    return Notification.objects.filter(recipient=user, is_read=False).count()


def mark_notification_read(user: User, notification_id) -> Notification:
    """
    标记单条通知已读
    """
    notification = Notification.objects.filter(id=notification_id, recipient=user).first()
    if not notification:
        raise BusinessException(code=c.NOTIFICATION_NOT_FOUND, msg=c.NOTIFICATION_NOT_FOUND_MSG)

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=['is_read', 'read_at', 'modified'])
    return notification


def mark_all_notifications_read(user: User) -> None:
    """
    标记当前用户全部通知为已读
    """
    now = timezone.now()
    Notification.objects.filter(recipient=user, is_read=False).update(
        is_read=True,
        read_at=now,
        modified=now,
    )
