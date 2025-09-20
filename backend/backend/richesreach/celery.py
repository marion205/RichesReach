# richesreach/celery.py
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
broker_url=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}',
# Result backend
result_backend=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}',
# Task routing
task_routes={
'core.stock_service.*': {'queue': 'stock_analysis'},
'core.*': {'queue': 'default'},
},
# Task serialization
task_serializer='json',
accept_content=['json'],
result_serializer='json',
# Task execution
task_always_eager=False, # Set to True for testing without Redis
task_eager_propagates=True,
# Worker settings
worker_prefetch_multiplier=1,
worker_max_tasks_per_child=1000,
# Task time limits
task_soft_time_limit=300, # 5 minutes
task_time_limit=600, # 10 minutes
# Beat schedule for periodic tasks
beat_schedule={
'update-stock-data': {
'task': 'core.stock_service.update_stock_data_periodic',
'schedule': 3600.0, # Every hour
},
'cleanup-old-cache': {
'task': 'core.stock_service.cleanup_old_cache',
'schedule': 86400.0, # Every day
},
},
# Redis result backend settings
redis_result_backend_settings={
'host': settings.REDIS_HOST,
'port': settings.REDIS_PORT,
'db': settings.REDIS_DB,
'password': settings.REDIS_PASSWORD,
},
)
@app.task(bind=True)
def debug_task(self):
print(f'Request: {self.request!r}')
