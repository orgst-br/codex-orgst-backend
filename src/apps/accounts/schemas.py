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
    name: str
    role_keys: list[str]


class InvitationCreateOut(Schema):
    id: str
    email: str
    name: str
    status: str
    expires_at: datetime
    invite_token: str | None = None  # token puro só em debug


class InvitationValidateOut(Schema):
    valid: bool
    email: str | None = None
    name: str | None = None
    expires_at: datetime | None = None


class TokenIn(Schema):
    # pode ser email OU username (te dá flexibilidade sem migration)
    identifier: str
    password: str


class TokenOut(Schema):
    access: str


class InvitationAcceptIn(Schema):
    invite_token: str
    password: str
    display_name: str
    bio: str | None = None
    github_url: str
    linkedin_url: str


class InvitationAcceptOut(Schema):
    user_id: str
    email: str
    access: str
    pid: int
    roles: list[str] = Field(default_factory=list)
