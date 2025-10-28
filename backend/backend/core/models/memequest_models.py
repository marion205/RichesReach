"""
Database Models for MemeQuest Social Trading Integration
=======================================================

This module defines all database models for:
1. Meme coin launches and bonding curves
2. Social trading posts and interactions
3. Trading raid coordination
4. DeFi yield farming positions
5. Voice command history and analytics
6. Enhanced user profiles
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid
from decimal import Decimal
from enum import Enum

# Get the custom User model
User = get_user_model()

# =============================================================================
# Enums and Choices
# =============================================================================

class MemeStatus(models.TextChoices):
    """Meme coin status choices."""
    CREATING = 'creating', 'Creating'
    ACTIVE = 'active', 'Active'
    GRADUATED = 'graduated', 'Graduated'
    FAILED = 'failed', 'Failed'
    RUGGED = 'rugged', 'Rugged'

class RaidStatus(models.TextChoices):
    """Raid status choices."""
    PLANNING = 'planning', 'Planning'
    ACTIVE = 'active', 'Active'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'

class SocialPostType(models.TextChoices):
    """Social post type choices."""
    MEME_LAUNCH = 'meme_launch', 'Meme Launch'
    RAID_JOIN = 'raid_join', 'Raid Join'
    TRADE_SHARE = 'trade_share', 'Trade Share'
    YIELD_FARM = 'yield_farm', 'Yield Farm'
    EDUCATIONAL = 'educational', 'Educational'
    GENERAL = 'general', 'General'

class DeFiProtocol(models.TextChoices):
    """DeFi protocol choices."""
    AAVE = 'aave', 'AAVE'
    COMPOUND = 'compound', 'Compound'
    UNISWAP = 'uniswap', 'Uniswap'
    PANCAKESWAP = 'pancakeswap', 'PancakeSwap'
    CURVE = 'curve', 'Curve'
    BALANCER = 'balancer', 'Balancer'

class YieldStrategy(models.TextChoices):
    """Yield farming strategy choices."""
    SIMPLE_STAKE = 'simple_stake', 'Simple Stake'
    LIQUIDITY_PROVISION = 'liquidity_provision', 'Liquidity Provision'
    LEVERAGED_YIELD = 'leveraged_yield', 'Leveraged Yield'
    AUTO_COMPOUND = 'auto_compound', 'Auto Compound'
    RISK_PARITY = 'risk_parity', 'Risk Parity'

class RiskLevel(models.TextChoices):
    """Risk level choices."""
    LOW = 'low', 'Low'
    MEDIUM = 'medium', 'Medium'
    HIGH = 'high', 'High'
    VERY_HIGH = 'very_high', 'Very High'

class VoiceCommandType(models.TextChoices):
    """Voice command type choices."""
    MEMEQUEST = 'memequest', 'MemeQuest'
    TRADING = 'trading', 'Trading'
    EDUCATION = 'education', 'Education'
    SOCIAL = 'social', 'Social'
    DEFI = 'defi', 'DeFi'
    GENERAL = 'general', 'General'

# =============================================================================
# Meme Coin Models
# =============================================================================

class MemeTemplate(models.Model):
    """Meme template for BIPOC-themed memes."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    image_url = models.URLField()
    description = models.TextField()
    cultural_theme = models.CharField(max_length=100)
    ai_prompt = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'meme_templates'
        verbose_name = 'Meme Template'
        verbose_name_plural = 'Meme Templates'

    def __str__(self):
        return self.name

