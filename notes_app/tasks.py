import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import Note

logger = logging.getLogger("email_tasks")


@shared_task
def check_deadlines_task():
    curr_time = timezone.now()
    day_from_curr_time = curr_time + timedelta(days=1)
    notes_to_notify = Note.objects.filter(
        is_todo=True,
        deadline__isnull=False,
        deadline__gt=curr_time,
        deadline__lte=day_from_curr_time,
    )
    if notes_to_notify.exists():
        logger.info(f"Found {notes_to_notify.count()} notes to process")
        for note in notes_to_notify:
            send_notification_task.delay(note.pk)

    notes_to_archive = Note.objects.filter(
        is_todo=True, deadline__isnull=False, deadline__lt=curr_time
    )
    if notes_to_archive.exists():
        notes_to_archive.update(is_todo=False, deadline=None)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def send_notification_task(self, note_id: int) -> None:
    note = Note.objects.filter(pk=note_id).first()

    if not note or not note.user:
        return

    user = note.user

    recipient = user.email
    mail_subject = "Reminder: Don't forget about your note"
    message = (
        f"Hello {user.username},\n\n"
        f"You have a note that is due soon:\n\n"
        f"Title: {note.name}\n"
        f"Deadline: {note.deadline.strftime('%Y-%m-%d %H:%M')}\n\n"
        f"Don't forget to complete it on time!\n\n"
        f"Best regards,\n"
        f"Your Notes App"
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
        logger.info(f"Deadline notification successfully sent to user {recipient}.")
    except Exception as e:
        logger.error(f"Failed to send deadline email for user {recipient}. Retrying...")
        raise self.retry(exc=e)
