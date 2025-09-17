from django.contrib.auth.models import AbstractUser
from django.db import models
from PIL import Image


class UserProfile(AbstractUser):
    avatar = models.ImageField(
        default="avatars/default_avatar.jpg", upload_to="avatars/"
    )
    bio = models.CharField(max_length=500, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username}"

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
            print(f"Error manipulating avatar image: {e}")
