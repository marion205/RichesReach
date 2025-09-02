# core/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    profile_pic = models.URLField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = UserManager()

    def __str__(self):
        return self.email
    
    @property
    def followers_count(self):
        return self.followers.count()
    
    @property
    def following_count(self):
        return self.following.count()
    
    def is_following(self, user):
        if user.is_anonymous:
            return False
        return self.following.filter(following=user).exists()
    
    def is_followed_by(self, user):
        if user.is_anonymous:
            return False
        return self.followers.filter(follower=user).exists()

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField()
    image = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.name}: {self.content[:30]}"
    
    @property
    def likes_count(self):
        return self.likes.count()
    
    @property
    def comments_count(self):
        return self.comments.count()
    
    def is_liked_by(self, user):
        if user.is_anonymous:
            return False
        return self.likes.filter(user=user).exists()

class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.name} - {self.title or 'Chat Session'} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]
    
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    confidence = models.FloatField(null=True, blank=True)
    tokens_used = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."

class Source(models.Model):
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='sources')
    title = models.CharField(max_length=255)
    url = models.URLField()
    snippet = models.TextField()
    
    def __str__(self):
        return self.title

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'post']
        db_table = 'core_like'
    
    def __str__(self):
        return f"{self.user.name} likes {self.post.content[:30]}"

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        db_table = 'core_comment'
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'
    
    def __str__(self):
        return f"{self.user.name}: {self.content[:30]}"

class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['follower', 'following']
        db_table = 'core_follow'
    
    def __str__(self):
        return f"{self.follower.name} follows {self.following.name}"

class Stock(models.Model):
    """Stock model to store basic stock information"""
    symbol = models.CharField(max_length=10, unique=True)
    company_name = models.CharField(max_length=255)
    sector = models.CharField(max_length=100, blank=True, null=True)
    market_cap = models.BigIntegerField(blank=True, null=True)  # Market capitalization
    current_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # Current stock price
    pe_ratio = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    dividend_yield = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    debt_ratio = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    volatility = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    beginner_friendly_score = models.IntegerField(default=0)  # 0-100 score for beginners
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.symbol} - {self.company_name}"
    
    class Meta:
        ordering = ['symbol']

class StockData(models.Model):
    """Historical stock price data"""
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='price_data')
    date = models.DateField()
    open_price = models.DecimalField(max_digits=10, decimal_places=2)
    high_price = models.DecimalField(max_digits=10, decimal_places=2)
    low_price = models.DecimalField(max_digits=10, decimal_places=2)
    close_price = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.BigIntegerField()
    
    class Meta:
        unique_together = ['stock', 'date']
        ordering = ['-date']

class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlists')
    name = models.CharField(max_length=100, null=True, blank=True)  # Temporary nullable
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    is_shared = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'name']
    
    def __str__(self):
        return f"{self.user.username}'s {self.name or 'Watchlist'}"
    
    def save(self, *args, **kwargs):
        # Auto-generate name if not provided
        if not self.name:
            self.name = f"Watchlist {self.id or 'New'}"
        super().save(*args, **kwargs)

class WatchlistItem(models.Model):
    watchlist = models.ForeignKey(Watchlist, on_delete=models.CASCADE, related_name='items')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    notes = models.TextField(blank=True)
    target_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['watchlist', 'stock']
    
    def __str__(self):
        return f"{self.stock.symbol} in {self.watchlist.name}"

