# marketdata/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # AI Options endpoints
    path("api/ai-options/recommendations", views.ai_options_recommendations, name='ai_options_recommendations'),
    path("api/ai-options/recommendations/", views.ai_options_recommendations, name='ai_options_recommendations_slash'),
    
    # Market data status
    path("api/market-data/status", views.market_data_status, name='market_data_status'),
]
