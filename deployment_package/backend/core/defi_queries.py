"""
GraphQL Queries for DeFi Operations
Serves live yield data from DefiLlama (cached in Redis/Postgres),
user positions, and AI-optimized portfolio allocations.
"""
import graphene
import logging
from graphql_jwt.decorators import login_required
from graphql import GraphQLError
from graphene.types import JSONString

logger = logging.getLogger(__name__)


class AchievementType(graphene.ObjectType):
    """DeFi achievement/badge"""
    id = graphene.String()
    title = graphene.String()
    description = graphene.String()
    icon = graphene.String()
    color = graphene.String()
    category = graphene.String()
    earned = graphene.Boolean()
    earned_at = graphene.String()
    progress = graphene.Float()


class PortfolioAnalyticsType(graphene.ObjectType):
    """DeFi portfolio analytics dashboard"""
    total_deposited_usd = graphene.Float()
    total_rewards_usd = graphene.Float()
    total_positions = graphene.Int()
    active_chains = graphene.List(graphene.String)
    active_protocols = graphene.List(graphene.String)
    realized_apy = graphene.Float()
    sharpe_ratio = graphene.Float()
    max_drawdown_estimate = graphene.Float()
    portfolio_diversity_score = graphene.Float()


class GhostWhisperType(graphene.ObjectType):
    """Ghost Whisper DeFi — AI recommendation"""
    message = graphene.String()
    action = graphene.String()
    confidence = graphene.Float()
    reasoning = graphene.String()
    suggested_pool = JSONString()


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
    """DeFi queries - powered by live DefiLlama data"""

    defi_reserves = graphene.List(DefiReserveType)
    defi_account = graphene.Field(DefiAccountType)

    @login_required
    def resolve_defi_reserves(self, info):
        """Get available DeFi reserves (AAVE, etc.)"""
        # Fetch lending-specific reserves from cached yield data
        try:
            from .defi_data_service import get_cached_yields
            yields = get_cached_yields(chain='all', limit=50)

            reserves = []
            seen_symbols = set()
            for y in yields:
                symbol = y.get('symbol', '')
                # Only show simple lending assets (not LP pairs)
                if '/' in symbol or '-' in symbol:
                    continue
                if symbol in seen_symbols:
                    continue
                seen_symbols.add(symbol)

                reserves.append(DefiReserveType(
                    symbol=symbol,
                    name=symbol,
                    ltv=0.75 if symbol in ('USDC', 'USDT', 'DAI') else 0.70,
                    liquidation_threshold=0.82 if symbol in ('USDC', 'USDT', 'DAI') else 0.78,
                    can_be_collateral=True,
                    supply_apy=y.get('apy', 0) / 100,  # Convert % to decimal
                    variable_borrow_apy=(y.get('apy', 0) + 2.0) / 100,
                    stable_borrow_apy=(y.get('apy', 0) + 1.5) / 100,
                ))

            if reserves:
                return reserves
        except Exception as e:
            logger.warning(f"Could not fetch live reserves, using defaults: {e}")

        # Fallback if no live data available yet
        return [
            DefiReserveType(
                symbol='USDC', name='USD Coin', ltv=0.8,
                liquidation_threshold=0.85, can_be_collateral=True,
                supply_apy=0.02, variable_borrow_apy=0.04, stable_borrow_apy=0.03
            ),
            DefiReserveType(
                symbol='ETH', name='Ethereum', ltv=0.75,
                liquidation_threshold=0.80, can_be_collateral=True,
                supply_apy=0.01, variable_borrow_apy=0.05, stable_borrow_apy=0.04
            ),
        ]

    @login_required
    def resolve_defi_account(self, info):
        """Get user's DeFi account information"""
        user = info.context.user

        # Check for active positions in database
        try:
            from .defi_models import UserDeFiPosition
            positions = UserDeFiPosition.objects.filter(
                user=user, is_active=True
            ).select_related('pool', 'pool__protocol')

            if positions.exists():
                total_value = sum(float(p.staked_value_usd) for p in positions)
                total_rewards = sum(float(p.rewards_earned) for p in positions)

                return DefiAccountType(
                    health_factor=1.5,  # Calculated from on-chain data in Phase 2
                    available_borrow_usd=total_value * 0.5,
                    collateral_usd=total_value,
                    debt_usd=0,
                    ltv_weighted=0.0,
                    liq_threshold_weighted=0.80,
                    supplies=[{
                        'symbol': p.pool.symbol,
                        'amount': str(p.staked_amount),
                        'valueUsd': float(p.staked_value_usd),
                    } for p in positions],
                    borrows=[],
                    prices_usd={}
                )
        except Exception as e:
            logger.warning(f"Could not fetch user DeFi positions: {e}")

        # Default for users with no positions
        return DefiAccountType(
            health_factor=0, available_borrow_usd=0,
            collateral_usd=0, debt_usd=0,
            ltv_weighted=0, liq_threshold_weighted=0,
            supplies=[], borrows=[], prices_usd={}
        )

    # ---- Yield queries (powered by DefiLlama) ----

    top_yields = graphene.List(
        'core.defi_mutations.YieldPoolType',
        chain=graphene.String(),
        limit=graphene.Int(),
        description="Get top yield opportunities from live DefiLlama data"
    )
    topYields = graphene.List(
        'core.defi_mutations.YieldPoolType',
        chain=graphene.String(),
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
    def resolve_top_yields(self, info, chain='all', limit=20):
        """Get top yield opportunities from live DefiLlama data"""
        from .defi_mutations import YieldPoolType

        try:
            from .defi_data_service import get_cached_yields
            yields = get_cached_yields(chain=chain or 'all', limit=limit)

            if yields:
                return [
                    YieldPoolType(
                        id=y.get('id', ''),
                        protocol=y.get('protocol', ''),
                        chain=y.get('chain', ''),
                        symbol=y.get('symbol', ''),
                        poolAddress=y.get('poolAddress', ''),
                        apy=y.get('apy', 0),
                        tvl=y.get('tvl', 0),
                        risk=y.get('risk', 0.5),
                    )
                    for y in yields
                ][:limit]
        except Exception as e:
            logger.warning(f"Could not fetch live yields, using fallback: {e}")

        # Fallback if DefiLlama data not yet loaded
        return [
            YieldPoolType(
                id="aave-v3-usdc", protocol="Aave V3", chain="ethereum",
                symbol="USDC", poolAddress="", apy=8.5, tvl=2500000000, risk=0.2
            )
        ][:limit]

    def resolve_topYields(self, info, chain='all', limit=20):
        """CamelCase alias for top_yields"""
        return self.resolve_top_yields(info, chain, limit)

    @login_required
    def resolve_ai_yield_optimizer(self, info, userRiskTolerance=0.5, chain="ethereum", limit=8):
        """Get AI-optimized yield portfolio"""
        from .defi_mutations import YieldOptimizerResultType, OptimizedPoolType

        try:
            from .defi_data_service import get_ai_optimized_portfolio
            result = get_ai_optimized_portfolio(
                risk_tolerance=userRiskTolerance,
                chain=chain or 'ethereum',
                limit=limit,
            )

            allocations = [
                OptimizedPoolType(
                    id=a['id'],
                    protocol=a['protocol'],
                    apy=a['apy'],
                    tvl=a['tvl'],
                    risk=a['risk'],
                    symbol=a['symbol'],
                    chain=a['chain'],
                    weight=a['weight'],
                )
                for a in result.get('allocations', [])
            ]

            return YieldOptimizerResultType(
                expectedApy=result.get('expectedApy', 0),
                totalRisk=result.get('totalRisk', 0),
                explanation=result.get('explanation', ''),
                optimizationStatus=result.get('optimizationStatus', 'NO_DATA'),
                allocations=allocations,
            )
        except Exception as e:
            logger.warning(f"AI yield optimizer error, using fallback: {e}")

        # Fallback
        return YieldOptimizerResultType(
            expectedApy=0, totalRisk=0,
            explanation="Yield data is loading. Please try again in a moment.",
            optimizationStatus="LOADING", allocations=[]
        )

    def resolve_aiYieldOptimizer(self, info, userRiskTolerance=0.5, chain="ethereum", limit=8):
        """CamelCase alias for ai_yield_optimizer"""
        return self.resolve_ai_yield_optimizer(info, userRiskTolerance, chain, limit)

    @login_required
    def resolve_pool_analytics(self, info, poolId, days=30):
        """Get pool analytics from historical yield snapshots"""
        from .defi_mutations import PoolAnalyticsPointType

        try:
            from .defi_data_service import get_pool_analytics
            analytics = get_pool_analytics(pool_id=poolId, days=days)

            if analytics:
                return [
                    PoolAnalyticsPointType(
                        date=a['date'],
                        feeApy=a['feeApy'],
                        ilEstimate=a['ilEstimate'],
                        netApy=a['netApy'],
                    )
                    for a in analytics
                ]
        except Exception as e:
            logger.warning(f"Pool analytics error: {e}")

        return []

    def resolve_poolAnalytics(self, info, poolId, days=30):
        """CamelCase alias for pool_analytics"""
        return self.resolve_pool_analytics(info, poolId, days)

    # ---- Achievements ----

    defi_achievements = graphene.List(
        AchievementType,
        description="Get user's DeFi achievements and progress"
    )
    defiAchievements = graphene.List(
        AchievementType,
        description="Get user's DeFi achievements (camelCase alias)"
    )

    @login_required
    def resolve_defi_achievements(self, info):
        """Get user's DeFi achievement progress"""
        user = info.context.user
        try:
            from .defi_achievement_service import check_achievements
            achievements = check_achievements(user)
            return [
                AchievementType(
                    id=a['id'],
                    title=a['title'],
                    description=a['description'],
                    icon=a['icon'],
                    color=a['color'],
                    category=a.get('category', 'milestone'),
                    earned=a['earned'],
                    earned_at=str(a['earned_at']) if a.get('earned_at') else None,
                    progress=a['progress'],
                )
                for a in achievements
            ]
        except Exception as e:
            logger.warning(f"Could not fetch achievements: {e}")
            return []

    def resolve_defiAchievements(self, info):
        """CamelCase alias for defi_achievements"""
        return self.resolve_defi_achievements(info)

    # ---- Portfolio Analytics ----

    portfolio_analytics_summary = graphene.Field(
        PortfolioAnalyticsType,
        description="Get DeFi portfolio analytics (Sharpe ratio, diversity, drawdown)"
    )
    portfolioAnalytics = graphene.Field(
        PortfolioAnalyticsType,
        description="Get DeFi portfolio analytics (camelCase alias)"
    )

    @login_required
    def resolve_portfolio_analytics_summary(self, info):
        """Get comprehensive portfolio analytics"""
        user = info.context.user
        try:
            from .defi_achievement_service import get_portfolio_analytics
            analytics = get_portfolio_analytics(user)
            return PortfolioAnalyticsType(
                total_deposited_usd=analytics.get('total_deposited_usd', 0),
                total_rewards_usd=analytics.get('total_rewards_usd', 0),
                total_positions=analytics.get('total_positions', 0),
                active_chains=analytics.get('active_chains', []),
                active_protocols=analytics.get('active_protocols', []),
                realized_apy=analytics.get('realized_apy', 0),
                sharpe_ratio=analytics.get('sharpe_ratio', 0),
                max_drawdown_estimate=analytics.get('max_drawdown_estimate', 0),
                portfolio_diversity_score=analytics.get('portfolio_diversity_score', 0),
            )
        except Exception as e:
            logger.warning(f"Could not fetch portfolio analytics: {e}")
            return PortfolioAnalyticsType(
                total_deposited_usd=0, total_rewards_usd=0, total_positions=0,
                active_chains=[], active_protocols=[], realized_apy=0,
                sharpe_ratio=0, max_drawdown_estimate=0, portfolio_diversity_score=0,
            )

    def resolve_portfolioAnalytics(self, info):
        """CamelCase alias for portfolio_analytics_summary"""
        return self.resolve_portfolio_analytics_summary(info)

    # ---- Ghost Whisper DeFi (AI Recommendation) ----

    ghost_whisper = graphene.Field(
        GhostWhisperType,
        description="Get personalized Ghost Whisper DeFi recommendation"
    )
    ghostWhisper = graphene.Field(
        GhostWhisperType,
        description="Get Ghost Whisper recommendation (camelCase alias)"
    )

    @login_required
    def resolve_ghost_whisper(self, info):
        """Get personalized AI-driven DeFi recommendation"""
        user = info.context.user
        try:
            from .defi_achievement_service import get_ghost_whisper_recommendation
            rec = get_ghost_whisper_recommendation(user)
            return GhostWhisperType(
                message=rec.get('message', ''),
                action=rec.get('action', 'hold'),
                confidence=rec.get('confidence', 0),
                reasoning=rec.get('reasoning', ''),
                suggested_pool=rec.get('suggested_pool'),
            )
        except Exception as e:
            logger.warning(f"Ghost Whisper error: {e}")
            return GhostWhisperType(
                message="Your fortress awaits. Connect your wallet to begin.",
                action='deposit',
                confidence=0.5,
                reasoning='Unable to load personalized recommendation.',
                suggested_pool=None,
            )
