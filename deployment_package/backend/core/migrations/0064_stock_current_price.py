# Restore current_price on Stock (removed in 0015; model still expects it for paper trading, ML, etc.)
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0063_safety_decision_log"),
    ]

    operations = [
        migrations.AddField(
            model_name="stock",
            name="current_price",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
