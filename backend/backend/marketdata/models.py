# marketdata/models.py
from django.db import models
from django.utils import timezone

class Equity(models.Model):
    """Core equity information"""
    symbol = models.CharField(max_length=16, unique=True, db_index=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    exchange = models.CharField(max_length=32, null=True, blank=True)
    sector = models.CharField(max_length=64, null=True, blank=True)
    industry = models.CharField(max_length=128, null=True, blank=True)
    market_cap = models.BigIntegerField(null=True, blank=True)
    pe_ratio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    dividend_yield = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'marketdata_equity'
        verbose_name_plural = 'Equities'

    def __str__(self):
        return f"{self.symbol} - {self.name or 'Unknown'}"

class DailyBar(models.Model):
    """Daily OHLCV data"""
    symbol = models.CharField(max_length=16, db_index=True)
    date = models.DateField(db_index=True)
    open = models.DecimalField(max_digits=12, decimal_places=4)
    high = models.DecimalField(max_digits=12, decimal_places=4)
    low = models.DecimalField(max_digits=12, decimal_places=4)
    close = models.DecimalField(max_digits=12, decimal_places=4)
    volume = models.BigIntegerField()
    adjusted_close = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'marketdata_daily_bar'
        unique_together = ("symbol", "date")
        indexes = [
            models.Index(fields=['symbol', 'date']),
        ]

    def __str__(self):
        return f"{self.symbol} {self.date}: ${self.close}"

class Quote(models.Model):
    """Real-time quote data with provider tracking"""
    symbol = models.CharField(max_length=16, db_index=True)
    price = models.DecimalField(max_digits=12, decimal_places=4)
    change = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    change_percent = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)
    high = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    low = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    open = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    provider = models.CharField(max_length=32)  # 'polygon', 'finnhub', etc.
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'marketdata_quote'
        indexes = [
            models.Index(fields=['symbol', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.symbol}: ${self.price} ({self.provider})"

class OptionContract(models.Model):
    """Options contract data"""
    symbol = models.CharField(max_length=32, db_index=True)  # e.g., AAPL240315C00150000
    underlying = models.CharField(max_length=16, db_index=True)  # e.g., AAPL
    contract_type = models.CharField(max_length=4, choices=[('CALL', 'Call'), ('PUT', 'Put')])
    strike = models.DecimalField(max_digits=10, decimal_places=2)
    expiration = models.DateField()
    bid = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    ask = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    last_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    volume = models.IntegerField(null=True, blank=True)
    open_interest = models.IntegerField(null=True, blank=True)
    implied_volatility = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    delta = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    gamma = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    theta = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    vega = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    provider = models.CharField(max_length=32)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'marketdata_option_contract'
        unique_together = ("symbol", "provider")
        indexes = [
            models.Index(fields=['underlying', 'expiration']),
            models.Index(fields=['underlying', 'contract_type']),
        ]

    def __str__(self):
        return f"{self.symbol} {self.contract_type} ${self.strike}"

class ProviderHealth(models.Model):
    """Track provider health and rate limits"""
    provider = models.CharField(max_length=32, unique=True)
    is_healthy = models.BooleanField(default=True)
    last_success = models.DateTimeField(null=True, blank=True)
    last_failure = models.DateTimeField(null=True, blank=True)
    failure_count = models.IntegerField(default=0)
    rate_limit_remaining = models.IntegerField(null=True, blank=True)
    rate_limit_reset = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'marketdata_provider_health'

    def __str__(self):
        status = "Healthy" if self.is_healthy else "Unhealthy"
        return f"{self.provider}: {status}"