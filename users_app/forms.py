from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=150,
        min_length=2,
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Your First name"}
        ),
    )
    last_name = forms.CharField(
        max_length=150,
        min_length=2,
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Your Last name"}
        ),
    )
    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "Your Email"}
        ),
    )
    password1 = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Password"}
        ),
    )
    password2 = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.PasswordInput(
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
        self.fields["username"].widget.attrs.update({"class": "form-control", "placeholder": "Your email"})
        self.fields["password"].widget.attrs.update({"class": "form-control", "placeholder": "Password"})
