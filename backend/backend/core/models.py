"""
Models for RichesReach Application
Includes User model, institutional features, and point-in-time data
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import json

class User(AbstractUser):
    """Custom User model for RichesReach"""
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255, default='User')
    username = models.CharField(max_length=150, unique=True, default='user')
    profile_pic = models.URLField(blank=True, null=True, help_text="URL to user's profile picture")
    
    # Add first_name and last_name fields that are expected by migrations
    first_name = models.CharField(max_length=150, blank=True, default='')
    last_name = models.CharField(max_length=150, blank=True, default='')
    
    # Add date_joined field that is expected by GraphQL
    date_joined = models.DateTimeField(default=timezone.now)
    
    # Additional fields for institutional features
    hasPremiumAccess = models.BooleanField(default=False)
    subscriptionTier = models.CharField(max_length=20, default='BASIC', choices=[
        ('BASIC', 'Basic'),
        ('PREMIUM', 'Premium'),
        ('ENTERPRISE', 'Enterprise'),
    ])
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'name']
    
    def __str__(self):
        return self.email

class TickerFollow(models.Model):
    """Model for users following ticker symbols"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ticker_follows')
    symbol = models.CharField(max_length=10, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'symbol']
        indexes = [
            models.Index(fields=['user', 'symbol']),
            models.Index(fields=['symbol']),
        ]
    
    def __str__(self):
        return f"{self.user.email} follows {self.symbol}"

# Existing models from the application
class Post(models.Model):
    """Post model for social features"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Post by {self.user.email}"

class Comment(models.Model):
    """Comment model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Comment by {self.user.email}"

class Like(models.Model):
    """Like model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'post']
    
    def __str__(self):
        return f"Like by {self.user.email}"

class Follow(models.Model):
    """Follow model for user relationships"""
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['follower', 'following']
    
    def __str__(self):
        return f"{self.follower.email} follows {self.following.email}"

class ChatSession(models.Model):
    """Chat session model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Chat session for {self.user.email}"

class ChatMessage(models.Model):
    """Chat message model"""
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    is_user = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Message in session {self.session.id}"

class Source(models.Model):
    """Source model for data sources"""
    name = models.CharField(max_length=100, default='Unknown Source')
    url = models.URLField(default='https://example.com')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Stock(models.Model):
    """Stock model"""
    symbol = models.CharField(max_length=10, unique=True)
    company_name = models.CharField(max_length=200)
    sector = models.CharField(max_length=100, default='Unknown')
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    market_cap = models.BigIntegerField(null=True, blank=True)
    pe_ratio = models.FloatField(null=True, blank=True)
    dividend_yield = models.FloatField(null=True, blank=True)
    debt_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    volatility = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    beginner_friendly_score = models.IntegerField(null=True, blank=True)
    dividend_score = models.IntegerField(null=True, blank=True, help_text="Dividend quality score (0-100)")
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.symbol} - {self.company_name}"

class StockData(models.Model):
    """Stock data model for historical data"""
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='stock_data')
    date = models.DateField()
    open_price = models.DecimalField(max_digits=10, decimal_places=2)
    high_price = models.DecimalField(max_digits=10, decimal_places=2)
    low_price = models.DecimalField(max_digits=10, decimal_places=2)
    close_price = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['stock', 'date']
    
    def __str__(self):
        return f"{self.stock.symbol} data for {self.date}"

class Watchlist(models.Model):
    """Watchlist model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlists')
    name = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField()
    is_public = models.BooleanField(default=False)
    is_shared = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email}'s {self.name} watchlist"

class WatchlistItem(models.Model):
    """Watchlist item model"""
    watchlist = models.ForeignKey(Watchlist, on_delete=models.CASCADE, related_name='items')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    notes = models.TextField()
    target_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['watchlist', 'stock']
    
    def __str__(self):
        return f"{self.stock.symbol} in {self.watchlist.name}"

class Portfolio(models.Model):
    """Portfolio model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolios')
    name = models.CharField(max_length=100, default='My Portfolio')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email}'s {self.name} portfolio"

class PortfolioPosition(models.Model):
    """Portfolio position model"""
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='positions')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    shares = models.DecimalField(max_digits=10, decimal_places=2)
    average_price = models.DecimalField(max_digits=10, decimal_places=2)
    added_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.shares} shares of {self.stock.symbol}"

