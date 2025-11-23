# core/types.py
import graphene
from graphene_django import DjangoObjectType
from .models import User, Post, ChatSession, ChatMessage, Source, Like, Comment, Follow, Stock, StockData, Watchlist, IncomeProfile, AIPortfolioRecommendation, Portfolio, StockDiscussion, DiscussionComment, StockMoment, MomentCategory


class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ("id", "email", "name", "profile_pic")

    # Add camelCase fields for frontend compatibility
    profilePic = graphene.String()  # camelCase field
    # Add income profile field - snake_case in Python, camelCase in GraphQL
    income_profile = graphene.Field('core.types.IncomeProfileType')

    def resolve_income_profile(self, info):
        """
        Resolve incomeProfile field for UserType.
        Returns the most recent IncomeProfile for this user, or None if none exists.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            user_id = getattr(self, 'id', 'unknown')
            user_email = getattr(self, 'email', 'unknown')
            
            logger.info(f"[UserType.resolve_incomeProfile] Resolving for user={user_id} email={user_email}")
            
            # Use filter().latest() to get the most recent profile (handles multiple profiles gracefully)
            # Since it's a OneToOneField, there should only be one, but this is safer
            from .models import IncomeProfile
            try:
                profile = IncomeProfile.objects.filter(user=self).latest('id')
                logger.info(f"[UserType.resolve_incomeProfile] Found profile id={profile.id} for user {user_id}")
                return profile
            except IncomeProfile.DoesNotExist:
                logger.info(f"[UserType.resolve_incomeProfile] No profile found for user {user_id}")
                return None
        except Exception as e:
            logger.exception(f"[UserType.resolve_incomeProfile] Error resolving incomeProfile for user {getattr(self, 'email', 'unknown')}: {e}")
            return None

    # Resolver for camelCase field
    def resolve_profilePic(self, info):
        return self.profile_pic

    # Add computed fields that the frontend expects
    followers_count = graphene.Int()
    following_count = graphene.Int()
    is_following_user = graphene.Boolean()
    is_followed_by_user = graphene.Boolean()
    # Add camelCase aliases for frontend compatibility
    followersCount = graphene.Int()
    followingCount = graphene.Int()
    isFollowingUser = graphene.Boolean()
    isFollowedByUser = graphene.Boolean()
    # Add subscription status fields
    hasPremiumAccess = graphene.Boolean()
    subscriptionTier = graphene.String()

    def resolve_followers_count(self, info):
        return self.followers.count()

    def resolve_following_count(self, info):
        return self.following.count()

    def resolve_is_following_user(self, info):
        user = info.context.user
        if user.is_anonymous:
            return False
        return user.is_following(self)

    def resolve_is_followed_by_user(self, info):
        user = info.context.user
        if user.is_anonymous:
            return False
        return user.is_followed_by(self)

    # Resolvers for camelCase aliases
    def resolve_followersCount(self, info):
        return self.followers.count()

    def resolve_followingCount(self, info):
        return self.following.count()

    def resolve_isFollowingUser(self, info):
        user = info.context.user
        if user.is_anonymous:
            return False
        return user.is_following(self)

    def resolve_isFollowedByUser(self, info):
        user = info.context.user
        if user.is_anonymous:
            return False
        return user.is_followed_by(self)

    def resolve_hasPremiumAccess(self, info):
        """Check if user has premium access"""
        from .premium_types import _has_premium_access
        return _has_premium_access(self)

    def resolve_subscriptionTier(self, info):
        """Get user's subscription tier"""
        from .premium_types import _has_premium_access
        if _has_premium_access(self):
            return "premium"
        return "free"


class IncomeProfileType(DjangoObjectType):
    class Meta:
        model = IncomeProfile
        fields = (
            "id",
            "income_bracket",
            "age",
            "investment_goals",
            "risk_tolerance",
            "investment_horizon",
            "created_at",
            "updated_at")

    # Add camelCase fields for frontend compatibility
    incomeBracket = graphene.String()
    investmentGoals = graphene.List(graphene.String)
    riskTolerance = graphene.String()
    investmentHorizon = graphene.String()
    createdAt = graphene.DateTime()
    updatedAt = graphene.DateTime()

    def resolve_incomeBracket(self, info):
        return self.income_bracket

    def resolve_investmentGoals(self, info):
        return self.investment_goals

    def resolve_riskTolerance(self, info):
        return self.risk_tolerance

    def resolve_investmentHorizon(self, info):
        return self.investment_horizon

    def resolve_createdAt(self, info):
        return self.created_at

    def resolve_updatedAt(self, info):
        return self.updated_at


