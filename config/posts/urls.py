from django.urls import path

from . import views

app_name = "posts"

urlpatterns = [
    path("lost-found/", views.LostFoundListView.as_view(), name="lostfound"),
    path("lost-found/new/", views.LostFoundCreateView.as_view(), name="lostfound_create"),
]
