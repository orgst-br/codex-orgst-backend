from django.contrib import admin

from apps.kanban.models import Board, Column, Tag, Task, TaskComment, TaskTag


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    """Admin configuration for Project boards (1:1 with Project)."""

    list_display = ("id", "project", "name", "created_at")
    search_fields = ("name",)
    list_select_related = ("project",)


@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    """Admin configuration for Board columns with explicit ordering via position."""

    list_display = (
        "id",
        "board",
        "name",
        "position",
        "wip_limit",
        "color",
        "is_archived",
    )
    list_filter = ("is_archived", "board")
    search_fields = ("name",)
    list_select_related = ("board",)
    ordering = ("board_id", "position")


class TaskTagInline(admin.TabularInline):
    """Inline editor for tags attached to a task."""

    model = TaskTag
    extra = 0


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Admin configuration for tasks ordered within a column by position."""

    list_display = (
        "id",
        "project",
        "column",
        "position",
        "title",
        "assignee",
        "priority",
        "due_date",
        "created_at",
    )
    list_filter = ("project", "column", "priority", "due_date")
    search_fields = ("title", "description")
    list_select_related = ("project", "column", "assignee", "created_by")
    ordering = ("column_id", "position")
    inlines = [TaskTagInline]


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    """Admin configuration for task comments."""

    list_display = ("id", "task", "author", "created_at")
    search_fields = ("content",)
    list_select_related = ("task", "author")
    ordering = ("-created_at",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin configuration for project-scoped tags."""

    list_display = ("id", "project", "name", "color")
    search_fields = ("name",)
    list_select_related = ("project",)


@admin.register(TaskTag)
class TaskTagAdmin(admin.ModelAdmin):
    """Admin configuration for Task <-> Tag relation."""

    list_display = ("id", "task", "tag")
    list_select_related = ("task", "tag")
