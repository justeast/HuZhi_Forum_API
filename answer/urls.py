from rest_framework.routers import DefaultRouter
from answer.views import AnswerViewSet

router = DefaultRouter()
router.register(r'', AnswerViewSet, basename='answer')

urlpatterns = router.urls
