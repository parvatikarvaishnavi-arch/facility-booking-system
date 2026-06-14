# Generated manually for the facility booking assignment.
import datetime

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Facility",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("slug", models.SlugField(max_length=140)),
                (
                    "facility_type",
                    models.CharField(
                        choices=[("hall", "Hall"), ("studio", "Studio"), ("lounge", "Lounge")],
                        max_length=20,
                    ),
                ),
                ("member_charge", models.DecimalField(decimal_places=2, max_digits=10)),
                ("non_member_charge", models.DecimalField(decimal_places=2, max_digits=10)),
                ("operating_start", models.TimeField()),
                ("operating_end", models.TimeField()),
                ("active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["facility_type", "name"]},
        ),
        migrations.CreateModel(
            name="Booking",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("customer_name", models.CharField(max_length=120)),
                ("customer_email", models.EmailField(max_length=254)),
                ("booking_date", models.DateField()),
                ("start_time", models.TimeField()),
                ("end_time", models.TimeField()),
                ("is_member", models.BooleanField(default=False)),
                ("total_charge", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("is_complimentary", models.BooleanField(default=False)),
                (
                    "status",
                    models.CharField(
                        choices=[("confirmed", "Confirmed"), ("cancelled", "Cancelled")],
                        default="confirmed",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "facility",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="bookings",
                        to="booking.facility",
                    ),
                ),
            ],
            options={"ordering": ["booking_date", "start_time"]},
        ),
        migrations.CreateModel(
            name="ComplimentaryLounge",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("customer_email", models.EmailField(max_length=254, unique=True)),
                ("customer_name", models.CharField(blank=True, max_length=120)),
                ("free_booking_used", models.BooleanField(default=False)),
                ("used_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "booking",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="complimentary_lounge_record",
                        to="booking.booking",
                    ),
                ),
            ],
            options={"ordering": ["customer_email"]},
        ),
        migrations.AddConstraint(
            model_name="facility",
            constraint=models.UniqueConstraint(fields=("facility_type", "slug"), name="unique_facility_type_slug"),
        ),
        migrations.AddConstraint(
            model_name="facility",
            constraint=models.CheckConstraint(
                check=models.Q(("operating_end__gt", models.F("operating_start"))),
                name="facility_operating_end_after_start",
            ),
        ),
        migrations.AddIndex(
            model_name="booking",
            index=models.Index(fields=["facility", "booking_date", "status"], name="booking_facilit_724ed1_idx"),
        ),
        migrations.AddIndex(
            model_name="booking",
            index=models.Index(fields=["customer_email", "booking_date"], name="booking_custome_8fed7a_idx"),
        ),
        migrations.AddConstraint(
            model_name="booking",
            constraint=models.CheckConstraint(
                check=models.Q(("end_time__gt", models.F("start_time"))),
                name="booking_end_after_start",
            ),
        ),
    ]

