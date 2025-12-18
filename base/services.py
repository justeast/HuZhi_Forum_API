from base.models import User


def create_user(validated_data: dict) -> User:
    """
    创建用户
    """
    # 提取密码，其余字段直接传入
    password = validated_data.pop('password')
    user = User.objects.create_user(password=password, **validated_data)
    return user
