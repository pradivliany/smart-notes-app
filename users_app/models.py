import logging

from django.contrib.auth.models import User
from django.db import models
from PIL import Image

logger = logging.getLogger("models_errors")


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(
        default="avatars/default_avatar.png", upload_to="avatars/"
    )
    bio = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        try:
            if self.avatar and self.avatar.path:
                img = Image.open(self.avatar.path)
                if img.height > 100 or img.width > 100:
                    max_size = (100, 100)
                    img.thumbnail(max_size)
                    img.save(self.avatar.path)
        except Exception as e:
            logger.error(f"Error manipulating avatar image: {e}")
