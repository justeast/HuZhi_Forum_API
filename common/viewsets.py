from rest_framework import viewsets
from common.pagination import StandardPagination
from common.response import OkResponse


class BaseModelViewSet(viewsets.ModelViewSet):
    """
    通用的 ModelViewSet 基类
    统一处理分页、响应格式等通用逻辑
    """
    pagination_class = StandardPagination
    
    def list(self, request, *args, **kwargs):
        """
        统一的列表接口实现
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return OkResponse(data=serializer.data)
