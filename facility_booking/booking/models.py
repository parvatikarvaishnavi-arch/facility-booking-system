from django.db import models
from django.db.models import F, Q


class Facility(models.Model):
    class Type(models.TextChoices):
        HALL = "hall", "Hall"
        STUDIO = "studio", "Studio"
        LOUNGE = "lounge", "Lounge"

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140)
    facility_type = models.CharField(max_length=20, choices=Type.choices)
    member_charge = models.DecimalField(max_digits=10, decimal_places=2)
    non_member_charge = models.DecimalField(max_digits=10, decimal_places=2)
    operating_start = models.TimeField()
    operating_end = models.TimeField()
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["facility_type", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["facility_type", "slug"],
                name="unique_facility_type_slug",
            ),
            models.CheckConstraint(
                check=Q(operating_end__gt=F("operating_start")),
                name="facility_operating_end_after_start",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_facility_type_display()})"


class Booking(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    facility = models.ForeignKey(
        Facility,
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    customer_name = models.CharField(max_length=120)
    customer_email = models.EmailField()
    booking_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_member = models.BooleanField(default=False)
    total_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_complimentary = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CONFIRMED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["booking_date", "start_time"]
        indexes = [
            models.Index(fields=["facility", "booking_date", "status"]),
            models.Index(fields=["customer_email", "booking_date"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(end_time__gt=F("start_time")),
                name="booking_end_after_start",
            ),
        ]

    def __str__(self):
        return (
            f"{self.customer_name} - {self.facility.name} - "
            f"{self.booking_date} {self.start_time}-{self.end_time}"
        )


class ComplimentaryLounge(models.Model):
    customer_email = models.EmailField(unique=True)
    customer_name = models.CharField(max_length=120, blank=True)
    free_booking_used = models.BooleanField(default=False)
    booking = models.OneToOneField(
        Booking,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="complimentary_lounge_record",
    )
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["customer_email"]

    def __str__(self):
        return self.customer_email

