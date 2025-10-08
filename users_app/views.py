from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.utils.http import urlsafe_base64_decode

from .emails import send_activation_email, send_reset_password_email
from .forms import (EmailForm, LoginForm, PasswordConfirmForm, ProfileForm,
                    SignUpForm)
from .models import Profile
from .tokens import password_reset_token, profile_activation_token


def signup_user(request):
    if request.user.is_authenticated:
        return redirect(to="notes_app:note_list")

    if request.method == "POST":
        form = SignUpForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data.get("email")

            if User.objects.filter(username=email).exists():
                messages.error(request, "User with such email already exists.")
                return redirect(to="users_app:login")

            user = form.save()
            send_activation_email(request, user)
            messages.success(
                request, "Please check your email to complete the activation."
            )
            return redirect(to="users_app:login")
        else:
            return render(request, "users_app/signup.html", {"form": form})

    return render(request, "users_app/signup.html", {"form": SignUpForm()})


def activate_user(request, uidb64, token):
    decoded_pk = urlsafe_base64_decode(uidb64).decode()

    try:
        user = User.objects.get(pk=decoded_pk)
    except User.DoesNotExist:
        messages.error(request, "Something went wrong. User not found.")
        return redirect(to="users_app:signup")

    if profile_activation_token.check_token(user, token):
        profile = user.profile
        profile.is_confirmed = True
        profile.save()
        messages.success(
            request,
            "Your account has been activated! Now you can add tags and notes.",
        )
        return redirect(to="notes_app:note_list")
    else:
        messages.error(request, "Invalid or expired activation link.")
        return redirect(to="users_app:signup")


def login_user(request):
    if request.user.is_authenticated:
        return redirect(to="notes_app:note_list")

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            if not request.user.profile.is_confirmed:
                messages.info(
                    request, "Please confirm your email to unlock full features."
                )
                return redirect(to="users_app:profile")
            return redirect(to="notes_app:note_list")
        return render(request, "users_app/login.html", {"form": form})

    return render(request, "users_app/login.html", {"form": LoginForm()})


@login_required
def logout_user(request):
    logout(request)
    return redirect(to="welcome")


@login_required
def profile(request):
    curr_profile = Profile.objects.get(user=request.user)
    return render(request, "users_app/profile.html", {"curr_profile": curr_profile})


@login_required
def edit_profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect(to="users_app:profile")

    else:
        form = ProfileForm(instance=request.user.profile)

    return render(request, "users_app/edit_profile.html", {"form": form})


# ------------------------
# RESET PASSWORD
# ------------------------


def reset_password(request):
    if request.method == "POST":
        form = EmailForm(request.POST)
        if form.is_valid():
            user = User.objects.filter(email=form.cleaned_data["email"]).first()
            if user:
                send_reset_password_email(request, user)

            return redirect(to="users_app:reset_password_done")
        else:
            messages.error(request, "Please enter a valid email address.")

    else:
        form = EmailForm()

    return render(request, "users_app/reset_password_form.html", {"form": form})


def reset_password_done(request):
    return render(request, "users_app/reset_password_done.html")


def reset_password_confirm(request, uidb64, token):
    decoded_pk = urlsafe_base64_decode(uidb64).decode()
    user = User.objects.filter(pk=decoded_pk).first()

    if user and password_reset_token.check_token(user, token):
        if request.method == "POST":
            form = PasswordConfirmForm(request.POST)
            if form.is_valid():
                user.set_password(form.cleaned_data["password1"])
                user.save()
                messages.success(
                    request,
                    "Your password has been successfully changed. You can now login with your new password.",
                )
                return redirect(to="users_app:login")
            else:
                messages.error(request, "Please correct the errors in the form below.")

        else:
            form = PasswordConfirmForm()

        return render(request, "users_app/reset_password_confirm.html", {"form": form})

    else:
        messages.error(
            request,
            "This password reset link is invalid or has expired. Please request a new one.",
        )
        return redirect(to="users_app:login")
