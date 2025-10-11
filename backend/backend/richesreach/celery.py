"""
Celery configuration for RichesReach
"""
import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings_production')

app = Celery('richesreach')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat schedule for real-time data updates
from core.celery_beat_schedule import CELERY_BEAT_SCHEDULE, CELERY_BEAT_SCHEDULE_DEV

# Avoid touching settings attributes at import time
try:
    _ = getattr(settings, "DEBUG", False)
except Exception:
    # If settings aren't ready, don't explode during import
    pass

# Use development schedule if DEBUG is True
# Use getattr to avoid AttributeError if settings not fully loaded
try:
    if getattr(settings, 'DEBUG', False):
        app.conf.beat_schedule = CELERY_BEAT_SCHEDULE_DEV
    else:
        app.conf.beat_schedule = CELERY_BEAT_SCHEDULE
except Exception:
    # Fallback to production schedule if settings access fails
    app.conf.beat_schedule = CELERY_BEAT_SCHEDULE

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')