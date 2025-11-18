"""
URL routing for Alpaca OAuth endpoints
Add to your main urls.py:
    path('api/auth/alpaca/', include('core.alpaca_oauth_urls')),
"""
from django.urls import path
from .alpaca_oauth_views import (
    alpaca_oauth_initiate,
    alpaca_oauth_callback,
    alpaca_oauth_disconnect,
)

app_name = 'alpaca_oauth'

urlpatterns = [
    path('initiate', alpaca_oauth_initiate, name='oauth_initiate'),
    path('callback', alpaca_oauth_callback, name='oauth_callback'),
    path('disconnect', alpaca_oauth_disconnect, name='oauth_disconnect'),
]

