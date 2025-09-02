# core/types.py
import graphene
from graphene_django import DjangoObjectType
from .models import User, Post, ChatSession, ChatMessage, Source, Like, Comment, Follow, Stock, StockData, Watchlist, WatchlistItem, StockDiscussion, DiscussionComment, Portfolio, PortfolioPosition, PriceAlert, SocialFeed, UserAchievement, StockSentiment, IncomeProfile, AIPortfolioRecommendation, StockRecommendation

class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ("id", "email", "name", "profile_pic")
    
    # Add camelCase fields for frontend compatibility
    profilePic = graphene.String()  # camelCase field
    
    # Add income profile field
    incomeProfile = graphene.Field('core.types.IncomeProfileType')
    
    def resolve_incomeProfile(self, info):
        try:
            return self.incomeProfile
        except:
            return None
    
    # Resolver for camelCase field
    def resolve_profilePic(self, info):
        return self.profile_pic
    
    # Add computed fields that the frontend expects
    followers_count = graphene.Int()
    following_count = graphene.Int()
    is_following_user = graphene.Boolean()
    is_followed_by_user = graphene.Boolean()
    
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
        fields = ("id", "symbol", "company_name", "sector", "market_cap", "pe_ratio", "dividend_yield", "debt_ratio", "volatility", "beginner_friendly_score")
    
    # Add camelCase fields for frontend compatibility
    companyName = graphene.String()  # camelCase field
    
    # Resolver for camelCase field
    def resolve_companyName(self, info):
        return self.company_name

class StockDataType(DjangoObjectType):
    class Meta:
        model = StockData
        fields = ("id", "stock", "date", "open_price", "high_price", "low_price", "close_price", "volume")

class WatchlistType(graphene.ObjectType):
    id = graphene.ID()
    name = graphene.String()
    description = graphene.String()
    is_public = graphene.Boolean()
    is_shared = graphene.Boolean()
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()
    user = graphene.Field('core.types.UserType')
    items = graphene.List(lambda: WatchlistItemType)
    item_count = graphene.Int()
    
    def resolve_items(self, info):
        return self.items.all()
    
    def resolve_item_count(self, info):
        return self.items.count()

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

class StockDiscussionType(graphene.ObjectType):
    id = graphene.ID()
    title = graphene.String()
    content = graphene.String()
    discussion_type = graphene.String()
    discussionType = graphene.String()  # camelCase field
    is_analysis = graphene.Boolean()
    analysis_data = graphene.JSONString()
    created_at = graphene.DateTime()
    createdAt = graphene.DateTime()  # camelCase field
    updated_at = graphene.DateTime()
    updatedAt = graphene.DateTime()  # camelCase field
    user = graphene.Field('core.types.UserType')
    stock = graphene.Field(StockType)
    likes = graphene.List('core.types.UserType')
    like_count = graphene.Int()
    likeCount = graphene.Int()  # camelCase field
    comments = graphene.List(lambda: DiscussionCommentType)
    comment_count = graphene.Int()
    commentCount = graphene.Int()  # camelCase field
    
    def resolve_likes(self, info):
        return self.likes.all()
    
    def resolve_like_count(self, info):
        return self.likes.count()
    
    def resolve_comments(self, info):
        return self.comments.all()
    
    def resolve_comment_count(self, info):
        return self.comments.count()
    
    # Resolvers for camelCase fields
    def resolve_discussionType(self, info):
        return self.discussion_type
    
    def resolve_createdAt(self, info):
        return self.created_at
    
    def resolve_updatedAt(self, info):
        return self.updated_at
    
    def resolve_likeCount(self, info):
        return self.likes.count()
    
    def resolve_commentCount(self, info):
        return self.comments.count()

class DiscussionCommentType(graphene.ObjectType):
    id = graphene.ID()
    content = graphene.String()
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()
    user = graphene.Field('core.types.UserType')
    discussion = graphene.Field(StockDiscussionType)
    likes = graphene.List('core.types.UserType')
    like_count = graphene.Int()
    
    def resolve_likes(self, info):
        return self.likes.all()
    
    def resolve_like_count(self, info):
        return self.likes.count()

class PortfolioType(DjangoObjectType):
    class Meta:
        model = Portfolio
        fields = '__all__'

    total_value = graphene.Float()
    market_value = graphene.Float()

    def resolve_total_value(self, info):
        return self.total_value

    def resolve_market_value(self, info):
        return self.market_value

