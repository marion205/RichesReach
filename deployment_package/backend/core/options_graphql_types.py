# options_graphql_types.py
"""
GraphQL types for Options Edge Factory pipeline.
Exposes ReadyToTradeAnalysis (Flight Manuals) via GraphQL.
"""
import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth import get_user_model
import logging

from .options_models import (
    OptionsPortfolio,
    OptionsPosition,
    OptionsRegimeSnapshot
)

logger = logging.getLogger(__name__)
User = get_user_model()


# ========== Django Model Types ==========

class OptionsPortfolioType(DjangoObjectType):
    """User's options portfolio with aggregate Greeks"""
    
    class Meta:
        model = OptionsPortfolio
        fields = (
            'id',
            'user',
            'account_equity',
            'total_delta',
            'total_vega',
            'total_theta',
            'total_gamma',
            'total_risk_dollars',
            'total_positions_count',
            'experience_level',
            'risk_appetite',
            'created_at',
            'updated_at'
        )
    
    # CamelCase aliases for mobile
    accountEquity = graphene.Float()
    totalDelta = graphene.Float()
    totalVega = graphene.Float()
    totalTheta = graphene.Float()
    totalGamma = graphene.Float()
    totalRiskDollars = graphene.Float()
    totalPositionsCount = graphene.Int()
    experienceLevel = graphene.String()
    riskAppetite = graphene.Float()
    createdAt = graphene.DateTime()
    updatedAt = graphene.DateTime()
    
    def resolve_accountEquity(self, info):
        return float(self.account_equity)
    
    def resolve_totalDelta(self, info):
        return float(self.total_delta)
    
    def resolve_totalVega(self, info):
        return float(self.total_vega)
    
    def resolve_totalTheta(self, info):
        return float(self.total_theta)
    
    def resolve_totalGamma(self, info):
        return float(self.total_gamma)
    
    def resolve_totalRiskDollars(self, info):
        return float(self.total_risk_dollars)
    
    def resolve_totalPositionsCount(self, info):
        return self.total_positions_count
    
    def resolve_experienceLevel(self, info):
        return self.experience_level
    
    def resolve_riskAppetite(self, info):
        return float(self.risk_appetite)
    
    def resolve_createdAt(self, info):
        return self.created_at
    
    def resolve_updatedAt(self, info):
        return self.updated_at


class OptionsPositionLegType(graphene.ObjectType):
    """Single leg of an options position"""
    type = graphene.String(description="call or put")
    strike = graphene.Float()
    expiry = graphene.String(description="ISO date: YYYY-MM-DD")
    contracts = graphene.Int()
    side = graphene.String(description="buy or sell")
    premium = graphene.Float(description="Per-contract premium")


