from django.shortcuts import render
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from .authentication import get_user_from_token
import json

User = get_user_model()

class AuthenticatedGraphQLView(GraphQLView):
    def parse_body(self, request):
        """Parse the request body and extract the JWT token"""
        if request.content_type == 'application/json':
            try:
                body = json.loads(request.body.decode('utf-8'))
                # Extract token from Authorization header or variables
                auth_header = request.META.get('HTTP_AUTHORIZATION', '')
                print(f"🔐 Auth Debug - Header: {auth_header}")
                
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]  # Remove 'Bearer ' prefix
                    print(f"🔐 Auth Debug - Bearer token: {token[:20]}...")
                    user = get_user_from_token(token)
                    print(f"🔐 Auth Debug - User from token: {user}")
                    if user:
                        request.user = user
                        print(f"🔐 Auth Debug - Set request.user: {request.user}")
                elif auth_header.startswith('JWT '):
                    token = auth_header[4:]  # Remove 'JWT ' prefix
                    print(f"🔐 Auth Debug - JWT token: {token[:20]}...")
                    user = get_user_from_token(token)
                    print(f"🔐 Auth Debug - User from token: {user}")
                    if user:
                        request.user = user
                        print(f"🔐 Auth Debug - Set request.user: {request.user}")
                else:
                    print(f"🔐 Auth Debug - No valid auth header found")
                
                print(f"🔐 Auth Debug - Final request.user: {request.user}")
            except (json.JSONDecodeError, Exception):
                pass
        return super().parse_body(request)

# Create the view instance with the core schema
from .schema import schema
graphql_view = csrf_exempt(AuthenticatedGraphQLView.as_view(schema=schema, graphiql=True))
