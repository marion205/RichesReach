# Generated migration for lesson progress tracking.
# Uses raw SQL so it works whether or not UserProgress exists in migration state
# (0042 removed the model from state; table may still exist in DB).

from django.db import migrations, connection


def add_column_if_exists(apps, schema_editor):
    with connection.cursor() as cursor:
        if connection.vendor == "postgresql":
            cursor.execute(
                """
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'user_progress'
                """
            )
            if cursor.fetchone():
                cursor.execute(
                    """
                    ALTER TABLE user_progress
                    ADD COLUMN IF NOT EXISTS completed_lesson_ids JSONB DEFAULT '[]'
                    """
                )
        else:
            # SQLite
            cursor.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='user_progress'"
            )
            if cursor.fetchone():
                try:
                    cursor.execute(
                        """
                        ALTER TABLE user_progress
                        ADD COLUMN completed_lesson_ids TEXT DEFAULT '[]'
                        """
                    )
                except Exception:
                    pass  # Column may already exist


def remove_column_if_exists(apps, schema_editor):
    with connection.cursor() as cursor:
        if connection.vendor == "postgresql":
            cursor.execute(
                """
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'user_progress'
                """
            )
            if cursor.fetchone():
                cursor.execute(
                    "ALTER TABLE user_progress DROP COLUMN IF EXISTS completed_lesson_ids"
                )
        # SQLite doesn't support DROP COLUMN easily on older versions; no-op for reverse


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0043_add_signal_tracking_fields"),
    ]

    operations = [
        migrations.RunPython(add_column_if_exists, remove_column_if_exists),
    ]
