from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework import status


class ParamException(APIException):
    """
    请求参数异常
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "请求参数错误"
    default_code = 400


class BusinessException(APIException):
    """
    业务逻辑异常
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "业务处理失败"
    default_code = 500

    def __init__(self, code=None, msg=None, status_code=None):
        self.code = code or self.default_code
        self.msg = msg or self.default_detail
        if status_code:
            self.status_code = status_code
        super().__init__(detail=self.msg)


def custom_exception_handler(exc, context):
    """
    自定义异常处理器
    将异常转换为统一格式：{code, msg, data:{}}
    """
    # 先调用DRF默认的异常处理
    response = exception_handler(exc, context)

    if response is not None:
        # 处理自定义异常
        if isinstance(exc, BusinessException):
            response.data = {
                'code': exc.code,
                'msg': exc.msg,
                'data': {}
            }
        elif isinstance(exc, ParamException):
            response.data = {
                'code': exc.default_code,
                'msg': exc.default_detail,
                'data': {}
            }
        else:
            # 处理DRF内置异常（如ValidationError等）
            detail = response.data.get('detail', str(response.data))
            response.data = {
                'code': response.status_code,
                'msg': detail if isinstance(detail, str) else "请求错误",
                'data': {}
            }

    return response