class OptionsPositionType(DjangoObjectType):
    """Single options position (may have multiple legs)"""
    
    class Meta:
        model = OptionsPosition
        fields = (
            'id',
            'portfolio',
            'ticker',
            'sector',
            'strategy_type',
            'legs',
            'contracts',
            'entry_price',
            'current_price',
            'position_delta',
            'position_vega',
            'position_theta',
            'position_gamma',
            'max_profit',
            'max_loss',
            'probability_of_profit',
            'realized_pnl',
            'unrealized_pnl',
            'regime_at_entry',
            'edge_score',
            'flight_manual',
            'is_closed',
            'opened_at',
            'closed_at',
            'created_at',
            'updated_at'
        )
    
    # Parse legs as structured objects
    legs_parsed = graphene.List(OptionsPositionLegType)
    
    # CamelCase aliases
    strategyType = graphene.String()
    entryPrice = graphene.Float()
    currentPrice = graphene.Float()
    positionDelta = graphene.Float()
    positionVega = graphene.Float()
    positionTheta = graphene.Float()
    positionGamma = graphene.Float()
    maxProfit = graphene.Float()
    maxLoss = graphene.Float()
    probabilityOfProfit = graphene.Float()
    realizedPnl = graphene.Float()
    unrealizedPnl = graphene.Float()
    regimeAtEntry = graphene.String()
    edgeScore = graphene.Float()
    flightManual = graphene.String()
    isClosed = graphene.Boolean()
    openedAt = graphene.DateTime()
    closedAt = graphene.DateTime()
    createdAt = graphene.DateTime()
    updatedAt = graphene.DateTime()
    
    def resolve_legs_parsed(self, info):
        """Convert JSON legs to structured objects"""
        import json
        legs_data = self.legs if isinstance(self.legs, list) else json.loads(self.legs)
        return [OptionsPositionLegType(**leg) for leg in legs_data]
    
    def resolve_strategyType(self, info):
        return self.strategy_type
    
    def resolve_entryPrice(self, info):
        return float(self.entry_price)
    
    def resolve_currentPrice(self, info):
        return float(self.current_price) if self.current_price else None
    
    def resolve_positionDelta(self, info):
        return float(self.position_delta)
    
    def resolve_positionVega(self, info):
        return float(self.position_vega)
    
    def resolve_positionTheta(self, info):
        return float(self.position_theta)
    
    def resolve_positionGamma(self, info):
        return float(self.position_gamma)
    
    def resolve_maxProfit(self, info):
        return float(self.max_profit)
    
    def resolve_maxLoss(self, info):
        return float(self.max_loss)
    
    def resolve_probabilityOfProfit(self, info):
        return float(self.probability_of_profit)
    
    def resolve_realizedPnl(self, info):
        return float(self.realized_pnl)
    
    def resolve_unrealizedPnl(self, info):
        return float(self.unrealized_pnl)
    
    def resolve_regimeAtEntry(self, info):
        return self.regime_at_entry
    
    def resolve_edgeScore(self, info):
        return float(self.edge_score) if self.edge_score else None
    
    def resolve_flightManual(self, info):
        return self.flight_manual
    
    def resolve_isClosed(self, info):
        return self.is_closed
    
    def resolve_openedAt(self, info):
        return self.opened_at
    
    def resolve_closedAt(self, info):
        return self.closed_at
    
    def resolve_createdAt(self, info):
        return self.created_at
    
    def resolve_updatedAt(self, info):
        return self.updated_at


class OptionsRegimeSnapshotType(DjangoObjectType):
    """Cached regime for a ticker"""
    
    class Meta:
        model = OptionsRegimeSnapshot
        fields = (
            'id',
            'ticker',
            'regime',
            'regime_confidence',
            'iv_rank',
            'regime_description',
            'last_updated',
            'created_at'
        )
    
    # CamelCase
    regimeConfidence = graphene.String()
    ivRank = graphene.Float()
    regimeDescription = graphene.String()
    lastUpdated = graphene.DateTime()
    createdAt = graphene.DateTime()
    
    def resolve_regimeConfidence(self, info):
        return self.regime_confidence
    
    def resolve_ivRank(self, info):
        return float(self.iv_rank)
    
    def resolve_regimeDescription(self, info):
        return self.regime_description
    
    def resolve_lastUpdated(self, info):
        return self.last_updated
    
    def resolve_createdAt(self, info):
        return self.created_at


# ========== Flight Manual Types (from pipeline) ==========

class FlightManualType(graphene.ObjectType):
    """One-screen trade plan with human-readable explanation"""
    
    # Header
    headline = graphene.String(
        description="e.g., 'Stable Drift: Collect Theta with Iron Condor'"
    )
    thesis_bullets = graphene.List(
        graphene.String,
        description="3-5 bullet points explaining the setup"
    )
    
    # Trade Details
    setup_description = graphene.String(
        description="e.g., 'Sell 100/105 call spread, sell 95/90 put spread, 21 DTE'"
    )
    entry_mechanics = graphene.String(
        description="How to enter (limit order price, timing)"
    )
    contracts = graphene.Int(description="Number of spreads to trade")
    risk_dollars = graphene.Float(description="Max loss in dollars")
    risk_pct_equity = graphene.Float(description="Max loss as % of equity")
    
    # Greeks Impact
    delta_impact = graphene.Float(description="Portfolio delta change")
    vega_impact = graphene.Float(description="Portfolio vega change")
    theta_impact = graphene.Float(description="Portfolio theta change")
    gamma_impact = graphene.Float(description="Portfolio gamma change")
    
    # Management Rules
    profit_rule = graphene.String(
        description="When to take profit (e.g., '50% max profit')"
    )
    stop_rule = graphene.String(
        description="When to cut loss (e.g., '2x credit received')"
    )
    time_rule = graphene.String(
        description="Time-based exit (e.g., 'Close at 7 DTE')"
    )
    fire_drill = graphene.String(
        description="What to do if things go wrong"
    )
    
    # Metrics
    max_profit_dollars = graphene.Float()
    max_loss_dollars = graphene.Float()
    probability_of_profit = graphene.Float(description="PoP as percentage")
    edge_score = graphene.Float(description="Composite score 0-100")
    confidence = graphene.String(description="HIGH, MEDIUM, LOW")
    
    # UI Hints
    action_recommended = graphene.Boolean(
        description="True if trade meets all criteria"
    )
    warnings = graphene.List(
        graphene.String,
        description="Risk warnings or limiting factors"
    )
    color_scheme = graphene.String(
        description="green, yellow, red (for UI rendering)"
    )
    
    # Raw data (for mobile to store)
    strategy_name = graphene.String()
    ticker = graphene.String()
    legs = graphene.JSONString(description="Raw legs data")


