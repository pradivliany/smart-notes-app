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
    """
    Checks all notes and performs two actions:

    1. Finds notes with a deadline within 24 hours and schedules email reminders.
    2. Archives notes whose deadlines have already passed.
    """
    curr_time = timezone.now()
    day_from_curr_time = curr_time + timedelta(days=1)

    notes = Note.objects.filter(is_todo=True, deadline__isnull=False).select_related(
        "user"
    )

    if not notes:
        logger.info("No notes with deadlines found.")
        return

    to_notify, to_archive = [], []

    for note in notes:
        if note.deadline <= curr_time:
            to_archive.append(note.pk)
        elif note.deadline <= day_from_curr_time:
            to_notify.append(note)

    if to_archive:
        Note.objects.filter(pk__in=to_archive).update(is_todo=False, deadline=None)
        logger.info(f"Archived {len(to_archive)} expired to-do notes.")

    if to_notify:
        logger.info(f"Found {len(to_notify)} to-do notes to process")
        for note in to_notify:
            send_notification_task.delay(note.pk)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def send_notification_task(self, note_id: int) -> None:
    """
    Sends an email reminder for an upcoming note deadline.
    Retries up to 3 times if sending fails.
    """
    try:
        note = Note.objects.select_related("user").get(pk=note_id)
    except Note.DoesNotExist:
        logger.warning(f"Note with ID {note_id} not found")
        return

    if not note.user or not note.user.email:
        logger.warning(f"Skipping note {note_id}: missing user or email.")
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
