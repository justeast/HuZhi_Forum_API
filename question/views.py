from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from question.models import Question
from question import serializers, services
from common.response import OkResponse
from common.permissions import IsOwnerOrReadOnly


class QuestionViewSet(viewsets.ModelViewSet):
    """
    问题视图集
    """
    permission_classes = [IsAuthenticated]
    queryset = Question.objects.select_related('questioner').prefetch_related('topics', 'followers')
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['topics']

    def get_serializer_class(self):
        """
        根据不同操作返回不同序列化器
        """
        if self.action == 'list':
            return serializers.QuestionListSerializer
        elif self.action == 'retrieve':
            return serializers.QuestionDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return serializers.QuestionWriteSerializer
        return serializers.QuestionListSerializer

    def get_permissions(self):
        """
        根据不同操作返回不同权限
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        return [IsAuthenticated()]

    def retrieve(self, request, *args, **kwargs):
        """
        获取问题详情，增加浏览量
        """
        instance = self.get_object()
        services.increment_view_count(instance)
        serializer = self.get_serializer(instance)
        return OkResponse(data=serializer.data)

    def create(self, request, *args, **kwargs):
        """
        创建问题
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = services.create_question(request.user, serializer.validated_data)
        resp_serializer = serializers.QuestionDetailSerializer(question, context={'request': request})
        return OkResponse(data=resp_serializer.data, status_code=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """
        更新问题（支持完整更新和部分更新）
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        self.check_object_permissions(request, instance)

        serializer = self.get_serializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        question = services.update_question(instance, serializer.validated_data)
        resp_serializer = serializers.QuestionDetailSerializer(question, context={'request': request})
        return OkResponse(data=resp_serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        删除问题
        """
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        instance.delete()
        return OkResponse(status_code=status.HTTP_204_NO_CONTENT)

    def list(self, request, *args, **kwargs):
        """
        获取问题列表
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
        关注/取消关注问题
        """
        question = self.get_object()
        serializer = serializers.QuestionFollowSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action_type = serializer.validated_data['action']
        services.toggle_follow_question(request.user, question, action_type)
        return OkResponse()
