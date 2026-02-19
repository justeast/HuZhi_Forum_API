from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter
from django.db.models import BooleanField, Count, Exists, OuterRef, Prefetch, Value
from django_filters.rest_framework import DjangoFilterBackend
from question.models import Question
from question import serializers, services, filters
from topic.models import Topic
from vote import services as vote_services
from vote.serializers import VoteReqSerializer
from common.response import OkResponse
from common.permissions import IsOwnerOrReadOnly
from common.viewsets import BaseModelViewSet


class QuestionViewSet(BaseModelViewSet):
    """
    问题视图集
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = filters.QuestionFilter
    search_fields = ['title']

    def get_queryset(self):
        """
        重写 queryset：预取 topics 时注解 is_following，避免嵌套话题序列化出现 N+1
        """
        if self.request.user and self.request.user.is_authenticated:
            is_following_expr = Exists(
                Topic.objects.filter(pk=OuterRef("pk"), followers=self.request.user)
            )
        else:
            is_following_expr = Value(False, output_field=BooleanField())

        topics_qs = Topic.objects.annotate(is_following=is_following_expr)
        if getattr(self, 'action', None) == 'retrieve':
            # 仅问题详情页的 topics 悬浮卡片需要展示统计信息，这里按需注解，避免影响其他接口返回与性能
            topics_qs = topics_qs.annotate(
                follower_count=Count('followers', distinct=True),
                question_count=Count('questions', distinct=True),
            )
        return (
            Question.objects.select_related('questioner')
            .prefetch_related(Prefetch('topics', queryset=topics_qs), 'followers')
        )

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

    @action(detail=True, methods=['post'], url_path='vote')
    def vote(self, request, pk=None):
        """
        对问题进行投票
        """
        question = self.get_object()
        serializer = VoteReqSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        vote_type = serializer.validated_data['vote_type']
        vote_services.vote_question(request.user, question, vote_type)
        
        # 返回更新后的问题详情
        resp_serializer = serializers.QuestionDetailSerializer(question, context={'request': request})
        return OkResponse(data=resp_serializer.data)
