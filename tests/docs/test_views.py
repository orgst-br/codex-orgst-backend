from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from ninja.errors import HttpError

from apps.docs import services
from apps.docs.models import DocumentVisibility
from apps.docs.views import (
    api_add_version,
    api_create_doc,
    api_get_doc,
    api_list_docs,
    api_list_versions,
)

User = get_user_model()


class DummyRequest:
    def __init__(self, user):
        self.user = user


class PayloadCreate:
    def __init__(
        self,
        title,
        body_md,
        summary=None,
        visibility=DocumentVisibility.COMMUNITY,
        tags=None,
        project_id=None,
    ):
        self.title = title
        self.body_md = body_md
        self.summary = summary
        self.visibility = visibility
        self.tags = tags
        self.project_id = project_id


class PayloadVersion:
    def __init__(self, body_md):
        self.body_md = body_md


class DocsViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="u1", email="u1@test.com", password="x"
        )
        cls.other = User.objects.create_user(
            username="u2", email="u2@test.com", password="x"
        )

    def setUp(self):
        self.req_auth = DummyRequest(self.user)
        self.req_anon = DummyRequest(AnonymousUser())

    def test_list_docs_requires_auth(self):
        with self.assertRaises(HttpError) as ctx:
            api_list_docs(self.req_anon)
        self.assertEqual(ctx.exception.status_code, 401)

    def test_create_doc_requires_auth(self):
        with self.assertRaises(HttpError) as ctx:
            api_create_doc(self.req_anon, PayloadCreate("t", "md"))
        self.assertEqual(ctx.exception.status_code, 401)

    def test_create_doc_happy_path(self):
        out = api_create_doc(
            self.req_auth, PayloadCreate("Doc", "# md", tags=["python", "django"])
        )
        self.assertTrue(out["id"])
        self.assertEqual(out["title"], "Doc")
        self.assertEqual({t["name"] for t in out["tags"]}, {"python", "django"})

    def test_get_doc_404(self):
        with self.assertRaises(HttpError) as ctx:
            api_get_doc(self.req_auth, 999999)
        self.assertEqual(ctx.exception.status_code, 404)

    def test_get_doc_forbidden(self):
        doc = services.create_document(
            title="Priv",
            body_md="x",
            created_by=self.other,
            visibility=DocumentVisibility.PRIVATE,
        )
        with self.assertRaises(HttpError) as ctx:
            api_get_doc(self.req_auth, doc.id)
        self.assertEqual(ctx.exception.status_code, 403)

    def test_get_doc_happy_path(self):
        doc = services.create_document(title="Pub", body_md="x", created_by=self.user)
        out = api_get_doc(self.req_auth, doc.id)
        self.assertEqual(out["id"], doc.id)

    def test_list_versions_happy_path(self):
        doc = services.create_document(title="Doc", body_md="v1", created_by=self.user)
        services.add_version(document=doc, body_md="v2", authored_by=self.user)

        out = api_list_versions(self.req_auth, doc.id)
        self.assertEqual([v["version_number"] for v in out], [2, 1])

    def test_add_version_happy_path(self):
        doc = services.create_document(title="Doc", body_md="v1", created_by=self.user)
        out = api_add_version(self.req_auth, doc.id, PayloadVersion("v2"))
        self.assertEqual(out["version_number"], 2)
        self.assertEqual(out["authored_by_id"], self.user.id)
