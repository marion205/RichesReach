"""
Alpaca Integration URLs
"""

from django.urls import path
from . import views

app_name = 'alpaca_integration'

urlpatterns = [
    # OAuth endpoints
    path('oauth/authorize/', views.AlpacaOAuthView.as_view(), name='oauth_authorize'),
    path('oauth/callback/', views.AlpacaCallbackView.as_view(), name='oauth_callback'),
    
    # Account endpoints
    path('account/', views.AlpacaAccountView.as_view(), name='account'),
    
    # Positions endpoints
    path('positions/', views.AlpacaPositionsView.as_view(), name='positions'),
    
    # Orders endpoints
    path('orders/', views.AlpacaOrdersView.as_view(), name='orders'),
    path('orders/<str:order_id>/', views.AlpacaOrderDetailView.as_view(), name='order_detail'),
    
    # Market data endpoints
    path('market-data/', views.AlpacaMarketDataView.as_view(), name='market_data'),
    
    # Legacy endpoints for compatibility
    path('connect/', views.alpaca_connect, name='connect'),
    path('callback/', views.alpaca_callback, name='callback'),
]
