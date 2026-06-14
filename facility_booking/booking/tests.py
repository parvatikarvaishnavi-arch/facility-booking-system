from datetime import date, time
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import Booking, ComplimentaryLounge, Facility
from .services import create_booking


class BookingRuleTests(TestCase):
    def setUp(self):
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
        self.make_booking(self.hall, time(10, 0), time(12, 0))

        with self.assertRaisesMessage(
            ValidationError,
            "Selected hall is already booked for this time slot.",
        ):
            self.make_booking(self.hall, time(11, 0), time(13, 0), "other@example.com")

    def test_hall_requires_one_hour_gap(self):
        self.make_booking(self.hall, time(10, 0), time(12, 0))

        with self.assertRaisesMessage(
            ValidationError,
            "Hall bookings must have a minimum gap of 1 hour.",
        ):
            self.make_booking(self.hall, time(12, 30), time(14, 0), "other@example.com")

        booking = self.make_booking(self.hall, time(13, 0), time(14, 0), "ok@example.com")
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)

    def test_studio_requires_thirty_minute_gap(self):
        self.make_booking(self.studio, time(10, 0), time(12, 0))

        with self.assertRaisesMessage(
            ValidationError,
            "Studio bookings must have a minimum gap of 30 minutes.",
        ):
            self.make_booking(self.studio, time(12, 15), time(13, 0), "other@example.com")

        booking = self.make_booking(self.studio, time(12, 30), time(13, 0), "ok@example.com")
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)

    def test_lounge_rejects_booking_outside_operating_hours(self):
        with self.assertRaisesMessage(
            ValidationError,
            "Lounge bookings are allowed only between 08:00 AM and 10:00 PM.",
        ):
            self.make_booking(self.lounge, time(7, 0), time(9, 0))

    def test_lounge_first_booking_up_to_four_hours_is_complimentary_once(self):
        first = self.make_booking(self.lounge, time(10, 0), time(14, 0))
        second = self.make_booking(self.lounge, time(15, 0), time(16, 0))

        tracker = ComplimentaryLounge.objects.get(customer_email="person@example.com")
        self.assertTrue(first.is_complimentary)
        self.assertEqual(first.total_charge, Decimal("0.00"))
        self.assertFalse(second.is_complimentary)
        self.assertEqual(second.total_charge, Decimal("300.00"))
        self.assertTrue(tracker.free_booking_used)

