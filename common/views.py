from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
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


class PaginatedListAPIView(GenericAPIView):
    """
    通用分页列表基类
    - 子类只需要提供 serializer_class 和 get_queryset()
    - 统一使用 StandardPagination + OkResponse 输出格式
    """

    pagination_class = StandardPagination
    serializer_class = None

    def get(self, request, *args, **kwargs):
        """
        支持 filter_backends（如 SearchFilter），并统一分页返回格式
        """
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return OkResponse(data=serializer.data)
