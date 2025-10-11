"""
WSGI config for richesreach project.
It exposes the WSGI callable as a module-level variable named ``application``.
For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "richesreach.settings_production")
print("[BOOT] Using DJANGO_SETTINGS_MODULE =", os.environ.get("DJANGO_SETTINGS_MODULE"))
from django.core.wsgi import get_wsgi_application
print("[BOOT] WSGI starting, GRAPHQL_MODE=", os.getenv("GRAPHQL_MODE"), flush=True)
application = get_wsgi_application()
