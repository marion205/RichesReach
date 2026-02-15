"""
Migration 0061: Add greeting_key to RitualDawnCompletion for A/B testing greeting copy.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0060_ritual_dawn_followed_through_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="ritualdawncompletion",
            name="greeting_key",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
    ]
