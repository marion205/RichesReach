from django.db import models
from django.conf import settings
from django.utils import timezone

class CustomBenchmark(models.Model):
    """Custom benchmark portfolio created by users"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='custom_benchmarks')
    name = models.CharField(max_length=200, help_text="Name of the custom benchmark")
    description = models.TextField(blank=True, help_text="Description of the benchmark strategy")
    is_active = models.BooleanField(default=True, help_text="Whether the benchmark is active")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_custom_benchmark'
        ordering = ['-created_at']
        unique_together = ['user', 'name']
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"
    
    @property
    def total_holdings(self):
        """Get total number of holdings in this benchmark"""
        return self.holdings.count()
    
    @property
    def total_weight(self):
        """Get total weight of all holdings (should be 1.0)"""
        return sum(holding.weight for holding in self.holdings.all())

class CustomBenchmarkHolding(models.Model):
    """Individual holding within a custom benchmark"""
    
    benchmark = models.ForeignKey(CustomBenchmark, on_delete=models.CASCADE, related_name='holdings')
    symbol = models.CharField(max_length=20, help_text="Stock symbol (e.g., AAPL)")
    weight = models.DecimalField(max_digits=5, decimal_places=4, help_text="Weight in portfolio (0.0000 to 1.0000)")
    name = models.CharField(max_length=200, blank=True, help_text="Company name")
    sector = models.CharField(max_length=100, blank=True, help_text="Sector classification")
    description = models.TextField(blank=True, help_text="Additional description")
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'core_custom_benchmark_holding'
        ordering = ['-weight', 'symbol']
        unique_together = ['benchmark', 'symbol']
    
    def __str__(self):
        return f"{self.benchmark.name} - {self.symbol} ({self.weight:.2%})"
    
    def clean(self):
        """Validate the holding data"""
        from django.core.exceptions import ValidationError
        
        if self.weight <= 0 or self.weight > 1:
            raise ValidationError("Weight must be between 0 and 1")
        
        if not self.symbol:
            raise ValidationError("Symbol is required")

class BenchmarkPerformanceHistory(models.Model):
    """Historical performance data for benchmarks"""
    
    benchmark_type = models.CharField(max_length=50, choices=[
        ('standard', 'Standard Benchmark'),
        ('custom', 'Custom Benchmark'),
    ])
    benchmark_id = models.CharField(max_length=100, help_text="ID of the benchmark (symbol or custom benchmark ID)")
    benchmark_name = models.CharField(max_length=200, help_text="Name of the benchmark")
    timeframe = models.CharField(max_length=10, choices=[
        ('1D', '1 Day'),
        ('1W', '1 Week'),
        ('1M', '1 Month'),
        ('3M', '3 Months'),
        ('1Y', '1 Year'),
        ('All', 'All Time'),
    ])
    date = models.DateField(help_text="Date of the performance data")
    value = models.DecimalField(max_digits=15, decimal_places=4, help_text="Benchmark value on this date")
    return_percent = models.DecimalField(max_digits=8, decimal_places=4, help_text="Daily return percentage")
    volume = models.BigIntegerField(null=True, blank=True, help_text="Trading volume")
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'core_benchmark_performance_history'
        ordering = ['-date', 'benchmark_id']
        unique_together = ['benchmark_id', 'timeframe', 'date']
        indexes = [
            models.Index(fields=['benchmark_id', 'timeframe', 'date']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"{self.benchmark_name} ({self.timeframe}) - {self.date}: {self.value}"

class BenchmarkAnalytics(models.Model):
    """Advanced analytics data for benchmarks"""
    
    benchmark_type = models.CharField(max_length=50, choices=[
        ('standard', 'Standard Benchmark'),
        ('custom', 'Custom Benchmark'),
    ])
    benchmark_id = models.CharField(max_length=100, help_text="ID of the benchmark")
    benchmark_name = models.CharField(max_length=200, help_text="Name of the benchmark")
    timeframe = models.CharField(max_length=10, choices=[
        ('1D', '1 Day'),
        ('1W', '1 Week'),
        ('1M', '1 Month'),
        ('3M', '3 Months'),
        ('1Y', '1 Year'),
        ('All', 'All Time'),
    ])
    calculation_date = models.DateTimeField(default=timezone.now)
    
    # Basic metrics
    total_return_percent = models.DecimalField(max_digits=8, decimal_places=4, help_text="Total return percentage")
    volatility = models.DecimalField(max_digits=8, decimal_places=4, help_text="Annualized volatility")
    sharpe_ratio = models.DecimalField(max_digits=8, decimal_places=4, help_text="Sharpe ratio")
    max_drawdown = models.DecimalField(max_digits=8, decimal_places=4, help_text="Maximum drawdown percentage")
    
    # Advanced metrics
    beta = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True, help_text="Beta relative to market")
    alpha = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True, help_text="Alpha")
    information_ratio = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True, help_text="Information ratio")
    sortino_ratio = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True, help_text="Sortino ratio")
    calmar_ratio = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True, help_text="Calmar ratio")
    
    # Risk metrics
    var_95 = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True, help_text="95% Value at Risk")
    var_99 = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True, help_text="99% Value at Risk")
    cvar_95 = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True, help_text="95% Conditional VaR")
    cvar_99 = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True, help_text="99% Conditional VaR")
    
    # Distribution metrics
    skewness = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True, help_text="Skewness")
    kurtosis = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True, help_text="Kurtosis")
    excess_kurtosis = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True, help_text="Excess kurtosis")
    
    class Meta:
        db_table = 'core_benchmark_analytics'
        ordering = ['-calculation_date', 'benchmark_id']
        unique_together = ['benchmark_id', 'timeframe', 'calculation_date']
        indexes = [
            models.Index(fields=['benchmark_id', 'timeframe']),
            models.Index(fields=['calculation_date']),
        ]
    
    def __str__(self):
        return f"{self.benchmark_name} Analytics ({self.timeframe}) - {self.calculation_date.date()}"

class BenchmarkComparison(models.Model):
    """Comparison between portfolio and benchmark performance"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='benchmark_comparisons')
    portfolio_id = models.CharField(max_length=100, help_text="Portfolio identifier")
    benchmark_id = models.CharField(max_length=100, help_text="Benchmark identifier")
    benchmark_name = models.CharField(max_length=200, help_text="Benchmark name")
    timeframe = models.CharField(max_length=10, choices=[
        ('1D', '1 Day'),
        ('1W', '1 Week'),
        ('1M', '1 Month'),
        ('3M', '3 Months'),
        ('1Y', '1 Year'),
        ('All', 'All Time'),
    ])
    comparison_date = models.DateTimeField(default=timezone.now)
    
    # Performance comparison
    portfolio_return = models.DecimalField(max_digits=8, decimal_places=4, help_text="Portfolio return percentage")
    benchmark_return = models.DecimalField(max_digits=8, decimal_places=4, help_text="Benchmark return percentage")
    excess_return = models.DecimalField(max_digits=8, decimal_places=4, help_text="Excess return percentage")
    
    # Risk comparison
    portfolio_volatility = models.DecimalField(max_digits=8, decimal_places=4, help_text="Portfolio volatility")
    benchmark_volatility = models.DecimalField(max_digits=8, decimal_places=4, help_text="Benchmark volatility")
    tracking_error = models.DecimalField(max_digits=8, decimal_places=4, help_text="Tracking error")
    
    # Risk-adjusted metrics
    portfolio_sharpe = models.DecimalField(max_digits=8, decimal_places=4, help_text="Portfolio Sharpe ratio")
    benchmark_sharpe = models.DecimalField(max_digits=8, decimal_places=4, help_text="Benchmark Sharpe ratio")
    information_ratio = models.DecimalField(max_digits=8, decimal_places=4, help_text="Information ratio")
    
    # Correlation metrics
    beta = models.DecimalField(max_digits=8, decimal_places=4, help_text="Beta")
    correlation = models.DecimalField(max_digits=8, decimal_places=4, help_text="Correlation coefficient")
    r_squared = models.DecimalField(max_digits=8, decimal_places=4, help_text="R-squared")
    
    class Meta:
        db_table = 'core_benchmark_comparison'
        ordering = ['-comparison_date', 'user']
        unique_together = ['user', 'portfolio_id', 'benchmark_id', 'timeframe', 'comparison_date']
        indexes = [
            models.Index(fields=['user', 'benchmark_id', 'timeframe']),
            models.Index(fields=['comparison_date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.benchmark_name} ({self.timeframe}) - {self.comparison_date.date()}"
