from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .tokens import password_reset_token, profile_activation_token


def send_activation_email_task(request, user) -> None:
    """
    Generates a unique activation token for the given user and constructs an account
    activation link containing the token and the user's UID.

    Prepares the email subject and body, then sends the email using the configured
    SMTP backend.

    This function does not return any value.
    """
    domain = get_current_site(request).domain
    mail_subject = "Activate your account"
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = profile_activation_token.make_token(user)
    message = (
        f"Hello {user.username}, \n\n"
        f"Click the link below to activate your account:\n"
        f"http://{domain}/users/activate/{uid}/{token} \n\n"
        f"If you did not register, please ignore this email."
    )
    to_email = user.email

    # todo before production to make fail_silently=True
    send_mail(
        mail_subject,
        message,
        settings.EMAIL_HOST_USER,
        [
            to_email,
        ],
        fail_silently=False,
    )


def send_reset_password_email(request, user) -> None:
    """
    Generates a unique password reset token for the given user and constructs a
    password reset link containing the token and the user's UID.

    Prepares the email subject and body, then sends the email using the configured
    SMTP backend.

    This function does not return any value.
    """
    domain = get_current_site(request).domain
    mail_subject = "Reset your password"
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = password_reset_token.make_token(user)
    message = (
        f"Hello {user.username}, \n\n"
        f"Click the link below to reset your password:\n"
        f"http://{domain}/users/reset_password/confirm/{uid}/{token} \n\n"
        f"If you did not register, please ignore this email."
    )
    to_email = user.email

    # todo before production to make fail_silently=True
    send_mail(
        mail_subject,
        message,
        settings.EMAIL_HOST_USER,
        [
            to_email,
        ],
        fail_silently=False,
    )
