"""
Subscription / Leak Detector — GraphQL Types & Query Mixin
===========================================================
Exposes SubscriptionDetector results via GraphQL.
Registered in schema.py as LeakDetectorQueries.

Queries
-------
  financialLeaks   →  LeakDetectorResultType
  financial_leaks  →  LeakDetectorResultType  (snake_case alias)
"""
import graphene
import logging

logger = logging.getLogger(__name__)


# ── GraphQL Types ─────────────────────────────────────────────────────────────

class DetectedSubscriptionType(graphene.ObjectType):
    """A single recurring charge detected in transaction history."""
    merchant_key   = graphene.String(required=True)
    display_name   = graphene.String(required=True)
    category       = graphene.String(required=True)
    cadence        = graphene.String(required=True)   # "monthly", "annual", etc.
    cadence_days   = graphene.Int(required=True)
    typical_amount = graphene.Float(required=True)
    monthly_cost   = graphene.Float(required=True)
    annual_cost    = graphene.Float(required=True)
    occurrences    = graphene.Int(required=True)
    last_charged   = graphene.String()   # ISO date string
    first_charged  = graphene.String()   # ISO date string
    confidence     = graphene.Float(required=True)
    is_likely_unused = graphene.Boolean(required=True)


class LeakDetectorResultType(graphene.ObjectType):
    """Full subscription / leak analysis for the authenticated user."""
    user_id = graphene.Int(required=True)

    subscriptions        = graphene.List(graphene.NonNull(DetectedSubscriptionType))
    subscription_count   = graphene.Int()
    likely_unused_count  = graphene.Int()

    total_monthly_leak   = graphene.Float()
    total_annual_leak    = graphene.Float()
    likely_unused_monthly = graphene.Float()
    likely_unused_annual  = graphene.Float()

    # Opportunity cost
    savings_impact_1yr   = graphene.Float()
    savings_impact_5yr   = graphene.Float()

    top_leak             = graphene.Field(DetectedSubscriptionType)
    headline_sentence    = graphene.String()
    data_quality         = graphene.String()


# ── Query Mixin ───────────────────────────────────────────────────────────────

class LeakDetectorQueries(graphene.ObjectType):
    """
    GraphQL query mixin: exposes subscription / financial leak detection.
    Added to ExtendedQuery in schema.py.
    """

    financial_leaks = graphene.Field(
        LeakDetectorResultType,
        description="Detect recurring subscription charges and financial leaks",
    )
    financialLeaks = graphene.Field(
        LeakDetectorResultType,
        description="Detect recurring subscription charges and financial leaks (camelCase alias)",
    )

    def resolve_financial_leaks(self, info):
        return _resolve_leaks(info)

    def resolve_financialLeaks(self, info):
        return _resolve_leaks(info)


# ── Shared resolver ───────────────────────────────────────────────────────────

def _resolve_leaks(info) -> LeakDetectorResultType | None:
    try:
        from .graphql_utils import get_user_from_context
        from .subscription_detector import SubscriptionDetector

        user = get_user_from_context(info.context)
        if not user or getattr(user, 'is_anonymous', True):
            return None

        result = SubscriptionDetector().detect_safe(user)

        return LeakDetectorResultType(
            user_id=result.user_id,
            subscriptions=[_sub_to_gql(s) for s in result.subscriptions],
            subscription_count=result.subscription_count,
            likely_unused_count=result.likely_unused_count,
            total_monthly_leak=result.total_monthly_leak,
            total_annual_leak=result.total_annual_leak,
            likely_unused_monthly=result.likely_unused_monthly,
            likely_unused_annual=result.likely_unused_annual,
            savings_impact_1yr=result.savings_impact_1yr,
            savings_impact_5yr=result.savings_impact_5yr,
            top_leak=_sub_to_gql(result.top_leak) if result.top_leak else None,
            headline_sentence=result.headline_sentence,
            data_quality=result.data_quality,
        )
    except Exception as exc:
        logger.warning("LeakDetectorQueries resolver error: %s", exc)
        return None


def _sub_to_gql(s) -> DetectedSubscriptionType:
    return DetectedSubscriptionType(
        merchant_key=s.merchant_key,
        display_name=s.display_name,
        category=s.category,
        cadence=s.cadence,
        cadence_days=s.cadence_days,
        typical_amount=s.typical_amount,
        monthly_cost=s.monthly_cost,
        annual_cost=s.annual_cost,
        occurrences=s.occurrences,
        last_charged=s.last_charged.isoformat() if s.last_charged else None,
        first_charged=s.first_charged.isoformat() if s.first_charged else None,
        confidence=s.confidence,
        is_likely_unused=s.is_likely_unused,
    )
