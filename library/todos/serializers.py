from rest_framework import serializers
from .models import Todo

class TodoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Todo
        fields = (
            "id",
            "title",
            "body",
        )

# NOTE
# 1. De-Serialization: some data is fed to us via view, we then do serializer.is_valid(data=request.data) to validate the data, if it's valid, we then do serializer.save() to save the data to the database.

# 2. Serialization: some data is queried from us, so the object is fetched from db, and it comes to serializer object as - 

# serializer = TodoSerializer(todo_object)
# serializer.data will give us the data in the format of a dictionary. This will then convert to json and be sent as response from view.