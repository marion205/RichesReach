"""
Migration 0055: Add DeFiAlert and DeFiNotificationPreferences models.

DeFiAlert provides persistent storage for DeFi health, APY, harvest,
and Auto-Pilot repair alerts. Replaces the logging-only stub in
defi_alert_service._send_alert() and enables alert deduplication.

DeFiNotificationPreferences stores per-user push notification settings
for DeFi/Autopilot features. Replaces the NotificationPreferences model
that was deleted in migration 0037.
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0055_defi_models"),
    ]

    operations = [
        migrations.CreateModel(
            name="DeFiAlert",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "alert_type",
                    models.CharField(
                        choices=[
                            ("health_warning", "Health Factor Warning"),
                            ("health_critical", "Health Factor Critical"),
                            ("health_danger", "Liquidation Risk"),
                            ("apy_change", "APY Changed"),
                            ("harvest_ready", "Rewards Ready"),
                            ("repair_available", "Repair Available"),
                            ("repair_executed", "Repair Executed"),
                            ("revert_expiring", "Revert Window Expiring"),
                            ("policy_breach", "Policy Breach"),
                        ],
                        db_index=True,
                        max_length=30,
                    ),
                ),
                (
                    "severity",
                    models.CharField(
                        choices=[
                            ("low", "Low"),
                            ("medium", "Medium"),
                            ("high", "High"),
                            ("urgent", "Urgent"),
                        ],
                        default="low",
                        max_length=10,
                    ),
                ),
                ("title", models.CharField(max_length=200)),
                ("message", models.TextField()),
                ("data", models.JSONField(blank=True, default=dict)),
                (
                    "repair_id",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        max_length=100,
                        null=True,
                    ),
                ),
                ("is_read", models.BooleanField(db_index=True, default=False)),
                ("is_dismissed", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="defi_alerts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "position",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="alerts",
                        to="core.userdefiposition",
                    ),
                ),
                (
                    "pool",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="alerts",
                        to="core.defipool",
                    ),
                ),
            ],
            options={
                "db_table": "defi_alert",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="defialert",
            index=models.Index(
                fields=["user", "-created_at"],
                name="defi_alert_user_id_created_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="defialert",
            index=models.Index(
                fields=["user", "alert_type", "-created_at"],
                name="defi_alert_user_type_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="defialert",
            index=models.Index(
                fields=["user", "is_read", "-created_at"],
                name="defi_alert_user_read_idx",
            ),
        ),
        migrations.CreateModel(
            name="DeFiNotificationPreferences",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "push_token",
                    models.TextField(
                        blank=True,
                        help_text="Expo push notification token",
                        null=True,
                    ),
                ),
                (
                    "push_enabled",
                    models.BooleanField(db_index=True, default=True),
                ),
                ("health_alerts_enabled", models.BooleanField(default=True)),
                ("apy_alerts_enabled", models.BooleanField(default=True)),
                ("harvest_alerts_enabled", models.BooleanField(default=True)),
                ("autopilot_alerts_enabled", models.BooleanField(default=True)),
                ("repair_alerts_enabled", models.BooleanField(default=True)),
                ("revert_reminder_enabled", models.BooleanField(default=True)),
                ("quiet_hours_enabled", models.BooleanField(default=False)),
                ("quiet_hours_start", models.TimeField(blank=True, null=True)),
                ("quiet_hours_end", models.TimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="defi_notification_preferences",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "defi_notification_preferences",
                "verbose_name": "DeFi Notification Preferences",
                "verbose_name_plural": "DeFi Notification Preferences",
            },
        ),
    ]
