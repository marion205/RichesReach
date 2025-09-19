# Generated manually to add recommended_stocks field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_add_institutional_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='aiportfoliorecommendation',
            name='recommended_stocks',
            field=models.JSONField(default=list),
        ),
    ]
