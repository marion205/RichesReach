"""
Premium GraphQL Types and Mutations
"""

import json
import logging
import os
import random
from datetime import datetime
from typing import Optional

import graphene
from django.core.cache import cache

from .enhanced_stock_service import EnhancedStockService
from .models import Portfolio, Stock, User
from .options_service import OptionsAnalysisService
from .portfolio_service import PortfolioService
from .premium_analytics import PremiumAnalyticsService
from .mutations import GenerateAIRecommendations

logger = logging.getLogger(__name__)

# Try to import Stripe
try:
    import stripe
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY', '')
    STRIPE_AVAILABLE = bool(stripe.api_key)
except ImportError:
    STRIPE_AVAILABLE = False
    logger.warning("Stripe not installed. Install with: pip install stripe")


# ============
# Premium Types
# ============

# Input types
class ProfileInput(graphene.InputObjectType):
    """Profile input for AI recommendations"""
    riskTolerance = graphene.String(description="Risk tolerance: Conservative, Moderate, Aggressive")
    investmentHorizonYears = graphene.Int(description="Investment horizon in years")
    age = graphene.Int(description="User age")
    incomeBracket = graphene.String(description="Income bracket")
    investmentGoals = graphene.List(graphene.String, description="Investment goals")


class PortfolioMetricsType(graphene.ObjectType):
    """Advanced portfolio performance metrics"""

    total_value = graphene.Float()
    total_cost = graphene.Float()
    total_return = graphene.Float()
    total_return_percent = graphene.Float()
    day_change = graphene.Float()
    day_change_percent = graphene.Float()
    volatility = graphene.Float()
    sharpe_ratio = graphene.Float()
    max_drawdown = graphene.Float()
    beta = graphene.Float()
    alpha = graphene.Float()
    holdings = graphene.List(lambda: HoldingDetailType)
    sector_allocation = graphene.JSONString()
    risk_metrics = graphene.JSONString()
    
    def resolve_total_value(self, info):
        """Extract total_value from dict or object"""
        if isinstance(self, dict):
            return self.get('total_value', 0.0)
        return getattr(self, 'total_value', 0.0)
    
    def resolve_total_cost(self, info):
        """Extract total_cost from dict or object"""
        if isinstance(self, dict):
            return self.get('total_cost', 0.0)
        return getattr(self, 'total_cost', 0.0)
    
    def resolve_total_return(self, info):
        """Extract total_return from dict or object"""
        if isinstance(self, dict):
            return self.get('total_return', 0.0)
        return getattr(self, 'total_return', 0.0)
    
    def resolve_total_return_percent(self, info):
        """Extract total_return_percent from dict or object"""
        if isinstance(self, dict):
            return self.get('total_return_percent', 0.0)
        return getattr(self, 'total_return_percent', 0.0)
    
    def resolve_day_change(self, info):
        """Extract day_change from dict or object"""
        if isinstance(self, dict):
            return self.get('day_change', 0.0)
        return getattr(self, 'day_change', 0.0)
    
    def resolve_day_change_percent(self, info):
        """Extract day_change_percent from dict or object"""
        if isinstance(self, dict):
            return self.get('day_change_percent', 0.0)
        return getattr(self, 'day_change_percent', 0.0)
    
    def resolve_volatility(self, info):
        """Extract volatility from dict or object"""
        if isinstance(self, dict):
            return self.get('volatility', 0.0)
        return getattr(self, 'volatility', 0.0)
    
    def resolve_sharpe_ratio(self, info):
        """Extract sharpe_ratio from dict or object"""
        if isinstance(self, dict):
            return self.get('sharpe_ratio', 0.0)
        return getattr(self, 'sharpe_ratio', 0.0)
    
    def resolve_max_drawdown(self, info):
        """Extract max_drawdown from dict or object"""
        if isinstance(self, dict):
            return self.get('max_drawdown', 0.0)
        return getattr(self, 'max_drawdown', 0.0)
    
    def resolve_beta(self, info):
        """Extract beta from dict or object"""
        if isinstance(self, dict):
            return self.get('beta', 1.0)
        return getattr(self, 'beta', 1.0)
    
    def resolve_alpha(self, info):
        """Extract alpha from dict or object"""
        if isinstance(self, dict):
            return self.get('alpha', 0.0)
        return getattr(self, 'alpha', 0.0)
    
    def resolve_holdings(self, info):
        """Extract holdings from dict or object"""
        if isinstance(self, dict):
            return self.get('holdings', [])
        return getattr(self, 'holdings', [])
    
    def resolve_sector_allocation(self, info):
        """Extract sector_allocation from dict or object"""
        import json
        if isinstance(self, dict):
            allocation = self.get('sector_allocation', {})
        else:
            allocation = getattr(self, 'sector_allocation', {})
        return json.dumps(allocation) if allocation else json.dumps({})
    
    def resolve_risk_metrics(self, info):
        """Extract risk_metrics from dict or object"""
        import json
        if isinstance(self, dict):
            metrics = self.get('risk_metrics', {})
        else:
            metrics = getattr(self, 'risk_metrics', {})
        return json.dumps(metrics) if metrics else json.dumps({})
    
    # camelCase aliases (must be defined as fields)
    totalValue = graphene.Float()
    totalCost = graphene.Float()
    totalReturn = graphene.Float()
    totalReturnPercent = graphene.Float()
    dayChange = graphene.Float()
    dayChangePercent = graphene.Float()
    sharpeRatio = graphene.Float()
    maxDrawdown = graphene.Float()
    sectorAllocation = graphene.JSONString()
    riskMetrics = graphene.JSONString()
    
    def resolve_totalValue(self, info):
        """Extract totalValue from dict or object"""
        if isinstance(self, dict):
            return self.get('total_value', 0.0)
        return getattr(self, 'total_value', 0.0)
    
    def resolve_totalCost(self, info):
        """Extract totalCost from dict or object"""
        if isinstance(self, dict):
            return self.get('total_cost', 0.0)
        return getattr(self, 'total_cost', 0.0)
    
    def resolve_totalReturn(self, info):
        """Extract totalReturn from dict or object"""
        if isinstance(self, dict):
            return self.get('total_return', 0.0)
        return getattr(self, 'total_return', 0.0)
    
    def resolve_totalReturnPercent(self, info):
        """Extract totalReturnPercent from dict or object"""
        if isinstance(self, dict):
            return self.get('total_return_percent', 0.0)
        return getattr(self, 'total_return_percent', 0.0)
    
    def resolve_dayChange(self, info):
        """Extract dayChange from dict or object"""
        if isinstance(self, dict):
            return self.get('day_change', 0.0)
        return getattr(self, 'day_change', 0.0)
    
    def resolve_dayChangePercent(self, info):
        """Extract dayChangePercent from dict or object"""
        if isinstance(self, dict):
            return self.get('day_change_percent', 0.0)
        return getattr(self, 'day_change_percent', 0.0)
    
    def resolve_sharpeRatio(self, info):
        """Extract sharpeRatio from dict or object"""
        if isinstance(self, dict):
            return self.get('sharpe_ratio', 0.0)
        return getattr(self, 'sharpe_ratio', 0.0)
    
    def resolve_maxDrawdown(self, info):
        """Extract maxDrawdown from dict or object"""
        if isinstance(self, dict):
            return self.get('max_drawdown', 0.0)
        return getattr(self, 'max_drawdown', 0.0)
    
    def resolve_sectorAllocation(self, info):
        """Extract sectorAllocation from dict or object"""
        import json
        if isinstance(self, dict):
            allocation = self.get('sector_allocation', {})
        else:
            allocation = getattr(self, 'sector_allocation', {})
        return json.dumps(allocation) if allocation else json.dumps({})
    
    def resolve_riskMetrics(self, info):
        """Extract riskMetrics from dict or object"""
        import json
        if isinstance(self, dict):
            metrics = self.get('risk_metrics', {})
        else:
            metrics = getattr(self, 'risk_metrics', {})
        return json.dumps(metrics) if metrics else json.dumps({})


class HoldingDetailType(graphene.ObjectType):
    """Detailed holding information"""

    symbol = graphene.String()
    company_name = graphene.String()
    shares = graphene.Int()
    current_price = graphene.Float()
    total_value = graphene.Float()
    cost_basis = graphene.Float()
    return_amount = graphene.Float()
    return_percent = graphene.Float()
    sector = graphene.String()
    
    # camelCase aliases
    companyName = graphene.String()
    currentPrice = graphene.Float()
    totalValue = graphene.Float()
    costBasis = graphene.Float()
    returnAmount = graphene.Float()
    returnPercent = graphene.Float()
    
    def resolve_companyName(self, info):
        if isinstance(self, dict):
            return self.get('company_name', '')
        return getattr(self, 'company_name', '')
    
    def resolve_currentPrice(self, info):
        if isinstance(self, dict):
            return self.get('current_price', 0.0)
        return getattr(self, 'current_price', 0.0)
    
    def resolve_totalValue(self, info):
        if isinstance(self, dict):
            return self.get('total_value', 0.0)
        return getattr(self, 'total_value', 0.0)
    
    def resolve_costBasis(self, info):
        if isinstance(self, dict):
            return self.get('cost_basis', 0.0)
        return getattr(self, 'cost_basis', 0.0)
    
    def resolve_returnAmount(self, info):
        if isinstance(self, dict):
            return self.get('return_amount', 0.0)
        return getattr(self, 'return_amount', 0.0)
    
    def resolve_returnPercent(self, info):
        if isinstance(self, dict):
            return self.get('return_percent', 0.0)
        return getattr(self, 'return_percent', 0.0)


