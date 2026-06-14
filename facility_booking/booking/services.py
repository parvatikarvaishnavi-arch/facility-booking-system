from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Booking, ComplimentaryLounge, Facility


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
    return (email or "").strip().lower()


def combine(booking_date, booking_time):
    return datetime.combine(booking_date, booking_time)


def duration_hours(booking_date, start_time, end_time):
    seconds = Decimal(
        (combine(booking_date, end_time) - combine(booking_date, start_time)).seconds
    )
    return (seconds / Decimal("3600")).quantize(Decimal("0.01"))


def calculate_charge(facility, booking_date, start_time, end_time, is_member):
    rate = facility.member_charge if is_member else facility.non_member_charge
    amount = duration_hours(booking_date, start_time, end_time) * rate
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def validate_booking_request(facility, booking_date, start_time, end_time):
    if end_time <= start_time:
        raise ValidationError("End time must be after start time.")

    if start_time < facility.operating_start or end_time > facility.operating_end:
        raise ValidationError(
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
            raise ValidationError(rules["overlap_message"])

        if minimum_gap and existing_end <= new_start < existing_end + minimum_gap:
            raise ValidationError(rules["gap_message"])

        if minimum_gap and existing_start - minimum_gap < new_end <= existing_start:
            raise ValidationError(rules["gap_message"])


@transaction.atomic
def create_booking(*, facility, customer_name, customer_email, booking_date, start_time, end_time, is_member):
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
        tracker, _ = ComplimentaryLounge.objects.select_for_update().get_or_create(
            customer_email=customer_email,
            defaults={"customer_name": customer_name.strip()},
        )

        if not tracker.free_booking_used and hours <= LOUNGE_FREE_HOURS:
            booking.is_complimentary = True
            booking.total_charge = Decimal("0.00")
            is_complimentary = True

    booking.save()

    if is_complimentary:
        ComplimentaryLounge.objects.filter(customer_email=customer_email).update(
            customer_name=customer_name.strip(),
            free_booking_used=True,
            booking=booking,
            used_at=timezone.now(),
        )

    return booking


def generate_available_slots(facility, booking_date, minutes=60):
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
        except ValidationError:
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

