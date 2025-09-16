# core/models.py
from __future__ import annotations

import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import UniqueConstraint, Index, Q
from django.utils import timezone


# ------------------------------ Base / Mixins ------------------------------ #

class UUIDModel(models.Model):
    """Base model with UUID primary key and created/updated timestamps."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# --------------------------------- Users ---------------------------------- #

class UserManager(BaseUserManager):
    def create_user(self, email: str, password: str | None = None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, UUIDModel):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    profile_pic = models.URLField(max_length=500, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Enhanced security
    failed_login_attempts = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    two_factor_enabled = models.BooleanField(default=False)
    # 32 fits most TOTP secrets (base32). Keep out of admin list_display.
    two_factor_secret = models.CharField(max_length=64, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]
    objects = UserManager()

    class Meta:
        indexes = [
            Index(fields=["email"]),
            Index(fields=["-created_at"]),
            Index(fields=["locked_until"]),
        ]

    def __str__(self) -> str:
        return self.email

    # Follows (convenience)
    def is_following(self, user: "User") -> bool:
        if not user or getattr(user, "is_anonymous", False):
            return False
        return self.following.filter(following=user).exists()

    def is_followed_by(self, user: "User") -> bool:
        if not user or getattr(user, "is_anonymous", False):
            return False
        return self.followers.filter(follower=user).exists()

    @property
    def followers_count(self) -> int:
        return self.followers.count()

    @property
    def following_count(self) -> int:
        return self.following.count()

    # Security helpers
    def is_locked(self) -> bool:
        return bool(self.locked_until and timezone.now() < self.locked_until)

    def lock_account(self, minutes: int = 30) -> None:
        self.locked_until = timezone.now() + timezone.timedelta(minutes=minutes)
        self.save(update_fields=["locked_until"])

    def unlock_account(self) -> None:
        self.locked_until = None
        self.failed_login_attempts = 0
        self.save(update_fields=["locked_until", "failed_login_attempts"])

    def record_failed_login(self) -> None:
        self.failed_login_attempts = (self.failed_login_attempts or 0) + 1
        if self.failed_login_attempts >= 5:
            self.lock_account(minutes=30)
        else:
            self.save(update_fields=["failed_login_attempts"])

    def clear_failed_logins(self) -> None:
        self.failed_login_attempts = 0
        self.save(update_fields=["failed_login_attempts"])


# --------------------------------- Posts ---------------------------------- #

class Post(UUIDModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField()
    image = models.URLField(max_length=500, blank=True, null=True)

    class Meta(UUIDModel.Meta):
        indexes = [
            Index(fields=["user", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.name}: {self.content[:30]}"

    @property
    def likes_count(self) -> int:
        return self.likes.count()

    @property
    def comments_count(self) -> int:
        return self.comments.count()

    def is_liked_by(self, user: User) -> bool:
        if not user or getattr(user, "is_anonymous", False):
            return False
        return self.likes.filter(user=user).exists()


# ------------------------------- Chat Models ------------------------------- #

class ChatSession(UUIDModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_sessions")
    title = models.CharField(max_length=255, blank=True)

    class Meta(UUIDModel.Meta):
        indexes = [
            Index(fields=["user", "-updated_at"]),
        ]

    def __str__(self) -> str:
        pretty = self.title or "Chat Session"
        return f"{self.user.name} - {pretty} ({self.created_at:%Y-%m-%d %H:%M})"


class ChatMessage(UUIDModel):
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"
        SYSTEM = "system", "System"

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField()
    confidence = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)])
    tokens_used = models.PositiveIntegerField(null=True, blank=True)

    class Meta(UUIDModel.Meta):
        ordering = ["created_at"]
        indexes = [
            Index(fields=["session", "created_at"]),
            Index(fields=["role"]),
        ]

    def __str__(self) -> str:
        return f"{self.role}: {self.content[:50]}..."


class Source(UUIDModel):
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name="sources")
    title = models.CharField(max_length=255)
    url = models.URLField()
    snippet = models.TextField()

    def __str__(self) -> str:
        return self.title


# --------------------------- Social Interactions --------------------------- #

class Like(UUIDModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")

    class Meta(UUIDModel.Meta):
        constraints = [
            UniqueConstraint(fields=["user", "post"], name="uq_like_user_post"),
        ]
        indexes = [
            Index(fields=["post"]),
        ]
        db_table = "core_like"

    def __str__(self) -> str:
        return f"{self.user.name} likes {self.post.content[:30]}"

    @staticmethod
    def toggle(user: User, post: Post) -> bool:
        """Returns True if liked after toggle, False if unliked."""
        obj, created = Like.objects.get_or_create(user=user, post=post)
        if created:
            return True
        obj.delete()
        return False


class Comment(UUIDModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()

    class Meta(UUIDModel.Meta):
        ordering = ["created_at"]
        indexes = [
            Index(fields=["post", "created_at"]),
        ]
        db_table = "core_comment"
        verbose_name = "Comment"
        verbose_name_plural = "Comments"

    def __str__(self) -> str:
        return f"{self.user.name}: {self.content[:30]}"


class Follow(UUIDModel):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name="following")
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name="followers")

    class Meta(UUIDModel.Meta):
        constraints = [
            UniqueConstraint(fields=["follower", "following"], name="uq_follow_follower_following"),
            models.CheckConstraint(check=~Q(follower=models.F("following")), name="ck_no_self_follow"),
        ]
        indexes = [
            Index(fields=["follower"]),
            Index(fields=["following"]),
        ]
        db_table = "core_follow"

    def __str__(self) -> str:
        return f"{self.follower.name} follows {self.following.name}"


# --------------------------------- Stocks ---------------------------------- #

class Stock(UUIDModel):
    """Stock model to store basic stock information"""

    symbol = models.CharField(max_length=10, unique=True, db_index=True)
    company_name = models.CharField(max_length=255)
    sector = models.CharField(max_length=100, blank=True, null=True)

    market_cap = models.BigIntegerField(blank=True, null=True, validators=[MinValueValidator(0)])
    pe_ratio = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    dividend_yield = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal("0"))]
    )
    debt_ratio = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    volatility = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    beginner_friendly_score = models.PositiveSmallIntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    current_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta(UUIDModel.Meta):
        ordering = ["symbol"]
        indexes = [
            Index(fields=["sector"]),
            Index(fields=["-last_updated"]),
        ]

    def __str__(self) -> str:
        return f"{self.symbol} - {self.company_name}"


class StockData(UUIDModel):
    """Historical stock price data (daily candles)."""

    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name="price_data")
    date = models.DateField(db_index=True)
    open_price = models.DecimalField(max_digits=12, decimal_places=4, validators=[MinValueValidator(0)])
    high_price = models.DecimalField(max_digits=12, decimal_places=4, validators=[MinValueValidator(0)])
    low_price = models.DecimalField(max_digits=12, decimal_places=4, validators=[MinValueValidator(0)])
    close_price = models.DecimalField(max_digits=12, decimal_places=4, validators=[MinValueValidator(0)])
    volume = models.BigIntegerField(validators=[MinValueValidator(0)])

    class Meta(UUIDModel.Meta):
        constraints = [
            UniqueConstraint(fields=["stock", "date"], name="uq_stockdata_stock_date"),
        ]
        ordering = ["-date"]
        indexes = [
            Index(fields=["stock", "-date"]),
        ]


class Watchlist(UUIDModel):
    """User's stock watchlist"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watchlists")
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name="watchlisted_by")
    added_at = models.DateTimeField(auto_now_add=True)

    # User meta
    notes = models.TextField(blank=True, null=True)
    target_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    # Compatibility fields (keep but default safely)
    description = models.TextField(blank=True, default="")
    is_public = models.BooleanField(default=False)
    is_shared = models.BooleanField(default=False)
    name = models.CharField(max_length=100, blank=True, null=True)

    class Meta(UUIDModel.Meta):
        constraints = [
            UniqueConstraint(fields=["user", "stock"], name="uq_watchlist_user_stock"),
        ]
        ordering = ["-added_at"]
        indexes = [
            Index(fields=["user", "-added_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.name} - {self.stock.symbol}"


# ---------------------------- Investor Profiles ---------------------------- #

class IncomeProfile(UUIDModel):
    """User's income and investment profile"""

    class Risk(models.TextChoices):
        CONSERVATIVE = "Conservative", "Conservative"
        MODERATE = "Moderate", "Moderate"
        AGGRESSIVE = "Aggressive", "Aggressive"

    class Horizon(models.TextChoices):
        Y1_3 = "1-3 years", "1-3 years"
        Y3_5 = "3-5 years", "3-5 years"
        Y5_10 = "5-10 years", "5-10 years"
        Y10P = "10+ years", "10+ years"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="incomeProfile")
    income_bracket = models.CharField(max_length=50)
    age = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(120)])
    investment_goals = models.JSONField(default=list)
    risk_tolerance = models.CharField(max_length=20, choices=Risk.choices)
    investment_horizon = models.CharField(max_length=20, choices=Horizon.choices)

    def __str__(self) -> str:
        return f"{self.user.name} - {self.risk_tolerance} Profile"


