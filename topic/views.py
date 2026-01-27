from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db.models import BooleanField, Exists, OuterRef, Value
from rest_framework.filters import SearchFilter
from topic.models import Topic
from topic import serializers, services
from common.response import OkResponse
from common.permissions import IsOwnerOrReadOnly
from common.viewsets import BaseModelViewSet


class TopicViewSet(BaseModelViewSet):
    """
    话题视图集
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ['name']

    def get_queryset(self):
        """
        重写 queryset：为每个话题注解 is_following，避免 N+1 且不预取大量 followers 用户
        """
        if self.request.user and self.request.user.is_authenticated:
            is_following_expr = Exists(
                Topic.objects.filter(pk=OuterRef("pk"), followers=self.request.user)
            )
        else:
            is_following_expr = Value(False, output_field=BooleanField())

        return (
            Topic.objects.select_related('creator')
            .prefetch_related('questions')
            .annotate(is_following=is_following_expr)
        )

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