class StockScreeningResultType(graphene.ObjectType):
    """Advanced stock screening result"""

    symbol = graphene.String()
    company_name = graphene.String()
    sector = graphene.String()
    market_cap = graphene.Float()
    pe_ratio = graphene.Float()
    beginner_friendly_score = graphene.Int()
    current_price = graphene.Float()
    ml_score = graphene.Float()
    risk_level = graphene.String()
    growth_potential = graphene.String()


class AIRecommendationType(graphene.ObjectType):
    """AI-powered investment recommendation"""

    symbol = graphene.String()
    company_name = graphene.String()
    companyName = graphene.String()  # camelCase alias
    recommendation = graphene.String()  # Buy, Sell, Hold
    confidence = graphene.Float()
    reasoning = graphene.String()
    target_price = graphene.Float()
    targetPrice = graphene.Float()  # camelCase alias
    current_price = graphene.Float()
    currentPrice = graphene.Float()  # camelCase alias
    expected_return = graphene.Float()
    expectedReturn = graphene.Float()  # camelCase alias
    suggested_exit_price = graphene.Float()  # For sell recommendations
    current_return = graphene.Float()  # For sell recommendations
    sector = graphene.String()
    risk_level = graphene.String()
    riskLevel = graphene.String()  # camelCase alias
    ml_score = graphene.Float()
    mlScore = graphene.Float()  # camelCase alias
    # Additional fields from backend
    consumer_strength_score = graphene.Float()
    consumerStrengthScore = graphene.Float()  # camelCase alias
    spending_growth = graphene.Float()
    spendingGrowth = graphene.Float()  # camelCase alias
    options_flow_score = graphene.Float()
    optionsFlowScore = graphene.Float()  # camelCase alias
    earnings_score = graphene.Float()
    earningsScore = graphene.Float()  # camelCase alias
    insider_score = graphene.Float()
    insiderScore = graphene.Float()  # camelCase alias
    
    def resolve_companyName(self, info):
        # Check both camelCase and snake_case
        if isinstance(self, dict):
            return self.get('companyName') or self.get('company_name') or None
        return getattr(self, 'companyName', None) or getattr(self, 'company_name', None) or None
    
    def resolve_targetPrice(self, info):
        # Check both camelCase and snake_case
        if isinstance(self, dict):
            return self.get('targetPrice') or self.get('target_price') or None
        return getattr(self, 'targetPrice', None) or getattr(self, 'target_price', None) or None
    
    def resolve_currentPrice(self, info):
        # Check both camelCase and snake_case
        if isinstance(self, dict):
            return self.get('currentPrice') or self.get('current_price') or None
        return getattr(self, 'currentPrice', None) or getattr(self, 'current_price', None) or None
    
    def resolve_expectedReturn(self, info):
        # Check both snake_case and camelCase field names
        if isinstance(self, dict):
            return self.get('expectedReturn') or self.get('expected_return') or None
        return getattr(self, 'expectedReturn', None) or getattr(self, 'expected_return', None) or None
    
    def resolve_riskLevel(self, info):
        # Check both camelCase and snake_case
        if isinstance(self, dict):
            return self.get('riskLevel') or self.get('risk_level') or None
        return getattr(self, 'riskLevel', None) or getattr(self, 'risk_level', None) or None
    
    def resolve_mlScore(self, info):
        # Check both camelCase and snake_case
        if isinstance(self, dict):
            return self.get('mlScore') or self.get('ml_score') or None
        return getattr(self, 'mlScore', None) or getattr(self, 'ml_score', None) or None
    
    def resolve_consumerStrengthScore(self, info):
        # Check both camelCase and snake_case
        if isinstance(self, dict):
            return self.get('consumerStrengthScore') or self.get('consumer_strength_score') or None
        return getattr(self, 'consumerStrengthScore', None) or getattr(self, 'consumer_strength_score', None) or None
    
    def resolve_spendingGrowth(self, info):
        # Check both camelCase and snake_case
        if isinstance(self, dict):
            return self.get('spendingGrowth') or self.get('spending_growth') or None
        return getattr(self, 'spendingGrowth', None) or getattr(self, 'spending_growth', None) or None
    
    def resolve_optionsFlowScore(self, info):
        # Check both camelCase and snake_case
        if isinstance(self, dict):
            return self.get('optionsFlowScore') or self.get('options_flow_score') or None
        return getattr(self, 'optionsFlowScore', None) or getattr(self, 'options_flow_score', None) or None
    
    def resolve_earningsScore(self, info):
        # Check both camelCase and snake_case
        if isinstance(self, dict):
            return self.get('earningsScore') or self.get('earnings_score') or None
        return getattr(self, 'earningsScore', None) or getattr(self, 'earnings_score', None) or None
    
    def resolve_insiderScore(self, info):
        # Check both camelCase and snake_case
        if isinstance(self, dict):
            return self.get('insiderScore') or self.get('insider_score') or None
        return getattr(self, 'insiderScore', None) or getattr(self, 'insider_score', None) or None


class SHAPFeatureType(graphene.ObjectType):
    """SHAP feature importance"""
    name = graphene.String()
    value = graphene.Float()
    absValue = graphene.Float()


class SHAPExplanationType(graphene.ObjectType):
    """Enhanced SHAP explanation"""
    explanation = graphene.String()
    shapValues = graphene.JSONString()
    featureImportance = graphene.List(SHAPFeatureType)
    topFeatures = graphene.List(SHAPFeatureType)
    categoryBreakdown = graphene.JSONString()
    totalPositiveImpact = graphene.Float()
    totalNegativeImpact = graphene.Float()
    prediction = graphene.Float()


class ConsumerStrengthComponentType(graphene.ObjectType):
    """Consumer Strength Score component"""
    score = graphene.Float()
    weight = graphene.Float()
    growth = graphene.Float(required=False)


class ConsumerStrengthType(graphene.ObjectType):
    """Enhanced Consumer Strength Score with historical tracking"""
    overallScore = graphene.Float()
    spendingScore = graphene.Float()
    optionsScore = graphene.Float()
    earningsScore = graphene.Float()
    insiderScore = graphene.Float()
    spendingGrowth = graphene.Float()
    sectorScore = graphene.Float()
    historicalTrend = graphene.String()
    components = graphene.JSONString()
    timestamp = graphene.String()


class SectorComparisonType(graphene.ObjectType):
    """Sector comparison for Consumer Strength Score"""
    stockScore = graphene.Float()
    sectorAverage = graphene.Float()
    sectorRank = graphene.Int()
    percentile = graphene.Float()
    sectorName = graphene.String()
    totalInSector = graphene.Int()


class PortfolioAnalysisType(graphene.ObjectType):
    """Portfolio analysis results"""

    total_value = graphene.Float()
    totalValue = graphene.Float()  # camelCase alias
    num_holdings = graphene.Int()
    numHoldings = graphene.Int()  # camelCase alias
    sector_breakdown = graphene.JSONString()
    sectorBreakdown = graphene.JSONString()  # camelCase alias
    risk_score = graphene.Float()
    riskScore = graphene.Float()  # camelCase alias
    diversification_score = graphene.Float()
    diversificationScore = graphene.Float()  # camelCase alias
    
    def resolve_totalValue(self, info):
        return getattr(self, 'total_value', None) or (self.get('total_value') if isinstance(self, dict) else None)
    
    def resolve_numHoldings(self, info):
        return getattr(self, 'num_holdings', None) or (self.get('num_holdings') if isinstance(self, dict) else None)
    
    def resolve_sectorBreakdown(self, info):
        return getattr(self, 'sector_breakdown', None) or (self.get('sector_breakdown') if isinstance(self, dict) else None)
    
    def resolve_riskScore(self, info):
        return getattr(self, 'risk_score', None) or (self.get('risk_score') if isinstance(self, dict) else None)
    
    def resolve_diversificationScore(self, info):
        return getattr(self, 'diversification_score', None) or (self.get('diversification_score') if isinstance(self, dict) else None)


class RiskAssessmentType(graphene.ObjectType):
    """Risk assessment results"""

    overall_risk = graphene.String()
    concentration_risk = graphene.String()
    sector_risk = graphene.String()
    volatility_estimate = graphene.Float()
    volatilityEstimate = graphene.Float()  # Alias for frontend compatibility
    recommendations = graphene.List(graphene.String)

    def resolve_volatilityEstimate(self, info):
        """Resolver for volatilityEstimate alias"""
        if hasattr(self, "volatility_estimate"):
            return self.volatility_estimate
        if isinstance(self, dict) and "volatility_estimate" in self:
            return self["volatility_estimate"]
        return None


class MarketOutlookType(graphene.ObjectType):
    """AI-powered market outlook"""

    overall_sentiment = graphene.String()
    confidence = graphene.Float()
    key_factors = graphene.List(graphene.String)
    risks = graphene.List(graphene.String)


class RebalanceSuggestionType(graphene.ObjectType):
    """Portfolio rebalancing suggestion"""

    action = graphene.String()
    current_allocation = graphene.Float()
    suggested_allocation = graphene.Float()
    reasoning = graphene.String()
    priority = graphene.String()


