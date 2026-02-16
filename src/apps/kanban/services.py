from __future__ import annotations

from django.db import transaction
from django.db.models import F

from apps.kanban.models import Board, Column, Task

DEFAULT_COLUMNS: list[tuple[str, int]] = [
    ("Backlog", 1),
    ("Doing", 2),
    ("Done", 3),
]


@transaction.atomic
def create_default_board(project) -> Board:
    """
    Create (or fetch) the default Kanban board for a project.

    Behavior:
        - Idempotent: if the board already exists, returns it without duplicating columns.
        - When creating a new board, also creates default columns:
          Backlog (1), Doing (2), Done (3).

    Args:
        project: Project instance.

    Returns:
        The existing or newly created Board.
    """
    board, created = Board.objects.get_or_create(
        project=project, defaults={"name": "Board"}
    )
    if created:
        Column.objects.bulk_create(
            [
                Column(board=board, name=name, position=pos)
                for name, pos in DEFAULT_COLUMNS
            ]
        )
    return board


@transaction.atomic
def reorder_columns(board: Board, ordered_ids: list[int]) -> None:
    """
    Reorder columns in a board by applying the given ordered list of column IDs.

    Invariants enforced:
        - Only columns belonging to `board` can be reordered.
        - `ordered_ids` must match exactly the set of non-archived board columns.
        - Column positions are reassigned to be compact (1..N), with no gaps.

    Args:
        board: Board instance.
        ordered_ids: Column IDs in the desired final order.

    Raises:
        ValueError: if `ordered_ids` does not match the existing column set.
    """
    qs = (
        Column.objects.select_for_update()
        .filter(board=board, is_archived=False)
        .order_by("position")
    )
    existing_ids = list(qs.values_list("id", flat=True))

    if sorted(existing_ids) != sorted(ordered_ids):
        raise ValueError("ordered_ids must match existing column ids for this board")

    id_to_pos = {col_id: i + 1 for i, col_id in enumerate(ordered_ids)}

    cols = list(qs)
    for col in cols:
        new_pos = id_to_pos[col.id]
        if col.position != new_pos:
            col.position = new_pos

    Column.objects.bulk_update(cols, ["position"])


@transaction.atomic
def move_task(task_id: int, to_column_id: int, to_position: int) -> None:
    """
    Move a task to another column and/or position while keeping positions compact.

    This service implements the "position shift" strategy:
        - Remove the task from its current position (closing the gap).
        - Shift destination tasks to open a slot at `to_position`.
        - Place the task in the destination.

    Invariants enforced:
        - Task cannot be moved to a column from another project.
        - Within each column, positions remain compact (1..N) and unique.

    Args:
        task_id: ID of the task to move.
        to_column_id: Destination column ID.
        to_position: 1-based destination position.

    Raises:
        ValueError: if destination column belongs to another project or invalid position.
    """
    task = (
        Task.objects.select_for_update()
        .select_related("column", "project")
        .get(id=task_id)
    )
    to_column = (
        Column.objects.select_for_update()
        .select_related("board__project")
        .get(id=to_column_id)
    )

    if to_column.board.project_id != task.project_id:
        raise ValueError("cannot move task to a column from another project")

    if to_position < 1:
        raise ValueError("to_position must be >= 1")

    from_column_id = task.column_id
    from_position = task.position

    # Determine destination upper bound: len(dest)+1 if changing columns, else len(dest).
    dest_count = Task.objects.filter(column_id=to_column_id).count()
    max_pos = dest_count if from_column_id == to_column_id else dest_count + 1
    if to_position > max_pos:
        to_position = max_pos  # policy: clamp (alternatively, raise ValueError)

    if from_column_id == to_column_id and to_position == from_position:
        return

    # Close gap in the source column
    Task.objects.filter(column_id=from_column_id, position__gt=from_position).update(
        position=F("position") - 1
    )

    # Open slot in the destination column
    Task.objects.filter(column_id=to_column_id, position__gte=to_position).update(
        position=F("position") + 1
    )

    # Move task
    task.column_id = to_column_id
    task.position = to_position
    task.save(update_fields=["column", "position", "updated_at"])
