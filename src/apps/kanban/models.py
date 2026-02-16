from django.conf import settings
from django.db import models

from apps.projects.models import Project


class Board(models.Model):
    """
    Represents the Kanban board for a project.

    Design decision:
        - Exactly one Board per Project (enforced by OneToOneField).

    Invariants:
        - Board lifecycle is tied to the Project (CASCADE).
        - Columns belong to the board and are ordered by `Column.position`.
    """

    project = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name="board"
    )
    name = models.CharField(max_length=120, default="Board")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        """Return a compact identifier for admin/debug."""
        return f"Board({self.project_id})"


class Column(models.Model):
    """
    Represents a column inside a Kanban Board.

    Ordering:
        - Columns are ordered by `position` (1..N, no gaps).
        - Uniqueness is enforced per board: (board, position).

    Optional constraints:
        - wip_limit: maximum number of tasks allowed in this column (if set).
        - color: UI hint.
        - is_archived: hides a column without deleting historical tasks (optional).

    Invariants:
        - (board, position) is unique.
        - `position` should be compact (1..N).
    """

    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="columns")
    name = models.CharField(max_length=80)
    position = models.PositiveIntegerField()
    wip_limit = models.PositiveIntegerField(null=True, blank=True)
    color = models.CharField(max_length=16, null=True, blank=True)
    is_archived = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["board", "position"], name="uniq_column_position"
            ),
            models.UniqueConstraint(fields=["board", "name"], name="uniq_column_name"),
        ]
        indexes = [models.Index(fields=["board", "position"])]

    def __str__(self) -> str:
        """Return a human-readable column identifier."""
        return f"{self.name} ({self.board_id})"


class Task(models.Model):
    """
    Represents a work item in a project's Kanban board.

    Ordering:
        - Tasks are ordered within a Column by `position` (1..N, no gaps).
        - Uniqueness is enforced per column: (column, position).

    Note:
        - `project` is stored redundantly (in addition to column->board->project)
          for query performance and integrity checks.
    """

    PRIORITY_LOW = 1
    PRIORITY_MEDIUM = 2
    PRIORITY_HIGH = 3
    PRIORITY_URGENT = 4

    PRIORITY_CHOICES = [
        (PRIORITY_LOW, "Low"),
        (PRIORITY_MEDIUM, "Medium"),
        (PRIORITY_HIGH, "High"),
        (PRIORITY_URGENT, "Urgent"),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    column = models.ForeignKey(Column, on_delete=models.CASCADE, related_name="tasks")
    position = models.PositiveIntegerField()

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks_assigned",
    )
    priority = models.PositiveSmallIntegerField(
        choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM
    )
    due_date = models.DateField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="tasks_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["column", "position"], name="uniq_task_position_in_column"
            ),
        ]
        indexes = [
            models.Index(fields=["column", "position"]),
            models.Index(fields=["project", "column"]),
        ]

    def __str__(self) -> str:
        """Return task title (useful for admin lists and debugging)."""
        return str(self.title)


class TaskComment(models.Model):
    """
    Represents a comment attached to a Task.

    Notes:
        - Comments are immutable in many systems; if you plan edits later,
          add updated_at and an edit flag.
    """

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="task_comments"
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Tag(models.Model):
    """
    Represents a label that can be attached to tasks within a Project.

    Scope:
        - Project-scoped tags (simple and sufficient for early stages).

    Invariants:
        - (project, name) is unique.
    """

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tags")
    name = models.CharField(max_length=60)
    color = models.CharField(max_length=16, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "name"], name="uniq_tag_per_project"
            ),
        ]

    def __str__(self) -> str:
        """Return the tag name for admin/debug."""
        return str(self.name)


class TaskTag(models.Model):
    """
    Many-to-many bridge between Task and Tag.

    Invariants:
        - (task, tag) is unique.
    """

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="task_tags")
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name="tag_tasks")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["task", "tag"], name="uniq_task_tag"),
        ]
