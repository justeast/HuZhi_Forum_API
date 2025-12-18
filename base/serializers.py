import re
from rest_framework import serializers
from base.models import User
from base import constants as c
from common.exceptions import BusinessException


class UserRegisterReqSerializer(serializers.Serializer):
    """
    用户注册请求序列化器
    """
    username = serializers.CharField(required=True, max_length=150)
    password = serializers.CharField(write_only=True, max_length=128)
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=11)
    avatar = serializers.URLField(required=False, allow_blank=True, allow_null=True, max_length=500)
    bio = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=500)

    def validate_password(self, value):
        """
        密码复杂度校验：需含大小写字母和数字，长度至少8位
        """
        if not re.match(c.PASSWORD_PATTERN, value):
            raise BusinessException(code=c.PASSWORD_FORMAT_ERROR, msg=c.PASSWORD_FORMAT_ERROR_MSG)
        return value


class UserRegisterRespSerializer(serializers.ModelSerializer):
    """
    用户注册响应序列化器
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'avatar', 'bio']


class UserLoginReqSerializer(serializers.Serializer):
    """
    用户登录请求序列化器
    """
    account = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
