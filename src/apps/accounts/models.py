from __future__ import annotations

import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.crypto import salted_hmac

from orgst.common.models import TimeStampedModel


class User(AbstractUser):
    """
    Custom User simples (mantém username) mas com email único.
    Se no futuro quiser login por email, dá pra evoluir com calma.
    """

    email = models.EmailField(unique=True)

    def __str__(self) -> str:
        return self.email or self.username


class Profile(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    display_name = models.CharField(max_length=160)

    # comunidade (fase 2)

    birth_date = models.DateField(null=True, blank=True)
    profession = models.CharField(max_length=120, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    location = models.CharField(max_length=120, null=True, blank=True)

    github_url = models.URLField(max_length=250, null=True, blank=True)
    linkedin_url = models.URLField(max_length=250, null=True, blank=True)

    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)

    def __str__(self) -> str:
        return str(self.display_name)


class Role(TimeStampedModel):
    """
    Mantém papéis como entidades (mentor/coach/mentorado/admin/cofounder),
    evitando depender de Django Groups por enquanto.
    """

    key = models.SlugField(max_length=50, unique=True)  # exemplo
    label = models.CharField(max_length=80)

    def __str__(self) -> str:
        return str(self.key)


class UserRole(TimeStampedModel):
    """
    Mantém papéis como entidades (mentor/coach/mentorado/admin/cofounder),
    evitando depender de Django Groups por enquanto.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_roles"
    )  # noqa
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_users")  # noqa

    class Meta:
        unique_together = [("user", "role")]

    def __str__(self) -> str:
        return f"{self.user} - {self.role}"


class InvitationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    EXPIRED = "expired", "Expired"
    REVOKED = "revoked", "Revoked"


class Invitation(TimeStampedModel):
    email = models.EmailField()
    token_hash = models.CharField(max_length=64, unique=True)
    status = models.CharField(
        max_length=20,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING,
    )  # noqa

    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sent_invitations",
    )
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="accepted_invitations",
    )

    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)

    roles = models.ManyToManyField(
        Role, through="InvitationRole", related_name="invitations"
    )

    class Meta:
        indexes = [
            models.Index(fields=["email", "status"]),
            models.Index(fields=["expires_at"]),
        ]

    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    @staticmethod
    def hash_token(token: str) -> str:
        return salted_hmac("orgst.invitation", token).hexdigest()

    @classmethod
    def build_token(cls) -> str:
        return secrets.token_urlsafe(32)

    @classmethod
    def default_expires_at(cls, days: int = 7):
        return timezone.now() + timedelta(days=days)


class InvitationRole(models.Model):
    invitation = models.ForeignKey(Invitation, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        unique_together = [("invitation", "role")]
