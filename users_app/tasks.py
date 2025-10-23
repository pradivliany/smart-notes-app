import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import User
from .tokens import password_reset_token, profile_activation_token

logger = logging.getLogger("email_tasks")


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def send_activation_email_task(self, user_id: int, domain: str) -> None:
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.warning(f"Task skipped. User with ID {user_id} not found.")
        return

    mail_subject = "Activate your account"
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = profile_activation_token.make_token(user)
    recipient = user.email
    message = (
        f"Hello {user.username},\n\n"
        f"Welcome to Notes App! 🎉\n\n"
        f"Please activate your account by clicking the link below:\n"
        f"http://{domain}/users/activate/{uid}/{token}\n\n"
        f"If you didn’t create an account, just ignore this message.\n\n"
        f"Best regards,\nThe Notes App Team"
    )

    try:
        send_mail(
            mail_subject,
            message,
            settings.EMAIL_HOST_USER,
            [
                recipient,
            ],
            fail_silently=False,
        )
        logger.info(
            f"Activation email successfully sent to user ID {user_id} ({recipient})."
        )
    except Exception as e:
        logger.error(f"Email failed for user {user_id}. Retrying...")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def send_reset_password_email_task(self, user_id: int, domain: str) -> None:
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.warning(f"User with ID {user_id} not found")
        return

    mail_subject = "Reset your password"
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = password_reset_token.make_token(user)
    recipient = user.email
    message = (
        f"Hello {user.username}, \n\n"
        f"Click the link below to reset your password:\n"
        f"http://{domain}/users/reset_password/confirm/{uid}/{token} \n\n"
        f"If you did not register, please ignore this email."
        f"Best regards,\nThe Notes App Team"
    )

    try:
        send_mail(
            mail_subject,
            message,
            settings.EMAIL_HOST_USER,
            [
                recipient,
            ],
            fail_silently=False,
        )
        logger.info(
            f"Password reset email successfully sent to user ID {user_id} ({recipient})."
        )
    except Exception as e:
        logger.error(f"Email failed for user {user_id}. Retrying...")
        raise self.retry(exc=e)
