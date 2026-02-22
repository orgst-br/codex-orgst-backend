from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from .models import Invitation, InvitationStatus, Profile, Role, User


@dataclass(frozen=True)
class CreatedInvitation:
    invitation: Invitation
    token: str  # token puro (retornar apenas na criação)


def _make_username(email: str) -> str:
    base = slugify(email.split("@")[0])[:25] or "user"
    candidate = base
    i = 0
    while User.objects.filter(username=candidate).exists():
        i += 1
        candidate = f"{base}{i}"[:30]
    return candidate


@transaction.atomic
def create_invitation(
    *, invited_by: User, email: str, role_keys: Iterable[str], expires_in_days: int = 7
) -> CreatedInvitation:
    token = Invitation.build_token()
    token_hash = Invitation.hash_token(token)

    inv = Invitation._default_manager.create(
        email=email.lower().strip(),
        token_hash=token_hash,
        invited_by=invited_by,
        status=InvitationStatus.PENDING,
        expires_at=Invitation.default_expires_at(expires_in_days),
    )

    roles = list(Role._default_manager.filter(key__in=list(role_keys)))
    inv.roles.add(*roles)

    return CreatedInvitation(invitation=inv, token=token)


def validate_invitation_token(*, token: str) -> Invitation | None:
    token_hash = Invitation.hash_token(token)
    inv = Invitation._default_manager.filter(token_hash=token_hash).first()
    if not inv:
        return None
    if inv.status != InvitationStatus.PENDING:
        return None
    if inv.is_expired():
        # opcional: atualizar status automaticamente
        inv.status = InvitationStatus.EXPIRED
        inv.save(update_fields=["status", "updated_at"])
        return None
    return inv


@transaction.atomic
def accept_invitation(*, token: str, password: str, display_name: str) -> User:
    inv = validate_invitation_token(token=token)
    if not inv:
        raise ValueError("INVALID_OR_EXPIRED_INVITATION")

    invite_role_keys = set(inv.roles.values_list("key", flat=True))
    profile_only_staff_roles = {"mentor", "mentorado"}
    is_profile_staff = bool(invite_role_keys & profile_only_staff_roles)

    user = User.objects.create(
        username=_make_username(inv.email),
        email=inv.email,
        is_staff=is_profile_staff,
        is_superuser=False,
        is_active=True,
    )
    user.set_password(password)
    user.save(update_fields=["password"])

    Profile.objects.create(user=user, display_name=display_name)

    # atribui roles
    for role in inv.roles.all():
        user.user_roles.create(role=role)

    inv.status = InvitationStatus.ACCEPTED
    inv.accepted_by = user
    inv.accepted_at = timezone.now()
    inv.save(update_fields=["status", "accepted_by", "accepted_at", "updated_at"])

    return user
