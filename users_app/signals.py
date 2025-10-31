from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    """
    Automatically creates or updates a Profile whenever a User is saved.
    - On creation: creates a new Profile.
    - On update: saves the existing Profile.
    """
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()
