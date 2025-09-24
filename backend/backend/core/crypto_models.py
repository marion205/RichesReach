"""
Crypto trading models for RichesReach
Supports top 15-20 liquid coins with SBLOC integration
"""

from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal
import json

User = get_user_model()


class Cryptocurrency(models.Model):
    """Supported cryptocurrencies"""
    symbol = models.CharField(max_length=10, unique=True)  # BTC, ETH, SOL, etc.
    name = models.CharField(max_length=100)  # Bitcoin, Ethereum, Solana
    coingecko_id = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    is_staking_available = models.BooleanField(default=False)
    min_trade_amount = models.DecimalField(max_digits=20, decimal_places=8, default=0.0001)
    precision = models.IntegerField(default=8)  # decimal places for display
    
    # Risk profile
    volatility_tier = models.CharField(
        max_length=20,
        choices=[
            ('LOW', 'Low Volatility'),
            ('MEDIUM', 'Medium Volatility'), 
            ('HIGH', 'High Volatility'),
            ('EXTREME', 'Extreme Volatility')
        ],
        default='HIGH'
    )
    
    # Compliance
    is_sec_compliant = models.BooleanField(default=False)
    regulatory_status = models.CharField(max_length=50, default='UNKNOWN')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'crypto_currencies'
        verbose_name = 'Cryptocurrency'
        verbose_name_plural = 'Cryptocurrencies'
    
    def __str__(self):
        return f"{self.symbol} - {self.name}"


class CryptoPrice(models.Model):
    """Real-time crypto price data"""
    cryptocurrency = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE, related_name='prices')
    price_usd = models.DecimalField(max_digits=20, decimal_places=8)
    price_btc = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    volume_24h = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    market_cap = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    price_change_24h = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    price_change_percentage_24h = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    
    # Technical indicators
    rsi_14 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    macd = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    bollinger_upper = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    bollinger_lower = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    
    # ML features
    volatility_7d = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    volatility_30d = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    momentum_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    sentiment_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'crypto_prices'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['cryptocurrency', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.cryptocurrency.symbol}: ${self.price_usd}"


class CryptoPortfolio(models.Model):
    """User's crypto holdings"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='crypto_portfolio')
    total_value_usd = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_cost_basis = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_pnl = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_pnl_percentage = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    
    # Risk metrics
    portfolio_volatility = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    sharpe_ratio = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    max_drawdown = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    
    # Diversification
    diversification_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    top_holding_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'crypto_portfolios'
    
    def __str__(self):
        return f"{self.user.username}'s Crypto Portfolio"


class CryptoHolding(models.Model):
    """Individual crypto holdings"""
    portfolio = models.ForeignKey(CryptoPortfolio, on_delete=models.CASCADE, related_name='holdings')
    cryptocurrency = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=20, decimal_places=8)
    average_cost = models.DecimalField(max_digits=20, decimal_places=8)
    current_price = models.DecimalField(max_digits=20, decimal_places=8)
    current_value = models.DecimalField(max_digits=20, decimal_places=2)
    unrealized_pnl = models.DecimalField(max_digits=20, decimal_places=2)
    unrealized_pnl_percentage = models.DecimalField(max_digits=10, decimal_places=4)
    
    # Staking info
    staked_quantity = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    staking_rewards = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    staking_apy = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # SBLOC integration
    is_collateralized = models.BooleanField(default=False)
    collateral_value = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    loan_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'crypto_holdings'
        unique_together = ['portfolio', 'cryptocurrency']
        indexes = [
            models.Index(fields=['portfolio', 'cryptocurrency']),
        ]
    
    def __str__(self):
        return f"{self.quantity} {self.cryptocurrency.symbol} @ ${self.average_cost}"


class CryptoTrade(models.Model):
    """Crypto trading history"""
    TRADE_TYPES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
        ('STAKING_REWARD', 'Staking Reward'),
        ('AIRDROP', 'Airdrop'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='crypto_trades')
    cryptocurrency = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE)
    trade_type = models.CharField(max_length=20, choices=TRADE_TYPES)
    quantity = models.DecimalField(max_digits=20, decimal_places=8)
    price_per_unit = models.DecimalField(max_digits=20, decimal_places=8)
    total_amount = models.DecimalField(max_digits=20, decimal_places=2)
    fees = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    
    # Order details
    order_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, default='COMPLETED')
    execution_time = models.DateTimeField(auto_now_add=True)
    
    # SBLOC integration
    is_sbloc_funded = models.BooleanField(default=False)
    sbloc_loan_id = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        db_table = 'crypto_trades'
        ordering = ['-execution_time']
        indexes = [
            models.Index(fields=['user', '-execution_time']),
            models.Index(fields=['cryptocurrency', '-execution_time']),
        ]
    
    def __str__(self):
        return f"{self.trade_type} {self.quantity} {self.cryptocurrency.symbol} @ ${self.price_per_unit}"


class CryptoMLPrediction(models.Model):
    """ML predictions for crypto price movements"""
    cryptocurrency = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE, related_name='predictions')
    prediction_type = models.CharField(
        max_length=20,
        choices=[
            ('BIG_UP_DAY', 'Big Up Day'),
            ('BIG_DOWN_DAY', 'Big Down Day'),
            ('VOLATILITY_SPIKE', 'Volatility Spike'),
            ('TREND_REVERSAL', 'Trend Reversal'),
        ]
    )
    
    # Prediction details
    probability = models.DecimalField(max_digits=5, decimal_places=4)  # 0.0000 to 1.0000
    confidence_level = models.CharField(
        max_length=20,
        choices=[
            ('LOW', 'Low Confidence'),
            ('MEDIUM', 'Medium Confidence'),
            ('HIGH', 'High Confidence'),
        ]
    )
    
    # Features used
    features_used = models.JSONField(default=dict)
    model_version = models.CharField(max_length=50, default='v1.0')
    
    # Timeframe
    prediction_horizon_hours = models.IntegerField(default=24)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    # Results (filled after prediction period)
    was_correct = models.BooleanField(null=True, blank=True)
    actual_return = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    
    class Meta:
        db_table = 'crypto_ml_predictions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['cryptocurrency', '-created_at']),
            models.Index(fields=['prediction_type', '-created_at']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.cryptocurrency.symbol} {self.prediction_type}: {self.probability:.2%}"


class CryptoSBLOCLoan(models.Model):
    """SBLOC loans backed by crypto collateral"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='crypto_sbloc_loans')
    cryptocurrency = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE)
    collateral_quantity = models.DecimalField(max_digits=20, decimal_places=8)
    collateral_value_at_loan = models.DecimalField(max_digits=20, decimal_places=2)
    loan_amount = models.DecimalField(max_digits=20, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=4)  # 0.0500 = 5%
    
    # Collateral requirements
    maintenance_margin = models.DecimalField(max_digits=5, decimal_places=4, default=0.5)  # 50%
    liquidation_threshold = models.DecimalField(max_digits=5, decimal_places=4, default=0.4)  # 40%
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('ACTIVE', 'Active'),
            ('LIQUIDATED', 'Liquidated'),
            ('REPAID', 'Repaid'),
            ('WARNING', 'Margin Call Warning'),
        ],
        default='ACTIVE'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'crypto_sbloc_loans'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"SBLOC Loan: {self.loan_amount} backed by {self.collateral_quantity} {self.cryptocurrency.symbol}"


