from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateAPIView
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
    PwdChangeReqSerializer,
    UserProfileSerializer,
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


class UserPwdChangeView(APIView):
    """
    修改密码（已登录用户）
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PwdChangeReqSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.change_password(
            user=request.user,
            old_password=serializer.validated_data['old_password'],
            new_password=serializer.validated_data['new_password']
        )
        return OkResponse(msg="密码修改成功")


class UserProfileView(RetrieveUpdateAPIView):
    """
    用户详情（获取和修改）
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return OkResponse(data=serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return OkResponse(data=serializer.data)
