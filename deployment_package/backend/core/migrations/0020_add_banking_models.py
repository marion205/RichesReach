# Generated migration for Banking models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0019_add_credit_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='BankProviderAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider_account_id', models.CharField(db_index=True, max_length=255, unique=True)),
                ('provider_name', models.CharField(max_length=255)),
                ('provider_id', models.CharField(blank=True, max_length=255)),
                ('access_token_enc', models.TextField(blank=True)),
                ('refresh_token_enc', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('ACTIVE', 'Active'), ('INACTIVE', 'Inactive'), ('ERROR', 'Error'), ('DELETED', 'Deleted')], default='ACTIVE', max_length=50)),
                ('last_refresh', models.DateTimeField(blank=True, null=True)),
                ('error_message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bank_provider_accounts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'bank_provider_accounts',
                'unique_together': {('user', 'provider_account_id')},
            },
        ),
        migrations.CreateModel(
            name='BankAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('yodlee_account_id', models.CharField(db_index=True, max_length=255)),
                ('provider', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('mask', models.CharField(max_length=10)),
                ('account_type', models.CharField(max_length=50)),
                ('account_subtype', models.CharField(blank=True, max_length=50)),
                ('currency', models.CharField(default='USD', max_length=10)),
                ('balance_current', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('balance_available', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('is_verified', models.BooleanField(default=False)),
                ('is_primary', models.BooleanField(default=False)),
                ('last_updated', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('provider_account', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='bank_accounts', to='core.bankprovideraccount')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bank_accounts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'bank_accounts',
                'unique_together': {('user', 'yodlee_account_id')},
            },
        ),
        migrations.CreateModel(
            name='BankTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('yodlee_transaction_id', models.CharField(db_index=True, max_length=255)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=15)),
                ('currency', models.CharField(default='USD', max_length=10)),
                ('description', models.CharField(max_length=500)),
                ('merchant_name', models.CharField(blank=True, max_length=255)),
                ('category', models.CharField(blank=True, max_length=100)),
                ('subcategory', models.CharField(blank=True, max_length=100)),
                ('transaction_type', models.CharField(choices=[('DEBIT', 'Debit'), ('CREDIT', 'Credit')], max_length=20)),
                ('posted_date', models.DateField()),
                ('transaction_date', models.DateField(blank=True, null=True)),
                ('status', models.CharField(choices=[('POSTED', 'Posted'), ('PENDING', 'Pending'), ('CANCELLED', 'Cancelled')], default='POSTED', max_length=50)),
                ('raw_json', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('bank_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='core.bankaccount')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bank_transactions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'bank_transactions',
                'unique_together': {('bank_account', 'yodlee_transaction_id'), ('bank_account', 'posted_date', 'amount', 'merchant_name')},
            },
        ),
        migrations.CreateModel(
            name='BankWebhookEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(max_length=100)),
                ('provider_account_id', models.CharField(max_length=255)),
                ('payload', models.JSONField()),
                ('signature', models.CharField(blank=True, max_length=500)),
                ('signature_valid', models.BooleanField(default=False)),
                ('processed', models.BooleanField(default=False)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('error_message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'bank_webhook_events',
            },
        ),
        migrations.AddIndex(
            model_name='bankprovideraccount',
            index=models.Index(fields=['user', 'provider_account_id'], name='core_bankpr_user_id_idx'),
        ),
        migrations.AddIndex(
            model_name='bankaccount',
            index=models.Index(fields=['user', 'yodlee_account_id'], name='core_bankacc_user_id_idx'),
        ),
        migrations.AddIndex(
            model_name='bankaccount',
            index=models.Index(fields=['user', 'is_primary'], name='core_bankacc_user_id_2_idx'),
        ),
        migrations.AddIndex(
            model_name='banktransaction',
            index=models.Index(fields=['user', 'posted_date'], name='core_banktra_user_id_idx'),
        ),
        migrations.AddIndex(
            model_name='banktransaction',
            index=models.Index(fields=['bank_account', 'posted_date'], name='core_banktra_bank_acc_idx'),
        ),
        migrations.AddIndex(
            model_name='banktransaction',
            index=models.Index(fields=['user', '-posted_date'], name='core_banktra_user_id_3_idx'),
        ),
    ]

