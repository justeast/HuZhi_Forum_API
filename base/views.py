from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from common.response import OkResponse
from base.serializers import (
    UserRegisterReqSerializer,
    UserRegisterRespSerializer,
    UserLoginReqSerializer,
    UserLogoutReqSerializer,
    SendPwdResetCodeReqSerializer,
    PwdResetReqSerializer,
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


class SendPwdResetCodeView(APIView):
    """
    发送密码重置验证码
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SendPwdResetCodeReqSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.send_pwd_reset_code(serializer.validated_data['email'])
        return OkResponse(msg="验证码已发送")


class UserPwdResetView(APIView):
    """
    重置密码
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PwdResetReqSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.reset_password(
            email=serializer.validated_data['email'],
            code=serializer.validated_data['code'],
            new_password=serializer.validated_data['new_password']
        )
        return OkResponse(msg="密码重置成功")
