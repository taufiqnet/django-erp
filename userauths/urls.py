from django.urls import path
from userauths.views import register_view, login_view, logout_view, retail_login_view

app_name = 'userauths'  # Ensure the app_name is defined

urlpatterns = [
    path("signup/", register_view, name="register"),
    path("login/", login_view, name="login"), # Existing generic login
    path("logout/", logout_view, name="logout"),
    # New path for retail login:
    path("retail/login/", retail_login_view, name="retail_login"),
]
