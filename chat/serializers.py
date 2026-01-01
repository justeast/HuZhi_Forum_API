from rest_framework import serializers
from chat.models import PrivateChat, Message
from base.models import User
from base.serializers import UserSimpleSerializer
from chat import constants as chat_c
from common.exceptions import BusinessException


class MessageListSerializer(serializers.ModelSerializer):
    """
    消息列表序列化器
    """
    sender = UserSimpleSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'content', 'msg_type',
            'is_read', 'created', 'modified'
        ]


class PrivateChatListSerializer(serializers.ModelSerializer):
    """
    会话列表序列化器
    包含对方用户信息、最后一条消息、未读消息数量
    """
    other_user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PrivateChat
        fields = [
            'id', 'other_user', 'last_message',
            'unread_count', 'created', 'modified'
        ]
    
    def get_other_user(self, obj):
        """
        获取对方用户信息
        """
        request = self.context.get('request')
        if not request or not request.user:
            return None
        
        # 判断当前用户是 user1 还是 user2，返回对方
        if obj.user1 == request.user:
            other = obj.user2
        else:
            other = obj.user1
        
        return UserSimpleSerializer(other).data
    
    def get_last_message(self, obj):
        """
        获取最后一条消息
        """
        last_msg = obj.messages.order_by('-created').first()
        if last_msg:
            return {
                'content': last_msg.content,
                'msg_type': last_msg.msg_type,
                'created': last_msg.created,
                'is_mine': last_msg.sender == self.context.get('request').user if self.context.get('request') else False
            }
        return None
    
    def get_unread_count(self, obj):
        """
        获取未读消息数量（对方发给我的未读消息）
        """
        request = self.context.get('request')
        if not request or not request.user:
            return 0
        
        # 统计对方发给我的未读消息
        return obj.messages.filter(
            is_read=False
        ).exclude(
            sender=request.user
        ).count()


class PrivateChatDetailSerializer(serializers.ModelSerializer):
    """
    会话详情序列化器
    """
    user1 = UserSimpleSerializer(read_only=True)
    user2 = UserSimpleSerializer(read_only=True)
    
    class Meta:
        model = PrivateChat
        fields = ['id', 'user1', 'user2', 'created', 'modified']


class ChatCreateReqSerializer(serializers.Serializer):
    """
    创建会话请求序列化器
    """
    receiver_id = serializers.UUIDField(required=True)
    
    def validate_receiver_id(self, value):
        """
        校验接收者是否存在
        """
        if not User.objects.filter(id=value).exists():
            raise BusinessException(code=chat_c.INVALID_RECEIVER, msg=chat_c.INVALID_RECEIVER_MSG)
        
        # 检查是否是自己
        request = self.context.get('request')
        if request and request.user.id == value:
            raise BusinessException(code=chat_c.CANNOT_CHAT_WITH_SELF, msg=chat_c.CANNOT_CHAT_WITH_SELF_MSG)
        
        return value


class MarkReadReqSerializer(serializers.Serializer):
    """
    标记消息已读请求序列化器
    """
    message_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
        help_text="消息ID列表，不传或传空数组表示标记该会话所有未读消息"
    )
