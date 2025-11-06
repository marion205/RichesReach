"""
URL routing for Broker API endpoints
Add to your main urls.py:
    path('broker/', include('core.broker_urls')),
"""
from django.urls import path
from .broker_views import (
    BrokerOnboardView,
    BrokerAccountView,
    BrokerOrdersView,
    BrokerPositionsView,
    BrokerActivitiesView,
    alpaca_webhook_trade_updates,
    alpaca_webhook_account_updates,
)

urlpatterns = [
    path('onboard', BrokerOnboardView.as_view(), name='broker_onboard'),
    path('account', BrokerAccountView.as_view(), name='broker_account'),
    path('orders', BrokerOrdersView.as_view(), name='broker_orders'),
    path('positions', BrokerPositionsView.as_view(), name='broker_positions'),
    path('activities', BrokerActivitiesView.as_view(), name='broker_activities'),
]

# Webhook endpoints (no authentication required, HMAC verified)
webhook_urlpatterns = [
    path('webhooks/alpaca/trade_updates', alpaca_webhook_trade_updates, name='alpaca_webhook_trade_updates'),
    path('webhooks/alpaca/account_updates', alpaca_webhook_account_updates, name='alpaca_webhook_account_updates'),
]