# --- AAVE-style lending models ---------------------------------------------

class LendingReserve(models.Model):
    """
    Per-asset risk parameters & dynamic APYs (AAVE-ish)
    """
    cryptocurrency = models.OneToOneField(
        Cryptocurrency, on_delete=models.CASCADE, related_name="reserve"
    )
    # Risk params (fractions: 0.80 = 80%)
    ltv = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal("0.70"))
    liquidation_threshold = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal("0.75"))
    liquidation_bonus = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal("0.0500"))
    reserve_factor = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal("0.1000"))

    # Capabilities
    can_borrow = models.BooleanField(default=True)
    can_be_collateral = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    # Live rates (optional; you can refresh from oracle/adapter)
    supply_apy = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    variable_borrow_apy = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    stable_borrow_apy = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "defi_lending_reserves"
        verbose_name = "Lending Reserve"
        indexes = [
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"Reserve({self.cryptocurrency.symbol})"


class SupplyPosition(models.Model):
    """
    User supplies asset into the reserve; may toggle 'use_as_collateral'.
    Denominated in ASSET UNITS.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="defi_supplies")
    reserve = models.ForeignKey(LendingReserve, on_delete=models.CASCADE, related_name="supplies")
    quantity = models.DecimalField(max_digits=28, decimal_places=10, default=0)
    use_as_collateral = models.BooleanField(default=True)

    # snapshot fields for convenience (optional)
    usd_value_cached = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "defi_supply_positions"
        unique_together = ["user", "reserve"]
        indexes = [
            models.Index(fields=["user", "reserve"]),
        ]

    def __str__(self):
        return f"{self.user_id} supplies {self.quantity} {self.reserve.cryptocurrency.symbol}"


class BorrowPosition(models.Model):
    """
    User borrows an asset (variable or stable). Denominated in ASSET UNITS.
    """
    RATE_MODE_CHOICES = [
        ("VARIABLE", "Variable"),
        ("STABLE", "Stable"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="defi_borrows")
    reserve = models.ForeignKey(LendingReserve, on_delete=models.CASCADE, related_name="borrows")
    amount = models.DecimalField(max_digits=28, decimal_places=10, default=0)  # in asset units
    rate_mode = models.CharField(max_length=10, choices=RATE_MODE_CHOICES, default="VARIABLE")
    apy_at_open = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)

    usd_value_cached = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    opened_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "defi_borrow_positions"
        indexes = [
            models.Index(fields=["user", "reserve", "is_active"]),
            models.Index(fields=["opened_at"]),
        ]

    def __str__(self):
        return f"{self.user_id} borrows {self.amount} {self.reserve.cryptocurrency.symbol} ({self.rate_mode})"


class CryptoEducationProgress(models.Model):
    """Track user's crypto education progress"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='crypto_education')
    module_name = models.CharField(max_length=100)
    module_type = models.CharField(
        max_length=20,
        choices=[
            ('BASIC', 'Basic Concepts'),
            ('TRADING', 'Trading Strategies'),
            ('DEFI', 'DeFi Protocols'),
            ('RISK', 'Risk Management'),
            ('DEFI_LENDING', 'DeFi Lending'),
        ]
    )
    
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Quiz scores
    quiz_attempts = models.IntegerField(default=0)
    best_quiz_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'crypto_education_progress'
        unique_together = ['user', 'module_name']
    
    def __str__(self):
        return f"{self.user.username} - {self.module_name}: {self.progress_percentage}%"
