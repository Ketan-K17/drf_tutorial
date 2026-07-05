from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAuthorOrReadOnly(BasePermission):
    def has_permission(self, request, view):
    # Authenticated users only can see list view
        if request.user.is_authenticated:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request so we'll always
        # allow GET, HEAD, or OPTIONS requests
        if request.method in SAFE_METHODS:
            return True

        # Write permissions are only allowed to the author of a post
        return obj.author == request.user

# NOTE: for custom permissions, you will mostly need a dedicated permissions.py file. This is because you will need to override the BasePermission class to have your own logic in it, and set that instead as the permission class for your views. That definition of your inheriting permission class will sit in permissions.py.

# has_permission() is called to check if the user has permission to access the view.
# has_object_permission() is called to check what permissions the user has on a specific object.

# NOTE: What we just controlled was Authorization, not Authentication. Authentication is the process of verifying who the user is, and Authorization is the process of verifying what the user is allowed to do.