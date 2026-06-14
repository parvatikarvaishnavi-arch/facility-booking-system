from datetime import date

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import BookingForm
from .models import Booking, Facility
from .services import create_booking, generate_available_slots


PAGE_CONFIG = {
    Facility.Type.HALL: {
        "template": "booking/hall.html",
        "title": "Hall Booking",
        "slot_minutes": 60,
        "notes": [
            "Minimum 1 hour gap is required between hall bookings.",
            "Member and non-member charges are calculated hourly.",
        ],
        "url_name": "hall_booking",
    },
    Facility.Type.STUDIO: {
        "template": "booking/studio.html",
        "title": "Studio Booking",
        "slot_minutes": 60,
        "notes": [
            "Minimum 30 minute gap is required between studio bookings.",
            "Member and non-member charges are calculated hourly.",
        ],
        "url_name": "studio_booking",
    },
    Facility.Type.LOUNGE: {
        "template": "booking/lounge.html",
        "title": "Lounge Booking",
        "slot_minutes": 60,
        "notes": [
            "Lounge operates within each lounge room's configured hours.",
            "One complimentary lounge booking up to 4 hours is available per email address.",
        ],
        "url_name": "lounge_booking",
    },
}


def parse_selected_date(raw_date):
    if not raw_date:
        return timezone.localdate()
    try:
        return date.fromisoformat(raw_date)
    except ValueError:
        return timezone.localdate()


def home(request):
    today = timezone.localdate()
    upcoming_query = (
        Booking.objects.select_related("facility")
        .filter(status=Booking.Status.CONFIRMED)
        .filter(Q(booking_date__gt=today) | Q(booking_date=today, end_time__gte=timezone.localtime().time()))
        .order_by("booking_date", "start_time")
    )
    facility_counts = {
        facility_type: Facility.objects.filter(active=True, facility_type=facility_type).count()
        for facility_type in Facility.Type.values
    }
    facility_summary = [
        {
            "name": "Hall",
            "count": facility_counts[Facility.Type.HALL],
            "rule": "1 hour gap",
            "url_name": "hall_booking",
        },
        {
            "name": "Studio",
            "count": facility_counts[Facility.Type.STUDIO],
            "rule": "30 minute gap",
            "url_name": "studio_booking",
        },
        {
            "name": "Lounge",
            "count": facility_counts[Facility.Type.LOUNGE],
            "rule": "Free first 4 hours",
            "url_name": "lounge_booking",
        },
    ]
    return render(
        request,
        "home.html",
        {
            "upcoming_bookings": upcoming_query[:12],
            "upcoming_count": upcoming_query.count(),
            "facility_summary": facility_summary,
        },
    )


def booking_page(request, facility_type):
    config = PAGE_CONFIG[facility_type]
    selected_date = parse_selected_date(request.GET.get("date"))
    facilities = Facility.objects.filter(active=True, facility_type=facility_type)

    if request.method == "POST":
        form = BookingForm(request.POST, facility_type=facility_type)
        if form.is_valid():
            try:
                booking = create_booking(**form.cleaned_data)
            except ValidationError as exc:
                messages.error(request, exc.messages[0])
            else:
                if booking.is_complimentary:
                    messages.success(request, "Complimentary lounge booking confirmed.")
                else:
                    messages.success(
                        request,
                        f"Booking confirmed. Total charge: INR {booking.total_charge}.",
                    )
                url = f"{reverse(config['url_name'])}?date={booking.booking_date.isoformat()}"
                return redirect(url)
    else:
        form = BookingForm(
            facility_type=facility_type,
            initial={"booking_date": selected_date},
        )

    daily_bookings = (
        Booking.objects.select_related("facility")
        .filter(
            facility__facility_type=facility_type,
            booking_date=selected_date,
            status=Booking.Status.CONFIRMED,
        )
        .order_by("facility__name", "start_time")
    )
    availability = {
        facility: generate_available_slots(
            facility,
            selected_date,
            minutes=config["slot_minutes"],
        )
        for facility in facilities
    }

    return render(
        request,
        config["template"],
        {
            "form": form,
            "facilities": facilities,
            "selected_date": selected_date,
            "daily_bookings": daily_bookings,
            "availability": availability,
            "title": config["title"],
            "notes": config["notes"],
        },
    )


def hall_booking(request):
    return booking_page(request, Facility.Type.HALL)


def studio_booking(request):
    return booking_page(request, Facility.Type.STUDIO)


def lounge_booking(request):
    return booking_page(request, Facility.Type.LOUNGE)


def cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk, status=Booking.Status.CONFIRMED)
    if request.method == "POST":
        booking.status = Booking.Status.CANCELLED
        booking.save(update_fields=["status", "updated_at"])
        messages.success(request, "Booking cancelled.")
    return redirect("home")
