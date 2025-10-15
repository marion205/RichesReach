"""
Celery Beat schedule configuration for real-time data updates
"""
from celery.schedules import crontab

# Celery Beat schedule for periodic tasks
CELERY_BEAT_SCHEDULE = {
    # Update priority stocks every 5 minutes during market hours
    'update-priority-stocks-every-5-minutes': {
        'task': 'core.tasks.update_priority_stocks_realtime',
        'schedule': crontab(minute='*/5', hour='9-16'),  # 9 AM to 4 PM EST
    },
    
    # Update all stocks every 15 minutes during market hours
    'update-all-stocks-every-15-minutes': {
        'task': 'core.tasks.update_all_stocks_realtime',
        'schedule': crontab(minute='*/15', hour='9-16'),  # 9 AM to 4 PM EST
    },
    
    # Update all stocks once at market open (9:30 AM EST)
    'update-all-stocks-market-open': {
        'task': 'core.tasks.update_all_stocks_realtime',
        'schedule': crontab(minute=30, hour=9),  # 9:30 AM EST
    },
    
    # Update all stocks once at market close (4:00 PM EST)
    'update-all-stocks-market-close': {
        'task': 'core.tasks.update_all_stocks_realtime',
        'schedule': crontab(minute=0, hour=16),  # 4:00 PM EST
    },
    
    # Cleanup old data daily at 2 AM
    'cleanup-old-stock-data': {
        'task': 'core.tasks.cleanup_old_stock_data',
        'schedule': crontab(minute=0, hour=2),  # 2:00 AM daily
    },
}

# Alternative schedule for development/testing (more frequent updates)
CELERY_BEAT_SCHEDULE_DEV = {
    # Update priority stocks every 2 minutes
    'update-priority-stocks-dev': {
        'task': 'core.tasks.update_priority_stocks_realtime',
        'schedule': crontab(minute='*/2'),
    },
    
    # Update all stocks every 10 minutes
    'update-all-stocks-dev': {
        'task': 'core.tasks.update_all_stocks_realtime',
        'schedule': crontab(minute='*/10'),
    },
    
    # Cleanup old data every 6 hours
    'cleanup-old-stock-data-dev': {
        'task': 'core.tasks.cleanup_old_stock_data',
        'schedule': crontab(minute=0, hour='*/6'),
    },
}
