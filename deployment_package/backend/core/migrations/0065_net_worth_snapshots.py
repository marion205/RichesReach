"""
Migration 0065 — Add NetWorthSnapshot table
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0064_stock_current_price"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="NetWorthSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="net_worth_snapshots",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("captured_at",     models.DateField()),
                ("net_worth",       models.DecimalField(max_digits=18, decimal_places=2)),
                ("portfolio_value", models.DecimalField(max_digits=18, decimal_places=2, default=0)),
                ("savings_balance", models.DecimalField(max_digits=18, decimal_places=2, default=0)),
                ("debt",            models.DecimalField(max_digits=18, decimal_places=2, default=0)),
                (
                    "source",
                    models.CharField(
                        choices=[
                            ("scheduled", "Scheduled (Celery beat)"),
                            ("on_demand", "On-demand (user loaded Wealth screen)"),
                            ("backfill",  "Backfill"),
                        ],
                        default="on_demand",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "net_worth_snapshots",
                "ordering": ["-captured_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="networthsnapshot",
            constraint=models.UniqueConstraint(
                fields=["user", "captured_at"],
                name="unique_user_captured_at",
            ),
        ),
        migrations.AddIndex(
            model_name="networthsnapshot",
            index=models.Index(fields=["user", "-captured_at"], name="net_worth_user_date_idx"),
        ),
    ]
