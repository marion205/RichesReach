"""
Net Worth Engine — GraphQL Types & Query Mixin
===============================================
Exposes NetWorthService history + live capture via GraphQL.
Registered in schema.py as NetWorthQueries.

Queries
-------
  netWorthHistory(days: Int)   →  NetWorthHistoryType
  net_worth_history(days: Int) →  NetWorthHistoryType  (snake_case alias)

On every query call the service also captures today's snapshot (idempotent),
so the chart always has a current data point without needing a separate mutation.
"""
import graphene
import logging

logger = logging.getLogger(__name__)


# ── GraphQL Types ─────────────────────────────────────────────────────────────

class NetWorthPointType(graphene.ObjectType):
    """A single daily net worth snapshot."""
    captured_at     = graphene.String(required=True)   # ISO date string
    net_worth       = graphene.Float(required=True)
    portfolio_value = graphene.Float(required=True)
    savings_balance = graphene.Float(required=True)
    debt            = graphene.Float(required=True)


class NetWorthHistoryType(graphene.ObjectType):
    """Full net worth history + derived metrics for the authenticated user."""
    user_id = graphene.Int(required=True)

    # Timeline
    history = graphene.List(graphene.NonNull(NetWorthPointType))

    # Current snapshot
    current_net_worth       = graphene.Float()
    current_portfolio_value = graphene.Float()
    current_savings_balance = graphene.Float()
    current_debt            = graphene.Float()

    # Change metrics
    change_7d          = graphene.Float()
    change_30d         = graphene.Float()
    change_90d         = graphene.Float()
    change_1yr         = graphene.Float()
    change_pct_30d     = graphene.Float()

    # Records (within query window)
    all_time_high      = graphene.Float()
    all_time_high_date = graphene.String()   # ISO date
    all_time_low       = graphene.Float()
    all_time_low_date  = graphene.String()   # ISO date

    # Growth streak
    increase_streak_days     = graphene.Int()
    snapshot_captured_today  = graphene.Boolean()

    headline_sentence = graphene.String()
    data_quality      = graphene.String()


# ── Query Mixin ───────────────────────────────────────────────────────────────

class NetWorthQueries(graphene.ObjectType):
    """
    GraphQL query mixin: exposes net worth history.
    Added to ExtendedQuery in schema.py.
    """

    net_worth_history = graphene.Field(
        NetWorthHistoryType,
        days=graphene.Int(
            default_value=365,
            description="Number of days of history to return (default 365)",
        ),
        description="Net worth history and derived metrics for the authenticated user",
    )
    netWorthHistory = graphene.Field(
        NetWorthHistoryType,
        days=graphene.Int(
            default_value=365,
            description="Number of days of history to return (default 365)",
        ),
        description="Net worth history (camelCase alias)",
    )

    def resolve_net_worth_history(self, info, days=365):
        return _resolve_net_worth(info, days)

    def resolve_netWorthHistory(self, info, days=365):
        return _resolve_net_worth(info, days)


# ── Shared resolver ───────────────────────────────────────────────────────────

def _resolve_net_worth(info, days: int) -> NetWorthHistoryType | None:
    try:
        from .graphql_utils import get_user_from_context
        from .net_worth_service import NetWorthService

        user = get_user_from_context(info.context)
        if not user or getattr(user, 'is_anonymous', True):
            return None

        svc = NetWorthService()

        # Capture today's snapshot on every query — idempotent (get_or_create)
        svc.capture_today_safe(user, source='on_demand')

        result = svc.get_history_safe(user, days=days)

        return NetWorthHistoryType(
            user_id=result.user_id,
            history=[
                NetWorthPointType(
                    captured_at=p.captured_at.isoformat(),
                    net_worth=p.net_worth,
                    portfolio_value=p.portfolio_value,
                    savings_balance=p.savings_balance,
                    debt=p.debt,
                )
                for p in result.history
            ],
            current_net_worth=result.current_net_worth,
            current_portfolio_value=result.current_portfolio_value,
            current_savings_balance=result.current_savings_balance,
            current_debt=result.current_debt,
            change_7d=result.change_7d,
            change_30d=result.change_30d,
            change_90d=result.change_90d,
            change_1yr=result.change_1yr,
            change_pct_30d=result.change_pct_30d,
            all_time_high=result.all_time_high,
            all_time_high_date=(
                result.all_time_high_date.isoformat()
                if result.all_time_high_date else None
            ),
            all_time_low=result.all_time_low,
            all_time_low_date=(
                result.all_time_low_date.isoformat()
                if result.all_time_low_date else None
            ),
            increase_streak_days=result.increase_streak_days,
            snapshot_captured_today=result.snapshot_captured_today,
            headline_sentence=result.headline_sentence,
            data_quality=result.data_quality,
        )
    except Exception as exc:
        logger.warning("NetWorthQueries resolver error: %s", exc)
        return None
