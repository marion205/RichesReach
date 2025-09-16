# core/types.py
from __future__ import annotations

import graphene
from graphene_django import DjangoObjectType

from .models import (
    User,
    Post,
    ChatSession,
    ChatMessage,
    Source,
    Like,
    Comment,
    Follow,
    Stock,
    StockData,
    Watchlist,
    IncomeProfile,
    AIPortfolioRecommendation,
    Portfolio,
    StockDiscussion,
    DiscussionComment,
)

# -----------------------------------------------------------------------------
# User & Profile
# -----------------------------------------------------------------------------

class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ("id", "email", "name", "profile_pic")

    # camelCase alias
    profilePic = graphene.String()

    # related profile
    incomeProfile = graphene.Field(lambda: IncomeProfileType)

    # computed fields often needed by mobile
    followers_count = graphene.Int()
    following_count = graphene.Int()
    is_following_user = graphene.Boolean()
    is_followed_by_user = graphene.Boolean()

    # premium flags expected by frontend (stubbed for now)
    hasPremiumAccess = graphene.Boolean()
    subscriptionTier = graphene.String()

    def resolve_profilePic(self, info):
        return self.profile_pic

    def resolve_incomeProfile(self, info):
        # OneToOne reverse accessor
        try:
            return self.incomeProfile
        except IncomeProfile.DoesNotExist:
            return None

    def resolve_followers_count(self, info):
        return self.followers.count()

    def resolve_following_count(self, info):
        return self.following.count()

    def resolve_is_following_user(self, info):
        user = info.context.user
        return False if user.is_anonymous else user.is_following(self)

    def resolve_is_followed_by_user(self, info):
        user = info.context.user
        return False if user.is_anonymous else user.is_followed_by(self)

    def resolve_hasPremiumAccess(self, info):
        return False

    def resolve_subscriptionTier(self, info):
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
            "updated_at",
        )

    # camelCase aliases
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


# -----------------------------------------------------------------------------
# Stocks & Analytics
# -----------------------------------------------------------------------------

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
            "current_price",
        )

    # camelCase aliases
    companyName = graphene.String()
    currentPrice = graphene.Float()
    marketCap = graphene.Float()
    peRatio = graphene.Float()
    dividendYield = graphene.Float()
    debtRatio = graphene.Float()
    volatility = graphene.Float()
    beginnerFriendlyScore = graphene.Int()
    reasoning = graphene.String()
    score = graphene.Float()
    mlScore = graphene.Float()

    def resolve_companyName(self, info):
        return self.company_name

    def resolve_currentPrice(self, info):
        return float(self.current_price) if self.current_price is not None else None

    def resolve_marketCap(self, info):
        return float(self.market_cap) if self.market_cap is not None else None

    def resolve_peRatio(self, info):
        return float(self.pe_ratio) if self.pe_ratio is not None else None

    def resolve_dividendYield(self, info):
        return float(self.dividend_yield) if self.dividend_yield is not None else None

    def resolve_debtRatio(self, info):
        return float(self.debt_ratio) if self.debt_ratio is not None else None

    def resolve_volatility(self, info):
        return float(self.volatility) if self.volatility is not None else None

    def resolve_beginnerFriendlyScore(self, info):
        return self.beginner_friendly_score

    def resolve_reasoning(self, info):
        # Generate reasoning based on stock data
        reasons = []
        if self.beginner_friendly_score and self.beginner_friendly_score >= 80:
            reasons.append("High beginner-friendly score")
        if self.market_cap and self.market_cap >= 1000000000000:  # $1T+
            reasons.append("Large market cap")
        if self.pe_ratio and 10 <= self.pe_ratio <= 25:
            reasons.append("Reasonable valuation")
        if self.dividend_yield and self.dividend_yield > 0.02:  # 2%+
            reasons.append("Good dividend yield")
        return "; ".join(reasons) if reasons else "Standard investment opportunity"

    def resolve_score(self, info):
        # Use beginner friendly score as the main score
        return float(self.beginner_friendly_score) if self.beginner_friendly_score else 0.0

    def resolve_mlScore(self, info):
        # Use beginner friendly score as ML score for now
        return float(self.beginner_friendly_score) if self.beginner_friendly_score else 0.0


class StockDataType(DjangoObjectType):
    class Meta:
        model = StockData
        fields = ("id", "stock", "date", "open_price", "high_price", "low_price", "close_price", "volume")


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
    valuationScore = graphene.Float()
    growthScore = graphene.Float()
    stabilityScore = graphene.Float()
    dividendScore = graphene.Float()
    debtScore = graphene.Float()


