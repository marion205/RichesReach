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
# Note: Import beat schedules but don't access settings at module level
# The beat schedule will be configured when Celery actually starts
from core.celery_beat_schedule import CELERY_BEAT_SCHEDULE, CELERY_BEAT_SCHEDULE_DEV

# Use production schedule by default (settings will be loaded when Celery starts)
app.conf.beat_schedule = CELERY_BEAT_SCHEDULE

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')