class AIPortfolioRecommendation(UUIDModel):
    """AI-generated portfolio recommendations"""

    class Risk(models.TextChoices):
        CONSERVATIVE = "Conservative", "Conservative"
        MODERATE = "Moderate", "Moderate"
        AGGRESSIVE = "Aggressive", "Aggressive"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ai_recommendations")
    risk_profile = models.CharField(max_length=20, choices=Risk.choices)
    portfolio_allocation = models.JSONField(default=dict)  # e.g. {"US Stocks": 0.6, "Bonds": 0.3, "Cash": 0.1}
    recommended_stocks = models.JSONField(default=list)
    expected_portfolio_return = models.FloatField(null=True, blank=True)
    risk_assessment = models.TextField(blank=True)

    class Meta(UUIDModel.Meta):
        ordering = ["-created_at"]
        indexes = [
            Index(fields=["user", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.name} - {self.risk_profile} Portfolio ({self.created_at:%Y-%m-%d})"


# ------------------------------- Portfolios -------------------------------- #

class Portfolio(UUIDModel):
    """User's portfolio holdings"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="portfolios")
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name="portfolio_holdings")
    shares = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True, null=True)

    # Use higher precision + Decimal math for money
    average_price = models.DecimalField(max_digits=12, decimal_places=4, default=Decimal("0"))
    current_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    total_value = models.DecimalField(max_digits=16, decimal_places=4, blank=True, null=True)

    class Meta(UUIDModel.Meta):
        constraints = [
            UniqueConstraint(fields=["user", "stock"], name="uq_portfolio_user_stock"),
        ]
        ordering = ["-updated_at"]
        indexes = [
            Index(fields=["user", "-updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.name} - {self.stock.symbol} ({self.shares} shares)"

    def save(self, *args, **kwargs):
        """
        - Compute total_value = current_price * shares (Decimal-safe)
        - If average_price not set but current_price is, initialize from current_price
        """
        if self.current_price is not None and self.shares:
            self.total_value = (Decimal(self.current_price) * Decimal(self.shares)).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )
        if (self.average_price is None or self.average_price == 0) and self.current_price is not None:
            self.average_price = Decimal(self.current_price)
        super().save(*args, **kwargs)


# ------------------------------ Discussions -------------------------------- #

class StockDiscussion(UUIDModel):
    """Reddit-like stock discussion posts"""

    class Visibility(models.TextChoices):
        PUBLIC = "public", "Public - Everyone can see"
        FOLLOWERS = "followers", "Followers Only - Only followers can see"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="discussions")
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name="discussions", null=True, blank=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    discussion_type = models.CharField(max_length=20, default="general")
    visibility = models.CharField(max_length=10, choices=Visibility.choices, default=Visibility.FOLLOWERS)

    # Existing table compatibility
    is_analysis = models.BooleanField(default=False)
    analysis_data = models.TextField(blank=True, null=True)

    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    is_pinned = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)

    class Meta(UUIDModel.Meta):
        ordering = ["-created_at"]
        indexes = [
            Index(fields=["user", "-created_at"]),
            Index(fields=["stock", "-created_at"]),
            Index(fields=["-upvotes"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} by {self.user.name}"

    @property
    def score(self) -> int:
        return (self.upvotes or 0) - (self.downvotes or 0)

    @property
    def comment_count(self) -> int:
        return self.comments.count()


class DiscussionComment(UUIDModel):
    """Comments on stock discussions (supports nesting via parent_comment)"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="discussion_comments")
    discussion = models.ForeignKey(StockDiscussion, on_delete=models.CASCADE, related_name="comments")
    parent_comment = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )
    content = models.TextField()
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    is_deleted = models.BooleanField(default=False)

    class Meta(UUIDModel.Meta):
        ordering = ["-created_at"]
        indexes = [
            Index(fields=["discussion", "-created_at"]),
            Index(fields=["parent_comment", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"Comment by {self.user.name} on {self.discussion.title}"

    @property
    def score(self) -> int:
        return (self.upvotes or 0) - (self.downvotes or 0)

    @property
    def reply_count(self) -> int:
        return self.replies.count()