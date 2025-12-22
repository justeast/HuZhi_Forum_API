from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter
from topic.models import Topic
from topic import serializers, services
from common.response import OkResponse
from common.permissions import IsOwnerOrReadOnly


class TopicViewSet(viewsets.ModelViewSet):
    """
    话题视图集
    """
    queryset = Topic.objects.select_related('creator').prefetch_related('followers', 'questions')
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ['name']

    def get_serializer_class(self):
        """
        根据不同操作返回不同序列化器
        """
        if self.action == 'list':
            return serializers.TopicListSerializer
        elif self.action == 'retrieve':
            return serializers.TopicDetailSerializer
        elif self.action == 'create':
            return serializers.TopicCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return serializers.TopicUpdateSerializer
        return serializers.TopicListSerializer

    def get_permissions(self):
        """
        根据不同操作返回不同权限
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        return [IsAuthenticated()]

    def retrieve(self, request, *args, **kwargs):
        """
        获取话题详情
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return OkResponse(data=serializer.data)

    def create(self, request, *args, **kwargs):
        """
        创建话题
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        topic = services.create_topic(request.user, serializer.validated_data)
        resp_serializer = serializers.TopicDetailSerializer(topic, context={'request': request})
        return OkResponse(data=resp_serializer.data, status_code=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """
        更新话题（支持完整更新和部分更新，但不允许修改 name）
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        self.check_object_permissions(request, instance)

        serializer = self.get_serializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        topic = services.update_topic(instance, serializer.validated_data)
        resp_serializer = serializers.TopicDetailSerializer(topic, context={'request': request})
        return OkResponse(data=resp_serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        删除话题
        """
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        instance.delete()
        return OkResponse(status_code=status.HTTP_204_NO_CONTENT)

    def list(self, request, *args, **kwargs):
        """
        获取话题列表
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return OkResponse(data=serializer.data)

    @action(detail=True, methods=['post'], url_path='follow')
    def toggle_follow(self, request, pk=None):
        """
        关注/取消关注话题
        """
        topic = self.get_object()
        serializer = serializers.TopicFollowSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action_type = serializer.validated_data['action']
        services.toggle_follow_topic(request.user, topic, action_type)
        return OkResponse()