class ProfileInput(graphene.InputObjectType):
    """Profile input for AI recommendations"""
    age = graphene.Int(required=False)
    incomeBracket = graphene.String(required=False)
    investmentGoals = graphene.List(graphene.String, required=False)
    investmentHorizonYears = graphene.Int(required=False)
    riskTolerance = graphene.String(required=False)


class StockRecommendationType(graphene.ObjectType):
    """Individual stock recommendation within a portfolio"""
    symbol = graphene.String()
    companyName = graphene.String()
    allocation = graphene.Float()
    reasoning = graphene.String()
    riskLevel = graphene.String()
    expectedReturn = graphene.Float()


class AIRecommendationsType(graphene.ObjectType):
    """Simplified AI recommendations response matching frontend expectations"""
    buyRecsCount = graphene.Int()
    usingDefaults = graphene.Boolean()
    recommendations = graphene.List('core.types.AIPortfolioRecommendationType')


class AIPortfolioRecommendationType(DjangoObjectType):
    class Meta:
        model = AIPortfolioRecommendation
        fields = (
            "id",
            "risk_profile",
            "portfolio_allocation",
            "recommended_stocks",
            "expected_portfolio_return",
            "risk_assessment",
            "created_at",
            "updated_at")
    
    # Add camelCase fields for frontend compatibility
    riskProfile = graphene.String()
    portfolioAllocation = graphene.JSONString()
    recommendedStocks = graphene.List(StockRecommendationType)
    expectedPortfolioReturn = graphene.Float()
    riskAssessment = graphene.String()
    createdAt = graphene.DateTime()
    updatedAt = graphene.DateTime()
    
    def resolve_riskProfile(self, info):
        return self.risk_profile
    
    def resolve_portfolioAllocation(self, info):
        return self.portfolio_allocation
    
    def resolve_recommendedStocks(self, info):
        # Convert JSON data to StockRecommendationType objects
        stocks_data = self.recommended_stocks or []
        return [
            StockRecommendationType(
                symbol=stock.get('symbol', ''),
                companyName=stock.get('companyName', ''),
                allocation=stock.get('allocation', 0.0),
                reasoning=stock.get('reasoning', ''),
                riskLevel=stock.get('riskLevel', ''),
                expectedReturn=stock.get('expectedReturn', 0.0)
            )
            for stock in stocks_data
        ]
    
    def resolve_expectedPortfolioReturn(self, info):
        if not self.expected_portfolio_return:
            return None
        try:
            return float(self.expected_portfolio_return)
        except (ValueError, TypeError):
            return None
    
    def resolve_riskAssessment(self, info):
        return self.risk_assessment
    
    def resolve_createdAt(self, info):
        return self.created_at
    
    def resolve_updatedAt(self, info):
        return self.updated_at


class TechnicalIndicatorsType(graphene.ObjectType):
    """Technical indicators for stock analysis"""
    rsi = graphene.Float()
    macd = graphene.Float()
    macdSignal = graphene.Float()
    macdHistogram = graphene.Float()
    sma20 = graphene.Float()
    sma50 = graphene.Float()
    ema12 = graphene.Float()
    ema26 = graphene.Float()
    bollingerUpper = graphene.Float()
    bollingerLower = graphene.Float()
    bollingerMiddle = graphene.Float()
class FundamentalAnalysisType(graphene.ObjectType):


    """Fundamental analysis scores"""
    valuationScore = graphene.Float()
    growthScore = graphene.Float()
    stabilityScore = graphene.Float()
    dividendScore = graphene.Float()
    debtScore = graphene.Float()
class SpendingDataPointType(graphene.ObjectType):
    """Spending data point for consumer spending surge chart"""
    date = graphene.String()
    spending = graphene.Float()
    spendingChange = graphene.Float()
    price = graphene.Float()
    priceChange = graphene.Float()


