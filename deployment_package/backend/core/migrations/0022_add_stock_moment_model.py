# Generated migration for StockMoment model
# Run: python manage.py migrate

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_add_sbloc_models'),  # Update this to match your latest migration
    ]

    operations = [
        migrations.CreateModel(
            name='StockMoment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('symbol', models.CharField(db_index=True, max_length=16)),
                ('timestamp', models.DateTimeField(db_index=True)),
                ('importance_score', models.FloatField(default=0.0)),
                ('category', models.CharField(choices=[('EARNINGS', 'Earnings'), ('NEWS', 'News'), ('INSIDER', 'Insider'), ('MACRO', 'Macro'), ('SENTIMENT', 'Sentiment'), ('OTHER', 'Other')], default='OTHER', max_length=32)),
                ('title', models.CharField(max_length=140)),
                ('quick_summary', models.TextField()),
                ('deep_summary', models.TextField()),
                ('source_links', models.JSONField(blank=True, default=list)),
                ('impact_1d', models.FloatField(blank=True, null=True)),
                ('impact_7d', models.FloatField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['symbol', '-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='stockmoment',
            index=models.Index(fields=['symbol', 'timestamp'], name='core_stockm_symbol_tim_idx'),
        ),
    ]

