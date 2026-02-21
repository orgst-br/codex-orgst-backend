from datetime import datetime

from ninja import Schema
from pydantic import Field


class MeOut(Schema):
    id: str
    username: str
    email: str | None = None
    display_name: str | None = None
    roles: list[str] = Field(default_factory=list)
    is_staff: bool = False


class InvitationCreateIn(Schema):
    email: str
    role_keys: list[str]
    expires_in_days: int = 7


class InvitationCreateOut(Schema):
    id: str
    email: str
    status: str
    expires_at: datetime
    invite_token: str  # token puro (retornar só aqui)


class InvitationValidateOut(Schema):
    valid: bool
    email: str | None = None
    role_keys: list[str] = Field(default_factory=list)
    expires_at: datetime | None = None


class TokenIn(Schema):
    # pode ser email OU username (te dá flexibilidade sem migration)
    identifier: str
    password: str


class TokenOut(Schema):
    access: str


class InvitationAcceptIn(Schema):
    token: str
    password: str
    display_name: str


class InvitationAcceptOut(Schema):
    user_id: str
    email: str
