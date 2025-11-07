from django.urls import re_path
from . import consumers
from .family_websocket import FamilyOrbSyncConsumer

websocket_urlpatterns = [
re_path(r'ws/stock-prices/$', consumers.StockPriceConsumer.as_asgi()),
re_path(r'ws/discussions/$', consumers.DiscussionConsumer.as_asgi()),
re_path(r'ws/portfolio/$', consumers.PortfolioConsumer.as_asgi()),
re_path(r'ws/family/orb-sync/$', FamilyOrbSyncConsumer.as_asgi()),
]
