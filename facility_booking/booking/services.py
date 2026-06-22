"""Business logic helpers for booking validation and scheduling."""
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Booking, Facility


class BookingValidationError(ValidationError):
    """Base exception for booking rule violations."""


class BookingTimeValidationError(BookingValidationError):
    """Raised when the time range is invalid."""


class BookingOperatingHoursError(BookingValidationError):
    """Raised when the requested slot is outside allowed operating hours."""


class BookingOverlapError(BookingValidationError):
    """Raised when the requested slot overlaps an existing booking."""


class BookingGapError(BookingValidationError):
    """Raised when the requested slot violates the minimum gap rule."""


FACILITY_RULES = {
    Facility.Type.HALL: {
        "gap": timedelta(hours=1),
        "overlap_message": "Selected hall is already booked for this time slot.",
        "gap_message": "Hall bookings must have a minimum gap of 1 hour.",
    },
    Facility.Type.STUDIO: {
        "gap": timedelta(minutes=30),
        "overlap_message": "Selected studio is already booked for this time slot.",
        "gap_message": "Studio bookings must have a minimum gap of 30 minutes.",
    },
    Facility.Type.LOUNGE: {
        "gap": timedelta(0),
        "overlap_message": "Selected lounge is already booked for this time slot.",
        "gap_message": "",
    },
}

LOUNGE_FREE_HOURS = Decimal("4.00")


def normalize_email(email):
    """Normalize an email address for consistent storage and lookup.

    Args:
        email: The email address to normalize.

    Returns:
        A trimmed, lowercase email string.
    """
    return (email or "").strip().lower()


def combine(booking_date, booking_time):
    """Combine a date and time into a datetime object.

    Args:
        booking_date: The booking date.
        booking_time: The booking time.

    Returns:
        A datetime value representing the given date and time.
    """
    return datetime.combine(booking_date, booking_time)


def duration_hours(booking_date, start_time, end_time):
    """Calculate the duration between two times in hours.

    Args:
        booking_date: The date used for the time comparison.
        start_time: The start time.
        end_time: The end time.

    Returns:
        The duration rounded to two decimal places.
    """
    seconds = Decimal(
        (combine(booking_date, end_time) - combine(booking_date, start_time)).seconds
    )
    return (seconds / Decimal("3600")).quantize(Decimal("0.01"))


def calculate_charge(facility, booking_date, start_time, end_time, is_member):
    """Calculate the booking charge for a requested time range.

    Args:
        facility: The facility being booked.
        booking_date: The date of the booking.
        start_time: The requested start time.
        end_time: The requested end time.
        is_member: Whether the customer is a member.

    Returns:
        The total charge rounded to two decimal places.
    """
    rate = facility.member_charge if is_member else facility.non_member_charge
    amount = duration_hours(booking_date, start_time, end_time) * rate
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def validate_booking_request(facility, booking_date, start_time, end_time):
    """Validate that a booking request is allowed for a facility.

    Args:
        facility: The facility to validate against.
        booking_date: The booking date.
        start_time: The requested start time.
        end_time: The requested end time.

    Raises:
        BookingValidationError: If the request overlaps existing bookings or
            falls outside operating hours.
    """
    if end_time <= start_time:
        raise BookingTimeValidationError("End time must be after start time.")

    if start_time < facility.operating_start or end_time > facility.operating_end:
        raise BookingOperatingHoursError(
            f"{facility.get_facility_type_display()} bookings are allowed only "
            f"between {facility.operating_start.strftime('%I:%M %p')} and "
            f"{facility.operating_end.strftime('%I:%M %p')}."
        )

    rules = FACILITY_RULES[facility.facility_type]
    minimum_gap = rules["gap"]
    new_start = combine(booking_date, start_time)
    new_end = combine(booking_date, end_time)

    bookings = Booking.objects.select_for_update().filter(
        facility=facility,
        booking_date=booking_date,
        status=Booking.Status.CONFIRMED,
    )

    for booking in bookings:
        existing_start = combine(booking.booking_date, booking.start_time)
        existing_end = combine(booking.booking_date, booking.end_time)

        if new_start < existing_end and new_end > existing_start:
            raise BookingOverlapError(rules["overlap_message"])

        if minimum_gap and existing_end <= new_start < existing_end + minimum_gap:
            raise BookingGapError(rules["gap_message"])

        if minimum_gap and existing_start - minimum_gap < new_end <= existing_start:
            raise BookingGapError(rules["gap_message"])


@transaction.atomic
def create_booking(*, facility, customer_name, customer_email, booking_date, start_time, end_time, is_member):
    """Create a booking record after validating the request.

    Args:
        facility: The facility to book.
        customer_name: The customer's display name.
        customer_email: The customer's email address.
        booking_date: The requested booking date.
        start_time: The requested start time.
        end_time: The requested end time.
        is_member: Whether the customer is a member.

    Returns:
        The created booking instance.
    """
    facility = Facility.objects.select_for_update().get(pk=facility.pk)
    customer_email = normalize_email(customer_email)

    validate_booking_request(facility, booking_date, start_time, end_time)

    charge = calculate_charge(facility, booking_date, start_time, end_time, is_member)
    is_complimentary = False

    booking = Booking(
        facility=facility,
        customer_name=customer_name.strip(),
        customer_email=customer_email,
        booking_date=booking_date,
        start_time=start_time,
        end_time=end_time,
        is_member=is_member,
        total_charge=charge,
    )

    if facility.facility_type == Facility.Type.LOUNGE:
        hours = duration_hours(booking_date, start_time, end_time)
        has_used_free_booking = Booking.objects.filter(
            customer_email=customer_email,
            facility__facility_type=Facility.Type.LOUNGE,
            is_complimentary=True,
        ).exists()

        if not has_used_free_booking and hours <= LOUNGE_FREE_HOURS:
            booking.is_complimentary = True
            booking.total_charge = Decimal("0.00")
            is_complimentary = True

    booking.save()

    return booking


def generate_available_slots(facility, booking_date, minutes=60):
    """Generate valid booking slots for a facility on a specific date.

    Args:
        facility: The facility to inspect.
        booking_date: The date for slot generation.
        minutes: The desired slot duration in minutes.

    Returns:
        A list of dictionaries containing available slot data.
    """
    slots = []
    cursor = combine(booking_date, facility.operating_start)
    closing = combine(booking_date, facility.operating_end)
    step = timedelta(minutes=30)
    duration = timedelta(minutes=minutes)

    while cursor + duration <= closing:
        start_time = cursor.time()
        end_time = (cursor + duration).time()
        try:
            validate_booking_request(facility, booking_date, start_time, end_time)
        except BookingValidationError:
            pass
        else:
            slots.append(
                {
                    "start": start_time,
                    "end": end_time,
                    "label": f"{start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}",
                }
            )
        cursor += step

    return slots

