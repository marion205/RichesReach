# Migration for SavedInsight and SavedInsightShare (ai_insights save/share).

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0046_alpaca_connection'),
    ]

    operations = [
        migrations.CreateModel(
            name='SavedInsight',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('insight_id', models.CharField(db_index=True, max_length=64)),
                ('title', models.CharField(blank=True, max_length=255)),
                ('summary', models.TextField(blank=True)),
                ('category', models.CharField(blank=True, max_length=64)),
                ('snapshot', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=models.CASCADE, related_name='saved_insights', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'core_saved_insight',
                'ordering': ['-created_at'],
                'unique_together': {('user', 'insight_id')},
            },
        ),
        migrations.CreateModel(
            name='SavedInsightShare',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('insight_id', models.CharField(db_index=True, max_length=64)),
                ('platform', models.CharField(max_length=32)),
                ('shared_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=models.CASCADE, related_name='insight_shares', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'core_saved_insight_share',
                'ordering': ['-shared_at'],
            },
        ),
    ]
