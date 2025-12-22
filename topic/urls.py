from django.urls import path, include
from rest_framework.routers import DefaultRouter
from topic import views

router = DefaultRouter()
router.register(r'', views.TopicViewSet, basename='topic')

urlpatterns = [
    path('', include(router.urls)),
]
