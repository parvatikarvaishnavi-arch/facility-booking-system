"""Tests for booking business rules and behavior."""
from datetime import date, time
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Booking, Facility
from .services import create_booking


# UNIT TESTS
class BookingRuleTests(TestCase):
    """Unit tests covering booking validation and complimentary rules."""

    def setUp(self):
        """Create reusable facilities and test data for each test."""
        self.hall = Facility.objects.create(
            name="Grand Hall",
            slug="grand-hall",
            facility_type=Facility.Type.HALL,
            member_charge=Decimal("1000.00"),
            non_member_charge=Decimal("1500.00"),
            operating_start=time(8, 0),
            operating_end=time(22, 0),
        )
        self.studio = Facility.objects.create(
            name="Podcast Studio",
            slug="podcast-studio",
            facility_type=Facility.Type.STUDIO,
            member_charge=Decimal("500.00"),
            non_member_charge=Decimal("800.00"),
            operating_start=time(8, 0),
            operating_end=time(22, 0),
        )
        self.lounge = Facility.objects.create(
            name="Member Lounge",
            slug="member-lounge",
            facility_type=Facility.Type.LOUNGE,
            member_charge=Decimal("300.00"),
            non_member_charge=Decimal("450.00"),
            operating_start=time(8, 0),
            operating_end=time(22, 0),
        )
        self.booking_date = date(2026, 7, 1)

    def make_booking(self, facility, start, end, email="person@example.com"):
        """Create a booking for the test fixture.

        Args:
            facility: The facility to book.
            start: The requested start time.
            end: The requested end time.
            email: The customer's email address.

        Returns:
            The created booking instance.
        """
        return create_booking(
            facility=facility,
            customer_name="Test User",
            customer_email=email,
            booking_date=self.booking_date,
            start_time=start,
            end_time=end,
            is_member=True,
        )

    def test_hall_rejects_overlapping_booking(self):
        """Ensure overlapping hall bookings are rejected."""
        self.make_booking(self.hall, time(10, 0), time(12, 0))

        with self.assertRaisesMessage(
            ValidationError,
            "Selected hall is already booked for this time slot.",
        ):
            self.make_booking(self.hall, time(11, 0), time(13, 0), "other@example.com")

    def test_hall_requires_one_hour_gap(self):
        """Ensure hall bookings respect the required one-hour gap."""
        self.make_booking(self.hall, time(10, 0), time(12, 0))

        with self.assertRaisesMessage(
            ValidationError,
            "Hall bookings must have a minimum gap of 1 hour.",
        ):
            self.make_booking(self.hall, time(12, 30), time(14, 0), "other@example.com")

        booking = self.make_booking(self.hall, time(13, 0), time(14, 0), "ok@example.com")
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)

    def test_studio_requires_thirty_minute_gap(self):
        """Ensure studio bookings respect the required thirty-minute gap."""
        self.make_booking(self.studio, time(10, 0), time(12, 0))

        with self.assertRaisesMessage(
            ValidationError,
            "Studio bookings must have a minimum gap of 30 minutes.",
        ):
            self.make_booking(self.studio, time(12, 15), time(13, 0), "other@example.com")

        booking = self.make_booking(self.studio, time(12, 30), time(13, 0), "ok@example.com")
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)

    def test_lounge_rejects_booking_outside_operating_hours(self):
        """Ensure lounge bookings cannot be made outside operating hours."""
        with self.assertRaisesMessage(
            ValidationError,
            "Lounge bookings are allowed only between 08:00 AM and 10:00 PM.",
        ):
            self.make_booking(self.lounge, time(7, 0), time(9, 0))

    def test_lounge_first_booking_up_to_four_hours_is_complimentary_once(self):
        """Ensure the first lounge booking up to four hours is complimentary once."""
        first = self.make_booking(self.lounge, time(10, 0), time(14, 0))
        second = self.make_booking(self.lounge, time(15, 0), time(16, 0))

        self.assertTrue(first.is_complimentary)
        self.assertEqual(first.total_charge, Decimal("0.00"))
        self.assertFalse(second.is_complimentary)
        self.assertEqual(second.total_charge, Decimal("300.00"))
        self.assertTrue(
            Booking.objects.filter(
                customer_email="person@example.com",
                facility__facility_type=Facility.Type.LOUNGE,
                is_complimentary=True,
            ).exists()
        )


