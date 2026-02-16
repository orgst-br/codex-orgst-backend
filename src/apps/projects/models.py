from __future__ import annotations

from django.conf import settings
from django.db import models

from orgst.common.models import TimeStampedModel


class ProjectStatus(models.TextChoices):
    """Lifecycle de um projeto dentro da comunidade."""

    ACTIVE = "active", "Active"
    PAUSED = "paused", "Paused"
    DONE = "done", "Done"


class Project(TimeStampedModel):
    """
    Represents a workspace container for collaborative work.

    A Project groups members, a single Kanban Board (1:1), and all related artifacts
    such as tasks and tags.

    Invariants:
        - A project is created by a user (`created_by`).
        - Membership is tracked via `ProjectMember`.
        - A single board is associated via `Board.project` (OneToOne) in the kanban app.
    """

    name = models.CharField(max_length=160, unique=True)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=ProjectStatus.choices, default=ProjectStatus.ACTIVE
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="projects_created",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_projects",
    )

    class Meta:
        indexes = [models.Index(fields=["created_by"])]

    def __str__(self) -> str:
        return str(self.name)


class ProjectMember(models.Model):
    """
    Represents a workspace container for collaborative work.

    A Project groups members, a single Kanban Board (1:1), and all related artifacts
    such as tasks and tags.

    Invariants:
        - A project is created by a user (`created_by`).
        - Membership is tracked via `ProjectMember`.
        - A single board is associated via `Board.project` (OneToOne) in the kanban app.
    """

    ROLE_OWNER = "owner"
    ROLE_ADMIN = "admin"
    ROLE_MEMBER = "member"

    ROLE_CHOICES = [
        (ROLE_OWNER, "Owner"),
        (ROLE_ADMIN, "Admin"),
        (ROLE_MEMBER, "Member"),
    ]

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_memberships",
    )
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "user"], name="uniq_project_member"
            ),
        ]
        indexes = [
            models.Index(fields=["project", "user"]),
        ]

    def __str__(self) -> str:
        """Return a concise membership representation for debugging/admin."""
        return f"{self.user_id} -> {self.project_id} ({self.role})"
