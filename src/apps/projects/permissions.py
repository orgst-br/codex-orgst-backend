from apps.projects.models import ProjectMember


def is_project_member(user, project_id: int) -> bool:
    """
    Check whether a user is a member of the given project.

    Args:
        user: Authenticated user instance.
        project_id: Target project ID.

    Returns:
        True if the user has a membership row for the project; otherwise False.
    """
    return ProjectMember.objects.filter(project_id=project_id, user=user).exists()


def can_write_project(user, project_id: int) -> bool:
    """
    Check whether a user has write permissions over a project.

    Policy (phase 4):
        - owner/admin can write
        - member is read-only

    Args:
        user: Authenticated user instance.
        project_id: Target project ID.

    Returns:
        True if the user role is owner/admin for the project; otherwise False.
    """
    return ProjectMember.objects.filter(
        project_id=project_id,
        user=user,
        role__in=[ProjectMember.ROLE_OWNER, ProjectMember.ROLE_ADMIN],
    ).exists()
