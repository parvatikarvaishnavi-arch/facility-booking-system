"""Forms used for booking interactions."""
from django import forms

from .models import Booking, Facility
from .services import normalize_email

class BookingForm(forms.ModelForm):
    """Form for creating and validating booking requests."""

    class Meta:
        """Metadata for the booking form."""

        model = Booking
        fields = [
            "facility",
            "customer_name",
            "customer_email",
            "booking_date",
            "start_time",
            "end_time",
            "is_member",
        ]
        widgets = {
            "booking_date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time", "step": 1800}),
            "end_time": forms.TimeInput(attrs={"type": "time", "step": 1800}),
        }
        labels = {
            "is_member": "Book as member",
        }

    def __init__(self, *args, facility_type=None, **kwargs):
        """Initialize the form and limit facilities by type if provided.

        Args:
            facility_type: Optional facility type used to filter choices.
        """
        super().__init__(*args, **kwargs)
        queryset = Facility.objects.filter(active=True)
        if facility_type:
            queryset = queryset.filter(facility_type=facility_type)
        self.fields["facility"].queryset = queryset
        self.fields["facility"].empty_label = "Choose a facility"

        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = "form-control"

        self.fields["facility"].widget.attrs["class"] = "form-select"

    def clean_customer_email(self):
        """Normalize the customer email before validation.

        Returns:
            A trimmed, lowercase email address.
        """
        return normalize_email(self.cleaned_data["customer_email"])

    def clean(self):
        """Validate that the selected time range is logically correct.

        Returns:
            The cleaned form data.

        Raises:
            ValidationError: If the end time is not after the start time.
        """
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time and end_time and end_time <= start_time:
            raise forms.ValidationError("End time must be after start time.")

        return cleaned_data


class AvailabilityDateForm(forms.Form):
    """Simple form used to select a booking date."""

    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))

