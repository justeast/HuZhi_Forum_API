from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from common.response import OkResponse
from base.serializers import (
    UserRegisterReqSerializer,
    UserRegisterRespSerializer,
    UserLoginReqSerializer,
    UserLogoutReqSerializer,
)
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


class UserLoginView(APIView):
    """
    用户登录
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginReqSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = services.authenticate_user(
            account=serializer.validated_data['account'],
            password=serializer.validated_data['password']
        )
        return OkResponse(data=data)


class UserLogoutView(APIView):
    """
    用户登出
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UserLogoutReqSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.logout_user(serializer.validated_data['refresh'])
        return OkResponse()
