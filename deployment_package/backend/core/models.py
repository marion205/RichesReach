# core/models.py
import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

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
    # Enhanced security fields
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=32, blank=True)
    # Yodlee integration
    yodlee_loginname = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        unique=True,
        db_index=True,
        help_text='Yodlee loginName for this user (format: rr_userid)'
    )
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
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
    
    # Enhanced security methods
    def is_locked(self):
        """Check if account is currently locked"""
        from django.utils import timezone
        if self.locked_until:
            return timezone.now() < self.locked_until
        return False
    
    def lock_account(self, minutes=30):
        """Lock account for specified minutes"""
        from django.utils import timezone
        self.locked_until = timezone.now() + timezone.timedelta(minutes=minutes)
        self.save()
    
    def unlock_account(self):
        """Unlock account"""
        self.locked_until = None
        self.failed_login_attempts = 0
        self.save()
    
    def record_failed_login(self):
        """Record a failed login attempt"""
        self.failed_login_attempts += 1
        # Lock account after 5 failed attempts
        if self.failed_login_attempts >= 5:
            self.lock_account(minutes=30)
        self.save()
    
    def clear_failed_logins(self):
        """Clear failed login attempts"""
        self.failed_login_attempts = 0
        self.save()
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
    market_cap = models.BigIntegerField(blank=True, null=True) # Market capitalization
    pe_ratio = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    dividend_yield = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    debt_ratio = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    volatility = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    beginner_friendly_score = models.IntegerField(default=0) # 0-100 score for beginners
    current_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True) # Current stock price
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
    """User's stock watchlist"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlists')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='watchlisted_by', default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True) # User's personal notes about the stock
    target_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True) # User's target price
    created_at = models.DateTimeField(default=timezone.now) # For compatibility with existing table
    updated_at = models.DateTimeField(auto_now=True) # For compatibility with existing table
    description = models.TextField(blank=True, default="") # For compatibility with existing table
    is_public = models.BooleanField(default=False) # For compatibility with existing table
    is_shared = models.BooleanField(default=False) # For compatibility with existing table
    name = models.CharField(max_length=100, blank=True, null=True) # For compatibility with existing table
    
    class Meta:
        unique_together = ['user', 'stock']
        ordering = ['-added_at']
    
    def __str__(self):
        return f"{self.user.name} - {self.stock.symbol}"
class IncomeProfile(models.Model):
    """User's income and investment profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='incomeProfile')
    income_bracket = models.CharField(max_length=50)
    age = models.IntegerField()
    investment_goals = models.JSONField(default=list) # List of investment goals
    risk_tolerance = models.CharField(max_length=20, choices=[
    ('Conservative', 'Conservative'),
    ('Moderate', 'Moderate'),
    ('Aggressive', 'Aggressive')
    ])
    investment_horizon = models.CharField(max_length=20, choices=[
    ('1-3 years', '1-3 years'),
    ('3-5 years', '3-5 years'),
    ('5-10 years', '5-10 years'),
    ('10+ years', '10+ years')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.name} - {self.risk_tolerance} Profile"
class AIPortfolioRecommendation(models.Model):
    """AI-generated portfolio recommendations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_recommendations')
    risk_profile = models.CharField(max_length=20, choices=[
        ('Conservative', 'Conservative'),
        ('Moderate', 'Moderate'),
        ('Aggressive', 'Aggressive')
    ])
    portfolio_allocation = models.JSONField(default=dict) # Asset allocation percentages
    recommended_stocks = models.JSONField(default=list) # List of recommended stocks with details
    expected_portfolio_return = models.FloatField(null=True, blank=True)
    risk_assessment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.name} - {self.risk_profile} Portfolio ({self.created_at.strftime('%Y-%m-%d')})"
class Portfolio(models.Model):
    """User's portfolio holdings"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolios')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='portfolio_holdings')
    shares = models.IntegerField(default=0)
    notes = models.TextField(blank=True, null=True)
    average_price = models.DecimalField(max_digits=10, decimal_places=2, default=0) # Required field
    current_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_value = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'stock']
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.name} - {self.stock.symbol} ({self.shares} shares)"
    
    def save(self, *args, **kwargs):
        # Calculate total value if current_price is provided
        if self.current_price and self.shares:
            self.total_value = self.current_price * self.shares
        # Set average_price to current_price if not set
        if not self.average_price and self.current_price:
            self.average_price = self.current_price
        super().save(*args, **kwargs)