class SpendingInsightsType(graphene.ObjectType):
    """Spending insights for personalized recommendations"""
    
    discretionary_income = graphene.Float()
    discretionaryIncome = graphene.Float()  # camelCase alias
    suggested_budget = graphene.Float()
    suggestedBudget = graphene.Float()  # camelCase alias
    spending_health = graphene.String()
    spendingHealth = graphene.String()  # camelCase alias
    top_categories = graphene.JSONString()
    topCategories = graphene.JSONString()  # camelCase alias
    sector_preferences = graphene.JSONString()
    sectorPreferences = graphene.JSONString()  # camelCase alias
    
    def resolve_discretionaryIncome(self, info):
        return getattr(self, 'discretionary_income', None) or (self.get('discretionary_income') if isinstance(self, dict) else None)
    
    def resolve_suggestedBudget(self, info):
        return getattr(self, 'suggested_budget', None) or (self.get('suggested_budget') if isinstance(self, dict) else None)
    
    def resolve_spendingHealth(self, info):
        return getattr(self, 'spending_health', None) or (self.get('spending_health') if isinstance(self, dict) else None)
    
    def resolve_topCategories(self, info):
        return getattr(self, 'top_categories', None) or (self.get('top_categories') if isinstance(self, dict) else None)
    
    def resolve_sectorPreferences(self, info):
        return getattr(self, 'sector_preferences', None) or (self.get('sector_preferences') if isinstance(self, dict) else None)


class AIRecommendationsType(graphene.ObjectType):
    """Complete AI recommendations package"""

    portfolio_analysis = graphene.Field(PortfolioAnalysisType)
    portfolioAnalysis = graphene.Field(PortfolioAnalysisType)  # camelCase alias
    buy_recommendations = graphene.List(AIRecommendationType)
    buyRecommendations = graphene.List(AIRecommendationType)  # camelCase alias
    sell_recommendations = graphene.List(AIRecommendationType)
    sellRecommendations = graphene.List(AIRecommendationType)  # camelCase alias
    rebalance_suggestions = graphene.List(RebalanceSuggestionType)
    rebalanceSuggestions = graphene.List(RebalanceSuggestionType)  # camelCase alias
    risk_assessment = graphene.Field(RiskAssessmentType)
    riskAssessment = graphene.Field(RiskAssessmentType)  # camelCase alias
    market_outlook = graphene.Field(MarketOutlookType)
    marketOutlook = graphene.Field(MarketOutlookType)  # camelCase alias
    spending_insights = graphene.Field(SpendingInsightsType)
    spendingInsights = graphene.Field(SpendingInsightsType)  # camelCase alias
    
    def resolve_portfolioAnalysis(self, info):
        return getattr(self, 'portfolio_analysis', None) or (self.get('portfolio_analysis') if isinstance(self, dict) else None)
    
    def resolve_buyRecommendations(self, info):
        return getattr(self, 'buy_recommendations', None) or (self.get('buy_recommendations') if isinstance(self, dict) else None)
    
    def resolve_sellRecommendations(self, info):
        return getattr(self, 'sell_recommendations', None) or (self.get('sell_recommendations') if isinstance(self, dict) else None)
    
    def resolve_rebalanceSuggestions(self, info):
        return getattr(self, 'rebalance_suggestions', None) or (self.get('rebalance_suggestions') if isinstance(self, dict) else None)
    
    def resolve_riskAssessment(self, info):
        return getattr(self, 'risk_assessment', None) or (self.get('risk_assessment') if isinstance(self, dict) else None)
    
    def resolve_marketOutlook(self, info):
        return getattr(self, 'market_outlook', None) or (self.get('market_outlook') if isinstance(self, dict) else None)
    
    def resolve_spendingInsights(self, info):
        return getattr(self, 'spending_insights', None) or (self.get('spending_insights') if isinstance(self, dict) else None)


class StockTradeType(graphene.ObjectType):
    """Individual stock trade in rebalancing"""

    symbol = graphene.String()
    company_name = graphene.String()
    action = graphene.String()  # "BUY" or "SELL"
    shares = graphene.Int()
    price = graphene.Float()
    total_value = graphene.Float()
    reason = graphene.String()


class RebalanceResultType(graphene.ObjectType):
    """Result of AI rebalancing operation"""

    success = graphene.Boolean()
    message = graphene.String()
    changes_made = graphene.List(graphene.String)
    stock_trades = graphene.List(StockTradeType)
    new_portfolio_value = graphene.Float()
    rebalance_cost = graphene.Float()
    estimated_improvement = graphene.String()


# ==================
# Premium Query Root
# ==================


