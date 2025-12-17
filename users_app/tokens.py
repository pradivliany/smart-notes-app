from django.contrib.auth.tokens import PasswordResetTokenGenerator

from .models import Profile


class ProfileActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp) -> str:
        profile = Profile.objects.get(user=user)
        return str(user.pk) + str(timestamp) + str(profile.is_confirmed)


profile_activation_token = ProfileActivationTokenGenerator()
password_reset_token = PasswordResetTokenGenerator()
