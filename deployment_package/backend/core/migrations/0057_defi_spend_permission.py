"""
Migration 0057: Add DeFiSpendPermission for EIP-712 signed spend permissions.
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0056_defi_repair_decision"),
    ]

    operations = [
        migrations.CreateModel(
            name="DeFiSpendPermission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("wallet_address", models.CharField(db_index=True, max_length=66)),
                ("chain_id", models.IntegerField(db_index=True)),
                ("max_amount_wei", models.CharField(max_length=78)),
                ("token_address", models.CharField(max_length=66)),
                ("valid_until", models.DateTimeField(db_index=True)),
                ("nonce", models.CharField(max_length=78)),
                ("raw_typed_data", models.JSONField(blank=True, default=dict)),
                ("signature", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="defi_spend_permissions", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "defi_spend_permission",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="defispendpermission",
            index=models.Index(fields=["user", "chain_id", "valid_until"], name="defi_spend_user_id_chain__idx"),
        ),
    ]