# INTEGRATION TESTS
class BookingViewIntegrationTests(TestCase):
    """Integration tests for booking views and user-facing workflows."""
    # These tests verify how the views, templates, forms, and database work together.

    def setUp(self):
        """Create reusable facilities and booking data for view tests."""
        self.hall = Facility.objects.create(
            name="Grand Hall",
            slug="grand-hall",
            facility_type=Facility.Type.HALL,
            member_charge=Decimal("1000.00"),
            non_member_charge=Decimal("1500.00"),
            operating_start=time(8, 0),
            operating_end=time(22, 0),
        )
        self.studio = Facility.objects.create(
            name="Podcast Studio",
            slug="podcast-studio",
            facility_type=Facility.Type.STUDIO,
            member_charge=Decimal("500.00"),
            non_member_charge=Decimal("800.00"),
            operating_start=time(8, 0),
            operating_end=time(22, 0),
        )
        self.lounge = Facility.objects.create(
            name="Member Lounge",
            slug="member-lounge",
            facility_type=Facility.Type.LOUNGE,
            member_charge=Decimal("300.00"),
            non_member_charge=Decimal("450.00"),
            operating_start=time(8, 0),
            operating_end=time(22, 0),
        )
        self.booking_date = date(2026, 7, 1)

    def test_home_page_renders_context_for_upcoming_bookings(self):
        """Ensure the home page includes upcoming booking summaries."""
        Booking.objects.create(
            facility=self.hall,
            customer_name="Alice",
            customer_email="alice@example.com",
            booking_date=self.booking_date,
            start_time=time(18, 0),
            end_time=time(19, 0),
            is_member=True,
            total_charge=Decimal("1000.00"),
        )

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["upcoming_count"], 1)
        self.assertEqual(len(response.context["facility_summary"]), 3)

    def test_booking_page_get_displays_date_and_form(self):
        """Ensure the booking page loads successfully for a selected date."""
        response = self.client.get(
            reverse("hall_booking") + f"?date={self.booking_date.isoformat()}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected_date"], self.booking_date)
        self.assertIn("form", response.context)

    def test_booking_page_post_creates_booking_and_redirects(self):
        """Ensure a valid booking request creates a record and redirects."""
        response = self.client.post(
            reverse("hall_booking"),
            {
                "facility": self.hall.pk,
                "customer_name": "Jane Doe",
                "customer_email": "jane@example.com",
                "booking_date": self.booking_date.isoformat(),
                "start_time": "09:00",
                "end_time": "10:00",
                "is_member": True,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Booking.objects.count(), 1)
        self.assertEqual(Booking.objects.first().customer_email, "jane@example.com")

    def test_booking_page_post_with_invalid_time_shows_error(self):
        """Ensure invalid booking data is rejected without creating a record."""
        response = self.client.post(
            reverse("hall_booking"),
            {
                "facility": self.hall.pk,
                "customer_name": "Jane Doe",
                "customer_email": "jane@example.com",
                "booking_date": self.booking_date.isoformat(),
                "start_time": "10:00",
                "end_time": "09:00",
                "is_member": True,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Booking.objects.count(), 0)
        self.assertContains(response, "End time must be after start time.")

    def test_cancel_booking_post_updates_status(self):
        """Ensure cancelling a confirmed booking changes its status."""
        booking = Booking.objects.create(
            facility=self.hall,
            customer_name="Alice",
            customer_email="alice@example.com",
            booking_date=self.booking_date,
            start_time=time(18, 0),
            end_time=time(19, 0),
            is_member=True,
            total_charge=Decimal("1000.00"),
        )

        response = self.client.post(
            reverse("cancel_booking", args=[booking.pk]),
        )

        self.assertEqual(response.status_code, 302)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CANCELLED)


# API / ENDPOINT TESTS
class BookingEndpointTests(TestCase):
    """HTTP endpoint / API-style tests for booking routes."""
    # These tests verify request/response behavior for the app endpoints.

    def setUp(self):
        """Create basic data needed for endpoint checks."""
        self.hall = Facility.objects.create(
            name="Grand Hall",
            slug="grand-hall",
            facility_type=Facility.Type.HALL,
            member_charge=Decimal("1000.00"),
            non_member_charge=Decimal("1500.00"),
            operating_start=time(8, 0),
            operating_end=time(22, 0),
        )

    def test_home_endpoint_returns_successful_response(self):
        """Ensure the home page endpoint responds successfully."""
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_booking_endpoint_returns_successful_response(self):
        """Ensure the facility booking page responds successfully."""
        response = self.client.get(reverse("hall_booking"))
        self.assertEqual(response.status_code, 200)

    def test_cancel_endpoint_redirects_to_home_for_get_requests(self):
        """Ensure the cancel endpoint redirects safely for non-POST requests."""
        booking = Booking.objects.create(
            facility=self.hall,
            customer_name="Alice",
            customer_email="alice@example.com",
            booking_date=date(2026, 7, 1),
            start_time=time(18, 0),
            end_time=time(19, 0),
            is_member=True,
            total_charge=Decimal("1000.00"),
        )

        response = self.client.get(reverse("cancel_booking", args=[booking.pk]))

        self.assertRedirects(response, reverse("home"))