class StockDiscussion(models.Model):
    """Reddit-like stock discussion posts"""
    VISIBILITY_CHOICES = [
    ('public', 'Public - Everyone can see'),
    ('followers', 'Followers Only - Only followers can see'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discussions')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='discussions', null=True, blank=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    discussion_type = models.CharField(max_length=20, default='general') # general, analysis, news, etc.
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='followers') # public or followers
    is_analysis = models.BooleanField(default=False) # Required by existing table
    analysis_data = models.TextField(blank=True, null=True) # Required by existing table
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    is_pinned = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} by {self.user.name}"
    
    @property
    def score(self):
        return self.upvotes - self.downvotes
    
    @property
    def comment_count(self):
        return self.comments.count()
class DiscussionComment(models.Model):
    """Comments on stock discussions (Reddit-style)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discussion_comments')
    discussion = models.ForeignKey(StockDiscussion, on_delete=models.CASCADE, related_name='comments')
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    content = models.TextField()
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.user.name} on {self.discussion.title}"
    
    @property
    def score(self):
        return self.upvotes - self.downvotes
    
    @property
    def reply_count(self):
        return self.replies.count()


class MomentCategory(models.TextChoices):
    """Categories for stock moments"""
    EARNINGS = "EARNINGS", "Earnings"
    NEWS = "NEWS", "News"
    INSIDER = "INSIDER", "Insider"
    MACRO = "MACRO", "Macro"
    SENTIMENT = "SENTIMENT", "Sentiment"
    OTHER = "OTHER", "Other"


class StockMoment(models.Model):
    """AI-generated key moments for stock price movements"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symbol = models.CharField(max_length=16, db_index=True)
    timestamp = models.DateTimeField(db_index=True)
    
    importance_score = models.FloatField(default=0.0)
    category = models.CharField(
        max_length=32,
        choices=MomentCategory.choices,
        default=MomentCategory.OTHER,
    )
    
    title = models.CharField(max_length=140)
    quick_summary = models.TextField()
    deep_summary = models.TextField()
    
    # Store source URLs as JSON array
    source_links = models.JSONField(default=list, blank=True)
    
    impact_1d = models.FloatField(null=True, blank=True)  # % move 1 day after
    impact_7d = models.FloatField(null=True, blank=True)  # % move 7 days after
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["symbol", "timestamp"]),
        ]
        ordering = ["symbol", "-timestamp"]
    
    def __str__(self):
        return f"{self.symbol} @ {self.timestamp} ({self.category})"


# Import paper trading models so Django can detect them for migrations
from .paper_trading_models import (
    PaperTradingAccount,
    PaperTradingPosition,
    PaperTradingOrder,
    PaperTradingTrade,
)