class RustStockAnalysisType(graphene.ObjectType):
    symbol = graphene.String()
    beginnerFriendlyScore = graphene.Float()
    riskLevel = graphene.String()
    recommendation = graphene.String()
    technicalIndicators = graphene.Field(TechnicalIndicatorsType)
    fundamentalAnalysis = graphene.Field(FundamentalAnalysisType)
    reasoning = graphene.List(graphene.String)


# -----------------------------------------------------------------------------
# AI Portfolio Recommendations (JSON-backed child objects)
# -----------------------------------------------------------------------------

class StockRecommendationType(graphene.ObjectType):
    symbol = graphene.String()
    companyName = graphene.String()
    allocation = graphene.Float()
    reasoning = graphene.String()
    riskLevel = graphene.String()
    expectedReturn = graphene.Float()


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
            "updated_at",
        )

    # camelCase aliases
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
        data = self.recommended_stocks or []
        return [
            StockRecommendationType(
                symbol=item.get("symbol", ""),
                companyName=item.get("companyName", ""),
                allocation=float(item.get("allocation", 0.0) or 0.0),
                reasoning=item.get("reasoning", ""),
                riskLevel=item.get("riskLevel", ""),
                expectedReturn=float(item.get("expectedReturn", 0.0) or 0.0),
            )
            for item in data
        ]

    def resolve_expectedPortfolioReturn(self, info):
        val = self.expected_portfolio_return
        try:
            return float(val) if val is not None else None
        except (ValueError, TypeError):
            return None

    def resolve_riskAssessment(self, info):
        return self.risk_assessment

    def resolve_createdAt(self, info):
        return self.created_at

    def resolve_updatedAt(self, info):
        return self.updated_at


# -----------------------------------------------------------------------------
# Social / Posts / Likes / Comments
# -----------------------------------------------------------------------------

class PostType(DjangoObjectType):
    class Meta:
        model = Post
        fields = ("id", "user", "content", "image", "created_at", "likes", "comments")


class ChatSessionType(DjangoObjectType):
    class Meta:
        model = ChatSession
        fields = ("id", "user", "title", "created_at", "updated_at", "messages")


class ChatMessageType(DjangoObjectType):
    class Meta:
        model = ChatMessage
        fields = ("id", "session", "role", "content", "created_at", "confidence", "tokens_used")


class SourceType(DjangoObjectType):
    class Meta:
        model = Source
        fields = ("id", "title", "url", "snippet")


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


# -----------------------------------------------------------------------------
# Watchlist / Portfolio
# -----------------------------------------------------------------------------

class WatchlistType(DjangoObjectType):
    class Meta:
        model = Watchlist
        fields = ("id", "user", "stock", "notes", "target_price", "added_at", "created_at", "updated_at", "name",
                  "is_public", "is_shared", "description")

    # camelCase aliases
    stock = graphene.Field(lambda: StockType)  # override for proper type
    targetPrice = graphene.Float()
    addedAt = graphene.DateTime()
    createdAt = graphene.DateTime()
    updatedAt = graphene.DateTime()

    def resolve_stock(self, info):
        return self.stock

    def resolve_targetPrice(self, info):
        return float(self.target_price) if self.target_price is not None else None

    def resolve_addedAt(self, info):
        return self.added_at

    def resolve_createdAt(self, info):
        return self.created_at

    def resolve_updatedAt(self, info):
        return self.updated_at


class PortfolioType(DjangoObjectType):
    class Meta:
        model = Portfolio
        fields = ("id", "user", "stock", "shares", "notes", "average_price",
                  "current_price", "total_value", "created_at", "updated_at")

    # camelCase aliases
    stock = graphene.Field(lambda: StockType)
    currentPrice = graphene.Float()
    totalValue = graphene.Float()
    createdAt = graphene.DateTime()
    updatedAt = graphene.DateTime()

    def resolve_stock(self, info):
        return self.stock

    def resolve_currentPrice(self, info):
        return float(self.current_price) if self.current_price is not None else None

    def resolve_totalValue(self, info):
        return float(self.total_value) if self.total_value is not None else None

    def resolve_createdAt(self, info):
        return self.created_at

    def resolve_updatedAt(self, info):
        return self.updated_at


# -----------------------------------------------------------------------------
# Discussions (Reddit-like)
# -----------------------------------------------------------------------------

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
            "updated_at",
        )

    # camelCase / computed
    user = graphene.Field(lambda: UserType)  # override to ensure proper type in schema
    parentComment = graphene.Field(lambda: DiscussionCommentType)
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
            "is_analysis",
            "analysis_data",
            "upvotes",
            "downvotes",
            "is_pinned",
            "is_locked",
            "created_at",
            "updated_at",
        )

    # camelCase / computed
    user = graphene.Field(lambda: UserType)
    stock = graphene.Field(lambda: StockType)
    discussionType = graphene.String()
    isPinned = graphene.Boolean()
    isLocked = graphene.Boolean()
    createdAt = graphene.DateTime()
    updatedAt = graphene.DateTime()
    score = graphene.Int()
    commentCount = graphene.Int()
    comments = graphene.List(lambda: DiscussionCommentType)

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
        # top-level comments only; newest first
        return self.comments.filter(parent_comment__isnull=True).order_by("-created_at")


