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
        # Always call super first to parse the body
        result = super().parse_body(request)
        
        # Then try to extract and validate the token
        if request.content_type == 'application/json':
            try:
                auth_header = request.META.get('HTTP_AUTHORIZATION', '')
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]  # Remove 'Bearer ' prefix
                    try:
                        user = get_user_from_token(token)
                        if user:
                            request.user = user
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"Token validation failed: {e}")
                        # If token validation fails, continue without user
                        pass
                elif auth_header.startswith('JWT '):
                    token = auth_header[4:]  # Remove 'JWT ' prefix
                    try:
                        user = get_user_from_token(token)
                        if user:
                            request.user = user
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"Token validation failed: {e}")
                        # If token validation fails, continue without user
                        pass
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Error in parse_body: {e}")
                # If anything fails, continue without authentication
                pass
        
        return result
    
    def get_context(self, request):
        """Override to ensure user and DataLoaders are in GraphQL context"""
        context = super().get_context(request)
        if hasattr(request, "user") and request.user and not request.user.is_anonymous:
            context.user = request.user
        try:
            from core.graphql.dataloaders import create_loaders_for_request
            context.loaders = create_loaders_for_request()
        except Exception:
            context.loaders = None
        return context


# Create the view instance with the core schema
from .schema import schema
# CSRF exempt because:
# 1. GraphQL endpoint uses Authorization: Bearer <token> header
# 2. No cookie-based sessions for GraphQL API
# 3. Stateless API design (JWT tokens)
# 4. Mobile app uses Bearer tokens exclusively
# See: CSRF_VERIFICATION_CHECKLIST.md for full justification
graphql_view = csrf_exempt(AuthenticatedGraphQLView.as_view(schema=schema, graphiql=True))
