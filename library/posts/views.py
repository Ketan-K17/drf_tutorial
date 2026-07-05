from rest_framework import permissions
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from .models import Post
from .serializers import PostSerializer
from .permissions import IsAuthorOrReadOnly


class PostList(ListCreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthorOrReadOnly]
    
class PostDetail(RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    # permission_classes = [permissions.IsAdminUser]
    permission_classes = [IsAuthorOrReadOnly]

# NOTE: for view level permissions, we can use the permission_classes attribute.