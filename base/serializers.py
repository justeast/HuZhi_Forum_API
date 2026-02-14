from rest_framework import serializers
from base.models import User
from base.models import UserFollow
from common.utils import (
    validate_password,
    validate_username_unique,
    validate_email_unique,
    validate_phone_unique,
)
from base import constants as c


class UserSimpleSerializer(serializers.Serializer):
    """
    用户简单信息序列化器（通用）
    用于在其他模块中展示用户基本信息
    """
    id = serializers.UUIDField()
    username = serializers.CharField()
    avatar = serializers.URLField()


class UserCardSerializer(serializers.ModelSerializer):
    """
    用户卡片序列化器
    用于关注/粉丝列表展示用户基础信息
    """

    class Meta:
        model = User
        fields = ['id', 'username', 'avatar', 'bio']


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

    def validate_username(self, value):
        """
        校验用户名唯一性
        """
        return validate_username_unique(value)

    def validate_email(self, value):
        """
        校验邮箱唯一性
        """
        return validate_email_unique(value)

    def validate_phone(self, value):
        """
        校验手机号唯一性
        """
        return validate_phone_unique(value)


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


class UserProfileSerializer(serializers.ModelSerializer):
    """
    用户详情序列化器（获取和修改）
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'avatar', 'cover_image', 'bio', 'created', 'modified']
        read_only_fields = ['id', 'created', 'modified']
        # 禁用ModelSerializer自动添加的UniqueValidator，使用自定义校验
        extra_kwargs = {
            'username': {'validators': []},
            'email': {'validators': []},
            'phone': {'validators': []},
        }

    def validate_username(self, value):
        """
        校验用户名唯一性（排除当前用户）
        """
        return validate_username_unique(value, exclude_pk=self.instance.pk)

    def validate_email(self, value):
        """
        校验邮箱唯一性（排除当前用户）
        """
        return validate_email_unique(value, exclude_pk=self.instance.pk)

    def validate_phone(self, value):
        """
        校验手机号唯一性（排除当前用户）
        """
        return validate_phone_unique(value, exclude_pk=self.instance.pk)


class UserAchievementsRespSerializer(serializers.Serializer):
    """
    用户个人成就响应序列化器
    """
    agree_count = serializers.IntegerField()
    answer_count = serializers.IntegerField()


class UserFollowReqSerializer(serializers.Serializer):
    """
    用户关注/取消关注请求序列化器
    """
    action = serializers.ChoiceField(choices=c.USER_FOLLOW_ACTION_CHOICES, required=True)


class UserFollowingListSerializer(serializers.ModelSerializer):
    """
    我关注的用户列表项
    """
    user = UserCardSerializer(source='following', read_only=True)
    followed_at = serializers.DateTimeField(source='created', read_only=True)
    is_mutual = serializers.BooleanField(read_only=True)

    class Meta:
        model = UserFollow
        fields = ['user', 'followed_at', 'is_mutual']


class UserFollowersListSerializer(serializers.ModelSerializer):
    """
    关注我的用户列表项
    """
    user = UserCardSerializer(source='follower', read_only=True)
    followed_at = serializers.DateTimeField(source='created', read_only=True)
    is_mutual = serializers.BooleanField(read_only=True)

    class Meta:
        model = UserFollow
        fields = ['user', 'followed_at', 'is_mutual']
