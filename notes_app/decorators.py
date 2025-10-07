from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def profile_confirmed_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        request = args[0]
        if request.user.profile.is_confirmed:
            result = func(*args, **kwargs)
            return result
        else:
            messages.info(
                request,
                "You need to confirm your profile. Check your mail inbox for activation link",
            )
            return redirect(to="users_app:profile")

    return wrapper
