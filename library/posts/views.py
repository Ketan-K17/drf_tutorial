from django.contrib.auth import get_user_model
from rest_framework import permissions, viewsets
from .models import Post
from .serializers import PostSerializer, UserSerializer
from .permissions import IsAuthorOrReadOnly

User = get_user_model()


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthorOrReadOnly]


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

# NOTE: PERMISSION CLASSES: for view level permissions, we can use the permission_classes attribute.

# NOTE: VIEWSETS: Viewsets & Routers are a way of reducing code repetition in your views and urls files. They group together views into one bunch..