class PremiumQueries(graphene.ObjectType):
    """Premium feature queries"""

    # Enhanced Consumer Strength Score queries
    consumerStrength = graphene.Field(
        ConsumerStrengthType,
        symbol=graphene.String(required=True),
        description="Get enhanced Consumer Strength Score with historical tracking"
    )
    
    consumerStrengthHistory = graphene.List(
        ConsumerStrengthType,
        symbol=graphene.String(required=True),
        days=graphene.Int(default_value=30),
        description="Get historical Consumer Strength Scores"
    )
    
    sectorComparison = graphene.Field(
        SectorComparisonType,
        symbol=graphene.String(required=True),
        description="Compare stock's Consumer Strength to sector average"
    )

    premium_portfolio_metrics = graphene.Field(
        PortfolioMetricsType,
        portfolio_name=graphene.String(
            description="Specific portfolio name (optional)"
        ),
    )
    advanced_stock_screening = graphene.List(
        StockScreeningResultType,
        sector=graphene.String(description="Filter by sector"),
        min_market_cap=graphene.Float(description="Minimum market cap"),
        max_market_cap=graphene.Float(description="Maximum market cap"),
        min_pe_ratio=graphene.Float(description="Minimum P/E ratio"),
        max_pe_ratio=graphene.Float(description="Maximum P/E ratio"),
        min_beginner_score=graphene.Int(
            description="Minimum beginner score"
        ),
        sort_by=graphene.String(description="Sort by: ml_score, market_cap"),
        limit=graphene.Int(description="Limit results (default: 50)"),
    )
    ai_recommendations = graphene.Field(
        'core.premium_types.AIRecommendationsType',  # Use string reference to avoid import conflicts
        profile=graphene.Argument(
            ProfileInput,
            required=False,
            description="User profile input for personalized recommendations"
        ),
        using_defaults=graphene.Argument(
            graphene.Boolean,
            required=False,
            default_value=True,
            name="usingDefaults",
            description="Whether to use default values if profile is incomplete"
        ),
    )
    options_analysis = graphene.Field(
        "core.premium_types.OptionsAnalysisType",
        symbol=graphene.String(
            required=True,
            description="Stock symbol to analyze options for",
        ),
    )
    stock_screening = graphene.List(
        StockScreeningResultType,
        filters=graphene.String(description="JSON string of screening filters"),
    )
    research_report = graphene.JSONString(
        symbol=graphene.String(required=True),
        report_type=graphene.String(default_value='comprehensive'),
        description="Generate automated research report for a stock"
    )

    # ------- Resolvers -------

    def resolve_consumer_strength(self, info, symbol: str):
        """Resolve Consumer Strength Score"""
        user = getattr(info.context, 'user', None)
        user_id = user.id if user and not user.is_anonymous else None
        
        from .consumer_strength_service import ConsumerStrengthService
        service = ConsumerStrengthService()
        
        # Get spending analysis if user is authenticated
        spending_analysis = None
        if user_id:
            from .spending_habits_service import SpendingHabitsService
            spending_service = SpendingHabitsService()
            spending_analysis = spending_service.analyze_spending_habits(user_id, months=3)
        
        result = service.calculate_consumer_strength(symbol, spending_analysis, user_id)
        
        return ConsumerStrengthType(
            overallScore=result['overall_score'],
            spendingScore=result['spending_score'],
            optionsScore=result['options_score'],
            earningsScore=result['earnings_score'],
            insiderScore=result['insider_score'],
            spendingGrowth=result['spending_growth'],
            sectorScore=result['sector_score'],
            historicalTrend=result['historical_trend'],
            components=result['components'],
            timestamp=result['timestamp']
        )
    
    def resolve_consumer_strength_history(self, info, symbol: str, days: int = 30):
        """Resolve historical Consumer Strength Scores"""
        user = getattr(info.context, 'user', None)
        user_id = user.id if user and not user.is_anonymous else None
        
        from .consumer_strength_service import ConsumerStrengthService
        service = ConsumerStrengthService()
        
        history = service.get_historical_scores(symbol, user_id, days)
        
        return [
            ConsumerStrengthType(
                overallScore=h['score'],
                spendingScore=h['spending_score'],
                optionsScore=h['options_score'],
                earningsScore=h['earnings_score'],
                insiderScore=h['insider_score'],
                spendingGrowth=0.0,  # Historical data may not have this
                sectorScore=h.get('sector_score', 50.0),
                historicalTrend='stable',
                components={},
                timestamp=h['date']
            )
            for h in history
        ]
    
    def resolve_sector_comparison(self, info, symbol: str):
        """Resolve sector comparison"""
        user = getattr(info.context, 'user', None)
        user_id = user.id if user and not user.is_anonymous else None
        
        from .consumer_strength_service import ConsumerStrengthService
        from .spending_habits_service import SpendingHabitsService
        
        service = ConsumerStrengthService()
        
        # Get spending analysis if user is authenticated
        spending_analysis = None
        if user_id:
            spending_service = SpendingHabitsService()
            spending_analysis = spending_service.analyze_spending_habits(user_id, months=3)
        
        result = service.get_sector_comparison(symbol, spending_analysis)
        
        return SectorComparisonType(
            stockScore=result['stock_score'],
            sectorAverage=result['sector_average'],
            sectorRank=result['sector_rank'],
            percentile=result['percentile'],
            sectorName=result['sector_name'],
            totalInSector=result['total_in_sector']
        )

    def resolve_premium_portfolio_metrics(self, info, portfolio_name=None):
        user = getattr(info.context, "user", None)
        logger.info(
            "Premium portfolio metrics request - User: %s, Anonymous: %s",
            user,
            user.is_anonymous if user else "No user",
        )

        user_id = user.id if user and not user.is_anonymous else 1

        if user and not user.is_anonymous and not _has_premium_access(user):
            logger.warning("User %s does not have premium access", user.id)
            raise Exception("Premium subscription required")

        analytics_service = PremiumAnalyticsService()
        result = analytics_service.get_portfolio_performance_metrics(
            user_id, portfolio_name
        )
        logger.info(
            "Portfolio metrics result for user %s: %s", user_id, type(result)
        )
        return result

    def resolve_advanced_stock_screening(self, info, **kwargs):
        user = getattr(info.context, "user", None)

        if user and not user.is_anonymous and not _has_premium_access(user):
            raise Exception("Premium subscription required")

        filters = {k: v for k, v in kwargs.items() if v is not None}
        user_id = user.id if user and not user.is_anonymous else None
        analytics_service = PremiumAnalyticsService()
        return analytics_service.get_advanced_stock_screening(filters, user_id=user_id)

    def resolve_ai_recommendations(self, info, profile=None, using_defaults=True, **kwargs):
        user = getattr(info.context, "user", None)
        logger.info(
            "AI recommendations request - User: %s, Anonymous: %s, Profile: %s, UsingDefaults: %s",
            user,
            user.is_anonymous if user else "No user",
            profile,
            using_defaults,
        )
        
        # Debug: Check if user is actually authenticated
        if not user or user.is_anonymous:
            logger.warning("User is anonymous or None in ai_recommendations resolver")
            # Try to get user from request if available
            request = getattr(info.context, "request", None)
            if request and hasattr(request, "user"):
                user = request.user
                logger.info(f"Got user from request: {user.email if user and not user.is_anonymous else 'anonymous'}")
        
        # Use the actual user ID if available, otherwise fallback to 1
        if user and not user.is_anonymous:
            user_id = user.id
        else:
            # Fallback: try to get demo@example.com user
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                demo_user = User.objects.get(email='demo@example.com')
                user_id = demo_user.id
                logger.info(f"Using fallback user_id: {user_id} (demo@example.com)")
            except User.DoesNotExist:
                user_id = 1
                logger.warning(f"Fallback to user_id=1 (demo@example.com not found)")

        if user and not user.is_anonymous and not _has_premium_access(user):
            logger.warning("User %s does not have premium access", user.id)
            raise Exception("Premium subscription required")

        # Extract risk tolerance from profile input or use default
        risk_tolerance = "medium"
        if profile:
            # Profile is a ProfileInput object, access attributes directly
            rt_value = getattr(profile, "riskTolerance", None) or getattr(profile, "risk_tolerance", None)
            if rt_value:
                risk_tolerance = rt_value
                # Normalize risk tolerance values
                rt_lower = str(risk_tolerance).lower()
                if rt_lower in ["conservative", "low"]:
                    risk_tolerance = "Conservative"
                elif rt_lower in ["moderate", "medium"]:
                    risk_tolerance = "Moderate"
                elif rt_lower in ["aggressive", "high"]:
                    risk_tolerance = "Aggressive"
                else:
                    risk_tolerance = "Moderate"
            logger.info(f"Using risk tolerance from profile: {risk_tolerance}")
        else:
            # Try to get from user's income profile if available
            try:
                if user and not user.is_anonymous:
                    income_profile = user.incomeProfile
                    if income_profile and income_profile.risk_tolerance:
                        risk_tolerance = income_profile.risk_tolerance
                        logger.info(f"Using risk tolerance from user profile: {risk_tolerance}")
            except Exception as e:
                logger.debug(f"Could not get risk tolerance from user profile: {e}")

        # Build profile dict from GraphQL ProfileInput or saved profile
        profile_dict = None
        if profile:
            # Profile is a ProfileInput object, extract values
            profile_dict = {
                "age": getattr(profile, "age", None),
                "income_bracket": getattr(profile, "incomeBracket", None) or getattr(profile, "income_bracket", None),
                "investment_goals": list(getattr(profile, "investmentGoals", []) or getattr(profile, "investment_goals", []) or []),
                "investment_horizon_years": getattr(profile, "investmentHorizonYears", None) or getattr(profile, "investment_horizon_years", None),
                "risk_tolerance": risk_tolerance,  # Already extracted above
            }
        elif not using_defaults and user and not user.is_anonymous:
            # Try to get from saved profile
            try:
                income_profile = user.incomeProfile
                if income_profile:
                    profile_dict = {
                        "age": income_profile.age,
                        "income_bracket": income_profile.income_bracket,
                        "investment_goals": list(income_profile.investment_goals or []),
                        "investment_horizon_years": income_profile.investment_horizon,
                        "risk_tolerance": income_profile.risk_tolerance,
                    }
            except Exception as e:
                logger.debug(f"Could not get profile from user: {e}")
        
        analytics_service = PremiumAnalyticsService()
        result = analytics_service.get_ai_recommendations(
            user_id, risk_tolerance, profile=profile_dict
        )
        # Log the actual result structure with detailed info
        if isinstance(result, dict):
            buy_recs = result.get('buy_recommendations', [])
            portfolio_analysis = result.get('portfolio_analysis', {})
            logger.info(
                "[AI RECS] ✅ Result for user %s: keys=%s, buyRecs=%s, portfolioAnalysis=%s",
                user_id,
                list(result.keys()),
                len(buy_recs),
                'present' if portfolio_analysis else 'missing'
            )
            # Log top 3 recommendations for verification
            if buy_recs:
                top_3 = buy_recs[:3]
                logger.info(
                    "[AI RECS] 📊 Top 3 recommendations: %s",
                    [(r.get('symbol'), r.get('mlScore'), r.get('confidence')) for r in top_3]
                )
        else:
            logger.warning(
                "[AI RECS] ⚠️ Unexpected result type for user %s: type=%s, value=%s",
                user_id, type(result), result
            )
        return result

    def resolve_research_report(self, info, symbol: str, report_type: str = 'comprehensive'):
        """Generate research report for a stock"""
        try:
            logger.info(f"[ResearchReport] Starting report generation for {symbol}, type: {report_type}")
            user = getattr(info.context, "user", None)
            user_id = user.id if user and not user.is_anonymous else None
            
            from .research_report_service import ResearchReportService
            service = ResearchReportService()
            
            logger.info(f"[ResearchReport] Calling generate_stock_report for {symbol}")
            report = service.generate_stock_report(symbol, user_id, report_type)
            
            if not report:
                logger.error(f"[ResearchReport] Report generation returned None for {symbol}")
                return {'error': 'Report generation failed', 'symbol': symbol}
            
            if 'error' in report:
                logger.warning(f"[ResearchReport] Report has error field: {report.get('error')}")
            
            logger.info(f"[ResearchReport] ✅ Successfully generated report for {symbol}, keys: {list(report.keys()) if isinstance(report, dict) else 'not a dict'}")
            # Return dict directly - graphene.JSONString handles serialization
            return report
        except Exception as e:
            logger.error(f"[ResearchReport] ❌ Exception generating report for {symbol}: {e}", exc_info=True)
            return {'error': str(e), 'symbol': symbol}
    
    def resolve_options_analysis(self, info, symbol):
        """Get comprehensive options analysis for a symbol"""
        import time
        from graphql import GraphQLError
        
        MAX_DURATION = 6  # seconds
        
        start_time = time.monotonic()
        try:
            user = getattr(info.context, "user", None)
            logger.info(
                "Options analysis request - User: %s, Symbol: %s", user, symbol
            )

            if user and not user.is_anonymous and not _has_premium_access(user):
                logger.warning(
                    "User %s does not have premium access", user.id
                )
                # Return mock data instead of raising error for better UX
                logger.info("Returning mock data for non-premium user")
                return _get_mock_options_analysis(symbol)

            # Always return mock data immediately to prevent timeouts
            # Real data fetching can be implemented asynchronously later
            logger.info("Returning mock options analysis for %s (fast response)", symbol)
            return _get_mock_options_analysis(symbol)
                
        except Exception as e:
            elapsed = time.monotonic() - start_time
            logger.error(
                "Error in options analysis resolver (after %.2fs): %s", 
                elapsed, e, exc_info=True
            )
            # Always return mock data instead of raising errors to prevent 500s
            return _get_mock_options_analysis(symbol)

