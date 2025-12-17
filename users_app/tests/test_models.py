import pytest
from django.test import override_settings
from PIL import Image

from users_app.models import Profile


@pytest.mark.django_db
def test_profile_is_created_with_default_fields_after_user_creation(
    tmp_path, unsaved_user
):
    """
    Verifies that after User is created:
    1. Profile is created via signal
    2. The Profile fields have their default values:
        - is_confirmed is False
        - bio is None
        - avatar is set to default_avatar.png
    """
    avatars_dir = tmp_path / "avatars"
    avatars_dir.mkdir(parents=True)
    img = Image.new("RGB", (2, 2), (255, 0, 255))
    img.save(avatars_dir / "default_avatar.png", format="PNG")

    with override_settings(MEDIA_ROOT=tmp_path):
        user = unsaved_user
        user.save()
        profile = user.profile

        assert profile is not None
        assert profile.is_confirmed is False
        assert profile.bio is None
        assert profile.avatar.name.endswith("default_avatar.png")


@pytest.mark.django_db
def test_profile_str_returns_username(unsaved_user):
    """
    Verifies that the __str__ dunder method of the Profile model
    returns the username of the associated User object.
    """
    user = unsaved_user
    user.save()
    profile = user.profile
    assert str(profile) == user.username


@pytest.mark.django_db
def test_profile_avatar_is_resized_on_save(tmp_path, unsaved_user, fake_img_file):
    """
    Verifies the avatar resizing logic: ensures a large image is reduced
    to the maximum size (100x100) when the profile is saved.
    """
    avatars_dir = tmp_path / "avatars"
    avatars_dir.mkdir(parents=True, exist_ok=True)
    default_avatar = Image.new("RGB", (2, 2), (255, 0, 255))
    default_avatar.save(avatars_dir / "default_avatar.png", format="PNG")

    with override_settings(MEDIA_ROOT=tmp_path):
        user = unsaved_user
        user.save()
        profile = user.profile

        profile.avatar = fake_img_file
        profile.save()

        resized_img = Image.open(profile.avatar)
        assert resized_img.height <= 100 and resized_img.width <= 100


@pytest.mark.django_db
def test_profile_is_deleted_after_user_deleted(unsaved_user):
    """
    Profile should be deleted when its User is deleted (cascade).
    """
    user = unsaved_user
    user.save()
    user_pk = user.pk
    user.delete()

    assert not Profile.objects.filter(user_id=user_pk).exists()
