"""
GraphQL Types and Resolvers for Weekly Wealth Digest & Identity Gap
====================================================================
"""

import graphene
from datetime import datetime

from .wealth_digest_service import (
    wealth_digest_service,
    WeeklyWealthDigest,
    DigestHighlightType,
)
from .identity_gap_service import (
    identity_gap_service,
    IdentityGap,
    BehaviorMetrics,
    GapType,
    GapSeverity,
)
from .investor_profile_service import investor_profile_service
from .investor_profile_types import (
    InvestorProfile,
    InvestorArchetype,
    CoachingTone,
    UserMaturityStage,
    QuizDimensions,
    BiasMatrix,
    BiasScore,
    BiasType,
)


# ══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ══════════════════════════════════════════════════════════════════════════════

class DigestHighlightTypeEnum(graphene.Enum):
    """GraphQL enum for digest highlight types."""
    PORTFOLIO_GROWTH = "portfolio_growth"
    LEAK_SAVINGS = "leak_savings"
    MILESTONE_PROGRESS = "milestone_progress"
    GOAL_ACCELERATION = "goal_acceleration"
    BIAS_IMPROVEMENT = "bias_improvement"
    CONTRIBUTION_STREAK = "contribution_streak"
    MARKET_BEAT = "market_beat"


class GapTypeEnum(graphene.Enum):
    """GraphQL enum for identity gap types."""
    ANXIETY_GAP = "anxiety_gap"
    ACTIVITY_GAP = "activity_gap"
    RISK_GAP = "risk_gap"
    CONCENTRATION_GAP = "concentration_gap"
    CONSISTENCY_GAP = "consistency_gap"


class GapSeverityEnum(graphene.Enum):
    """GraphQL enum for gap severity levels."""
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


# ══════════════════════════════════════════════════════════════════════════════
# OBJECT TYPES
# ══════════════════════════════════════════════════════════════════════════════

class DigestHighlightType(graphene.ObjectType):
    """A single highlight in the weekly digest."""
    type = graphene.String()
    headline = graphene.String()
    value = graphene.String()
    subtext = graphene.String()
    icon = graphene.String()
    color = graphene.String()
    is_positive = graphene.Boolean()


class WeeklyWealthDigestType(graphene.ObjectType):
    """Complete weekly wealth digest."""
    user_id = graphene.String()
    week_ending = graphene.String()
    
    portfolio_value = graphene.Float()
    portfolio_change_amount = graphene.Float()
    portfolio_change_percent = graphene.Float()
    
    days_closer_to_goal = graphene.Int()
    goal_progress_percent = graphene.Float()
    estimated_goal_date = graphene.String()
    
    leaks_redirected_amount = graphene.Float()
    contributions_this_week = graphene.Float()
    contribution_streak_days = graphene.Int()
    
    sp500_change_percent = graphene.Float()
    beat_market = graphene.Boolean()
    
    highlights = graphene.List(DigestHighlightType)
    
    coaching_headline = graphene.String()
    coaching_message = graphene.String()
    coaching_tone = graphene.String()
    
    next_action_headline = graphene.String()
    next_action_screen = graphene.String()
    
    generated_at = graphene.String()


class IdentityGapType(graphene.ObjectType):
    """A detected gap between stated and actual behavior."""
    gap_type = GapTypeEnum()
    severity = GapSeverityEnum()
    stated_behavior = graphene.String()
    actual_behavior = graphene.String()
    gap_score = graphene.Float()
    headline = graphene.String()
    message = graphene.String()
    suggested_action = graphene.String()
    action_screen = graphene.String()
    detected_at = graphene.String()


# ══════════════════════════════════════════════════════════════════════════════
# QUERIES
# ══════════════════════════════════════════════════════════════════════════════

class WealthDigestQueries(graphene.ObjectType):
    """Queries for wealth digest and identity gap features."""
    
    weekly_wealth_digest = graphene.Field(
        WeeklyWealthDigestType,
        description="Get the user's weekly wealth digest"
    )
    
    identity_gaps = graphene.List(
        IdentityGapType,
        description="Get detected identity gaps (quiz vs actual behavior)"
    )
    
    def resolve_weekly_wealth_digest(self, info):
        """Resolve weekly wealth digest."""
        # In production, this would fetch real data
        # For demo mode, return mock data
        return {
            "user_id": "demo-user",
            "week_ending": "2026-03-09",
            "portfolio_value": 47832,
            "portfolio_change_amount": 1247,
            "portfolio_change_percent": 2.68,
            "days_closer_to_goal": 14,
            "goal_progress_percent": 4.78,
            "estimated_goal_date": "August 2041",
            "leaks_redirected_amount": 127,
            "contributions_this_week": 287,
            "contribution_streak_days": 23,
            "sp500_change_percent": 1.92,
            "beat_market": True,
            "highlights": [
                {
                    "type": "portfolio_growth",
                    "headline": "Portfolio Growth",
                    "value": "+$1,247",
                    "subtext": "+2.68% this week",
                    "icon": "trending-up",
                    "color": "#10B981",
                    "is_positive": True,
                },
                {
                    "type": "leak_savings",
                    "headline": "Leaks Redirected",
                    "value": "$127/mo",
                    "subtext": "Worth $63,450 in 20 years",
                    "icon": "shield",
                    "color": "#6366F1",
                    "is_positive": True,
                },
                {
                    "type": "goal_acceleration",
                    "headline": "Goal Acceleration",
                    "value": "14 days closer",
                    "subtext": "To your millionaire date",
                    "icon": "zap",
                    "color": "#10B981",
                    "is_positive": True,
                },
                {
                    "type": "market_beat",
                    "headline": "Beat the Market",
                    "value": "+0.76%",
                    "subtext": "S&P 500 was +1.92%",
                    "icon": "award",
                    "color": "#F59E0B",
                    "is_positive": True,
                },
            ],
            "coaching_headline": "The System Is Working",
            "coaching_message": (
                "+$1,247 this week — the math of compounding in action. "
                "You're now 14 days ahead of schedule. "
                "Plus, you redirected $127/mo in leaks — worth $63,450 long-term!"
            ),
            "coaching_tone": "the_architect",
            "next_action_headline": "Review your portfolio allocation",
            "next_action_screen": "AIPortfolioBuilder",
            "generated_at": datetime.utcnow().isoformat(),
        }
    
    def resolve_identity_gaps(self, info):
        """Resolve identity gaps."""
        # Demo data showing anxiety gap
        return [
            {
                "gap_type": GapTypeEnum.ANXIETY_GAP,
                "severity": GapSeverityEnum.MILD,
                "stated_behavior": "Loss aversion: 45/100 (quiz)",
                "actual_behavior": "Checking app 4.2x/day, 8 times during volatility",
                "gap_score": 28,
                "headline": "System Check: Anxiety Detected",
                "message": (
                    "Data shows 4.2 app opens per day — above your baseline. "
                    "This pattern often indicates anxiety overriding your systematic approach. "
                    "The math hasn't changed. Your 20-year projection is still on track."
                ),
                "suggested_action": "See your 20-year projection",
                "action_screen": "WealthArrival",
                "detected_at": datetime.utcnow().isoformat(),
            }
        ]
