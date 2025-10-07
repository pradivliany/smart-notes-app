from django.contrib.auth.tokens import PasswordResetTokenGenerator


class ProfileActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp) -> str:
        return str(user.pk) + str(timestamp) + str(user.profile.is_confirmed)


profile_activation_token = ProfileActivationTokenGenerator()
