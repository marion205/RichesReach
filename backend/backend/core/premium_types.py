import graphene
from .models import User
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Premium Analytics Types
class PortfolioMetricsType(graphene.ObjectType):
    """Advanced portfolio performance metrics"""
    total_value = graphene.Float()
    total_cost = graphene.Float()
    total_return = graphene.Float()
    total_return_percent = graphene.Float()
    volatility = graphene.Float()
    sharpe_ratio = graphene.Float()
    max_drawdown = graphene.Float()
    beta = graphene.Float()
    alpha = graphene.Float()
    holdings = graphene.List('core.premium_types.HoldingDetailType')
    sector_allocation = graphene.JSONString()
    risk_metrics = graphene.JSONString()

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

class StockScreeningResultType(graphene.ObjectType):
    """Advanced stock screening result"""
    symbol = graphene.String()
    company_name = graphene.String()
    sector = graphene.String()
    market_cap = graphene.Float()
    pe_ratio = graphene.Float()
    dividend_yield = graphene.Float()
    volatility = graphene.Float()
    score = graphene.Float()
    ml_score = graphene.Float()  # For mobile app compatibility
    reasoning = graphene.String()
    beginner_friendly_score = graphene.Int()
    current_price = graphene.Float()
    debt_ratio = graphene.Float()

class OptionsAnalysisType(graphene.ObjectType):
    """Comprehensive options analysis"""
    symbol = graphene.String()
    current_price = graphene.Float()
    implied_volatility = graphene.Float()
    options_chain = graphene.JSONString()
    greeks = graphene.JSONString()
    strategies = graphene.List('core.premium_types.OptionsStrategyType')
    risk_metrics = graphene.JSONString()

class OptionsStrategyType(graphene.ObjectType):
    """Options trading strategy"""
    name = graphene.String()
    description = graphene.String()
    risk_level = graphene.String()
    max_profit = graphene.Float()
    max_loss = graphene.Float()
    breakeven_points = graphene.List(graphene.Float)
    probability_of_profit = graphene.Float()

class AIRecommendationsType(graphene.ObjectType):
    """AI-powered investment recommendations"""
    recommendations = graphene.List('core.premium_types.AIRecommendationType')
    risk_profile = graphene.String()
    time_horizon = graphene.String()
    confidence_score = graphene.Float()

class AIRecommendationType(graphene.ObjectType):
    """Individual AI recommendation"""
    symbol = graphene.String()
    action = graphene.String()  # 'buy', 'sell', 'hold'
    confidence = graphene.Float()
    reasoning = graphene.String()
    target_price = graphene.Float()
    stop_loss = graphene.Float()
    time_horizon = graphene.String()

class PremiumQueries(graphene.ObjectType):
    """Premium feature queries"""
    pass

class PremiumMutations(graphene.ObjectType):
    """Premium feature mutations"""
    pass
