from rest_framework import serializers
from base.models import User
from common.utils import validate_password


class UserRegisterReqSerializer(serializers.Serializer):
    """
    用户注册请求序列化器
    """
    username = serializers.CharField(required=True, max_length=150)
    password = serializers.CharField(write_only=True, max_length=128, validators=[validate_password])
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=11)
    avatar = serializers.URLField(required=False, allow_blank=True, allow_null=True, max_length=500)
    bio = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=500)


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


class UserLogoutReqSerializer(serializers.Serializer):
    """
    用户登出请求序列化器
    """
    refresh = serializers.CharField(required=True)


class SendPwdResetCodeReqSerializer(serializers.Serializer):
    """
    发送密码重置验证码请求序列化器
    """
    email = serializers.EmailField(required=True)


class PwdResetReqSerializer(serializers.Serializer):
    """
    密码重置请求序列化器
    """
    email = serializers.EmailField(required=True)
    code = serializers.CharField(required=True, max_length=6)
    new_password = serializers.CharField(required=True, max_length=128, validators=[validate_password])


class PwdChangeReqSerializer(serializers.Serializer):
    """
    修改密码请求序列化器
    """
    old_password = serializers.CharField(required=True, max_length=128)
    new_password = serializers.CharField(required=True, max_length=128, validators=[validate_password])