# Security Fortress Models
class SecurityEvent(models.Model):
    """Track security events and threats"""
    THREAT_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    EVENT_TYPES = [
        ('suspicious_login', 'Suspicious Login'),
        ('fraud_detection', 'Fraud Detection'),
        ('biometric_failure', 'Biometric Failure'),
        ('unusual_activity', 'Unusual Activity'),
        ('device_change', 'Device Change'),
        ('location_change', 'Location Change'),
        ('password_breach', 'Password Breach'),
        ('api_abuse', 'API Abuse'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_events')
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    threat_level = models.CharField(max_length=20, choices=THREAT_LEVELS)
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)  # Store additional event data
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_events')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['threat_level', 'resolved']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.event_type} ({self.threat_level})"


class BiometricSettings(models.Model):
    """User biometric authentication settings"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='biometric_settings')
    face_id_enabled = models.BooleanField(default=False)
    voice_id_enabled = models.BooleanField(default=False)
    behavioral_id_enabled = models.BooleanField(default=True)
    device_fingerprint_enabled = models.BooleanField(default=True)
    location_tracking_enabled = models.BooleanField(default=False)
    face_id_data = models.TextField(blank=True)  # Encrypted biometric data
    voice_id_data = models.TextField(blank=True)  # Encrypted voice print
    device_fingerprint = models.CharField(max_length=255, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Biometric Settings for {self.user.email}"


class ComplianceStatus(models.Model):
    """Track compliance readiness and controls coverage
    
    NOTE: These scores represent internal readiness indicators, not official certifications.
    For production, consider renaming to 'ReadinessScore' or 'ControlsCoverage' to avoid
    legal/compliance confusion.
    """
    STANDARDS = [
        ('SOC2', 'SOC 2 Type II'),
        ('PCI_DSS', 'PCI DSS'),
        ('GDPR', 'GDPR'),
        ('CCPA', 'CCPA'),
        ('HIPAA', 'HIPAA'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    standard = models.CharField(max_length=50, choices=STANDARDS, unique=True)
    status = models.CharField(max_length=50, default='Compliant')  # Consider: 'ReadinessStatus'
    score = models.IntegerField(default=0)  # 0-100 readiness score (not certification)
    last_audit_date = models.DateField(null=True, blank=True)
    next_audit_date = models.DateField(null=True, blank=True)
    audit_report_url = models.URLField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['standard']
    
    def __str__(self):
        return f"{self.standard} - {self.status}"


class SecurityScore(models.Model):
    """Track user security score over time"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_scores')
    score = models.IntegerField(default=0)  # 0-100
    factors = models.JSONField(default=dict)  # Breakdown of score factors
    calculated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-calculated_at']
        indexes = [
            models.Index(fields=['user', '-calculated_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.score}/100"


class DeviceTrust(models.Model):
    """Zero Trust: Device trust scores and fingerprints"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trusted_devices')
    device_id = models.CharField(max_length=255, db_index=True)
    device_fingerprint = models.TextField()  # JSON-encoded device characteristics
    trust_score = models.IntegerField(default=50)  # 0-100
    first_seen = models.DateTimeField(auto_now_add=True)
    last_verified = models.DateTimeField(auto_now=True)
    last_ip_address = models.GenericIPAddressField(null=True, blank=True)
    is_trusted = models.BooleanField(default=False)
    verification_count = models.IntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['user', 'device_id']]
        indexes = [
            models.Index(fields=['user', 'device_id']),
            models.Index(fields=['user', '-trust_score']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - Device {self.device_id[:8]} (Trust: {self.trust_score})"


class AccessPolicy(models.Model):
    """Zero Trust: Access policies for least privilege"""
    POLICY_TYPES = [
        ('allow', 'Allow'),
        ('deny', 'Deny'),
        ('mfa_required', 'MFA Required'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='access_policies')
    action = models.CharField(max_length=100)  # e.g., 'create_trade', 'withdraw_funds'
    resource = models.CharField(max_length=100)  # e.g., 'trading', 'banking'
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPES, default='mfa_required')
    conditions = models.JSONField(default=dict)  # e.g., {'trust_score_min': 70, 'device_trusted': True}
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['user', 'action', 'resource']]
        indexes = [
            models.Index(fields=['user', 'action', 'resource']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.action} on {self.resource}: {self.policy_type}"


class SupplyChainVendor(models.Model):
    """Supply chain vendor monitoring for compliance"""
    VENDOR_TYPES = [
        ('payment_processor', 'Payment Processor'),
        ('data_provider', 'Data Provider'),
        ('cloud_provider', 'Cloud Provider'),
        ('security_service', 'Security Service'),
        ('ai_service', 'AI Service'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('monitoring', 'Under Monitoring'),
        ('suspended', 'Suspended'),
        ('terminated', 'Terminated'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    vendor_type = models.CharField(max_length=50, choices=VENDOR_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    compliance_certifications = models.JSONField(default=list)  # e.g., ['SOC2', 'ISO27001', 'PCI-DSS']
    last_audit_date = models.DateTimeField(null=True, blank=True)
    next_audit_date = models.DateTimeField(null=True, blank=True)
    risk_score = models.IntegerField(default=50)  # 0-100
    security_incidents = models.IntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-risk_score', 'name']
        indexes = [
            models.Index(fields=['vendor_type', 'status']),
            models.Index(fields=['risk_score']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.vendor_type}) - Risk: {self.risk_score}"


class ComplianceAutomation(models.Model):
    """Automated compliance checks and reports"""
    COMPLIANCE_STANDARDS = [
        ('SOC2', 'SOC 2'),
        ('ISO27001', 'ISO 27001'),
        ('PCI-DSS', 'PCI-DSS'),
        ('GDPR', 'GDPR'),
        ('CCPA', 'CCPA'),
        ('HIPAA', 'HIPAA'),
    ]
    
    CHECK_TYPES = [
        ('automated', 'Automated'),
        ('manual', 'Manual'),
        ('scheduled', 'Scheduled'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('warning', 'Warning'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    standard = models.CharField(max_length=50, choices=COMPLIANCE_STANDARDS)
    check_type = models.CharField(max_length=20, choices=CHECK_TYPES, default='automated')
    check_name = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    result = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['standard', 'check_name']
        indexes = [
            models.Index(fields=['standard', 'status']),
            models.Index(fields=['next_run']),
        ]
    
    def __str__(self):
        return f"{self.standard} - {self.check_name} ({self.status})"


# Import signal performance models so Django can detect them for migrations
from .signal_performance_models import (
    DayTradingSignal,
    SignalPerformance,
    StrategyPerformance,
    UserRiskBudget,
)