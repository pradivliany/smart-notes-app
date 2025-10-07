from django.urls import path

from . import views

app_name = "users_app"

urlpatterns = [
    path("signup/", views.signup_user, name="signup"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("activate/<str:uidb64>/<str:token>/", views.activate_user, name="activate"),
    path("reset_password/", views.reset_password, name="reset_password"),
]
