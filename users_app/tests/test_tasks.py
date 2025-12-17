import pytest
from celery.exceptions import Retry

from users_app.tasks import send_activation_email_task, send_reset_password_email_task


@pytest.mark.django_db
class TestSendActivationEmailTask:
    def test_user_exists(self, mocker, user_with_profile):
        mock_send_email = mocker.patch("users_app.tasks.send_mail")
        user, _ = user_with_profile

        send_activation_email_task(user.pk, "example.com")

        args, kwargs = mock_send_email.call_args
        mock_send_email.assert_called_once()
        assert "Activate" in args[0]
        assert "Hello" in args[1]
        assert args[3][0] == user.email

    def test_user_does_not_exist(self, mocker):
        mock_send_email = mocker.patch("users_app.tasks.send_mail")
        send_activation_email_task(9999, "example.com")
        mock_send_email.assert_not_called()

    def test_error_occurred(self, mocker, user_with_profile):
        user, _ = user_with_profile
        expected_exception = Exception("Some error occurred")

        mocker.patch("users_app.tasks.send_mail", side_effect=expected_exception)
        mock_retry = mocker.patch.object(
            send_activation_email_task, "retry", side_effect=Retry()
        )

        with pytest.raises(Retry):
            send_activation_email_task.run(user.pk, "example.com")

        mock_retry.assert_called_once()
        args, kwargs = mock_retry.call_args
        assert kwargs["exc"] is expected_exception


@pytest.mark.django_db
class TestSendResetPasswordEmailTask:
    def test_user_exists(self, mocker, user_with_profile):
        mock_send_email = mocker.patch("users_app.tasks.send_mail")
        user, _ = user_with_profile

        send_reset_password_email_task(user.pk, "example.com")

        args, kwargs = mock_send_email.call_args
        mock_send_email.assert_called_once()
        assert "Reset" in args[0]
        assert "Hello" in args[1]
        assert args[3][0] == user.email

    def test_user_does_not_exist(self, mocker):
        mock_send_email = mocker.patch("users_app.tasks.send_mail")
        send_reset_password_email_task(9999, "example.com")
        mock_send_email.assert_not_called()

    def test_error_occurred(self, mocker, user_with_profile):
        user, _ = user_with_profile
        expected_exception = Exception("Some error occurred")

        mocker.patch("users_app.tasks.send_mail", side_effect=expected_exception)
        mock_retry = mocker.patch.object(
            send_reset_password_email_task, "retry", side_effect=Retry()
        )

        with pytest.raises(Retry):
            send_reset_password_email_task.run(user.pk, "example.com")

        mock_retry.assert_called_once()
        args, kwargs = mock_retry.call_args
        assert kwargs["exc"] is expected_exception
