from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db.models import Exists, OuterRef
from collection.models import Collection
from answer.models import Answer
from collection import serializers, services
from common.response import OkResponse
from common.permissions import IsOwnerOrReadOnly, IsCollectionOwnerOrPublic
from common.exceptions import BusinessException
from common.utils import parse_uuid_query_param
from answer import constants as answer_c
from base.models import User
from base import constants as base_c
from common.viewsets import BaseModelViewSet


class CollectionViewSet(BaseModelViewSet):
    """
    收藏夹视图集
    """
    permission_classes = [IsAuthenticated]
    queryset = Collection.objects.select_related('owner').prefetch_related('answers')

    def get_serializer_class(self):
        """
        根据不同操作返回不同序列化器
        """
        if self.action == 'list':
            return serializers.CollectionListSerializer
        elif self.action == 'retrieve':
            return serializers.CollectionDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return serializers.CollectionWriteSerializer
        elif self.action == 'answers':
            return serializers.CollectionAnswerListSerializer
        return serializers.CollectionListSerializer

    def get_queryset(self):
        """
        重写queryset：
        - 列表接口只返回当前用户的收藏夹
        - 支持通过 ?owner=<user_id> 查看他人公开收藏夹（用于他人主页收藏Tab）
        - 支持通过 ?answer=<answer_id> 过滤出“包含该回答”的收藏夹列表（用于取消收藏时弹窗选择）
        """
        if self.action == 'list':
            answer_uuid = parse_uuid_query_param(self.request, 'answer')
            if answer_uuid:
                # 取消收藏弹窗场景：仅允许查询“我自己的”收藏夹列表
                queryset = Collection.objects.filter(owner=self.request.user).select_related('owner')

                # 若回答不存在，则直接返回业务错误，避免前端误用导致“静默空列表”难以排查
                if not Answer.objects.filter(id=answer_uuid).exists():
                    raise BusinessException(
                        code=answer_c.ANSWER_NOT_FOUND,
                        msg=answer_c.ANSWER_NOT_FOUND_MSG,
                    )

                queryset = queryset.filter(answers__id=answer_uuid).distinct()
                return queryset

            owner_uuid = parse_uuid_query_param(self.request, 'owner')
            if owner_uuid:

                # 查看自己：返回全部（公开+私有）
                if owner_uuid == self.request.user.id:
                    return Collection.objects.filter(owner=self.request.user).select_related('owner')

                # 查看他人：仅返回公开收藏夹
                if not User.objects.filter(id=owner_uuid).exists():
                    raise BusinessException(code=base_c.USER_NOT_FOUND, msg=base_c.USER_NOT_FOUND_MSG)

                return (
                    Collection.objects.filter(owner_id=owner_uuid, is_public=True)
                    .select_related('owner')
                )

            # 默认：返回当前用户自己的收藏夹
            return Collection.objects.filter(owner=self.request.user).select_related('owner')
        return super().get_queryset()

    def get_permissions(self):
        """
        根据不同操作返回不同权限
        """
        if self.action in ['retrieve', 'answers']:
            # 详情接口和收藏夹内回答列表接口：公开收藏夹任何人可看，私有收藏夹仅owner可看
            return [IsAuthenticated(), IsCollectionOwnerOrPublic()]
        elif self.action in ['update', 'partial_update', 'destroy', 'collect_answer']:
            # 修改/删除/收藏回答接口：仅owner可操作
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        """
        创建收藏夹
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        collection = services.create_collection(request.user, serializer.validated_data)
        resp_serializer = serializers.CollectionDetailSerializer(collection, context={'request': request})
        return OkResponse(data=resp_serializer.data, status_code=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """
        更新收藏夹（支持完整更新和部分更新）
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        self.check_object_permissions(request, instance)

        serializer = self.get_serializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        collection = services.update_collection(instance, serializer.validated_data)
        resp_serializer = serializers.CollectionDetailSerializer(collection, context={'request': request})
        return OkResponse(data=resp_serializer.data)

    @action(detail=True, methods=['post'], url_path='collect_answer')
    def collect_answer(self, request, pk=None):
        """
        收藏/取消收藏回答（toggle操作）
        """
        collection = self.get_object()
        self.check_object_permissions(request, collection)

        # 验证请求数据
        req_serializer = serializers.CollectAnswerReqSerializer(data=request.data)
        req_serializer.is_valid(raise_exception=True)

        # 获取回答对象（序列化器已校验存在性）
        answer_id = req_serializer.validated_data['answer_id']
        answer = Answer.objects.get(id=answer_id)

        # 执行toggle操作
        is_collected, answer_count = services.toggle_collect_answer(collection, answer)

        # 返回操作结果
        resp_serializer = serializers.CollectAnswerRespSerializer(data={
            'collected': is_collected,
            'answer_count': answer_count
        })
        resp_serializer.is_valid()
        return OkResponse(data=resp_serializer.data)

    @action(detail=True, methods=['get'], url_path='answers')
    def answers(self, request, pk=None):
        """
        获取收藏夹内的回答列表（分页）
        """
        collection = self.get_object()
        self.check_object_permissions(request, collection)

        # 获取收藏夹内的回答列表
        queryset = (
            collection.answers.select_related('respondent', 'question')
            .prefetch_related('comments')
            # 当前用户是否已收藏该回答：AnswerSimpleSerializer 会优先读取该注解，避免列表场景 N+1
            .annotate(is_collected=Exists(
                Collection.objects.filter(owner=request.user, answers=OuterRef('pk'))
            ))
        )
        
        # 分页
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return OkResponse(data=serializer.data)
