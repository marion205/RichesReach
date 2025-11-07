# Generated manually for credit building models
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_add_family_sharing_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='CreditScore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.IntegerField()),
                ('provider', models.CharField(choices=[('experian', 'Experian'), ('equifax', 'Equifax'), ('transunion', 'TransUnion'), ('self_reported', 'Self Reported'), ('credit_karma', 'Credit Karma')], default='self_reported', max_length=50)),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('factors', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='credit_scores', to='core.user')),
            ],
            options={
                'ordering': ['-date'],
                'unique_together': {('user', 'date', 'provider')},
            },
        ),
        migrations.CreateModel(
            name='CreditCard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('limit', models.DecimalField(decimal_places=2, max_digits=10)),
                ('balance', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('utilization', models.FloatField(default=0)),
                ('yodlee_account_id', models.CharField(blank=True, max_length=100, null=True)),
                ('last_synced', models.DateTimeField(blank=True, null=True)),
                ('payment_due_date', models.DateField(blank=True, null=True)),
                ('minimum_payment', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='credit_cards', to='core.user')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CreditAction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action_type', models.CharField(choices=[('AUTOPAY_SETUP', 'Set Up Autopay'), ('CARD_APPLIED', 'Applied for Card'), ('PAYMENT_MADE', 'Made Payment'), ('LIMIT_INCREASE', 'Requested Limit Increase'), ('UTILIZATION_REDUCED', 'Reduced Utilization')], max_length=50)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('completed', models.BooleanField(default=False)),
                ('projected_score_gain', models.IntegerField(blank=True, null=True)),
                ('due_date', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='credit_actions', to='core.user')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CreditProjection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_score', models.IntegerField()),
                ('projected_score_6m', models.IntegerField()),
                ('projected_score_12m', models.IntegerField(blank=True, null=True)),
                ('top_action', models.CharField(max_length=200)),
                ('confidence', models.FloatField(default=0.5)),
                ('factors', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='credit_projections', to='core.user')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]

