from django.shortcuts import render, HttpResponse

# Create your views here.


def signup_user(request):
    return HttpResponse('Welcome to Signup page')


def login_user(request):
    return HttpResponse('Welcome to Login page')


def logout_user(request):
    return HttpResponse('Welcome to Logout page')
