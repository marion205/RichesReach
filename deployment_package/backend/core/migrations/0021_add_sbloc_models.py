# Generated migration for SBLOC models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_add_banking_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='SBLOCBank',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('external_id', models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('logo_url', models.URLField(blank=True, max_length=500, null=True)),
                ('min_apr', models.DecimalField(blank=True, decimal_places=4, help_text='Minimum APR as decimal (0.065 = 6.5%)', max_digits=5, null=True)),
                ('max_apr', models.DecimalField(blank=True, decimal_places=4, help_text='Maximum APR as decimal', max_digits=5, null=True)),
                ('min_ltv', models.DecimalField(blank=True, decimal_places=4, help_text='Minimum LTV as decimal (0.5 = 50%)', max_digits=5, null=True)),
                ('max_ltv', models.DecimalField(blank=True, decimal_places=4, help_text='Maximum LTV as decimal', max_digits=5, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('regions', models.JSONField(default=list, help_text="List of regions (e.g., ['US', 'EU', 'CA'])")),
                ('min_loan_usd', models.IntegerField(blank=True, help_text='Minimum loan amount in USD', null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('priority', models.IntegerField(default=0, help_text='Display priority (higher = shown first)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'sbloc_banks',
                'ordering': ['-priority', 'name'],
            },
        ),
        migrations.CreateModel(
            name='SBLOCSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount_usd', models.IntegerField(help_text='Requested loan amount in USD')),
                ('session_id', models.CharField(max_length=255, unique=True, help_text='External session ID')),
                ('application_url', models.URLField(blank=True, max_length=500, null=True)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('IN_PROGRESS', 'In Progress'), ('COMPLETED', 'Completed'), ('CANCELLED', 'Cancelled'), ('FAILED', 'Failed')], default='PENDING', max_length=20)),
                ('aggregator_response', models.JSONField(blank=True, default=dict, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('bank', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='core.sblocbank')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sbloc_sessions', to='core.user')),
            ],
            options={
                'db_table': 'sbloc_sessions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='sblocbank',
            index=models.Index(fields=['is_active', 'priority'], name='sbloc_banks_is_acti_priority_idx'),
        ),
        migrations.AddIndex(
            model_name='sblocsession',
            index=models.Index(fields=['user', 'status'], name='sbloc_sessions_user_id_status_idx'),
        ),
        migrations.AddIndex(
            model_name='sblocsession',
            index=models.Index(fields=['session_id'], name='sbloc_sessions_session_id_idx'),
        ),
    ]

