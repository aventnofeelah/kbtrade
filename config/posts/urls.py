from django.urls import path
from . import views

app_name = "posts"

urlpatterns = [
    path("", views.feed, name="feed"),
    path("marketplace/", views.feed, {"kind": "sale"}, name="marketplace"),
    path("lost-found/", views.feed, {"kind": "lostfound"}, name="lostfound"),
    path("lost-found/new/", views.listing_form, {"default_kind": "lost"}, name="lostfound_create"),
    path("listings/new/", views.listing_form, name="create"),
    path("profile/listings/", views.my_listings, name="my_listings"),
    path("listings/<str:section>/<int:pk>/", views.detail, name="detail"),
    path("listings/<str:section>/<int:pk>/edit/", views.listing_form, name="edit"),
    path("listings/<str:section>/<int:pk>/delete/", views.delete_listing, name="delete"),
]
