# Migration for AlpacaConnection model (alpaca_oauth stores connection in DB).

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0045_privacysettings'),
    ]

    operations = [
        migrations.CreateModel(
            name='AlpacaConnection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alpaca_account_id', models.CharField(db_index=True, max_length=64)),
                ('access_token', models.TextField()),
                ('refresh_token', models.TextField()),
                ('token_expires_at', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=models.CASCADE, related_name='alpaca_connection', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'core_alpaca_connection',
            },
        ),
    ]
