from rest_framework.response import Response
from rest_framework import status


class OkResponse(Response):
    """
    统一成功响应格式
    """

    def __init__(self, data=None, msg="ok", code=1, status_code=status.HTTP_200_OK, **kwargs):
        response_data = {
            'code': code,
            'msg': msg,
            'data': data if data is not None else {}
        }
        super().__init__(data=response_data, status=status_code, **kwargs)
