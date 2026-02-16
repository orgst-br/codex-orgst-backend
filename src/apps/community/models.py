from __future__ import annotations

from django.conf import settings
from django.db import models

from orgst.common.models import TimeStampedModel


class SkillCategory(models.TextChoices):
    BACKEND = "backend", "Backend"
    FRONTEND = "frontend", "Frontend"
    DEVOPS = "devops", "DevOps"
    QA = "qa", "QA"
    SQL = "sql", "SQL"
    PM = "pm", "PM"
    DESIGN = "design", "Design"
    OTHER = "other", "Other"


class Skill(TimeStampedModel):
    name = models.CharField(max_length=80, unique=True)
    category = models.CharField(
        max_length=20, choices=SkillCategory.choices, default=SkillCategory.OTHER
    )

    class Meta:
        indexes = [models.Index(fields=["category", "name"])]

    def __str__(self) -> str:
        return self.name


class UserSkill(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="skills"
    )
    skill = models.ForeignKey(
        Skill, on_delete=models.CASCADE, related_name="user_skills"
    )
    level = models.PositiveSmallIntegerField(default=1)
    years_exp = models.PositiveSmallIntegerField(default=0)
    can_mentor = models.BooleanField(default=False)

    class Meta:
        unique_together = [("user", "skill")]
        indexes = [models.Index(fields=["can_mentor", "level"])]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.skill.name}"
