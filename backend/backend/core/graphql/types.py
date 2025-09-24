from graphene_django import DjangoObjectType
from graphene.types.generic import GenericScalar
import graphene
from django.utils import timezone

# Create a simple ObjectType instead of DjangoObjectType for User (database-free)
class UserType(graphene.ObjectType):
    id = graphene.ID()
    username = graphene.String()
    name = graphene.String()
    email = graphene.String()
    hasPremiumAccess = graphene.Boolean()
    subscriptionTier = graphene.String()

# Create a simple ObjectType instead of DjangoObjectType for Signal
class SignalType(graphene.ObjectType):
    id = graphene.ID()
    symbol = graphene.String()
    timeframe = graphene.String()
    triggered_at = graphene.DateTime()
    signal_type = graphene.String()
    entry_price = graphene.Float()
    stop_price = graphene.Float()
    target_price = graphene.Float()
    ml_score = graphene.Float()
    thesis = graphene.String()
    risk_reward_ratio = graphene.Float()
    is_active = graphene.Boolean()
    is_validated = graphene.Boolean()
    validation_price = graphene.Float()
    validation_timestamp = graphene.DateTime()
    created_by = graphene.Field(UserType)
    features = GenericScalar()  # JSONField
    
    # computed/exposed extras your query asks for
    days_since_triggered = graphene.Int()
    is_liked_by_user = graphene.Boolean()
    user_like_count = graphene.Int()

    # resolvers for computed fields
    def resolve_days_since_triggered(self, info):
        if not self.triggered_at:
            return None
        return (timezone.now() - self.triggered_at).days

    def resolve_is_liked_by_user(self, info):
        user = info.context.user
        if not user or user.is_anonymous:
            return False
        # Mock implementation - return False for now
        return False

    def resolve_user_like_count(self, info):
        # Mock implementation - return a random count
        return getattr(self, "user_like_count", 15)

# Mock Signal class for data
class MockSignal:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

# TraderScore type for leaderboard
class TraderScoreType(graphene.ObjectType):
    id = graphene.ID()
    overallScore = graphene.Float()
    accuracyScore = graphene.Float()
    consistencyScore = graphene.Float()
    disciplineScore = graphene.Float()
    totalSignals = graphene.Int()
    validatedSignals = graphene.Int()
    winRate = graphene.Float()
    avgReturn = graphene.Float()
    totalReturn = graphene.Float()
    sharpeRatio = graphene.Float()
    maxDrawdown = graphene.Float()
    lastUpdated = graphene.DateTime()

# LeaderboardEntry type
class LeaderboardEntryType(graphene.ObjectType):
    id = graphene.ID()
    username = graphene.String()
    name = graphene.String()
    rank = graphene.Int()
    category = graphene.String()
    totalSignals = graphene.Int()
    winRate = graphene.Float()
    avgReturn = graphene.Float()
    totalReturn = graphene.Float()
    user = graphene.Field(UserType)
    traderScore = graphene.Field(TraderScoreType)

# Mock TraderScore class
class MockTraderScore:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

# Mock LeaderboardEntry class
class MockLeaderboardEntry:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

# BacktestStrategy type
class BacktestStrategyType(graphene.ObjectType):
    id = graphene.ID()
    name = graphene.String()
    description = graphene.String()
    strategyType = graphene.String()
    parameters = GenericScalar()  # JSONField
    totalReturn = graphene.Float()
    winRate = graphene.Float()
    maxDrawdown = graphene.Float()
    sharpeRatio = graphene.Float()
    totalTrades = graphene.Int()
    isPublic = graphene.Boolean()
    isActive = graphene.Boolean()
    likesCount = graphene.Int()
    sharesCount = graphene.Int()
    createdAt = graphene.DateTime()
    updatedAt = graphene.DateTime()
    user = graphene.Field(UserType)

# Mock BacktestStrategy class
class MockBacktestStrategy:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

