from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from answer.models import Answer
from answer import serializers, services
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

    def get_serializer_class(self):
        """
        根据不同操作返回不同序列化器
        """
        if self.action == 'list':
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

    def retrieve(self, request, *args, **kwargs):
        """
        获取回答详情
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return OkResponse(data=serializer.data)

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

    def destroy(self, request, *args, **kwargs):
        """
        删除回答
        """
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        instance.delete()
        return OkResponse(status_code=status.HTTP_204_NO_CONTENT)

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
