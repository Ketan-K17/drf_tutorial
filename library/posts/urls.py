from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import PostViewSet, UserViewSet

router = DefaultRouter()
router.register("posts", PostViewSet, basename="post")
router.register("users", UserViewSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
]
