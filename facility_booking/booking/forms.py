from django import forms

from .models import Booking, Facility
from .services import normalize_email


class BookingForm(forms.ModelForm):
    class Meta:
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
        return normalize_email(self.cleaned_data["customer_email"])

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time and end_time and end_time <= start_time:
            raise forms.ValidationError("End time must be after start time.")

        return cleaned_data


class AvailabilityDateForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))

