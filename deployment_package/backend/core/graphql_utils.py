"""
GraphQL utility functions for consistent context access.
"""


def get_user_from_context(context):
    """
    Safely extract user from GraphQL context, supporting both object and dict styles.
    
    Args:
        context: GraphQL context (can be SimpleContext, dict, or Django request)
    
    Returns:
        User object or None
    """
    if context is None:
        return None
    
    # Try object-style access first
    user = getattr(context, "user", None)
    
    # Fallback to dict-style access
    if user is None and isinstance(context, dict):
        user = context.get("user")
    
    # Check if user is authenticated
    if user and hasattr(user, "is_authenticated"):
        if not user.is_authenticated:
            return None
    
    return user

