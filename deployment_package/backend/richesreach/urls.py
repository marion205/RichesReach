"""
URL configuration for richesreach project.
"""
from django.contrib import admin
from django.urls import path, include
from core.views import graphql_view
from graphene_django.views import GraphQLView
from core.daytrading_test_schema import schema as daytrading_test_schema
from core.market_views import QuotesView
from core.wealth_circles_views import WealthCirclePostsView
from core.voices_views import VoicesListView
from core.ai_options_views import AIOptionsRecommendationsView
from core.auth_views import LoginView
from core.ai_async_views import chat_view, stream_chat_view, health_view

urlpatterns = [
    path('admin/', admin.site.urls),
    # GraphQL endpoint (main)
    path('graphql/', graphql_view, name='graphql'),
    # Test endpoint for day trading picks (isolated schema)
    path('graphql-daytrading-test/', GraphQLView.as_view(schema=daytrading_test_schema, graphiql=True), name='graphql-daytrading-test'),
    # Include core app URLs (banking endpoints)
    path('', include('core.banking_urls')),
    # Authentication endpoints
    path('api/auth/login/', LoginView.as_view(), name='auth_login'),
    # Alpaca OAuth endpoints
    path('api/auth/alpaca/', include('core.alpaca_oauth_urls')),
    # Market data endpoints
    path('api/market/quotes/', QuotesView.as_view(), name='market_quotes'),
    # Wealth circles endpoints
    path('api/wealth-circles/<str:circle_id>/posts/', WealthCirclePostsView.as_view(), name='wealth_circle_posts'),
    # Voice/TTS endpoints
    path('api/voices/', VoicesListView.as_view(), name='voices_list'),
    # AI Options endpoints
    path('api/ai-options/recommendations/', AIOptionsRecommendationsView.as_view(), name='ai_options_recommendations'),
    # Async AI Chat endpoints (requires ASGI)
    # Views are already decorated with async-aware decorators
    path('api/ai/chat/', chat_view, name='ai_chat'),
    path('api/ai/chat/stream/', stream_chat_view, name='ai_chat_stream'),
    path('api/ai/health/', health_view, name='ai_health'),
]

