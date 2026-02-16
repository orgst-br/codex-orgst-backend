from __future__ import annotations

from collections.abc import Iterable

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Prefetch, Q

from apps.accounts.models import UserRole

from .models import Skill, UserSkill

User = get_user_model()


def list_members(*, q: str | None, role: str | None, skills: list[str] | None):
    qs = User.objects.select_related("profile").prefetch_related(
        Prefetch("user_roles", queryset=UserRole.objects.select_related("role")),
        Prefetch("skills", queryset=UserSkill.objects.select_related("skill")),
    )

    if q:
        qs = qs.filter(Q(email__icontains=q) | Q(profile__display_name__icontains=q))

    if role:
        qs = qs.filter(user_roles__role__key=role)

    if skills:
        # skills por nome (ex: skills=python,sql)
        qs = qs.filter(skills__skill__name__in=skills).distinct()

    return qs.order_by("id")


def get_member(*, user_id: int):
    return (
        User.objects.select_related("profile")
        .prefetch_related(
            Prefetch("user_roles", queryset=UserRole.objects.select_related("role")),
            Prefetch("skills", queryset=UserSkill.objects.select_related("skill")),
        )
        .filter(id=user_id)
        .first()
    )


@transaction.atomic
def replace_user_skills(*, user: User, items: Iterable[dict]):
    """
    Substitui o conjunto inteiro de skills do usuário.
    (PUT idempotente, simples pro front)
    """
    UserSkill.objects.filter(user=user).delete()

    skill_ids = [i["skill_id"] for i in items]
    skills_map = {s.id: s for s in Skill.objects.filter(id__in=skill_ids)}

    created = []
    for i in items:
        skill = skills_map.get(i["skill_id"])
        if not skill:
            continue
        created.append(
            UserSkill(
                user=user,
                skill=skill,
                level=max(1, min(int(i.get("level", 1)), 5)),
                years_exp=max(0, int(i.get("years_exp", 0))),
                can_mentor=bool(i.get("can_mentor", False)),
            )
        )
    UserSkill.objects.bulk_create(created)