class MemeCoin(models.Model):
    """Meme coin data and bonding curve information."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=20)
    template = models.ForeignKey(MemeTemplate, on_delete=models.CASCADE, null=True, blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_memes')
    network = models.CharField(max_length=20, default='solana')
    contract_address = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=20, choices=MemeStatus.choices, default=MemeStatus.CREATING)
    
    # Bonding curve data
    initial_price = models.DecimalField(max_digits=20, decimal_places=10, default=Decimal('0.0001'))
    current_price = models.DecimalField(max_digits=20, decimal_places=10, default=Decimal('0.0001'))
    market_cap = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    total_supply = models.DecimalField(max_digits=20, decimal_places=0, default=Decimal('1000000000'))
    holders = models.IntegerField(default=0)
    volume_24h = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    
    # Bonding curve settings
    bonding_curve_active = models.BooleanField(default=True)
    graduation_threshold = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('69000'))
    graduation_progress = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0'))
    
    # Metadata
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    cultural_theme = models.CharField(max_length=100, blank=True)
    ai_generated = models.BooleanField(default=False)
    performance_metrics = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    graduated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'meme_coins'
        verbose_name = 'Meme Coin'
        verbose_name_plural = 'Meme Coins'
        indexes = [
            models.Index(fields=['creator', 'status']),
            models.Index(fields=['network', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['cultural_theme']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.symbol})"

# =============================================================================
# Social Trading Models
# =============================================================================

class SocialPost(models.Model):
    """Social trading posts and interactions."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_posts')
    post_type = models.CharField(max_length=20, choices=SocialPostType.choices)
    content = models.TextField()
    
    # Media content
    image_url = models.URLField(blank=True)
    video_url = models.URLField(blank=True)
    
    # Related objects
    meme_coin = models.ForeignKey(MemeCoin, on_delete=models.CASCADE, null=True, blank=True, related_name='social_posts')
    raid = models.ForeignKey('Raid', on_delete=models.CASCADE, null=True, blank=True, related_name='social_posts')
    yield_position = models.ForeignKey('YieldPosition', on_delete=models.CASCADE, null=True, blank=True, related_name='social_posts')
    
    # Engagement metrics
    likes = models.IntegerField(default=0)
    shares = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)
    views = models.IntegerField(default=0)
    
    # Gamification
    xp_reward = models.IntegerField(default=10)
    is_spotlight = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'social_posts'
        verbose_name = 'Social Post'
        verbose_name_plural = 'Social Posts'
        indexes = [
            models.Index(fields=['user', 'post_type']),
            models.Index(fields=['meme_coin', 'created_at']),
            models.Index(fields=['raid', 'created_at']),
            models.Index(fields=['is_spotlight', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.content[:50]}..."

class PostEngagement(models.Model):
    """User engagement with social posts."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(SocialPost, on_delete=models.CASCADE, related_name='engagements')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_engagements')
    engagement_type = models.CharField(max_length=20, choices=[
        ('like', 'Like'),
        ('share', 'Share'),
        ('comment', 'Comment'),
        ('view', 'View'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'post_engagements'
        verbose_name = 'Post Engagement'
        verbose_name_plural = 'Post Engagements'
        unique_together = ['post', 'user', 'engagement_type']
        indexes = [
            models.Index(fields=['post', 'engagement_type']),
            models.Index(fields=['user', 'engagement_type']),
        ]

    def __str__(self):
        return f"{self.user.username} {self.engagement_type}d {self.post.id}"

# =============================================================================
# Raid Models
# =============================================================================

class Raid(models.Model):
    """Trading raid coordination."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    meme_coin = models.ForeignKey(MemeCoin, on_delete=models.CASCADE, related_name='raids')
    leader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='led_raids')
    
    # Raid parameters
    target_amount = models.DecimalField(max_digits=20, decimal_places=2)
    current_amount = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    status = models.CharField(max_length=20, choices=RaidStatus.choices, default=RaidStatus.PLANNING)
    
    # Gamification
    xp_reward = models.IntegerField(default=50)
    success_bonus = models.IntegerField(default=100)
    
    # Timestamps
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'raids'
        verbose_name = 'Raid'
        verbose_name_plural = 'Raids'
        indexes = [
            models.Index(fields=['leader', 'status']),
            models.Index(fields=['meme_coin', 'status']),
            models.Index(fields=['start_time']),
        ]

    def __str__(self):
        return f"{self.name} - {self.meme_coin.symbol}"

class RaidParticipation(models.Model):
    """User participation in raids."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    raid = models.ForeignKey(Raid, on_delete=models.CASCADE, related_name='participations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='raid_participations')
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    xp_earned = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'raid_participations'
        verbose_name = 'Raid Participation'
        verbose_name_plural = 'Raid Participations'
        unique_together = ['raid', 'user']
        indexes = [
            models.Index(fields=['raid', 'user']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} participated in {self.raid.name}"

# =============================================================================
# DeFi Yield Farming Models
# =============================================================================

class YieldPool(models.Model):
    """DeFi yield farming pools."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    protocol = models.CharField(max_length=20, choices=DeFiProtocol.choices)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_pools')
    
    # Pool metrics
    apy = models.DecimalField(max_digits=5, decimal_places=2)
    tvl = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    risk_level = models.CharField(max_length=20, choices=RiskLevel.choices, default=RiskLevel.MEDIUM)
    
    # Pool parameters
    tokens = models.JSONField(default=list)  # List of token addresses
    min_stake = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    max_stake = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    fees = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0'))
    lock_period = models.IntegerField(default=0)  # Days
    
    # Features
    auto_compound = models.BooleanField(default=False)
    cross_chain = models.BooleanField(default=False)
    is_community_pool = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'yield_pools'
        verbose_name = 'Yield Pool'
        verbose_name_plural = 'Yield Pools'
        indexes = [
            models.Index(fields=['protocol', 'risk_level']),
            models.Index(fields=['apy']),
            models.Index(fields=['is_community_pool']),
        ]

    def __str__(self):
        return f"{self.name} ({self.protocol})"

class YieldPosition(models.Model):
    """User yield farming positions."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='yield_positions')
    pool = models.ForeignKey(YieldPool, on_delete=models.CASCADE, related_name='positions')
    strategy = models.CharField(max_length=20, choices=YieldStrategy.choices, default=YieldStrategy.SIMPLE_STAKE)
    
    # Position data
    amount_staked = models.DecimalField(max_digits=20, decimal_places=2)
    tokens_staked = models.JSONField(default=dict)  # Token amounts
    current_apy = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Yield data
    earned_yield = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    total_value = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    last_harvest = models.DateTimeField(null=True, blank=True)
    
    # Risk management
    risk_score = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('0.5'))
    auto_compound = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'yield_positions'
        verbose_name = 'Yield Position'
        verbose_name_plural = 'Yield Positions'
        indexes = [
            models.Index(fields=['user', 'strategy']),
            models.Index(fields=['pool', 'created_at']),
            models.Index(fields=['auto_compound']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.pool.name}"

class YieldTransaction(models.Model):
    """Yield farming transactions."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='yield_transactions')
    pool = models.ForeignKey(YieldPool, on_delete=models.CASCADE, related_name='transactions')
    position = models.ForeignKey(YieldPosition, on_delete=models.CASCADE, null=True, blank=True, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=[
        ('stake', 'Stake'),
        ('unstake', 'Unstake'),
        ('harvest', 'Harvest'),
        ('compound', 'Compound'),
    ])
    
    # Transaction data
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    tokens = models.JSONField(default=dict)  # Token amounts
    
    # Blockchain data
    transaction_hash = models.CharField(max_length=100, blank=True)
    gas_used = models.IntegerField(default=0)
    gas_price = models.DecimalField(max_digits=20, decimal_places=0, default=Decimal('0'))
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('failed', 'Failed'),
    ], default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'yield_transactions'
        verbose_name = 'Yield Transaction'
        verbose_name_plural = 'Yield Transactions'
        indexes = [
            models.Index(fields=['user', 'transaction_type']),
            models.Index(fields=['pool', 'transaction_type']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - {self.amount}"

# =============================================================================
# Voice Command Models
# =============================================================================

class VoiceCommand(models.Model):
    """Voice command history and analytics."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='voice_commands')
    command_type = models.CharField(max_length=20, choices=VoiceCommandType.choices)
    
    # Command data
    original_command = models.TextField()
    parsed_intent = models.CharField(max_length=100)
    parameters = models.JSONField(default=dict)
    confidence = models.DecimalField(max_digits=3, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(1)])
    
    # Processing
    processed = models.BooleanField(default=False)
    result = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    
    # Context
    current_screen = models.CharField(max_length=50, blank=True)
    active_tab = models.CharField(max_length=50, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'voice_commands'
        verbose_name = 'Voice Command'
        verbose_name_plural = 'Voice Commands'
        indexes = [
            models.Index(fields=['user', 'command_type']),
            models.Index(fields=['processed', 'created_at']),
            models.Index(fields=['confidence']),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.original_command[:50]}..."

# =============================================================================
# Enhanced User Profile Models
# =============================================================================

class UserProfile(models.Model):
    """Enhanced user profile with MemeQuest data."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # MemeQuest specific data
    current_streak = models.IntegerField(default=0)
    total_xp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    
    # Wallet information
    wallet_address = models.CharField(max_length=100, blank=True)
    wallet_connected = models.BooleanField(default=False)
    preferred_network = models.CharField(max_length=20, default='solana')
    
    # Preferences
    voice_enabled = models.BooleanField(default=True)
    selected_voice = models.CharField(max_length=20, default='alloy')
    voice_speed = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('1.0'))
    voice_emotion = models.CharField(max_length=20, default='neutral')
    
    # BIPOC community features
    is_bipoc = models.BooleanField(default=False)
    cultural_theme = models.CharField(max_length=100, blank=True)
    community_contributions = models.IntegerField(default=0)
    
    # Analytics
    total_memes_created = models.IntegerField(default=0)
    total_raids_joined = models.IntegerField(default=0)
    total_yield_earned = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    total_social_posts = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_active = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        indexes = [
            models.Index(fields=['current_streak']),
            models.Index(fields=['total_xp']),
            models.Index(fields=['is_bipoc']),
            models.Index(fields=['last_active']),
        ]

    def __str__(self):
        return f"{self.user.username} Profile"

class UserAchievement(models.Model):
    """User achievements and badges."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement_type = models.CharField(max_length=50, choices=[
        ('meme_creator', 'Meme Creator'),
        ('raid_leader', 'Raid Leader'),
        ('yield_farmer', 'Yield Farmer'),
        ('social_influencer', 'Social Influencer'),
        ('voice_master', 'Voice Master'),
        ('bipoc_champion', 'BIPOC Champion'),
        ('streak_master', 'Streak Master'),
        ('xp_legend', 'XP Legend'),
    ])
    title = models.CharField(max_length=100)
    description = models.TextField()
    icon_url = models.URLField(blank=True)
    xp_reward = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_achievements'
        verbose_name = 'User Achievement'
        verbose_name_plural = 'User Achievements'
        unique_together = ['user', 'achievement_type']
        indexes = [
            models.Index(fields=['user', 'achievement_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.title}"

# =============================================================================
# Analytics Models
# =============================================================================

class MemeQuestAnalytics(models.Model):
    """Analytics data for MemeQuest features."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField()
    
    # User metrics
    daily_active_users = models.IntegerField(default=0)
    new_users = models.IntegerField(default=0)
    returning_users = models.IntegerField(default=0)
    
    # MemeQuest metrics
    memes_created = models.IntegerField(default=0)
    raids_joined = models.IntegerField(default=0)
    yield_positions_opened = models.IntegerField(default=0)
    social_posts_created = models.IntegerField(default=0)
    voice_commands_processed = models.IntegerField(default=0)
    
    # Engagement metrics
    total_likes = models.IntegerField(default=0)
    total_shares = models.IntegerField(default=0)
    total_comments = models.IntegerField(default=0)
    total_views = models.IntegerField(default=0)
    
    # Revenue metrics
    total_volume = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    total_fees = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    total_yield_earned = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    
    # BIPOC community metrics
    bipoc_users_active = models.IntegerField(default=0)
    bipoc_content_created = models.IntegerField(default=0)
    community_contributions = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'memequest_analytics'
        verbose_name = 'MemeQuest Analytics'
        verbose_name_plural = 'MemeQuest Analytics'
        unique_together = ['date']
        indexes = [
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"Analytics for {self.date}"