class OptionsAnalysisType(graphene.ObjectType):
    """Complete analysis output from Options Edge Factory pipeline"""
    
    # Market Context
    ticker = graphene.String()
    regime = graphene.String(description="Current market regime")
    regime_confidence = graphene.String(description="HIGH, MEDIUM, LOW")
    market_context = graphene.String(description="Human-readable regime explanation")
    iv_rank = graphene.Float(description="IV percentile 0-100")
    
    # Flight Manuals (top 3 strategies)
    flight_manuals = graphene.List(
        FlightManualType,
        description="Top 3 trade plans ranked by composite score"
    )
    
    # Portfolio State
    current_portfolio_delta = graphene.Float()
    current_portfolio_vega = graphene.Float()
    current_portfolio_risk_pct = graphene.Float(
        description="Total risk as % of equity"
    )
    
    # Metadata
    warnings = graphene.List(graphene.String)
    timestamp = graphene.DateTime()


# ========== Queries ==========

class OptionsQueries(graphene.ObjectType):
    """GraphQL queries for Options Edge Factory"""
    
    # Portfolio queries
    my_options_portfolio = graphene.Field(
        OptionsPortfolioType,
        description="Get current user's options portfolio"
    )
    
    options_positions = graphene.List(
        OptionsPositionType,
        ticker=graphene.String(),
        is_closed=graphene.Boolean(default_value=False),
        description="Get options positions (optionally filter by ticker/status)"
    )
    
    # Regime query
    options_regime = graphene.Field(
        OptionsRegimeSnapshotType,
        ticker=graphene.String(required=True),
        description="Get cached market regime for ticker"
    )
    
    # Main pipeline query
    options_analysis = graphene.Field(
        OptionsAnalysisType,
        ticker=graphene.String(required=True),
        experience_level=graphene.String(default_value="basic"),
        description="Get top 3 trade plans (Flight Manuals) for ticker"
    )
    
    # ========== Resolvers ==========
    
    def resolve_my_options_portfolio(self, info):
        """Get or create user's options portfolio"""
        user = info.context.user
        if not user.is_authenticated:
            return None
        
        portfolio, created = OptionsPortfolio.objects.get_or_create(
            user=user,
            defaults={'account_equity': 25000}  # Default starting equity
        )
        return portfolio
    
    def resolve_options_positions(self, info, ticker=None, is_closed=False):
        """Get user's options positions"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        try:
            portfolio = user.options_portfolio
        except OptionsPortfolio.DoesNotExist:
            return []
        
        positions = portfolio.positions.filter(is_closed=is_closed)
        
        if ticker:
            positions = positions.filter(ticker=ticker.upper())
        
        return positions.order_by('-opened_at')[:50]  # Limit to 50
    
    def resolve_options_regime(self, info, ticker):
        """Get cached regime snapshot"""
        try:
            return OptionsRegimeSnapshot.objects.get(ticker=ticker.upper())
        except OptionsRegimeSnapshot.DoesNotExist:
            return None
    
    def resolve_options_analysis(self, info, ticker, experience_level="basic"):
        """
        Main pipeline: Market Data → Regime → Router → Sizer → Flight Manual
        Returns top 3 trade plans ready for execution.
        """
        user = info.context.user
        if not user.is_authenticated:
            logger.warning("Unauthenticated user attempted options_analysis")
            return None
        
        try:
            # Get or create portfolio
            portfolio, _ = OptionsPortfolio.objects.get_or_create(
                user=user,
                defaults={'account_equity': 25000, 'experience_level': experience_level}
            )
            
            # Import pipeline components
            from .options_api_wiring import OptionsAnalysisPipeline
            from .options_adapter import build_portfolio_snapshot_from_db
            import os
            
            # Initialize pipeline
            polygon_api_key = os.getenv("POLYGON_API_KEY", "")
            if not polygon_api_key:
                logger.error("POLYGON_API_KEY not set")
                return OptionsAnalysisType(
                    ticker=ticker,
                    regime="UNKNOWN",
                    regime_confidence="LOW",
                    market_context="API key not configured",
                    flight_manuals=[],
                    warnings=["POLYGON_API_KEY not configured in environment"]
                )
            
            # Load config files
            import json
            config_dir = os.path.join(os.path.dirname(__file__), 'config')
            
            try:
                with open(os.path.join(config_dir, 'options_playbooks.json')) as f:
                    playbooks_config = json.load(f)
            except FileNotFoundError:
                logger.warning("options_playbooks.json not found, using empty config")
                playbooks_config = {}
            
            pipeline = OptionsAnalysisPipeline(
                polygon_api_key=polygon_api_key,
                playbooks_config=playbooks_config
            )
            
            # Run pipeline
            analysis = pipeline.get_ready_to_trade_plans(
                user_id=user.id,
                ticker=ticker.upper(),
                user_experience_level=experience_level
            )
            
            # Convert to GraphQL type
            flight_manuals = []
            for fm in analysis.flight_manuals:
                flight_manuals.append(FlightManualType(
                    headline=fm.headline,
                    thesis_bullets=fm.thesis_bullets,
                    setup_description=fm.setup_description,
                    entry_mechanics=fm.entry_mechanics,
                    contracts=fm.contracts,
                    risk_dollars=fm.risk_dollars,
                    risk_pct_equity=fm.risk_pct_equity,
                    delta_impact=fm.delta_impact,
                    vega_impact=fm.vega_impact,
                    theta_impact=fm.theta_impact,
                    gamma_impact=fm.gamma_impact,
                    profit_rule=fm.profit_rule,
                    stop_rule=fm.stop_rule,
                    time_rule=fm.time_rule,
                    fire_drill=fm.fire_drill,
                    max_profit_dollars=fm.max_profit_dollars,
                    max_loss_dollars=fm.max_loss_dollars,
                    probability_of_profit=fm.probability_of_profit,
                    edge_score=fm.edge_score,
                    confidence=fm.confidence,
                    action_recommended=fm.action_recommended,
                    warnings=fm.warnings,
                    color_scheme=fm.color_scheme,
                    strategy_name=fm.strategy_name,
                    ticker=fm.ticker,
                    legs=fm.legs
                ))
            
            return OptionsAnalysisType(
                ticker=ticker.upper(),
                regime=analysis.regime,
                regime_confidence=analysis.confidence_level,
                market_context=analysis.market_context,
                iv_rank=analysis.iv_rank if hasattr(analysis, 'iv_rank') else None,
                flight_manuals=flight_manuals,
                current_portfolio_delta=float(portfolio.total_delta),
                current_portfolio_vega=float(portfolio.total_vega),
                current_portfolio_risk_pct=float(
                    portfolio.total_risk_dollars / portfolio.account_equity * 100
                    if portfolio.account_equity > 0 else 0
                ),
                warnings=analysis.warnings,
                timestamp=timezone.now()
            )
            
        except Exception as e:
            logger.error(f"Error in options_analysis resolver: {e}", exc_info=True)
            return OptionsAnalysisType(
                ticker=ticker,
                regime="ERROR",
                regime_confidence="LOW",
                market_context=f"Pipeline error: {str(e)}",
                flight_manuals=[],
                warnings=[f"Error: {str(e)}"]
            )
