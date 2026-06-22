"""Application configuration for the booking app."""
from django.apps import AppConfig


class BookingConfig(AppConfig):
    """Configuration settings for the booking application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "booking"