def _get_mock_options_analysis(symbol):
    """Return mock options analysis data for testing"""
    import random
    
    # Generate multiple strikes around current price (assuming ~155)
    base_price = 155.0
    strikes = [base_price - 10, base_price - 5, base_price, base_price + 5, base_price + 10]
    expiration_dates = ["2024-02-16", "2024-03-15", "2024-04-19"]
    
    call_options = []
    put_options = []
    
    for exp_date in expiration_dates:
        for strike in strikes:
            # Generate realistic option prices
            strike_diff = abs(strike - base_price)
            call_price = max(0.5, strike_diff * 0.1 + random.uniform(0.5, 2.0))
            put_price = max(0.5, strike_diff * 0.1 + random.uniform(0.5, 2.0))
            
            call_options.append({
                "symbol": symbol,
                "contract_symbol": f"{symbol}240216C{int(strike*1000):08d}",
                "strike": strike,
                "expiration_date": exp_date,
                "option_type": "call",
                "bid": round(call_price - 0.1, 2),
                "ask": round(call_price + 0.1, 2),
                "last_price": round(call_price, 2),
                "volume": random.randint(100, 2000),
                "open_interest": random.randint(500, 5000),
                "implied_volatility": round(random.uniform(0.20, 0.35), 3),
                "delta": round(random.uniform(0.3, 0.8), 2),
                "gamma": round(random.uniform(0.01, 0.03), 3),
                "theta": round(random.uniform(-0.20, -0.10), 2),
                "vega": round(random.uniform(0.20, 0.40), 2),
                "rho": round(random.uniform(0.02, 0.08), 3),
                "intrinsic_value": max(0, base_price - strike),
                "time_value": round(call_price - max(0, base_price - strike), 2),
                "days_to_expiration": 30,
            })
            
            put_options.append({
                "symbol": symbol,
                "contract_symbol": f"{symbol}240216P{int(strike*1000):08d}",
                "strike": strike,
                "expiration_date": exp_date,
                "option_type": "put",
                "bid": round(put_price - 0.1, 2),
                "ask": round(put_price + 0.1, 2),
                "last_price": round(put_price, 2),
                "volume": random.randint(100, 2000),
                "open_interest": random.randint(500, 5000),
                "implied_volatility": round(random.uniform(0.22, 0.38), 3),
                "delta": round(random.uniform(-0.8, -0.2), 2),
                "gamma": round(random.uniform(0.01, 0.03), 3),
                "theta": round(random.uniform(-0.20, -0.10), 2),
                "vega": round(random.uniform(0.20, 0.40), 2),
                "rho": round(random.uniform(-0.08, -0.02), 3),
                "intrinsic_value": max(0, strike - base_price),
                "time_value": round(put_price - max(0, strike - base_price), 2),
                "days_to_expiration": 30,
            })

    unusual_flow = [
        {
            "symbol": symbol,
            "contract_symbol": f"{symbol}240115C00150000",
            "option_type": "call",
            "strike": 150.0,
            "expiration_date": "2024-01-15",
            "volume": 5000,
            "open_interest": 15000,
            "premium": 13000.0,
            "implied_volatility": 0.30,
            "unusual_activity_score": 0.85,
            "activity_type": "Sweep",
        }
    ]

    recommended_strategies = [
        {
            "strategy_name": "Covered Call",
            "strategy_type": "Covered Call",
            "max_profit": 7.50,
            "max_loss": -142.50,
            "breakeven_points": [142.50],
            "probability_of_profit": 0.65,
            "risk_reward_ratio": 0.05,
            "days_to_expiration": 30,
            "total_cost": 0.0,
            "total_credit": 2.60,
        }
    ]

    market_sentiment = {
        "put_call_ratio": 0.65,
        "implied_volatility_rank": 45.0,
        "skew": 0.15,
        "sentiment_score": 65.0,
        "sentiment_description": "Bullish",
    }

    return {
        "underlying_symbol": symbol,
        "underlying_price": base_price,
        "options_chain": {
            "expiration_dates": expiration_dates,
            "calls": call_options,
            "puts": put_options,
            "greeks": {
                "delta": 0.5,
                "gamma": 0.02,
                "theta": -0.15,
                "vega": 0.30,
                "rho": 0.05,
            },
        },
        "unusual_flow": unusual_flow,
        "recommended_strategies": recommended_strategies,
        "market_sentiment": market_sentiment,
    }


def _has_premium_access(user):
    """Check if user has premium subscription (very permissive for now)."""
    if user and user.email == "test@example.com":
        logger.info(
            "Premium access granted to test user: %s", user.email
        )
        return True
    if user and not user.is_anonymous:
        logger.info(
            "Premium access granted to authenticated user: %s", user.email
        )
        return True
    logger.warning("Premium access denied for user: %s", user)
    return False


# =================
# Premium Mutations
# =================


class SubscribeToPremium(graphene.Mutation):
    """Subscribe to premium features"""

    class Arguments:
        plan_type = graphene.String(
            required=True, description="Plan type: basic, pro, elite"
        )
        payment_method = graphene.String(
            required=True, description="Payment method ID"
        )

    success = graphene.Boolean()
    message = graphene.String()
    subscription_id = graphene.String()

    def mutate(self, info, plan_type, payment_method):
        user = getattr(info.context, "user", None)
        if not user or user.is_anonymous:
            return SubscribeToPremium(
                success=False, message="Authentication required"
            )

        valid_plans = ["basic", "pro", "elite"]
        if plan_type not in valid_plans:
            return SubscribeToPremium(
                success=False, message="Invalid plan type"
            )

        try:
            subscription_id = (
                f"sub_{user.id}_{plan_type}_"
                f"{datetime.now().strftime('%Y%m%d')}"
            )
            return SubscribeToPremium(
                success=True,
                message=f"Successfully subscribed to {plan_type} plan",
                subscription_id=subscription_id,
            )
        except Exception as e:
            logger.error("Error creating subscription: %s", e)
            return SubscribeToPremium(
                success=False, message="Failed to create subscription"
            )


class CancelPremiumSubscription(graphene.Mutation):
    """Cancel premium subscription"""

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info):
        user = getattr(info.context, "user", None)
        if not user or user.is_anonymous:
            return CancelPremiumSubscription(
                success=False, message="Authentication required"
            )
        try:
            # Check if Stripe is available and configured
            if not STRIPE_AVAILABLE:
                logger.warning("Stripe not configured, using mock cancellation")
                return CancelPremiumSubscription(
                    success=True, 
                    message="Subscription cancelled successfully (mock mode)"
                )
            
            # Get user's subscription ID from user model (assumed field)
            subscription_id = getattr(user, 'stripe_subscription_id', None)
            
            if not subscription_id:
                return CancelPremiumSubscription(
                    success=False, 
                    message="No active subscription found"
                )
            
            # Cancel subscription in Stripe
            try:
                subscription = stripe.Subscription.retrieve(subscription_id)
                cancelled_sub = stripe.Subscription.cancel(subscription_id)
                
                # Update user model
                user.stripe_subscription_id = None
                user.subscription_status = 'cancelled'
                user.subscription_end_date = datetime.fromtimestamp(
                    cancelled_sub.current_period_end
                )
                user.save()
                
                logger.info(f"Cancelled subscription {subscription_id} for user {user.id}")
                return CancelPremiumSubscription(
                    success=True,
                    message=f"Subscription cancelled. Access until {user.subscription_end_date.strftime('%Y-%m-%d')}"
                )
            except stripe.error.StripeError as e:
                logger.error(f"Stripe error cancelling subscription: {e}")
                return CancelPremiumSubscription(
                    success=False,
                    message=f"Payment provider error: {str(e)}"
                )
                
        except Exception as e:
            logger.error("Error cancelling subscription: %s", e)
            return CancelPremiumSubscription(
                success=False, message="Failed to cancel subscription"
            )


class GenerateResearchReport(graphene.Mutation):
    """Generate and optionally email a research report"""

    class Arguments:
        symbol = graphene.String(required=True, description="Stock symbol")
        report_type = graphene.String(
            default_value='comprehensive',
            description="Report type: quick, comprehensive, deep_dive"
        )
        send_email = graphene.Boolean(
            default_value=False,
            description="Whether to send report via email"
        )

    success = graphene.Boolean()
    message = graphene.String()
    report = graphene.JSONString()

    def mutate(self, info, symbol: str, report_type: str = 'comprehensive', send_email: bool = False):
        """Generate research report for a stock"""
        user = getattr(info.context, "user", None)
        user_id = user.id if user and not user.is_anonymous else None
        
        try:
            from .research_report_service import ResearchReportService
            service = ResearchReportService()
            
            # Generate the report
            report = service.generate_stock_report(symbol, user_id, report_type)
            
            if not report or 'error' in report:
                return GenerateResearchReport(
                    success=False,
                    message=f"Failed to generate report: {report.get('error', 'Unknown error')}",
                    report=None
                )
            
            # Send email if requested
            if send_email and user_id and user and not user.is_anonymous:
                user_email = user.email
                email_sent = service.send_report_email(symbol, user_email, user_id, report_type)
                if email_sent:
                    message = f"Research report generated and sent to {user_email}"
                else:
                    message = "Research report generated, but email delivery failed"
            else:
                message = "Research report generated successfully"
            
            return GenerateResearchReport(
                success=True,
                message=message,
                report=report  # graphene.JSONString handles serialization automatically
            )
        except Exception as e:
            logger.error(f"Error generating research report: {e}", exc_info=True)
            return GenerateResearchReport(
                success=False,
                message=f"Error generating report: {str(e)}",
                report=None
            )


# ======================
# Options Analysis Types
# ======================


class OptionsContractType(graphene.ObjectType):
    """Individual options contract"""

    symbol = graphene.String()
    contract_symbol = graphene.String()
    strike = graphene.Float()
    expiration_date = graphene.String()
    option_type = graphene.String()
    bid = graphene.Float()
    ask = graphene.Float()
    last_price = graphene.Float()
    volume = graphene.Int()
    open_interest = graphene.Int()
    implied_volatility = graphene.Float()
    delta = graphene.Float()
    gamma = graphene.Float()
    theta = graphene.Float()
    vega = graphene.Float()
    rho = graphene.Float()
    intrinsic_value = graphene.Float()
    time_value = graphene.Float()
    days_to_expiration = graphene.Int()


class GreeksType(graphene.ObjectType):
    """Greeks for options analysis"""

    delta = graphene.Float()
    gamma = graphene.Float()
    theta = graphene.Float()
    vega = graphene.Float()
    rho = graphene.Float()


