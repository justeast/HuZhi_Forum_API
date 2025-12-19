import re
import random
import string
from base import constants as c
from common.exceptions import BusinessException


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
