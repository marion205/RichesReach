"""
Migration 0059: Add RitualDawnCompletion for persisting Ritual Dawn commitment actions.
"""
import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0058_defi_session_authorization"),
    ]

    operations = [
        migrations.CreateModel(
            name="RitualDawnCompletion",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("date", models.DateField(db_index=True, default=django.utils.timezone.now)),
                ("action_taken", models.CharField(blank=True, default="", max_length=255)),
                ("completed_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ritual_dawn_completions", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "ritual_dawn_completions",
                "ordering": ["-date"],
                "unique_together": [("user", "date")],
            },
        ),
        migrations.AddIndex(
            model_name="ritualdawncompletion",
            index=models.Index(fields=["user", "date"], name="ritual_dawn_user_date_idx"),
        ),
    ]
