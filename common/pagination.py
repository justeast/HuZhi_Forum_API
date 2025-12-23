from rest_framework.pagination import PageNumberPagination
from common.response import OkResponse


class StandardPagination(PageNumberPagination):
    """
    统一的分页类
    """
    page_size = 20
    page_size_query_param = 'size'
    page_query_param = 'page'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        """
        自定义分页响应格式，统一使用 OkResponse
        """
        return OkResponse(data={
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })
