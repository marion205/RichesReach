# Generated manually for enhanced authentication system
from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [
    ('core', '0013_stock_current_price'),
    ]
    operations = [
    migrations.AddField(
    model_name='user',
    name='failed_login_attempts',
    field=models.IntegerField(default=0, help_text='Number of consecutive failed login attempts'),
    ),
    migrations.AddField(
    model_name='user',
    name='locked_until',
    field=models.DateTimeField(blank=True, null=True, help_text='Account lockout expiration time'),
    ),
    migrations.AddField(
    model_name='user',
    name='last_login_ip',
    field=models.GenericIPAddressField(blank=True, null=True, help_text='IP address of last login'),
    ),
    migrations.AddField(
    model_name='user',
    name='email_verified',
    field=models.BooleanField(default=False, help_text='Whether email address has been verified'),
    ),
    migrations.AddField(
    model_name='user',
    name='two_factor_enabled',
    field=models.BooleanField(default=False, help_text='Whether two-factor authentication is enabled'),
    ),
    migrations.AddField(
    model_name='user',
    name='two_factor_secret',
    field=models.CharField(blank=True, max_length=32, help_text='Secret key for two-factor authentication'),
    ),
    migrations.AddField(
    model_name='user',
    name='created_at',
    field=models.DateTimeField(auto_now_add=True, help_text='Account creation timestamp'),
    ),
    migrations.AddField(
    model_name='user',
    name='updated_at',
    field=models.DateTimeField(auto_now=True, help_text='Last update timestamp'),
    ),
    ]
