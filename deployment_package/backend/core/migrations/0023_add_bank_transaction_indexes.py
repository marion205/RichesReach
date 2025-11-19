# Generated manually for performance optimization
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_add_stock_moment_model'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='banktransaction',
            index=models.Index(fields=['user', 'transaction_date', 'transaction_type'], name='core_banktr_user_id_trans_idx'),
        ),
        migrations.AddIndex(
            model_name='banktransaction',
            index=models.Index(fields=['user', 'transaction_type', 'transaction_date'], name='core_banktr_user_id_type_idx'),
        ),
    ]

