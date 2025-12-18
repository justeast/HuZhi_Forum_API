from django.urls import path
from base import views

urlpatterns = [
    path('register/', views.UserRegisterView.as_view(), name='register'),
]
