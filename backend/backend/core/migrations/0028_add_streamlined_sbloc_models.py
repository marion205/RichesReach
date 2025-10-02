# Generated manually for streamlined SBLOC integration
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0027_add_yodlee_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='SblocBank',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('slug', models.SlugField(unique=True)),
                ('logo_url', models.URLField(blank=True)),
                ('min_apr', models.FloatField(default=0.06)),
                ('max_apr', models.FloatField(default=0.12)),
                ('min_ltv', models.FloatField(default=0.30)),
                ('max_ltv', models.FloatField(default=0.50)),
                ('min_loan_usd', models.IntegerField(default=5000)),
                ('regions', models.JSONField(default=list, blank=True)),
                ('notes', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='SblocReferral',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.IntegerField(blank=True, null=True)),
                ('amount_usd', models.IntegerField()),
                ('status', models.CharField(default='DRAFT', max_length=32)),
                ('external_ref', models.CharField(blank=True, max_length=128)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('bank', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.sblocbank')),
            ],
        ),
        migrations.CreateModel(
            name='SblocSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('application_url', models.URLField()),
                ('external_session_id', models.CharField(max_length=128)),
                ('status', models.CharField(default='CREATED', max_length=32)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('referral', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.sblocreferral')),
            ],
        ),
    ]