class StockDiscussion(models.Model):
    DISCUSSION_TYPES = [
        ('analysis', 'Stock Analysis'),
        ('news', 'Market News'),
        ('strategy', 'Trading Strategy'),
        ('question', 'Question'),
        ('meme', 'Meme/Entertainment'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stock_discussions')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='discussions')
    title = models.CharField(max_length=200)
    content = models.TextField()
    discussion_type = models.CharField(max_length=20, choices=DISCUSSION_TYPES, default='analysis')
    is_analysis = models.BooleanField(default=False)
    analysis_data = models.JSONField(null=True, blank=True)
    likes = models.ManyToManyField(User, related_name='liked_discussions', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} by {self.user.username}"

class DiscussionComment(models.Model):
    discussion = models.ForeignKey(StockDiscussion, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discussion_comments')
    content = models.TextField()
    likes = models.ManyToManyField(User, related_name='liked_comments', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.discussion.title}"

class Portfolio(models.Model):
    """User portfolio with stock positions and share quantities"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolios')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, null=True, blank=True)
    shares = models.IntegerField(default=0)
    average_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'stock']
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.email} - {self.stock.symbol}: {self.shares} shares"

    @property
    def total_value(self):
        """Calculate total value based on current stock price"""
        if hasattr(self.stock, 'current_price') and self.stock.current_price:
            return self.shares * float(self.stock.current_price)
        return 0

    @property
    def market_value(self):
        """Get current market value"""
        return self.total_value

class PortfolioPosition(models.Model):
    POSITION_TYPES = [
        ('long', 'Long'),
        ('short', 'Short'),
        ('paper', 'Paper Trade'),
    ]
    
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='positions')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    position_type = models.CharField(max_length=10, choices=POSITION_TYPES, default='paper')
    shares = models.DecimalField(max_digits=15, decimal_places=6)
    entry_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    entry_date = models.DateTimeField(auto_now_add=True)
    exit_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['portfolio', 'stock']
    
    def __str__(self):
        return f"{self.shares} shares of {self.stock.symbol} in {self.portfolio.name}"
    
    @property
    def current_value(self):
        if self.current_price:
            return self.shares * self.current_price
        return self.shares * self.entry_price
    
    @property
    def total_return(self):
        if self.current_price:
            return ((self.current_price - self.entry_price) / self.entry_price) * 100
        return 0
    
    @property
    def total_return_dollars(self):
        if self.current_price:
            return (self.current_price - self.entry_price) * self.shares
        return 0

class PriceAlert(models.Model):
    ALERT_TYPES = [
        ('above', 'Price Above'),
        ('below', 'Price Below'),
        ('percent_change', 'Percent Change'),
        ('volume_spike', 'Volume Spike'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='price_alerts')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    target_value = models.DecimalField(max_digits=15, decimal_places=4)
    is_active = models.BooleanField(default=True)
    is_triggered = models.BooleanField(default=False)
    triggered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.alert_type} alert for {self.stock.symbol} at {self.target_value}"

class SocialFeed(models.Model):
    """Aggregated social feed for users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_feeds')
    content_type = models.CharField(max_length=20)  # 'discussion', 'watchlist_update', 'portfolio_update'
    content_id = models.IntegerField()  # ID of the related object
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'content_type', 'content_id']
    
    def __str__(self):
        return f"{self.content_type} feed item for {self.user.username}"

class UserAchievement(models.Model):
    """Gamification system for user engagement"""
    ACHIEVEMENT_TYPES = [
        ('first_post', 'First Discussion Post'),
        ('first_watchlist', 'First Watchlist'),
        ('first_portfolio', 'First Portfolio'),
        ('popular_post', 'Popular Post (10+ likes)'),
        ('viral_post', 'Viral Post (100+ likes)'),
        ('consistent_poster', 'Consistent Poster (7 days)'),
        ('stock_expert', 'Stock Expert (50+ posts)'),
        ('watchlist_curator', 'Watchlist Curator (5+ public watchlists)'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement_type = models.CharField(max_length=30, choices=ACHIEVEMENT_TYPES)
    title = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='🏆')
    earned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'achievement_type']
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user.username} earned {self.title}"

class StockSentiment(models.Model):
    """Track community sentiment for stocks"""
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='sentiments')
    positive_votes = models.IntegerField(default=0)
    negative_votes = models.IntegerField(default=0)
    neutral_votes = models.IntegerField(default=0)
    total_votes = models.IntegerField(default=0)
    sentiment_score = models.DecimalField(max_digits=5, decimal_places=4, default=0)  # -1 to 1
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['stock']
    
    def __str__(self):
        return f"Sentiment for {self.stock.symbol}: {self.sentiment_score}"
    
    def update_sentiment(self):
        """Calculate sentiment score based on votes"""
        if self.total_votes > 0:
            self.sentiment_score = (self.positive_votes - self.negative_votes) / self.total_votes
        else:
            self.sentiment_score = 0
        self.save()


class IncomeProfile(models.Model):
    """User's financial profile for AI recommendations"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='incomeProfile')
    income_bracket = models.CharField(max_length=50)
    age = models.IntegerField()
    investment_goals = models.JSONField(default=list)  # List of goal strings
    risk_tolerance = models.CharField(max_length=20)  # Conservative, Moderate, Aggressive
    investment_horizon = models.CharField(max_length=20)  # 1-3 years, 3-5 years, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Financial profile for {self.user.name}"


class AIPortfolioRecommendation(models.Model):
    """AI-generated portfolio recommendations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='aiRecommendations')
    risk_profile = models.CharField(max_length=50)  # Low, Medium, High
    portfolio_allocation = models.JSONField()  # {stocks: 60, bonds: 30, etfs: 10, cash: 0}
    expected_portfolio_return = models.CharField(max_length=20)  # e.g., "8-12%"
    risk_assessment = models.CharField(max_length=50)  # e.g., "Moderate Risk"
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"AI recommendation for {self.user.name} - {self.risk_profile}"


class StockRecommendation(models.Model):
    """Individual stock recommendations within AI portfolio"""
    portfolio_recommendation = models.ForeignKey(AIPortfolioRecommendation, on_delete=models.CASCADE, related_name='recommendedStocks')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    allocation = models.DecimalField(max_digits=5, decimal_places=2)  # Percentage allocation
    reasoning = models.TextField()  # AI explanation for recommendation
    risk_level = models.CharField(max_length=20)  # Low, Medium, High
    expected_return = models.CharField(max_length=20)  # e.g., "15-20%"
    
    class Meta:
        unique_together = ['portfolio_recommendation', 'stock']
    
    def __str__(self):
        return f"{self.stock.symbol} - {self.allocation}% allocation"