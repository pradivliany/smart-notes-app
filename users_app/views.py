from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.http import urlsafe_base64_decode

from .forms import EmailForm, LoginForm, PasswordConfirmForm, ProfileForm, SignUpForm
from .models import Profile
from .tasks import send_activation_email_task, send_reset_password_email_task
from .tokens import password_reset_token, profile_activation_token


def signup_user(request: HttpRequest) -> HttpResponse:
    """
    Handles the registration of a new user.

    If the user is already authenticated -> redirected to the notes list.

    On POST request:
    1. Data is validated using SignUpForm.
    2. If valid:
       - The new User instance is saved to the database.
       - An asynchronous task (Celery) is scheduled to send the activation email.
       - The user is shown a success message and redirected to the login page.
    3. If invalid, the form is rendered with error messages.

    On GET request:
    Renders an empty registration form.
    """
    if request.user.is_authenticated:
        return redirect(to="notes_app:note_list")

    form = SignUpForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]

        if User.objects.filter(username=email).exists():
            messages.error(request, "User with such email already exists.")
            return redirect(to="users_app:login")

        user = form.save()

        transaction.on_commit(
            lambda: send_activation_email_task.delay(
                user.pk, get_current_site(request).domain
            )
        )

        messages.success(
            request,
            "Registration successful! Please check your email to activate your account.",
        )
        return redirect(to="users_app:login")

    return render(request, "users_app/signup.html", {"form": form})


def activate_user(request: HttpRequest, uidb64: str, token: str) -> HttpResponse:
    """
    Activates a user's account via the email confirmation link.

    Steps:
    1. Decodes uidb64 and retrieves the user.
    2. Checks the activation token.
    3. If valid → marks profile as confirmed and redirects to notes.
    4. If invalid → shows an error and redirects to signup.
    """
    try:
        decoded_pk = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=decoded_pk)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and profile_activation_token.check_token(user, token):
        user_profile, _ = Profile.objects.get_or_create(user=user)
        user_profile.is_confirmed = True
        user_profile.save()
        messages.success(
            request,
            "Your account has been activated! Now you can add tags and notes.",
        )
        return redirect(to="notes_app:note_list")

    messages.error(request, "Invalid or expired activation link.")
    return redirect(to="users_app:signup")


def login_user(request: HttpRequest) -> HttpResponse:
    """
    Logs a user into the application.

    Steps:
    1. If the user is already authenticated → redirects to notes.
    2. On POST:
       - Validates credentials via LoginForm.
       - If valid → logs user in and checks profile confirmation.
       - If profile not confirmed → shows info message and redirects to profile.
    3. On GET → renders an empty login form.
    """
    if request.user.is_authenticated:
        return redirect(to="notes_app:note_list")

    form = LoginForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())

        user_profile, _ = Profile.objects.get_or_create(user=request.user)
        if not user_profile.is_confirmed:
            messages.info(request, "Please confirm your email to unlock full features.")
            return redirect(to="users_app:profile")

        return redirect(to="notes_app:note_list")

    return render(request, "users_app/login.html", {"form": form})


@login_required
def logout_user(request: HttpRequest) -> HttpResponse:
    """Logs out the current user and redirects to the welcome page."""
    logout(request)
    return redirect(to="welcome")


@login_required
def profile(request: HttpRequest) -> HttpResponse:
    """Displays the current user's profile page."""
    curr_profile = Profile.objects.get(user=request.user)
    return render(request, "users_app/profile.html", {"curr_profile": curr_profile})


@login_required
def edit_profile(request: HttpRequest) -> HttpResponse:
    """
    Edits the authenticated user's profile.

    GET: Shows the form pre-filled with the user's profile data.
    POST: Validates the submitted data and saves changes if valid.
    """
    user_profile, _ = Profile.objects.get_or_create(user=request.user)
    form = ProfileForm(
        request.POST or None, request.FILES or None, instance=user_profile
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile updated successfully.")
        return redirect(to="users_app:profile")

    return render(request, "users_app/edit_profile.html", {"form": form})


# RESET PASSWORD


def reset_password(request: HttpRequest) -> HttpResponse:
    """
    Handles the password reset request.

    GET: Shows the form to enter an email.
    POST: Validates the email and sends a reset link via Celery task if the user exists.
    Shows success or error messages accordingly.
    """
    form = EmailForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            user = User.objects.filter(email=form.cleaned_data["email"]).first()
            if user:
                send_reset_password_email_task.delay(
                    user.pk, get_current_site(request).domain
                )
            messages.success(
                request,
                "If an account with that email exists, we've sent instructions to complete the reset. "
                "Please check your spam folder.",
            )
            return redirect(to="users_app:reset_password_done")

        messages.error(request, "Please enter a valid email address.")
        return render(request, "users_app/reset_password_form.html", {"form": form})

    return render(request, "users_app/reset_password_form.html", {"form": form})


def reset_password_done(request: HttpRequest) -> HttpResponse:
    return render(request, "users_app/reset_password_done.html")


def reset_password_confirm(request: HttpRequest, uidb64, token) -> HttpResponse:
    """
    Confirms a password reset request via a secure link.

    Steps:
    1. Decodes the Base64 user ID (uidb64) and retrieves the user.
    2. Validates the password reset token.
    3. If valid:
        - Shows a form to enter a new password.
        - On valid submission, updates the user's password and shows a success message.
    4. If invalid or expired:
        - Shows an error message and redirects to login page.
    """
    try:
        decoded_pk = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=decoded_pk)
    except (User.DoesNotExist, TypeError, ValueError):
        user = None

    if not user or not password_reset_token.check_token(user, token):
        messages.error(
            request,
            "This password reset link is invalid or has expired. Please request a new one.",
        )
        return redirect(to="users_app:login")

    form = PasswordConfirmForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user.set_password(form.cleaned_data["password1"])
        user.save()
        messages.success(
            request,
            "Your password has been successfully changed. You can now login with your new password.",
        )
        return redirect(to="users_app:login")

    return render(request, "users_app/reset_password_confirm.html", {"form": form})