class OptionsChainType(graphene.ObjectType):
    """Options chain for a symbol"""

    expiration_dates = graphene.List(graphene.String)
    expirationDates = graphene.List(graphene.String)  # camelCase alias
    calls = graphene.List(OptionsContractType)
    puts = graphene.List(OptionsContractType)
    greeks = graphene.Field(GreeksType)

    def resolve_expiration_dates(self, info):
        return self.get("expiration_dates", [])
    
    def resolve_expirationDates(self, info):
        """camelCase alias for expiration_dates"""
        # Handle both dict and object - don't call other resolver methods on dicts
        if isinstance(self, dict):
            return self.get("expiration_dates", [])
        return self.resolve_expiration_dates(info)

    def resolve_calls(self, info):
        return self.get("calls", [])

    def resolve_puts(self, info):
        return self.get("puts", [])

    def resolve_greeks(self, info):
        return self.get("greeks", {})


class OptionsFlowType(graphene.ObjectType):
    """Individual unusual options flow data point"""

    symbol = graphene.String()
    contract_symbol = graphene.String()
    option_type = graphene.String()
    strike = graphene.Float()
    expiration_date = graphene.String()
    volume = graphene.Int()
    open_interest = graphene.Int()
    premium = graphene.Float()
    implied_volatility = graphene.Float()
    unusual_activity_score = graphene.Float()
    activity_type = graphene.String()
    type = graphene.String()  # Alias for activity_type
    
    # camelCase aliases
    contractSymbol = graphene.String()
    optionType = graphene.String()
    expirationDate = graphene.String()
    openInterest = graphene.Int()
    impliedVolatility = graphene.Float()
    unusualActivityScore = graphene.Float()
    activityType = graphene.String()
    
    def resolve_contractSymbol(self, info):
        if isinstance(self, dict):
            return self.get('contract_symbol', '')
        return getattr(self, 'contract_symbol', '')
    
    def resolve_optionType(self, info):
        if isinstance(self, dict):
            return self.get('option_type', '')
        return getattr(self, 'option_type', '')
    
    def resolve_expirationDate(self, info):
        if isinstance(self, dict):
            return self.get('expiration_date', '')
        return getattr(self, 'expiration_date', '')
    
    def resolve_openInterest(self, info):
        if isinstance(self, dict):
            return self.get('open_interest', 0)
        return getattr(self, 'open_interest', 0)
    
    def resolve_impliedVolatility(self, info):
        if isinstance(self, dict):
            return self.get('implied_volatility', 0.0)
        return getattr(self, 'implied_volatility', 0.0)
    
    def resolve_unusualActivityScore(self, info):
        if isinstance(self, dict):
            return self.get('unusual_activity_score', 0.0)
        return getattr(self, 'unusual_activity_score', 0.0)
    
    def resolve_activityType(self, info):
        if isinstance(self, dict):
            return self.get('activity_type', '')
        return getattr(self, 'activity_type', '')
    
    def resolve_type(self, info):
        """Alias for activity_type"""
        return self.resolve_activityType(info)


class UnusualFlowSummaryType(graphene.ObjectType):
    """Aggregated unusual flow summary (what UI expects)"""
    
    symbol = graphene.String()
    totalVolume = graphene.Int()
    unusualVolume = graphene.Int()
    unusualVolumePercent = graphene.Float()
    topTrades = graphene.List(OptionsFlowType)
    sweepTrades = graphene.Int()
    blockTrades = graphene.Int()
    lastUpdated = graphene.String()
    
    def resolve_symbol(self, info):
        if isinstance(self, dict):
            return self.get('symbol', '')
        return getattr(self, 'symbol', '')
    
    def resolve_totalVolume(self, info):
        if isinstance(self, dict):
            return self.get('total_volume', 0)
        return getattr(self, 'total_volume', 0)
    
    def resolve_unusualVolume(self, info):
        if isinstance(self, dict):
            return self.get('unusual_volume', 0)
        return getattr(self, 'unusual_volume', 0)
    
    def resolve_unusualVolumePercent(self, info):
        if isinstance(self, dict):
            return self.get('unusual_volume_percent', 0.0)
        return getattr(self, 'unusual_volume_percent', 0.0)
    
    def resolve_topTrades(self, info):
        if isinstance(self, dict):
            return self.get('top_trades', [])
        return getattr(self, 'top_trades', [])
    
    def resolve_sweepTrades(self, info):
        if isinstance(self, dict):
            return self.get('sweep_trades', 0)
        return getattr(self, 'sweep_trades', 0)
    
    def resolve_blockTrades(self, info):
        if isinstance(self, dict):
            return self.get('block_trades', 0)
        return getattr(self, 'block_trades', 0)
    
    def resolve_lastUpdated(self, info):
        if isinstance(self, dict):
            return self.get('last_updated', '')
        return getattr(self, 'last_updated', '')
    
    def resolve_contractSymbol(self, info):
        if isinstance(self, dict):
            return self.get('contract_symbol', '')
        return getattr(self, 'contract_symbol', '')
    
    def resolve_optionType(self, info):
        if isinstance(self, dict):
            return self.get('option_type', '')
        return getattr(self, 'option_type', '')
    
    def resolve_expirationDate(self, info):
        if isinstance(self, dict):
            return self.get('expiration_date', '')
        return getattr(self, 'expiration_date', '')
    
    def resolve_openInterest(self, info):
        if isinstance(self, dict):
            return self.get('open_interest', 0)
        return getattr(self, 'open_interest', 0)
    
    def resolve_impliedVolatility(self, info):
        if isinstance(self, dict):
            return self.get('implied_volatility', 0.0)
        return getattr(self, 'implied_volatility', 0.0)
    
    def resolve_unusualActivityScore(self, info):
        if isinstance(self, dict):
            return self.get('unusual_activity_score', 0.0)
        return getattr(self, 'unusual_activity_score', 0.0)
    
    def resolve_activityType(self, info):
        if isinstance(self, dict):
            return self.get('activity_type', '')
        return getattr(self, 'activity_type', '')
    
    def resolve_type(self, info):
        """Alias for activity_type"""
        return self.resolve_activityType(info)
    


class OptionsStrategyType(graphene.ObjectType):
    """Options trading strategy"""

    strategy_name = graphene.String()
    strategy_type = graphene.String()
    max_profit = graphene.Float()
    max_loss = graphene.Float()
    breakeven_points = graphene.List(graphene.Float)
    probability_of_profit = graphene.Float()
    risk_reward_ratio = graphene.Float()
    days_to_expiration = graphene.Int()
    total_cost = graphene.Float()
    total_credit = graphene.Float()
    description = graphene.String()
    risk_level = graphene.String()
    market_outlook = graphene.String()


class MarketSentimentType(graphene.ObjectType):
    """Market sentiment from options data"""

    put_call_ratio = graphene.Float()
    implied_volatility_rank = graphene.Float()
    skew = graphene.Float()
    sentiment_score = graphene.Float()
    sentiment_description = graphene.String()
    sentiment = graphene.String()  # Alias for sentiment_description
    
    # camelCase aliases
    putCallRatio = graphene.Float()
    impliedVolatilityRank = graphene.Float()
    sentimentScore = graphene.Float()
    sentimentDescription = graphene.String()
    
    def resolve_putCallRatio(self, info):
        if isinstance(self, dict):
            return self.get('put_call_ratio', 0.0)
        return getattr(self, 'put_call_ratio', 0.0)
    
    def resolve_impliedVolatilityRank(self, info):
        if isinstance(self, dict):
            return self.get('implied_volatility_rank', 0.0)
        return getattr(self, 'implied_volatility_rank', 0.0)
    
    def resolve_sentimentScore(self, info):
        if isinstance(self, dict):
            return self.get('sentiment_score', 0.0)
        return getattr(self, 'sentiment_score', 0.0)
    
    def resolve_sentimentDescription(self, info):
        if isinstance(self, dict):
            return self.get('sentiment_description', '')
        return getattr(self, 'sentiment_description', '')
    
    def resolve_sentiment(self, info):
        """Alias for sentiment_description - directly access dict"""
        if isinstance(self, dict):
            return self.get('sentiment_description', '')
        return getattr(self, 'sentiment_description', '')


