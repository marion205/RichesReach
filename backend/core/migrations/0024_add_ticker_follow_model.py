# Generated manually to add TickerFollow model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0023_add_recommended_stocks_field'),
    ]

    operations = [
        migrations.CreateModel(
            name='TickerFollow',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.CharField(db_index=True, max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ticker_follows', to='core.user')),
            ],
            options={
                'unique_together': {('user', 'symbol')},
            },
        ),
        migrations.AddIndex(
            model_name='tickerfollow',
            index=models.Index(fields=['user', 'symbol'], name='core_tickerf_user_id_symbol_idx'),
        ),
        migrations.AddIndex(
            model_name='tickerfollow',
            index=models.Index(fields=['symbol'], name='core_tickerf_symbol_idx'),
        ),
    ]
