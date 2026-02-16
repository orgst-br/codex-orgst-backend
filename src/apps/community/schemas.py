from datetime import date, datetime

from ninja import Schema


class SkillOut(Schema):
    id: int
    name: str
    category: str
    created_at: datetime


class UserSkillIn(Schema):
    skill_id: int
    level: int = 1
    years_exp: int = 0
    can_mentor: bool = False


class UserSkillOut(Schema):
    skill: SkillOut
    level: int
    years_exp: int
    can_mentor: bool


class MemberCardOut(Schema):
    id: int
    email: str
    display_name: str
    avatar_url: str | None = None
    roles: list[str]
    skills: list[str]  # nomes simples pra card


class MemberDetailOut(Schema):
    id: int
    email: str
    display_name: str
    avatar_url: str | None = None

    birth_date: date | None = None
    profession: str | None = None
    bio: str | None = None
    location: str | None = None
    github_url: str | None = None
    linkedin_url: str | None = None

    roles: list[str]
    skills: list[UserSkillOut]


class ProfilePatchIn(Schema):
    display_name: str | None = None
    birth_date: date | None = None
    profession: str | None = None
    bio: str | None = None
    location: str | None = None
    github_url: str | None = None
    linkedin_url: str | None = None
