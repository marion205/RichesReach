# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
# Lazy import to avoid settings access during module import
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "richesreach.settings_production")

# Only import celery after Django settings are configured
def get_celery_app():
    from .celery import app as celery_app
    return celery_app

# For backward compatibility, but this will be lazy-loaded
celery_app = None

def __getattr__(name):
    if name == 'celery_app' and celery_app is None:
        global celery_app
        celery_app = get_celery_app()
        return celery_app
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = ('celery_app',)