class OptionsFlowDataPointType(graphene.ObjectType):
    """Options flow data point for smart money flow chart"""
    date = graphene.String()
    price = graphene.Float()
    unusualVolumePercent = graphene.Float()
    sweepCount = graphene.Int()
    putCallRatio = graphene.Float()


class SignalContributionType(graphene.ObjectType):
    """Signal contribution for feature importance"""
    name = graphene.String()
    contribution = graphene.Float()
    color = graphene.String()
    description = graphene.String()


class SHAPValueType(graphene.ObjectType):
    """SHAP value for explainability"""
    feature = graphene.String()
    value = graphene.Float()
    importance = graphene.Float()


class RustStockAnalysisType(graphene.ObjectType):


    """Rust engine stock analysis"""
    symbol = graphene.String()
    beginnerFriendlyScore = graphene.Float()
    riskLevel = graphene.String()
    recommendation = graphene.String()
    technicalIndicators = graphene.Field(TechnicalIndicatorsType)
    fundamentalAnalysis = graphene.Field(FundamentalAnalysisType)
    reasoning = graphene.List(graphene.String)
    # Week 3: Chart data fields
    spendingData = graphene.List(SpendingDataPointType)
    optionsFlowData = graphene.List(OptionsFlowDataPointType)
    signalContributions = graphene.List(SignalContributionType)
    shapValues = graphene.List(SHAPValueType)
    shapExplanation = graphene.String()


class PostType(DjangoObjectType):
    class Meta:
        model = Post
        fields = ("id", "user", "content", "image", "created_at", "likes", "comments")


class ChatSessionType(DjangoObjectType):
    class Meta:
        model = ChatSession
        fields = ("id", "user", "created_at", "messages")


class ChatMessageType(DjangoObjectType):
    class Meta:


        model = ChatMessage
        fields = ("id", "session", "role", "content", "created_at")
class SourceType(DjangoObjectType):
    class Meta:


        model = Source
        fields = ("id", "url")
class LikeType(DjangoObjectType):
    class Meta:


        model = Like
        fields = ("id", "user", "post", "created_at")
class CommentType(DjangoObjectType):
    class Meta:


        model = Comment
        fields = ("id", "user", "post", "content", "created_at")
class FollowType(DjangoObjectType):
    class Meta:


        model = Follow
        fields = ("id", "follower", "following", "created_at")
class StockType(DjangoObjectType):
    class Meta:


        model = Stock
        fields = (
    "id",
    "symbol",
    "company_name",
    "sector",
    "market_cap",
    "pe_ratio",
    "dividend_yield",
    "debt_ratio",
    "volatility",
    "beginner_friendly_score",
    "current_price")
# Add camelCase fields for frontend compatibility
    companyName = graphene.String()  # camelCase field
    currentPrice = graphene.Float()  # camelCase field
# Resolver for camelCase field
    def resolve_companyName(self, info):
        return self.company_name
    
    def resolve_currentPrice(self, info):
        """Return current price from database (updated by resolvers that fetch real-time data)"""
        # Note: Real-time price fetching is handled in the resolvers (beginnerFriendlyStocks, aiRecommendations)
        # to avoid async issues in GraphQL resolvers. The database price is updated there.
        if self.current_price:
            return float(self.current_price)
        return None
class StockDataType(DjangoObjectType):
    class Meta:


        model = StockData
        fields = (
    "id",
    "stock",
    "date",
    "open_price",
    "high_price",
    "low_price",
    "close_price",
    "volume")


class WatchlistType(graphene.ObjectType):


    id = graphene.ID()
    stock = graphene.Field('core.types.StockType')
    notes = graphene.String()
    targetPrice = graphene.Float()
    addedAt = graphene.DateTime()
    createdAt = graphene.DateTime()
    updatedAt = graphene.DateTime()
    def resolve_stock(self, info):
        return self.stock
    
    def resolve_notes(self, info):
        return self.notes
    
    def resolve_targetPrice(self, info):
        if self.target_price:
            return float(self.target_price)
        return None
    def resolve_addedAt(self, info):


                return self.added_at
    def resolve_createdAt(self, info):


                return self.created_at
    def resolve_updatedAt(self, info):


                return self.updated_at
class WatchlistItemType(graphene.ObjectType):


    id = graphene.ID()
    watchlist = graphene.Field(WatchlistType)
    stock = graphene.Field(StockType)
    notes = graphene.String()
    target_price = graphene.Decimal()
    added_at = graphene.DateTime()
