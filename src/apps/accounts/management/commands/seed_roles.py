from django.core.management.base import BaseCommand

from apps.accounts.models import Role

DEFAULT_ROLES = [
    ("cofounder", "Co-founder"),
    ("admin", "Admin"),
    ("mentor", "Mentor"),
    ("coach", "Coach"),
    ("mentorado", "Mentorado"),
]


class Command(BaseCommand):
    help = "Seed default roles for Orgst"

    def handle(self, *args, **options):
        created = 0
        for key, label in DEFAULT_ROLES:
            _, was_created = Role.objects.get_or_create(
                key=key, defaults={"label": label}
            )
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(f"Roles seeded. Created={created}"))
