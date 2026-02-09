"""
Migration 0058: Add DeFiSessionAuthorization for EIP-712 session-key style authorizations.
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0057_defi_spend_permission"),
    ]

    operations = [
        migrations.CreateModel(
            name="DeFiSessionAuthorization",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("session_id", models.CharField(db_index=True, max_length=128, unique=True)),
                ("wallet_address", models.CharField(db_index=True, max_length=66)),
                ("chain_id", models.IntegerField(db_index=True)),
                ("max_amount_wei", models.CharField(max_length=78)),
                ("valid_until", models.DateTimeField(db_index=True)),
                ("nonce", models.CharField(max_length=78)),
                ("raw_typed_data", models.JSONField(blank=True, default=dict)),
                ("signature", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="defi_session_authorizations", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "defi_session_authorization",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="defisessionauthorization",
            index=models.Index(fields=["user", "valid_until"], name="defi_sessio_user_id_valid__idx"),
        ),
        migrations.AddIndex(
            model_name="defisessionauthorization",
            index=models.Index(fields=["session_id", "valid_until"], name="defi_sessio_session_valid__idx"),
        ),
    ]
