# core/routing.py
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/stock-prices/', consumers.StockPriceConsumer.as_asgi()),
    path('ws/notifications/', consumers.NotificationConsumer.as_asgi()),
]