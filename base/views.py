from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import status
from common.response import OkResponse
from base.serializers import UserRegisterReqSerializer, UserRegisterRespSerializer
from base import services


class UserRegisterView(APIView):
    """
    用户注册
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterReqSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.create_user(serializer.validated_data)
        resp_serializer = UserRegisterRespSerializer(user)
        return OkResponse(data=resp_serializer.data, status_code=status.HTTP_201_CREATED)
