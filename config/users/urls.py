from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register, name="register"),
    path("register/verify/", views.verify_email, name="verify_email"),
]