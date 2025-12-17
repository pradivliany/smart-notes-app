import pytest
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import Client
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from users_app.tokens import password_reset_token, profile_activation_token


@pytest.mark.django_db
class TestSignupUserView:
    url = reverse("users_app:signup")

    def test_get_for_authenticated_user(self, client: Client, user_with_profile):
        user, profile = user_with_profile
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302
        assert response.headers["Location"] == reverse("notes_app:note_list")

    def test_get_for_anonymous_user(self, client: Client):
        response = client.get(self.url)
        assert response.status_code == 200
        assert "form" in response.context

    def test_post_valid_data(self, mocker, client: Client):
        mock_delay = mocker.patch("users_app.tasks.send_activation_email_task.delay")
        mocker.patch("django.db.transaction.on_commit", side_effect=lambda func: func())
        response = client.post(
            self.url,
            data={
                "first_name": "Yaroslav",
                "last_name": "Pradyvlianyi",
                "email": "pradivliany@example.com",
                "password1": "Super187",
                "password2": "Super187",
            },
        )
        created_user = User.objects.get(email="pradivliany@example.com")
        assert response.status_code == 302
        assert response.headers["Location"].startswith(reverse("users_app:login"))
        mock_delay.assert_called_once_with(created_user.pk, "testserver")

    def test_post_invalid_data(self, client: Client):
        response = client.post(
            self.url,
            data={
                "first_name": "",
                "last_name": "wro",
                "email": "pradivliany",
                "password1": "18",
                "password2": "Super18",
            },
        )
        assert response.status_code == 200
        assert response.context["form"].errors
        assert not User.objects.filter(email="pradivliany").exists()

    def test_post_authenticated_user(self, client: Client, user_with_profile):
        user, profile = user_with_profile
        client.force_login(user)
        response = client.post(self.url, data={})
        assert response.status_code == 302
        assert response.headers["Location"] == reverse("notes_app:note_list")


@pytest.mark.django_db
class TestLogoutUserView:
    url = reverse("users_app:logout")

    def test_logout_redirect_authenticated_user(
        self, client: Client, user_with_profile
    ):
        user, profile = user_with_profile
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302
        assert response.headers["Location"] == reverse("welcome")
        assert not response.wsgi_request.user.is_authenticated

    def test_logout_redirect_anonymous_user(self, client: Client):
        response = client.get(self.url)
        assert response.status_code == 302
        assert response.headers["Location"].startswith(reverse("welcome"))


@pytest.mark.django_db
class TestLoginUserView:
    url = reverse("users_app:login")

    def test_get_for_authenticated_user(self, client: Client, user_with_profile):
        user, profile = user_with_profile
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302
        assert response.headers["Location"].startswith(reverse("notes_app:note_list"))

    def test_get_for_anonymous_user(self, client: Client):
        response = client.get(self.url)
        assert response.status_code == 200
        assert "form" in response.context

    def test_post_valid_data_with_confirmed_profile(
        self, client: Client, user_with_profile
    ):
        user, profile = user_with_profile
        profile.is_confirmed = True
        profile.save()

        response = client.post(
            self.url,
            data={"username": "pradivliany@example.com", "password": "Super786"},
        )

        assert response.status_code == 302
        assert response.headers["Location"].startswith(reverse("notes_app:note_list"))
        assert response.wsgi_request.user.is_authenticated
        assert profile.is_confirmed

    def test_post_valid_data_with_not_confirmed_profile(
        self, client: Client, user_with_profile
    ):
        user, profile = user_with_profile

        response = client.post(
            self.url,
            data={"username": "pradivliany@example.com", "password": "Super786"},
        )

        messages_list = list(get_messages(response.wsgi_request))

        assert response.status_code == 302
        assert response.headers["Location"].startswith(reverse("users_app:profile"))
        assert response.wsgi_request.user.is_authenticated
        assert not profile.is_confirmed
        assert len(messages_list) == 1

    def test_post_invalid_data(self, client: Client):
        response = client.post(
            self.url, data={"username": "empty", "password": "wrong"}
        )
        assert response.status_code == 200
        assert "form" in response.context
        assert response.context["form"].errors
        assert not response.wsgi_request.user.is_authenticated

    def test_post_authenticated_user(self, client: Client, user_with_profile):
        user, profile = user_with_profile
        client.force_login(user)
        response = client.post(self.url, data={})

        assert response.status_code == 302
        assert response.headers["Location"].startswith(reverse("notes_app:note_list"))