# BacktestResult type
class BacktestResultType(graphene.ObjectType):
    id = graphene.ID()
    strategyId = graphene.String()
    strategyName = graphene.String()
    symbol = graphene.String()
    timeframe = graphene.String()
    startDate = graphene.DateTime()
    endDate = graphene.DateTime()
    initialCapital = graphene.Float()
    finalCapital = graphene.Float()
    totalReturn = graphene.Float()
    totalReturnPercent = graphene.Float()
    annualizedReturn = graphene.Float()
    maxDrawdown = graphene.Float()
    sharpeRatio = graphene.Float()
    sortinoRatio = graphene.Float()
    calmarRatio = graphene.Float()
    winRate = graphene.Float()
    profitFactor = graphene.Float()
    totalTrades = graphene.Int()
    winningTrades = graphene.Int()
    losingTrades = graphene.Int()
    avgWin = graphene.Float()
    avgLoss = graphene.Float()
    createdAt = graphene.DateTime()

# Mock BacktestResult class
class MockBacktestResult:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

# StrategyParams input type  
class StrategyParamsType(graphene.InputObjectType):
    ema_fast = graphene.Int()
    ema_slow = graphene.Int()
    rsi_period = graphene.Int()
    rsiPeriod = graphene.Int()
    oversold_threshold = graphene.Float()
    oversoldThreshold = graphene.Float()
    overbought_threshold = graphene.Float()
    overboughtThreshold = graphene.Float()
    stop_loss = graphene.Float()
    stopLoss = graphene.Float()
    take_profit = graphene.Float()
    takeProfit = graphene.Float()
    volume_threshold = graphene.Float()
    volumeThreshold = graphene.Float()

# BacktestConfig input type
class BacktestConfigType(graphene.InputObjectType):
    strategyId = graphene.String()
    startDate = graphene.DateTime()
    endDate = graphene.DateTime()
    initialCapital = graphene.Float()
    commissionPerTrade = graphene.Float()
    slippagePct = graphene.Float()
    maxPositionSize = graphene.Float()
    riskPerTrade = graphene.Float()
    maxTradesPerDay = graphene.Int()
    maxOpenPositions = graphene.Int()
    parameters = graphene.Field(StrategyParamsType)

# BacktestResult output type (for mutations)
class BacktestResultOutputType(graphene.ObjectType):
    id = graphene.ID()
    strategyId = graphene.String()
    strategyName = graphene.String()
    startDate = graphene.DateTime()
    endDate = graphene.DateTime()
    totalReturn = graphene.Float()
    totalReturnPercent = graphene.Float()
    annualizedReturn = graphene.Float()
    maxDrawdown = graphene.Float()
    sharpeRatio = graphene.Float()
    sortinoRatio = graphene.Float()
    calmarRatio = graphene.Float()
    winRate = graphene.Float()
    profitFactor = graphene.Float()
    totalTrades = graphene.Int()
    winningTrades = graphene.Int()
    losingTrades = graphene.Int()
    avgWin = graphene.Float()
    avgLoss = graphene.Float()
    initialCapital = graphene.Float()
    finalCapital = graphene.Float()
    equityCurve = GenericScalar()  # JSON array
    dailyReturns = GenericScalar()  # JSON array
    createdAt = graphene.DateTime()

# RunBacktest result type
class RunBacktestResultType(graphene.ObjectType):
    success = graphene.Boolean()
    result = graphene.Field(BacktestResultOutputType)
    error = graphene.String()
    errors = graphene.List(graphene.String)

# Target Price Calculation result type
class TargetPriceResultType(graphene.ObjectType):
    targetPrice = graphene.Float()
    riskAmount = graphene.Float()
    rewardAmount = graphene.Float()
    rewardDistance = graphene.Float()
    riskRewardRatio = graphene.Float()
    method = graphene.String()
    rrTarget = graphene.Float()
    atrTarget = graphene.Float()
    srTarget = graphene.Float()

# Position Size Calculation result type
class PositionSizeResultType(graphene.ObjectType):
    positionSize = graphene.Float()
    shares = graphene.Int()
    dollarAmount = graphene.Float()
    riskAmount = graphene.Float()
    riskPercentage = graphene.Float()
    method = graphene.String()
    maxPositionSize = graphene.Float()
    recommendedSize = graphene.Float()
    
    # Additional fields expected by mobile app
    dollarRisk = graphene.Float()
    positionValue = graphene.Float()
    positionPct = graphene.Float()
    riskPerTradePct = graphene.Float()
    riskPerShare = graphene.Float()
    maxSharesFixedRisk = graphene.Int()
    maxSharesPosition = graphene.Int()

