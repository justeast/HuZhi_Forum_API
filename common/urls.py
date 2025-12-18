from django.urls import path
from common import views

urlpatterns = [
    path('upload/token/', views.UploadTokenView.as_view(), name='upload_token'),
]
