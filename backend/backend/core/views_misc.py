"""
Miscellaneous views for debugging and monitoring
"""

import os
from django.http import JsonResponse

def version(request):
    """Return version information for deployment verification"""
    return JsonResponse({
        "git_sha": os.getenv("APP_GIT_SHA", "unknown"),
        "status": "ok"
    })
