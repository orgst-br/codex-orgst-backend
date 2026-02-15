from django.contrib import admin

from .models import (
    Invitation,
    InvitationRole,
    Profile,
    Role,
    User,
    UserRole,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "username", "is_staff", "is_active", "date_joined")
    search_fields = ("email", "username")
    list_filter = ("is_staff", "is_active")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "display_name", "created_at", "updated_at")
    search_fields = ("display_name", "user__email")


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
