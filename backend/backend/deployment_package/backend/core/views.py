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
if auth_header.startswith('Bearer '):
token = auth_header[7:] # Remove 'Bearer ' prefix
user = get_user_from_token(token)
if user:
request.user = user
elif auth_header.startswith('JWT '):
token = auth_header[4:] # Remove 'JWT ' prefix
user = get_user_from_token(token)
if user:
request.user = user
except (json.JSONDecodeError, Exception):
pass
return super().parse_body(request)
# Create the view instance with the core schema
from .schema import schema
graphql_view = csrf_exempt(AuthenticatedGraphQLView.as_view(schema=schema, graphiql=True))
