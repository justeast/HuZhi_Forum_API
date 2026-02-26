from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from django_filters.rest_framework import DjangoFilterBackend
from comment.models import Comment
from comment import serializers, services
from common.response import OkResponse
from common.pagination import StandardPagination
from common.permissions import IsCommentOwnerOrAnswerAuthor


class CommentViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    """
    评论视图集（增删查 + 点赞）
    """
    permission_classes = [IsAuthenticated]
    queryset = Comment.objects.select_related('user', 'reply_to', 'answer')
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['answer', 'parent']
    pagination_class = StandardPagination
    
    def get_serializer_class(self):
        """
        根据不同操作返回不同序列化器
        """
        if self.action == 'create':
            return serializers.CommentCreateSerializer
        return serializers.CommentListSerializer
    
    def get_permissions(self):
        """
        根据不同操作返回不同权限
        """
        if self.action == 'destroy':
            return [IsAuthenticated(), IsCommentOwnerOrAnswerAuthor()]
        return [IsAuthenticated()]
    
    def list(self, request, *args, **kwargs):
        """
        获取评论列表
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return OkResponse(data=serializer.data)
    
    def create(self, request, *args, **kwargs):
        """
        创建评论
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = services.create_comment(request.user, serializer.validated_data)
        resp_serializer = serializers.CommentDetailSerializer(comment, context={'request': request})
        return OkResponse(data=resp_serializer.data, status_code=status.HTTP_201_CREATED)
    
    def destroy(self, request, *args, **kwargs):
        """
        删除评论
        """
        instance = self.get_object()
        self.check_object_permissions(request, instance)

        # 先记录所属回答，用于删除后返回该回答的最新评论总数（包含二级评论）
        answer_id = instance.answer_id

        # 删除父评论时会级联删除其 replies（二级评论）
        instance.delete()

        # 返回删除后的评论总数，便于前端准确更新 answer.comment_count
        comment_count = Comment.objects.filter(answer_id=answer_id).count()
        return OkResponse(data={'comment_count': comment_count})
    
    @action(detail=True, methods=['post'], url_path='like')
    def like(self, request, pk=None):
        """
        评论点赞/取消点赞（toggle操作）
        """
        comment = self.get_object()
        services.like_comment(request.user, comment)
        
        # 返回更新后的评论信息
        resp_serializer = serializers.CommentDetailSerializer(comment, context={'request': request})
        return OkResponse(data=resp_serializer.data)