# Add camelCase aliases for mobile app compatibility
    addedAt = graphene.DateTime()
    def resolve_addedAt(self, info):


                return self.added_at
class PortfolioType(DjangoObjectType):
    class Meta:


        model = Portfolio
        fields = (
    "id",
    "stock",
    "shares",
    "notes",
    "current_price",
    "total_value",
    "created_at",
    "updated_at")
# Add camelCase fields for frontend compatibility
    stock = graphene.Field('core.types.StockType')
    currentPrice = graphene.Float()
    totalValue = graphene.Float()
    createdAt = graphene.DateTime()
    updatedAt = graphene.DateTime()
    def resolve_stock(self, info):


                return self.stock
    def resolve_currentPrice(self, info):


        if self.current_price:
            return float(self.current_price)
        return None
    def resolve_totalValue(self, info):


        if self.total_value:
            return float(self.total_value)
        return None
    def resolve_createdAt(self, info):


                return self.created_at
    def resolve_updatedAt(self, info):


                return self.updated_at
class DiscussionCommentType(DjangoObjectType):
    class Meta:


        model = DiscussionComment
        fields = (
    "id",
    "user",
    "discussion",
    "parent_comment",
    "content",
    "upvotes",
    "downvotes",
    "is_deleted",
    "created_at",
    "updated_at")
# Add camelCase fields for frontend compatibility
    user = graphene.Field('core.types.UserType')
    parentComment = graphene.Field('core.types.DiscussionCommentType')
    createdAt = graphene.DateTime()
    updatedAt = graphene.DateTime()
    score = graphene.Int()
    replyCount = graphene.Int()
    def resolve_user(self, info):


                return self.user
    def resolve_parentComment(self, info):


                return self.parent_comment
    def resolve_createdAt(self, info):


                return self.created_at
    def resolve_updatedAt(self, info):


                return self.updated_at
    def resolve_score(self, info):


                return self.score
    def resolve_replyCount(self, info):


                return self.reply_count
class StockDiscussionType(DjangoObjectType):
    class Meta:


        model = StockDiscussion
        fields = (
    "id",
    "user",
    "stock",
    "title",
    "content",
    "discussion_type",
    "visibility",
    "upvotes",
    "downvotes",
    "is_pinned",
    "is_locked",
    "created_at",
    "updated_at")
# Add camelCase fields for frontend compatibility
    user = graphene.Field('core.types.UserType')
    stock = graphene.Field('core.types.StockType')
    discussionType = graphene.String()
    visibility = graphene.String()
    isPinned = graphene.Boolean()
    isLocked = graphene.Boolean()
    createdAt = graphene.DateTime()
    updatedAt = graphene.DateTime()
    score = graphene.Int()
    commentCount = graphene.Int()
    comments = graphene.List(DiscussionCommentType)
    def resolve_user(self, info):


                return self.user
    def resolve_stock(self, info):


                return self.stock
    def resolve_discussionType(self, info):


                return self.discussion_type
    def resolve_isPinned(self, info):


                return self.is_pinned
    def resolve_isLocked(self, info):


                return self.is_locked
    def resolve_createdAt(self, info):


                return self.created_at
    def resolve_updatedAt(self, info):


                return self.updated_at
    def resolve_score(self, info):


                return self.score
    def resolve_commentCount(self, info):


                return self.comment_count
    def resolve_comments(self, info):


                return self.comments.filter(
        parent_comment__isnull=True).order_by('-created_at')
# class PortfolioPositionType(graphene.ObjectType):
# id = graphene.ID()
# position_type = graphene.String()
# shares = graphene.Decimal()
# entry_price = graphene.Decimal()
# current_price = graphene.Decimal()
# entry_date = graphene.DateTime()
# exit_date = graphene.DateTime()
# notes = graphene.String()
# portfolio = graphene.Field(PortfolioType)
# stock = graphene.Field(StockType)
# current_value = graphene.Decimal()
# total_return = graphene.Decimal()
# total_return_percent = graphene.Decimal()
class PriceAlertType(graphene.ObjectType):


    id = graphene.ID()
    alert_type = graphene.String()
    target_value = graphene.Decimal()
    is_active = graphene.Boolean()
    is_triggered = graphene.Boolean()
    triggered_at = graphene.DateTime()
    created_at = graphene.DateTime()
    user = graphene.Field('core.types.UserType')
    stock = graphene.Field(StockType)
