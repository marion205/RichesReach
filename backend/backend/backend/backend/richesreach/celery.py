"""
Celery configuration for RichesReach
"""
import os
from celery import Celery

# ✅ Belt-and-suspenders: force production settings before Django loads
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "richesreach.settings_production")

app = Celery("richesreach")

# This will read from Django settings *after* DJANGO_SETTINGS_MODULE is set
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Celery Beat schedule for real-time data updates
# Note: Import beat schedules but don't access settings at module level
# The beat schedule will be configured when Celery actually starts
from core.celery_beat_schedule import CELERY_BEAT_SCHEDULE, CELERY_BEAT_SCHEDULE_DEV

# Use production schedule by default (settings will be loaded when Celery starts)
app.conf.beat_schedule = CELERY_BEAT_SCHEDULE

# ✅ If you need quick diagnostics without touching Django settings, rely on env only
if os.environ.get("RR_LOG_CELERY_CONFIG", "").lower() in ("1", "true", "yes"):
    print("[celery] broker:", os.environ.get("CELERY_BROKER_URL", "<unset>"))

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')