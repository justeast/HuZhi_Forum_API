from django.db.models import Q
from django.conf import settings
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from base.models import User
from base import constants as c
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
