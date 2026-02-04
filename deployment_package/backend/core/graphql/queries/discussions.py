"""
Watchlists, discussions, social feed, portfolios, and related GraphQL queries.
Exposes watchlists, watchlist, public_watchlists, my_watchlist, stock_discussions,
discussion_detail, social_feed, top_performers, market_sentiment,
ai_portfolio_recommendations, stock_moments. Composed into ExtendedQuery.
"""
import logging
from datetime import timedelta

import django.db.models as models
import graphene
from django.utils import timezone

from core.types import ChartRangeEnum

logger = logging.getLogger(__name__)


class DiscussionsQuery(graphene.ObjectType):
    """Watchlists, discussions, social feed, and related root fields."""

    watchlists = graphene.List("core.types.WatchlistType", user_id=graphene.ID())
    watchlist = graphene.Field("core.types.WatchlistType", id=graphene.ID(required=True))
    public_watchlists = graphene.List("core.types.WatchlistType")
    my_watchlist = graphene.List("core.types.WatchlistType")
    stock_discussions = graphene.List(
        "core.types.StockDiscussionType",
        stock_symbol=graphene.String(required=False),
        limit=graphene.Int(required=False),
    )
    discussion_detail = graphene.Field(
        "core.types.StockDiscussionType",
        id=graphene.ID(required=True),
    )
    social_feed = graphene.List("core.types.StockDiscussionType")
    top_performers = graphene.List("core.types.StockType")
    market_sentiment = graphene.Field(graphene.JSONString)
    ai_portfolio_recommendations = graphene.List(
        "core.types.AIPortfolioRecommendationType",
        userId=graphene.ID(required=True),
    )
    stock_moments = graphene.List(
        "core.types.StockMomentType",
        symbol=graphene.String(required=True),
        range=graphene.Argument(ChartRangeEnum, required=True),
    )

    def resolve_watchlists(self, info, user_id=None):
        from core.models import Watchlist

        user = getattr(info.context, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return []
        qs = Watchlist.objects.select_related("user", "stock")
        if user_id:
            return qs.filter(user_id=user_id)
        return qs.filter(user=user)

    def resolve_watchlist(self, info, id):
        from core.models import Watchlist

        try:
            watchlist = Watchlist.objects.select_related("user", "stock").get(id=id)
            user = getattr(info.context, "user", None)
            if watchlist.is_public or (user and watchlist.user == user):
                return watchlist
            return None
        except Watchlist.DoesNotExist:
            return None

    def resolve_public_watchlists(self, info):
        from core.models import Watchlist

        return Watchlist.objects.filter(is_public=True).order_by("-created_at")[:20]

    def resolve_my_watchlist(self, info):
        from core.graphql_utils import get_user_from_context
        from core.models import Watchlist

        user = get_user_from_context(info.context)
        if not user or getattr(user, "is_anonymous", True):
            return []
        return Watchlist.objects.filter(user=user).select_related("stock").order_by("-added_at")

    def resolve_stock_discussions(self, info, stock_symbol=None, limit=20):
        from core.models import Stock, StockDiscussion

        user = getattr(info.context, "user", None)
        if not user or getattr(user, "is_anonymous", True):
            return []
        followed_users = user.following.values_list("following", flat=True)
        discussions = StockDiscussion.objects.filter(
            models.Q(visibility="public")
            | models.Q(user__in=followed_users)
            | models.Q(user=user)
        ).distinct()
        if stock_symbol:
            try:
                stock = Stock.objects.get(symbol=stock_symbol.upper())
                discussions = discussions.filter(stock=stock)
            except Stock.DoesNotExist:
                return []
        return list(
            discussions.select_related("user", "stock")
            .prefetch_related("comments")
            .order_by("-created_at")[:limit]
        )

    def resolve_discussion_detail(self, info, id):
        from core.models import StockDiscussion

        try:
            return StockDiscussion.objects.select_related("user", "stock").prefetch_related("comments").get(id=id)
        except StockDiscussion.DoesNotExist:
            return None

    def resolve_social_feed(self, info):
        from core.models import StockDiscussion

        user = getattr(info.context, "user", None)
        if not user or getattr(user, "is_anonymous", True):
            return []
        followed_users = user.following.values_list("following", flat=True)
        if not followed_users:
            return []
        return (
            StockDiscussion.objects.filter(user__in=followed_users)
            .select_related("user", "stock")
            .prefetch_related("comments")
            .order_by("-created_at")
        )

    def resolve_top_performers(self, info):
        from core.models import Stock

        return (
            Stock.objects.filter(beginner_friendly_score__isnull=False)
            .order_by("-beginner_friendly_score")[:10]
        )

    def resolve_market_sentiment(self, info):
        try:
            from core.models import StockSentiment

            sentiments = StockSentiment.objects.all()
            if sentiments.exists():
                avg_sentiment = sum(s.sentiment_score for s in sentiments) / sentiments.count()
                total_votes = sum(s.total_votes for s in sentiments)
                return {
                    "average_sentiment": float(avg_sentiment),
                    "total_votes": total_votes,
                    "stocks_tracked": sentiments.count(),
                    "market_mood": (
                        "bullish"
                        if avg_sentiment > 0.1
                        else "bearish"
                        if avg_sentiment < -0.1
                        else "neutral"
                    ),
                }
        except Exception as e:
            logger.warning("Error resolving market_sentiment: %s", e)
        return {
            "average_sentiment": 0,
            "total_votes": 0,
            "stocks_tracked": 0,
            "market_mood": "neutral",
        }

    def resolve_ai_portfolio_recommendations(self, info, userId):
        from core.graphql_utils import get_user_from_context
        from core.models import AIPortfolioRecommendation

        user = get_user_from_context(info.context)
        if not user or getattr(user, "is_anonymous", True):
            return []
        if str(user.id) != str(userId):
            return []
        return AIPortfolioRecommendation.objects.filter(user=user).order_by("-created_at")

    def resolve_stock_moments(self, info, symbol, range):
        from core.models import StockMoment

        try:
            now = timezone.now()
            symbol_upper = symbol.upper()
            range_value = range.value if hasattr(range, "value") else str(range)
            if range_value == "ONE_MONTH" or range == ChartRangeEnum.ONE_MONTH:
                start = now - timedelta(days=30)
            elif range_value == "THREE_MONTHS" or range == ChartRangeEnum.THREE_MONTHS:
                start = now - timedelta(days=90)
            elif range_value == "SIX_MONTHS" or range == ChartRangeEnum.SIX_MONTHS:
                start = now - timedelta(days=180)
            elif range_value == "YEAR_TO_DATE" or range == ChartRangeEnum.YEAR_TO_DATE:
                start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            elif range_value == "ONE_YEAR" or range == ChartRangeEnum.ONE_YEAR:
                start = now - timedelta(days=365)
            else:
                logger.warning("Unrecognized range: %s, defaulting to ONE_MONTH", range_value)
                start = now - timedelta(days=30)
            moments = (
                StockMoment.objects.filter(symbol=symbol_upper, timestamp__gte=start)
                .order_by("-importance_score", "-timestamp")[:50]
            )
            return list(moments)
        except Exception as e:
            logger.error("Error resolving stock moments for %s: %s", symbol, e, exc_info=True)
            return []
