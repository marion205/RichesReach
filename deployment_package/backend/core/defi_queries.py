"""
GraphQL Queries for DeFi Operations (AAVE, etc.)
"""
import graphene
import logging
from graphql_jwt.decorators import login_required
from graphql import GraphQLError
from graphene.types import JSONString

logger = logging.getLogger(__name__)


class DefiReserveType(graphene.ObjectType):
    """DeFi reserve information"""
    symbol = graphene.String()
    name = graphene.String()
    ltv = graphene.Float()  # Loan-to-value ratio
    liquidation_threshold = graphene.Float()
    can_be_collateral = graphene.Boolean()
    supply_apy = graphene.Float()
    variable_borrow_apy = graphene.Float()
    stable_borrow_apy = graphene.Float()


class DefiAccountType(graphene.ObjectType):
    """DeFi account information"""
    health_factor = graphene.Float()
    available_borrow_usd = graphene.Float()
    collateral_usd = graphene.Float()
    debt_usd = graphene.Float()
    ltv_weighted = graphene.Float()
    liq_threshold_weighted = graphene.Float()
    supplies = graphene.List(JSONString)
    borrows = graphene.List(JSONString)
    prices_usd = JSONString


class DefiQueries(graphene.ObjectType):
    """DeFi queries"""
    
    defi_reserves = graphene.List(DefiReserveType)
    defi_account = graphene.Field(DefiAccountType)
    
    @login_required
    def resolve_defi_reserves(self, info):
        """Get available DeFi reserves (AAVE, etc.)"""
        # This would fetch from actual DeFi protocol
        # For now, return mock data
        return [
            DefiReserveType(
                symbol='USDC',
                name='USD Coin',
                ltv=0.8,
                liquidation_threshold=0.85,
                can_be_collateral=True,
                supply_apy=0.02,
                variable_borrow_apy=0.04,
                stable_borrow_apy=0.03
            ),
            DefiReserveType(
                symbol='ETH',
                name='Ethereum',
                ltv=0.75,
                liquidation_threshold=0.80,
                can_be_collateral=True,
                supply_apy=0.01,
                variable_borrow_apy=0.05,
                stable_borrow_apy=0.04
            ),
        ]
    
    @login_required
    def resolve_defi_account(self, info):
        """Get user's DeFi account information"""
        user = info.context.user
        # This would fetch from actual DeFi protocol
        return DefiAccountType(
            health_factor=1.5,
            available_borrow_usd=10000.0,
            collateral_usd=20000.0,
            debt_usd=5000.0,
            ltv_weighted=0.25,
            liq_threshold_weighted=0.30,
            supplies=[],
            borrows=[],
            prices_usd={}
        )
    
    # Additional DeFi queries
    top_yields = graphene.List(
        'core.defi_mutations.YieldPoolType',
        limit=graphene.Int(),
        description="Get top yield opportunities"
    )
    topYields = graphene.List(
        'core.defi_mutations.YieldPoolType',
        limit=graphene.Int(),
        description="Get top yield opportunities (camelCase alias)"
    )
    
    ai_yield_optimizer = graphene.Field(
        'core.defi_mutations.YieldOptimizerResultType',
        userRiskTolerance=graphene.Float(),
        chain=graphene.String(),
        limit=graphene.Int(),
        description="Get AI-optimized yield portfolio"
    )
    aiYieldOptimizer = graphene.Field(
        'core.defi_mutations.YieldOptimizerResultType',
        userRiskTolerance=graphene.Float(),
        chain=graphene.String(),
        limit=graphene.Int(),
        description="Get AI-optimized yield portfolio (camelCase alias)"
    )
    
    pool_analytics = graphene.List(
        'core.defi_mutations.PoolAnalyticsPointType',
        poolId=graphene.String(required=True),
        days=graphene.Int(),
        description="Get pool analytics data"
    )
    poolAnalytics = graphene.List(
        'core.defi_mutations.PoolAnalyticsPointType',
        poolId=graphene.String(required=True),
        days=graphene.Int(),
        description="Get pool analytics data (camelCase alias)"
    )
    
    @login_required
    def resolve_top_yields(self, info, limit=20):
        """Get top yield opportunities"""
        from .defi_mutations import YieldPoolType
        # In production, query from DeFi protocols
        return [
            YieldPoolType(
                id="aave-v3-usdc",
                protocol="Aave V3",
                chain="ethereum",
                symbol="USDC",
                poolAddress="0x...",
                apy=8.5,
                tvl=2500000000,
                risk=0.2
            )
        ][:limit]
    
    def resolve_topYields(self, info, limit=20):
        """CamelCase alias for top_yields"""
        return self.resolve_top_yields(info, limit)
    
    @login_required
    def resolve_ai_yield_optimizer(self, info, userRiskTolerance=0.5, chain="ethereum", limit=8):
        """Get AI-optimized yield portfolio"""
        from .defi_mutations import YieldOptimizerResultType, OptimizedPoolType
        # In production, use ML to optimize
        return YieldOptimizerResultType(
            expectedApy=12.5,
            totalRisk=0.65,
            explanation="Optimized portfolio based on risk tolerance",
            optimizationStatus="OPTIMIZED",
            allocations=[
                OptimizedPoolType(
                    id="aave-v3-eth",
                    protocol="Aave V3",
                    apy=8.5,
                    tvl=1200000000,
                    risk=0.3,
                    symbol="ETH",
                    chain="ethereum",
                    weight=0.4
                )
            ]
        )
    
    def resolve_aiYieldOptimizer(self, info, userRiskTolerance=0.5, chain="ethereum", limit=8):
        """CamelCase alias for ai_yield_optimizer"""
        return self.resolve_ai_yield_optimizer(info, userRiskTolerance, chain, limit)
    
    @login_required
    def resolve_pool_analytics(self, info, poolId, days=30):
        """Get pool analytics"""
        from .defi_mutations import PoolAnalyticsPointType
        # In production, query historical data
        return [
            PoolAnalyticsPointType(
                date="2024-01-01",
                feeApy=6.2,
                ilEstimate=0.5,
                netApy=5.7
            )
        ]
    
    def resolve_poolAnalytics(self, info, poolId, days=30):
        """CamelCase alias for pool_analytics"""
        return self.resolve_pool_analytics(info, poolId, days)