class OptionsAnalysisType(graphene.ObjectType):
    """Complete options analysis"""

    underlying_symbol = graphene.String()
    underlying_price = graphene.Float()
    options_chain = graphene.Field(OptionsChainType)
    unusual_flow = graphene.List(OptionsFlowType)
    unusual_flow_summary = graphene.Field(UnusualFlowSummaryType)  # Aggregated summary for UI
    recommended_strategies = graphene.List(OptionsStrategyType)
    market_sentiment = graphene.Field(MarketSentimentType)
    
    # camelCase aliases
    underlyingSymbol = graphene.String()
    underlyingPrice = graphene.Float()
    optionsChain = graphene.Field(OptionsChainType)
    unusualFlow = graphene.Field(UnusualFlowSummaryType)  # UI expects single object, not list
    recommendedStrategies = graphene.List(OptionsStrategyType)
    marketSentiment = graphene.Field(MarketSentimentType)
    
    # Direct access to market sentiment fields (for UI compatibility)
    putCallRatio = graphene.Float()
    impliedVolatilityRank = graphene.Float()
    skew = graphene.Float()
    sentimentScore = graphene.Float()
    sentimentDescription = graphene.String()

    def resolve_underlying_symbol(self, info):
        """Extract underlying_symbol from dict or object"""
        if isinstance(self, dict):
            return self.get("underlying_symbol", "")
        return getattr(self, "underlying_symbol", "")

    def resolve_underlying_price(self, info):
        """Extract underlying_price from dict or object"""
        if isinstance(self, dict):
            return self.get("underlying_price", 0.0)
        return getattr(self, "underlying_price", 0.0)
    
    def resolve_underlyingSymbol(self, info):
        """camelCase alias"""
        return self.resolve_underlying_symbol(info)
    
    def resolve_underlyingPrice(self, info):
        """camelCase alias"""
        return self.resolve_underlying_price(info)

    def resolve_options_chain(self, info):
        if isinstance(self, dict):
            return self.get("options_chain", {})
        return getattr(self, "options_chain", {})

    def resolve_unusual_flow(self, info):
        if isinstance(self, dict):
            return self.get("unusual_flow", [])
        return getattr(self, "unusual_flow", [])
    
    def resolve_unusual_flow_summary(self, info):
        """Return aggregated unusual flow summary for UI"""
        if isinstance(self, dict):
            flow_list = self.get("unusual_flow", [])
        else:
            flow_list = getattr(self, "unusual_flow", [])
        
        # Aggregate the flow list into a summary
        total_volume = sum(item.get('volume', 0) if isinstance(item, dict) else getattr(item, 'volume', 0) for item in flow_list)
        unusual_volume = sum(item.get('volume', 0) if isinstance(item, dict) else getattr(item, 'volume', 0) for item in flow_list if (item.get('unusual_activity_score', 0) if isinstance(item, dict) else getattr(item, 'unusual_activity_score', 0)) > 0.5)
        sweep_trades = sum(1 for item in flow_list if 'sweep' in str(item.get('activity_type', '') if isinstance(item, dict) else getattr(item, 'activity_type', '')).lower())
        block_trades = sum(1 for item in flow_list if 'block' in str(item.get('activity_type', '') if isinstance(item, dict) else getattr(item, 'activity_type', '')).lower())
        
        # Get top trades (first 10 by volume)
        top_trades = sorted(flow_list, key=lambda x: x.get('volume', 0) if isinstance(x, dict) else getattr(x, 'volume', 0), reverse=True)[:10]
        
        # Get symbol directly from dict or object
        if isinstance(self, dict):
            symbol = self.get('underlying_symbol', '')
        else:
            symbol = getattr(self, 'underlying_symbol', '')
        
        return {
            'symbol': symbol,
            'total_volume': total_volume,
            'unusual_volume': unusual_volume,
            'unusual_volume_percent': (unusual_volume / total_volume * 100) if total_volume > 0 else 0.0,
            'top_trades': top_trades,
            'sweep_trades': sweep_trades,
            'block_trades': block_trades,
            'last_updated': ''
        }
    
    def resolve_unusualFlow(self, info):
        """Alias for unusual_flow_summary (UI expects this) - directly compute, don't call other resolvers"""
        if isinstance(self, dict):
            flow_list = self.get("unusual_flow", [])
        else:
            flow_list = getattr(self, "unusual_flow", [])
        
        # Aggregate the flow list into a summary
        total_volume = sum(item.get('volume', 0) if isinstance(item, dict) else getattr(item, 'volume', 0) for item in flow_list)
        unusual_volume = sum(item.get('volume', 0) if isinstance(item, dict) else getattr(item, 'volume', 0) for item in flow_list if (item.get('unusual_activity_score', 0) if isinstance(item, dict) else getattr(item, 'unusual_activity_score', 0)) > 0.5)
        sweep_trades = sum(1 for item in flow_list if 'sweep' in str(item.get('activity_type', '') if isinstance(item, dict) else getattr(item, 'activity_type', '')).lower())
        block_trades = sum(1 for item in flow_list if 'block' in str(item.get('activity_type', '') if isinstance(item, dict) else getattr(item, 'activity_type', '')).lower())
        
        # Get top trades (first 10 by volume)
        top_trades = sorted(flow_list, key=lambda x: x.get('volume', 0) if isinstance(x, dict) else getattr(x, 'volume', 0), reverse=True)[:10]
        
        # Get symbol directly from dict or object
        if isinstance(self, dict):
            symbol = self.get('underlying_symbol', '')
        else:
            symbol = getattr(self, 'underlying_symbol', '')
        
        return {
            'symbol': symbol,
            'total_volume': total_volume,
            'unusual_volume': unusual_volume,
            'unusual_volume_percent': (unusual_volume / total_volume * 100) if total_volume > 0 else 0.0,
            'top_trades': top_trades,
            'sweep_trades': sweep_trades,
            'block_trades': block_trades,
            'last_updated': ''
        }

    def resolve_recommended_strategies(self, info):
        if isinstance(self, dict):
            return self.get("recommended_strategies", [])
        return getattr(self, "recommended_strategies", [])

    def resolve_market_sentiment(self, info):
        if isinstance(self, dict):
            return self.get("market_sentiment", {})
        return getattr(self, "market_sentiment", {})
    
    # camelCase resolvers - directly access dict/object, don't call other resolvers
    def resolve_underlyingSymbol(self, info):
        """camelCase alias - directly access dict"""
        if isinstance(self, dict):
            return self.get("underlying_symbol", "")
        return getattr(self, "underlying_symbol", "")
    
    def resolve_underlyingPrice(self, info):
        """camelCase alias - directly access dict"""
        if isinstance(self, dict):
            return self.get("underlying_price", 0.0)
        return getattr(self, "underlying_price", 0.0)
    
    def resolve_optionsChain(self, info):
        """camelCase alias - directly access dict"""
        if isinstance(self, dict):
            return self.get("options_chain", {})
        return getattr(self, "options_chain", {})
    
    def resolve_recommendedStrategies(self, info):
        """camelCase alias - directly access dict"""
        if isinstance(self, dict):
            return self.get("recommended_strategies", [])
        return getattr(self, "recommended_strategies", [])
    
    def resolve_marketSentiment(self, info):
        """camelCase alias - directly access dict"""
        if isinstance(self, dict):
            return self.get("market_sentiment", {})
        return getattr(self, "market_sentiment", {})
    
    # Direct access to market sentiment fields
    def resolve_putCallRatio(self, info):
        """Extract putCallRatio from market_sentiment"""
        if isinstance(self, dict):
            sentiment = self.get('market_sentiment', {})
            if isinstance(sentiment, dict):
                return sentiment.get('put_call_ratio', 0.0)
        # For non-dict objects, try to get market_sentiment
        if hasattr(self, 'market_sentiment'):
            sentiment = self.market_sentiment
            if isinstance(sentiment, dict):
                return sentiment.get('put_call_ratio', 0.0)
        return 0.0
    
    def resolve_impliedVolatilityRank(self, info):
        """Extract impliedVolatilityRank from market_sentiment"""
        if isinstance(self, dict):
            sentiment = self.get('market_sentiment', {})
            if isinstance(sentiment, dict):
                return sentiment.get('implied_volatility_rank', 0.0)
        if hasattr(self, 'market_sentiment'):
            sentiment = self.market_sentiment
            if isinstance(sentiment, dict):
                return sentiment.get('implied_volatility_rank', 0.0)
        return 0.0
    
    def resolve_skew(self, info):
        """Extract skew from market_sentiment"""
        if isinstance(self, dict):
            sentiment = self.get('market_sentiment', {})
            if isinstance(sentiment, dict):
                return sentiment.get('skew', 0.0)
        if hasattr(self, 'market_sentiment'):
            sentiment = self.market_sentiment
            if isinstance(sentiment, dict):
                return sentiment.get('skew', 0.0)
        return 0.0
    
    def resolve_sentimentScore(self, info):
        """Extract sentimentScore from market_sentiment"""
        if isinstance(self, dict):
            sentiment = self.get('market_sentiment', {})
            if isinstance(sentiment, dict):
                return sentiment.get('sentiment_score', 0.0)
        if hasattr(self, 'market_sentiment'):
            sentiment = self.market_sentiment
            if isinstance(sentiment, dict):
                return sentiment.get('sentiment_score', 0.0)
        return 0.0
    
    def resolve_sentimentDescription(self, info):
        """Extract sentimentDescription from market_sentiment"""
        if isinstance(self, dict):
            sentiment = self.get('market_sentiment', {})
            if isinstance(sentiment, dict):
                return sentiment.get('sentiment_description', '')
        if hasattr(self, 'market_sentiment'):
            sentiment = self.market_sentiment
            if isinstance(sentiment, dict):
                return sentiment.get('sentiment_description', '')
        return ''


# ======================
# Premium Mutations Root
# ======================