class AIPortfolioRecommendation(models.Model):
    """AI Portfolio Recommendation model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='aiRecommendations')
    risk_profile = models.CharField(max_length=50, default='Moderate')
    portfolio_allocation = models.JSONField(default=dict)
    recommended_stocks = models.JSONField(default=list)
    expected_portfolio_return = models.FloatField(default=0.0)
    risk_assessment = models.TextField(default='No assessment available')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Recommendation for {self.user.email} - {self.risk_profile}"

class StockRecommendation(models.Model):
    """Stock recommendation model"""
    portfolio_recommendation = models.ForeignKey(AIPortfolioRecommendation, on_delete=models.CASCADE, related_name='stock_recommendations')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    allocation = models.FloatField()
    reasoning = models.TextField()
    risk_level = models.CharField(max_length=20)
    expected_return = models.CharField(max_length=20)
    
    def __str__(self):
        return f"{self.stock.symbol} recommendation"

class IncomeProfile(models.Model):
    """Income Profile model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='incomeProfile')
    age = models.IntegerField()
    income_bracket = models.CharField(max_length=100)
    investment_goals = models.JSONField()
    risk_tolerance = models.CharField(max_length=50)
    investment_horizon = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Income profile for {self.user.email}"

class StockDiscussion(models.Model):
    """Stock discussion model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stock_discussions')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='discussions', null=True, blank=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    discussion_type = models.CharField(max_length=20, default='general')
    is_analysis = models.BooleanField(default=False)
    analysis_data = models.TextField(blank=True, null=True)
    likes = models.ManyToManyField(User, blank=True, related_name='liked_discussions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Discussion about {self.stock.symbol} by {self.user.email}"

class DiscussionComment(models.Model):
    """Discussion comment model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discussion_comments')
    discussion = models.ForeignKey(StockDiscussion, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    likes = models.ManyToManyField(User, blank=True, related_name='liked_comments')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Comment by {self.user.email} on {self.discussion.title}"

# New institutional models
class StockPriceSnapshot(models.Model):
    """
    Point-in-time snapshot of stock prices for institutional features
    """
    stock = models.ForeignKey('Stock', on_delete=models.CASCADE, related_name='price_snapshots')
    symbol = models.CharField(max_length=10, db_index=True)
    as_of = models.DateField(db_index=True)
    open_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    high_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    low_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    close = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)
    adjusted_close = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    dividend_amount = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    split_coefficient = models.DecimalField(max_digits=10, decimal_places=6, default=1.0)
    
    # Additional institutional metrics
    adv_score = models.FloatField(null=True, blank=True, help_text="Average Daily Volume score")
    volatility = models.FloatField(null=True, blank=True, help_text="30-day volatility")
    beta = models.FloatField(null=True, blank=True, help_text="Beta vs market")
    market_cap = models.BigIntegerField(null=True, blank=True)
    pe_ratio = models.FloatField(null=True, blank=True)
    dividend_yield = models.FloatField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    source = models.CharField(max_length=50, default='api', help_text="Data source")
    
    class Meta:
        unique_together = ['stock', 'as_of']
        indexes = [
            models.Index(fields=['symbol', 'as_of']),
            models.Index(fields=['as_of', 'symbol']),
        ]
        ordering = ['-as_of', 'symbol']
    
    def __str__(self):
        return f"{self.symbol} @ {self.as_of} - ${self.close}"
    
    @property
    def price_change(self):
        """Calculate price change from previous day"""
        if not self.close:
            return None
        
        try:
            prev_snapshot = StockPriceSnapshot.objects.filter(
                stock=self.stock,
                as_of__lt=self.as_of
            ).order_by('-as_of').first()
            
            if prev_snapshot and prev_snapshot.close:
                return float(self.close - prev_snapshot.close)
        except Exception:
            pass
        return None
    
    @property
    def price_change_percent(self):
        """Calculate price change percentage from previous day"""
        if not self.close:
            return None
        
        try:
            prev_snapshot = StockPriceSnapshot.objects.filter(
                stock=self.stock,
                as_of__lt=self.as_of
            ).order_by('-as_of').first()
            
            if prev_snapshot and prev_snapshot.close:
                return float((self.close - prev_snapshot.close) / prev_snapshot.close * 100)
        except Exception:
            pass
        return None

class CorporateAction(models.Model):
    """
    Corporate actions (splits, dividends, etc.) for point-in-time accuracy
    """
    ACTION_TYPES = [
        ('DIVIDEND', 'Dividend'),
        ('SPLIT', 'Stock Split'),
        ('SPINOFF', 'Spinoff'),
        ('MERGER', 'Merger'),
        ('ACQUISITION', 'Acquisition'),
    ]
    
    stock = models.ForeignKey('Stock', on_delete=models.CASCADE, related_name='corporate_actions')
    symbol = models.CharField(max_length=10, db_index=True)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    ex_date = models.DateField(db_index=True)
    record_date = models.DateField(null=True, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    
    # Action details
    amount = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    ratio = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    description = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=50, default='api')
    
    class Meta:
        ordering = ['-ex_date', 'symbol']
        indexes = [
            models.Index(fields=['symbol', 'ex_date']),
            models.Index(fields=['ex_date', 'action_type']),
        ]
    
    def __str__(self):
        return f"{self.symbol} {self.action_type} on {self.ex_date}"

