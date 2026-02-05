# options_models.py
"""
Database models for Options Portfolio tracking.
Supports multi-leg strategies with Greek aggregation.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import json

User = get_user_model()


class OptionsPortfolio(models.Model):
    """
    Top-level container for a user's options positions.
    Tracks aggregate Greeks and account equity.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='options_portfolio'
    )
    account_equity = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Total account value (cash + positions)"
    )
    
    # Aggregate Greeks (sum across all open positions)
    total_delta = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    total_vega = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    total_theta = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    total_gamma = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    
    # Risk metrics
    total_risk_dollars = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Sum of max_loss across all positions"
    )
    total_positions_count = models.IntegerField(default=0)
    
    # Experience level (governs position sizing)
    experience_level = models.CharField(
        max_length=20,
        choices=[
            ('basic', 'Basic'),
            ('intermediate', 'Intermediate'),
            ('pro', 'Professional'),
        ],
        default='basic'
    )
    
    # Risk appetite (0.0-1.0)
    risk_appetite = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.5,
        help_text="Risk tolerance: 0.0 (conservative) to 1.0 (aggressive)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Options Portfolio"
        verbose_name_plural = "Options Portfolios"
    
    def __str__(self):
        return f"{self.user.email} Options Portfolio (${self.account_equity})"
    
    def recalculate_greeks(self):
        """Aggregate Greeks from all open positions"""
        open_positions = self.positions.filter(is_closed=False)
        
        self.total_delta = sum(p.position_delta for p in open_positions)
        self.total_vega = sum(p.position_vega for p in open_positions)
        self.total_theta = sum(p.position_theta for p in open_positions)
        self.total_gamma = sum(p.position_gamma for p in open_positions)
        self.total_risk_dollars = sum(p.max_loss for p in open_positions)
        self.total_positions_count = open_positions.count()
        self.save()


class OptionsPosition(models.Model):
    """
    Single options position (can be multi-leg strategy).
    Stores legs as JSON, Greeks per position, and P&L tracking.
    """
    portfolio = models.ForeignKey(
        OptionsPortfolio,
        on_delete=models.CASCADE,
        related_name='positions'
    )
    ticker = models.CharField(max_length=10, db_index=True)
    sector = models.CharField(max_length=50, blank=True, default='Unknown')
    strategy_type = models.CharField(
        max_length=50,
        help_text="e.g., IRON_CONDOR, BULL_CALL_SPREAD, LONG_STRADDLE"
    )
    
    # Trade details
    legs = models.JSONField(
        help_text="Array of legs: [{type: 'call', strike: 100, expiry: '2026-03-20', contracts: 2, side: 'buy'}]"
    )
    contracts = models.IntegerField(
        default=1,
        help_text="Number of spreads/straddles (multiply legs by this)"
    )
    entry_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Net credit/debit at entry (positive = credit)"
    )
    current_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Current mark price (updated via data feed)"
    )
    
    # Greeks (per position, not per contract)
    position_delta = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    position_vega = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    position_theta = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    position_gamma = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    
    # Risk metrics
    max_profit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Max gain in dollars"
    )
    max_loss = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Max loss in dollars (risk amount)"
    )
    probability_of_profit = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="PoP as percentage (e.g., 66.00 for 66%)"
    )
    
    # P&L tracking
    realized_pnl = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Locked-in profit/loss after close"
    )
    unrealized_pnl = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Current P&L (updated via mark price)"
    )
    
    # Metadata
    regime_at_entry = models.CharField(
        max_length=30,
        blank=True,
        help_text="Market regime when trade was opened (e.g., MEAN_REVERSION)"
    )
    edge_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Router composite score at entry (0-100)"
    )
    flight_manual = models.TextField(
        blank=True,
        help_text="JSON serialized FlightManual for reference"
    )
    
    # Status
    is_closed = models.BooleanField(default=False, db_index=True)
    opened_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-opened_at']
        verbose_name = "Options Position"
        verbose_name_plural = "Options Positions"
    
    def __str__(self):
        status = "CLOSED" if self.is_closed else "OPEN"
        return f"{self.ticker} {self.strategy_type} ({self.contracts}x) - {status}"
    
    def update_current_price_and_pnl(self, new_mark_price):
        """Update mark price and recalculate unrealized P&L"""
        self.current_price = new_mark_price
        # For credit spreads: entry_price is positive (credit received)
        # Unrealized P&L = entry_price - current_price (you want price to drop)
        # For debit spreads: entry_price is negative (debit paid)
        # Unrealized P&L = current_price - abs(entry_price) (you want price to rise)
        if self.entry_price > 0:
            # Credit spread
            self.unrealized_pnl = (self.entry_price - new_mark_price) * 100 * self.contracts
        else:
            # Debit spread
            self.unrealized_pnl = (new_mark_price - abs(self.entry_price)) * 100 * self.contracts
        self.save()
    
    def close_position(self, exit_price):
        """Mark position as closed and calculate realized P&L"""
        self.is_closed = True
        self.closed_at = timezone.now()
        self.current_price = exit_price
        
        if self.entry_price > 0:
            # Credit spread: profit if price drops
            self.realized_pnl = (self.entry_price - exit_price) * 100 * self.contracts
        else:
            # Debit spread: profit if price rises
            self.realized_pnl = (exit_price - abs(self.entry_price)) * 100 * self.contracts
        
        self.unrealized_pnl = 0
        self.save()
        
        # Recalculate portfolio Greeks
        self.portfolio.recalculate_greeks()
    
    def get_legs_parsed(self):
        """Return legs as Python list (parse JSON)"""
        if isinstance(self.legs, str):
            return json.loads(self.legs)
        return self.legs
    
    def get_sector_exposure(self):
        """Return sector exposure as fraction of portfolio equity"""
        if self.portfolio.account_equity == 0:
            return 0.0
        sector_risk = sum(
            p.max_loss for p in self.portfolio.positions.filter(
                sector=self.sector, is_closed=False
            )
        )
        return float(sector_risk / self.portfolio.account_equity)
    
    def get_ticker_exposure(self):
        """Return ticker exposure as fraction of portfolio equity"""
        if self.portfolio.account_equity == 0:
            return 0.0
        ticker_risk = sum(
            p.max_loss for p in self.portfolio.positions.filter(
                ticker=self.ticker, is_closed=False
            )
        )
        return float(ticker_risk / self.portfolio.account_equity)


class OptionsRegimeSnapshot(models.Model):
    """
    Cached market regime for a ticker.
    Updated hourly by scheduled task.
    """
    ticker = models.CharField(max_length=10, unique=True, db_index=True)
    regime = models.CharField(
        max_length=30,
        help_text="e.g., MEAN_REVERSION, TREND_UP, CRASH_PANIC"
    )
    regime_confidence = models.CharField(
        max_length=10,
        default='MEDIUM',
        help_text="HIGH, MEDIUM, LOW"
    )
    iv_rank = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="IV percentile (0-100)"
    )
    regime_description = models.TextField(
        blank=True,
        help_text="Human-readable regime context"
    )
    
    # Metadata
    last_updated = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Options Regime Snapshot"
        verbose_name_plural = "Options Regime Snapshots"
    
    def __str__(self):
        return f"{self.ticker}: {self.regime} ({self.regime_confidence})"
    
    def is_stale(self, hours=1):
        """Check if snapshot is older than N hours"""
        return (timezone.now() - self.last_updated).total_seconds() > (hours * 3600)
