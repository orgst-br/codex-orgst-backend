from django.contrib.auth import get_user_model
from ninja import File, Router
from ninja.errors import HttpError
from ninja.files import UploadedFile

from apps.accounts.models import Profile

from .models import Skill
from .schemas import (
    MemberCardOut,
    MemberDetailOut,
    ProfilePatchIn,
    SkillOut,
    UserSkillIn,
)
from .services import get_member, list_members, replace_user_skills

User = get_user_model()
router = Router(tags=["community"])


def _avatar_url(request, profile):
    if profile and getattr(profile, "avatar", None) and hasattr(profile.avatar, "url"):
        return request.build_absolute_uri(profile.avatar.url)
    return None


@router.get("/skills", response=list[SkillOut])
def list_skills(request, category: str | None = None, q: str | None = None):
    qs = Skill.objects.all().order_by("name")
    if category:
        qs = qs.filter(category=category)
    if q:
        qs = qs.filter(name__icontains=q)
    return qs


@router.get("/members", response=list[MemberCardOut])
def members(
    request,
    q: str | None = None,
    role: str | None = None,
    skills: str | None = None,
):
    skill_list = [s.strip() for s in skills.split(",") if s.strip()] if skills else None
    users = list_members(q=q, role=role, skills=skill_list)

    out = []
    for u in users:
        profile = getattr(u, "profile", None)
        out.append(
            {
                "id": u.id,
                "email": u.email,
                "display_name": profile.display_name if profile else u.username,
                "avatar_url": _avatar_url(request, profile),
                "roles": [ur.role.key for ur in u.user_roles.all()],
                "skills": [us.skill.name for us in u.skills.all()],
            }
        )
    return out


router.get("/members/{user_id}", response=MemberDetailOut)


def member_detail(request, user_id: int):
    u = get_member(user_id=user_id)
    if not u:
        raise HttpError(404, "MEMBER_NOT_FOUND")

    p = getattr(u, "profile", None)
    if not p:
        raise HttpError(404, "PROFILE_NOT_FOUND")

    return {
        "id": u.id,
        "email": u.email,
        "display_name": p.display_name,
        "avatar_url": _avatar_url(request, p),
        "birth_date": p.birth_date,
        "profession": p.profession,
        "bio": p.bio,
        "location": p.location,
        "github_url": p.github_url,
        "linkedin_url": p.linkedin_url,
        "roles": [ur.role.key for ur in u.user_roles.all()],
        "skills": [
            {
                "skill": {
                    "id": us.skill.id,
                    "name": us.skill.name,
                    "category": us.skill.category,
                    "created_at": us.skill.created_at,
                },
                "level": us.level,
                "years_exp": us.years_exp,
                "can_mentor": us.can_mentor,
            }
            for us in u.skills.all()
        ],
    }


@router.patch("/members/{user_id}/profile")
def patch_profile(request, user_id: int, payload: ProfilePatchIn):
    if not request.user.is_authenticated:
        raise HttpError(401, "AUTH_REQUIRED")
    if request.user.id != user_id and not request.user.is_staff:
        raise HttpError(403, "FORBIDDEN")

    profile = Profile.objects.filter(user_id=user_id).first()
    if not profile:
        raise HttpError(404, "PROFILE_NOT_FOUND")

    changed = []

    for field in (
        "display_name",
        "birth_date",
        "profession",
        "bio",
        "location",
        "github_url",
        "linkedin_url",
    ):
        value = getattr(payload, field)
        if value is not None:
            setattr(profile, field, value.strip() if isinstance(value, str) else value)
            changed.append(field)

    if changed:
        changed.append("updated_at")
        profile.save(update_fields=changed)

    return {"ok": True}


@router.put("/members/{user_id}/skills")
def put_member_skills(request, user_id: int, payload: list[UserSkillIn]):
    if not request.user.is_authenticated:
        raise HttpError(401, "AUTH_REQUIRED")
    if request.user.id != user_id and not request.user.is_staff:
        raise HttpError(403, "FORBIDDEN")

    user = User.objects.filter(id=user_id).first()
    if not user:
        raise HttpError(404, "MEMBER_NOT_FOUND")

    replace_user_skills(user=user, items=[p.dict() for p in payload])
    return {"ok": True}


@router.post("/members/{user_id}/avatar")
def upload_avatar(request, user_id: int, file: UploadedFile = File(...)):  # noqa: B008
    if not request.user.is_authenticated:
        raise HttpError(401, "AUTH_REQUIRED")
    if request.user.id != user_id and not request.user.is_staff:
        raise HttpError(403, "FORBIDDEN")

    profile = Profile.objects.filter(user_id=user_id).first()
    if not profile:
        raise HttpError(404, "PROFILE_NOT_FOUND")

    # validação básica
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HttpError(400, "INVALID_IMAGE")

    if file.size and file.size > 5 * 1024 * 1024:
        raise HttpError(400, "IMAGE_TOO_LARGE")

    profile.avatar.save(file.name, file, save=True)

    return {"ok": True, "avatar_url": _avatar_url(request, profile)}
