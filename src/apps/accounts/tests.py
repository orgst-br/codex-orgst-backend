import json
import re

from django.core import mail
from django.test import Client, TransactionTestCase, override_settings

from apps.accounts.auth import create_access_token
from apps.accounts.models import Invitation, InvitationStatus, Profile, Role, User


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    FRONTEND_INVITE_URL="https://weorgst.com/invite",
)
class InvitationFlowTests(TransactionTestCase):
    def setUp(self):
        self.client = Client()
        self.manager = User.objects.create_user(
            username="tiago",
            email="tiago@example.com",
            password="adminpass123",
            is_superuser=True,
            is_staff=True,
        )
        self.role = Role.objects.create(key="mentorado", label="Mentorado")
        self.auth_header = {
            "HTTP_AUTHORIZATION": f"Bearer {create_access_token(self.manager)}"
        }

    def _extract_token_from_email(self) -> str:
        body = mail.outbox[-1].body
        match = re.search(r"https://weorgst\.com/invite\?token=([a-f0-9]+)", body)
        self.assertIsNotNone(match)
        return match.group(1)

    def test_create_invitation_sends_email_and_exposes_validation_data(self):
        response = self.client.post(
            "/api/v1/accounts/invitations",
            data=json.dumps(
                {
                    "email": "novo@orgst.com",
                    "name": "Novo Membro",
                    "role_keys": [self.role.key],
                }
            ),
            content_type="application/json",
            **self.auth_header,
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["email"], "novo@orgst.com")
        self.assertEqual(payload["name"], "Novo Membro")

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("ORGST DEV_PLATFORM v1.0.0", mail.outbox[0].subject)
        self.assertIn("Novo Membro", mail.outbox[0].body)
        self.assertIn("https://weorgst.com/invite?token=", mail.outbox[0].body)
        invite_token = self._extract_token_from_email()

        validate_response = self.client.get(
            "/api/v1/accounts/invitations/validate",
            {"token": invite_token},
        )
        self.assertEqual(validate_response.status_code, 200)
        self.assertEqual(
            validate_response.json(),
            {
                "valid": True,
                "email": "novo@orgst.com",
                "name": "Novo Membro",
                "expires_at": payload["expires_at"],
            },
        )

    def test_register_from_invitation_creates_user_marks_invite_as_used_and_returns_jwt(
        self,
    ):
        invitation_response = self.client.post(
            "/api/v1/accounts/invitations",
            data=json.dumps(
                {
                    "email": "new.member@orgst.com",
                    "name": "New Member",
                    "role_keys": [self.role.key],
                }
            ),
            content_type="application/json",
            **self.auth_header,
        )
        self.assertEqual(invitation_response.status_code, 200)
        token = self._extract_token_from_email()

        register_response = self.client.post(
            "/api/v1/accounts/register",
            data=json.dumps(
                {
                    "invite_token": token,
                    "password": "senhaforte123",
                    "display_name": "New Member",
                    "bio": "Backend volunteer",
                    "github_url": "https://github.com/new-member",
                    "linkedin_url": "https://linkedin.com/in/new-member",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(register_response.status_code, 200)
        payload = register_response.json()
        self.assertTrue(payload["access"])
        self.assertEqual(payload["pid"], int(payload["user_id"]))
        self.assertEqual(payload["roles"], ["mentorado"])

        user = User.objects.get(email="new.member@orgst.com")
        invitation = Invitation.objects.get(email="new.member@orgst.com")
        profile = Profile.objects.get(user=user)

        self.assertEqual(profile.display_name, "New Member")
        self.assertEqual(profile.bio, "Backend volunteer")
        self.assertEqual(profile.github_url, "https://github.com/new-member")
        self.assertEqual(profile.linkedin_url, "https://linkedin.com/in/new-member")
        self.assertEqual(invitation.status, InvitationStatus.ACCEPTED)
        self.assertIsNotNone(invitation.used_at)

        second_attempt = self.client.post(
            "/api/v1/accounts/register",
            data=json.dumps(
                {
                    "invite_token": token,
                    "password": "outrasenha123",
                    "display_name": "Duplicado",
                    "bio": "Should fail",
                    "github_url": "https://github.com/duplicado",
                    "linkedin_url": "https://linkedin.com/in/duplicado",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(second_attempt.status_code, 400)
