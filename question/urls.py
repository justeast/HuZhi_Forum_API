from django.urls import path, include
from rest_framework.routers import DefaultRouter
from question import views

router = DefaultRouter()
router.register(r'', views.QuestionViewSet, basename='question')

urlpatterns = [
    path('', include(router.urls)),
]
