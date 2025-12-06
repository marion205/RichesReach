"""
RAHA (RichesReach Adaptive Hybrid Algo) Models
Database models for strategy catalog, user settings, signals, and backtests
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import json
import uuid

User = get_user_model()


class Strategy(models.Model):
    """
    Strategy catalog - stores available trading strategies (ORB, Momentum, etc.)
    """
    CATEGORY_CHOICES = [
        ('MOMENTUM', 'Momentum'),
        ('REVERSAL', 'Reversal'),
        ('SWING', 'Swing'),
        ('FUTURES', 'Futures'),
        ('FOREX', 'Forex'),
        ('CRYPTO', 'Crypto'),
    ]
    
    MARKET_TYPE_CHOICES = [
        ('STOCKS', 'Stocks'),
        ('FUTURES', 'Futures'),
        ('FOREX', 'Forex'),
        ('CRYPTO', 'Crypto'),
        ('OPTIONS', 'Options'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(unique=True, max_length=100, db_index=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, db_index=True)
    description = models.TextField()
    influencer_ref = models.CharField(
        max_length=50,
        blank=True,
        help_text="Internal reference to influencer (e.g., 'pj_trades', 'ross_cameron')"
    )
    market_type = models.CharField(max_length=20, choices=MARKET_TYPE_CHOICES, db_index=True)
    timeframe_supported = models.JSONField(
        default=list,
        help_text="List of supported timeframes: ['1m', '5m', '15m', '1h']"
    )
    enabled = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'raha_strategies'
        verbose_name = 'RAHA Strategy'
        verbose_name_plural = 'RAHA Strategies'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.category})"


class StrategyVersion(models.Model):
    """
    Versioned strategy definitions - allows strategy evolution without breaking user settings
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name='versions')
    version = models.IntegerField(default=1)
    config_schema = models.JSONField(
        default=dict,
        help_text="JSON schema defining strategy parameters and allowed ranges"
    )
    logic_ref = models.CharField(
        max_length=100,
        help_text="Reference to implementation (e.g., 'ORB_v1', 'MOMENTUM_BREAKOUT_v1')"
    )
    is_default = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'raha_strategy_versions'
        unique_together = [['strategy', 'version']]
        verbose_name = 'Strategy Version'
        verbose_name_plural = 'Strategy Versions'
        ordering = ['strategy', '-version']
    
    def __str__(self):
        return f"{self.strategy.name} v{self.version}"


class UserStrategySettings(models.Model):
    """
    User-specific strategy configuration - which strategies are enabled, with what parameters
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='raha_strategy_settings')
    strategy_version = models.ForeignKey(StrategyVersion, on_delete=models.CASCADE, related_name='user_settings')
    parameters = models.JSONField(
        default=dict,
        help_text="User's parameter overrides (e.g., {'risk_per_trade': 0.01, 'orb_minutes': 15})"
    )
    enabled = models.BooleanField(default=True, db_index=True)
    auto_trade_enabled = models.BooleanField(
        default=False,
        help_text="If true, signals will auto-execute (requires risk limits)"
    )
    max_daily_loss_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Daily loss limit (e.g., 2.0 for 2%)"
    )
    max_concurrent_positions = models.IntegerField(
        default=3,
        help_text="Maximum concurrent positions for this strategy"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'raha_user_strategy_settings'
        unique_together = [['user', 'strategy_version']]
        verbose_name = 'User Strategy Settings'
        verbose_name_plural = 'User Strategy Settings'
        indexes = [
            models.Index(fields=['user', 'enabled']),
            models.Index(fields=['strategy_version', 'enabled']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.strategy_version.strategy.name}"


class RAHASignal(models.Model):
    """
    RAHA-generated trading signals - entries, exits, TP/SL levels
    """
    SIGNAL_TYPE_CHOICES = [
        ('ENTRY_LONG', 'Entry Long'),
        ('ENTRY_SHORT', 'Entry Short'),
        ('EXIT', 'Exit'),
        ('TAKE_PROFIT', 'Take Profit'),
        ('STOP_LOSS', 'Stop Loss'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='raha_signals',
        null=True,
        blank=True,
        help_text="Null for global signals, set for personalized signals"
    )
    strategy_version = models.ForeignKey(StrategyVersion, on_delete=models.CASCADE, related_name='signals')
    symbol = models.CharField(max_length=10, db_index=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    timeframe = models.CharField(max_length=10, default='5m')
    signal_type = models.CharField(max_length=20, choices=SIGNAL_TYPE_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stop_loss = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    take_profit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    confidence_score = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal('0.5'),
        help_text="ML confidence score (0-1)"
    )
    meta = models.JSONField(
        default=dict,
        help_text="Additional signal metadata (candle pattern, ORB range, zone info, etc.)"
    )
    
    # Link to existing signal tracking (optional)
    day_trading_signal = models.ForeignKey(
        'core.DayTradingSignal',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='raha_signals',
        help_text="Link to DayTradingSignal if this was generated from day trading engine"
    )
    
    class Meta:
        db_table = 'raha_signals'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'strategy_version']),
            models.Index(fields=['symbol', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['strategy_version', 'signal_type']),
        ]
        verbose_name = 'RAHA Signal'
        verbose_name_plural = 'RAHA Signals'
    
    def __str__(self):
        return f"{self.symbol} {self.signal_type} ({self.strategy_version.strategy.name}) - {self.timestamp}"


class RAHABacktestRun(models.Model):
    """
    Backtest execution results - stores equity curves, metrics, trade logs
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='raha_backtests')
    strategy_version = models.ForeignKey(StrategyVersion, on_delete=models.CASCADE, related_name='backtests')
    symbol = models.CharField(max_length=10, db_index=True)
    timeframe = models.CharField(max_length=10, default='5m')
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    parameters = models.JSONField(
        default=dict,
        help_text="Parameters used for this backtest"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    
    # Results
    metrics = models.JSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="Performance metrics: {win_rate, sharpe, max_drawdown, expectancy, etc.}"
    )
    equity_curve = models.JSONField(
        default=list,
        null=True,
        blank=True,
        help_text="Array of {timestamp, equity} points"
    )
    trade_log = models.JSONField(
        default=list,
        null=True,
        blank=True,
        help_text="Array of executed trades"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'raha_backtest_runs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['strategy_version', 'status']),
            models.Index(fields=['symbol', 'start_date', 'end_date']),
        ]
        verbose_name = 'RAHA Backtest Run'
        verbose_name_plural = 'RAHA Backtest Runs'
    
    def __str__(self):
        return f"{self.strategy_version.strategy.name} on {self.symbol} ({self.start_date} to {self.end_date}) - {self.status}"

