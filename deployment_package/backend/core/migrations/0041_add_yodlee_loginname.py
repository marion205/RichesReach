# Generated migration for Yodlee loginName storage
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0040_add_daily_brief_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='yodlee_loginname',
            field=models.CharField(
                max_length=150,
                blank=True,
                null=True,
                unique=True,
                db_index=True,
                help_text='Yodlee loginName for this user (format: rr_userid)'
            ),
        ),
    ]

