import graphene
import graphql_jwt
from graphene_django import DjangoObjectType
from django.contrib.auth import get_user_model
from core.graphql.queries import Query as SwingQuery, RunBacktestMutation, PortfolioMetricsType, PortfolioHoldingType, _mock_portfolio_metrics, StockType, AdvancedStockScreeningResultType, WatchlistItemType, WatchlistStockType, RustStockAnalysisType, TechnicalIndicatorsType, FundamentalAnalysisType, get_mock_stocks, get_mock_advanced_screening_results, get_mock_watchlist, get_mock_rust_stock_analysis, TargetPriceResultType, PositionSizeResultType, DynamicStopResultType
from core.graphql.types import DayTradingPicksType, DayTradingPickType, DayTradingFeaturesType, DayTradingRiskType
from core.types import StockDiscussionType, OptionOrderType, IncomeProfileType, AIRecommendationsType
from core.crypto_graphql import CryptoPriceType, CryptocurrencyType, CryptoMutation
from core.sbloc_queries import SblocQuery
from core.sbloc_mutations import SblocMutation
from core.notification_graphql import NotificationQuery, NotificationMutation
from core.benchmark_graphql import BenchmarkQuery

User = get_user_model()

# Helper function to add budget-aware scoring breakdown to StockType
def add_scoring_breakdown(stock_type, stock_data=None, user_budget=1000.0):
    """Add budget-aware scoring breakdown to a StockType object"""
    try:
        from .scoring.beginner_score import compute_beginner_score
        
        # Use provided data or extract from stock_type
        if stock_data:
            overview_data = stock_data
        else:
            overview_data = {
                'Name': getattr(stock_type, 'companyName', ''),
                'Symbol': getattr(stock_type, 'symbol', ''),
                'Sector': getattr(stock_type, 'sector', ''),
                'MarketCapitalization': str(getattr(stock_type, 'marketCap', 0)) if getattr(stock_type, 'marketCap', 0) else None,
                'PERatio': str(getattr(stock_type, 'peRatio', 0)) if getattr(stock_type, 'peRatio', 0) else None,
                'DividendYield': str(getattr(stock_type, 'dividendYield', 0)) if getattr(stock_type, 'dividendYield', 0) else None,
                'Beta': '1.0',
                'ProfitMargin': '0.15',
                'ReturnOnEquityTTM': '0.20',
                'DebtToEquity': '0.5'
            }
        
        market_data = {
            'price': getattr(stock_type, 'currentPrice', 100.0),
            'avgDollarVolume': 5e7,  # Default $50M/day
            'annualizedVol': 0.25,  # Default 25% volatility
            'beta': 1.0
        }
        
        score_result = compute_beginner_score(overview_data, market_data, user_budget)
        
        # Create breakdown object
        breakdown = BeginnerScoreBreakdownType()
        breakdown.score = score_result.score
        breakdown.factors = []
        for factor in score_result.factors:
            factor_obj = FactorType()
            factor_obj.name = factor.name
            factor_obj.weight = factor.weight
            factor_obj.value = factor.value
            factor_obj.contrib = factor.contrib
            factor_obj.detail = factor.detail
            breakdown.factors.append(factor_obj)
        breakdown.notes = score_result.notes
        stock_type.beginnerScoreBreakdown = breakdown
        
    except Exception as e:
        print(f"Scoring breakdown error for {getattr(stock_type, 'symbol', 'Unknown')}: {e}")
        stock_type.beginnerScoreBreakdown = None

# Mock types for missing functionality
# CryptoPriceType is defined in crypto_graphql.py

class ResearchHubType(graphene.ObjectType):
    symbol = graphene.String()
    news = graphene.List(graphene.String)
    analysis = graphene.String()

class StockChartDataType(graphene.ObjectType):
    symbol = graphene.String()
    data = graphene.List(graphene.Float)

class CryptoMLSignalType(graphene.ObjectType):
    symbol = graphene.String()
    signal = graphene.String()
    confidence = graphene.Float()

class CryptoRecommendationType(graphene.ObjectType):
    symbol = graphene.String()
    recommendation = graphene.String()
    price = graphene.Float()

