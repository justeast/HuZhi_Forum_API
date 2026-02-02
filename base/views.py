from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.filters import SearchFilter
from django.db.models import BooleanField, Exists, OuterRef, Prefetch, Value
from common.response import OkResponse
from common.views import PaginatedListAPIView
from base.serializers import (
    UserRegisterReqSerializer,
    UserRegisterRespSerializer,
    UserLoginReqSerializer,
    UserLogoutReqSerializer,
    SendPwdResetCodeReqSerializer,
    PwdResetReqSerializer,
    PwdChangeReqSerializer,
    UserProfileSerializer,
    UserAchievementsRespSerializer,
)
from base import services
from question.models import Question
from question.serializers import QuestionListSerializer
from topic.models import Topic
from topic.serializers import TopicListSerializer


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


class UserFollowingTopicsView(PaginatedListAPIView):
    """
    用户关注的话题列表
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TopicListSerializer
    filter_backends = [SearchFilter]
    search_fields = ['name']

    def get_queryset(self):
        return (
            Topic.objects.filter(followers=self.request.user)
            .select_related('creator')
            .prefetch_related('questions')
            .annotate(is_following=Value(True, output_field=BooleanField()))
            .order_by('-modified', '-created')
        )


class UserFollowingQuestionsView(PaginatedListAPIView):
    """
    用户关注的问题列表
    """
    permission_classes = [IsAuthenticated]
    serializer_class = QuestionListSerializer
    filter_backends = [SearchFilter]
    search_fields = ['title']

    def get_queryset(self):
        # 为嵌套话题预取注解 is_following，避免 TopicSimpleSerializer 触发 N+1
        topic_is_following_expr = Exists(
            Topic.objects.filter(pk=OuterRef("pk"), followers=self.request.user)
        )
        topics_qs = Topic.objects.annotate(is_following=topic_is_following_expr)

        return (
            Question.objects.filter(followers=self.request.user)
            .select_related('questioner')
            .prefetch_related(Prefetch('topics', queryset=topics_qs), 'followers')
            .order_by('-modified', '-created')
        )


class UserAchievementsView(APIView):
    """
    用户的个人成就
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = services.get_user_achievements(request.user)
        serializer = UserAchievementsRespSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return OkResponse(data=serializer.validated_data)
