from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = [
        "email",
        "username",
        "name",
        "is_staff",
    ]

    fieldsets = UserAdmin.fieldsets + (("Name", {"fields": ("name",)}),)
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "password1", "password2", "email", "name"),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # usable_password is a form-only field added by the auth forms at
        # __init__ time; remove it so modelform_factory's field check is happy.
        form.base_fields.pop("usable_password", None)
        return form

admin.site.register(CustomUser, CustomUserAdmin)