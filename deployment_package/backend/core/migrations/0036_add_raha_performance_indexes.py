# Generated migration for RAHA performance indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0035_brokerorder_raha_signal_brokerorder_source_and_more'),
    ]

    operations = [
        # Add composite indexes for frequently queried RAHA fields
        migrations.AddIndex(
            model_name='rahasignal',
            index=models.Index(
                fields=['user', 'symbol', 'timestamp'],
                name='raha_signal_user_symbol_time_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='rahasignal',
            index=models.Index(
                fields=['user', 'strategy_version', 'timestamp'],
                name='raha_signal_user_strategy_time_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='rahasignal',
            index=models.Index(
                fields=['symbol', 'timeframe', 'timestamp'],
                name='raha_signal_symbol_timeframe_time_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='rahabacktestrun',
            index=models.Index(
                fields=['user', 'strategy_version', 'status', 'completed_at'],
                name='raha_backtest_user_strategy_status_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='rahabacktestrun',
            index=models.Index(
                fields=['user', 'status', 'completed_at'],
                name='raha_backtest_user_status_completed_idx'
            ),
        ),
        # Add index for SignalPerformance lookups (signal field is a ForeignKey to DayTradingSignal)
        migrations.AddIndex(
            model_name='signalperformance',
            index=models.Index(
                fields=['signal', 'evaluated_at'],
                name='signal_perf_signal_evaluated_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='signalperformance',
            index=models.Index(
                fields=['outcome', 'evaluated_at'],
                name='signal_perf_outcome_evaluated_idx'
            ),
        ),
    ]

