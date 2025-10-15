"""
GraphQL Types for Swing Trading Features
"""
import graphene
from graphene_django import DjangoObjectType
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from core.models import (
    OHLCV, Signal, SignalLike, SignalComment, TraderScore, 
    BacktestStrategy, BacktestResult, SwingWatchlist
)

logger = logging.getLogger(__name__)


class OHLCVType(DjangoObjectType):
    """OHLCV data type"""
    class Meta:
        model = OHLCV
        fields = "__all__"


class SignalType(DjangoObjectType):
    """Signal type with computed fields"""
    risk_reward_ratio = graphene.Float()
    days_since_triggered = graphene.Int()
    is_liked_by_user = graphene.Boolean()
    user_like_count = graphene.Int()
    
    class Meta:
        model = Signal
        fields = "__all__"
    
    def resolve_risk_reward_ratio(self, info):
        """Calculate risk/reward ratio"""
        if self.stop_price and self.target_price:
            risk = abs(float(self.entry_price - self.stop_price))
            reward = abs(float(self.target_price - self.entry_price))
            return reward / risk if risk > 0 else 0
        return None
    
    def resolve_days_since_triggered(self, info):
        """Calculate days since signal was triggered"""
        return (timezone.now() - self.triggered_at).days
    
    def resolve_is_liked_by_user(self, info):
        """Check if current user liked this signal"""
        user = info.context.user
        if user.is_authenticated:
            return SignalLike.objects.filter(user=user, signal=self).exists()
        return False
    
    def resolve_user_like_count(self, info):
        """Get like count for this signal"""
        return self.likes_count


class SignalLikeType(DjangoObjectType):
    """Signal like type"""
    class Meta:
        model = SignalLike
        fields = "__all__"


class SignalCommentType(DjangoObjectType):
    """Signal comment type"""
    class Meta:
        model = SignalComment
        fields = "__all__"


class TraderScoreType(DjangoObjectType):
    """Trader score type"""
    class Meta:
        model = TraderScore
        fields = "__all__"


class BacktestStrategyType(DjangoObjectType):
    """Backtest strategy type"""
    class Meta:
        model = BacktestStrategy
        fields = "__all__"


class BacktestResultType(DjangoObjectType):
    """Backtest result type"""
    class Meta:
        model = BacktestResult
        fields = "__all__"


class SwingWatchlistType(DjangoObjectType):
    """Swing Watchlist type"""
    class Meta:
        model = SwingWatchlist
        fields = "__all__"


class SignalConnection(graphene.relay.Connection):
    """Connection type for signals with pagination"""
    class Meta:
        node = SignalType


class BacktestResultConnection(graphene.relay.Connection):
    """Connection type for backtest results with pagination"""
    class Meta:
        node = BacktestResultType


class RiskAnalysisType(graphene.ObjectType):
    """Risk analysis type"""
    position_size = graphene.Int()
    dollar_risk = graphene.Float()
    position_value = graphene.Float()
    position_pct = graphene.Float()
    risk_per_trade_pct = graphene.Float()
    method = graphene.String()
    recommendations = graphene.List(graphene.String)


class PortfolioHeatType(graphene.ObjectType):
    """Portfolio heat analysis type"""
    total_risk = graphene.Float()
    total_value = graphene.Float()
    heat_percentage = graphene.Float()
    sector_exposure = graphene.JSONString()
    correlation_risk = graphene.Float()
    recommendations = graphene.List(graphene.String)
    position_count = graphene.Int()


class BacktestMetricsType(graphene.ObjectType):
    """Backtest performance metrics type"""
    total_return = graphene.Float()
    annualized_return = graphene.Float()
    max_drawdown = graphene.Float()
    sharpe_ratio = graphene.Float()
    sortino_ratio = graphene.Float()
    calmar_ratio = graphene.Float()
    win_rate = graphene.Float()
    profit_factor = graphene.Float()
    total_trades = graphene.Int()
    winning_trades = graphene.Int()
    losing_trades = graphene.Int()
    avg_win = graphene.Float()
    avg_loss = graphene.Float()
    initial_capital = graphene.Float()
    final_capital = graphene.Float()
    equity_curve = graphene.List(graphene.Float)
    daily_returns = graphene.List(graphene.Float)


