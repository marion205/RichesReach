"""
Financial Health Score — GraphQL Types & Query Mixin
=====================================================
Exposes FinancialHealthService results via GraphQL.
Registered in schema.py as FinancialHealthQueries.

Queries
-------
  financialHealth   →  FinancialHealthType
  financial_health  →  FinancialHealthType  (snake_case alias)
"""
import graphene
import logging

logger = logging.getLogger(__name__)


# ── GraphQL Types ─────────────────────────────────────────────────────────────

class HealthPillarType(graphene.ObjectType):
    """A single scored pillar of financial health."""
    name           = graphene.String(required=True)   # savings_rate | emergency_fund | debt_ratio | credit_utilization
    label          = graphene.String(required=True)   # Human-readable name
    score          = graphene.Float(required=True)    # 0–100
    grade          = graphene.String(required=True)   # A / B / C / D / F
    value          = graphene.Float()                 # Raw metric (may be null if no data)
    unit           = graphene.String(required=True)   # "%" or "months"
    insight        = graphene.String(required=True)   # 1-sentence explanation
    action         = graphene.String(required=True)   # Concrete next step
    weight         = graphene.Float(required=True)    # Contribution to composite (0–1)


class FinancialHealthType(graphene.ObjectType):
    """Composite financial health score for the authenticated user."""
    user_id        = graphene.Int(required=True)

    # Composite
    score          = graphene.Float(required=True)    # 0–100
    grade          = graphene.String(required=True)   # A–F
    headline_sentence = graphene.String()
    data_quality   = graphene.String()                # "actual" | "estimated" | "insufficient"

    # Individual pillars
    pillars        = graphene.List(graphene.NonNull(HealthPillarType))

    # Raw inputs (handy for UI display without re-deriving)
    savings_rate_pct      = graphene.Float()
    monthly_income        = graphene.Float()
    monthly_debt_service  = graphene.Float()
    debt_to_income_pct    = graphene.Float()
    emergency_fund_months = graphene.Float()
    credit_utilization_pct = graphene.Float()


# ── Query Mixin ───────────────────────────────────────────────────────────────

class FinancialHealthQueries(graphene.ObjectType):
    """
    GraphQL query mixin: exposes the Financial Health Score.
    Added to ExtendedQuery in schema.py.
    """

    financial_health = graphene.Field(
        FinancialHealthType,
        description="Composite financial health score with pillar breakdown",
    )
    financialHealth = graphene.Field(
        FinancialHealthType,
        description="Financial health score (camelCase alias)",
    )

    def resolve_financial_health(self, info):
        return _resolve_financial_health(info)

    def resolve_financialHealth(self, info):
        return _resolve_financial_health(info)


# ── Shared resolver logic ─────────────────────────────────────────────────────

def _resolve_financial_health(info) -> FinancialHealthType | None:
    try:
        from .graphql_utils import get_user_from_context
        from .financial_health_service import FinancialHealthService

        user = get_user_from_context(info.context)
        if not user or getattr(user, 'is_anonymous', True):
            return None

        result = FinancialHealthService().score_safe(user)

        return FinancialHealthType(
            user_id=result.user_id,
            score=result.score,
            grade=result.grade,
            headline_sentence=result.headline_sentence,
            data_quality=result.data_quality,
            pillars=[
                HealthPillarType(
                    name=p.name,
                    label=p.label,
                    score=p.score,
                    grade=p.grade,
                    value=p.value,
                    unit=p.unit,
                    insight=p.insight,
                    action=p.action,
                    weight=p.weight,
                )
                for p in result.pillars
            ],
            savings_rate_pct=result.savings_rate_pct,
            monthly_income=result.monthly_income,
            monthly_debt_service=result.monthly_debt_service,
            debt_to_income_pct=result.debt_to_income_pct,
            emergency_fund_months=result.emergency_fund_months,
            credit_utilization_pct=result.credit_utilization_pct,
        )
    except Exception as exc:
        logger.warning("FinancialHealthQueries resolver error: %s", exc)
        return None
