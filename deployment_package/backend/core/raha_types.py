"""
RAHA GraphQL Types
GraphQL type definitions for strategy catalog, signals, and backtests
"""
import graphene
from graphene_django import DjangoObjectType
from .raha_models import Strategy, StrategyVersion, UserStrategySettings, RAHASignal, RAHABacktestRun
from django.contrib.auth import get_user_model

User = get_user_model()


class StrategyType(DjangoObjectType):
    """GraphQL type for Strategy"""
    class Meta:
        model = Strategy
        fields = '__all__'
    
    timeframe_supported = graphene.List(graphene.String)
    default_version = graphene.Field(lambda: StrategyVersionType)
    
    def resolve_timeframe_supported(self, info):
        """Convert JSON list to GraphQL list"""
        return self.timeframe_supported or []
    
    def resolve_default_version(self, info):
        """Return the default version of this strategy"""
        try:
            return self.versions.filter(is_default=True).first() or self.versions.order_by('-version').first()
        except Exception:
            return None


class StrategyVersionType(DjangoObjectType):
    """GraphQL type for StrategyVersion"""
    class Meta:
        model = StrategyVersion
        fields = '__all__'
    
    config_schema = graphene.JSONString()
    
    def resolve_config_schema(self, info):
        """Return config schema as JSON"""
        return self.config_schema or {}


class UserStrategySettingsType(DjangoObjectType):
    """GraphQL type for UserStrategySettings"""
    class Meta:
        model = UserStrategySettings
        fields = '__all__'
    
    parameters = graphene.JSONString()
    
    def resolve_parameters(self, info):
        """Return parameters as JSON"""
        return self.parameters or {}


class RAHASignalType(DjangoObjectType):
    """GraphQL type for RAHA Signal"""
    class Meta:
        model = RAHASignal
        fields = '__all__'
    
    meta = graphene.JSONString()
    
    def resolve_meta(self, info):
        """Return meta as JSON"""
        return self.meta or {}


class EquityPointType(graphene.ObjectType):
    """Type for equity curve data points"""
    timestamp = graphene.DateTime(required=True)
    equity = graphene.Float(required=True)


class RAHABacktestRunType(DjangoObjectType):
    """GraphQL type for RAHA Backtest Run"""
    class Meta:
        model = RAHABacktestRun
        fields = '__all__'
    
    parameters = graphene.JSONString()
    metrics = graphene.JSONString()
    equity_curve = graphene.List(EquityPointType)
    trade_log = graphene.JSONString()
    
    def resolve_parameters(self, info):
        return self.parameters or {}
    
    def resolve_metrics(self, info):
        return self.metrics or {}
    
    def resolve_equity_curve(self, info):
        """Convert JSON array to GraphQL list of EquityPointType"""
        if not self.equity_curve:
            return []
        return [
            EquityPointType(timestamp=point['timestamp'], equity=float(point['equity']))
            for point in self.equity_curve
        ]
    
    def resolve_trade_log(self, info):
        return self.trade_log or []


class RAHAMetricsType(graphene.ObjectType):
    """Aggregated performance metrics for a strategy"""
    strategy_version_id = graphene.ID(required=True)
    period = graphene.String(required=True)
    
    # Signal counts
    total_signals = graphene.Int()
    winning_signals = graphene.Int()
    losing_signals = graphene.Int()
    win_rate = graphene.Float()
    
    # P&L metrics
    total_pnl_dollars = graphene.Float()
    total_pnl_percent = graphene.Float()
    avg_pnl_per_signal = graphene.Float()
    
    # Risk metrics
    sharpe_ratio = graphene.Float()
    sortino_ratio = graphene.Float()
    max_drawdown = graphene.Float()
    max_drawdown_duration_days = graphene.Int()
    
    # Expectancy
    expectancy = graphene.Float(description="Expected value per trade (R-multiple)")
    avg_win = graphene.Float()
    avg_loss = graphene.Float()
    
    # R-multiples
    avg_r_multiple = graphene.Float()
    best_r_multiple = graphene.Float()
    worst_r_multiple = graphene.Float()

