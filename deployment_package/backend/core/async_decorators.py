# core/async_decorators.py
"""
Async-aware decorators for Django views that preserve async functions
and maintain decorator attributes (like csrf_exempt).
"""
import asyncio
from functools import wraps
from django.http import JsonResponse


def async_csrf_exempt(view_func):
    """
    Async-safe csrf_exempt. Sets csrf_exempt=True on the FINAL callable.
    """
    if asyncio.iscoroutinefunction(view_func):
        @wraps(view_func)
        async def _wrapped(*args, **kwargs):
            return await view_func(*args, **kwargs)
        _wrapped.csrf_exempt = True
        return _wrapped

    # sync fallback
    from django.views.decorators.csrf import csrf_exempt
    return csrf_exempt(view_func)


def async_require_http_methods(methods):
    """
    Async-safe require_http_methods that preserves csrf_exempt and other attrs.
    """
    methods = {m.upper() for m in methods}

    def decorator(view_func):
        if asyncio.iscoroutinefunction(view_func):
            @wraps(view_func)
            async def _wrapped(request, *args, **kwargs):
                if request.method.upper() not in methods:
                    return JsonResponse({"error": f"Method {request.method} not allowed"}, status=405)
                return await view_func(request, *args, **kwargs)

            # IMPORTANT: preserve csrf_exempt if it was set before
            _wrapped.csrf_exempt = getattr(view_func, "csrf_exempt", False)
            return _wrapped

        # sync fallback
        from django.views.decorators.http import require_http_methods
        wrapped = require_http_methods(list(methods))(view_func)
        wrapped.csrf_exempt = getattr(view_func, "csrf_exempt", False)
        return wrapped

    return decorator

