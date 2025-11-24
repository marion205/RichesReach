"""
SimpleContext - A context wrapper for GraphQL that supports both object and dict access patterns.

This ensures that resolvers can access context.user whether the context is:
- A dict: context.get('user') or context['user']
- An object: context.user

Usage:
    ctx = SimpleContext(user=user, request=request)
    result = schema.execute(query, context_value=ctx)
"""


class SimpleContext:
    """
    A simple context object that supports both attribute and dict-style access.
    
    This makes it compatible with resolvers that expect:
    - info.context.user (object-style)
    - info.context.get('user') (dict-style)
    """
    
    def __init__(self, user=None, request=None, **kwargs):
        self.user = user
        self.request = request
        # Support additional attributes
        for k, v in kwargs.items():
            setattr(self, k, v)
    
    def get(self, key, default=None):
        """Dict-style access for compatibility"""
        return getattr(self, key, default)
    
    def __getitem__(self, key):
        """Dict-style access for compatibility"""
        return getattr(self, key)
    
    def __contains__(self, key):
        """Dict-style 'in' operator support"""
        return hasattr(self, key)

