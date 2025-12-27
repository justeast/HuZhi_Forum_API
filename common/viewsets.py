from rest_framework import viewsets, status
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
    
    def retrieve(self, request, *args, **kwargs):
        """
        统一的详情接口实现
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return OkResponse(data=serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """
        统一的删除接口实现
        """
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        instance.delete()
        return OkResponse(status_code=status.HTTP_204_NO_CONTENT)