class SignalAnalysisType(graphene.ObjectType):
    """Signal analysis type"""
    signal = graphene.Field(SignalType)
    risk_analysis = graphene.Field(RiskAnalysisType)
    confidence_score = graphene.Float()
    market_conditions = graphene.JSONString()
    similar_signals = graphene.List(SignalType)


class LeaderboardEntryType(graphene.ObjectType):
    """Leaderboard entry type"""
    user = graphene.Field('core.types.UserType')
    trader_score = graphene.Field(TraderScoreType)
    rank = graphene.Int()
    category = graphene.String()


class StrategyPerformanceType(graphene.ObjectType):
    """Strategy performance type"""
    strategy_name = graphene.String()
    total_return = graphene.Float()
    win_rate = graphene.Float()
    max_drawdown = graphene.Float()
    sharpe_ratio = graphene.Float()
    total_trades = graphene.Int()
    avg_trade_duration = graphene.Float()
    best_trade = graphene.Float()
    worst_trade = graphene.Float()


class MarketConditionType(graphene.ObjectType):
    """Market condition type"""
    volatility_regime = graphene.String()  # 'low', 'medium', 'high'
    trend_direction = graphene.String()    # 'bullish', 'bearish', 'sideways'
    volume_profile = graphene.String()     # 'low', 'normal', 'high'
    market_sentiment = graphene.String()   # 'fear', 'neutral', 'greed'
    vix_level = graphene.Float()
    sector_rotation = graphene.JSONString()


class SignalFilterType(graphene.InputObjectType):
    """Signal filter input type"""
    symbol = graphene.String()
    signal_type = graphene.String()
    min_ml_score = graphene.Float()
    max_ml_score = graphene.Float()
    min_risk_reward = graphene.Float()
    max_risk_reward = graphene.Float()
    is_active = graphene.Boolean()
    created_after = graphene.DateTime()
    created_before = graphene.DateTime()


class BacktestConfigType(graphene.InputObjectType):
    """Backtest configuration input type"""
    initial_capital = graphene.Float()
    commission_per_trade = graphene.Float()
    slippage_pct = graphene.Float()
    max_position_size = graphene.Float()
    risk_per_trade = graphene.Float()
    max_trades_per_day = graphene.Int()
    max_open_positions = graphene.Int()
    start_date = graphene.DateTime()
    end_date = graphene.DateTime()


class StrategyParamsType(graphene.InputObjectType):
    """Strategy parameters input type"""
    ema_fast = graphene.Int()
    ema_slow = graphene.Int()
    rsi_period = graphene.Int()
    rsi_oversold = graphene.Float()
    rsi_overbought = graphene.Float()
    atr_period = graphene.Int()
    atr_multiplier = graphene.Float()
    volume_threshold = graphene.Float()
    risk_reward_ratio = graphene.Float()
    max_hold_days = graphene.Int()


class PositionSizeInputType(graphene.InputObjectType):
    """Position sizing input type"""
    account_equity = graphene.Float(required=True)
    entry_price = graphene.Float(required=True)
    stop_price = graphene.Float(required=True)
    risk_per_trade = graphene.Float()
    max_position_pct = graphene.Float()
    confidence = graphene.Float()


class DynamicStopInputType(graphene.InputObjectType):
    """Dynamic stop loss input type"""
    entry_price = graphene.Float(required=True)
    atr = graphene.Float(required=True)
    atr_multiplier = graphene.Float()
    support_level = graphene.Float()
    resistance_level = graphene.Float()
    signal_type = graphene.String()


class TargetPriceInputType(graphene.InputObjectType):
    """Target price input type"""
    entry_price = graphene.Float(required=True)
    stop_price = graphene.Float(required=True)
    risk_reward_ratio = graphene.Float()
    atr = graphene.Float()
    resistance_level = graphene.Float()
    support_level = graphene.Float()
    signal_type = graphene.String()


class SwingWatchlistInputType(graphene.InputObjectType):
    """Swing Watchlist input type"""
    name = graphene.String(required=True)
    description = graphene.String()
    symbols = graphene.List(graphene.String, required=True)
    is_public = graphene.Boolean()


class SignalCommentInputType(graphene.InputObjectType):
    """Signal comment input type"""
    signal_id = graphene.ID(required=True)
    content = graphene.String(required=True)


