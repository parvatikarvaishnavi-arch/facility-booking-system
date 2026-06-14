# Assumptions

- Operating hours are configured per facility. Sample data uses 8:00 AM to 10:00 PM.
- Charges are hourly. The total charge is `duration in hours * member/non-member hourly rate`.
- A user is identified by email address because authentication is optional for this assignment.
- Lounge complimentary usage is tracked by email address in the `ComplimentaryLounge` table.
- The first lounge booking of up to 4 hours for an email address is complimentary. Longer lounge bookings are chargeable and do not consume the complimentary booking.
- Bookings are same-day bookings only. Overnight bookings are rejected because end time must be after start time.
- Cancelled bookings do not block future availability.
- Availability chips show possible 1-hour slots in 30-minute increments. Users may still submit longer custom durations through the form.
- Race-condition protection is implemented by locking the selected facility row inside a transaction before checking and creating a booking.

