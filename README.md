# Facility Booking System

A Django facility booking application for halls, studios, and lounges. It uses SQLite by default for local setup, so no separate database software is required.

## Features

- Navigation for Hall Booking, Studio Booking, and Lounge Booking.
- Hall booking with member/non-member pricing, overlap prevention, and a 1 hour gap rule.
- Studio booking with member/non-member pricing, overlap prevention, and a 30 minute gap rule.
- Lounge booking with hourly pricing, operating-hour validation, overlap prevention, and one complimentary booking up to 4 hours per email address.
- Availability display for each selected date.
- Dashboard of upcoming bookings.
- Booking cancellation.
- Django Admin management.
- Focused unit tests for overlap, gap, operating-hour, and complimentary lounge rules.

## Tech Stack

- Python 3.9+
- Django 4.2 LTS
- SQLite for local development
- Bootstrap 5

## Setup

SQLite is included with Python, and Django creates the local `db.sqlite3` file when migrations run. You only need Python 3.9+ installed; no database server or native database client libraries are required.

### macOS or Linux

1. Create and activate a virtual environment from the project root:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   python3 -m pip install -r requirements.txt
   ```

3. Run migrations and load sample facilities:

   ```bash
   cd facility_booking
   python3 manage.py migrate
   python3 manage.py loaddata sample_data
   ```

4. Optional: create an admin user:

   ```bash
   python3 manage.py createsuperuser
   ```

5. Start the server:

   ```bash
   python3 manage.py runserver
   ```

Open `http://127.0.0.1:8000/`.

### Windows PowerShell

1. Create and activate a virtual environment from the project root:

   ```powershell
   py -3 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If `py -3` is not available, use `python` instead.

2. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Run migrations and load sample facilities:

   ```powershell
   cd facility_booking
   python manage.py migrate
   python manage.py loaddata sample_data
   ```

4. Optional: create an admin user:

   ```powershell
   python manage.py createsuperuser
   ```

5. Start the server:

   ```powershell
   python manage.py runserver
   ```

Open `http://127.0.0.1:8000/`.

## Testing

Tests use SQLite by default.

```bash
cd facility_booking
python3 manage.py test
```

On Windows PowerShell, use:

```powershell
cd facility_booking
python manage.py test
```

## Booking Rules Implemented

- A booking is rejected when `end_time <= start_time`.
- A booking is rejected when it is outside the selected facility's operating hours.
- Confirmed bookings block overlapping bookings for the same facility and date.
- Hall bookings require a 1 hour gap before or after another confirmed hall booking.
- Studio bookings require a 30 minute gap before or after another confirmed studio booking.
- Lounge bookings do not require an extra buffer, but they cannot overlap and must stay inside operating hours.
- The first lounge booking up to 4 hours for a customer email is complimentary.
- Complimentary lounge usage is stored in the database, not in the browser session.

## Database Schema

The SQL schema is documented in [`docs/database_schema.sql`](docs/database_schema.sql). The app uses SQLite locally unless `DB_ENGINE` is set to another Django database backend.

Core tables:

- `booking_facility`
- `booking_booking`
- `booking_complimentarylounge`

## Sample Data

Sample facilities are provided in `facility_booking/booking/fixtures/sample_data.json`.

Load them with:

```bash
cd facility_booking
python3 manage.py loaddata sample_data
```

On Windows PowerShell, use `python manage.py loaddata sample_data` from the `facility_booking` directory.

## Assumptions

See [`docs/ASSUMPTIONS.md`](docs/ASSUMPTIONS.md).

## Deployment Notes

For production deployment:

- Set `DEBUG=False`.
- Set a strong `SECRET_KEY`.
- Set `ALLOWED_HOSTS` to the deployed domain.
- Run `python3 manage.py collectstatic` on macOS/Linux, or `python manage.py collectstatic` on Windows.
- Serve with Gunicorn/uWSGI behind Nginx or deploy to a Django-friendly platform.

MySQL is optional. If you choose to use MySQL instead of SQLite, install the correct database driver, set `DB_ENGINE=django.db.backends.mysql`, and provide `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT`.

## Submission Links

- GitHub repository link: add the final repository URL after pushing.
- Live application URL: add the deployed application URL after deployment.
