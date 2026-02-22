from django.contrib.auth import get_user_model
from django.http import HttpRequest
from ninja import Router

from .schemas import (
    InvitationAcceptIn,
    InvitationAcceptOut,
    InvitationCreateIn,
    InvitationCreateOut,
    InvitationValidateOut,
)
from .services import accept_invitation, create_invitation, validate_invitation_token

router = Router(tags=["accounts"])
User = get_user_model()


@router.post("/invitations", response=InvitationCreateOut)
def api_create_invitation(request: HttpRequest, payload: InvitationCreateIn):
    # MVP: usa usuário autenticado via Django Admin session.
    # Depois trocamos para JWT facilmente.
    if not request.user.is_authenticated:
        # Ninja vai serializar isso em 500 se levantar Exception genérica;
        # depois a gente padroniza erro.
        raise PermissionError("AUTH_REQUIRED")

    created = create_invitation(
        invited_by=request.user,
        email=payload.email,
        role_keys=payload.role_keys,
        expires_in_days=payload.expires_in_days,
    )

    inv = created.invitation
    return {
        "id": str(inv.id),
        "email": inv.email,
        "status": inv.status,
        "expires_at": inv.expires_at,
        "invite_token": created.token,
    }


@router.get("/invitations/validate", response=InvitationValidateOut)
def api_validate_invitation(request: HttpRequest, token: str):
    inv = validate_invitation_token(token=token)
    if not inv:
        return {"valid": False}

    return {
        "valid": True,
        "email": inv.email,
        "role_keys": [r.key for r in inv.roles.all()],
        "expires_at": inv.expires_at,
    }


@router.post("/invitations/accept", response=InvitationAcceptOut)
def api_accept_invitation(request: HttpRequest, payload: InvitationAcceptIn):
    user = accept_invitation(
        token=payload.token,
        password=payload.password,
        display_name=payload.display_name,
    )
    return {"user_id": str(user.id), "email": user.email}
