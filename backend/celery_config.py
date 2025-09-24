"""
Celery Configuration for RichesReach Swing Trading Platform
Production-ready Celery setup with Redis backend
"""

import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')

app = Celery('richesreach')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Configuration
app.conf.update(
    # Broker settings
    broker_url='redis://127.0.0.1:6379/0',
    result_backend='redis://127.0.0.1:6379/0',
    
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task routing
    task_routes={
        'core.swing_trading.tasks.*': {'queue': 'swing_trading'},
        'core.tasks.*': {'queue': 'general'},
    },
    
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # Task execution settings
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,       # 10 minutes
    task_always_eager=False,   # Set to True for testing
    
    # Result backend settings
    result_expires=3600,       # 1 hour
    result_persistent=True,
    
    # Beat scheduler
    beat_scheduler='django_celery_beat.schedulers:DatabaseScheduler',
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Error handling
    task_reject_on_worker_lost=True,
    task_ignore_result=False,
    
    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Security
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
)

# Periodic tasks for swing trading
app.conf.beat_schedule = {
    'scan-symbols-for-signals': {
        'task': 'core.swing_trading.tasks.scan_symbol_for_signals',
        'schedule': 300.0,  # Every 5 minutes
        'args': ('AAPL', '1d'),  # Default symbol and timeframe
    },
    'update-ohlcv-indicators': {
        'task': 'core.swing_trading.tasks.update_ohlcv_indicators',
        'schedule': 3600.0,  # Every hour
        'args': ('AAPL', '1d'),
    },
    'validate-signals': {
        'task': 'core.swing_trading.tasks.validate_signals',
        'schedule': 1800.0,  # Every 30 minutes
    },
    'update-trader-scores': {
        'task': 'core.swing_trading.tasks.update_trader_scores',
        'schedule': 86400.0,  # Daily
    },
    'cleanup-old-data': {
        'task': 'core.swing_trading.tasks.cleanup_old_data',
        'schedule': 604800.0,  # Weekly
    },
    'generate-daily-report': {
        'task': 'core.swing_trading.tasks.generate_daily_report',
        'schedule': 86400.0,  # Daily at midnight
    },
    'train-ml-models': {
        'task': 'core.swing_trading.tasks.train_ml_models',
        'schedule': 86400.0,  # Daily
    },
}

@app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery setup"""
    print(f'Request: {self.request!r}')
    return 'Celery is working!'

# Task monitoring and logging
@app.task(bind=True)
def log_task_execution(self, task_name, status, message=''):
    """Log task execution for monitoring"""
    print(f'Task {task_name} {status}: {message}')
    
    # You can add more sophisticated logging here
    # For example, send to monitoring service, database, etc.
    
    return f'Logged: {task_name} {status}'

# Error handling
@app.task(bind=True)
def handle_task_error(self, exc, task_id, args, kwargs, einfo):
    """Handle task errors"""
    print(f'Task {task_id} failed: {exc}')
    print(f'Args: {args}, Kwargs: {kwargs}')
    print(f'Exception info: {einfo}')
    
    # You can add error reporting here
    # For example, send to Sentry, email admin, etc.
    
    return f'Error handled for task {task_id}'

# Health check task
@app.task
def health_check():
    """Health check task for monitoring"""
    return {
        'status': 'healthy',
        'timestamp': '2024-01-01T00:00:00Z',
        'version': '1.0.0'
    }

if __name__ == '__main__':
    app.start()
