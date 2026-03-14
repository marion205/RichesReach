"""
Income Intelligence — GraphQL Types & Query Mixin
==================================================
Exposes IncomeIntelligenceService results via GraphQL.
Registered in schema.py as IncomeIntelligenceQueries.

Queries
-------
  incomeIntelligence   →  IncomeIntelligenceType
  income_intelligence  →  IncomeIntelligenceType  (snake_case alias)
"""
import graphene
import logging

logger = logging.getLogger(__name__)


# ── GraphQL Types ─────────────────────────────────────────────────────────────

class IncomeStreamType(graphene.ObjectType):
    """An aggregated income stream (salary, side hustle, etc.)."""
    stream_type       = graphene.String(required=True)   # salary | side_hustle | freelance | investment | other
    label             = graphene.String(required=True)   # Human-readable name
    monthly_amount    = graphene.Float(required=True)    # Estimated $/month
    annual_amount     = graphene.Float(required=True)    # Projected $/year
    transaction_count = graphene.Int(required=True)
    top_sources       = graphene.List(graphene.String)   # Top merchant names
    pct_of_total      = graphene.Float()                 # % of total income
    insight           = graphene.String()                # 1-sentence explanation


class IncomeIntelligenceType(graphene.ObjectType):
    """Full income classification for the authenticated user."""
    user_id = graphene.Int(required=True)

    # Totals
    total_monthly_income     = graphene.Float()
    total_annual_income      = graphene.Float()
    primary_income_monthly   = graphene.Float()    # Salary only
    secondary_income_monthly = graphene.Float()    # Side hustle + freelance

    # Diversity
    income_diversity_score   = graphene.Float()    # 0–100
    stream_count             = graphene.Int()

    # Breakdown
    streams = graphene.List(graphene.NonNull(IncomeStreamType))

    # Metadata
    lookback_days     = graphene.Int()
    headline_sentence = graphene.String()
    data_quality      = graphene.String()   # "actual" | "estimated" | "insufficient"


# ── Query Mixin ───────────────────────────────────────────────────────────────

class IncomeIntelligenceQueries(graphene.ObjectType):
    """
    GraphQL query mixin: exposes Income Intelligence classification.
    Added to ExtendedQuery in schema.py.
    """

    income_intelligence = graphene.Field(
        IncomeIntelligenceType,
        description="Classify bank deposits into income streams (salary, side hustle, etc.)",
    )
    incomeIntelligence = graphene.Field(
        IncomeIntelligenceType,
        description="Income intelligence (camelCase alias)",
    )

    def resolve_income_intelligence(self, info):
        return _resolve_income_intelligence(info)

    def resolve_incomeIntelligence(self, info):
        return _resolve_income_intelligence(info)


# ── Shared resolver logic ─────────────────────────────────────────────────────

def _resolve_income_intelligence(info) -> IncomeIntelligenceType | None:
    try:
        from .graphql_utils import get_user_from_context
        from .income_intelligence_service import IncomeIntelligenceService

        user = get_user_from_context(info.context)
        if not user or getattr(user, 'is_anonymous', True):
            return None

        result = IncomeIntelligenceService().analyze_safe(user)

        return IncomeIntelligenceType(
            user_id=result.user_id,
            total_monthly_income=result.total_monthly_income,
            total_annual_income=result.total_annual_income,
            primary_income_monthly=result.primary_income_monthly,
            secondary_income_monthly=result.secondary_income_monthly,
            income_diversity_score=result.income_diversity_score,
            stream_count=result.stream_count,
            streams=[
                IncomeStreamType(
                    stream_type=s.stream_type,
                    label=s.label,
                    monthly_amount=s.monthly_amount,
                    annual_amount=s.annual_amount,
                    transaction_count=s.transaction_count,
                    top_sources=s.top_sources,
                    pct_of_total=s.pct_of_total,
                    insight=s.insight,
                )
                for s in result.streams
            ],
            lookback_days=result.lookback_days,
            headline_sentence=result.headline_sentence,
            data_quality=result.data_quality,
        )
    except Exception as exc:
        logger.warning("IncomeIntelligenceQueries resolver error: %s", exc)
        return None
