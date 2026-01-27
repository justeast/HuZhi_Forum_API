from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from common.response import OkResponse
from common.pagination import StandardPagination
from common.cos import get_cos_temporary_credential


class UploadTokenView(APIView):
    """
    获取COS上传临时密钥
    """
    permission_classes = [AllowAny]

    def get(self, request):
        credential = get_cos_temporary_credential()
        return OkResponse(data=credential)


class PaginatedListAPIView(APIView):
    """
    通用分页列表基类
    - 子类只需要提供 serializer_class 和 get_queryset()
    - 统一使用 StandardPagination + OkResponse 输出格式
    """

    pagination_class = StandardPagination
    serializer_class = None

    def get_queryset(self):
        raise NotImplementedError("子类必须实现 get_queryset()")

    def get_serializer_class(self):
        if self.serializer_class is None:
            raise NotImplementedError("子类必须设置 serializer_class 或实现 get_serializer_class()")
        return self.serializer_class

    def get_serializer_context(self, request):
        """
        统一注入 request，便于序列化器计算用户态字段
        """
        return {"request": request}

    def get(self, request):
        queryset = self.get_queryset()

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        if page is not None:
            serializer = self.get_serializer_class()(page, many=True, context=self.get_serializer_context(request))
            return paginator.get_paginated_response(serializer.data)

        serializer = self.get_serializer_class()(queryset, many=True, context=self.get_serializer_context(request))
        return OkResponse(data=serializer.data)
