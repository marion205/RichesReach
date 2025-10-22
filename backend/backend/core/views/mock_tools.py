"""
Mock tools for development, e.g., SBLOC simulation.
"""
import logging
from django.http import JsonResponse
from typing import Optional

logger = logging.getLogger(__name__)

def dev_sbloc_advance(request, advance_amount: Optional[float] = None):
    """
    Mock SBLOC advance for dev testing - advances status every 30s.
    """
    logger.info(f"Mock SBLOC advance requested: {advance_amount or 'default'}")
    # Simulate advance logic (e.g., update mock DB or cache)
    # In prod, replace with real SBLOC integration
    return JsonResponse({
        'status': 'advanced',
        'amount': advance_amount or 1000.0,
        'message': 'Mock advance completed (dev mode)',
        'next_advance_in': '30s'
    })
