from django.contrib import admin

from .models import (
    Invitation,
    InvitationRole,
    Profile,
    Role,
    User,
    UserRole,
)


def _is_profile_staff(user):
    return (
        user.is_authenticated
        and user.is_staff
        and not user.is_superuser
        and user.user_roles.filter(role__key__in=["mentor", "mentorado"]).exists()
    )


class SuperuserOnlyAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "username", "is_staff", "is_active", "date_joined")
    search_fields = ("email", "username")
    list_filter = ("is_staff", "is_active")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "display_name", "created_at", "updated_at")
    search_fields = ("display_name", "user__email")

    def has_module_permission(self, request):
        return request.user.is_superuser or _is_profile_staff(request.user)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if _is_profile_staff(request.user):
            return qs.filter(user=request.user)
        return qs.none()

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if not _is_profile_staff(request.user):
            return False
        return obj is None or obj.user_id == request.user.id

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if not _is_profile_staff(request.user):
            return False
        return obj is None or obj.user_id == request.user.id

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return self.readonly_fields
        return ("user", "created_at", "updated_at")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id", "key", "label", "created_at")
    search_fields = ("key", "label")


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("user__email", "role__key")


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "status", "expires_at", "invited_by", "accepted_by")
    list_filter = ("status",)
    search_fields = ("email",)
    readonly_fields = ("token_hash", "accepted_at", "created_at", "updated_at")


@admin.register(InvitationRole)
class InvitationRoleAdmin(admin.ModelAdmin):
    list_display = ("id", "invitation", "role")
    list_filter = ("role",)
