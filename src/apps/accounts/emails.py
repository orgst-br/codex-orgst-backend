from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.timezone import localtime

from .models import Invitation


def build_invite_link(token: str) -> str:
    base_url = settings.FRONTEND_INVITE_URL.rstrip("/")
    return f"{base_url}?token={token}"


def send_invitation_email(*, invitation: Invitation, raw_token: str) -> None:
    invite_link = build_invite_link(raw_token)
    context = {
        "name": invitation.invitee_name,
        "invite_link": invite_link,
        "expires_at": localtime(invitation.expires_at).strftime("%d/%m/%Y %H:%M"),
    }

    subject = "ORGST DEV_PLATFORM v1.0.0"
    text_body = render_to_string("emails/invite.txt", context)
    html_body = render_to_string("emails/invite.html", context)

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[invitation.email],
    )
    message.attach_alternative(html_body, "text/html")
    message.send(fail_silently=False)
