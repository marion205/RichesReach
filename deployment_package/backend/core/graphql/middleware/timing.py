"""
GraphQL profiling middleware: resolver timing + DB query count.

Toggle via env GRAPHQL_PROFILING=1 or header X-GraphQL-Profiling: 1.
When enabled, logs for each resolver: name, duration_ms, db_query_count.

DB query count is only available when Django DEBUG=True (connection.queries);
otherwise duration is still logged and query_count is reported as N/A.
"""
import logging
import os
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)


def _profiling_enabled(context: Any) -> bool:
    """True if profiling is enabled by env or request header."""
    if os.getenv("GRAPHQL_PROFILING", "").lower() in ("1", "true", "yes"):
        return True
    if not context or not hasattr(context, "request"):
        return False
    req = getattr(context.request, "META", None) or getattr(context.request, "headers", None)
    if not req:
        return False
    # META: HTTP_X_GRAPHQL_PROFILING; headers: X-GraphQL-Profiling
    if hasattr(req, "get"):
        val = req.get("HTTP_X_GRAPHQL_PROFILING") or req.get("X-GraphQL-Profiling")
        return str(val).strip() in ("1", "true", "yes")
    return False


def _get_resolver_name(info: Any) -> str:
    """Human-readable resolver name from GraphQL resolve info."""
    if not info:
        return "unknown"
    field_name = getattr(info, "field_name", None)
    if field_name:
        return str(field_name)
    parent = getattr(info, "parent_type", None)
    if parent is not None:
        return getattr(parent, "name", str(parent))
    return "unknown"


def _initial_query_count() -> int:
    """
    Return current number of DB queries so far (for delta after resolver).
    When DEBUG is False, connection.queries is not populated; return 0 (caller will log N/A).
    """
    try:
        from django.db import connection

        if not getattr(connection, "queries", None):
            return -1
        return len(connection.queries)
    except Exception:
        return -1


def _query_count_since(initial: int) -> int:
    """Return number of queries executed since initial count. -1 if not available."""
    try:
        from django.db import connection

        if not getattr(connection, "queries", None):
            return -1
        return len(connection.queries) - initial
    except Exception:
        return -1


class GraphQLProfilingMiddleware:
    """
    Graphene-Django middleware that logs resolver name, duration (ms), and DB query count.
    Only runs when GRAPHQL_PROFILING=1 or X-GraphQL-Profiling: 1.
    """

    def resolve(self, next: Callable, root: Any, info: Any, **kwargs: Any) -> Any:
        if not _profiling_enabled(info.context):
            return next(root, info, **kwargs)

        resolver_name = _get_resolver_name(info)
        initial_queries = _initial_query_count()
        start = time.perf_counter()
        try:
            result = next(root, info, **kwargs)
            return result
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            query_count = _query_count_since(initial_queries) if initial_queries >= 0 else -1
            if query_count >= 0:
                logger.info(
                    "GRAPHQL_PROFILING resolver=%s duration_ms=%.2f db_queries=%d",
                    resolver_name,
                    duration_ms,
                    query_count,
                )
            else:
                logger.info(
                    "GRAPHQL_PROFILING resolver=%s duration_ms=%.2f db_queries=N/A",
                    resolver_name,
                    duration_ms,
                )
