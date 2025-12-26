from rest_framework.routers import DefaultRouter
from collection.views import CollectionViewSet

router = DefaultRouter()
router.register(r'', CollectionViewSet, basename='collection')

urlpatterns = router.urls
