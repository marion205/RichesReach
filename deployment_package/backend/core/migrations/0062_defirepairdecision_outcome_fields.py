"""
Migration 0062: Add outcome tracking fields to DeFiRepairDecision.
Trust-First Framework: post-repair outcome attribution and post-mortems.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0061_ritual_dawn_greeting_key"),
    ]

    operations = [
        migrations.AddField(
            model_name="defirepairdecision",
            name="outcome_status",
            field=models.CharField(blank=True, default="", max_length=32),
        ),
        migrations.AddField(
            model_name="defirepairdecision",
            name="outcome_report",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="defirepairdecision",
            name="outcome_checked_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
