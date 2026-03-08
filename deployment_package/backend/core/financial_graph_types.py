"""
Financial Intelligence Graph — GraphQL Types & Query Mixin
==========================================================
Exposes the FinancialGraphContext computed by FinancialGraphService
via GraphQL. Registered in schema.py as FinancialGraphQueries.

Queries:
  financialGraph  →  FinancialGraphType
  financial_graph →  FinancialGraphType  (snake_case alias)
"""
import graphene
import logging

logger = logging.getLogger(__name__)


# ── GraphQL Types ─────────────────────────────────────────────────────────────

class GraphEdgeType(graphene.ObjectType):
    """A single computed cross-silo relationship edge."""
    relationship_id = graphene.String(required=True)
    source_label = graphene.String(required=True)
    target_label = graphene.String(required=True)
    explanation = graphene.String(required=True)
    numeric_impact = graphene.Float()
    unit = graphene.String()
    direction = graphene.String(required=True)   # "positive" | "negative" | "neutral"
    confidence = graphene.Float(required=True)


class FinancialGraphType(graphene.ObjectType):
    """Full financial intelligence graph for the authenticated user."""
    user_id = graphene.Int(required=True)
    edges = graphene.List(graphene.NonNull(GraphEdgeType))
    summary_sentences = graphene.List(graphene.String)

    # Raw silo snapshots
    total_cc_balance = graphene.Float()
    total_cc_min_payments = graphene.Float()
    total_savings_balance = graphene.Float()
    emergency_fund_months = graphene.Float()
    avg_credit_utilization = graphene.Float()
    best_credit_score = graphene.Int()
    estimated_monthly_income = graphene.Float()
    investable_surplus_monthly = graphene.Float()
    portfolio_total_value = graphene.Float()


# ── Query Mixin ───────────────────────────────────────────────────────────────

class FinancialGraphQueries(graphene.ObjectType):
    """
    GraphQL query mixin: exposes the financial intelligence graph.
    Added to ExtendedQuery in schema.py.
    """

    financial_graph = graphene.Field(
        FinancialGraphType,
        description="Cross-silo financial relationship graph for the authenticated user",
    )
    # camelCase alias for mobile GraphQL clients
    financialGraph = graphene.Field(
        FinancialGraphType,
        description="Cross-silo financial relationship graph (camelCase alias)",
    )

    def resolve_financial_graph(self, info):
        return _resolve_graph(info)

    def resolve_financialGraph(self, info):
        return _resolve_graph(info)


# ── Shared resolver logic ─────────────────────────────────────────────────────

def _resolve_graph(info):
    try:
        from .graphql_utils import get_user_from_context
        from .financial_graph_service import FinancialGraphService, GraphEdge

        user = get_user_from_context(info.context)
        if not user or getattr(user, 'is_anonymous', True):
            return None

        ctx = FinancialGraphService().build_graph_safe(user)
        if ctx is None:
            return None

        return FinancialGraphType(
            user_id=ctx.user_id,
            edges=[
                GraphEdgeType(
                    relationship_id=e.relationship_id,
                    source_label=e.source_label,
                    target_label=e.target_label,
                    explanation=e.explanation,
                    numeric_impact=e.numeric_impact,
                    unit=e.unit,
                    direction=e.direction,
                    confidence=e.confidence,
                )
                for e in ctx.edges
            ],
            summary_sentences=ctx.summary_sentences,
            total_cc_balance=ctx.total_cc_balance,
            total_cc_min_payments=ctx.total_cc_min_payments,
            total_savings_balance=ctx.total_savings_balance,
            emergency_fund_months=ctx.emergency_fund_months,
            avg_credit_utilization=ctx.avg_credit_utilization,
            best_credit_score=ctx.best_credit_score,
            estimated_monthly_income=ctx.estimated_monthly_income,
            investable_surplus_monthly=ctx.investable_surplus_monthly,
            portfolio_total_value=ctx.portfolio_total_value,
        )
    except Exception as exc:
        logger.warning("FinancialGraphQueries resolver error: %s", exc)
        return None
