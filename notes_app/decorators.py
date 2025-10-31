from functools import wraps
from typing import Callable

from django.contrib import messages
from django.shortcuts import redirect


def profile_confirmed_required(func: Callable) -> Callable:
    """
    Ensures that the user's profile is confirmed before accessing a view.

    - If confirmed: proceeds to the view.
    - If not confirmed: shows an info message and redirects to profile page.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        request = args[0]
        if request.user.profile.is_confirmed:
            return func(*args, **kwargs)
        else:
            messages.info(
                request,
                "You need to confirm your profile. Check your mail inbox for activation link",
            )
            return redirect(to="users_app:profile")

    return wrapper
