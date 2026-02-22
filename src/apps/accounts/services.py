from __future__ import annotations

import secrets
import string
from collections.abc import Iterable
from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from .models import Invitation, InvitationStatus, Profile, Role, User

ALLOWED_ADMIN_ONLY_ROLES = {"mentor", "mentorado"}


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


def _generate_temp_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


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
    is_profile_staff = bool(invite_role_keys & ALLOWED_ADMIN_ONLY_ROLES)

    user = User.objects.create(
        username=_make_username(inv.email),
        email=inv.email,
        is_staff=is_profile_staff,
        is_superuser=False,
        is_active=True,
        must_change_password=False,  # requer campo no model User
    )
    user.set_password(password)
    user.save(update_fields=["password"])

    Profile.objects.create(user=user, display_name=display_name)

    for role in inv.roles.all():
        user.user_roles.create(role=role)

    inv.status = InvitationStatus.ACCEPTED
    inv.accepted_by = user
    inv.accepted_at = timezone.now()
    inv.save(update_fields=["status", "accepted_by", "accepted_at", "updated_at"])

    return user


def provision_admin_only_invitation(
    *, invitation: Invitation, provisioned_by: User
) -> tuple[User, str]:
    if invitation.status != InvitationStatus.PENDING:
        raise ValueError("INVITATION_NOT_PENDING")

    if invitation.is_expired():
        invitation.status = InvitationStatus.EXPIRED
        invitation.save(update_fields=["status", "updated_at"])
        raise ValueError("INVITATION_EXPIRED")

    with transaction.atomic():
        role_keys = set(invitation.roles.values_list("key", flat=True))
        selected_keys = role_keys & ALLOWED_ADMIN_ONLY_ROLES
        if not selected_keys:
            raise ValueError("INVITATION_ROLE_REQUIRED")

        email = invitation.email.lower().strip()
        user = User.objects.filter(email__iexact=email).first()

        if not user:
            user = User.objects.create(
                username=_make_username(email),
                email=email,
                is_active=True,
                is_staff=True,
                is_superuser=False,
                must_change_password=True,  # requer campo no model User
            )

        temp_password = _generate_temp_password()
        user.is_staff = True
        user.is_superuser = False
        user.is_active = True
        user.must_change_password = True
        user.set_password(temp_password)
        user.save(
            update_fields=[
                "password",
                "is_staff",
                "is_superuser",
                "is_active",
                "must_change_password",
            ]
        )

        Profile.objects.get_or_create(
            user=user,
            defaults={"display_name": email.split("@")[0]},
        )

        for role in Role.objects.filter(key__in=selected_keys):
            user.user_roles.get_or_create(role=role)

        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_by = user
        invitation.accepted_at = timezone.now()
        if not invitation.invited_by_id:
            invitation.invited_by = provisioned_by
            invitation.save(
                update_fields=[
                    "status",
                    "accepted_by",
                    "accepted_at",
                    "invited_by",
                    "updated_at",
                ]
            )
        else:
            invitation.save(
                update_fields=["status", "accepted_by", "accepted_at", "updated_at"]
            )

        return user, temp_password
