from datetime import timedelta

from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Invitation, InvitationStatus, Profile, Role, User
from apps.accounts.services import provision_admin_only_invitation
from orgst.common.middleware import ForcePasswordChangeMiddleware


class AdminOnlyInviteFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.role_admin = Role.objects.create(key="admin", label="Admin")
        cls.role_mentor = Role.objects.create(key="mentor", label="Mentor")
        cls.role_mentorado = Role.objects.create(key="mentorado", label="Mentorado")

        cls.provisioner = User.objects.create_user(
            username="owner",
            email="owner@orgst.dev",
            password="secret123",
            is_staff=True,
            is_superuser=True,
        )

    def test_provision_creates_staff_user_with_must_change_password(self):
        inv = Invitation.objects.create(
            email="novo@orgst.dev",
            invited_by=self.provisioner,
            status=InvitationStatus.PENDING,
            expires_at=timezone.now() + timedelta(days=1),
        )
        inv.roles.add(self.role_mentor)

        user, temp_password = provision_admin_only_invitation(
            invitation=inv,
            provisioned_by=self.provisioner,
        )

        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.must_change_password)
        self.assertTrue(user.check_password(temp_password))
        self.assertTrue(Profile.objects.filter(user=user).exists())
        self.assertTrue(user.user_roles.filter(role__key="mentor").exists())

        inv.refresh_from_db()
        self.assertEqual(inv.status, InvitationStatus.ACCEPTED)
        self.assertEqual(inv.accepted_by_id, user.id)

    def test_provision_expired_invitation_raises(self):
        inv = Invitation.objects.create(
            email="expira@orgst.dev",
            invited_by=self.provisioner,
            status=InvitationStatus.PENDING,
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        inv.roles.add(self.role_mentor)

        with self.assertRaises(ValueError):
            provision_admin_only_invitation(
                invitation=inv,
                provisioned_by=self.provisioner,
            )

        inv.refresh_from_db()
        self.assertEqual(inv.status, InvitationStatus.EXPIRED)

    def test_provision_requires_mentor_or_mentorado_role(self):
        inv = Invitation.objects.create(
            email="semrole@orgst.dev",
            invited_by=self.provisioner,
            status=InvitationStatus.PENDING,
            expires_at=timezone.now() + timedelta(days=1),
        )
        inv.roles.add(self.role_admin)

        with self.assertRaises(ValueError):
            provision_admin_only_invitation(
                invitation=inv,
                provisioned_by=self.provisioner,
            )


class ForcePasswordChangeMiddlewareTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="mentor1",
            email="mentor1@orgst.dev",
            password="temp12345",
            is_staff=True,
            must_change_password=True,
        )

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = ForcePasswordChangeMiddleware(
            lambda request: HttpResponse("OK")
        )

    def test_redirects_admin_root_when_must_change_password(self):
        request = self.factory.get("/admin/")
        request.user = self.user

        response = self.middleware(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("admin_force_password_change"))

    def test_allows_force_password_change_url(self):
        request = self.factory.get(reverse("admin_force_password_change"))
        request.user = self.user

        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)