class CreateIncomeProfileResult(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()

class AIRecommendationType(graphene.ObjectType):
    id = graphene.ID()
    riskProfile = graphene.String()
    portfolioAllocation = graphene.String()
    recommendedStocks = graphene.List(graphene.String)
    expectedPortfolioReturn = graphene.Float()
    riskAssessment = graphene.String()

class GenerateAIRecommendationsResult(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()
    recommendations = graphene.List(AIRecommendationType)

# ML System Types
class OutcomeTrackingType(graphene.ObjectType):
    total_outcomes = graphene.Int()
    recent_outcomes = graphene.Int()

class ModelsType(graphene.ObjectType):
    safe_model = graphene.String()
    aggressive_model = graphene.String()

class BanditStrategyType(graphene.ObjectType):
    win_rate = graphene.Float()
    confidence = graphene.Float()
    alpha = graphene.Float()
    beta = graphene.Float()

class BanditType(graphene.ObjectType):
    breakout = graphene.Field(BanditStrategyType)
    mean_reversion = graphene.Field(BanditStrategyType)
    momentum = graphene.Field(BanditStrategyType)
    etf_rotation = graphene.Field(BanditStrategyType)

class LastTrainingType(graphene.ObjectType):
    SAFE = graphene.String()
    AGGRESSIVE = graphene.String()

class MLSystemStatusType(graphene.ObjectType):
    outcome_tracking = graphene.Field(OutcomeTrackingType)
    models = graphene.Field(ModelsType)
    bandit = graphene.Field(BanditType)
    last_training = graphene.Field(LastTrainingType)
    ml_available = graphene.Boolean()

# Risk Management Types
class RiskLimitsType(graphene.ObjectType):
    max_position_size = graphene.Float()
    max_daily_loss = graphene.Float()
    max_concurrent_trades = graphene.Int()
    max_sector_exposure = graphene.Float()

class RiskSummaryType(graphene.ObjectType):
    account_value = graphene.Float()
    daily_pnl = graphene.Float()
    daily_pnl_pct = graphene.Float()
    daily_trades = graphene.Int()
    active_positions = graphene.Int()
    total_exposure = graphene.Float()
    exposure_pct = graphene.Float()
    sector_exposure = graphene.JSONString()
    risk_level = graphene.String()
    risk_limits = graphene.Field(RiskLimitsType)

class ActivePositionType(graphene.ObjectType):
    symbol = graphene.String()
    side = graphene.String()
    entry_price = graphene.Float()
    quantity = graphene.Int()
    entry_time = graphene.String()
    stop_loss_price = graphene.Float()
    take_profit_price = graphene.Float()
    max_hold_until = graphene.String()
    atr_stop_price = graphene.Float()
    current_pnl = graphene.Float()
    time_remaining_minutes = graphene.Int()

# Risk Management Mutation Types
class CreatePositionResultType(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()
    position = graphene.Field(ActivePositionType)

class ExitedPositionType(graphene.ObjectType):
    symbol = graphene.String()
    side = graphene.String()
    entry_price = graphene.Float()
    exit_price = graphene.Float()
    quantity = graphene.Int()
    pnl = graphene.Float()
    exit_reason = graphene.String()
    exit_time = graphene.String()

class CheckExitsResultType(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()
    exited_positions = graphene.List(ExitedPositionType)

class UpdateRiskSettingsResultType(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()
    current_settings = graphene.Field(RiskSummaryType)

# Social Feed Types
class SocialFeedUserType(graphene.ObjectType):
    id = graphene.ID()
    name = graphene.String()
    email = graphene.String()
    profilePic = graphene.String()
    experienceLevel = graphene.String()

class PortfolioType(graphene.ObjectType):
    id = graphene.ID()
    name = graphene.String()
    totalValue = graphene.Float()
    totalReturnPercent = graphene.Float()
    holdingsCount = graphene.Int()
    holdings = graphene.List(lambda: MyPortfolioHoldingType)

class FactorType(graphene.ObjectType):
    name = graphene.String()
    weight = graphene.Float()
    value = graphene.Float()
    contrib = graphene.Float()
    detail = graphene.String()

class BeginnerScoreBreakdownType(graphene.ObjectType):
    score = graphene.Int()
    factors = graphene.List(FactorType)
    notes = graphene.List(graphene.String)

# Bank Account Types
class BankAccountType(graphene.ObjectType):
    id = graphene.ID()
    bankName = graphene.String()
    accountType = graphene.String()
    lastFour = graphene.String()
    isVerified = graphene.Boolean()
    isPrimary = graphene.Boolean()
    linkedAt = graphene.String()

class FundingHistoryType(graphene.ObjectType):
    id = graphene.ID()
    amount = graphene.Float()
    status = graphene.String()
    bankAccountId = graphene.String()
    initiatedAt = graphene.String()
    completedAt = graphene.String()

class SblocOfferType(graphene.ObjectType):
    ltv = graphene.Float()
    apr = graphene.Float()
    minDraw = graphene.Float()
    maxDrawMultiplier = graphene.Float()
    disclosures = graphene.List(graphene.String)
    eligibleEquity = graphene.Float()
    updatedAt = graphene.String()

# Bank Account Mutation Result Types
class LinkBankAccountResultType(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()
    bankAccount = graphene.Field(BankAccountType)

class InitiateFundingResultType(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()
    funding = graphene.Field(FundingHistoryType)

class StockType(graphene.ObjectType):
    id = graphene.ID()
    symbol = graphene.String()
    companyName = graphene.String()
    currentPrice = graphene.Float()
    changePercent = graphene.Float()
    sector = graphene.String()
    marketCap = graphene.Float()
    peRatio = graphene.Float()
    dividendYield = graphene.Float()
    beginnerFriendlyScore = graphene.Int()
    beginnerScoreBreakdown = graphene.Field(BeginnerScoreBreakdownType)

class CommentType(graphene.ObjectType):
    id = graphene.ID()
    content = graphene.String()
    createdAt = graphene.DateTime()
    user = graphene.Field(SocialFeedUserType)

class SocialFeedItemType(graphene.ObjectType):
    id = graphene.ID()
    type = graphene.String()
    title = graphene.String()
    content = graphene.String()
    createdAt = graphene.DateTime()
    score = graphene.Float()
    commentCount = graphene.Int()
    user = graphene.Field(SocialFeedUserType)
    portfolio = graphene.Field(PortfolioType)
    stock = graphene.Field(StockType)
    likesCount = graphene.Int()
    commentsCount = graphene.Int()
    isLiked = graphene.Boolean()
    comments = graphene.List(CommentType)

class FeedItemType(graphene.ObjectType):
    id = graphene.ID()
    kind = graphene.String()
    title = graphene.String()
    content = graphene.String()
    tickers = graphene.List(graphene.String)
    score = graphene.Float()
    commentCount = graphene.Int()
    user = graphene.Field(SocialFeedUserType)
    createdAt = graphene.DateTime()

class QuoteType(graphene.ObjectType):
    symbol = graphene.String()
    last = graphene.Float()
    changePct = graphene.Float()
    # Additional fields for mobile app
    price = graphene.Float()
    chg = graphene.Float()
    chgPct = graphene.Float()
    high = graphene.Float()
    low = graphene.Float()
    volume = graphene.Float()
    currentPrice = graphene.Float()
    change = graphene.Float()

# Options Analysis Types
class OptionType(graphene.ObjectType):
    symbol = graphene.String()
    contractSymbol = graphene.String()
    strike = graphene.Float()
    expirationDate = graphene.String()
    optionType = graphene.String()
    bid = graphene.Float()
    ask = graphene.Float()
    lastPrice = graphene.Float()
    volume = graphene.Int()
    openInterest = graphene.Int()
    impliedVolatility = graphene.Float()
    delta = graphene.Float()
    gamma = graphene.Float()
    theta = graphene.Float()
    vega = graphene.Float()
    rho = graphene.Float()
    intrinsicValue = graphene.Float()
    timeValue = graphene.Float()
    daysToExpiration = graphene.Int()

class GreeksType(graphene.ObjectType):
    delta = graphene.Float()
    gamma = graphene.Float()
    theta = graphene.Float()
    vega = graphene.Float()
    rho = graphene.Float()

class TopTradeType(graphene.ObjectType):
    symbol = graphene.String()
    contractSymbol = graphene.String()
    optionType = graphene.String()
    strike = graphene.Float()
    expirationDate = graphene.String()
    volume = graphene.Int()
    openInterest = graphene.Int()
    premium = graphene.Float()
    impliedVolatility = graphene.Float()
    unusualActivityScore = graphene.Float()
    activityType = graphene.String()
    type = graphene.String()

class UnusualFlowType(graphene.ObjectType):
    symbol = graphene.String()
    totalVolume = graphene.Int()
    unusualVolume = graphene.Int()
    unusualVolumePercent = graphene.Float()
    topTrades = graphene.List(TopTradeType)
    sweepTrades = graphene.List(graphene.String)
    blockTrades = graphene.List(graphene.String)
    lastUpdated = graphene.String()

class RecommendedStrategyType(graphene.ObjectType):
    strategyName = graphene.String()
    strategyType = graphene.String()
    description = graphene.String()
    riskLevel = graphene.String()
    marketOutlook = graphene.String()
    maxProfit = graphene.Float()
    maxLoss = graphene.Float()
    breakevenPoints = graphene.List(graphene.Float)
    probabilityOfProfit = graphene.Float()
    riskRewardRatio = graphene.Float()
    daysToExpiration = graphene.Int()
    totalCost = graphene.Float()
    totalCredit = graphene.Float()

class MarketSentimentType(graphene.ObjectType):
    sentiment = graphene.String()
    sentimentDescription = graphene.String()

class OptionsChainType(graphene.ObjectType):
    expirationDates = graphene.List(graphene.String)
    calls = graphene.List(OptionType)
    puts = graphene.List(OptionType)
    greeks = graphene.Field(GreeksType)

class OptionsAnalysisType(graphene.ObjectType):
    underlyingSymbol = graphene.String()
    underlyingPrice = graphene.Float()
    optionsChain = graphene.Field(OptionsChainType)
    unusualFlow = graphene.Field(UnusualFlowType)
    recommendedStrategies = graphene.List(RecommendedStrategyType)
    marketSentiment = graphene.Field(MarketSentimentType)
    putCallRatio = graphene.Float()
    impliedVolatilityRank = graphene.Float()
    skew = graphene.Float()
    sentimentScore = graphene.Float()
    sentimentDescription = graphene.String()

# PortfolioHoldingType for mobile app compatibility (myPortfolios)
class MyPortfolioHoldingType(graphene.ObjectType):
    id = graphene.ID()
    stock = graphene.Field(lambda: StockType)
    shares = graphene.Int()
    averagePrice = graphene.Float()
    currentPrice = graphene.Float()
    totalValue = graphene.Float()
    notes = graphene.String()
    createdAt = graphene.DateTime()
    updatedAt = graphene.DateTime()

# PortfolioType already defined above

class MyPortfoliosType(graphene.ObjectType):
    totalPortfolios = graphene.Int()
    totalValue = graphene.Float()
    portfolios = graphene.List(PortfolioType)

class TradingAccountType(graphene.ObjectType):
    id = graphene.ID()
    buyingPower = graphene.Float()
    cash = graphene.Float()
    portfolioValue = graphene.Float()
    equity = graphene.Float()
    dayTradeCount = graphene.Int()
    patternDayTrader = graphene.Boolean()
    tradingBlocked = graphene.Boolean()
    dayTradingBuyingPower = graphene.Float()
    isDayTradingEnabled = graphene.Boolean()
    accountStatus = graphene.String()
    createdAt = graphene.DateTime()

class TradingPositionType(graphene.ObjectType):
    id = graphene.ID()
    symbol = graphene.String()
    quantity = graphene.Float()
    marketValue = graphene.Float()
    costBasis = graphene.Float()
    unrealizedPl = graphene.Float()
    unrealizedpi = graphene.Float()
    unrealizedPI = graphene.Float()
    unrealizedPLPercent = graphene.Float()
    unrealizedPlpc = graphene.Float()
    currentPrice = graphene.Float()
    side = graphene.String()

class TradingOrderType(graphene.ObjectType):
    id = graphene.ID()
    symbol = graphene.String()
    side = graphene.String()
    orderType = graphene.String()
    quantity = graphene.Float()
    price = graphene.Float()
    stopPrice = graphene.Float()
    status = graphene.String()
    createdAt = graphene.DateTime()
    filledAt = graphene.DateTime()
    filledQuantity = graphene.Float()
    averageFillPrice = graphene.Float()
    commission = graphene.Float()
    notes = graphene.String()

# CryptocurrencyType is defined in crypto_graphql.py

class CryptoPortfolioType(graphene.ObjectType):
    totalValue = graphene.Float()
    holdings = graphene.List(graphene.String)

# Simple auth payload that doesn't use UserType
class AuthPayload(graphene.ObjectType):
    token = graphene.String()
    user = graphene.Field(lambda: UserType)

class UserType(graphene.ObjectType):
    id = graphene.ID()
    email = graphene.String()
    name = graphene.String()
    username = graphene.String()  # Add username field for signals
    # Add missing fields that mobile app expects
    incomeProfile = graphene.Field(IncomeProfileType)
    followedTickers = graphene.List(graphene.String)

# Research-related types
class CompanySnapshotType(graphene.ObjectType):
    name = graphene.String()
    sector = graphene.String()
    marketCap = graphene.Float()
    country = graphene.String()
    website = graphene.String()

    volume = graphene.Float()

class TechnicalType(graphene.ObjectType):
    rsi = graphene.Float()
    macd = graphene.Float()
    macdhistogram = graphene.Float()
    movingAverage50 = graphene.Float()
    movingAverage200 = graphene.Float()
    supportLevel = graphene.Float()
    resistanceLevel = graphene.Float()
    impliedVolatility = graphene.Float()

class SentimentType(graphene.ObjectType):
    label = graphene.String()
    score = graphene.Float()
    confidence = graphene.Float()
    # Use a field name that won't be auto-converted
    article_count = graphene.Int(name='article_count')
    articleCount = graphene.Int()
    
    def resolve_article_count(self, info):
        return getattr(self, 'article_count', 15)
    
    def resolve_articleCount(self, info):
        return getattr(self, 'article_count', 15)

class MacroType(graphene.ObjectType):
    vix = graphene.Float()
    marketSentiment = graphene.String()
    riskAppetite = graphene.String()

class MarketRegimeType(graphene.ObjectType):
    confidence = graphene.Float()
    # Use field names that won't be auto-converted
    market_regime = graphene.String(name='market_regime')
    marketRegime = graphene.String()
    recommended_strategy = graphene.String(name='recommended_strategy')
    recommendedStrategy = graphene.String()
    
    def resolve_market_regime(self, info):
        return getattr(self, 'market_regime', 'bull_market')
    
    def resolve_marketRegime(self, info):
        return getattr(self, 'market_regime', 'bull_market')
    
    def resolve_recommended_strategy(self, info):
        return getattr(self, 'recommended_strategy', 'momentum_trading')
    
    def resolve_recommendedStrategy(self, info):
        return getattr(self, 'recommended_strategy', 'momentum_trading')

class ResearchHubType(graphene.ObjectType):
    symbol = graphene.String()
    snapshot = graphene.Field(CompanySnapshotType)
    quote = graphene.Field(QuoteType)
    technical = graphene.Field(TechnicalType)
    sentiment = graphene.Field(SentimentType)
    macro = graphene.Field(MacroType)
    marketRegime = graphene.Field(MarketRegimeType)
    peers = graphene.List(graphene.String)
    updatedAt = graphene.String()

class ChartDataType(graphene.ObjectType):
    timestamp = graphene.String()
    open = graphene.Float()
    high = graphene.Float()
    low = graphene.Float()
    close = graphene.Float()
    volume = graphene.Float()

class IndicatorsType(graphene.ObjectType):
    SMA20 = graphene.Float()
    SMA50 = graphene.Float()
    EMA12 = graphene.Float()
    EMA26 = graphene.Float()
    BB_upper = graphene.Float()
    BB_middle = graphene.Float()
    BB_lower = graphene.Float()
    RSI14 = graphene.Float()
    MACD = graphene.Float()
    MACD_signal = graphene.Float()
    MACD_hist = graphene.Float()
    # camelCase aliases
    BBUpper = graphene.Float()
    BBMiddle = graphene.Float()
    BBLower = graphene.Float()
    MACDSignal = graphene.Float()
    MACDHist = graphene.Float()
    macdHistogram = graphene.Float()  # Add the missing field

class StockChartDataType(graphene.ObjectType):
    symbol = graphene.String()
    interval = graphene.String()
    limit = graphene.Int()
    currentPrice = graphene.Float()
    change = graphene.Float()
    changePercent = graphene.Float()
    data = graphene.List(ChartDataType)
    indicators = graphene.Field(IndicatorsType)

class CryptoMLSignalType(graphene.ObjectType):
    symbol = graphene.String()
    probability = graphene.Float()
    confidenceLevel = graphene.String()  # Changed from Float to String
    explanation = graphene.String()
    features = graphene.List(graphene.String)
    modelVersion = graphene.String()
    timestamp = graphene.String()

# CryptocurrencyType is defined in crypto_graphql.py
    priceUsd = graphene.Float()
    marketCap = graphene.Float()
    volume24h = graphene.Float()
    change24h = graphene.Float()
    changePercent24h = graphene.Float()

class CryptoRecommendationType(graphene.ObjectType):
    symbol = graphene.String()
    score = graphene.Float()
    probability = graphene.Float()
    confidenceLevel = graphene.String()
    priceUsd = graphene.Float()
    volatilityTier = graphene.String()
    liquidity24hUsd = graphene.Float()
    rationale = graphene.String()
    recommendation = graphene.String()
    riskLevel = graphene.String()

class CryptoHoldingType(graphene.ObjectType):
    cryptocurrency = graphene.Field(CryptocurrencyType)
    quantity = graphene.Float()
    valueUsd = graphene.Float()
    gainLoss = graphene.Float()
    gainLossPercent = graphene.Float()

class CryptoPortfolioType(graphene.ObjectType):
    totalValueUsd = graphene.Float()
    totalGainLoss = graphene.Float()
    totalGainLossPercent = graphene.Float()
    holdings = graphene.List(CryptoHoldingType)

class ObtainJSONWebToken(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)
    
    token = graphene.String()
    user = graphene.Field(UserType)
    
    def mutate(self, info, email, password):
        # For development, always return a mock token and user
        # In production, you would validate credentials here
        mock_token = "mock_jwt_token_for_development"
        mock_user = UserType(
            id=1,
            email=email,
            name='Test User'
        )
        return ObtainJSONWebToken(token=mock_token, user=mock_user)

class BaseQuery(graphene.ObjectType):
    ping = graphene.String()
    me = graphene.Field(UserType)
    portfolioMetrics = graphene.Field(PortfolioMetricsType)
    stocks = graphene.List(
        StockType,
        search=graphene.String(),
        limit=graphene.Int(default_value=10),
        offset=graphene.Int(default_value=0),
    )
    advancedStockScreening = graphene.List(
        AdvancedStockScreeningResultType,
        sector=graphene.String(),
        minMarketCap=graphene.Float(),
        maxMarketCap=graphene.Float(),
        minPeRatio=graphene.Float(),
        maxPeRatio=graphene.Float(),
        minDividendYield=graphene.Float(),
        minBeginnerScore=graphene.Int(),
        sortBy=graphene.String(),
        limit=graphene.Int(default_value=10),
    )
    myWatchlist = graphene.List(
        WatchlistItemType,
        limit=graphene.Int(default_value=10),
    )
    rustStockAnalysis = graphene.Field(
        RustStockAnalysisType,
        symbol=graphene.String(required=True),
    )
    beginnerFriendlyStocks = graphene.List(
        StockType,
        limit=graphene.Int(default_value=10),
    )
    bankAccounts = graphene.List(BankAccountType)
    fundingHistory = graphene.List(FundingHistoryType)
    sblocOffer = graphene.Field(SblocOfferType)
    calculateTargetPrice = graphene.Field(
        TargetPriceResultType,
        entryPrice=graphene.Float(required=True),
        stopPrice=graphene.Float(required=True),
        riskRewardRatio=graphene.Float(),
        atr=graphene.Float(),
        resistanceLevel=graphene.Float(),
        supportLevel=graphene.Float(),
        signalType=graphene.String(),
    )
    calculatePositionSize = graphene.Field(
        PositionSizeResultType,
        accountBalance=graphene.Float(),
        accountEquity=graphene.Float(),
        entryPrice=graphene.Float(required=True),
        stopPrice=graphene.Float(required=True),
        riskPercentage=graphene.Float(),
        riskPerTrade=graphene.Float(),
        riskAmount=graphene.Float(),
        maxPositionSize=graphene.Float(),
        maxPositionPct=graphene.Float(),
        confidence=graphene.Float(),
        method=graphene.String(),
    )
    calculateDynamicStop = graphene.Field(
        DynamicStopResultType,
        entryPrice=graphene.Float(required=True),
        atr=graphene.Float(required=True),
        atrMultiplier=graphene.Float(),
        supportLevel=graphene.Float(),
        resistanceLevel=graphene.Float(),
        signalType=graphene.String(),
    )
    # Add missing queries that mobile app expects
    stockDiscussions = graphene.List(StockDiscussionType, stockSymbol=graphene.String(), limit=graphene.Int())
    cryptoPrices = graphene.List(CryptoPriceType, symbols=graphene.List(graphene.String))
    cryptoPrice = graphene.Field(CryptoPriceType, symbol=graphene.String(required=True))
    portfolioAnalysis = graphene.Field(PortfolioMetricsType)
    researchHub = graphene.Field(ResearchHubType, symbol=graphene.String(required=True))
    stockChartData = graphene.Field(StockChartDataType, 
        symbol=graphene.String(required=True),
        timeframe=graphene.String(),
        interval=graphene.String(),
        limit=graphene.Int(),
        indicators=graphene.List(graphene.String)
    )
    cryptoMlSignal = graphene.Field(CryptoMLSignalType, symbol=graphene.String(required=True))
    cryptoRecommendations = graphene.List(
        CryptoRecommendationType,
        limit=graphene.Int(),
        symbols=graphene.List(graphene.String)
    )
    supportedCurrencies = graphene.List(CryptocurrencyType)
    cryptoPortfolio = graphene.Field(lambda: CryptoPortfolioType)
    dayTradingPicks = graphene.Field(lambda: DayTradingPicksType, mode=graphene.String(required=True))
    aiRecommendations = graphene.Field(AIRecommendationsType, riskTolerance=graphene.String())
    
    # Trading fields
    tradingAccount = graphene.Field(TradingAccountType)
    tradingPositions = graphene.List(TradingPositionType)
    tradingOrders = graphene.List(TradingOrderType, status=graphene.String(), limit=graphene.Int())
    
    # ML System fields
    mlSystemStatus = graphene.Field(MLSystemStatusType)
    
    # Risk Management fields
    riskSummary = graphene.Field(RiskSummaryType)
    getActivePositions = graphene.List(ActivePositionType)
    
    # Social Feed fields
    socialFeed = graphene.List(SocialFeedItemType, limit=graphene.Int(), offset=graphene.Int())
    stockDiscussions = graphene.List(SocialFeedItemType, limit=graphene.Int(), offset=graphene.Int())
    feedByTickers = graphene.List(FeedItemType, symbols=graphene.List(graphene.String), limit=graphene.Int())
    
    # Quotes field
    quotes = graphene.List(QuoteType, symbols=graphene.List(graphene.String))
    
    # Portfolio fields
    myPortfolios = graphene.Field(MyPortfoliosType)

    def resolve_ping(root, info):
        return "pong"
    
    def resolve_me(self, info):
        # Return mock user without authentication for development
        mock_income_profile = IncomeProfileType(
            id=1,
            income_bracket='$75,000 - $100,000',
            age=28,
            investment_goals=['Wealth Building', 'Retirement Savings'],
            risk_tolerance='Moderate',
            investment_horizon='5-10 years',
            created_at='2024-01-01T00:00:00Z',
            updated_at='2024-01-01T00:00:00Z'
        )
        
        return UserType(
            id=1,
            email='test@example.com',
            name='Test User',
            username='testuser',  # Add username for signals
            profilePic='https://example.com/profile.jpg',  # Add profilePic
            followersCount=1247,  # Add followersCount
            followingCount=89,  # Add followingCount
            isFollowingUser=False,  # Add isFollowingUser
            isFollowedByUser=False,  # Add isFollowedByUser
            hasPremiumAccess=True,  # Add hasPremiumAccess
            subscriptionTier='Premium',  # Add subscriptionTier
            incomeProfile=mock_income_profile,
            followedTickers=['AAPL', 'TSLA', 'NVDA']
        )
    
    def resolve_portfolioMetrics(self, info):
        d = _mock_portfolio_metrics()
        # Return the mock data directly - PortfolioMetricsType will handle the field resolution
        return PortfolioMetricsType(
            total_value=d["total_value"],
            total_cost=d["total_cost"],
            total_return=d["total_return"],
            total_return_percent=d["total_return_percent"],
            holdings=d["holdings"],  # Pass the raw data, let Graphene handle the conversion
        )
    
    def resolve_ping(self, info):
        # Simple diagnostic field to test GraphQL endpoint
        return "ok"
    
    def resolve_bankAccounts(self, info):
        # Return mock bank account data for development
        return [
            BankAccountType(
                id="1",
                bankName="Chase Bank",
                accountType="Checking",
                lastFour="1234",
                isVerified=True,
                isPrimary=True,
                linkedAt="2024-01-15T10:30:00Z"
            ),
            BankAccountType(
                id="2", 
                bankName="Bank of America",
                accountType="Savings",
                lastFour="5678",
                isVerified=True,
                isPrimary=False,
                linkedAt="2024-02-20T14:45:00Z"
            )
        ]
    
    def resolve_fundingHistory(self, info):
        # Return mock funding history data for development
        return [
            FundingHistoryType(
                id="1",
                amount=5000.0,
                status="completed",
                bankAccountId="1",
                initiatedAt="2024-03-01T09:00:00Z",
                completedAt="2024-03-01T09:15:00Z"
            ),
            FundingHistoryType(
                id="2",
                amount=2500.0,
                status="pending",
                bankAccountId="2",
                initiatedAt="2024-03-15T11:30:00Z",
                completedAt=None
            )
        ]
    
    def resolve_sblocOffer(self, info):
        # Return mock SBLOC offer data for development
        return SblocOfferType(
            ltv=0.5,  # 50% loan-to-value
            apr=0.085,  # 8.5% APR
            minDraw=1000.0,
            maxDrawMultiplier=0.95,
            disclosures=[
                "Securities-based lending involves risk of loss",
                "Interest rates may vary based on market conditions",
                "Collateral requirements may change"
            ],
            eligibleEquity=50000.0,  # $50k eligible equity
            updatedAt="2024-03-20T12:00:00Z"
        )
    
    def resolve_stocks(self, info, search=None, limit=10, offset=0):
        # Use real ML/AI services to get stock recommendations
        try:
            from .models import Stock
            import django.db.models as djmodels
            
            limit = max(1, min(limit or 10, 200))
            offset = max(0, offset or 0)
            
            # If there's a search term, try to use the stock service to search and sync real data
            if search and search.strip():
                try:
                    from .stock_service import SimpleStockSearchService
                    stock_service = SimpleStockSearchService()
                    # Search and sync stocks from external APIs
                    searched_stocks = stock_service.search_and_sync_stocks(search.strip())
                    if searched_stocks:
                        return searched_stocks[offset:offset+limit]
                except Exception as e:
                    print(f"Stock service search error: {e}")
            
            # Get stocks from database with ML-enhanced scoring
            qs = Stock.objects.all()
            if search:
                qs = qs.filter(
                    djmodels.Q(symbol__icontains=search.upper()) |
                    djmodels.Q(company_name__icontains=search)
                )
            
            # Try to enhance with ML scoring if available
            try:
                from .ml_stock_recommender import MLStockRecommender
                from .models import User
                
                # Get a default user for ML recommendations
                user = User.objects.first()
                if user:
                    ml_recommender = MLStockRecommender()
                    # Get ML-generated stock recommendations
                    recommendations = ml_recommender.generate_ml_recommendations(user, limit=limit + offset)
                    
                    # Apply search filter if provided
                    if search:
                        search_lower = search.lower()
                        recommendations = [
                            rec for rec in recommendations 
                            if (search_lower in rec.stock.symbol.lower() or 
                                search_lower in rec.stock.company_name.lower())
                        ]
                    
                    # Apply pagination
                    recommendations = recommendations[offset:offset + limit]
                    
                    # Convert to StockType format
                    result = []
                    for rec in recommendations:
                        stock = StockType()
                        stock.id = rec.stock.symbol
                        stock.symbol = rec.stock.symbol
                        stock.companyName = rec.stock.company_name
                        stock.currentPrice = float(rec.stock.current_price) if rec.stock.current_price else 0.0
                        stock.changePercent = 0.0  # Will be updated with real-time data
                        stock.sector = rec.stock.sector or 'Unknown'
                        stock.marketCap = float(rec.stock.market_cap) if rec.stock.market_cap else 0.0
                        stock.peRatio = float(rec.stock.pe_ratio) if rec.stock.pe_ratio else 0.0
                        stock.dividendYield = float(rec.stock.dividend_yield) if rec.stock.dividend_yield else 0.0
                        stock.beginnerFriendlyScore = int(rec.confidence_score * 100)  # Convert 0-1 to 0-100
                        result.append(stock)
                    
                    return result
            except Exception as e:
                print(f"ML enhancement error: {e}")
            
            # Fallback to regular database query - convert to StockType objects
            db_stocks = qs.order_by('symbol')[offset:offset+limit]
            result = []
            for stock in db_stocks:
                stock_type = StockType()
                stock_type.id = stock.symbol
                stock_type.symbol = stock.symbol
                stock_type.companyName = stock.company_name
                stock_type.currentPrice = float(stock.current_price) if stock.current_price else 0.0
                stock_type.changePercent = 0.0  # Will be updated with real-time data
                stock_type.sector = stock.sector or 'Unknown'
                stock_type.marketCap = float(stock.market_cap) if stock.market_cap else 0.0
                stock_type.peRatio = float(stock.pe_ratio) if stock.pe_ratio else 0.0
                stock_type.dividendYield = float(stock.dividend_yield) if stock.dividend_yield else 0.0
                stock_type.beginnerFriendlyScore = stock.beginner_friendly_score
                
                # Add budget-aware scoring breakdown
                add_scoring_breakdown(stock_type, user_budget=1000.0)
                
                result.append(stock_type)
            return result
            
        except Exception as e:
            print(f"Stock query error: {e}")
            # Final fallback to mock data
        from core.graphql.queries import get_mock_advanced_screening_results
        
        items = get_mock_advanced_screening_results()
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            items = [
                item for item in items 
                if (search_lower in item.get('symbol', '').lower() or 
                    search_lower in item.get('companyName', '').lower())
            ]
        
        # Apply pagination
        items = items[offset:offset + limit]
        
        # Convert to basic StockType format
        result = []
        for item in items:
                stock = StockType()
                stock.id = item.get('symbol', '')
                stock.symbol = item.get('symbol', '')
                stock.companyName = item.get('company_name', '')
                stock.currentPrice = item.get('current_price', 0.0)
                stock.changePercent = item.get('change_percent', 0.0)
                stock.sector = item.get('sector', '')
                stock.marketCap = item.get('market_cap', 0.0)
                stock.peRatio = item.get('pe_ratio', 0.0)
                stock.dividendYield = item.get('dividend_yield', 0.0)
                stock.beginnerFriendlyScore = item.get('beginner_friendly_score', 0)
                result.append(stock)
        
        return result
    
    def resolve_advancedStockScreening(self, info, sector=None, minMarketCap=None, 
                                     maxMarketCap=None, minPeRatio=None, maxPeRatio=None, 
                                     minDividendYield=None, minBeginnerScore=None, 
                                     sortBy=None, limit=10):
        # Try to get real ML data first, fallback to mock data
        try:
            from .ai_service import AIService
            from .market_data_service import MarketDataService
            
            # Initialize services
            ai_service = AIService()
            market_service = MarketDataService()
            
            # Get real market data for popular stocks
            popular_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'AMD', 'INTC']
            
            # Filter by sector if specified
            if sector:
                sector_symbols = {
                    'Technology': ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'AMD', 'INTC'],
                    'Consumer Discretionary': ['AMZN', 'TSLA', 'NFLX'],
                    'Communication Services': ['GOOGL', 'META', 'NFLX'],
                    'Healthcare': ['JNJ', 'PFE', 'UNH'],
                    'Financial': ['JPM', 'BAC', 'WFC']
                }
                popular_symbols = sector_symbols.get(sector, popular_symbols[:5])
            
            # Get real market data
            real_quotes = market_service.get_quotes(popular_symbols)
            
            if real_quotes and len(real_quotes) > 0:
                # Convert real data to our format
                results = []
                for quote in real_quotes:
                    symbol = quote.get('symbol', 'AAPL')
                    
                    # Get real ML score if available
                    try:
                        ml_score = ai_service.score_stocks_ml([{'symbol': symbol}], {})
                        real_ml_score = ml_score[0].get('ml_score', 0.5) if ml_score else 0.5
                    except:
                        real_ml_score = 0.5
                    
                    # Calculate beginner-friendly score based on real metrics
                    price = quote.get('price', 100.0)
                    change_pct = abs(quote.get('changePct', 0.0))
                    volume = quote.get('volume', 1000000)
                    
                    # Simple beginner score calculation
                    beginner_score = 50.0  # Base score
                    if price < 200:  # Affordable stocks
                        beginner_score += 20
                    if change_pct < 5:  # Stable stocks
                        beginner_score += 15
                    if volume > 1000000:  # Liquid stocks
                        beginner_score += 15
                    
                    beginner_score = min(100, max(0, beginner_score))
                    
                    # Get sector from symbol
                    sector_map = {
                        'AAPL': 'Technology', 'MSFT': 'Technology', 'GOOGL': 'Technology',
                        'META': 'Technology', 'NVDA': 'Technology', 'AMD': 'Technology',
                        'AMZN': 'Consumer Discretionary', 'TSLA': 'Consumer Discretionary',
                        'NFLX': 'Communication Services'
                    }
                    
                    result = {
                        'symbol': symbol,
                        'company_name': quote.get('companyName', f'{symbol} Inc.'),
                        'current_price': price,
                        'change_percent': quote.get('changePct', 0.0),
                        'sector': sector_map.get(symbol, 'Technology'),
                        'market_cap': price * 1000000000,  # Estimate
                        'pe_ratio': 25.0 + (change_pct * 2),  # Estimate based on volatility
                        'dividend_yield': 0.02 if symbol in ['AAPL', 'MSFT'] else 0.0,
                        'beginner_friendly_score': beginner_score / 100.0,
                        'ml_score': real_ml_score,
                        'volume': volume,
                        'high_52_week': price * 1.2,
                        'low_52_week': price * 0.8
                    }
                    results.append(result)
                
                print(f"✅ Using REAL market data for {len(results)} stocks")
            else:
                raise Exception("No real market data available")
                
        except Exception as e:
            print(f"⚠️ Real ML data unavailable ({e}), using mock data")
        results = get_mock_advanced_screening_results()
        
        # Apply filters
        filtered_results = []
        for result in results:
            # Sector filter
            if sector and result['sector'] != sector:
                continue
            
            # Market cap filters
            if minMarketCap and result['market_cap'] < minMarketCap:
                continue
            if maxMarketCap and result['market_cap'] > maxMarketCap:
                continue
            
            # PE ratio filters
            if minPeRatio and result['pe_ratio'] < minPeRatio:
                continue
            if maxPeRatio and result['pe_ratio'] > maxPeRatio:
                continue
            
            # Dividend yield filter
            if minDividendYield and result['dividend_yield'] < minDividendYield:
                continue
            
            # Beginner score filter (convert to float for comparison)
            if minBeginnerScore is not None and result['beginner_friendly_score'] < (minBeginnerScore / 100.0):
                continue
            
            # Generate reasoning based on scores and metrics
            beginner_score = int(float(result.get("beginner_friendly_score", 0)) * 100)
            ml_score = float(result.get("ml_score", 0.0))
            reasoning_parts = []

            if beginner_score >= 70:
                reasoning_parts.append("High beginner-friendly score")
            elif beginner_score >= 50:
                reasoning_parts.append("Moderate beginner-friendly score")
            else:
                reasoning_parts.append("Lower beginner-friendly score")

            if ml_score >= 0.7:
                reasoning_parts.append("Strong ML analysis")
            elif ml_score >= 0.5:
                reasoning_parts.append("Moderate ML analysis")
            else:
                reasoning_parts.append("Weaker ML analysis")

            if result.get("pe_ratio", 0) < 20:
                reasoning_parts.append("Attractive valuation")
            elif result.get("pe_ratio", 0) > 30:
                reasoning_parts.append("Higher valuation")

            if result.get("dividend_yield", 0) > 2.0:
                reasoning_parts.append("Good dividend yield")

            reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Standard investment opportunity"
            
            # Add reasoning to result
            result["reasoning"] = reasoning
            filtered_results.append(result)
        
        # Apply sorting
        if sortBy:
            if sortBy == 'ml_score':
                filtered_results.sort(key=lambda x: x['ml_score'], reverse=True)
            elif sortBy == 'score':
                filtered_results.sort(key=lambda x: x['score'], reverse=True)
            elif sortBy == 'market_cap':
                filtered_results.sort(key=lambda x: x['market_cap'], reverse=True)
            elif sortBy == 'pe_ratio':
                filtered_results.sort(key=lambda x: x['pe_ratio'], reverse=True)
            elif sortBy == 'volatility':
                filtered_results.sort(key=lambda x: x['volatility'], reverse=True)
        
        # Apply limit
        return [AdvancedStockScreeningResultType(**result) for result in filtered_results[:limit]]
    
    def resolve_myWatchlist(self, info, limit=10):
        watchlist = get_mock_watchlist()
        result = []
        for item in watchlist[:limit]:
            # Create the nested stock object
            stock_data = item['stock']
            stock = WatchlistStockType(
                id=stock_data['id'],
                symbol=stock_data['symbol'],
                company_name=stock_data['company_name'],
                companyName=stock_data['companyName'],
                sector=stock_data['sector'],
                current_price=stock_data['current_price'],
                currentPrice=stock_data['currentPrice'],
                beginner_friendly_score=stock_data['beginner_friendly_score'],
                change=stock_data['change'],
                changePercent=stock_data['changePercent']
            )
            
            # Create the watchlist item with the nested stock
            watchlist_item = WatchlistItemType(
                id=item['id'],
                stock=stock,
                added_at=item['added_at'],
                notes=item['notes'],
                target_price=item['target_price'],
                # Direct fields for mobile app compatibility
                symbol=stock_data['symbol'],
                companyName=stock_data['companyName'],
                currentPrice=stock_data['currentPrice'],
                change=stock_data['change'],
                changePercent=stock_data['changePercent']
            )
            result.append(watchlist_item)
        
        return result
    
    def resolve_rustStockAnalysis(self, info, symbol):
        analysis_data = get_mock_rust_stock_analysis(symbol)
        
        # Create technical indicators object
        tech_data = analysis_data['technical_indicators']
        technical_indicators = TechnicalIndicatorsType(
            rsi=tech_data['rsi'],
            macd=tech_data['macd'],
            macd_signal=tech_data['macd_signal'],
            macd_histogram=tech_data['macd_histogram'],
            sma20=tech_data['sma20'],
            sma50=tech_data['sma50'],
            ema12=tech_data['ema12'],
            ema26=tech_data['ema26'],
            bollinger_upper=tech_data['bollinger_upper'],
            bollinger_lower=tech_data['bollinger_lower'],
            bollinger_middle=tech_data['bollinger_middle']
        )
        
        # Create fundamental analysis object
        fund_data = analysis_data['fundamental_analysis']
        fundamental_analysis = FundamentalAnalysisType(
            valuation_score=fund_data['valuation_score'],
            growth_score=fund_data['growth_score'],
            stability_score=fund_data['stability_score'],
            debt_score=fund_data['debt_score'],
            dividend_score=fund_data.get('dividend_score', 0),
            peRatio=fund_data.get('peRatio', 25.0),  # Add missing field
            marketCap=fund_data.get('marketCap', 1000000000.0)  # Add missing field
        )
        
        # Create the main analysis object
        return RustStockAnalysisType(
            symbol=analysis_data['symbol'],
            beginner_friendly_score=analysis_data['beginner_friendly_score'],
            risk_level=analysis_data['risk_level'],
            recommendation=analysis_data['recommendation'],
            technical_indicators=technical_indicators,
            fundamental_analysis=fundamental_analysis,
            reasoning=analysis_data['reasoning']
        )
    
    def resolve_beginnerFriendlyStocks(self, info, limit=10):
        # Use real ML/AI services to get beginner-friendly stock recommendations
        try:
            from .models import Stock
            
            # Try to enhance with ML scoring if available
            try:
                from .ml_stock_recommender import MLStockRecommender
                from .models import User
                
                # Get a default user for ML recommendations
                user = User.objects.first()
                if user:
                    ml_recommender = MLStockRecommender()
                    
                    # Get ML-generated beginner-friendly stock recommendations
                    recommendations = ml_recommender.get_beginner_friendly_stocks(user, limit=limit)
                    
                    # Convert to StockType format
                    result = []
                    for rec in recommendations:
                        stock = StockType()
                        stock.id = rec.stock.symbol
                        stock.symbol = rec.stock.symbol
                        stock.companyName = rec.stock.company_name
                        stock.currentPrice = float(rec.stock.current_price) if rec.stock.current_price else 0.0
                        stock.changePercent = 0.0  # Will be updated with real-time data
                        stock.sector = rec.stock.sector or 'Unknown'
                        stock.marketCap = float(rec.stock.market_cap) if rec.stock.market_cap else 0.0
                        stock.peRatio = float(rec.stock.pe_ratio) if rec.stock.pe_ratio else 0.0
                        stock.dividendYield = float(rec.stock.dividend_yield) if rec.stock.dividend_yield else 0.0
                        stock.beginnerFriendlyScore = int(rec.confidence_score * 100)  # Convert 0-1 to 0-100
                        result.append(stock)
                    
                    return result
            except Exception as e:
                print(f"ML enhancement error: {e}")
            
            # Fallback to database query - convert to StockType objects
            db_stocks = Stock.objects.filter(
                beginner_friendly_score__gte=65, # Moderate beginner-friendly score
                market_cap__gte=10000000000, # Mid to large cap companies (>$10B)
            ).order_by('-beginner_friendly_score')[:limit]
            
            result = []
            for stock in db_stocks:
                stock_type = StockType()
                stock_type.id = stock.symbol
                stock_type.symbol = stock.symbol
                stock_type.companyName = stock.company_name
                stock_type.currentPrice = float(stock.current_price) if stock.current_price else 0.0
                stock_type.changePercent = 0.0  # Will be updated with real-time data
                stock_type.sector = stock.sector or 'Unknown'
                stock_type.marketCap = float(stock.market_cap) if stock.market_cap else 0.0
                stock_type.peRatio = float(stock.pe_ratio) if stock.pe_ratio else 0.0
                stock_type.dividendYield = float(stock.dividend_yield) if stock.dividend_yield else 0.0
                stock_type.beginnerFriendlyScore = stock.beginner_friendly_score
                
                # Add budget-aware scoring breakdown
                add_scoring_breakdown(stock_type, user_budget=1000.0)
                
                result.append(stock_type)
            return result
            
        except Exception as e:
            print(f"Beginner-friendly stock query error: {e}")
            # Final fallback to mock data
        from core.graphql.queries import get_mock_advanced_screening_results
        
        # Get mock data and filter for beginner-friendly stocks (score >= 80)
        mock_data = get_mock_advanced_screening_results()
        beginner_stocks = [
            stock for stock in mock_data 
            if stock.get('beginner_friendly_score', 0) >= 80
        ]
        
        # Sort by beginner-friendly score (highest first) and limit
        beginner_stocks.sort(key=lambda x: x.get('beginner_friendly_score', 0), reverse=True)
        beginner_stocks = beginner_stocks[:limit]
        
        # Convert to GraphQL format
        result = []
        for stock_data in beginner_stocks:
                stock = StockType()
                stock.id = stock_data.get('id', '')
                stock.symbol = stock_data.get('symbol', '')
                stock.companyName = stock_data.get('company_name', '')
                stock.currentPrice = stock_data.get('current_price', 0.0)
                stock.changePercent = stock_data.get('change_percent', 0.0)
                stock.sector = stock_data.get('sector', '')
                stock.marketCap = stock_data.get('market_cap', 0.0)
                stock.peRatio = stock_data.get('pe_ratio', 0.0)
                stock.dividendYield = stock_data.get('dividend_yield', 0.0)
                stock.beginnerFriendlyScore = stock_data.get('beginner_friendly_score', 0)
                result.append(stock)
        
        return result
    
    def resolve_stockDiscussions(self, info, stockSymbol=None, limit=10):
        """Resolve stock discussions query"""
        from core.models import StockDiscussion
        
        discussions = StockDiscussion.objects.all()
        if stockSymbol:
            discussions = discussions.filter(stock__symbol__iexact=stockSymbol)
        
        return discussions[:limit]
    
    def resolve_cryptoPrices(self, info, symbols=None):
        """Resolve crypto prices query"""
        # Return mock crypto prices for now
        mock_prices = [
            {"symbol": "BTC", "price": 45000.0, "change24h": 1200.0, "changePercent24h": 2.74},
            {"symbol": "ETH", "price": 3200.0, "change24h": -50.0, "changePercent24h": -1.54}
        ]
        
        if symbols:
            return [price for price in mock_prices if price["symbol"] in symbols]
        return mock_prices
    
    def resolve_cryptoPrice(self, info, symbol):
        """Resolve single crypto price query"""
        # Return None for now - let the frontend handle missing data gracefully
        # In a real implementation, this would query the database or external API
        return None
    
    def resolve_portfolioAnalysis(self, info):
        """Resolve portfolio analysis query - alias for portfolioMetrics"""
        # Return mock portfolio metrics for now
        from core.graphql.queries import _mock_portfolio_metrics, PortfolioMetricsType
        mock_data = _mock_portfolio_metrics()
        return PortfolioMetricsType(
            total_value=mock_data.get('total_value', 0.0),
            total_cost=mock_data.get('total_cost', 0.0),
            total_return=mock_data.get('total_return', 0.0),
            total_return_percent=mock_data.get('total_return_percent', 0.0),
            holdings=mock_data.get('holdings', []),
            dailyChange=mock_data.get('dailyChange', 0.0),
            dailyChangePercent=mock_data.get('dailyChangePercent', 0.0)
        )
    
    def resolve_calculateTargetPrice(self, info, entryPrice, stopPrice, riskRewardRatio=None, atr=None, resistanceLevel=None, supportLevel=None, signalType=None):
        # Import the resolver from queries.py
        from core.graphql.queries import Query as SwingQuery
        swing_query = SwingQuery()
        return swing_query.resolve_calculateTargetPrice(info, entryPrice, stopPrice, riskRewardRatio, atr, resistanceLevel, supportLevel, signalType)
    
    def resolve_calculatePositionSize(self, info, accountBalance=None, accountEquity=None, entryPrice=None, stopPrice=None, riskPercentage=None, riskPerTrade=None, riskAmount=None, maxPositionSize=None, maxPositionPct=None, confidence=None, method=None):
        # Import the resolver from queries.py
        from core.graphql.queries import Query as SwingQuery
        swing_query = SwingQuery()
        return swing_query.resolve_calculatePositionSize(info, accountBalance, accountEquity, entryPrice, stopPrice, riskPercentage, riskPerTrade, riskAmount, maxPositionSize, maxPositionPct, confidence, method)
    
    def resolve_calculateDynamicStop(self, info, entryPrice, atr, atrMultiplier=None, supportLevel=None, resistanceLevel=None, signalType=None):
        # Import the resolver from queries.py
        from core.graphql.queries import Query as SwingQuery
        swing_query = SwingQuery()
        return swing_query.resolve_calculateDynamicStop(info, entryPrice, atr, atrMultiplier, supportLevel, resistanceLevel, signalType)
    
    
    def resolve_researchHub(self, info, symbol):
        # Mock research hub data for demo
        return ResearchHubType(
            symbol=symbol,
            snapshot=CompanySnapshotType(
                name=f"{symbol} Inc.",
                sector="Technology",
                marketCap=2000000000000.0,
                country="USA",
                website=f"https://{symbol.lower()}.com"
            ),
            quote=QuoteType(
                price=150.0,
                chg=2.5,
                chgPct=1.69,
                high=152.0,
                low=148.0,
                volume=50000000.0
            ),
            technical=TechnicalType(
                rsi=65.0,
                macd=1.2,
                macdhistogram=0.3,
                movingAverage50=145.0,
                movingAverage200=140.0,
                supportLevel=145.0,
                resistanceLevel=155.0,
                impliedVolatility=0.25
            ),
            sentiment=SentimentType(
                label="Bullish",
                score=0.75,
                article_count=25,
                confidence=0.8,
                articleCount=25
            ),
            macro=MacroType(
                vix=18.5,
                marketSentiment="Risk On",
                riskAppetite="High"
            ),
            marketRegime=MarketRegimeType(
                market_regime="Bull Market",
                confidence=0.85,
                recommended_strategy="Growth",
                marketRegime="Bull Market",
                recommendedStrategy="Growth"
            ),
            peers=["MSFT", "GOOGL", "AMZN"],
            updatedAt="2025-09-25T16:45:00Z"
        )
    
    def resolve_stockChartData(self, info, symbol, timeframe="1D", interval="1D", limit=180, indicators=None):
        # Use real market data from Finnhub/Polygon
        from .market_data_service import MarketDataService
        
        try:
            market_service = MarketDataService()
            
            # Map timeframe to Finnhub resolution
            resolution_map = {
                '1H': '1',
                '1D': 'D',
                '1W': 'W',
                '1M': 'M'
            }
            resolution = resolution_map.get(timeframe, 'D')
            
            # Get real chart data
            chart_data = market_service.get_stock_chart_data(symbol, resolution, limit)
            
            if not chart_data or not chart_data.get('data'):
                # Fallback to mock data if real data unavailable
                import time
                current_time = int(time.time())
                chart_data = []
                base_price = 150.0
                for i in range(min(limit, 30)):
                    timestamp = current_time - (i * 3600)
                    price = base_price + (i * 0.5) + (i % 3 - 1) * 2
                    chart_data.append(ChartDataType(
                        timestamp=str(timestamp),
                        open=price,
                        high=price + 1.0,
                        low=price - 1.0,
                        close=price + 0.5,
                        volume=1000000.0
                    ))
            else:
                # Convert real data to ChartDataType objects
                chart_data_objects = []
                for point in chart_data['data']:
                    chart_data_objects.append(ChartDataType(
                        timestamp=str(point.get('timestamp', '')),
                        open=point.get('open', 0),
                        high=point.get('high', 0),
                        low=point.get('low', 0),
                        close=point.get('close', 0),
                        volume=point.get('volume', 0)
                    ))
                chart_data = chart_data_objects
                
        except Exception as e:
            # Fallback to mock data on error
            import time
            current_time = int(time.time())
            chart_data = []
            base_price = 150.0
            for i in range(min(limit, 30)):
                timestamp = current_time - (i * 3600)
                price = base_price + (i * 0.5) + (i % 3 - 1) * 2
                chart_data.append(ChartDataType(
                    timestamp=str(timestamp),
                    open=price,
                    high=price + 1.0,
                    low=price - 1.0,
                    close=price + 0.5,
                    volume=1000000.0
                ))
        
        # Handle indicators parameter - support both 'indicators' and 'inds'
        indicators_list = indicators or []
        
        # Generate indicators based on what's requested
        indicators_data = {}
        if not indicators_list or "SMA20" in indicators_list:
            indicators_data["SMA20"] = 148.0
        if not indicators_list or "SMA50" in indicators_list:
            indicators_data["SMA50"] = 145.0
        if not indicators_list or "EMA12" in indicators_list:
            indicators_data["EMA12"] = 149.0
        if not indicators_list or "EMA26" in indicators_list:
            indicators_data["EMA26"] = 146.0
        if not indicators_list or "BB" in indicators_list or "BB_upper" in indicators_list:
            indicators_data["BB_upper"] = 155.0
            indicators_data["BB_middle"] = 150.0
            indicators_data["BB_lower"] = 145.0
            indicators_data["BBUpper"] = 155.0
            indicators_data["BBMiddle"] = 150.0
            indicators_data["BBLower"] = 145.0
        if not indicators_list or "RSI" in indicators_list or "RSI14" in indicators_list:
            indicators_data["RSI14"] = 65.0
        if not indicators_list or "MACD" in indicators_list:
            indicators_data["MACD"] = 1.2
        if not indicators_list or "MACD" in indicators_list or "MACD_signal" in indicators_list:
            indicators_data["MACD_signal"] = 1.0
            indicators_data["MACDSignal"] = 1.0
        if not indicators_list or "MACDHist" in indicators_list or "MACD_hist" in indicators_list:
            indicators_data["MACD_hist"] = 0.2
            indicators_data["MACDHist"] = 0.2
            indicators_data["macdHistogram"] = 0.2
        
        # Calculate current price from the latest data point
        current_price = 150.0  # Default fallback
        if chart_data:
            current_price = chart_data[-1].close if hasattr(chart_data[-1], 'close') else 150.0
        
        return StockChartDataType(
            symbol=symbol,
            interval=interval,
            limit=limit,
            currentPrice=current_price,
            change=2.5,
            changePercent=1.69,
            data=chart_data,
            indicators=IndicatorsType(**indicators_data)
        )

    def resolve_cryptoMlSignal(self, info, symbol):
        # Mock crypto ML signal data for demo
        import time
        current_time = int(time.time())
        
        # Mock probability based on symbol
        if symbol.upper() == 'BTC':
            probability = 0.75
            confidence_level = 0.85
            confidence_level_str = "HIGH"
            explanation = "Strong bullish momentum detected with high volume and positive sentiment indicators"
            features = ["price_momentum", "volume_spike", "sentiment_score", "technical_breakout"]
        elif symbol.upper() == 'ETH':
            probability = 0.68
            confidence_level = 0.78
            confidence_level_str = "HIGH"
            explanation = "Moderate bullish signal with improving technical indicators"
            features = ["rsi_oversold_recovery", "moving_average_crossover", "volume_trend"]
        else:
            probability = 0.55
            confidence_level = 0.65
            confidence_level_str = "MEDIUM"
            explanation = "Neutral to slightly bullish signal with mixed indicators"
            features = ["price_action", "market_sentiment", "volatility_analysis"]
        
        return CryptoMLSignalType(
            symbol=symbol.upper(),
            probability=probability,
            confidenceLevel=confidence_level_str,  # Return string instead of number
            explanation=explanation,
            features=features,
            modelVersion="v2.1.0",
            timestamp=str(current_time)
        )

    def resolve_cryptoRecommendations(self, info, limit=10, symbols=None):
        # Mock crypto recommendations data
        recommendations = [
            {
                'symbol': 'BTC',
                'score': 0.85,
                'probability': 0.75,
                'confidenceLevel': 'HIGH',
                'priceUsd': 45000.0,
                'volatilityTier': 'MEDIUM',
                'liquidity24hUsd': 25000000000.0,
                'rationale': 'Strong institutional adoption and limited supply',
                'recommendation': 'BUY',
                'riskLevel': 'MEDIUM'
            },
            {
                'symbol': 'ETH',
                'score': 0.78,
                'probability': 0.68,
                'confidenceLevel': 'HIGH',
                'priceUsd': 3000.0,
                'volatilityTier': 'HIGH',
                'liquidity24hUsd': 15000000000.0,
                'rationale': 'Ethereum 2.0 upgrades and DeFi growth',
                'recommendation': 'BUY',
                'riskLevel': 'HIGH'
            },
            {
                'symbol': 'ADA',
                'score': 0.65,
                'probability': 0.55,
                'confidenceLevel': 'MEDIUM',
                'priceUsd': 0.45,
                'volatilityTier': 'HIGH',
                'liquidity24hUsd': 500000000.0,
                'rationale': 'Smart contract platform with strong fundamentals',
                'recommendation': 'HOLD',
                'riskLevel': 'HIGH'
            },
            {
                'symbol': 'SOL',
                'score': 0.72,
                'probability': 0.62,
                'confidenceLevel': 'MEDIUM',
                'priceUsd': 95.0,
                'volatilityTier': 'HIGH',
                'liquidity24hUsd': 2000000000.0,
                'rationale': 'Fast blockchain with growing ecosystem',
                'recommendation': 'BUY',
                'riskLevel': 'HIGH'
            },
            {
                'symbol': 'DOT',
                'score': 0.68,
                'probability': 0.58,
                'confidenceLevel': 'MEDIUM',
                'priceUsd': 6.5,
                'volatilityTier': 'MEDIUM',
                'liquidity24hUsd': 800000000.0,
                'rationale': 'Interoperability protocol with strong development',
                'recommendation': 'HOLD',
                'riskLevel': 'MEDIUM'
            },
            {
                'symbol': 'MATIC',
                'score': 0.70,
                'probability': 0.60,
                'confidenceLevel': 'MEDIUM',
                'priceUsd': 0.85,
                'volatilityTier': 'HIGH',
                'liquidity24hUsd': 600000000.0,
                'rationale': 'Layer 2 scaling solution for Ethereum',
                'recommendation': 'BUY',
                'riskLevel': 'MEDIUM'
            }
        ]
        
        # Filter by symbols if provided
        if symbols:
            recommendations = [r for r in recommendations if r['symbol'] in symbols]
        
        # Limit results
        recommendations = recommendations[:limit]
        
        return [CryptoRecommendationType(**rec) for rec in recommendations]

    def resolve_supportedCurrencies(self, info):
        # Return empty list for now - let the frontend handle missing data gracefully
        # In a real implementation, this would query the database
        return []

    def resolve_cryptoPortfolio(self, info):
        # Return empty portfolio for now - let the frontend handle missing data gracefully
        # In a real implementation, this would query the database
        return None
    
    def resolve_tradingAccount(self, info):
        # Mock trading account data
        from datetime import datetime
        return {
            "id": "1",
            "buyingPower": 50000.0,
            "cash": 25000.0,
            "portfolioValue": 75000.0,
            "equity": 75000.0,
            "dayTradeCount": 0,
            "patternDayTrader": False,
            "tradingBlocked": False,
            "dayTradingBuyingPower": 100000.0,
            "isDayTradingEnabled": True,
            "accountStatus": "ACTIVE",
            "createdAt": datetime(2024, 1, 1, 0, 0, 0)
        }
    
    def resolve_tradingPositions(self, info):
        # Mock trading positions data
        return [
            {
                "id": "1",
                "symbol": "AAPL",
                "quantity": 100.0,
                "marketValue": 15000.0,
                "costBasis": 14000.0,
                "unrealizedPl": 1000.0,
                "unrealizedpi": 1000.0,
                "unrealizedPI": 1000.0,
                "unrealizedPLPercent": 0.071,
                "unrealizedPlpc": 0.071,
                "currentPrice": 150.0,
                "side": "long"
            },
            {
                "id": "2",
                "symbol": "TSLA",
                "quantity": 50.0,
                "marketValue": 10000.0,
                "costBasis": 12000.0,
                "unrealizedPl": -2000.0,
                "unrealizedpi": -2000.0,
                "unrealizedPI": -2000.0,
                "unrealizedPLPercent": -0.167,
                "unrealizedPlpc": -0.167,
                "currentPrice": 200.0,
                "side": "long"
            }
        ]
    
    def resolve_tradingOrders(self, info, status=None, limit=None):
        # Mock trading orders data
        from datetime import datetime
        mock_orders = [
            {
                "id": "1",
                "symbol": "AAPL",
                "side": "BUY",
                "orderType": "LIMIT",
                "quantity": 10.0,
                "price": 145.0,
                "stopPrice": None,
                "status": "FILLED",
                "createdAt": datetime(2024, 1, 15, 10, 30, 0),
                "filledAt": datetime(2024, 1, 15, 10, 31, 0),
                "filledQuantity": 10.0,
                "averageFillPrice": 144.95,
                "commission": 1.0,
                "notes": "Limit order filled"
            },
            {
                "id": "2",
                "symbol": "MSFT",
                "side": "SELL",
                "orderType": "MARKET",
                "quantity": 5.0,
                "price": None,
                "stopPrice": None,
                "status": "PENDING",
                "createdAt": datetime(2024, 1, 16, 14, 20, 0),
                "filledAt": None,
                "filledQuantity": 0.0,
                "averageFillPrice": None,
                "commission": 0.0,
                "notes": "Market sell order pending"
            }
        ]
        
        # Filter by status if provided
        if status:
            mock_orders = [order for order in mock_orders if order["status"] == status.upper()]
        
        # Apply limit if provided
        if limit:
            mock_orders = mock_orders[:limit]
        
        return mock_orders
    
    def resolve_optionsAnalysis(self, info, symbol):
        # Try real options data first, fallback to mock data
        from datetime import datetime, timedelta
        import random
        
        try:
            from .market_data_service import MarketDataService
            market_service = MarketDataService()
            
            # Get real market data for the symbol
            real_quotes = market_service.get_quotes([symbol])
            
            if real_quotes and len(real_quotes) > 0:
                real_quote = real_quotes[0]
                current_price = real_quote.get('price', 150.0)
                print(f"✅ Using REAL options data for {symbol} at ${current_price}")
            else:
                raise Exception("No real market data available")
                
        except Exception as e:
            print(f"⚠️ Real options data unavailable ({e}), using mock data")
            # Use a more stable price for better performance (less random variation)
            base_price = 150.0
            current_price = base_price + random.uniform(-5, 5)  # Reduced variation
        
        # Generate expiration dates (next 4 Fridays)
        today = datetime.now()
        expirations = []
        for i in range(1, 5):
            exp_date = today + timedelta(days=7*i)
            expirations.append(exp_date.strftime('%Y-%m-%d'))
        
        # Generate calls and puts (reduced set for better performance)
        calls = []
        puts = []
        
        # Only generate options for 2 expiration dates and fewer strikes for better performance
        for exp in expirations[:2]:  # Only first 2 expirations
            for strike in range(int(current_price - 15), int(current_price + 15), 10):  # Wider strike spacing
                # Call option
                call = OptionType()
                call.symbol = f'{symbol}{exp.replace("-", "")}C{strike:05d}'
                call.contractSymbol = f'{symbol}{exp.replace("-", "")}C{strike:05d}'
                call.strike = float(strike)
                call.expirationDate = exp
                call.optionType = 'call'
                call.bid = max(0.01, (current_price - strike) * 0.1 + random.uniform(-0.5, 0.5))
                call.ask = max(0.01, (current_price - strike) * 0.1 + random.uniform(0.5, 1.0))
                call.lastPrice = max(0.01, (current_price - strike) * 0.1 + random.uniform(-0.3, 0.3))
                call.volume = random.randint(100, 500)  # Reduced range
                call.openInterest = random.randint(1000, 3000)  # Reduced range
                call.impliedVolatility = round(random.uniform(0.20, 0.35), 3)  # Simplified range
                call.delta = round(max(0, min(1, (current_price - strike) / current_price)), 3)  # Simplified calculation
                call.gamma = round(random.uniform(0.005, 0.015), 4)  # Simplified range
                call.theta = round(-random.uniform(0.02, 0.04), 3)  # Simplified range
                call.vega = round(random.uniform(0.15, 0.25), 3)  # Simplified range
                call.rho = round(random.uniform(0.02, 0.04), 3)  # Simplified range
                call.intrinsicValue = max(0, current_price - strike)
                call.timeValue = max(0.01, random.uniform(0.5, 5.0))
                call.daysToExpiration = (datetime.strptime(exp, '%Y-%m-%d') - today).days
                calls.append(call)
                
                # Put option
                put = OptionType()
                put.symbol = f'{symbol}{exp.replace("-", "")}P{strike:05d}'
                put.contractSymbol = f'{symbol}{exp.replace("-", "")}P{strike:05d}'
                put.strike = float(strike)
                put.expirationDate = exp
                put.optionType = 'put'
                put.bid = max(0.01, (strike - current_price) * 0.1 + random.uniform(-0.5, 0.5))
                put.ask = max(0.01, (strike - current_price) * 0.1 + random.uniform(0.5, 1.0))
                put.lastPrice = max(0.01, (strike - current_price) * 0.1 + random.uniform(-0.3, 0.3))
                put.volume = random.randint(100, 500)  # Reduced range
                put.openInterest = random.randint(1000, 3000)  # Reduced range
                put.impliedVolatility = round(random.uniform(0.20, 0.35), 3)  # Simplified range
                put.delta = round(max(-1, min(0, (current_price - strike) / current_price)), 3)  # Simplified calculation
                put.gamma = round(random.uniform(0.005, 0.015), 4)  # Simplified range
                put.theta = round(-random.uniform(0.02, 0.04), 3)  # Simplified range
                put.vega = round(random.uniform(0.15, 0.25), 3)  # Simplified range
                put.rho = round(-random.uniform(0.02, 0.04), 3)  # Simplified range
                put.intrinsicValue = max(0, strike - current_price)
                put.timeValue = max(0.01, random.uniform(0.5, 5.0))
                put.daysToExpiration = (datetime.strptime(exp, '%Y-%m-%d') - today).days
                puts.append(put)
        
        # Calculate additional metrics
        total_call_volume = sum(call.volume for call in calls)
        total_put_volume = sum(put.volume for put in puts)
        put_call_ratio = total_put_volume / total_call_volume if total_call_volume > 0 else 0.0
        
        # Calculate average implied volatility
        all_ivs = [call.impliedVolatility for call in calls] + [put.impliedVolatility for put in puts]
        avg_iv = sum(all_ivs) / len(all_ivs) if all_ivs else 0.0
        
        # Generate mock unusual flow data
        top_trades = [
            TopTradeType(
                symbol=f"{symbol}20251007C00150",
                contractSymbol=f"{symbol}20251007C00150",
                optionType="call",
                strike=150.0,
                expirationDate="2025-10-07",
                volume=5000,
                openInterest=10000,
                premium=2.50,
                impliedVolatility=0.25,
                unusualActivityScore=0.85,
                activityType="sweep",
                type="unusual"
            ),
            TopTradeType(
                symbol=f"{symbol}20251014P00140",
                contractSymbol=f"{symbol}20251014P00140",
                optionType="put",
                strike=140.0,
                expirationDate="2025-10-14",
                volume=3000,
                openInterest=8000,
                premium=1.80,
                impliedVolatility=0.30,
                unusualActivityScore=0.75,
                activityType="block",
                type="unusual"
            )
        ]
        
        unusual_flow = UnusualFlowType(
            symbol=symbol,
            totalVolume=50000,
            unusualVolume=8000,
            unusualVolumePercent=16.0,
            topTrades=top_trades,
            sweepTrades=[f"{symbol}20251021C00155", f"{symbol}20251028P00145"],
            blockTrades=[f"{symbol}20251014C00150", f"{symbol}20251021P00140"],
            lastUpdated="2025-09-30T15:30:00Z"
        )
        
        # Generate mock recommended strategies
        recommended_strategies = [
            RecommendedStrategyType(
                strategyName="Covered Call Strategy",
                strategyType="income",
                description="Sell call options against long stock position",
                riskLevel="low",
                marketOutlook="neutral",
                maxProfit=2.50,
                maxLoss=-10.0,
                breakevenPoints=[145.0, 155.0],
                probabilityOfProfit=0.65,
                riskRewardRatio=0.25,
                daysToExpiration=30,
                totalCost=0.0,
                totalCredit=2.50
            ),
            RecommendedStrategyType(
                strategyName="Protective Put Strategy",
                strategyType="protection",
                description="Buy put options to protect long stock position",
                riskLevel="low",
                marketOutlook="bearish",
                maxProfit=1000.0,  # Large but finite number
                maxLoss=-2.0,
                breakevenPoints=[148.0],
                probabilityOfProfit=0.40,
                riskRewardRatio=500.0,  # Large but finite number
                daysToExpiration=30,
                totalCost=2.0,
                totalCredit=0.0
            ),
            RecommendedStrategyType(
                strategyName="Iron Condor Strategy",
                strategyType="neutral",
                description="Sell call and put spreads for income",
                riskLevel="medium",
                marketOutlook="neutral",
                maxProfit=1.50,
                maxLoss=-3.50,
                breakevenPoints=[146.5, 153.5],
                probabilityOfProfit=0.70,
                riskRewardRatio=0.43,
                daysToExpiration=30,
                totalCost=0.0,
                totalCredit=1.50
            ),
            RecommendedStrategyType(
                strategyName="Straddle Strategy",
                strategyType="volatility",
                description="Buy call and put at same strike",
                riskLevel="high",
                marketOutlook="volatile",
                maxProfit=1000.0,  # Large but finite number
                maxLoss=-5.0,
                breakevenPoints=[145.0, 155.0],
                probabilityOfProfit=0.30,
                riskRewardRatio=200.0,  # Large but finite number
                daysToExpiration=30,
                totalCost=5.0,
                totalCredit=0.0
            )
        ]
        
        # Determine market sentiment based on put/call ratio
        if put_call_ratio > 1.2:
            market_sentiment = MarketSentimentType(
                sentiment="Bearish",
                sentimentDescription="High put activity suggests bearish sentiment"
            )
            sentiment_score = -0.7
            sentiment_description = "High put activity suggests bearish sentiment"
        elif put_call_ratio < 0.8:
            market_sentiment = MarketSentimentType(
                sentiment="Bullish",
                sentimentDescription="High call activity suggests bullish sentiment"
            )
            sentiment_score = 0.7
            sentiment_description = "High call activity suggests bullish sentiment"
        else:
            market_sentiment = MarketSentimentType(
                sentiment="Neutral",
                sentimentDescription="Balanced options activity suggests neutral sentiment"
            )
            sentiment_score = 0.0
            sentiment_description = "Balanced options activity suggests neutral sentiment"
        
        # Calculate skew (difference between put and call IVs)
        call_ivs = [call.impliedVolatility for call in calls if call.impliedVolatility > 0]
        put_ivs = [put.impliedVolatility for put in puts if put.impliedVolatility > 0]
        avg_call_iv = sum(call_ivs) / len(call_ivs) if call_ivs else 0.0
        avg_put_iv = sum(put_ivs) / len(put_ivs) if put_ivs else 0.0
        skew = avg_put_iv - avg_call_iv
        
        # Generate mock Greeks summary
        greeks_summary = GreeksType(
            delta=0.5,
            gamma=0.02,
            theta=-0.05,
            vega=0.15,
            rho=0.01
        )
        
        return OptionsAnalysisType(
            underlyingSymbol=symbol,
            underlyingPrice=current_price,
            optionsChain=OptionsChainType(
                expirationDates=expirations,
                calls=calls,
                puts=puts,
                greeks=greeks_summary
            ),
            unusualFlow=unusual_flow,
            recommendedStrategies=recommended_strategies,
            marketSentiment=market_sentiment,
            putCallRatio=round(put_call_ratio, 3),
            impliedVolatilityRank=round(avg_iv, 3),
            skew=round(skew, 3),
            sentimentScore=round(sentiment_score, 2),
            sentimentDescription=sentiment_description
        )

class Query(SwingQuery, BaseQuery, SblocQuery, NotificationQuery, BenchmarkQuery, graphene.ObjectType):
    # merging by multiple inheritance; keep simple to avoid MRO issues
    optionOrders = graphene.List(OptionOrderType, status=graphene.String())
    
    # Options Analysis
    optionsAnalysis = graphene.Field(lambda: OptionsAnalysisType, symbol=graphene.String(required=True))
    
    def resolve_optionOrders(self, info, status=None):
        # Mock implementation - return sample option orders
        from datetime import datetime, timedelta
        
        mock_orders = [
            OptionOrderType(
                id="1",
                symbol="AAPL",
                optionType="CALL",
                strike=150.0,
                expiration="2024-12-20",
                side="BUY",
                quantity=10,
                orderType="LIMIT",
                limitPrice=5.50,
                timeInForce="GTC",
                status="FILLED",
                filledPrice=5.45,
                filledQuantity=10,
                createdAt=datetime.now() - timedelta(days=1),
                updatedAt=datetime.now() - timedelta(hours=2),
                notes="Bullish play on earnings"
            ),
            OptionOrderType(
                id="2",
                symbol="TSLA",
                optionType="PUT",
                strike=200.0,
                expiration="2024-11-15",
                side="SELL",
                quantity=5,
                orderType="MARKET",
                limitPrice=None,
                timeInForce="DAY",
                status="PENDING",
                filledPrice=None,
                filledQuantity=0,
                createdAt=datetime.now() - timedelta(hours=3),
                updatedAt=datetime.now() - timedelta(minutes=30),
                notes="Hedge against portfolio"
            ),
            OptionOrderType(
                id="3",
                symbol="NVDA",
                optionType="CALL",
                strike=400.0,
                expiration="2024-10-18",
                side="BUY",
                quantity=20,
                orderType="LIMIT",
                limitPrice=12.00,
                timeInForce="GTC",
                status="CANCELLED",
                filledPrice=None,
                filledQuantity=0,
                createdAt=datetime.now() - timedelta(days=2),
                updatedAt=datetime.now() - timedelta(days=1),
                notes="Cancelled due to market conditions"
            )
        ]
        
        # Filter by status if provided
        if status:
            mock_orders = [order for order in mock_orders if order.status == status.upper()]
        
        return mock_orders

    def resolve_mlSystemStatus(self, info):
        # Mock implementation for ML system status
        from datetime import datetime, timedelta
        
        # Create mock outcome tracking
        outcome_tracking = {
            "total_outcomes": 1250,
            "recent_outcomes": 45
        }
        
        # Create mock models
        models = {
            "safe_model": "safe_model_v2.1.3",
            "aggressive_model": "aggressive_model_v1.8.7"
        }
        
        # Create mock bandit strategies
        bandit = {
            "breakout": {
                "win_rate": 0.68,
                "confidence": 0.85,
                "alpha": 12.5,
                "beta": 5.8
            },
            "mean_reversion": {
                "win_rate": 0.72,
                "confidence": 0.78,
                "alpha": 15.2,
                "beta": 6.1
            },
            "momentum": {
                "win_rate": 0.65,
                "confidence": 0.82,
                "alpha": 11.8,
                "beta": 6.4
            },
            "etf_rotation": {
                "win_rate": 0.58,
                "confidence": 0.75,
                "alpha": 9.3,
                "beta": 6.7
            }
        }
        
        # Create mock last training times
        last_training = {
            "SAFE": (datetime.now() - timedelta(hours=6)).isoformat(),
            "AGGRESSIVE": (datetime.now() - timedelta(hours=12)).isoformat()
        }
        
        return {
            "outcome_tracking": outcome_tracking,
            "models": models,
            "bandit": bandit,
            "last_training": last_training,
            "ml_available": True
        }

    def resolve_riskSummary(self, info):
        # Mock implementation for risk summary
        from datetime import datetime, timedelta
        
        # Create mock risk limits
        risk_limits = {
            "max_position_size": 0.10,  # 10% max position size
            "max_daily_loss": 0.05,     # 5% max daily loss
            "max_concurrent_trades": 5,  # Max 5 concurrent trades
            "max_sector_exposure": 0.30  # 30% max sector exposure
        }
        
        # Create mock sector exposure
        sector_exposure = {
            "Technology": 0.25,
            "Healthcare": 0.15,
            "Financial": 0.20,
            "Energy": 0.10,
            "Consumer": 0.15,
            "Industrial": 0.15
        }
        
        return {
            "account_value": 100000.0,
            "daily_pnl": 1250.0,
            "daily_pnl_pct": 0.0125,  # 1.25%
            "daily_trades": 8,
            "active_positions": 3,
            "total_exposure": 25000.0,
            "exposure_pct": 0.25,  # 25% exposure
            "sector_exposure": sector_exposure,
            "risk_level": "MODERATE",
            "risk_limits": risk_limits
        }

    def resolve_getActivePositions(self, info):
        # Mock implementation for active positions
        from datetime import datetime, timedelta
        
        mock_positions = [
            {
                "symbol": "AAPL",
                "side": "LONG",
                "entry_price": 150.0,
                "quantity": 100,
                "entry_time": (datetime.now() - timedelta(hours=2)).isoformat(),
                "stop_loss_price": 145.0,
                "take_profit_price": 160.0,
                "max_hold_until": (datetime.now() + timedelta(hours=6)).isoformat(),
                "atr_stop_price": 144.5,
                "current_pnl": 500.0,
                "time_remaining_minutes": 240  # 4 hours
            },
            {
                "symbol": "TSLA",
                "side": "SHORT",
                "entry_price": 200.0,
                "quantity": 50,
                "entry_time": (datetime.now() - timedelta(hours=1)).isoformat(),
                "stop_loss_price": 205.0,
                "take_profit_price": 190.0,
                "max_hold_until": (datetime.now() + timedelta(hours=3)).isoformat(),
                "atr_stop_price": 205.5,
                "current_pnl": -250.0,
                "time_remaining_minutes": 120  # 2 hours
            },
            {
                "symbol": "NVDA",
                "side": "LONG",
                "entry_price": 400.0,
                "quantity": 25,
                "entry_time": (datetime.now() - timedelta(minutes=30)).isoformat(),
                "stop_loss_price": 390.0,
                "take_profit_price": 420.0,
                "max_hold_until": (datetime.now() + timedelta(hours=4)).isoformat(),
                "atr_stop_price": 388.0,
                "current_pnl": 125.0,
                "time_remaining_minutes": 210  # 3.5 hours
            }
        ]
        
        return mock_positions

    def resolve_socialFeed(self, info, limit=None, offset=None):
        # Mock implementation for social feed
        from datetime import datetime, timedelta
        
        # Create mock users
        mock_users = [
            {
                "id": "1",
                "name": "John Trader",
                "email": "john@example.com",
                "profilePic": "https://example.com/profile1.jpg",
                "experienceLevel": "Expert"
            },
            {
                "id": "2", 
                "name": "Sarah Investor",
                "email": "sarah@example.com",
                "profilePic": "https://example.com/profile2.jpg",
                "experienceLevel": "Intermediate"
            },
            {
                "id": "3",
                "name": "Mike Analyst",
                "email": "mike@example.com",
                "profilePic": "https://example.com/profile3.jpg",
                "experienceLevel": "Advanced"
            }
        ]
        
        # Create mock portfolios
        mock_portfolios = [
            {
                "id": "1",
                "name": "Growth Portfolio",
                "totalValue": 125000.0,
                "totalReturnPercent": 15.2
            },
            {
                "id": "2",
                "name": "Conservative Portfolio", 
                "totalValue": 85000.0,
                "totalReturnPercent": 8.7
            }
        ]
        
        # Create mock stocks
        mock_stocks = [
            {
                "symbol": "AAPL",
                "companyName": "Apple Inc.",
                "currentPrice": 150.25,
                "changePercent": 2.1
            },
            {
                "symbol": "TSLA",
                "companyName": "Tesla Inc.",
                "currentPrice": 245.80,
                "changePercent": -1.5
            }
        ]
        
        # Create mock comments
        mock_comments = [
            {
                "id": "1",
                "content": "Great analysis! I agree with your assessment.",
                "createdAt": datetime.now() - timedelta(hours=2),
                "user": mock_users[1]
            },
            {
                "id": "2",
                "content": "Thanks for sharing this insight.",
                "createdAt": datetime.now() - timedelta(hours=1),
                "user": mock_users[2]
            }
        ]
        
        # Create mock social feed items
        mock_feed_items = [
            {
                "id": "1",
                "type": "PORTFOLIO_UPDATE",
                "title": "Portfolio Rebalancing Update",
                "content": "Just rebalanced my portfolio with more tech exposure. Feeling bullish on the sector!",
                "createdAt": datetime.now() - timedelta(hours=1),
                "score": 0.85,
                "commentCount": 3,
                "user": mock_users[0],
                "portfolio": mock_portfolios[0],
                "stock": None,
                "likesCount": 12,
                "commentsCount": 3,
                "isLiked": False,
                "comments": mock_comments[:1]
            },
            {
                "id": "2",
                "type": "STOCK_ANALYSIS",
                "title": "AAPL Technical Analysis",
                "content": "AAPL showing strong technical patterns. RSI oversold, potential bounce coming.",
                "createdAt": datetime.now() - timedelta(hours=3),
                "score": 0.92,
                "commentCount": 2,
                "user": mock_users[1],
                "portfolio": None,
                "stock": mock_stocks[0],
                "likesCount": 8,
                "commentsCount": 2,
                "isLiked": True,
                "comments": mock_comments[1:]
            },
            {
                "id": "3",
                "type": "MARKET_COMMENTARY",
                "title": "Market Volatility Insights",
                "content": "Market volatility is creating great opportunities for swing traders. Stay disciplined!",
                "createdAt": datetime.now() - timedelta(hours=5),
                "score": 0.78,
                "commentCount": 5,
                "user": mock_users[2],
                "portfolio": None,
                "stock": None,
                "likesCount": 15,
                "commentsCount": 5,
                "isLiked": False,
                "comments": []
            }
        ]
        
        # Apply limit and offset
        if offset:
            mock_feed_items = mock_feed_items[offset:]
        if limit:
            mock_feed_items = mock_feed_items[:limit]
            
        return mock_feed_items

    def resolve_stockDiscussions(self, info, limit=None, offset=None):
        # Mock implementation for stock discussions - similar to socialFeed but focused on stock-related content
        from datetime import datetime, timedelta
        
        # Create mock users
        mock_users = [
            {
                "id": "1",
                "name": "TraderMike",
                "email": "mike@trader.com",
                "profilePic": "https://example.com/mike.jpg",
                "experienceLevel": "Expert"
            },
            {
                "id": "2", 
                "name": "StockAnalyst",
                "email": "analyst@stocks.com",
                "profilePic": "https://example.com/analyst.jpg",
                "experienceLevel": "Advanced"
            },
            {
                "id": "3",
                "name": "DayTrader",
                "email": "day@trader.com",
                "profilePic": "https://example.com/daytrader.jpg",
                "experienceLevel": "Expert"
            }
        ]
        
        # Create mock stocks
        mock_stocks = [
            {
                "symbol": "AAPL",
                "companyName": "Apple Inc.",
                "currentPrice": 150.25,
                "changePercent": 2.1
            },
            {
                "symbol": "TSLA",
                "companyName": "Tesla Inc.",
                "currentPrice": 245.80,
                "changePercent": -1.5
            },
            {
                "symbol": "NVDA",
                "companyName": "NVIDIA Corporation",
                "currentPrice": 450.20,
                "changePercent": 3.2
            }
        ]
        
        # Create mock comments
        mock_comments = [
            {
                "id": "1",
                "content": "Great analysis! I'm also bullish on this stock.",
                "createdAt": datetime.now() - timedelta(hours=1),
                "user": mock_users[1]
            },
            {
                "id": "2",
                "content": "What's your price target?",
                "createdAt": datetime.now() - timedelta(minutes=30),
                "user": mock_users[2]
            }
        ]
        
        # Create mock stock discussions
        mock_discussions = [
            {
                "id": "1",
                "type": "STOCK_ANALYSIS",
                "title": "AAPL Technical Analysis - Bullish Breakout Pattern",
                "content": "Apple is showing a strong bullish breakout pattern with volume confirmation. The stock has broken above key resistance at $150 and is now targeting $160. RSI is in healthy territory and MACD shows bullish momentum.",
                "createdAt": datetime.now() - timedelta(hours=2),
                "score": 0.92,
                "commentCount": 8,
                "user": mock_users[0],
                "portfolio": None,
                "stock": mock_stocks[0],
                "likesCount": 15,
                "commentsCount": 8,
                "isLiked": False,
                "comments": mock_comments[:1]
            },
            {
                "id": "2",
                "type": "STOCK_ANALYSIS",
                "title": "TSLA Earnings Preview - What to Expect",
                "content": "Tesla's upcoming earnings report is crucial for the stock's direction. With production ramping up and delivery numbers strong, I expect positive guidance. However, margin pressure from price cuts could be a concern.",
                "createdAt": datetime.now() - timedelta(hours=4),
                "score": 0.88,
                "commentCount": 12,
                "user": mock_users[1],
                "portfolio": None,
                "stock": mock_stocks[1],
                "likesCount": 22,
                "commentsCount": 12,
                "isLiked": True,
                "comments": mock_comments[1:]
            },
            {
                "id": "3",
                "type": "STOCK_ANALYSIS",
                "title": "NVDA AI Boom - Still Time to Buy?",
                "content": "NVIDIA continues to benefit from the AI revolution. With data center revenue growing exponentially and new AI chips in development, the stock still has room to run despite recent gains.",
                "createdAt": datetime.now() - timedelta(hours=6),
                "score": 0.85,
                "commentCount": 6,
                "user": mock_users[2],
                "portfolio": None,
                "stock": mock_stocks[2],
                "likesCount": 18,
                "commentsCount": 6,
                "isLiked": False,
                "comments": []
            }
        ]
        
        # Apply limit and offset
        if offset:
            mock_discussions = mock_discussions[offset:]
        if limit:
            mock_discussions = mock_discussions[:limit]
            
        return mock_discussions

    def resolve_feedByTickers(self, info, symbols=None, limit=None):
        # Mock implementation for feed by tickers
        from datetime import datetime, timedelta
        
        # Create mock users
        mock_users = [
            {
                "id": "1",
                "name": "Alex Trader",
                "email": "alex@example.com",
                "profilePic": "https://example.com/alex.jpg",
                "experienceLevel": "Expert"
            },
            {
                "id": "2",
                "name": "Emma Investor",
                "email": "emma@example.com", 
                "profilePic": "https://example.com/emma.jpg",
                "experienceLevel": "Intermediate"
            }
        ]
        
        # Create mock feed items based on symbols
        mock_feed_items = []
        
        if symbols:
            for i, symbol in enumerate(symbols[:5]):  # Limit to 5 symbols
                mock_feed_items.append({
                    "id": f"feed_{i+1}",
                    "kind": "DISCUSSION",
                    "title": f"Analysis: {symbol} Technical Outlook",
                    "content": f"Deep dive into {symbol}'s chart patterns and potential price targets. The stock is showing strong momentum with key resistance levels ahead.",
                    "tickers": [symbol],
                    "score": 0.85 - (i * 0.1),
                    "commentCount": 5 + i,
                    "user": mock_users[i % len(mock_users)],
                    "createdAt": datetime.now() - timedelta(hours=i+1)
                })
        else:
            # Default feed items
            mock_feed_items = [
                {
                    "id": "feed_1",
                    "kind": "DISCUSSION",
                    "title": "Market Analysis: Tech Sector Outlook",
                    "content": "Comprehensive analysis of the technology sector with focus on AI and cloud computing trends.",
                    "tickers": ["AAPL", "MSFT", "GOOGL"],
                    "score": 0.92,
                    "commentCount": 12,
                    "user": mock_users[0],
                    "createdAt": datetime.now() - timedelta(hours=1)
                },
                {
                    "id": "feed_2",
                    "kind": "PREDICTION",
                    "title": "TSLA Price Target Update",
                    "content": "Updated price targets for Tesla based on recent earnings and production data.",
                    "tickers": ["TSLA"],
                    "score": 0.78,
                    "commentCount": 8,
                    "user": mock_users[1],
                    "createdAt": datetime.now() - timedelta(hours=2)
                }
            ]
        
        # Apply limit
        if limit:
            mock_feed_items = mock_feed_items[:limit]
            
        return mock_feed_items

    def resolve_quotes(self, info, symbols=None):
        # Try real market data first, fallback to mock data
        if not symbols:
            symbols = ["AAPL", "TSLA", "MSFT", "GOOGL", "AMZN"]
        
        try:
            from .market_data_service import MarketDataService
            market_service = MarketDataService()
            
            # Get real market data
            real_quotes = market_service.get_quotes(symbols)
            
            if real_quotes and len(real_quotes) > 0:
                print(f"✅ Using REAL market data for {len(real_quotes)} quotes")
                quotes = []
                for quote_data in real_quotes:
                    quote = QuoteType()
                    quote.symbol = quote_data.get('symbol', 'AAPL')
                    quote.last = quote_data.get('price', 100.0)
                    quote.changePct = quote_data.get('changePct', 0.0)
                    quote.price = quote_data.get('price', 100.0)
                    quote.chg = quote_data.get('chg', 0.0)
                    quote.chgPct = quote_data.get('changePct', 0.0)
                    quote.high = quote_data.get('high', quote.last * 1.02)
                    quote.low = quote_data.get('low', quote.last * 0.98)
                    quote.volume = quote_data.get('volume', 1000000)
                    quote.currentPrice = quote_data.get('price', 100.0)
                    quote.change = quote_data.get('chg', 0.0)
                    quotes.append(quote)
                return quotes
            else:
                raise Exception("No real market data available")
                
        except Exception as e:
            print(f"⚠️ Real market data unavailable ({e}), using mock data")
        
        # Mock quote data fallback
        mock_quotes = []
        base_prices = {
            "AAPL": 150.25,
            "TSLA": 245.80,
            "MSFT": 330.15,
            "GOOGL": 2800.50,
            "AMZN": 3200.75,
            "NVDA": 450.20,
            "META": 350.60,
            "NFLX": 420.30
        }
        
        for symbol in symbols:
            base_price = base_prices.get(symbol, 100.0)
            # Add some random variation
            import random
            variation = random.uniform(-0.05, 0.05)  # ±5% variation
            current_price = base_price * (1 + variation)
            change_pct = variation * 100
            change_amount = current_price - base_price
            
            # Create QuoteType object
            quote = QuoteType()
            quote.symbol = symbol
            quote.last = round(current_price, 2)
            quote.changePct = round(change_pct, 2)
            quote.price = round(current_price, 2)
            quote.chg = round(change_amount, 2)
            quote.chgPct = round(change_pct, 2)
            quote.high = round(current_price * 1.02, 2)  # Mock high
            quote.low = round(current_price * 0.98, 2)   # Mock low
            quote.volume = random.randint(1000000, 10000000)  # Mock volume
            quote.currentPrice = round(current_price, 2)
            quote.change = round(change_amount, 2)
            
            mock_quotes.append(quote)
        
        return mock_quotes

    def resolve_myPortfolios(self, info):
        # Mock implementation for my portfolios
        from datetime import datetime, timedelta
        
        # Create mock stock data
        mock_stocks = [
            {
                "id": "1",
                "symbol": "AAPL",
                "companyName": "Apple Inc.",
                "currentPrice": 150.25
            },
            {
                "id": "2", 
                "symbol": "TSLA",
                "companyName": "Tesla Inc.",
                "currentPrice": 245.80
            },
            {
                "id": "3",
                "symbol": "MSFT",
                "companyName": "Microsoft Corporation",
                "currentPrice": 330.15
            }
        ]
        
        # Create mock holdings with the structure expected by mobile app
        mock_holdings = [
            {
                "id": "1",
                "stock": {
                    "id": "1",
                    "symbol": "AAPL",
                    "companyName": "Apple Inc."
                },
                "shares": 100,
                "averagePrice": 145.50,
                "currentPrice": 150.25,
                "totalValue": 15025.0,
                "notes": "Long-term hold",
                "createdAt": datetime.now() - timedelta(days=30),
                "updatedAt": datetime.now() - timedelta(days=1)
            },
            {
                "id": "2",
                "stock": {
                    "id": "2",
                    "symbol": "TSLA",
                    "companyName": "Tesla Inc."
                },
                "shares": 50,
                "averagePrice": 240.00,
                "currentPrice": 245.80,
                "totalValue": 12290.0,
                "notes": "Growth play",
                "createdAt": datetime.now() - timedelta(days=15),
                "updatedAt": datetime.now() - timedelta(days=2)
            },
            {
                "id": "3",
                "stock": {
                    "id": "3",
                    "symbol": "MSFT",
                    "companyName": "Microsoft Corporation"
                },
                "shares": 75,
                "averagePrice": 325.00,
                "currentPrice": 330.15,
                "totalValue": 24761.25,
                "notes": "Tech diversification",
                "createdAt": datetime.now() - timedelta(days=45),
                "updatedAt": datetime.now() - timedelta(days=3)
            }
        ]
        
        # Create mock portfolios
        mock_portfolios = [
            {
                "name": "Growth Portfolio",
                "totalValue": 27315.0,  # AAPL + TSLA
                "holdingsCount": 2,
                "holdings": mock_holdings[:2]
            },
            {
                "name": "Tech Diversification",
                "totalValue": 24761.25,  # MSFT
                "holdingsCount": 1,
                "holdings": mock_holdings[2:]
            }
        ]
        
        # Create properly instantiated PortfolioType objects
        portfolio_objects = []
        for portfolio_data in mock_portfolios:
            portfolio = PortfolioType()
            portfolio.name = portfolio_data["name"]
            portfolio.totalValue = portfolio_data["totalValue"]
            portfolio.holdingsCount = portfolio_data["holdingsCount"]
            
            # Create properly instantiated PortfolioHoldingType objects
            holdings_objects = []
            for holding_data in portfolio_data["holdings"]:
                # Create StockType object
                stock = StockType()
                stock.id = holding_data["stock"]["id"]
                stock.symbol = holding_data["stock"]["symbol"]
                stock.companyName = holding_data["stock"]["companyName"]
                
                # Create MyPortfolioHoldingType object
                holding = MyPortfolioHoldingType()
                holding.id = holding_data["id"]
                holding.stock = stock
                holding.shares = holding_data["shares"]
                holding.averagePrice = holding_data["averagePrice"]
                holding.currentPrice = holding_data["currentPrice"]
                holding.totalValue = holding_data["totalValue"]
                holding.notes = holding_data["notes"]
                holding.createdAt = holding_data["createdAt"]
                holding.updatedAt = holding_data["updatedAt"]
                holdings_objects.append(holding)
            
            portfolio.holdings = holdings_objects
            portfolio_objects.append(portfolio)
        
        return MyPortfoliosType(
            totalPortfolios=2,
            totalValue=52076.25,
            portfolios=portfolio_objects
        )

    def resolve_dayTradingPicks(self, info, mode):
        # Mock implementation for day trading picks
        from datetime import datetime
        
        # Create mock features
        features = {
            "momentum15m": 0.75,
            "rvol10m": 1.2,
            "vwapDist": 0.05,
            "breakoutPct": 0.15,
            "spreadBps": 2.5,
            "catalystScore": 0.8
        }
        
        # Create mock risk
        risk = {
            "atr5m": 1.5,
            "sizeShares": 100,
            "stop": 145.0,
            "targets": [160.0, 170.0],
            "timeStopMin": 30
        }
        
        # Create mock picks
        picks = [
            {
                "symbol": "AAPL",
                "side": "BUY",
                "score": 0.85,
                "features": features,
                "risk": risk,
                "notes": "Strong momentum with breakout potential"
            },
            {
                "symbol": "TSLA",
                "side": "SELL",
                "score": 0.72,
                "features": features,
                "risk": risk,
                "notes": "Overbought conditions, potential reversal"
            }
        ]
        
        return {
            "asOf": datetime.now().isoformat(),
            "mode": mode,
            "picks": picks,
            "universeSize": 500,
            "qualityThreshold": 0.7
        }
    
    def resolve_aiRecommendations(self, info, riskTolerance='medium'):
        """Resolve AI recommendations query"""
        # Mock AI recommendations for now
        recommendations = {
            'low': [
                {'symbol': 'VTI', 'companyName': 'Vanguard Total Stock Market ETF', 'recommendation': 'BUY', 'confidence': 0.85, 'reason': 'Diversified low-risk investment'},
                {'symbol': 'BND', 'companyName': 'Vanguard Total Bond Market ETF', 'recommendation': 'BUY', 'confidence': 0.80, 'reason': 'Stable income generation'},
                {'symbol': 'VXUS', 'companyName': 'Vanguard Total International Stock ETF', 'recommendation': 'BUY', 'confidence': 0.75, 'reason': 'International diversification'}
            ],
            'medium': [
                {'symbol': 'AAPL', 'companyName': 'Apple Inc.', 'recommendation': 'BUY', 'confidence': 0.82, 'reason': 'Strong fundamentals and innovation'},
                {'symbol': 'MSFT', 'companyName': 'Microsoft Corporation', 'recommendation': 'BUY', 'confidence': 0.78, 'reason': 'Cloud computing leadership'},
                {'symbol': 'GOOGL', 'companyName': 'Alphabet Inc.', 'recommendation': 'HOLD', 'confidence': 0.70, 'reason': 'Search dominance but regulatory concerns'}
            ],
            'high': [
                {'symbol': 'TSLA', 'companyName': 'Tesla Inc.', 'recommendation': 'BUY', 'confidence': 0.75, 'reason': 'EV market leadership'},
                {'symbol': 'NVDA', 'companyName': 'NVIDIA Corp', 'recommendation': 'BUY', 'confidence': 0.80, 'reason': 'AI and GPU dominance'},
                {'symbol': 'ARKK', 'companyName': 'ARK Innovation ETF', 'recommendation': 'HOLD', 'confidence': 0.65, 'reason': 'High growth potential but volatile'}
            ]
        }
        
        # Generate mock rebalancing suggestions
        rebalance_suggestions = [
            {
                'action': 'Reduce Technology allocation',
                'currentAllocation': 0.35,
                'suggestedAllocation': 0.25,
                'reasoning': 'Technology sector is over-concentrated, consider diversifying into healthcare',
                'priority': 'High'
            },
            {
                'action': 'Increase Healthcare allocation',
                'currentAllocation': 0.20,
                'suggestedAllocation': 0.30,
                'reasoning': 'Healthcare provides better risk-adjusted returns in current market',
                'priority': 'Medium'
            },
            {
                'action': 'Add International exposure',
                'currentAllocation': 0.0,
                'suggestedAllocation': 0.15,
                'reasoning': 'International diversification reduces portfolio volatility',
                'priority': 'Low'
            }
        ]
        
        # Generate mock risk assessment
        risk_assessment = {
            'overallRisk': 'Medium-High' if riskTolerance == 'high' else 'Medium' if riskTolerance == 'medium' else 'Low',
            'volatilityEstimate': 0.18 if riskTolerance == 'high' else 0.12 if riskTolerance == 'medium' else 0.08,
            'recommendations': [
                'Consider reducing concentration in single sectors',
                'Add defensive positions for market volatility',
                'Regular rebalancing recommended quarterly'
            ]
        }
        
        # Generate mock market outlook
        market_outlook = {
            'overallSentiment': 'Bullish' if riskTolerance == 'high' else 'Neutral' if riskTolerance == 'medium' else 'Cautious',
            'confidence': 0.75 if riskTolerance == 'high' else 0.65 if riskTolerance == 'medium' else 0.55,
            'keyFactors': [
                'Strong corporate earnings growth',
                'Federal Reserve policy support',
                'Technology sector innovation',
                'Global economic recovery trends',
                'Inflation concerns moderating'
            ]
        }
        
        return {
            'portfolioAnalysis': {
                'totalValue': 10000.0,
                'numHoldings': 5,
                'sectorBreakdown': {
                    'Technology': 0.35,
                    'Healthcare': 0.20,
                    'Financial': 0.15,
                    'Consumer': 0.15,
                    'Other': 0.15
                },
                'riskScore': 0.6 if riskTolerance == 'medium' else 0.4 if riskTolerance == 'low' else 0.8,
                'diversificationScore': 0.7,
                'expectedImpact': {
                    'evPct': 0.12 if riskTolerance == 'high' else 0.08 if riskTolerance == 'medium' else 0.05,
                    'evAbs': 1200 if riskTolerance == 'high' else 800 if riskTolerance == 'medium' else 500,
                    'per10k': 1200 if riskTolerance == 'high' else 800 if riskTolerance == 'medium' else 500
                },
                'risk': {
                    'volatilityEstimate': 0.25 if riskTolerance == 'high' else 0.15 if riskTolerance == 'medium' else 0.08,
                    'maxDrawdownPct': 0.30 if riskTolerance == 'high' else 0.20 if riskTolerance == 'medium' else 0.10,
                    'var95': 0.15 if riskTolerance == 'high' else 0.10 if riskTolerance == 'medium' else 0.05,
                    'sharpeRatio': 1.2 if riskTolerance == 'high' else 1.0 if riskTolerance == 'medium' else 0.8
                },
                'assetAllocation': {
                    'stocks': 0.80 if riskTolerance == 'high' else 0.70 if riskTolerance == 'medium' else 0.50,
                    'bonds': 0.15 if riskTolerance == 'high' else 0.25 if riskTolerance == 'medium' else 0.40,
                    'cash': 0.05 if riskTolerance == 'high' else 0.05 if riskTolerance == 'medium' else 0.10,
                    'alternatives': 0.00 if riskTolerance == 'high' else 0.00 if riskTolerance == 'medium' else 0.00
                }
            },
            'buyRecommendations': [
                {
                    'symbol': rec['symbol'],
                    'companyName': rec['companyName'],
                    'recommendation': rec['recommendation'],
                    'confidence': rec['confidence'],
                    'reasoning': rec['reason'],
                    'targetPrice': 200.0,  # Mock data
                    'currentPrice': 180.0,  # Mock data
                    'expectedReturn': 0.11,  # Mock data
                    'allocation': 0.05  # Mock data - 5% allocation
                }
                for rec in recommendations.get(riskTolerance, recommendations['medium'])
                if rec['recommendation'] in ['BUY', 'STRONG_BUY']
            ],
            'sellRecommendations': [
                {
                    'symbol': rec['symbol'],
                    'companyName': rec['companyName'],
                    'recommendation': rec['recommendation'],
                    'confidence': rec['confidence'],
                    'reasoning': rec['reason'],
                    'targetPrice': 150.0,  # Mock data
                    'currentPrice': 180.0,  # Mock data
                    'expectedReturn': -0.17,  # Mock data
                    'allocation': 0.0  # Mock data - 0% allocation for sell recommendations
                }
                for rec in recommendations.get(riskTolerance, recommendations['medium'])
                if rec['recommendation'] in ['SELL', 'STRONG_SELL']
            ],
            'rebalanceSuggestions': rebalance_suggestions,
            'riskAssessment': risk_assessment,
            'marketOutlook': market_outlook,
            'marketInsights': {
                'sectorAllocation': {
                    'Technology': 0.35,
                    'Healthcare': 0.20,
                    'Financial': 0.15,
                    'Consumer': 0.15,
                    'Other': 0.15
                },
                'riskAssessment': 'Moderate risk portfolio with growth potential'
            }
        }

class Mutation(SblocMutation, NotificationMutation, graphene.ObjectType):
    token_auth = ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    runBacktest = RunBacktestMutation.Field()
    
    # SBLOC mutations
    create_sbloc_session = SblocMutation.create_sbloc_session
    
    # Income profile mutations
    createIncomeProfile = graphene.Field(
        CreateIncomeProfileResult,
        incomeBracket=graphene.String(required=True),
        age=graphene.Int(required=True),
        riskTolerance=graphene.String(required=True),
        investmentHorizon=graphene.String(required=True),
        investmentGoals=graphene.List(graphene.String),
        description="Create or update user's income profile"
    )
    
    # AI recommendations mutations
    generateAiRecommendations = graphene.Field(
        GenerateAIRecommendationsResult,
        description="Generate AI portfolio recommendations based on user's income profile"
    )
    
    # Risk Management Mutations
    createPosition = graphene.Field(
        CreatePositionResultType,
        symbol=graphene.String(required=True),
        side=graphene.String(required=True),
        price=graphene.Float(required=True),
        quantity=graphene.Int(),
        atr=graphene.Float(required=True),
        sector=graphene.String(),
        confidence=graphene.Float(),
        description="Create a new trading position"
    )

    checkPositionExits = graphene.Field(
        CheckExitsResultType,
        currentPrices=graphene.JSONString(),
        description="Check for position exits based on current prices"
    )

    updateRiskSettings = graphene.Field(
        UpdateRiskSettingsResultType,
        accountValue=graphene.Float(),
        riskLevel=graphene.String(),
        description="Update risk management settings"
    )
    
    # Signal mutations
    likeSignal = graphene.Field(
        graphene.NonNull(graphene.Boolean),
        signalId=graphene.ID(required=True),
        description="Like or unlike a signal"
    )
    
    commentSignal = graphene.Field(
        graphene.NonNull(graphene.Boolean),
        signalId=graphene.ID(required=True),
        content=graphene.String(required=True),
        description="Add a comment to a signal"
    )
    
    # Option Order Mutations
    placeOptionOrder = graphene.Field(
        graphene.NonNull(graphene.Boolean),
        symbol=graphene.String(required=True),
        optionType=graphene.String(required=True),
        strike=graphene.Float(required=True),
        expiration=graphene.String(required=True),
        side=graphene.String(required=True),
        quantity=graphene.Int(required=True),
        orderType=graphene.String(required=True),
        limitPrice=graphene.Float(),
        timeInForce=graphene.String(required=True),
        description="Place an option order"
    )
    
    cancelOptionOrder = graphene.Field(
        graphene.NonNull(graphene.Boolean),
        orderId=graphene.String(required=True),
        description="Cancel an option order"
    )
    
    # Bank Account Mutations
    linkBankAccount = graphene.Field(
        LinkBankAccountResultType,
        bankName=graphene.String(required=True),
        accountNumber=graphene.String(required=True),
        routingNumber=graphene.String(required=True),
        description="Link a bank account (mock implementation)"
    )
    
    initiateFunding = graphene.Field(
        InitiateFundingResultType,
        amount=graphene.Float(required=True),
        bankAccountId=graphene.String(required=True),
        description="Initiate funding from bank account (mock implementation)"
    )
    
    def resolve_likeSignal(self, info, signalId):
        # Mock implementation - always return success
        return True
    
    def resolve_commentSignal(self, info, signalId, content):
        # Mock implementation - always return success
        return True
    
    def resolve_linkBankAccount(self, info, bankName, accountNumber, routingNumber):
        # Mock implementation for bank account linking
        # In production, this would integrate with Plaid, Yodlee, or direct bank APIs
        
        # Basic validation
        if not bankName or not accountNumber or not routingNumber:
            return LinkBankAccountResultType(
                success=False,
                message="All fields are required",
                bankAccount=None
            )
        
        # Mock validation - check routing number format (9 digits)
        if len(routingNumber) != 9 or not routingNumber.isdigit():
            return LinkBankAccountResultType(
                success=False,
                message="Invalid routing number format",
                bankAccount=None
            )
        
        # Mock account number validation (4-17 digits)
        if len(accountNumber) < 4 or len(accountNumber) > 17 or not accountNumber.isdigit():
            return LinkBankAccountResultType(
                success=False,
                message="Invalid account number format",
                bankAccount=None
            )
        
        # Mock successful linking
        import uuid
        from datetime import datetime
        
        new_bank_account = BankAccountType(
            id=str(uuid.uuid4()),
            bankName=bankName,
            accountType="Checking",  # Default to checking
            lastFour=accountNumber[-4:],  # Last 4 digits
            isVerified=True,  # Mock as verified
            isPrimary=False,  # Not primary by default
            linkedAt=datetime.now().isoformat() + "Z"
        )
        
        return LinkBankAccountResultType(
            success=True,
            message="Bank account linked successfully",
            bankAccount=new_bank_account
        )
    
    def resolve_initiateFunding(self, info, amount, bankAccountId):
        # Mock implementation for funding initiation
        # In production, this would integrate with ACH/wire transfer services
        
        # Basic validation
        if amount <= 0:
            return InitiateFundingResultType(
                success=False,
                message="Amount must be greater than 0",
                funding=None
            )
        
        if amount < 1.0:
            return InitiateFundingResultType(
                success=False,
                message="Minimum funding amount is $1.00",
                funding=None
            )
        
        if amount > 100000.0:
            return InitiateFundingResultType(
                success=False,
                message="Maximum funding amount is $100,000.00",
                funding=None
            )
        
        # Mock successful funding initiation
        import uuid
        from datetime import datetime, timedelta
        
        # Mock funding transaction
        funding_transaction = FundingHistoryType(
            id=str(uuid.uuid4()),
            amount=amount,
            status="pending",  # Mock as pending
            bankAccountId=bankAccountId,
            initiatedAt=datetime.now().isoformat() + "Z",
            completedAt=None  # Will be completed later
        )
        
        return InitiateFundingResultType(
            success=True,
            message=f"Funding of ${amount:,.2f} initiated successfully. Expected completion: 1-3 business days.",
            funding=funding_transaction
        )
    
    def resolve_createIncomeProfile(self, info, incomeBracket, age, riskTolerance, investmentHorizon, investmentGoals=None):
        # Mock implementation - always return success
        # In a real implementation, this would save the income profile to the database
        return CreateIncomeProfileResult(
            success=True,
            message="Income profile created successfully"
        )
    
        def resolve_generateAiRecommendations(self, info):
            print("DEBUG: generateAiRecommendations mutation called - USING REAL AI")
            # Check if user is authenticated
            user = info.context.user
            print(f"DEBUG: User: {user}, Authenticated: {user.is_authenticated if user else 'No user'}")
            
            # For development, let's create a mock user if none exists
            if not user or not user.is_authenticated:
                print("DEBUG: No authenticated user, creating mock user for development")
                # Create a mock user object for development
                class MockUser:
                    def __init__(self):
                        self.id = 1
                        self.is_authenticated = True
                        self.email = "test@example.com"
                        self.username = "dev"
                user = MockUser()
            
            # Get user profile data
            user_profile = {}
            try:
                # Try to get the income profile
                income_profile = getattr(user, 'incomeprofile', None)
                if income_profile:
                    user_profile = {
                        'age': getattr(income_profile, 'age', 30),
                        'income_bracket': getattr(income_profile, 'income_bracket', 'Unknown'),
                        'investment_horizon': getattr(income_profile, 'investment_horizon', '5-10 years'),
                        'risk_tolerance': getattr(income_profile, 'risk_tolerance', 'Moderate'),
                        'investment_goals': getattr(income_profile, 'investment_goals', ['Wealth Building'])
                    }
                    print(f"DEBUG: Using real user profile: {user_profile}")
                else:
                    print("DEBUG: No income profile found, using default profile")
                    user_profile = {
                        'age': 30,
                        'income_bracket': 'Unknown',
                        'investment_horizon': '5-10 years',
                        'risk_tolerance': 'Moderate',
                        'investment_goals': ['Wealth Building']
                    }
            except Exception as e:
                print(f"DEBUG: Profile error: {e}, using default profile")
                user_profile = {
                    'age': 30,
                    'income_bracket': 'Unknown',
                    'investment_horizon': '5-10 years',
                    'risk_tolerance': 'Moderate',
                    'investment_goals': ['Wealth Building']
                }
        
        # Generate REAL AI recommendations using OpenAI (Production-Safe Implementation)
        try:
            from openai import OpenAI
            from django.conf import settings
            import json
            
            if settings.OPENAI_API_KEY:
                print("DEBUG: Using OpenAI API for real AI recommendations")
                
                # Production-safe OpenAI integration
                client = OpenAI(api_key=settings.OPENAI_API_KEY)
                
                SYSTEM_PROMPT = (
                    "You are a professional financial advisor. "
                    "Return strict JSON only. No prose, no markdown."
                )
                
                def build_prompt(user_profile: dict) -> str:
                    return f"""
Create 3 personalized investment portfolio recommendations for:
Age: {user_profile.get('age')}
Income: {user_profile.get('income_bracket')}
Risk Tolerance: {user_profile.get('risk_tolerance')}
Goals: {', '.join(user_profile.get('investment_goals', []))}
Investment Horizon: {user_profile.get('investment_horizon')}

Return a JSON array with 3 items. Each item must have:
- "riskProfile": "Conservative" | "Moderate" | "Aggressive"
- "portfolioAllocation": string (e.g., "60% Stocks, 30% Bonds, 10% Cash")
- "recommendedStocks": string[] (tickers like ["VTI","BND","QQQ"])
- "expectedPortfolioReturn": number (decimal, e.g., 0.08)
- "riskAssessment": string
"""
                
                def parse_or_fallback(text: str, fallback_data: list) -> list:
                    try:
                        data = json.loads(text)
                        if isinstance(data, list) and len(data) >= 1:
                            return data
                    except Exception:
                        pass
                    return fallback_data
                
                def fallback_recommendations(user_profile: dict) -> list:
                    return [
                        {
                            "riskProfile": "Moderate",
                            "portfolioAllocation": "60% Stocks, 30% Bonds, 10% Cash",
                            "recommendedStocks": ["VTI", "VXUS", "BND"],
                            "expectedPortfolioReturn": 0.07,
                            "riskAssessment": "Diversified core allocation with moderate volatility."
                        },
                        {
                            "riskProfile": "Conservative",
                            "portfolioAllocation": "40% Stocks, 50% Bonds, 10% Cash",
                            "recommendedStocks": ["VTV", "BND", "SHY"],
                            "expectedPortfolioReturn": 0.05,
                            "riskAssessment": "Lower volatility focus with income tilt."
                        },
                        {
                            "riskProfile": "Aggressive",
                            "portfolioAllocation": "80% Stocks, 15% Bonds, 5% Cash",
                            "recommendedStocks": ["QQQ", "VTI", "IWM"],
                            "expectedPortfolioReturn": 0.10,
                            "riskAssessment": "Higher growth potential with higher drawdown risk."
                        },
                    ]
                
                # Check if OpenAI is enabled
                if not settings.USE_OPENAI:
                    print("DEBUG: OpenAI disabled via USE_OPENAI flag, using fallback recommendations")
                    raise Exception("OpenAI disabled")
                
                # Generate AI recommendations with smart model fallback
                prompt = build_prompt(user_profile)
                
                # Try models in order of preference
                models_to_try = [settings.OPENAI_MODEL, "gpt-4o-mini", "gpt-3.5-turbo"]
                
                try:
                    for model in models_to_try:
                        try:
                            print(f"DEBUG: Trying model: {model}")
                            # Use the new Responses API with timeout
                            res = client.chat.completions.create(
                                model=model,
                                messages=[
                                    {"role": "system", "content": SYSTEM_PROMPT},
                                    {"role": "user", "content": prompt},
                                ],
                                temperature=0.6,
                                max_tokens=settings.OPENAI_MAX_TOKENS,
                                timeout=settings.OPENAI_TIMEOUT_MS / 1000,  # Convert to seconds
                            )
                            print(f"DEBUG: Successfully used model: {model}")
                            break  # Success, exit the loop
                        except Exception as model_error:
                            print(f"DEBUG: Model {model} failed: {model_error}")
                            if model == models_to_try[-1]:  # Last model failed
                                raise model_error  # Re-raise the last error
                            continue  # Try next model
                    
                    # If we get here, one of the models worked
                    text = res.choices[0].message.content
                    data = parse_or_fallback(text, fallback_recommendations(user_profile))
                    
                    # Convert to GraphQL format
                    recommendations = []
                    for i, rec in enumerate(data):
                        recommendations.append(AIRecommendationType(
                            id=str(i + 1),
                            riskProfile=rec.get('riskProfile', 'Moderate'),
                            portfolioAllocation=rec.get('portfolioAllocation', '60% Stocks, 30% Bonds, 10% Cash'),
                            recommendedStocks=rec.get('recommendedStocks', ['VTI', 'BND', 'VXUS']),
                            expectedPortfolioReturn=float(rec.get('expectedPortfolioReturn', 0.08)),
                            riskAssessment=rec.get('riskAssessment', 'Moderate risk with balanced growth potential')
                        ))
                    
                    print("DEBUG: Successfully generated real AI recommendations")
                    return GenerateAIRecommendationsResult(
                        success=True,
                        message="AI recommendations generated successfully using OpenAI",
                        recommendations=recommendations
                    )
                
                except Exception as e:
                    msg = str(e).lower()
                    quota_like = any(k in msg for k in ["insufficient_quota", "billing", "rate limit", "exceeded"])
                    timeout_like = any(k in msg for k in ["timeout", "timed out", "connection"])
                    
                    if not settings.OPENAI_ENABLE_FALLBACK:
                        print(f"DEBUG: OpenAI error and fallback disabled: {e}")
                        raise e
                    
                    if quota_like:
                        print(f"DEBUG: OpenAI quota/limit error: {e}, using fallback recommendations")
                    elif timeout_like:
                        print(f"DEBUG: OpenAI timeout error: {e}, using fallback recommendations")
                    else:
                        print(f"DEBUG: OpenAI error: {e}, using fallback recommendations")
                    
                    # Use fallback data
                    fallback_data = fallback_recommendations(user_profile)
                    recommendations = []
                    for i, rec in enumerate(fallback_data):
                        recommendations.append(AIRecommendationType(
                            id=str(i + 1),
                            riskProfile=rec.get('riskProfile', 'Moderate'),
                            portfolioAllocation=rec.get('portfolioAllocation', '60% Stocks, 30% Bonds, 10% Cash'),
                            recommendedStocks=rec.get('recommendedStocks', ['VTI', 'BND', 'VXUS']),
                            expectedPortfolioReturn=float(rec.get('expectedPortfolioReturn', 0.08)),
                            riskAssessment=rec.get('riskAssessment', 'Moderate risk with balanced growth potential')
                        ))
                    
                    return GenerateAIRecommendationsResult(
                        success=True,
                        message="AI recommendations generated successfully (fallback mode)",
                        recommendations=recommendations
                    )
            else:
                print("DEBUG: No OpenAI API key, using fallback recommendations")
        except Exception as e:
            print(f"DEBUG: OpenAI setup error: {e}, using fallback recommendations")
        
        # Fallback to smart mock recommendations based on user profile
        risk_tolerance = user_profile.get('risk_tolerance', 'Moderate').lower()
        age = user_profile.get('age', 30)
        
        if 'conservative' in risk_tolerance or age > 50:
            recommendations = [
                AIRecommendationType(
                    id="1",
                    riskProfile="Conservative",
                    portfolioAllocation="40% Stocks, 50% Bonds, 10% Cash",
                    recommendedStocks=["VTI", "BND", "VXUS", "GLD"],
                    expectedPortfolioReturn=0.06,
                    riskAssessment="Conservative approach with stable returns and lower volatility"
                ),
                AIRecommendationType(
                    id="2",
                    riskProfile="Moderate",
                    portfolioAllocation="60% Stocks, 30% Bonds, 10% Cash",
                    recommendedStocks=["VTI", "BND", "VXUS", "QQQ"],
                    expectedPortfolioReturn=0.08,
                    riskAssessment="Balanced approach with moderate risk and steady growth"
                )
            ]
        elif 'aggressive' in risk_tolerance or age < 30:
            recommendations = [
                AIRecommendationType(
                    id="1",
                    riskProfile="Aggressive",
                    portfolioAllocation="80% Stocks, 15% Bonds, 5% Cash",
                    recommendedStocks=["QQQ", "VTI", "ARKK", "TSLA", "NVDA"],
                    expectedPortfolioReturn=0.12,
                    riskAssessment="High growth potential with increased volatility and risk"
                ),
                AIRecommendationType(
                    id="2",
                    riskProfile="Moderate",
                    portfolioAllocation="60% Stocks, 30% Bonds, 10% Cash",
                    recommendedStocks=["VTI", "BND", "VXUS", "QQQ"],
                    expectedPortfolioReturn=0.08,
                    riskAssessment="Balanced approach with moderate risk and steady growth"
                )
            ]
        else:  # Moderate
            recommendations = [
                AIRecommendationType(
                    id="1",
                    riskProfile="Moderate",
                    portfolioAllocation="60% Stocks, 30% Bonds, 10% Cash",
                    recommendedStocks=["VTI", "BND", "VXUS", "QQQ"],
                    expectedPortfolioReturn=0.08,
                    riskAssessment="Balanced approach with moderate risk and steady growth potential"
                ),
                AIRecommendationType(
                    id="2",
                    riskProfile="Conservative",
                    portfolioAllocation="40% Stocks, 50% Bonds, 10% Cash",
                    recommendedStocks=["VTI", "BND", "VXUS", "GLD"],
                    expectedPortfolioReturn=0.06,
                    riskAssessment="Conservative approach with stable returns"
                )
            ]
        
            print("DEBUG: Returning fallback AI recommendations")
            return GenerateAIRecommendationsResult(
                success=True,
                message="AI recommendations generated successfully (fallback mode)",
                recommendations=recommendations
            )


    def resolve_createPosition(self, info, symbol, side, price, atr, quantity=None, sector=None, confidence=None):
        # Mock implementation for creating a position
        from datetime import datetime, timedelta
        
        # Calculate stop loss and take profit based on ATR
        if side.upper() == "LONG":
            stop_loss_price = price - (atr * 2)
            take_profit_price = price + (atr * 3)
        else:  # SHORT
            stop_loss_price = price + (atr * 2)
            take_profit_price = price - (atr * 3)
        
        # Create mock position
        position = {
            "symbol": symbol,
            "side": side.upper(),
            "entry_price": price,
            "quantity": quantity or 100,
            "entry_time": datetime.now().isoformat(),
            "stop_loss_price": stop_loss_price,
            "take_profit_price": take_profit_price,
            "max_hold_until": (datetime.now() + timedelta(hours=4)).isoformat(),
            "atr_stop_price": stop_loss_price - (atr * 0.5) if side.upper() == "LONG" else stop_loss_price + (atr * 0.5)
        }
        
        return {
            "success": True,
            "message": f"Position created successfully for {symbol}",
            "position": position
        }

    def resolve_checkPositionExits(self, info, currentPrices=None):
        # Mock implementation for checking position exits
        from datetime import datetime
        
        # Mock exited positions
        exited_positions = [
            {
                "symbol": "MSFT",
                "side": "LONG",
                "entry_price": 300.0,
                "exit_price": 315.0,
                "quantity": 50,
                "pnl": 750.0,
                "exit_reason": "Take profit hit",
                "exit_time": datetime.now().isoformat()
            }
        ]
        
        return {
            "success": True,
            "message": "Position exit check completed",
            "exited_positions": exited_positions
        }

    def resolve_updateRiskSettings(self, info, accountValue=None, riskLevel=None):
        # Mock implementation for updating risk settings
        # Return updated risk summary
        risk_limits = {
            "max_position_size": 0.10,
            "max_daily_loss": 0.05,
            "max_concurrent_trades": 5,
            "max_sector_exposure": 0.30
        }
        
        sector_exposure = {
            "Technology": 0.25,
            "Healthcare": 0.15,
            "Financial": 0.20,
            "Energy": 0.10,
            "Consumer": 0.15,
            "Industrial": 0.15
        }
        
        current_settings = {
            "account_value": accountValue or 100000.0,
            "daily_pnl": 1250.0,
            "daily_pnl_pct": 0.0125,
            "daily_trades": 8,
            "active_positions": 3,
            "total_exposure": 25000.0,
            "exposure_pct": 0.25,
            "sector_exposure": sector_exposure,
            "risk_level": riskLevel or "MODERATE",
            "risk_limits": risk_limits
        }
        
        return {
            "success": True,
            "message": "Risk settings updated successfully",
            "current_settings": current_settings
        }
    
    def resolve_placeOptionOrder(self, info, symbol, optionType, strike, expiration, side, quantity, orderType, timeInForce, limitPrice=None):
        # Mock implementation for placing option orders
        # In a real implementation, this would validate the order and place it with a broker
        return True
    
    def resolve_cancelOptionOrder(self, info, orderId):
        # Mock implementation for canceling option orders
        # In a real implementation, this would cancel the order with the broker
        return True
    
    
    
    
    # Include crypto mutations
    crypto = graphene.Field(CryptoMutation)
    
    def resolve_crypto(self, info):
        # Return a CryptoMutation instance to access its fields
        return CryptoMutation()

# Subscription Types
class TickerPostType(graphene.ObjectType):
    id = graphene.ID()
    kind = graphene.String()
    title = graphene.String()
    tickers = graphene.List(graphene.String)
    user = graphene.Field(lambda: UserType)
    createdAt = graphene.DateTime()

class Subscription(graphene.ObjectType):
    # Day Trading Updates Subscription
    dayTradingUpdates = graphene.Field(
        'core.graphql.types.DayTradingPicksType',
        mode=graphene.String(required=True)
    )
    
    # Ticker Post Created Subscription
    tickerPostCreated = graphene.Field(
        TickerPostType,
        symbols=graphene.List(graphene.String)
    )

    def resolve_dayTradingUpdates(self, info, mode):
        # Mock implementation for day trading updates subscription
        # In a real implementation, this would use WebSocket or Server-Sent Events
        from datetime import datetime
        
        # Create mock features
        features = {
            "momentum15m": 0.75,
            "rvol10m": 1.2,
            "vwapDist": 0.05,
            "breakoutPct": 0.15,
            "spreadBps": 2.5,
            "catalystScore": 0.8
        }
        
        # Create mock risk
        risk = {
            "atr5m": 1.5,
            "sizeShares": 100,
            "stop": 145.0,
            "targets": [160.0, 170.0],
            "timeStopMin": 30
        }
        
        # Create mock picks
        picks = [
            {
                "symbol": "AAPL",
                "side": "BUY",
                "score": 0.85,
                "features": features,
                "risk": risk,
                "notes": "Strong momentum with breakout potential"
            },
            {
                "symbol": "TSLA",
                "side": "SELL",
                "score": 0.72,
                "features": features,
                "risk": risk,
                "notes": "Overbought conditions, potential reversal"
            }
        ]
        
        return {
            "asOf": datetime.now().isoformat(),
            "mode": mode,
            "picks": picks,
            "universeSize": 500,
            "qualityThreshold": 0.7
        }

    def resolve_tickerPostCreated(self, info, symbols=None):
        # Mock implementation for ticker post created subscription
        # In a real implementation, this would use WebSocket or Server-Sent Events
        from datetime import datetime
        
        return {
            "id": "1",
            "kind": "DISCUSSION",
            "title": "Market Analysis Update",
            "tickers": symbols or ["AAPL", "TSLA"],
            "user": {
                "id": "1",
                "name": "Test User"
            },
            "createdAt": datetime.now()
        }

schema = graphene.Schema(query=Query, mutation=Mutation, subscription=Subscription, auto_camelcase=True)