class SocialFeedType(graphene.ObjectType):


    """Aggregated social feed for users"""
    id = graphene.ID()
    content_type = graphene.String()
    content_id = graphene.Int()
    is_read = graphene.Boolean()
    created_at = graphene.DateTime()
    user = graphene.Field('core.types.UserType')
# Simplified content field - we'll handle the union logic in resolvers
    content_summary = graphene.String()
    def resolve_content_summary(self, info):
        """Provide a summary of the content"""
        if self.content_type == 'discussion':
            try:
                discussion = StockDiscussion.objects.get(id=self.content_id)
                return f"Discussion: {discussion.title}"
            except BaseException:
                return "Discussion content"
        elif self.content_type == 'watchlist':
            try:
                watchlist = Watchlist.objects.get(id=self.content_id)
                return f"Watchlist: {watchlist.name}"
            except BaseException:
                return "Watchlist content"
        elif self.content_type == 'portfolio':
            try:
                portfolio = Portfolio.objects.get(id=self.content_id)
                return f"Portfolio: {portfolio.name}"
            except BaseException:
                return "Portfolio content"
        return "Unknown content type"
class UserAchievementType(graphene.ObjectType):


    id = graphene.ID()
    achievement_type = graphene.String()
    title = graphene.String()
    description = graphene.String()
    icon = graphene.String()
    earned_at = graphene.DateTime()
    user = graphene.Field('core.types.UserType')
class StockSentimentType(graphene.ObjectType):


    id = graphene.ID()
    positive_votes = graphene.Int()
    negative_votes = graphene.Int()
    neutral_votes = graphene.Int()
    total_votes = graphene.Int()
    sentiment_score = graphene.Decimal()
    last_updated = graphene.DateTime()
    stock = graphene.Field(StockType)
class WatchlistContent(graphene.ObjectType):


    """Union type for watchlist content"""
    watchlist = graphene.Field(WatchlistType)
# Rust Analysis Types
class TechnicalIndicatorsType(graphene.ObjectType):


    rsi = graphene.Float()
    macd = graphene.Float()
    macdSignal = graphene.Float()
    macdHistogram = graphene.Float()
    sma20 = graphene.Float()
    sma50 = graphene.Float()
    ema12 = graphene.Float()
    ema26 = graphene.Float()
    bollingerUpper = graphene.Float()
    bollingerLower = graphene.Float()
    bollingerMiddle = graphene.Float()
class FundamentalAnalysisType(graphene.ObjectType):


    valuationScore = graphene.Int()
    growthScore = graphene.Int()
    stabilityScore = graphene.Int()
    dividendScore = graphene.Int()
    debtScore = graphene.Int()
class RustRecommendationType(graphene.ObjectType):


    symbol = graphene.String()
    reason = graphene.String()
    riskLevel = graphene.String()
    beginnerScore = graphene.Int()
class RustHealthType(graphene.ObjectType):


    status = graphene.String()
    service = graphene.String()
    timestamp = graphene.String()
class StockPriceType(graphene.ObjectType):


    """Type for current stock price data"""
    symbol = graphene.String()
    current_price = graphene.Float()
    change = graphene.Float()
    change_percent = graphene.String()
    last_updated = graphene.String()
    source = graphene.String()
    verified = graphene.Boolean()
    api_response = graphene.JSONString()


class MomentCategoryEnum(graphene.Enum):
    """Enum for moment categories"""
    EARNINGS = "EARNINGS"
    NEWS = "NEWS"
    INSIDER = "INSIDER"
    MACRO = "MACRO"
    SENTIMENT = "SENTIMENT"
    OTHER = "OTHER"


class ChartRangeEnum(graphene.Enum):
    """Enum for chart time ranges"""
    ONE_MONTH = "ONE_MONTH"
    THREE_MONTHS = "THREE_MONTHS"
    SIX_MONTHS = "SIX_MONTHS"
    YEAR_TO_DATE = "YEAR_TO_DATE"
    ONE_YEAR = "ONE_YEAR"


