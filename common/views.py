from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from common.response import OkResponse
from common.cos import get_cos_temporary_credential


class UploadTokenView(APIView):
    """
    获取COS上传临时密钥
    """
    permission_classes = [AllowAny]

    def get(self, request):
        credential = get_cos_temporary_credential()
        return OkResponse(data=credential)
