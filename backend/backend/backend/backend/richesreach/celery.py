"""
Celery Configuration for RichesReach DeFi Background Jobs
Production-grade task queue with Redis backend
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

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    'daily-yield-refresh': {
        'task': 'core.tasks.daily_yield_refresh',
        'schedule': 86400.0,  # 24 hours
    },
    'hourly-position-updates': {
        'task': 'core.tasks.hourly_position_updates',
        'schedule': 3600.0,   # 1 hour
    },
    'every-5min-transaction-verification': {
        'task': 'core.tasks.every_5min_transaction_verification',
        'schedule': 300.0,    # 5 minutes
    },
    'daily-cleanup': {
        'task': 'core.tasks.cleanup_old_data',
        'schedule': 86400.0,  # 24 hours
    },
}

app.conf.timezone = 'UTC'

# Task routing and optimization
app.conf.task_routes = {
    'core.tasks.refresh_yield_data': {'queue': 'yield_refresh'},
    'core.tasks.update_farm_positions': {'queue': 'position_updates'},
    'core.tasks.verify_pending_transactions': {'queue': 'transaction_verification'},
    'core.tasks.cleanup_old_data': {'queue': 'maintenance'},
}

# Task execution settings
app.conf.task_serializer = 'json'
app.conf.accept_content = ['json']
app.conf.result_serializer = 'json'
app.conf.timezone = 'UTC'
app.conf.enable_utc = True

# Task retry settings
app.conf.task_acks_late = True
app.conf.worker_prefetch_multiplier = 1
app.conf.task_reject_on_worker_lost = True

# Result backend settings
app.conf.result_expires = 3600  # 1 hour

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')