@pytest.mark.django_db
class TestProfileView:
    url = reverse("users_app:profile")

    def test_get_anonymous_user(self, client: Client):
        response = client.get(self.url)
        assert response.status_code == 302
        assert response.headers["Location"].startswith(reverse("users_app:login"))

    def test_get_user_authenticated(self, client: Client, user_with_profile):
        user, profile = user_with_profile
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert "curr_profile" in response.context


@pytest.mark.django_db
class TestEditProfileView:
    url = reverse("users_app:edit_profile")

    def test_get_anonymous_user(self, client: Client):
        response = client.get(self.url)
        assert response.status_code == 302
        assert response.headers["Location"].startswith(reverse("users_app:login"))

    def test_get_authenticated_user(self, client: Client, user_with_profile):
        user, profile = user_with_profile
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert "form" in response.context

    def test_post_authenticated_user_valid_data(
        self, client: Client, fake_img_file, user_with_profile
    ):
        user, profile = user_with_profile
        client.force_login(user)
        response = client.post(
            self.url,
            data={"bio": "My new test bio.", "avatar": fake_img_file},
        )
        messages_list = list(get_messages(response.wsgi_request))

        assert response.status_code == 302
        assert response.headers["Location"].startswith(reverse("users_app:profile"))
        assert len(messages_list) == 1

        profile.refresh_from_db()

        assert profile.bio == "My new test bio."
        assert "test" in profile.avatar.name

    def test_post_authenticated_user_invalid_data(
        self, client: Client, user_with_profile
    ):
        user, profile = user_with_profile
        client.force_login(user)
        response = client.post(self.url, data={"bio": "a"})
        assert response.status_code == 200
        assert "form" in response.context
        assert response.context["form"].errors

    def test_post_anonymous_user(self, client: Client):
        response = client.post(self.url, data={})
        assert response.status_code == 302
        assert response.headers["Location"].startswith(reverse("users_app:login"))


@pytest.mark.django_db
class TestResetPasswordDoneView:
    def test_get(self, client: Client):
        response = client.get(reverse("users_app:reset_password_done"))
        assert response.status_code == 200


@pytest.mark.django_db
class TestResetPasswordView:
    url = reverse("users_app:reset_password")

    def test_get(self, client: Client):
        response = client.get(self.url)
        assert response.status_code == 200
        assert "form" in response.context

    def test_post_valid_email_existing_user(
        self, mocker, client: Client, user_with_profile
    ):
        user, profile = user_with_profile
        mock_delay = mocker.patch(
            "users_app.tasks.send_reset_password_email_task.delay"
        )

        response = client.post(self.url, data={"email": "pradivliany@example.com"})
        messages_list = list(get_messages(response.wsgi_request))

        assert response.status_code == 302
        assert response.headers["Location"].startswith(
            reverse("users_app:reset_password_done")
        )
        assert len(messages_list) == 1
        mock_delay.assert_called_once_with(user.pk, "testserver")

    def test_post_valid_email_nonexisting_user(self, client: Client):
        response = client.post(self.url, data={"email": "notexist@example.com"})
        messages_list = list(get_messages(response.wsgi_request))
        assert response.status_code == 302
        assert response.headers["Location"].startswith(
            reverse("users_app:reset_password_done")
        )
        assert len(messages_list) >= 1

    def test_post_invalid_data(self, client: Client):
        response = client.post(self.url, data={"email": ""})
        messages_list = list(get_messages(response.wsgi_request))
        assert response.status_code == 200
        assert len(messages_list) == 1
        assert "form" in response.context
        assert response.context["form"].errors