# Dynamic Stop Loss Calculation result type
class DynamicStopResultType(graphene.ObjectType):
    stopPrice = graphene.Float()
    stopDistance = graphene.Float()
    riskPercentage = graphene.Float()
    method = graphene.String()
    atrStop = graphene.Float()
    srStop = graphene.Float()
    pctStop = graphene.Float()

# Portfolio Holding type
class PortfolioHoldingType(graphene.ObjectType):
    # Use snake_case here; Graphene will expose camelCase in GraphQL
    symbol = graphene.String(required=True)
    company_name = graphene.String()
    shares = graphene.Int(required=True)
    current_price = graphene.Float(required=True)
    total_value = graphene.Float(required=True)
    cost_basis = graphene.Float(required=True)
    return_amount = graphene.Float(required=True)
    return_percent = graphene.Float(required=True)
    sector = graphene.String()

# Portfolio Metrics type
class PortfolioMetricsType(graphene.ObjectType):
    total_value = graphene.Float(required=True)
    total_cost = graphene.Float(required=True)
    total_return = graphene.Float(required=True)
    total_return_percent = graphene.Float(required=True)
    holdings = graphene.List(PortfolioHoldingType, required=True)

# Stock type for stock browsing
class StockType(graphene.ObjectType):
    id = graphene.ID(required=True)
    symbol = graphene.String(required=True)
    company_name = graphene.String()
    sector = graphene.String()
    current_price = graphene.Float()
    market_cap = graphene.Float()
    pe_ratio = graphene.Float()
    dividend_yield = graphene.Float()
    beginner_friendly_score = graphene.Float()
    dividend_score = graphene.Int()

# Advanced Stock Screening Result type
class AdvancedStockScreeningResultType(graphene.ObjectType):
    id = graphene.ID(required=True)
    symbol = graphene.String(required=True)
    company_name = graphene.String()
    sector = graphene.String()
    market_cap = graphene.Float()
    pe_ratio = graphene.Float()
    dividend_yield = graphene.Float()
    beginner_friendly_score = graphene.Float()
    dividend_score = graphene.Int()
    technical_score = graphene.Float()
    fundamental_score = graphene.Float()
    growth_score = graphene.Float()
    value_score = graphene.Float()
    current_price = graphene.Float()
    volatility = graphene.Float()
    debt_ratio = graphene.Float()
    reasoning = graphene.String()
    score = graphene.Float()
    ml_score = graphene.Float()

# Watchlist Stock type (nested in watchlist item)
class WatchlistStockType(graphene.ObjectType):
    id = graphene.ID(required=True)
    symbol = graphene.String(required=True)
    company_name = graphene.String()
    sector = graphene.String()
    current_price = graphene.Float()
    market_cap = graphene.Float()
    pe_ratio = graphene.Float()
    dividend_yield = graphene.Float()
    beginner_friendly_score = graphene.Float()
    dividend_score = graphene.Int()

# Watchlist Item type
class WatchlistItemType(graphene.ObjectType):
    id = graphene.ID(required=True)
    stock = graphene.Field(WatchlistStockType, required=True)
    added_at = graphene.DateTime()
    notes = graphene.String()
    target_price = graphene.Float()

# Technical Indicators type
class TechnicalIndicatorsType(graphene.ObjectType):
    rsi = graphene.Float()
    macd = graphene.Float()
    macd_signal = graphene.Float()
    macd_histogram = graphene.Float()
    sma20 = graphene.Float()
    sma50 = graphene.Float()
    ema12 = graphene.Float()
    ema26 = graphene.Float()
    bollinger_upper = graphene.Float()
    bollinger_lower = graphene.Float()
    bollinger_middle = graphene.Float()

# Fundamental Analysis type
class FundamentalAnalysisType(graphene.ObjectType):
    valuation_score = graphene.Float()
    growth_score = graphene.Float()
    stability_score = graphene.Float()
    dividend_score = graphene.Float()
    debt_score = graphene.Float()

# Rust Stock Analysis type
class RustStockAnalysisType(graphene.ObjectType):
    symbol = graphene.String(required=True)
    beginner_friendly_score = graphene.Float()
    risk_level = graphene.String()
    recommendation = graphene.String()
    technical_indicators = graphene.Field(TechnicalIndicatorsType)
    fundamental_analysis = graphene.Field(FundamentalAnalysisType)
    reasoning = graphene.String()

# Mock User class for data (database-free)
class MockUser:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
