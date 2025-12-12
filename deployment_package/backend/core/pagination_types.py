"""
GraphQL Pagination Types
Implements cursor-based pagination following Relay Connection spec
"""
import graphene
from typing import List, Optional, Tuple, Any
from django.core.paginator import Paginator


class PageInfoType(graphene.ObjectType):
    """Pagination metadata"""
    has_next_page = graphene.Boolean(description="Whether there are more items after this page")
    has_previous_page = graphene.Boolean(description="Whether there are more items before this page")
    start_cursor = graphene.String(description="Cursor for the first item in this page")
    end_cursor = graphene.String(description="Cursor for the last item in this page")


def create_cursor(item: Any, field: str = 'id') -> str:
    """Create a cursor from an item (typically using ID or timestamp)"""
    import base64
    cursor_value = str(getattr(item, field, item))
    return base64.b64encode(cursor_value.encode()).decode()


def decode_cursor(cursor: str) -> str:
    """Decode a cursor back to its original value"""
    import base64
    try:
        return base64.b64decode(cursor.encode()).decode()
    except Exception:
        return ""


def paginate_queryset(
    queryset,
    first: Optional[int] = None,
    after: Optional[str] = None,
    last: Optional[int] = None,
    before: Optional[str] = None,
    order_by: str = '-created_at',
    cursor_field: str = 'id'
) -> Tuple[List[Any], PageInfoType]:
    """
    Paginate a Django queryset using cursor-based pagination.
    
    Args:
        queryset: Django QuerySet to paginate
        first: Number of items to fetch after cursor
        after: Cursor to start after
        last: Number of items to fetch before cursor (not commonly used)
        before: Cursor to start before (not commonly used)
        order_by: Field to order by (default: '-created_at')
        cursor_field: Field to use for cursor (default: 'id')
    
    Returns:
        Tuple of (items, page_info)
    """
    # Apply ordering
    if order_by:
        queryset = queryset.order_by(order_by)
    
    # Default to first=20 if not specified
    if first is None and last is None:
        first = 20
    
    items = []
    has_next_page = False
    has_previous_page = False
    start_cursor = None
    end_cursor = None
    
    if after:
        # Decode cursor and filter
        cursor_value = decode_cursor(after)
        if order_by.startswith('-'):
            # Descending order
            field_name = order_by[1:]
            queryset = queryset.filter(**{f'{field_name}__lt': cursor_value})
        else:
            # Ascending order
            queryset = queryset.filter(**{f'{order_by}__gt': cursor_value})
    
    # Get items
    if first:
        # Fetch one extra to check if there's a next page
        items = list(queryset[:first + 1])
        has_next_page = len(items) > first
        if has_next_page:
            items = items[:first]
    elif last:
        # Reverse for "last" (less common)
        items = list(queryset[:last + 1])
        has_previous_page = len(items) > last
        if has_previous_page:
            items = items[:last]
        items = list(reversed(items))
    
    # Generate cursors
    if items:
        start_cursor = create_cursor(items[0], cursor_field)
        end_cursor = create_cursor(items[-1], cursor_field)
    
    # Check for previous page (if we have an after cursor, there's likely a previous page)
    if after:
        has_previous_page = True
    
    page_info = PageInfoType(
        has_next_page=has_next_page,
        has_previous_page=has_previous_page,
        start_cursor=start_cursor,
        end_cursor=end_cursor
    )
    
    return items, page_info

