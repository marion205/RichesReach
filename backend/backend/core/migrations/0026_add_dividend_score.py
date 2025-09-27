# Generated manually to fix missing dividend_score field
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_merge_20250920_0325'),
    ]

    operations = [
        migrations.AddField(
            model_name='stock',
            name='dividend_score',
            field=models.IntegerField(blank=True, null=True, help_text='Dividend quality score (0-100)'),
        ),
    ]
