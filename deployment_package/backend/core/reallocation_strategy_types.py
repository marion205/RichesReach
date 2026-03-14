"""
Reallocation Strategy — GraphQL Types & Query Mixin
=====================================================
Exposes ReallocationStrategyService results via GraphQL.
Registered in schema.py as ReallocationStrategyQueries.

Queries
-------
  reallocationStrategies(monthlyAmount: Float!) → ReallocationSuggestionType
  reallocation_strategies(monthly_amount: Float!) → ReallocationSuggestionType (snake_case alias)
"""
import graphene
import logging

logger = logging.getLogger(__name__)


# ── GraphQL Types ─────────────────────────────────────────────────────────────

class ProjectedOutcomeType(graphene.ObjectType):
    """Projected future value at a given return rate."""
    return_rate = graphene.Float(required=True)
    return_label = graphene.String(required=True)
    value_10yr = graphene.Float(required=True)
    value_20yr = graphene.Float(required=True)
    value_30yr = graphene.Float(required=True)


class ExampleAssetType(graphene.ObjectType):
    """A representative asset for a strategy category."""
    symbol = graphene.String(required=True)
    name = graphene.String(required=True)
    description = graphene.String(required=True)
    asset_class = graphene.String(required=True)


class StrategyCategoryType(graphene.ObjectType):
    """An investment strategy category with examples and projections."""
    id = graphene.String(required=True)
    name = graphene.String(required=True)
    tagline = graphene.String(required=True)
    icon = graphene.String(required=True)
    color = graphene.String(required=True)
    
    risk_level = graphene.String(required=True)
    time_horizon = graphene.String(required=True)
    
    examples = graphene.List(graphene.NonNull(ExampleAssetType))
    projections = graphene.List(graphene.NonNull(ProjectedOutcomeType))
    
    graph_rationale = graphene.String()
    fit_score = graphene.Int()
    warning = graphene.String()


class ReallocationSuggestionType(graphene.ObjectType):
    """Full suggestion output for a given freed amount."""
    user_id = graphene.Int(required=True)
    monthly_amount = graphene.Float(required=True)
    annual_amount = graphene.Float(required=True)
    
    strategies = graphene.List(graphene.NonNull(StrategyCategoryType))
    
    headline_sentence = graphene.String()
    current_portfolio_summary = graphene.String()
    data_quality = graphene.String()


# ── Query Mixin ───────────────────────────────────────────────────────────────

class ReallocationStrategyQueries(graphene.ObjectType):
    """
    GraphQL query mixin: exposes Reallocation Strategy suggestions.
    Added to ExtendedQuery in schema.py.
    """
    
    reallocation_strategies = graphene.Field(
        ReallocationSuggestionType,
        monthly_amount=graphene.Float(required=True, description="Freed money per month"),
        description="Get investment strategy suggestions for freed/reallocated money",
    )
    reallocationStrategies = graphene.Field(
        ReallocationSuggestionType,
        monthly_amount=graphene.Float(required=True, description="Freed money per month"),
        description="Reallocation strategies (camelCase alias)",
    )
    
    def resolve_reallocation_strategies(self, info, monthly_amount: float):
        return _resolve_reallocation(info, monthly_amount)
    
    def resolve_reallocationStrategies(self, info, monthly_amount: float):
        return _resolve_reallocation(info, monthly_amount)


# ── Shared resolver logic ─────────────────────────────────────────────────────

def _resolve_reallocation(info, monthly_amount: float) -> ReallocationSuggestionType | None:
    try:
        from .graphql_utils import get_user_from_context
        from .reallocation_strategy_service import ReallocationStrategyService
        from .financial_graph_service import FinancialGraphService
        
        user = get_user_from_context(info.context)
        if not user or getattr(user, 'is_anonymous', True):
            return None
        
        # Fetch financial graph for personalized rationale
        graph_context = None
        try:
            graph_ctx = FinancialGraphService().build_graph_safe(user)
            if graph_ctx and graph_ctx.data_quality != 'insufficient':
                graph_context = graph_ctx
        except Exception as graph_err:
            logger.debug(f"Could not load financial graph: {graph_err}")
        
        result = ReallocationStrategyService().suggest_safe(
            user_id=user.id,
            monthly_amount=monthly_amount,
            graph_context=graph_context,
        )
        
        return ReallocationSuggestionType(
            user_id=result.user_id,
            monthly_amount=result.monthly_amount,
            annual_amount=result.annual_amount,
            strategies=[
                StrategyCategoryType(
                    id=s.id,
                    name=s.name,
                    tagline=s.tagline,
                    icon=s.icon,
                    color=s.color,
                    risk_level=s.risk_level,
                    time_horizon=s.time_horizon,
                    examples=[
                        ExampleAssetType(
                            symbol=e.symbol,
                            name=e.name,
                            description=e.description,
                            asset_class=e.asset_class,
                        )
                        for e in s.examples
                    ],
                    projections=[
                        ProjectedOutcomeType(
                            return_rate=p.return_rate,
                            return_label=p.return_label,
                            value_10yr=p.value_10yr,
                            value_20yr=p.value_20yr,
                            value_30yr=p.value_30yr,
                        )
                        for p in s.projections
                    ],
                    graph_rationale=s.graph_rationale,
                    fit_score=s.fit_score,
                    warning=s.warning,
                )
                for s in result.strategies
            ],
            headline_sentence=result.headline_sentence,
            current_portfolio_summary=result.current_portfolio_summary,
            data_quality=result.data_quality,
        )
    except Exception as exc:
        logger.warning(f"ReallocationStrategyQueries resolver error: {exc}")
        return None
