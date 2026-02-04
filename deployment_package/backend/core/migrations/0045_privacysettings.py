# Migration for PrivacySettings model (privacy_types use real DB).

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0044_add_lesson_progress_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='PrivacySettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_sharing_enabled', models.BooleanField(default=True)),
                ('ai_analysis_enabled', models.BooleanField(default=True)),
                ('ml_predictions_enabled', models.BooleanField(default=True)),
                ('analytics_enabled', models.BooleanField(default=True)),
                ('session_tracking_enabled', models.BooleanField(default=False)),
                ('data_retention_days', models.IntegerField(default=90)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=models.CASCADE, related_name='privacy_settings', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'core_privacy_settings',
                'verbose_name_plural': 'Privacy settings',
            },
        ),
    ]
