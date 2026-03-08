"""
Migration 0063: Safety v0 — SafetyDecisionLog for cross-cutting guardrail audit.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0062_defirepairdecision_outcome_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="SafetyDecisionLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("user_id", models.CharField(db_index=True, help_text="User ID from request or Django user pk", max_length=64)),
                ("action_type", models.CharField(db_index=True, max_length=64)),
                ("decision", models.CharField(db_index=True, max_length=32)),
                ("reason", models.TextField(blank=True, default="")),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "safety_decision_log",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="safetydecisionlog",
            index=models.Index(fields=["action_type", "-created_at"], name="safety_log_action_created_idx"),
        ),
    ]
