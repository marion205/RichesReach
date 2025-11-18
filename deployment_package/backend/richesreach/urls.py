"""
URL configuration for richesreach project.
"""
from django.contrib import admin
from django.urls import path, include
from core.views import graphql_view
from graphene_django.views import GraphQLView
from core.daytrading_test_schema import schema as daytrading_test_schema

urlpatterns = [
    path('admin/', admin.site.urls),
    # GraphQL endpoint (main)
    path('graphql/', graphql_view, name='graphql'),
    # Test endpoint for day trading picks (isolated schema)
    path('graphql-daytrading-test/', GraphQLView.as_view(schema=daytrading_test_schema, graphiql=True), name='graphql-daytrading-test'),
    # Include core app URLs (banking endpoints)
    path('', include('core.banking_urls')),
    # Alpaca OAuth endpoints
    path('api/auth/alpaca/', include('core.alpaca_oauth_urls')),
]

