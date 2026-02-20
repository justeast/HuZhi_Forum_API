from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Exists, OuterRef
from django_filters.rest_framework import DjangoFilterBackend
from answer.models import Answer
from answer import serializers, services
from collection.models import Collection
from vote import services as vote_services
from vote.serializers import VoteReqSerializer
from common.response import OkResponse
from common.permissions import IsOwnerOrReadOnly
from common.viewsets import BaseModelViewSet


class AnswerViewSet(BaseModelViewSet):
    """
    回答视图集
    """
    permission_classes = [IsAuthenticated]
    queryset = Answer.objects.select_related('respondent', 'question').prefetch_related('comments')
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['question']

    def get_queryset(self):
        """
        list 场景下（问题详情页回答列表）补充 collected_count（按用户去重），避免额外接口/查询
        """
        queryset = super().get_queryset()
        if self.action == 'list' and self.request.query_params.get('question'):
            return queryset.annotate(
                collected_count=Count('collections__owner', distinct=True),
                # 当前用户是否已收藏该回答（存在任意一个归属当前用户的收藏夹包含该回答即可）
                is_collected=Exists(
                    Collection.objects.filter(owner=self.request.user, answers=OuterRef('pk'))
                ),
            )
        return queryset

    def get_serializer_class(self):
        """
        根据不同操作返回不同序列化器
        """
        if self.action == 'list':
            # 问题详情页：通过 query string 传 question 获取回答列表
            if self.request.query_params.get('question'):
                return serializers.AnswerListForQuestionSerializer
            return serializers.AnswerListSerializer
        elif self.action == 'retrieve':
            return serializers.AnswerDetailSerializer
        elif self.action == 'create':
            return serializers.AnswerCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return serializers.AnswerUpdateSerializer
        return serializers.AnswerListSerializer

    def get_permissions(self):
        """
        根据不同操作返回不同权限
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        """
        创建回答
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        answer = services.create_answer(request.user, serializer.validated_data)
        resp_serializer = serializers.AnswerDetailSerializer(answer, context={'request': request})
        return OkResponse(data=resp_serializer.data, status_code=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """
        更新回答（支持完整更新和部分更新）
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        self.check_object_permissions(request, instance)

        serializer = self.get_serializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        answer = services.update_answer(instance, serializer.validated_data)
        resp_serializer = serializers.AnswerDetailSerializer(answer, context={'request': request})
        return OkResponse(data=resp_serializer.data)

    @action(detail=True, methods=['post'], url_path='vote')
    def vote(self, request, pk=None):
        """
        对回答进行投票
        """
        answer = self.get_object()
        serializer = VoteReqSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        vote_type = serializer.validated_data['vote_type']
        vote_services.vote_answer(request.user, answer, vote_type)
        
        # 返回更新后的回答详情
        resp_serializer = serializers.AnswerDetailSerializer(answer, context={'request': request})
        return OkResponse(data=resp_serializer.data)
