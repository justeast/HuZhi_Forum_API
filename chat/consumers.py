from urllib.parse import parse_qs
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from chat.models import PrivateChat
from chat import constants as chat_c
from chat import services
from chat.serializers import MessageListSerializer

User = get_user_model()


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket 聊天消费者
    """
    
    async def connect(self):
        """
        WebSocket 连接建立时调用
        """
        # 从 query_string 获取 token
        query_string = self.scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]
        
        if not token:
            await self.close(code=4001)
            return
        
        # 验证 JWT token 并获取用户
        user = await self.get_user_from_token(token)
        if not user:
            await self.close(code=4001)
            return
        
        self.user = user
        self.user_group_name = f"user_{self.user.id}"
        
        # 将用户加入自己的 group（用于接收发给自己的消息）
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        # 接受连接
        await self.accept()
    
    async def disconnect(self, close_code):
        """
        WebSocket 连接断开时调用
        """
        if hasattr(self, 'user_group_name'):
            # 离开 group
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
    
    async def receive_json(self, content):
        """
        接收客户端发送的 JSON 消息
        """
        msg_type = content.get('type')
        
        if msg_type == chat_c.WS_MSG_TYPE_SEND:
            # 处理发送消息请求
            await self.handle_send_message(content)
        else:
            # 未知消息类型
            await self.send_json({
                'type': chat_c.WS_MSG_TYPE_ERROR,
                'code': chat_c.MESSAGE_SEND_FAILED,
                'message': '未知的消息类型'
            })
    
    async def handle_send_message(self, content):
        """
        处理发送消息
        """
        chat_id = content.get('chat_id')
        receiver_id = content.get('receiver_id')
        message_content = content.get('content')
        msg_type = content.get('msg_type', chat_c.TEXT)
        
        # 验证必要字段
        if not message_content:
            await self.send_json({
                'type': chat_c.WS_MSG_TYPE_ERROR,
                'code': chat_c.MESSAGE_SEND_FAILED,
                'message': '消息内容不能为空'
            })
            return
        
        # 如果没有 chat_id，必须有 receiver_id 来创建会话
        if not chat_id and not receiver_id:
            await self.send_json({
                'type': chat_c.WS_MSG_TYPE_ERROR,
                'code': chat_c.MESSAGE_SEND_FAILED,
                'message': '必须提供 chat_id 或 receiver_id'
            })
            return
        
        try:
            # 获取或创建会话
            if chat_id:
                chat = await self.get_chat(chat_id)
                if not chat:
                    await self.send_json({
                        'type': chat_c.WS_MSG_TYPE_ERROR,
                        'code': chat_c.CHAT_NOT_FOUND,
                        'message': chat_c.CHAT_NOT_FOUND_MSG
                    })
                    return
                
                # 检查权限
                has_permission = await self.check_chat_permission(chat)
                if not has_permission:
                    await self.send_json({
                        'type': chat_c.WS_MSG_TYPE_ERROR,
                        'code': chat_c.CHAT_PERMISSION_DENIED,
                        'message': chat_c.CHAT_PERMISSION_DENIED_MSG
                    })
                    return
            else:
                # 通过 receiver_id 创建会话
                chat, created = await self.get_or_create_chat_by_receiver(receiver_id)
                if not chat:
                    await self.send_json({
                        'type': chat_c.WS_MSG_TYPE_ERROR,
                        'code': chat_c.INVALID_RECEIVER,
                        'message': chat_c.INVALID_RECEIVER_MSG
                    })
                    return
            
            # 发送消息
            message = await self.save_message(chat, message_content, msg_type)
            
            # 序列化消息
            message_data = await self.serialize_message(message)
            
            # 获取接收者
            receiver = await self.get_other_user(chat)
            
            # 构建响应数据
            response_data = {
                'type': chat_c.WS_MSG_TYPE_NEW,
                'chat_id': str(chat.id),
                'message': message_data
            }
            
            # 推送给发送者（确认）
            await self.send_json(response_data)
            
            # 推送给接收者（所有该用户的连接）
            receiver_group_name = f"user_{receiver.id}"
            await self.channel_layer.group_send(
                receiver_group_name,
                {
                    'type': 'chat_message',
                    'data': response_data
                }
            )
            
        except Exception as e:
            await self.send_json({
                'type': chat_c.WS_MSG_TYPE_ERROR,
                'code': chat_c.MESSAGE_SEND_FAILED,
                'message': str(e)
            })
    
    async def chat_message(self, event):
        """
        接收 channel layer 推送的消息并发送给客户端
        """
        await self.send_json(event['data'])
    
    # ==================== 数据库操作辅助方法 ====================
    
    @database_sync_to_async
    def get_user_from_token(self, token):
        """
        从 JWT token 获取用户
        """
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            user = User.objects.get(id=user_id)
            return user
        except Exception:
            return None
    
    @database_sync_to_async
    def get_chat(self, chat_id):
        """
        获取会话
        """
        try:
            return PrivateChat.objects.get(id=chat_id)
        except PrivateChat.DoesNotExist:
            return None
    
    @database_sync_to_async
    def check_chat_permission(self, chat):
        """
        检查用户是否有权限访问会话
        """
        return services.check_chat_permission(chat, self.user)
    
    @database_sync_to_async
    def get_or_create_chat_by_receiver(self, receiver_id):
        """
        通过接收者ID获取或创建会话
        """
        try:
            return services.get_or_create_chat(self.user, receiver_id)
        except Exception:
            return None, False
    
    @database_sync_to_async
    def save_message(self, chat, content, msg_type):
        """
        保存消息到数据库
        """
        return services.send_message(chat, self.user, content, msg_type)
    
    @database_sync_to_async
    def serialize_message(self, message):
        """
        序列化消息对象
        """
        serializer = MessageListSerializer(message)
        return serializer.data
    
    @database_sync_to_async
    def get_other_user(self, chat):
        """
        获取会话中的对方用户
        """
        return services.get_other_user(chat, self.user)
