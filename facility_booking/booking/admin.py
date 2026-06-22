"""Admin configuration for the booking application."""
from django.contrib import admin

from .models import Booking, Facility


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    """Admin configuration for facility records."""

    list_display = (
        "name",
        "facility_type",
        "member_charge",
        "non_member_charge",
        "operating_start",
        "operating_end",
        "active",
    )
    list_filter = ("facility_type", "active")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Admin configuration for booking records."""

    list_display = (
        "facility",
        "customer_name",
        "customer_email",
        "booking_date",
        "start_time",
        "end_time",
        "status",
        "total_charge",
        "is_complimentary",
    )
    list_filter = ("facility__facility_type", "status", "is_member", "is_complimentary")
    search_fields = ("customer_name", "customer_email", "facility__name")
    date_hierarchy = "booking_date"

