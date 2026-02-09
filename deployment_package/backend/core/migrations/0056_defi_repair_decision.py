"""
Migration 0056: Add DeFiRepairDecision model for Auto-Pilot decision ledger.
Logs every suggested and executed repair for audit trail and outcome attribution.
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0055_defialert"),
    ]

    operations = [
        migrations.CreateModel(
            name="DeFiRepairDecision",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("repair_id", models.CharField(db_index=True, max_length=200)),
                ("decision_type", models.CharField(choices=[("suggested", "Suggested"), ("executed", "Executed"), ("dismissed", "Dismissed")], db_index=True, max_length=20)),
                ("inputs", models.JSONField(blank=True, default=dict)),
                ("explanation", models.TextField(blank=True, default="")),
                ("expected_apy_delta", models.FloatField(blank=True, null=True)),
                ("policy_version", models.CharField(blank=True, default="", max_length=50)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("executed_at", models.DateTimeField(blank=True, null=True)),
                ("actual_apy_delta", models.FloatField(blank=True, null=True)),
                ("tx_hash", models.CharField(blank=True, default="", max_length=66)),
                ("from_pool", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="repair_decisions_from", to="core.defipool")),
                ("position", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="repair_decisions", to="core.userdefiposition")),
                ("to_pool", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="repair_decisions_to", to="core.defipool")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="defi_repair_decisions", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "defi_repair_decision",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="defirepairdecision",
            index=models.Index(fields=["user", "-created_at"], name="defi_repair_user_id_created_idx"),
        ),
        migrations.AddIndex(
            model_name="defirepairdecision",
            index=models.Index(fields=["user", "decision_type"], name="defi_repair_user_id_decis_idx"),
        ),
    ]
