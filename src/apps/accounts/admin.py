from django.contrib import admin, messages

from .models import Invitation, InvitationRole, Profile, Role, User, UserRole
from .services import provision_admin_only_invitation


def _is_profile_staff(user):
    return (
        user.is_authenticated
        and user.is_staff
        and not user.is_superuser
        and user.user_roles.filter(role__key__in=["mentor", "mentorado"]).exists()
    )


def _is_invite_manager(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.user_roles.filter(role__key__in=["admin", "cofounder"]).exists()


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
class UserAdmin(SuperuserOnlyAdmin):
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
class RoleAdmin(SuperuserOnlyAdmin):
    list_display = ("id", "key", "label", "created_at")
    search_fields = ("key", "label")


@admin.register(UserRole)
class UserRoleAdmin(SuperuserOnlyAdmin):
    list_display = ("id", "user", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("user__email", "role__key")


class InvitationRoleInline(admin.TabularInline):
    model = InvitationRole
    extra = 1


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "status", "expires_at", "invited_by", "accepted_by")
    list_filter = ("status",)
    search_fields = ("email",)
    readonly_fields = ("token_hash", "accepted_at", "created_at", "updated_at")
    inlines = [InvitationRoleInline]
    actions = ["provision_temp_admin_access"]

    def has_module_permission(self, request):
        return _is_invite_manager(request.user)

    def has_view_permission(self, request, obj=None):
        return _is_invite_manager(request.user)

    def has_change_permission(self, request, obj=None):
        return _is_invite_manager(request.user)

    def has_add_permission(self, request):
        return _is_invite_manager(request.user)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def save_model(self, request, obj, form, change):
        if not obj.invited_by_id:
            obj.invited_by = request.user
        if not obj.expires_at:
            obj.expires_at = Invitation.default_expires_at(days=7)
        if not obj.token_hash:
            obj.token_hash = Invitation.hash_token(Invitation.build_token())
        super().save_model(request, obj, form, change)

    @admin.action(description="Provisionar acesso temporário (senha provisória)")
    def provision_temp_admin_access(self, request, queryset):
        total_ok = 0
        for invitation in queryset:
            try:
                user, temp_password = provision_admin_only_invitation(
                    invitation=invitation,
                    provisioned_by=request.user,
                )
            except ValueError as exc:
                self.message_user(
                    request,
                    f"{invitation.email}: {exc}",
                    level=messages.ERROR,
                )
                continue

            total_ok += 1
            self.message_user(
                request,
                (
                    f"{invitation.email} provisionado. "
                    f"Login: {user.email} | Senha temporária: {temp_password}"
                ),
                level=messages.WARNING,  # destaque no admin
            )

        if total_ok:
            self.message_user(
                request,
                f"{total_ok} convite(s) provisionado(s) com sucesso.",
                level=messages.SUCCESS,
            )


@admin.register(InvitationRole)
class InvitationRoleAdmin(SuperuserOnlyAdmin):
    list_display = ("id", "invitation", "role")
    list_filter = ("role",)