class BacktestStrategyInputType(graphene.InputObjectType):
    """Backtest strategy input type"""
    name = graphene.String(required=True)
    description = graphene.String()
    strategy_type = graphene.String(required=True)
    parameters = graphene.JSONString(required=True)
    is_public = graphene.Boolean()


class OHLCVFilterType(graphene.InputObjectType):
    """OHLCV filter input type"""
    symbol = graphene.String()
    timeframe = graphene.String()
    start_date = graphene.DateTime()
    end_date = graphene.DateTime()
    limit = graphene.Int()


class SignalStatsType(graphene.ObjectType):
    """Signal statistics type"""
    total_signals = graphene.Int()
    active_signals = graphene.Int()
    validated_signals = graphene.Int()
    avg_ml_score = graphene.Float()
    avg_risk_reward = graphene.Float()
    top_performing_symbols = graphene.List(graphene.String)
    signal_type_distribution = graphene.JSONString()
    daily_signal_count = graphene.List(graphene.Int)


class TraderPerformanceType(graphene.ObjectType):
    """Trader performance type"""
    user = graphene.Field('core.types.UserType')
    total_signals = graphene.Int()
    win_rate = graphene.Float()
    avg_return = graphene.Float()
    best_trade = graphene.Float()
    worst_trade = graphene.Float()
    total_pnl = graphene.Float()
    sharpe_ratio = graphene.Float()
    max_drawdown = graphene.Float()
    consistency_score = graphene.Float()
    risk_score = graphene.Float()


class MarketScannerType(graphene.ObjectType):
    """Market scanner type"""
    symbol = graphene.String()
    current_price = graphene.Float()
    signal_type = graphene.String()
    ml_score = graphene.Float()
    risk_reward_ratio = graphene.Float()
    volume_surge = graphene.Float()
    rsi = graphene.Float()
    ema_trend = graphene.String()
    market_cap = graphene.Float()
    sector = graphene.String()
    last_updated = graphene.DateTime()


class AlertType(graphene.ObjectType):
    """Alert type"""
    id = graphene.ID()
    user = graphene.Field('core.types.UserType')
    symbol = graphene.String()
    alert_type = graphene.String()
    condition = graphene.String()
    threshold = graphene.Float()
    is_active = graphene.Boolean()
    created_at = graphene.DateTime()
    triggered_at = graphene.DateTime()
    message = graphene.String()


class NotificationType(graphene.ObjectType):
    """Notification type"""
    id = graphene.ID()
    user = graphene.Field('core.types.UserType')
    type = graphene.String()
    title = graphene.String()
    message = graphene.String()
    data = graphene.JSONString()
    is_read = graphene.Boolean()
    created_at = graphene.DateTime()


class SocialFeedItemType(graphene.Union):
    """Social feed item type (union of Signal, BacktestResult, etc.)"""
    class Meta:
        types = (SignalType, BacktestResultType, BacktestStrategyType)


class FeedItemType(graphene.ObjectType):
    """Feed item type"""
    id = graphene.ID()
    type = graphene.String()
    content = graphene.Field(SocialFeedItemType)
    user = graphene.Field('core.types.UserType')
    created_at = graphene.DateTime()
    likes_count = graphene.Int()
    comments_count = graphene.Int()
    shares_count = graphene.Int()
    is_liked_by_user = graphene.Boolean()


class TrendingStrategyType(graphene.ObjectType):
    """Trending strategy type"""
    strategy = graphene.Field(BacktestStrategyType)
    performance_score = graphene.Float()
    popularity_score = graphene.Float()
    trending_score = graphene.Float()
    followers_count = graphene.Int()
    recent_performance = graphene.Float()


class MarketInsightType(graphene.ObjectType):
    """Market insight type"""
    insight_type = graphene.String()
    title = graphene.String()
    description = graphene.String()
    confidence = graphene.Float()
    impact_level = graphene.String()
    affected_symbols = graphene.List(graphene.String)
    time_horizon = graphene.String()
    created_at = graphene.DateTime()
    expires_at = graphene.DateTime()


class PerformanceComparisonType(graphene.ObjectType):
    """Performance comparison type"""
    benchmark = graphene.String()
    strategy_performance = graphene.Float()
    benchmark_performance = graphene.Float()
    outperformance = graphene.Float()
    correlation = graphene.Float()
    beta = graphene.Float()
    alpha = graphene.Float()
    tracking_error = graphene.Float()
    information_ratio = graphene.Float()
