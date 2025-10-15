"""
ASGI config for richesreach project.
It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "richesreach.settings")

# Try to import channels, fallback to basic ASGI if not available
try:
    from channels.routing import ProtocolTypeRouter, URLRouter
    from channels.auth import AuthMiddlewareStack
    from core.routing import websocket_urlpatterns
    
    application = ProtocolTypeRouter({
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        ),
    })
except ImportError:
    # Fallback to basic ASGI if channels is not available
    application = get_asgi_application()
