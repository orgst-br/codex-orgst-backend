from __future__ import annotations

from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from django.contrib.admin.sites import AdminSite

from apps.accounts.admin import ProfileAdmin
from apps.accounts.models import InvitationStatus, Profile
from apps.accounts.services import (
    accept_invitation,
    create_invitation,
    validate_invitation_token,
)
from apps.accounts.views import _can_create_invitation


class AccountsUnitTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        self.inviter = SimpleNamespace(id=1, email="cofounder@orgst.dev")

    def tearDown(self):
        pass

    def test_create_invitation_links_email_and_roles(self):
        with patch("apps.accounts.services.Invitation") as invitation_cls, patch(
            "apps.accounts.services.Role"
        ) as role_cls:
            fake_inv = Mock()
            fake_inv.roles = Mock()

            invitation_cls.build_token.return_value = "plain-token"
            invitation_cls.hash_token.return_value = "hashed-token"
            invitation_cls.default_expires_at.return_value = "expires-at"
            invitation_cls._default_manager.create.return_value = fake_inv
            role_cls._default_manager.filter.return_value = ["mentor_role", "mentorado_role"]

            created = create_invitation.__wrapped__(
                invited_by=self.inviter,
                email="NOVO@ORGST.DEV ",
                role_keys=["mentor", "mentorado"],
                expires_in_days=7,
            )

            self.assertEqual(created.token, "plain-token")
            invitation_cls._default_manager.create.assert_called_once()
            fake_inv.roles.add.assert_called_once_with("mentor_role", "mentorado_role")


    def test_validate_invitation_expired_returns_none_and_marks_expired(self):
        with patch("apps.accounts.services.Invitation") as invitation_cls:
            fake_inv = Mock(status=InvitationStatus.PENDING)
            fake_inv.is_expired.return_value = True

            invitation_cls.hash_token.return_value = "hashed"
            invitation_cls._default_manager.filter.return_value.first.return_value = (
                fake_inv
            )

            result = validate_invitation_token(token="plain")

            self.assertIsNone(result)
            self.assertEqual(fake_inv.status, InvitationStatus.EXPIRED)
            fake_inv.save.assert_called_once()

    def test_create_invitation_links_email_and_roles(self):
        with patch("apps.accounts.services.Invitation") as invitation_cls, patch(
            "apps.accounts.services.Role"
        ) as role_cls:
            fake_inv = Mock()
            fake_inv.roles = Mock()

            invitation_cls.build_token.return_value = "plain-token"
            invitation_cls.hash_token.return_value = "hashed-token"
            invitation_cls.default_expires_at.return_value = "expires-at"
            invitation_cls._default_manager.create.return_value = fake_inv
            role_cls._default_manager.filter.return_value = ["mentor_role", "mentorado_role"]

            created = create_invitation.__wrapped__(
                invited_by=self.inviter,
                email="NOVO@ORGST.DEV ",
                role_keys=["mentor", "mentorado"],
                expires_in_days=7,
            )

            self.assertEqual(created.token, "plain-token")
            invitation_cls._default_manager.create.assert_called_once()
            fake_inv.roles.add.assert_called_once_with("mentor_role", "mentorado_role")

    def test_can_create_invitation_permissions(self):
        user_super = SimpleNamespace(
            is_authenticated=True,
            is_staff=False,
            is_superuser=True,
            user_roles=Mock(),
        )
        user_admin = SimpleNamespace(
            is_authenticated=True,
            is_staff=False,
            is_superuser=False,
            user_roles=Mock(),
        )
        user_admin.user_roles.filter.return_value.exists.return_value = True

        user_mentor = SimpleNamespace(
            is_authenticated=True,
            is_staff=True,
            is_superuser=False,
            user_roles=Mock(),
        )
        user_mentor.user_roles.filter.return_value.exists.return_value = False

        self.assertTrue(_can_create_invitation(user_super))
        self.assertTrue(_can_create_invitation(user_admin))
        self.assertFalse(_can_create_invitation(user_mentor))


class ProfileAdminUnitTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.site = AdminSite()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        self.admin = ProfileAdmin(Profile, self.site)

    def tearDown(self):
        pass

    def _request(self, *, is_superuser: bool, user_id: int = 1):
        user = SimpleNamespace(
            is_superuser=is_superuser,
            is_staff=not is_superuser,
            is_authenticated=True,
            id=user_id,
            user_roles=Mock(),
        )
        return SimpleNamespace(user=user)

    @patch("apps.accounts.admin._is_profile_staff", return_value=True)
    def test_has_module_permission_profile_staff(self, _is_profile_staff):
        req = self._request(is_superuser=False)
        self.assertTrue(self.admin.has_module_permission(req))

    @patch("apps.accounts.admin._is_profile_staff", return_value=False)
    def test_has_module_permission_denied_for_non_staff_non_superuser(
        self, _is_profile_staff
    ):
        req = self._request(is_superuser=False)
        self.assertFalse(self.admin.has_module_permission(req))

    @patch("apps.accounts.admin._is_profile_staff", return_value=True)
    @patch("django.contrib.admin.options.ModelAdmin.get_queryset")
    def test_get_queryset_profile_staff_only_own(
        self, super_get_queryset, _is_profile_staff
    ):
        req = self._request(is_superuser=False, user_id=77)
        fake_qs = Mock()
        super_get_queryset.return_value = fake_qs

        result = self.admin.get_queryset(req)

        fake_qs.filter.assert_called_once_with(user=req.user)
        self.assertIs(result, fake_qs.filter.return_value)

    @patch("apps.accounts.admin._is_profile_staff", return_value=False)
    @patch("django.contrib.admin.options.ModelAdmin.get_queryset")
    def test_get_queryset_non_allowed_returns_none_queryset(
        self, super_get_queryset, _is_profile_staff
    ):
        req = self._request(is_superuser=False, user_id=77)
        fake_qs = Mock()
        super_get_queryset.return_value = fake_qs

        result = self.admin.get_queryset(req)

        fake_qs.none.assert_called_once()
        self.assertIs(result, fake_qs.none.return_value)

    @patch("apps.accounts.admin._is_profile_staff", return_value=True)
    def test_has_change_permission_profile_staff_only_own(self, _is_profile_staff):
        req = self._request(is_superuser=False, user_id=10)
        own_obj = SimpleNamespace(user_id=10)
        other_obj = SimpleNamespace(user_id=11)

        self.assertTrue(self.admin.has_change_permission(req, obj=own_obj))
        self.assertFalse(self.admin.has_change_permission(req, obj=other_obj))

    def test_has_change_permission_superuser_always_true(self):
        req = self._request(is_superuser=True, user_id=10)
        obj = SimpleNamespace(user_id=999)
        self.assertTrue(self.admin.has_change_permission(req, obj=obj))

    def test_has_add_permission_only_superuser(self):
        self.assertTrue(self.admin.has_add_permission(self._request(is_superuser=True)))
        self.assertFalse(
            self.admin.has_add_permission(self._request(is_superuser=False))
        )

    def test_has_delete_permission_only_superuser(self):
        self.assertTrue(
            self.admin.has_delete_permission(self._request(is_superuser=True))
        )
        self.assertFalse(
            self.admin.has_delete_permission(self._request(is_superuser=False))
        )
