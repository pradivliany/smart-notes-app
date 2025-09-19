from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=150, min_length=2, required=True, widget=forms.TextInput()
    )
    last_name = forms.CharField(
        max_length=150, min_length=2, required=True, widget=forms.TextInput()
    )
    email = forms.EmailField(max_length=254, required=True, widget=forms.TextInput())
    password1 = forms.CharField(
        max_length=50, required=True, widget=forms.PasswordInput()
    )
    password2 = forms.CharField(
        max_length=50, required=True, widget=forms.PasswordInput()
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
    class Meta:
        model = User
        fields = ["username", "password"]
