from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import LoginForm, SignUpForm


def signup_user(request):
    if request.user.is_authenticated:
        return redirect(to="notes_app:note_list")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(to="users_app:login")
        else:
            return render(request, "users_app/signup.html", {"form": form})

    # request.method == "GET"
    return render(request, "users_app/signup.html", {"form": SignUpForm()})


def login_user(request):
    if request.user.is_authenticated:
        return redirect(to="notes_app:note_list")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )
            if user:
                login(request, user)
                return redirect(to="notes_app:note_list")
            else:
                messages.error(request, "Username or password did not match")
        return render(request, "users_app/login.html", {"form": form})

    # request.method == "GET"
    return render(request, "users_app/login.html", {"form": LoginForm()})


@login_required
def logout_user(request):
    logout(request)
    return redirect(to="welcome")
