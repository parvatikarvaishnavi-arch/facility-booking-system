from django.contrib import admin

from .models import Booking, ComplimentaryLounge, Facility


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
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


@admin.register(ComplimentaryLounge)
class ComplimentaryLoungeAdmin(admin.ModelAdmin):
    list_display = ("customer_email", "customer_name", "free_booking_used", "used_at")
    search_fields = ("customer_email", "customer_name")