# -----------------------------------------------------------------------------
# Misc simple objects used by resolvers
# -----------------------------------------------------------------------------

class PriceAlertType(graphene.ObjectType):
    id = graphene.ID()
    alert_type = graphene.String()
    target_value = graphene.Decimal()
    is_active = graphene.Boolean()
    is_triggered = graphene.Boolean()
    triggered_at = graphene.DateTime()
    created_at = graphene.DateTime()
    user = graphene.Field(lambda: UserType)
    stock = graphene.Field(StockType)


class SocialFeedType(graphene.ObjectType):
    """Lightweight union-like item with a text summary for the feed."""
    id = graphene.ID()
    content_type = graphene.String()
    content_id = graphene.Int()
    is_read = graphene.Boolean()
    created_at = graphene.DateTime()
    user = graphene.Field(lambda: UserType)
    content_summary = graphene.String()

    def resolve_content_summary(self, info):
        if self.content_type == "discussion":
            try:
                d = StockDiscussion.objects.get(id=self.content_id)
                return f"Discussion: {d.title}"
            except StockDiscussion.DoesNotExist:
                return "Discussion content"
        if self.content_type == "watchlist":
            try:
                w = Watchlist.objects.get(id=self.content_id)
                return f"Watchlist: {w.name or w.stock.symbol}"
            except Watchlist.DoesNotExist:
                return "Watchlist content"
        if self.content_type == "portfolio":
            try:
                p = Portfolio.objects.get(id=self.content_id)
                return f"Portfolio holding: {p.stock.symbol} ({p.shares} shares)"
            except Portfolio.DoesNotExist:
                return "Portfolio content"
        return "Unknown content"


class UserAchievementType(graphene.ObjectType):
    id = graphene.ID()
    achievement_type = graphene.String()
    title = graphene.String()
    description = graphene.String()
    icon = graphene.String()
    earned_at = graphene.DateTime()
    user = graphene.Field(lambda: UserType)


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
    """Example union wrapper (kept for compatibility)."""
    watchlist = graphene.Field(WatchlistType)


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
    """For current/streamed price results from services."""
    symbol = graphene.String()
    current_price = graphene.Float()
    change = graphene.Float()
    change_percent = graphene.String()
    last_updated = graphene.String()
    source = graphene.String()
    verified = graphene.Boolean()
    api_response = graphene.JSONString()


# ---- Financial Tool Types ----
class DebtInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    balance = graphene.Float(required=True)
    apr = graphene.Float(required=True)
    minPayment = graphene.Float(required=True)

class DebtBalanceType(graphene.ObjectType):
    name = graphene.String()
    balance = graphene.Float()

class DebtMonthPreviewType(graphene.ObjectType):
    month = graphene.Int()
    totalPaid = graphene.Float()
    interestPaid = graphene.Float()
    balances = graphene.List(DebtBalanceType)

class DebtSnowballResultType(graphene.ObjectType):
    status = graphene.String()
    monthsToDebtFree = graphene.Int()
    totalInterest = graphene.Float()
    payoffOrder = graphene.List(graphene.String)
    schedulePreview = graphene.List(DebtMonthPreviewType)

class CardInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    limit = graphene.Float(required=True)
    balance = graphene.Float(required=True)
    apr = graphene.Float()  # optional

class CardAllocationType(graphene.ObjectType):
    name = graphene.String()
    pay = graphene.Float()

class CreditUtilResultType(graphene.ObjectType):
    currentUtilization = graphene.Float()
    targetUtilization = graphene.Float()
    amountToPay = graphene.Float()
    allocation = graphene.List(CardAllocationType)
    note = graphene.String()

class PurchaseAdviceType(graphene.ObjectType):
    decision = graphene.String()
    reasons = graphene.List(graphene.String)
    bands = graphene.JSONString()
    current = graphene.JSONString()
    item = graphene.JSONString()

# Rust Stock Analysis Types
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
    valuationScore = graphene.Float()
    growthScore = graphene.Float()
    stabilityScore = graphene.Float()
    dividendScore = graphene.Float()
    debtScore = graphene.Float()

class RustStockAnalysisType(graphene.ObjectType):
    symbol = graphene.String()
    beginnerFriendlyScore = graphene.Int()
    riskLevel = graphene.String()
    recommendation = graphene.String()
    technicalIndicators = graphene.Field(TechnicalIndicatorsType)
    fundamentalAnalysis = graphene.Field(FundamentalAnalysisType)
    reasoning = graphene.String()