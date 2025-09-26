from typing import Callable
from django.contrib.auth.models import AnonymousUser

class JWTAuthMiddleware:
    """Minimal pass-through JWT middleware (replace with real token parsing)."""

    def __init__(self, app: Callable):
        self.app = app

    async def __call__(self, scope, receive, send):
        # TODO: parse JWT from headers/querystring and set scope["user"]
        scope.setdefault("user", AnonymousUser())
        return await self.app(scope, receive, send)

def JWTAuthMiddlewareStack(inner: Callable):
    return JWTAuthMiddleware(inner)