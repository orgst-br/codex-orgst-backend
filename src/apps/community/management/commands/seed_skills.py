from django.core.management.base import BaseCommand

from apps.community.models import Skill, SkillCategory

DEFAULT_SKILLS = [
    ("Python", SkillCategory.BACKEND),
    ("Django", SkillCategory.BACKEND),
    ("Flask", SkillCategory.BACKEND),
    ("FastAPI", SkillCategory.BACKEND),
    ("PostgreSQL", SkillCategory.SQL),
    ("Redis", SkillCategory.DEVOPS),
    ("Docker", SkillCategory.DEVOPS),
    ("Kubernetes", SkillCategory.DEVOPS),
    ("React", SkillCategory.FRONTEND),
    ("Next.js", SkillCategory.FRONTEND),
    ("TypeScript", SkillCategory.FRONTEND),
    ("QA", SkillCategory.QA),
]


class Command(BaseCommand):
    help = "Seed default skills for Orgst"

    def handle(self, *args, **options):
        created = 0
        for name, category in DEFAULT_SKILLS:
            _, was_created = Skill.objects.get_or_create(
                name=name, defaults={"category": category}
            )
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(f"Skills seeded. Created={created}"))
