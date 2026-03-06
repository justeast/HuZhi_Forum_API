import re
import random
import string
import uuid
from django.db.models import Func
from django.db.models import IntegerField
from base import constants as c
from base.models import User
from common.exceptions import BusinessException, ParamException


class TimestampDiffHours(Func):
    """
    计算两个时间字段的小时差（MySQL）
    生成 SQL：TIMESTAMPDIFF(HOUR, datetime1, datetime2)
    """

    function = "TIMESTAMPDIFF"
    template = "%(function)s(HOUR, %(expressions)s)"
    arity = 2
    output_field = IntegerField()


def parse_uuid_query_param(request, key: str):
    """
    解析 query string 中的 UUID 参数。

    - 参数不存在/为空：返回 None
    - 参数非合法 UUID：抛 ParamException（请求参数错误）
    """
    value = request.query_params.get(key)
    if not value:
        return None

    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError, TypeError):
        raise ParamException()


def validate_password(value: str) -> str:
    """
    密码复杂度校验：需含大小写字母和数字，长度至少8位
    """
    if not re.match(c.PASSWORD_PATTERN, value):
        raise BusinessException(code=c.PASSWORD_FORMAT_ERROR, msg=c.PASSWORD_FORMAT_ERROR_MSG)
    return value


def generate_verify_code(length: int = 6) -> str:
    """
    生成数字验证码
    """
    return ''.join(random.choices(string.digits, k=length))


def validate_username_unique(value: str, exclude_pk=None) -> str:
    """
    校验用户名唯一性
    :param value: 用户名
    :param exclude_pk: 排除的用户主键（用于修改时排除当前用户）
    """
    queryset = User.objects.all()
    if exclude_pk:
        queryset = queryset.exclude(pk=exclude_pk)
    if queryset.filter(username=value).exists():
        raise BusinessException(code=c.USERNAME_ALREADY_EXISTS, msg=c.USERNAME_ALREADY_EXISTS_MSG)
    return value


def validate_email_unique(value: str, exclude_pk=None) -> str:
    """
    校验邮箱唯一性
    :param value: 邮箱
    :param exclude_pk: 排除的用户主键（用于修改时排除当前用户）
    """
    queryset = User.objects.all()
    if exclude_pk:
        queryset = queryset.exclude(pk=exclude_pk)
    if queryset.filter(email=value).exists():
        raise BusinessException(code=c.EMAIL_ALREADY_EXISTS, msg=c.EMAIL_ALREADY_EXISTS_MSG)
    return value


def validate_phone_unique(value: str, exclude_pk=None) -> str:
    """
    校验手机号唯一性
    :param value: 手机号
    :param exclude_pk: 排除的用户主键（用于修改时排除当前用户）
    """
    if not value:
        return value

    queryset = User.objects.all()
    if exclude_pk:
        queryset = queryset.exclude(pk=exclude_pk)
    if queryset.filter(phone=value).exists():
        raise BusinessException(code=c.PHONE_ALREADY_EXISTS, msg=c.PHONE_ALREADY_EXISTS_MSG)
    return value
