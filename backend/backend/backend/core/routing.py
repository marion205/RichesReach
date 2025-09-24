from django.urls import re_path
from . import consumers
websocket_urlpatterns = [
re_path(r'ws/stock-prices/$', consumers.StockPriceConsumer.as_asgi()),
re_path(r'ws/discussions/$', consumers.DiscussionConsumer.as_asgi()),
re_path(r'ws/portfolio/$', consumers.PortfolioConsumer.as_asgi()),
]
