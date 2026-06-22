"""URL patterns for the booking application."""
from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("hall/", views.hall_booking, name="hall_booking"),
    path("studio/", views.studio_booking, name="studio_booking"),
    path("lounge/", views.lounge_booking, name="lounge_booking"),
    path("bookings/<uuid:pk>/cancel/", views.cancel_booking, name="cancel_booking"),
]

