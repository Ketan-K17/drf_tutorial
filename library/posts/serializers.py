from rest_framework import serializers
from .models import Post

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            "id",
            "author",
            "title",
            "body",
            "created_at",
        )
        # NOTE: we've not added 'updated_at' field to the serializer.. that value should be decided by backend.
        model = Post