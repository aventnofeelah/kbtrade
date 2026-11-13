from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("register/verify/", views.verify_email, name="verify_email"),

    path("home/", views.home, name="home")
]