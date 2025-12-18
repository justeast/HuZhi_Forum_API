from django.db.models import Q
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from base.models import User
from base import constants as c
from common.exceptions import BusinessException


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
