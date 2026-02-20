from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.filters import SearchFilter
from django.db.models import BooleanField, Exists, OuterRef, Value
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
    UserFollowReqSerializer,
    UserFollowingListSerializer,
    UserFollowersListSerializer,
    UserCardRespSerializer,
)
from base import constants as c
from base import services
from answer.models import Answer
from answer.serializers import AnswerWithQuestionSerializer
from collection.models import Collection
from question.models import Question
from question.serializers import QuestionListSerializer
from question import services as question_services
from topic.models import Topic
from topic.serializers import TopicListSerializer
from base.models import UserFollow


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
        base_qs = Question.objects.filter(followers=self.request.user)
        return question_services.build_question_list_queryset(self.request.user, base_qs)


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


class UserFollowView(APIView):
    """
    关注/取消关注用户
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        serializer = UserFollowReqSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        services.toggle_follow_user(
            user=request.user,
            target_user_id=user_id,
            action=serializer.validated_data['action'],
        )
        return OkResponse()


class UserFollowingUsersView(PaginatedListAPIView):
    """
    我关注的用户列表
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserFollowingListSerializer

    def get_queryset(self):
        return (
            UserFollow.objects.filter(follower=self.request.user)
            # 是否互关：对方也关注了我
            .annotate(is_mutual=Exists(
                UserFollow.objects.filter(
                    follower_id=OuterRef('following_id'),
                    following=self.request.user,
                )
            ))
            .select_related('following')
            .order_by('-created')
        )


class UserFollowersUsersView(PaginatedListAPIView):
    """
    关注我的用户列表
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserFollowersListSerializer

    def get_queryset(self):
        return (
            UserFollow.objects.filter(following=self.request.user)
            # 是否互关：我也关注了对方
            .annotate(is_mutual=Exists(
                UserFollow.objects.filter(
                    follower=self.request.user,
                    following_id=OuterRef('follower_id'),
                )
            ))
            .select_related('follower')
            .order_by('-created')
        )


class UserQuestionsView(PaginatedListAPIView):
    """
    我的提问列表
    """
    permission_classes = [IsAuthenticated]
    serializer_class = QuestionListSerializer

    def get_queryset(self):
        base_qs = Question.objects.filter(questioner=self.request.user)
        return question_services.build_question_list_queryset(self.request.user, base_qs)


class UserAnswersView(PaginatedListAPIView):
    """
    我的回答列表（包含所属问题标题）
    """
    permission_classes = [IsAuthenticated]
    serializer_class = AnswerWithQuestionSerializer

    def get_queryset(self):
        return (
            Answer.objects.filter(respondent=self.request.user)
            .select_related('respondent', 'question')
            .prefetch_related('comments')
            # 当前用户是否已收藏该回答：AnswerSimpleSerializer 会优先读取该注解，避免列表场景 N+1
            .annotate(is_collected=Exists(
                Collection.objects.filter(owner=self.request.user, answers=OuterRef('pk'))
            ))
            .order_by('-modified', '-created')
        )


class UserCardView(APIView):
    """
    用户卡片统计（用于“关于作者”卡片）
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        data = services.get_user_card(current_user=request.user, target_user_id=user_id)
        serializer = UserCardRespSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return OkResponse(data=serializer.validated_data)