class MarketRegime(models.Model):
    """
    Market regime classification for point-in-time analysis
    """
    REGIME_TYPES = [
        ('BULL', 'Bull Market'),
        ('BEAR', 'Bear Market'),
        ('VOLATILE', 'High Volatility'),
        ('SIDEWAYS', 'Sideways'),
        ('CRISIS', 'Crisis'),
    ]
    
    as_of = models.DateField(unique=True, db_index=True)
    regime = models.CharField(max_length=20, choices=REGIME_TYPES)
    confidence = models.FloatField(help_text="Confidence score 0-1")
    
    # Market metrics
    vix_level = models.FloatField(null=True, blank=True)
    market_return = models.FloatField(null=True, blank=True)
    volatility = models.FloatField(null=True, blank=True)
    
    # ML predictions
    ml_prediction = models.JSONField(null=True, blank=True)
    feature_importance = models.JSONField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    model_version = models.CharField(max_length=50, default='v1.0')
    
    class Meta:
        ordering = ['-as_of']
    
    def __str__(self):
        return f"{self.regime} market on {self.as_of} (confidence: {self.confidence:.2f})"

class PortfolioSnapshot(models.Model):
    """
    Point-in-time portfolio snapshots for institutional analysis
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolio_snapshots')
    as_of = models.DateField(db_index=True)
    
    # Portfolio composition
    holdings = models.JSONField(help_text="Portfolio holdings as of date")
    total_value = models.DecimalField(max_digits=15, decimal_places=2)
    cash_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Performance metrics
    daily_return = models.FloatField(null=True, blank=True)
    total_return = models.FloatField(null=True, blank=True)
    volatility = models.FloatField(null=True, blank=True)
    sharpe_ratio = models.FloatField(null=True, blank=True)
    max_drawdown = models.FloatField(null=True, blank=True)
    
    # Risk metrics
    var_95 = models.FloatField(null=True, blank=True, help_text="95% VaR")
    cvar_95 = models.FloatField(null=True, blank=True, help_text="95% CVaR")
    beta = models.FloatField(null=True, blank=True)
    tracking_error = models.FloatField(null=True, blank=True)
    
    # Sector allocation
    sector_allocation = models.JSONField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=50, default='system')
    
    class Meta:
        unique_together = ['user', 'as_of']
        ordering = ['-as_of']
        indexes = [
            models.Index(fields=['user', 'as_of']),
            models.Index(fields=['as_of']),
        ]
    
    def __str__(self):
        return f"{self.user.username} portfolio @ {self.as_of} - ${self.total_value:,.2f}"

class MLModelVersion(models.Model):
    """
    Track ML model versions for reproducibility
    """
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=50)
    model_type = models.CharField(max_length=50)  # portfolio, market, risk, etc.
    
    # Model details
    file_path = models.CharField(max_length=500)
    parameters = models.JSONField()
    performance_metrics = models.JSONField(null=True, blank=True)
    
    # Training info
    trained_on = models.DateField()
    training_data_hash = models.CharField(max_length=64, help_text="SHA256 of training data")
    
    # Status
    is_active = models.BooleanField(default=False)
    is_production = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        unique_together = ['name', 'version']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} v{self.version} ({'active' if self.is_active else 'inactive'})"

class AuditLog(models.Model):
    """
    Audit log for ML mutations and institutional features
    """
    ACTION_TYPES = [
        ('ML_RECOMMENDATION', 'ML Portfolio Recommendation'),
        ('INSTITUTIONAL_RECOMMENDATION', 'Institutional Portfolio Recommendation'),
        ('MARKET_ANALYSIS', 'Market Analysis'),
        ('RISK_ANALYSIS', 'Risk Analysis'),
        ('OPTIMIZATION', 'Portfolio Optimization'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audit_logs')
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Request details
    request_id = models.CharField(max_length=100, unique=True)
    input_data = models.JSONField()
    output_data = models.JSONField(null=True, blank=True)
    
    # Performance metrics
    execution_time_ms = models.IntegerField(null=True, blank=True)
    memory_usage_mb = models.FloatField(null=True, blank=True)
    
    # Status
    success = models.BooleanField()
    error_message = models.TextField(blank=True)
    
    # ML specific
    model_version = models.CharField(max_length=50, blank=True)
    feature_version = models.CharField(max_length=50, blank=True)
    optimization_method = models.CharField(max_length=50, blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action_type', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.action_type} by {self.user.username} at {self.timestamp}"
