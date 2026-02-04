# Lesson model for lesson library (replaces MOCK_LESSONS in lesson_api)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0048_recreate_daily_brief_models"),
    ]

    operations = [
        migrations.CreateModel(
            name="Lesson",
            fields=[
                ("id", models.CharField(help_text="Stable ID for progress tracking", max_length=100, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("duration_minutes", models.PositiveSmallIntegerField(default=2)),
                (
                    "difficulty",
                    models.CharField(
                        choices=[
                            ("beginner", "Beginner"),
                            ("intermediate", "Intermediate"),
                            ("advanced", "Advanced"),
                        ],
                        default="beginner",
                        max_length=20,
                    ),
                ),
                ("category", models.CharField(db_index=True, max_length=50)),
                ("concepts", models.JSONField(default=list, help_text="List of concept tags")),
                ("content", models.TextField()),
                ("key_takeaways", models.JSONField(default=list, help_text="List of takeaway strings")),
                ("order", models.PositiveIntegerField(default=0, help_text="Display order in library")),
            ],
            options={
                "db_table": "core_lessons",
                "ordering": ["order", "id"],
            },
        ),
    ]
