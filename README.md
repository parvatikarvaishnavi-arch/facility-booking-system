# Facility Booking System

A Django + MySQL facility booking application for halls, studios, and lounges.

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
- MySQL 8+
- Bootstrap 5

## Setup

1. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

   On macOS, `mysqlclient` requires MySQL client libraries. If installation fails, install MySQL or MariaDB development files first, then rerun the command.

3. Create a MySQL database:

   ```sql
   CREATE DATABASE facility_booking CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

4. Create `.env` from the example and update database credentials:

   ```bash
   cp .env.example .env
   ```

5. Export environment variables before running Django:

   ```bash
   export $(grep -v '^#' .env | xargs)
   ```

6. Run migrations and load sample facilities:

   ```bash
   cd facility_booking
   python manage.py migrate
   python manage.py loaddata sample_data
   ```

7. Create an admin user:

   ```bash
   python manage.py createsuperuser
   ```

8. Start the server:

   ```bash
   python manage.py runserver
   ```

Open `http://127.0.0.1:8000/`.

## Testing

Tests automatically use SQLite when `manage.py test` is run without `DB_ENGINE`.

```bash
cd facility_booking
python manage.py test
```

To run the app locally without MySQL, use the SQLite fallback:

```bash
cd facility_booking
USE_SQLITE=True python manage.py migrate
USE_SQLITE=True python manage.py loaddata sample_data
USE_SQLITE=True python manage.py runserver
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

The SQL schema is documented in [`docs/database_schema.sql`](docs/database_schema.sql).

Core tables:

- `booking_facility`
- `booking_booking`
- `booking_complimentarylounge`

## Sample Data

Sample facilities are provided in `facility_booking/booking/fixtures/sample_data.json`.

Load them with:

```bash
cd facility_booking
python manage.py loaddata sample_data
```

## Assumptions

See [`docs/ASSUMPTIONS.md`](docs/ASSUMPTIONS.md).

## Deployment Notes

For production deployment:

- Set `DEBUG=False`.
- Set a strong `SECRET_KEY`.
- Set `ALLOWED_HOSTS` to the deployed domain.
- Use a managed MySQL database.
- Run `python manage.py collectstatic`.
- Serve with Gunicorn/uWSGI behind Nginx or deploy to a Django-friendly platform.

## Submission Links

- GitHub repository link: add the final repository URL after pushing.
- Live application URL: add the deployed application URL after deployment.
