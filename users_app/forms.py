from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.forms import (CharField, EmailField, EmailInput, ImageField,
                          PasswordInput, TextInput)
from django.forms.widgets import Textarea

from .models import Profile


class SignUpForm(UserCreationForm):
    first_name = CharField(
        max_length=150,
        min_length=2,
        required=True,
        widget=TextInput(
            attrs={"class": "form-control", "placeholder": "Your First name"}
        ),
    )
    last_name = CharField(
        max_length=150,
        min_length=2,
        required=True,
        widget=TextInput(
            attrs={"class": "form-control", "placeholder": "Your Last name"}
        ),
    )
    email = EmailField(
        max_length=254,
        required=True,
        widget=EmailInput(attrs={"class": "form-control", "placeholder": "Your Email"}),
    )
    password1 = CharField(
        max_length=50,
        required=True,
        widget=PasswordInput(
            attrs={"class": "form-control", "placeholder": "Password"}
        ),
    )
    password2 = CharField(
        max_length=50,
        required=True,
        widget=PasswordInput(
            attrs={"class": "form-control", "placeholder": "Repeat your password"}
        ),
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Your email"}
        )
        self.fields["password"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Password"}
        )


class ProfileForm(forms.ModelForm):
    avatar = ImageField(widget=forms.FileInput(attrs={"class": "form-control"}))
    bio = CharField(
        min_length=4,
        max_length=500,
        required=False,
        widget=Textarea(attrs={"class": "form-control", "placeholder": "Your bio"}),
    )

    class Meta:
        model = Profile
        fields = ["avatar", "bio"]


class EmailForm(forms.Form):
    email = EmailField(
        max_length=254,
        min_length=5,
        required=True,
        widget=EmailInput(attrs={"class": "form-control", "placeholder": "Your Email"}),
    )


class PasswordConfirmForm(forms.Form):
    password1 = CharField(
        max_length=50,
        required=True,
        widget=PasswordInput(
            attrs={"class": "form-control", "placeholder": "Password"}
        ),
    )
    password2 = CharField(
        max_length=50,
        required=True,
        widget=PasswordInput(
            attrs={"class": "form-control", "placeholder": "Repeat your password"}
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        pw1, pw2 = cleaned_data.get("password1"), cleaned_data.get("password2")
        if pw1 != pw2:
            raise ValidationError("Passwords do not match")
