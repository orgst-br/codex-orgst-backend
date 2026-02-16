from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from apps.docs import services
from apps.docs.models import DocumentVersion, DocumentVisibility

User = get_user_model()


class ServicesVisibilityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="u1", email="u1@test.com", password="x"
        )
        cls.other = User.objects.create_user(
            username="u2", email="u2@test.com", password="x"
        )
        cls.staff = User.objects.create_user(
            username="staff", email="staff@test.com", password="x"
        )
        cls.staff.is_staff = True
        cls.staff.save(update_fields=["is_staff"])

    def test_can_view_document_requires_auth(self):
        doc = services.create_document(title="Doc", body_md="x", created_by=self.user)
        anon = AnonymousUser()
        self.assertFalse(services.can_view_document(anon, doc))

    def test_staff_can_view_anything(self):
        doc = services.create_document(
            title="Priv",
            body_md="x",
            created_by=self.user,
            visibility=DocumentVisibility.PRIVATE,
        )
        self.assertTrue(services.can_view_document(self.staff, doc))

    def test_community_any_authenticated(self):
        doc = services.create_document(
            title="Pub",
            body_md="x",
            created_by=self.other,
            visibility=DocumentVisibility.COMMUNITY,
        )
        self.assertTrue(services.can_view_document(self.user, doc))

    def test_private_only_creator(self):
        doc = services.create_document(
            title="Priv",
            body_md="x",
            created_by=self.other,
            visibility=DocumentVisibility.PRIVATE,
        )
        self.assertFalse(services.can_view_document(self.user, doc))
        self.assertTrue(services.can_view_document(self.other, doc))

    def test_mentors_only_uses_roles(self):
        doc = services.create_document(
            title="Mentors",
            body_md="x",
            created_by=self.other,
            visibility=DocumentVisibility.MENTORS_ONLY,
        )

        with patch("apps.docs.services.user_has_any_role", return_value=True):
            self.assertTrue(services.can_view_document(self.user, doc))

        with patch("apps.docs.services.user_has_any_role", return_value=False):
            self.assertFalse(services.can_view_document(self.user, doc))


class ServicesCreateAndVersionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="u1", email="u1@test.com", password="x"
        )

    def test_create_document_creates_v1_and_tags(self):
        doc = services.create_document(
            title="Meu Doc",
            body_md="# hello",
            created_by=self.user,
            tag_names=[" python ", "django", "", "   "],
        )

        self.assertTrue(
            DocumentVersion.objects.filter(document=doc, version_number=1).exists()
        )
        self.assertEqual(
            sorted(list(doc.tags.values_list("name", flat=True))),
            ["django", "python"],
        )

    def test_create_document_unique_slug_suffixes(self):
        d1 = services.create_document(
            title="Mesmo Título", body_md="a", created_by=self.user
        )
        d2 = services.create_document(
            title="Mesmo Título", body_md="b", created_by=self.user
        )

        self.assertNotEqual(d1.slug, d2.slug)
        self.assertTrue(d2.slug.startswith(d1.slug))

    def test_add_version_increments(self):
        doc = services.create_document(title="Doc", body_md="v1", created_by=self.user)

        v2 = services.add_version(document=doc, body_md="v2", authored_by=self.user)
        v3 = services.add_version(document=doc, body_md="v3", authored_by=self.user)

        self.assertEqual(v2.version_number, 2)
        self.assertEqual(v3.version_number, 3)

    def test_list_documents_respects_visibility(self):
        other = User.objects.create_user(
            username="u2", email="u2@test.com", password="x"
        )

        d_public = services.create_document(
            title="Public", body_md="a", created_by=other
        )
        d_private_other = services.create_document(
            title="Private",
            body_md="b",
            created_by=other,
            visibility=DocumentVisibility.PRIVATE,
        )
        d_private_user = services.create_document(
            title="Mine",
            body_md="c",
            created_by=self.user,
            visibility=DocumentVisibility.PRIVATE,
        )

        docs = services.list_documents(
            user=self.user, q=None, tag=None, project_id=None
        )
        ids = {d.id for d in docs}

        self.assertIn(d_public.id, ids)
        self.assertIn(d_private_user.id, ids)
        self.assertNotIn(d_private_other.id, ids)

    def test_list_documents_tag_filter(self):
        doc = services.create_document(
            title="Com Tag", body_md="x", created_by=self.user, tag_names=["Python"]
        )

        docs = services.list_documents(
            user=self.user, q=None, tag="python", project_id=None
        )
        self.assertEqual([d.id for d in docs], [doc.id])

        docs = services.list_documents(
            user=self.user, q=None, tag="django", project_id=None
        )
        self.assertEqual(docs, [])