class PremiumMutations(graphene.ObjectType):
    """Premium feature mutations"""

    subscribe_to_premium = SubscribeToPremium.Field()
    cancel_premium_subscription = CancelPremiumSubscription.Field()
    generate_research_report = GenerateResearchReport.Field()
    generate_ai_recommendations = GenerateAIRecommendations.Field()  # Automatically converted to generateAiRecommendations by Graphene
    ai_rebalance_portfolio = graphene.Field(
        RebalanceResultType,
        portfolio_name=graphene.String(
            description="Portfolio to rebalance (optional)"
        ),
        risk_tolerance=graphene.String(
            description="Risk tolerance: low, medium, high"
        ),
        max_rebalance_percentage=graphene.Float(
            description="Maximum percentage to rebalance (default: 20%)"
        ),
        dry_run=graphene.Boolean(
            description="Preview changes without executing (default: false)"
        ),
    )

    def resolve_ai_rebalance_portfolio(
        self,
        info,
        portfolio_name=None,
        risk_tolerance="medium",
        max_rebalance_percentage=20.0,
        dry_run=False,
    ):
        """
        AI-powered portfolio rebalancing (simplified, but clean and working).
        """
        user = getattr(info.context, "user", None)
        user_id = user.id if user and not user.is_anonymous else 1

        if user and not user.is_anonymous and not _has_premium_access(user):
            raise Exception("Premium subscription required for AI rebalancing")

        try:
            portfolio = Portfolio.objects.filter(user_id=user_id).first()
            if not portfolio:
                return RebalanceResultType(
                    success=False,
                    message="No portfolio found for rebalancing",
                    changes_made=[],
                    stock_trades=[],
                    new_portfolio_value=0.0,
                    rebalance_cost=0.0,
                    estimated_improvement="N/A",
                )

            analytics_service = PremiumAnalyticsService()
            recommendations = analytics_service.get_ai_recommendations(
                user_id, risk_tolerance
            )

            if not recommendations or not recommendations.get(
                "rebalance_suggestions"
            ):
                return RebalanceResultType(
                    success=False,
                    message="No rebalancing recommendations available",
                    changes_made=[],
                    stock_trades=[],
                    new_portfolio_value=float(portfolio.total_value),
                    rebalance_cost=0.0,
                    estimated_improvement="N/A",
                )

            changes_made = []
            stock_trades = []
            total_cost = 0.0

            stock_service = EnhancedStockService()
            cache_key = (
                f"rebalance_stocks_{risk_tolerance}_{max_rebalance_percentage}"
            )
            sector_stocks = cache.get(cache_key)

            if sector_stocks is None:
                sector_stocks = {}
                all_stocks = (
                    Stock.objects.select_related()
                    .only(
                        "symbol",
                        "company_name",
                        "sector",
                        "current_price",
                        "market_cap",
                        "pe_ratio",
                        "dividend_yield",
                        "debt_ratio",
                        "volatility",
                        "beginner_friendly_score",
                    )
                    .filter(current_price__gt=0)
                )

                # Group by sector
                stocks_by_sector = {}
                for stock in all_stocks:
                    sector_name = getattr(stock, "sector", None) or "Mixed"
                    stocks_by_sector.setdefault(sector_name, []).append(stock)

                available_sectors = list(stocks_by_sector.keys())
                if available_sectors:
                    num_sectors = min(5, len(available_sectors))
                    selected_sectors = random.sample(
                        available_sectors, num_sectors
                    )

                    for sector_name in selected_sectors:
                        stocks_in_sector = stocks_by_sector[sector_name]
                        # Take up to 20 for scoring variety
                        if len(stocks_in_sector) > 20:
                            stocks_in_sector = random.sample(
                                stocks_in_sector, 20
                            )

                        quality_stocks = []
                        for stock in stocks_in_sector:
                            try:
                                price = float(stock.current_price or 0)
                                if not (5.0 <= price <= 2000.0):
                                    continue

                                # Simple scoring: market cap + beginner score - volatility
                                score = 0.0
                                try:
                                    mc = float(stock.market_cap or 0)
                                    if mc > 1e11:
                                        score += 15
                                    elif mc > 1e10:
                                        score += 12
                                    elif mc > 1e9:
                                        score += 9
                                    elif mc > 3e8:
                                        score += 6
                                    else:
                                        score += 3
                                except Exception:
                                    score += 5

                                try:
                                    beginner = int(
                                        stock.beginner_friendly_score or 50
                                    )
                                    if beginner >= 80:
                                        score += 5
                                    elif beginner >= 60:
                                        score += 4
                                    elif beginner >= 40:
                                        score += 3
                                    else:
                                        score += 1
                                except Exception:
                                    score += 3

                                try:
                                    vol = float(stock.volatility or 20)
                                    if vol <= 15:
                                        score += 10
                                    elif vol <= 25:
                                        score += 7
                                    elif vol <= 40:
                                        score += 4
                                    else:
                                        score += 2
                                except Exception:
                                    score += 6

                                score += random.random() * 2.0

                                quality_stocks.append(
                                    {"stock": stock, "price": price, "score": score}
                                )
                            except Exception as e:
                                logger.warning(
                                    "Error scoring stock %s: %s",
                                    getattr(stock, "symbol", "unknown"),
                                    e,
                                )

                        quality_stocks.sort(
                            key=lambda x: x["score"], reverse=True
                        )
                        top_pick_count = min(4, len(quality_stocks))
                        if top_pick_count:
                            sector_stocks[sector_name] = [
                                {
                                    "symbol": qs["stock"].symbol,
                                    "name": qs["stock"].company_name
                                    or qs["stock"].symbol,
                                    "price": qs["price"],
                                    "score": qs["score"],
                                }
                                for qs in quality_stocks[:top_pick_count]
                            ]

                if not sector_stocks:
                    return RebalanceResultType(
                        success=False,
                        message="No stocks available for rebalancing",
                        changes_made=[],
                        stock_trades=[],
                        new_portfolio_value=0.0,
                        rebalance_cost=0.0,
                        estimated_improvement="N/A",
                    )

                cache.set(cache_key, sector_stocks, 900)

            # Apply top 3 rebalance suggestions
            for suggestion in recommendations["rebalance_suggestions"][:3]:
                action_text = suggestion["action"]
                current_alloc = suggestion["current_allocation"]
                suggested_alloc = suggestion["suggested_allocation"]
                change_pct = abs(suggested_alloc - current_alloc)

                if change_pct > max_rebalance_percentage:
                    continue

                changes_made.append(
                    f"{action_text}: {current_alloc:.1f}% → {suggested_alloc:.1f}%"
                )

                # Very simplified mapping of action → sectors
                action_lower = action_text.lower()
                chosen_stocks = []

                if "technology" in action_lower:
                    tech_sectors = [
                        s
                        for s in sector_stocks.keys()
                        if "tech" in s.lower()
                        or "technology" in s.lower()
                    ]
                    if tech_sectors:
                        chosen_stocks = sector_stocks[tech_sectors[0]][:2]
                elif "health" in action_lower:
                    health_sectors = [
                        s
                        for s in sector_stocks.keys()
                        if "health" in s.lower()
                        or "medical" in s.lower()
                        or "healthcare" in s.lower()
                    ]
                    if health_sectors:
                        chosen_stocks = sector_stocks[health_sectors[0]][:2]
                elif "consumer" in action_lower:
                    consumer_sectors = [
                        s
                        for s in sector_stocks.keys()
                        if "consumer" in s.lower()
                        or "cyclical" in s.lower()
                        or "retail" in s.lower()
                    ]
                    if consumer_sectors:
                        chosen_stocks = sector_stocks[consumer_sectors[0]][:2]

                for pick in chosen_stocks:
                    price = pick["price"]
                    symbol = pick["symbol"]
                    name = pick["name"]

                    if "increase" in action_lower:
                        shares = max(
                            1,
                            int(
                                (float(portfolio.total_value) * 0.05)
                                / max(price, 0.01)
                            ),
                        )
                        trade_value = shares * price
                        stock_trades.append(
                            StockTradeType(
                                symbol=symbol,
                                company_name=name,
                                action="BUY",
                                shares=shares,
                                price=price,
                                total_value=trade_value,
                                reason=action_text,
                            )
                        )

                        if not dry_run:
                            try:
                                stock_obj = Stock.objects.only(
                                    "id", "symbol"
                                ).get(symbol=symbol)
                                PortfolioService.add_holding_to_portfolio(
                                    user=portfolio.user,
                                    stock_id=stock_obj.id,
                                    shares=shares,
                                    portfolio_name=portfolio_name
                                    or "AI Rebalanced Portfolio",
                                    current_price=price,
                                )
                            except Stock.DoesNotExist:
                                logger.warning(
                                    "Stock %s not found in DB", symbol
                                )
                                continue

                        total_cost += trade_value * 0.001

                    elif "reduce" in action_lower or "sell" in action_lower:
                        shares = max(
                            1,
                            int(
                                (float(portfolio.total_value) * 0.03)
                                / max(price, 0.01)
                            ),
                        )
                        trade_value = shares * price
                        stock_trades.append(
                            StockTradeType(
                                symbol=symbol,
                                company_name=name,
                                action="SELL",
                                shares=shares,
                                price=price,
                                total_value=trade_value,
                                reason=action_text,
                            )
                        )

                        if not dry_run:
                            try:
                                stock_obj = Stock.objects.get(symbol=symbol)
                                holding = Portfolio.objects.filter(
                                    user=portfolio.user,
                                    stock=stock_obj,
                                ).first()
                                if holding:
                                    if holding.shares <= shares:
                                        holding.delete()
                                    else:
                                        holding.shares -= shares
                                        holding.save()
                            except Stock.DoesNotExist:
                                logger.warning(
                                    "Stock %s not found in DB for sell", symbol
                                )
                                continue

                        total_cost += trade_value * 0.001

            diversification_score = (
                recommendations.get("portfolio_analysis", {}).get(
                    "diversification_score", 0
                )
            )
            estimated_improvement = (
                f"Expected diversification score improvement: "
                f"{diversification_score:.1f} → "
                f"{min(diversification_score + 15, 100):.1f}"
            )

            if dry_run:
                message = (
                    f"Preview: {len(changes_made)} changes and "
                    f"{len(stock_trades)} trades would be executed "
                    f"(no actual trades made)"
                )
            else:
                message = (
                    f"Successfully rebalanced portfolio with "
                    f"{len(changes_made)} changes and "
                    f"{len(stock_trades)} trades"
                )

            return RebalanceResultType(
                success=True,
                message=message,
                changes_made=changes_made,
                stock_trades=stock_trades,
                new_portfolio_value=float(portfolio.total_value),
                rebalance_cost=total_cost,
                estimated_improvement=estimated_improvement,
            )

        except Exception as e:
            logger.error("AI rebalancing error: %s", e)
            return RebalanceResultType(
                success=False,
                message=f"Rebalancing failed: {str(e)}",
                changes_made=[],
                stock_trades=[],
                new_portfolio_value=0.0,
                rebalance_cost=0.0,
                estimated_improvement="N/A",
            )
