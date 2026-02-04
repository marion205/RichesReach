"""
GraphQL DataLoaders: per-request loaders attached to context to avoid N+1.
Use info.context.loaders.user_loader.load(id) in resolvers when available.
"""
from .context import get_loaders_for_context, create_loaders_for_request, GraphQLLoaders

__all__ = ["get_loaders_for_context", "create_loaders_for_request", "GraphQLLoaders"]
