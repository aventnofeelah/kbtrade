from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy
from . import views

app_name = "users"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("register/verify/", views.verify_email, name="verify_email"),
    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("profile/", views.profile, name="profile"),
    path("profile/password/", auth_views.PasswordChangeView.as_view(
        template_name="password_change.html", success_url=reverse_lazy("users:password_done")), name="password_change"),
    path("profile/password/done/", auth_views.PasswordChangeDoneView.as_view(
        template_name="password_done.html"), name="password_done"),
    path("home/", views.home, name="home"),
]
