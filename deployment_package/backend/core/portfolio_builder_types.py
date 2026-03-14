"""
AI Portfolio Builder — GraphQL Types & Query Mixin
====================================================
Exposes PortfolioBuilderService results via GraphQL.
Registered in schema.py as PortfolioBuilderQueries.

Queries
-------
  buildPortfolio(monthlyAmount: Float!, riskPreference: String) → PortfolioBuilderResultType
  build_portfolio(monthly_amount: Float!, risk_preference: String) → PortfolioBuilderResultType (snake_case alias)
"""
import graphene
import logging

logger = logging.getLogger(__name__)


# ── GraphQL Types ─────────────────────────────────────────────────────────────

class AllocationSliceType(graphene.ObjectType):
    """A single slice of the portfolio allocation."""
    strategy_id = graphene.String(required=True)
    strategy_name = graphene.String(required=True)
    percentage = graphene.Float(required=True)
    monthly_amount = graphene.Float(required=True)
    annual_amount = graphene.Float(required=True)
    color = graphene.String(required=True)
    icon = graphene.String(required=True)
    primary_etf = graphene.String(required=True)
    primary_etf_name = graphene.String(required=True)
    rationale = graphene.String(required=True)


class ProjectedMilestoneType(graphene.ObjectType):
    """A milestone in the wealth journey."""
    years = graphene.Int(required=True)
    value = graphene.Float(required=True)
    label = graphene.String(required=True)


class PortfolioBuilderResultType(graphene.ObjectType):
    """Complete portfolio builder output."""
    user_id = graphene.Int(required=True)
    monthly_amount = graphene.Float(required=True)
    annual_amount = graphene.Float(required=True)
    
    risk_profile = graphene.String(required=True)
    risk_rationale = graphene.String(required=True)
    
    allocations = graphene.List(graphene.NonNull(AllocationSliceType))
    
    projected_10yr = graphene.Float()
    projected_20yr = graphene.Float()
    projected_30yr = graphene.Float()
    expected_return_rate = graphene.Float()
    
    milestones = graphene.List(graphene.NonNull(ProjectedMilestoneType))
    
    headline = graphene.String()
    portfolio_adjustments = graphene.List(graphene.String)
    warnings = graphene.List(graphene.String)
    
    data_quality = graphene.String()


# ── Query Mixin ───────────────────────────────────────────────────────────────

class PortfolioBuilderQueries(graphene.ObjectType):
    """
    GraphQL query mixin: exposes AI Portfolio Builder.
    Added to ExtendedQuery in schema.py.
    """
    
    build_portfolio = graphene.Field(
        PortfolioBuilderResultType,
        monthly_amount=graphene.Float(required=True, description="Amount to invest per month"),
        risk_preference=graphene.String(description="Optional risk preference: conservative, moderate, aggressive"),
        description="Build a personalized portfolio allocation based on financial context",
    )
    buildPortfolio = graphene.Field(
        PortfolioBuilderResultType,
        monthly_amount=graphene.Float(required=True, description="Amount to invest per month"),
        risk_preference=graphene.String(description="Optional risk preference: conservative, moderate, aggressive"),
        description="Build portfolio (camelCase alias)",
    )
    
    def resolve_build_portfolio(self, info, monthly_amount: float, risk_preference: str = None):
        return _resolve_build_portfolio(info, monthly_amount, risk_preference)
    
    def resolve_buildPortfolio(self, info, monthly_amount: float, risk_preference: str = None):
        return _resolve_build_portfolio(info, monthly_amount, risk_preference)


# ── Shared resolver logic ─────────────────────────────────────────────────────

def _resolve_build_portfolio(info, monthly_amount: float, risk_preference: str = None) -> PortfolioBuilderResultType | None:
    try:
        from .graphql_utils import get_user_from_context
        from .portfolio_builder_service import PortfolioBuilderService
        from .financial_graph_service import FinancialGraphService
        
        user = get_user_from_context(info.context)
        if not user or getattr(user, 'is_anonymous', True):
            return None
        
        # Fetch financial graph for personalized allocation
        graph_context = None
        try:
            graph_ctx = FinancialGraphService().build_graph_safe(user)
            if graph_ctx and graph_ctx.data_quality != 'insufficient':
                graph_context = graph_ctx
        except Exception as graph_err:
            logger.debug(f"Could not load financial graph: {graph_err}")
        
        result = PortfolioBuilderService().build_safe(
            user_id=user.id,
            monthly_amount=monthly_amount,
            risk_preference=risk_preference,
            graph_context=graph_context,
        )
        
        return PortfolioBuilderResultType(
            user_id=result.user_id,
            monthly_amount=result.monthly_amount,
            annual_amount=result.annual_amount,
            risk_profile=result.risk_profile,
            risk_rationale=result.risk_rationale,
            allocations=[
                AllocationSliceType(
                    strategy_id=a.strategy_id,
                    strategy_name=a.strategy_name,
                    percentage=a.percentage,
                    monthly_amount=a.monthly_amount,
                    annual_amount=a.annual_amount,
                    color=a.color,
                    icon=a.icon,
                    primary_etf=a.primary_etf,
                    primary_etf_name=a.primary_etf_name,
                    rationale=a.rationale,
                )
                for a in result.allocations
            ],
            projected_10yr=result.projected_10yr,
            projected_20yr=result.projected_20yr,
            projected_30yr=result.projected_30yr,
            expected_return_rate=result.expected_return_rate,
            milestones=[
                ProjectedMilestoneType(
                    years=m.years,
                    value=m.value,
                    label=m.label,
                )
                for m in result.milestones
            ],
            headline=result.headline,
            portfolio_adjustments=result.portfolio_adjustments,
            warnings=result.warnings,
            data_quality=result.data_quality,
        )
    except Exception as exc:
        logger.warning(f"PortfolioBuilderQueries resolver error: {exc}")
        return None
