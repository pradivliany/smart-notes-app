import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.datastructures import MultiValueDict

from users_app.forms import (
    EmailForm,
    LoginForm,
    PasswordConfirmForm,
    ProfileForm,
    SignUpForm,
)


class TestEmailForm:
    @pytest.mark.parametrize(
        "email, expected",
        [
            ("pradivliany@example.com", True),
            ("a" * 251 + "@b.c", False),
            ("a@b.", False),
        ],
    )
    def test_is_valid(self, email, expected):
        """
        Verifies EmailForm validation for different types of test emails.
        """
        form = EmailForm({"email": email})
        assert form.is_valid() == expected


class TestLoginForm:
    def test_widgets_modified(self):
        """
        Verifies that the LoginForm widgets have the correct custom HTML attributes.
        """
        form = LoginForm()

        username_attrs = form.fields["username"].widget.attrs
        password_attrs = form.fields["password"].widget.attrs

        assert (
            username_attrs["class"] == "form-control"
            and username_attrs["placeholder"] == "Your email"
        )
        assert (
            password_attrs["class"] == "form-control"
            and password_attrs["placeholder"] == "Password"
        )


class TestPasswordConfirmForm:
    @pytest.mark.parametrize(
        "pass1, pass2, expected",
        [
            ("great187", "great187", True),
            ("great18", "great17", False),
            ("short", "short", False),
            ("superlong" * 8, "superlong" * 8, False),
        ],
    )
    def test_is_valid(self, pass1, pass2, expected):
        """
        Verifies that the PasswordConfirmForm validation checks:
        1. Passwords match (pass1 == pass2).
        2. Passwords meet minimum length requirements.
        3. Passwords do not exceed maximum length limits.
        """
        form = PasswordConfirmForm({"password1": pass1, "password2": pass2})
        assert form.is_valid() == expected


class TestSignUpForm:
    @pytest.mark.parametrize(
        "name, surname, email, pass1, pass2, expected",
        [
            ("John", "Doe", "john@example.com", "super718", "super718", True),
            ("J", "Doe", "john@example.com", "super718", "super718", False),
            ("John", "D", "john@example.com", "super718", "super718", False),
            ("John", "Doe", "john@", "super718", "super718", False),
            ("John", "Doe", "john@example.com", "super718", "super719", False),
            ("John", "Doe", "john@example.com", "short", "short", False),
            ("John", "Doe", "a@.c", "super718", "super718", False),
        ],
    )
    def test_is_valid(self, name, surname, email, pass1, pass2, expected):
        """
        Verifies full validation logic for the SignUpForm, testing multiple
        form fields.
        """
        form = SignUpForm(
            {
                "first_name": name,
                "last_name": surname,
                "email": email,
                "password1": pass1,
                "password2": pass2,
            }
        )
        assert form.is_valid() == expected

    @pytest.mark.django_db
    def test_save_method(self):
        """
        Verifies the functionality of the SignUpForm's custom save() method.
        """
        form = SignUpForm(
            {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "password1": "super718",
                "password2": "super718",
            }
        )
        user = form.save()
        assert user.pk is not None
        assert user.username == "john@example.com"
        assert user.email == "john@example.com"


class TestProfileForm:
    @pytest.mark.parametrize(
        "bio, avatar, expected",
        [
            ("my name is yaroslav", "valid", True),
            ("hi", "valid", False),
            ("", "valid", True),
            ("my name is", "invalid", False),
        ],
    )
    def test_is_valid(self, fake_img_file, bio, avatar, expected):
        """
        Verifies the ProfileForm validation for text and file inputs.
        """
        if avatar == "valid":
            img_to_use = fake_img_file
        else:
            img_to_use = SimpleUploadedFile(
                "not_image.txt", b"Not image", content_type="text/plain"
            )

        form = ProfileForm(
            data={"bio": bio}, files=MultiValueDict({"avatar": [img_to_use]})
        )
        assert form.is_valid() == expected
