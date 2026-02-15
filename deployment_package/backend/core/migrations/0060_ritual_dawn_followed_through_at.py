"""
Migration 0060: Add followed_through_at to RitualDawnCompletion for action follow-through tracking.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0059_ritual_dawn_completion"),
    ]

    operations = [
        migrations.AddField(
            model_name="ritualdawncompletion",
            name="followed_through_at",
            field=models.DateTimeField(blank=True, help_text="When user opened the target screen (e.g. StockDetail for committed symbol)", null=True),
        ),
    ]
