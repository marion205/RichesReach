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
    regimeMultiplier = graphene.Float(description="Position size multiplier based on current market regime")
    regimeNarration = graphene.String(description="Human-readable explanation of current regime")
    globalRegime = graphene.String(description="Current global market regime")
    localContext = graphene.String(description="Local context for this symbol")
    
    def resolve_meta(self, info):
        """Return meta as JSON"""
        return self.meta or {}
    
    def resolve_regimeMultiplier(self, info):
        """Get position size multiplier based on regime"""
        # ✅ Check meta first for mock data
        if self.meta and 'regime_multiplier' in self.meta:
            return float(self.meta['regime_multiplier'])
        
        try:
            from .raha_regime_integration import raha_regime_integration
            multiplier = raha_regime_integration.get_position_multiplier(self)
            return float(multiplier)
        except Exception:
            return 1.0
    
    def resolve_regimeNarration(self, info):
        """Get human-readable regime narration"""
        # ✅ Check meta first for mock data
        if self.meta and 'regime_narration' in self.meta:
            return str(self.meta['regime_narration'])
        
        try:
            from .raha_regime_integration import raha_regime_integration
            narration = raha_regime_integration.get_regime_narration(self.symbol)
            if narration:
                return narration.get('action_summary', '')
        except Exception:
            pass
        return ''
    
    def resolve_globalRegime(self, info):
        """Get current global market regime"""
        # ✅ Check meta first for mock data
        if self.meta and 'regime_global' in self.meta:
            return str(self.meta['regime_global'])
        
        try:
            from .raha_regime_integration import raha_regime_integration
            regime_analysis = raha_regime_integration.get_regime_analysis(self.symbol)
            if regime_analysis:
                return regime_analysis.get('global_regime', 'NEUTRAL')
        except Exception:
            pass
        return 'NEUTRAL'
    
    def resolve_localContext(self, info):
        """Get local context for this symbol"""
        # ✅ Check meta first for mock data
        if self.meta and 'regime_local' in self.meta:
            return str(self.meta['regime_local'])
        
        try:
            from .raha_regime_integration import raha_regime_integration
            regime_analysis = raha_regime_integration.get_regime_analysis(self.symbol)
            if regime_analysis:
                return regime_analysis.get('local_context', 'NORMAL')
        except Exception:
            pass
        return 'NORMAL'


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

