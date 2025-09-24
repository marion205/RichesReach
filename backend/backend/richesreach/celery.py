"""
Celery configuration for RichesReach
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

# Celery Beat schedule for real-time data updates
from core.celery_beat_schedule import CELERY_BEAT_SCHEDULE, CELERY_BEAT_SCHEDULE_DEV

# Use development schedule if DEBUG is True
if settings.DEBUG:
    app.conf.beat_schedule = CELERY_BEAT_SCHEDULE_DEV
else:
    app.conf.beat_schedule = CELERY_BEAT_SCHEDULE

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')