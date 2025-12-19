from django.urls import path
from base import views

urlpatterns = [
    path('register/', views.UserRegisterView.as_view(), name='register'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('pwd-reset/code/', views.SendPwdResetCodeView.as_view(), name='pwd_reset_code'),
    path('pwd-reset/', views.UserPwdResetView.as_view(), name='pwd_reset'),
]
