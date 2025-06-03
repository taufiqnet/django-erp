from django.urls import path
from userauths.views import register_view, login_view, logout_view

app_name = 'userauths'  # Ensure the app_name is defined

urlpatterns = [
    path("signup/", register_view, name="register"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
]
