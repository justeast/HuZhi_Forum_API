from django.urls import path
from base import views

urlpatterns = [
    path('register/', views.UserRegisterView.as_view(), name='register'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('pwd-reset/code/', views.SendPwdResetCodeView.as_view(), name='pwd_reset_code'),
    path('pwd-reset/', views.UserPwdResetView.as_view(), name='pwd_reset'),
    path('pwd-change/', views.UserPwdChangeView.as_view(), name='pwd_change'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('following/topics/', views.UserFollowingTopicsView.as_view(), name='following_topics'),
    path('following/questions/', views.UserFollowingQuestionsView.as_view(), name='following_questions'),
    path('following/users/', views.UserFollowingUsersView.as_view(), name='following_users'),
    path('followers/users/', views.UserFollowersUsersView.as_view(), name='followers_users'),
    path('<uuid:user_id>/follow/', views.UserFollowView.as_view(), name='user_follow'),
    path('achievements/', views.UserAchievementsView.as_view(), name='user_achievements'),
    path('questions/', views.UserQuestionsView.as_view(), name='user_questions'),
    path('answers/', views.UserAnswersView.as_view(), name='user_answers'),
]
