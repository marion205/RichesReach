"""
Opportunity Discovery — GraphQL Types & Query Mixin
====================================================
Exposes OpportunityDiscoveryService via GraphQL.
Registered in schema.py as OpportunityDiscoveryQueries.

Queries:
  opportunities(assetClass, minScore, includeGraphContext)  →  [OpportunityType]
  getOpportunities(...)                                     →  [OpportunityType]  (camelCase)
"""
import graphene
import logging

logger = logging.getLogger(__name__)


# ── GraphQL Types ─────────────────────────────────────────────────────────────

class OpportunityType(graphene.ObjectType):
    """A single curated investment opportunity with optional graph context."""
    id = graphene.ID(required=True)
    asset_class = graphene.String(required=True)
    name = graphene.String(required=True)
    tagline = graphene.String(required=True)
    score = graphene.Int(required=True)
    category = graphene.String(required=True)

    # Graph-aware fields
    graph_rationale = graphene.String()
    graph_edge_ids = graphene.List(graphene.String)

    # Display / filter metadata
    minimum_investment = graphene.Float()
    expected_return_range = graphene.String()
    liquidity = graphene.String()
    risk_level = graphene.String()


# ── Query Mixin ───────────────────────────────────────────────────────────────

class OpportunityDiscoveryQueries(graphene.ObjectType):
    """
    GraphQL query mixin: exposes multi-asset opportunity discovery.
    Added to ExtendedQuery in schema.py.
    """

    opportunities = graphene.List(
        OpportunityType,
        asset_class=graphene.String(
            description="Filter by asset class: real_estate | alternatives | fixed_income"
        ),
        min_score=graphene.Int(
            default_value=0,
            description="Exclude opportunities with score below this threshold",
        ),
        include_graph_context=graphene.Boolean(
            default_value=True,
            description="When true, injects the user's financial graph rationale into results",
        ),
        description="Multi-asset curated opportunity discovery with optional graph-aware ranking",
    )

    # camelCase alias for mobile clients
    getOpportunities = graphene.List(
        OpportunityType,
        asset_class=graphene.String(),
        min_score=graphene.Int(default_value=0),
        include_graph_context=graphene.Boolean(default_value=True),
        description="Multi-asset opportunity discovery (camelCase alias)",
    )

    def resolve_opportunities(
        self, info,
        asset_class=None,
        min_score=0,
        include_graph_context=True,
    ):
        return _resolve_opportunities(info, asset_class, min_score, include_graph_context)

    def resolve_getOpportunities(
        self, info,
        asset_class=None,
        min_score=0,
        include_graph_context=True,
    ):
        return _resolve_opportunities(info, asset_class, min_score, include_graph_context)


# ── Shared resolver logic ─────────────────────────────────────────────────────

def _resolve_opportunities(info, asset_class, min_score, include_graph_context):
    try:
        from .opportunity_discovery_service import OpportunityDiscoveryService

        graph_ctx = None
        if include_graph_context:
            try:
                from .graphql_utils import get_user_from_context
                from .financial_graph_service import FinancialGraphService
                user = get_user_from_context(info.context)
                if user and not getattr(user, 'is_anonymous', True):
                    graph_ctx = FinancialGraphService().build_graph_safe(user)
            except Exception as exc:
                logger.debug("Graph context unavailable for opportunity discovery: %s", exc)

        service = OpportunityDiscoveryService()
        opps = service.get_opportunities(
            asset_class=asset_class,
            graph_context=graph_ctx,
            min_score=min_score,
        )

        return [
            OpportunityType(
                id=o.id,
                asset_class=o.asset_class,
                name=o.name,
                tagline=o.tagline,
                score=o.score,
                category=o.category,
                graph_rationale=o.graph_rationale,
                graph_edge_ids=o.graph_edge_ids,
                minimum_investment=o.minimum_investment,
                expected_return_range=o.expected_return_range,
                liquidity=o.liquidity,
                risk_level=o.risk_level,
            )
            for o in opps
        ]
    except Exception as exc:
        logger.warning("OpportunityDiscoveryQueries resolver error: %s", exc)
        return []