@pytest.mark.django_db
class TestActivateUserView:
    def test_get_valid_uidb_token(self, client: Client, user_with_profile):
        user, profile = user_with_profile

        uidb = urlsafe_base64_encode(force_bytes(user.pk))
        token = profile_activation_token.make_token(user)
        url = reverse("users_app:activate", args=[uidb, token])

        response = client.get(url)
        messages_list = list(get_messages(response.wsgi_request))
        profile.refresh_from_db()

        assert response.status_code == 302
        assert response.headers["Location"].startswith(reverse("notes_app:note_list"))
        assert len(messages_list) == 1
        assert profile.is_confirmed is True

    def test_get_invalid_uidb(self, client: Client, user_with_profile):
        user, profile = user_with_profile

        uidb = urlsafe_base64_encode(force_bytes(9999))
        token = profile_activation_token.make_token(user)
        url = reverse("users_app:activate", args=[uidb, token])

        response = client.get(url)
        messages_list = list(get_messages(response.wsgi_request))

        assert response.status_code == 302
        assert response.headers["Location"].startswith(reverse("users_app:signup"))
        assert len(messages_list) == 1
        assert profile.is_confirmed is False

    def test_get_invalid_token(self, client: Client, user_with_profile):
        user, profile = user_with_profile

        uidb = urlsafe_base64_encode(force_bytes(user.pk))
        token = "invalid-token"
        url = reverse("users_app:activate", args=[uidb, token])

        response = client.get(url)
        messages_list = list(get_messages(response.wsgi_request))

        assert response.status_code == 302
        assert response.headers["Location"].startswith(reverse("users_app:signup"))
        assert len(messages_list) == 1
        assert profile.is_confirmed is False


@pytest.mark.django_db
class TestResetPasswordConfirmView:
    def test_get_valid_uidb_token(self, client: Client, user_with_profile):
        user, profile = user_with_profile
        uidb = urlsafe_base64_encode(force_bytes(user.pk))
        token = password_reset_token.make_token(user)
        url = reverse("users_app:reset_password_confirm", args=[uidb, token])
        response = client.get(url)

        assert response.status_code == 200
        assert "form" in response.context

    def test_get_invalid_uidb(self, client: Client, user_with_profile):
        user, profile = user_with_profile
        uidb = urlsafe_base64_encode(force_bytes(9999))
        token = password_reset_token.make_token(user)
        url = reverse("users_app:reset_password_confirm", args=[uidb, token])
        response = client.get(url)
        messages_list = list(get_messages(response.wsgi_request))

        assert response.status_code == 302
        assert len(messages_list) == 1
        assert response.headers["Location"].startswith(reverse("users_app:login"))

    def test_get_invalid_token(self, client: Client, user_with_profile):
        user, profile = user_with_profile
        uidb = urlsafe_base64_encode(force_bytes(user.pk))
        token = "invalid-token"
        url = reverse("users_app:reset_password_confirm", args=[uidb, token])
        response = client.get(url)
        messages_list = list(get_messages(response.wsgi_request))

        assert response.status_code == 302
        assert len(messages_list) == 1
        assert response.headers["Location"].startswith(reverse("users_app:login"))

    def test_post_valid_uidb_token_password(self, client: Client, user_with_profile):
        user, profile = user_with_profile
        uidb = urlsafe_base64_encode(force_bytes(user.pk))
        token = password_reset_token.make_token(user)
        url = reverse("users_app:reset_password_confirm", args=[uidb, token])
        response = client.post(
            url, data={"password1": "Super765", "password2": "Super765"}
        )
        messages_list = list(get_messages(response.wsgi_request))
        user.refresh_from_db()

        assert response.status_code == 302
        assert response.headers["Location"].startswith(reverse("users_app:login"))
        assert len(messages_list) == 1
        assert user.check_password("Super765")

    def test_post_invalid_form(self, client: Client, user_with_profile):
        user, profile = user_with_profile
        uidb = urlsafe_base64_encode(force_bytes(user.pk))
        token = password_reset_token.make_token(user)
        url = reverse("users_app:reset_password_confirm", args=[uidb, token])
        response = client.post(
            url, data={"password1": "Super765", "password2": "Super766"}
        )

        assert response.status_code == 200
        assert "form" in response.context