class StockMomentType(DjangoObjectType):
    """GraphQL type for stock moments"""
    category = graphene.Field(MomentCategoryEnum)
    importanceScore = graphene.Float()
    quickSummary = graphene.String()
    deepSummary = graphene.String()
    sourceLinks = graphene.List(graphene.String)
    impact1D = graphene.Float()
    impact7D = graphene.Float()

    class Meta:
        model = StockMoment
        fields = (
            "id",
            "symbol",
            "timestamp",
            "importance_score",
            "category",
            "title",
            "quick_summary",
            "deep_summary",
            "source_links",
            "impact_1d",
            "impact_7d",
        )

    def resolve_category(self, info):
        return self.category

    def resolve_importanceScore(self, info):
        return self.importance_score

    def resolve_quickSummary(self, info):
        return self.quick_summary

    def resolve_deepSummary(self, info):
        return self.deep_summary

    def resolve_sourceLinks(self, info):
        return self.source_links or []

    def resolve_impact1D(self, info):
        return self.impact_1d

    def resolve_impact7D(self, info):
        return self.impact_7d


# Day Trading Types
class DayTradingFeaturesType(graphene.ObjectType):
    """GraphQL type for day trading features"""
    momentum15m = graphene.Float()
    rvol10m = graphene.Float()
    vwapDist = graphene.Float()
    breakoutPct = graphene.Float()
    spreadBps = graphene.Float()
    catalystScore = graphene.Float()


class DayTradingRiskType(graphene.ObjectType):
    """GraphQL type for day trading risk metrics"""
    atr5m = graphene.Float()
    sizeShares = graphene.Int()
    stop = graphene.Float()
    targets = graphene.List(graphene.Float)
    timeStopMin = graphene.Int()


class DayTradingPickType(graphene.ObjectType):
    """GraphQL type for a day trading pick"""
    symbol = graphene.String()
    side = graphene.String()  # "LONG" or "SHORT"
    score = graphene.Float()
    features = graphene.Field(DayTradingFeaturesType)
    risk = graphene.Field(DayTradingRiskType)
    notes = graphene.String()


class DayTradingDataType(graphene.ObjectType):
    """GraphQL type for day trading picks data"""
    asOf = graphene.String()
    mode = graphene.String()  # "SAFE" or "AGGRESSIVE"
    picks = graphene.List(DayTradingPickType)
    universeSize = graphene.Int()
    qualityThreshold = graphene.Float()


# Research Hub Types
class SnapshotType(graphene.ObjectType):
    """Company snapshot data"""
    name = graphene.String()
    sector = graphene.String()
    marketCap = graphene.Float()
    country = graphene.String()
    website = graphene.String()


class QuoteType(graphene.ObjectType):
    """Stock quote data"""
    price = graphene.Float()
    chg = graphene.Float()
    chgPct = graphene.Float()
    high = graphene.Float()
    low = graphene.Float()
    volume = graphene.Float()


class TechnicalType(graphene.ObjectType):
    """Technical analysis indicators"""
    rsi = graphene.Float()
    macd = graphene.Float()
    macdhistogram = graphene.Float()
    movingAverage50 = graphene.Float()
    movingAverage200 = graphene.Float()
    supportLevel = graphene.Float()
    resistanceLevel = graphene.Float()
    impliedVolatility = graphene.Float()


class SentimentType(graphene.ObjectType):
    """Sentiment analysis data"""
    label = graphene.String()
    score = graphene.Float()
    articleCount = graphene.Int()
    confidence = graphene.Float()


class MacroType(graphene.ObjectType):
    """Macro market data"""
    vix = graphene.Float()
    marketSentiment = graphene.String()
    riskAppetite = graphene.Float()


class MarketRegimeType(graphene.ObjectType):
    """Market regime analysis"""
    market_regime = graphene.String()
    confidence = graphene.Float()
    recommended_strategy = graphene.String()


class ResearchHubType(graphene.ObjectType):
    """Complete research hub data for a stock"""
    symbol = graphene.String()
    snapshot = graphene.Field(SnapshotType)
    quote = graphene.Field(QuoteType)
    technical = graphene.Field(TechnicalType)
    sentiment = graphene.Field(SentimentType)
    macro = graphene.Field(MacroType)
    marketRegime = graphene.Field(MarketRegimeType)
    peers = graphene.List(graphene.String)
    updatedAt = graphene.String()
