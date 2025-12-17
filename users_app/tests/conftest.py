import io

import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from users_app.models import Profile


@pytest.fixture
def unsaved_user(db):
    user = User(username="pradivliany@example.com", email="pradivliany@example.com")
    user.set_password("Super786")
    return user


@pytest.fixture
def user_with_profile(db):
    user = User.objects.create_user(
        username="pradivliany@example.com",
        email="pradivliany@example.com",
        password="Super786",
    )
    profile, _ = Profile.objects.get_or_create(user=user)
    return user, profile


@pytest.fixture
def fake_img_file():
    buffer = io.BytesIO()
    Image.new("RGB", (300, 300), (0, 255, 0)).save(buffer, format="PNG")
    return SimpleUploadedFile("test.png", buffer.getvalue(), content_type="image/png")
