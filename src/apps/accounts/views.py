from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import HttpRequest
from ninja import Router
from ninja.errors import HttpError

from .auth import create_access_token
from .schemas import (
    InvitationAcceptIn,
    InvitationAcceptOut,
    InvitationCreateIn,
    InvitationCreateOut,
    InvitationValidateOut,
    MeOut,
    TokenIn,
    TokenOut,
)
from .services import accept_invitation, create_invitation, validate_invitation_token

router = Router(tags=["accounts"])
User = get_user_model()


def _can_create_invitation(user) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    return user.user_roles.filter(role__key__in=["admin", "cofounder"]).exists()


@router.get("/me", response=MeOut)
def api_me(request: HttpRequest):
    user = request.user

    # Com auth global, isso quase nunca roda sem user válido,
    # mas fica defensivo caso alguém use esse router sem auth no futuro
    if not getattr(user, "is_authenticated", False):
        raise HttpError(401, "UNAUTHORIZED")

    # Profile pode não existir dependendo do fluxo (ex.: usuário criado via admin)
    display_name = None
    profile = getattr(user, "profile", None)
    if profile:
        display_name = getattr(profile, "display_name", None)

    roles = list(
        user.user_roles.select_related("role").values_list("role__key", flat=True)
    )

    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "display_name": display_name,
        "roles": roles,
        "is_staff": bool(user.is_staff),
    }


@router.post("/auth/token", auth=None, response=TokenOut)
def api_token(request: HttpRequest, payload: TokenIn):
    identifier = payload.identifier.strip()

    user = (
        User.objects.filter(
            Q(email__iexact=identifier) | Q(username__iexact=identifier)
        )
        .only("id", "is_active", "password", "email", "username")
        .first()
    )

    if not user or not user.is_active or not user.check_password(payload.password):
        raise HttpError(401, "INVALID_CREDENTIALS")

    return {"access": create_access_token(user)}


@router.post("/invitations", response=InvitationCreateOut)
def api_create_invitation(request: HttpRequest, payload: InvitationCreateIn):
    if not _can_create_invitation(request.user):
        raise HttpError(403, "FORBIDDEN")

    created = create_invitation(
        invited_by=request.user,
        email=payload.email,
        invitee_name=payload.name,
        role_keys=payload.role_keys,
    )

    inv = created.invitation
    return {
        "id": str(inv.id),
        "email": inv.email,
        "name": inv.invitee_name,
        "status": inv.status,
        "expires_at": inv.expires_at,
        "invite_token": created.token if settings.DEBUG else None,
    }


@router.get("/invitations/validate", auth=None, response=InvitationValidateOut)
def api_validate_invitation(request: HttpRequest, token: str):
    inv = validate_invitation_token(token=token)
    if not inv:
        return {"valid": False}

    return {
        "valid": True,
        "email": inv.email,
        "name": inv.invitee_name,
        "expires_at": inv.expires_at,
    }


@router.post("/register", auth=None, response=InvitationAcceptOut)
def api_register_from_invitation(request: HttpRequest, payload: InvitationAcceptIn):
    try:
        user = accept_invitation(
            token=payload.invite_token,
            password=payload.password,
            display_name=payload.display_name,
            bio=payload.bio,
            github_url=payload.github_url,
            linkedin_url=payload.linkedin_url,
        )
    except ValueError:
        raise HttpError(400, "INVALID_OR_EXPIRED_INVITATION") from None

    roles = list(
        user.user_roles.select_related("role").values_list("role__key", flat=True)
    )

    return {
        "user_id": str(user.id),
        "email": user.email,
        "access": create_access_token(user),
        "pid": user.id,
        "roles": roles,
    }


@router.post("/invitations/accept", auth=None, response=InvitationAcceptOut)
def api_accept_invitation(request: HttpRequest, payload: InvitationAcceptIn):
    try:
        user = accept_invitation(
            token=payload.invite_token,
            password=payload.password,
            display_name=payload.display_name,
            bio=payload.bio,
            github_url=payload.github_url,
            linkedin_url=payload.linkedin_url,
        )
    except ValueError:
        raise HttpError(400, "INVALID_OR_EXPIRED_INVITATION") from None

    roles = list(
        user.user_roles.select_related("role").values_list("role__key", flat=True)
    )

    return {
        "user_id": str(user.id),
        "email": user.email,
        "access": create_access_token(user),
        "pid": user.id,
        "roles": roles,
    }
