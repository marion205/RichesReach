# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
# Lazy accessor to avoid importing celery (and settings) at module import time
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "richesreach.settings_production")

def get_celery_app():
    from .celery import app
    return app

# Remove eager import completely - only use lazy accessor
__all__ = ("get_celery_app",)