class PortfolioPositionType(graphene.ObjectType):
    id = graphene.ID()
    position_type = graphene.String()
    shares = graphene.Decimal()
    entry_price = graphene.Decimal()
    current_price = graphene.Decimal()
    entry_date = graphene.DateTime()
    exit_date = graphene.DateTime()
    notes = graphene.String()
    portfolio = graphene.Field(PortfolioType)
    stock = graphene.Field(StockType)
    current_value = graphene.Decimal()
    total_return = graphene.Decimal()
    total_return_percent = graphene.Decimal()

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
            except:
                return "Discussion content"
        elif self.content_type == 'watchlist':
            try:
                watchlist = Watchlist.objects.get(id=self.content_id)
                return f"Watchlist: {watchlist.name}"
            except:
                return "Watchlist content"
        elif self.content_type == 'portfolio':
            try:
                portfolio = Portfolio.objects.get(id=self.content_id)
                return f"Portfolio: {portfolio.name}"
            except:
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

class DiscussionContent(graphene.ObjectType):
    """Union type for discussion content"""
    discussion = graphene.Field(StockDiscussionType)

class WatchlistContent(graphene.ObjectType):
    """Union type for watchlist content"""
    watchlist = graphene.Field(WatchlistType)

class PortfolioContent(graphene.ObjectType):
    """Union type for portfolio content"""
    portfolio = graphene.Field(PortfolioType)

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

class RustStockAnalysisType(graphene.ObjectType):
    symbol = graphene.String()
    beginnerFriendlyScore = graphene.Int()
    riskLevel = graphene.String()
    recommendation = graphene.String()
    technicalIndicators = graphene.Field(TechnicalIndicatorsType)
    fundamentalAnalysis = graphene.Field(FundamentalAnalysisType)
    reasoning = graphene.List(graphene.String)

class RustRecommendationType(graphene.ObjectType):
    symbol = graphene.String()
    reason = graphene.String()
    riskLevel = graphene.String()
    beginnerScore = graphene.Int()

class RustHealthType(graphene.ObjectType):
    status = graphene.String()
    service = graphene.String()
    timestamp = graphene.String()


class IncomeProfileType(DjangoObjectType):
    class Meta:
        model = IncomeProfile
        fields = ("id", "income_bracket", "age", "investment_goals", "risk_tolerance", "investment_horizon", "created_at", "updated_at")


class AIPortfolioRecommendationType(DjangoObjectType):
    class Meta:
        model = AIPortfolioRecommendation
        fields = ("id", "user", "risk_profile", "portfolio_allocation", "expected_portfolio_return", "risk_assessment", "created_at")
    
    # Add computed field for stock recommendations
    recommendedStocks = graphene.List('core.types.StockRecommendationType')
    
    # Add camelCase aliases for frontend compatibility
    riskProfile = graphene.String()
    expectedPortfolioReturn = graphene.String()
    riskAssessment = graphene.String()
    portfolioAllocation = graphene.JSONString()
    
    def resolve_recommendedStocks(self, info):
        return self.recommendedStocks.all()
    
    def resolve_riskProfile(self, info):
        return self.risk_profile
    
    def resolve_expectedPortfolioReturn(self, info):
        return self.expected_portfolio_return
    
    def resolve_riskAssessment(self, info):
        return self.risk_assessment
    
    def resolve_portfolioAllocation(self, info):
        return self.portfolio_allocation


class StockRecommendationType(DjangoObjectType):
    class Meta:
        model = StockRecommendation
        fields = ("id", "portfolio_recommendation", "stock", "allocation", "reasoning", "risk_level", "expected_return")
    
    # Add computed fields for frontend compatibility
    companyName = graphene.String()
    symbol = graphene.String()
    riskLevel = graphene.String()
    expectedReturn = graphene.String()
    allocation = graphene.Float()
    
    def resolve_companyName(self, info):
        return self.stock.company_name if self.stock else None
    
    def resolve_symbol(self, info):
        return self.stock.symbol if self.stock else None
    
    def resolve_riskLevel(self, info):
        return self.risk_level
    
    def resolve_expectedReturn(self, info):
        return self.expected_return
    
    def resolve_allocation(self, info):
        return self.allocation
    
    def resolve_reasoning(self, info):
        return self.reasoning