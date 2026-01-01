from django.db.models import Q
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from chat.models import PrivateChat
from chat import serializers, services
from common.response import OkResponse
from common.pagination import StandardPagination
from common.permissions import IsChatParticipant


class ChatViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    """
    私信会话视图集
    只提供：列表、创建、获取消息、标记已读
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    queryset = PrivateChat.objects.select_related('user1', 'user2').prefetch_related('messages')
    
    def get_permissions(self):
        """
        根据不同操作返回不同权限
        """
        if self.action in ['messages', 'mark_read']:
            return [IsAuthenticated(), IsChatParticipant()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        """
        根据不同操作返回不同序列化器
        """
        if self.action == 'list':
            return serializers.PrivateChatListSerializer
        elif self.action == 'create':
            return serializers.ChatCreateReqSerializer
        elif self.action == 'messages':
            return serializers.MessageListSerializer
        return serializers.PrivateChatListSerializer
    
    def get_queryset(self):
        """
        重写queryset，只返回当前用户的会话
        """
        return PrivateChat.objects.filter(
            Q(user1=self.request.user) | Q(user2=self.request.user)
        ).select_related('user1', 'user2').prefetch_related('messages')
    
    def create(self, request, *args, **kwargs):
        """
        创建/获取会话
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        receiver_id = serializer.validated_data['receiver_id']
        chat, created = services.get_or_create_chat(request.user, receiver_id)
        
        resp_serializer = serializers.PrivateChatDetailSerializer(chat, context={'request': request})
        return OkResponse(
            data=resp_serializer.data,
            status_code=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['get'], url_path='messages')
    def messages(self, request, pk=None):
        """
        获取会话的历史消息（分页）
        """
        chat = self.get_object()
        
        # 获取历史消息
        messages = services.get_chat_messages(chat)
        
        # 分页
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(messages, many=True)
        return OkResponse(data=serializer.data)
    
    @action(detail=True, methods=['post'], url_path='read')
    def mark_read(self, request, pk=None):
        """
        标记消息已读
        """
        chat = self.get_object()
        
        # 验证请求数据
        req_serializer = serializers.MarkReadReqSerializer(data=request.data)
        req_serializer.is_valid(raise_exception=True)
        
        message_ids = req_serializer.validated_data.get('message_ids')
        
        # 标记已读
        updated_count = services.mark_messages_read(chat, request.user, message_ids)
        
        return OkResponse(data={'updated_count': updated_count})
