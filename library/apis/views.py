from rest_framework import generics
from books.models import Book
from .serializers import BookSerializer

class BookAPIView(generics.ListAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

# NOTE: A little something about serializers..

# for drf, the pattern for exposing any data is mostly similar to how traditional django does it, with one key difference.. views in drf serve data such as json / xml as opposed to actual web-pages / templates in case of traditional django.

# An additional step that we tend to use for drf, requiring its own file too, is serialization / de-serialization. Serialization is the proess of converting complex model instances / other data structures into json / xml. De-serialization, conversely, is the process of building your model instances / objects from this json / xml.

# serializers.py sits between your view and your model —
# the view receives raw JSON, hands it to the serializer,
# and the serializer handles validation + conversion before
# anything touches the database.

# under the hood, de-serialization is a 2-step process.

# **Step 1: JSON → Python dictionary**
# This is the *validation* step. The raw JSON bytes are parsed into a native Python dict, field types are coerced, and validation rules are checked. At this stage you have a `validated_data` dict. you can access it via serializer.validated_data

# **Step 2: Python dictionary → Model instance**
# This is the *save* step. The validated dict is then passed to `.create()` or `.update()`, which produces or modifies an actual model instance in the database.

# So the full deserialization pipeline is really:

# ```
# JSON → dict (validated_data) → model instance
# ```