import uuid

from django.db import migrations


def normalize_uuid(value):
    """Return Django's SQLite UUID storage format, or a new UUID for legacy IDs."""
    try:
        return uuid.UUID(str(value)).hex
    except ValueError:
        return uuid.uuid4().hex


def migrate_uuid_primary_keys(apps, schema_editor):
    """Repair legacy integer primary keys so UUID-based models can be read correctly."""
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SELECT id FROM booking_facility")
        facility_rows = cursor.fetchall()
        facility_id_map = {}

        for (old_facility_id,) in facility_rows:
            new_facility_id = normalize_uuid(old_facility_id)
            old_facility_id = str(old_facility_id)
            facility_id_map[old_facility_id] = new_facility_id
            if old_facility_id != new_facility_id:
                cursor.execute(
                    "UPDATE booking_facility SET id = %s WHERE id = %s",
                    [new_facility_id, old_facility_id],
                )

        cursor.execute("SELECT id, facility_id FROM booking_booking")
        for (old_booking_id, old_facility_id) in cursor.fetchall():
            old_booking_id = str(old_booking_id)
            old_facility_id = str(old_facility_id)
            new_booking_id = normalize_uuid(old_booking_id)
            new_facility_id = facility_id_map.get(old_facility_id, normalize_uuid(old_facility_id))
            if old_booking_id != new_booking_id or old_facility_id != new_facility_id:
                cursor.execute(
                    "UPDATE booking_booking SET id = %s, facility_id = %s WHERE id = %s",
                    [new_booking_id, new_facility_id, old_booking_id],
                )


def reverse_migration(apps, schema_editor):
    """No-op reverse migration for the UUID repair step."""


class Migration(migrations.Migration):
    dependencies = [
        ("booking", "0003_alter_booking_id_alter_facility_id_and_more"),
    ]

    operations = [
        migrations.RunPython(
            migrate_uuid_primary_keys,
            reverse_migration,
        ),
    ]
