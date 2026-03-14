"""
Weekly Wealth Digest Service
=============================
Generates personalized weekly wealth summaries.
Part of the "Hooked" engagement loop - the Variable Reward.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import math

from .investor_profile_types import (
    InvestorProfile,
    CoachingTone,
    UserMaturityStage,
)
from .ai_coaching_service import ai_coaching_service


class DigestHighlightType(Enum):
    """Types of highlights in the weekly digest."""
    PORTFOLIO_GROWTH = "portfolio_growth"
    LEAK_SAVINGS = "leak_savings"
    MILESTONE_PROGRESS = "milestone_progress"
    GOAL_ACCELERATION = "goal_acceleration"
    BIAS_IMPROVEMENT = "bias_improvement"
    CONTRIBUTION_STREAK = "contribution_streak"
    MARKET_BEAT = "market_beat"


@dataclass
class DigestHighlight:
    """A single highlight in the weekly digest."""
    type: DigestHighlightType
    headline: str
    value: str
    subtext: str
    icon: str
    color: str
    is_positive: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "headline": self.headline,
            "value": self.value,
            "subtext": self.subtext,
            "icon": self.icon,
            "color": self.color,
            "is_positive": self.is_positive,
        }


@dataclass
class WeeklyWealthDigest:
    """Complete weekly wealth digest."""
    user_id: str
    week_ending: datetime
    
    # Hero metrics
    portfolio_value: float
    portfolio_change_amount: float
    portfolio_change_percent: float
    
    # Goal progress
    days_closer_to_goal: int
    goal_progress_percent: float
    estimated_goal_date: Optional[datetime] = None
    
    # Behavioral wins
    leaks_redirected_amount: float = 0.0
    contributions_this_week: float = 0.0
    contribution_streak_days: int = 0
    
    # Market context
    sp500_change_percent: float = 0.0
    beat_market: bool = False
    
    # Highlights
    highlights: List[DigestHighlight] = field(default_factory=list)
    
    # Coaching message (personalized by archetype)
    coaching_headline: str = ""
    coaching_message: str = ""
    coaching_tone: str = ""
    
    # Next best action
    next_action_headline: str = ""
    next_action_screen: str = ""
    
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "week_ending": self.week_ending.isoformat(),
            "portfolio_value": self.portfolio_value,
            "portfolio_change_amount": self.portfolio_change_amount,
            "portfolio_change_percent": self.portfolio_change_percent,
            "days_closer_to_goal": self.days_closer_to_goal,
            "goal_progress_percent": self.goal_progress_percent,
            "estimated_goal_date": self.estimated_goal_date.isoformat() if self.estimated_goal_date else None,
            "leaks_redirected_amount": self.leaks_redirected_amount,
            "contributions_this_week": self.contributions_this_week,
            "contribution_streak_days": self.contribution_streak_days,
            "sp500_change_percent": self.sp500_change_percent,
            "beat_market": self.beat_market,
            "highlights": [h.to_dict() for h in self.highlights],
            "coaching_headline": self.coaching_headline,
            "coaching_message": self.coaching_message,
            "coaching_tone": self.coaching_tone,
            "next_action_headline": self.next_action_headline,
            "next_action_screen": self.next_action_screen,
            "generated_at": self.generated_at.isoformat(),
        }


class WeeklyWealthDigestService:
    """
    Generates personalized weekly wealth digests.
    
    The digest is designed to be the "Variable Reward" in the Hooked loop:
    - Always show progress (even small wins)
    - Quantify the future value of actions
    - Connect to millionaire timeline
    - Personalize based on archetype
    """

    def __init__(self):
        self.assumed_annual_return = 0.07

    def generate_digest(
        self,
        user_id: str,
        profile: InvestorProfile,
        portfolio_data: Dict[str, Any],
        activity_data: Dict[str, Any],
        market_data: Dict[str, Any],
    ) -> WeeklyWealthDigest:
        """
        Generate a complete weekly digest.
        
        Args:
            user_id: User identifier
            profile: User's investor profile
            portfolio_data: {
                current_value, previous_value, change_amount, change_percent,
                contributions_this_week, goal_amount, current_progress_percent
            }
            activity_data: {
                leaks_redirected_amount, contribution_streak_days,
                app_opens, trades_count
            }
            market_data: {
                sp500_change_percent
            }
        
        Returns:
            WeeklyWealthDigest with all metrics and personalized messaging
        """
        now = datetime.utcnow()
        week_ending = now - timedelta(days=now.weekday())  # Last Sunday
        
        # Extract data
        portfolio_value = portfolio_data.get("current_value", 0)
        portfolio_change = portfolio_data.get("change_amount", 0)
        portfolio_change_pct = portfolio_data.get("change_percent", 0)
        contributions = portfolio_data.get("contributions_this_week", 0)
        goal_amount = portfolio_data.get("goal_amount", 1_000_000)
        goal_progress = portfolio_data.get("current_progress_percent", 0)
        
        leaks_redirected = activity_data.get("leaks_redirected_amount", 0)
        streak_days = activity_data.get("contribution_streak_days", 0)
        
        sp500_change = market_data.get("sp500_change_percent", 0)
        beat_market = portfolio_change_pct > sp500_change
        
        # Calculate days closer to goal
        days_closer = self._calculate_days_closer(
            portfolio_change + contributions + leaks_redirected,
            goal_amount,
            portfolio_value,
        )
        
        # Estimate goal date
        estimated_goal_date = self._estimate_goal_date(
            portfolio_value,
            goal_amount,
            contributions + leaks_redirected,  # Monthly contribution estimate
        )
        
        # Generate highlights
        highlights = self._generate_highlights(
            profile=profile,
            portfolio_change=portfolio_change,
            portfolio_change_pct=portfolio_change_pct,
            contributions=contributions,
            leaks_redirected=leaks_redirected,
            streak_days=streak_days,
            beat_market=beat_market,
            sp500_change=sp500_change,
            days_closer=days_closer,
        )
        
        # Generate coaching message
        coaching = self._generate_coaching_message(
            profile=profile,
            portfolio_change=portfolio_change,
            portfolio_change_pct=portfolio_change_pct,
            days_closer=days_closer,
            leaks_redirected=leaks_redirected,
            beat_market=beat_market,
        )
        
        # Determine next action
        next_action = self._get_next_action(profile, activity_data)
        
        return WeeklyWealthDigest(
            user_id=user_id,
            week_ending=week_ending,
            portfolio_value=portfolio_value,
            portfolio_change_amount=portfolio_change,
            portfolio_change_percent=portfolio_change_pct,
            days_closer_to_goal=days_closer,
            goal_progress_percent=goal_progress,
            estimated_goal_date=estimated_goal_date,
            leaks_redirected_amount=leaks_redirected,
            contributions_this_week=contributions,
            contribution_streak_days=streak_days,
            sp500_change_percent=sp500_change,
            beat_market=beat_market,
            highlights=highlights,
            coaching_headline=coaching["headline"],
            coaching_message=coaching["message"],
            coaching_tone=profile.coaching_tone.value,
            next_action_headline=next_action["headline"],
            next_action_screen=next_action["screen"],
        )

    def _calculate_days_closer(
        self,
        weekly_progress: float,
        goal_amount: float,
        current_value: float,
    ) -> int:
        """Calculate how many days closer to the goal based on this week's progress."""
        if weekly_progress <= 0 or goal_amount <= current_value:
            return 0
        
        remaining = goal_amount - current_value
        # Estimate weeks remaining at current pace
        weeks_remaining = remaining / max(weekly_progress, 1)
        
        # Compare to if we hadn't made this week's progress
        weeks_remaining_without = remaining / max(weekly_progress * 0.9, 1)
        
        days_saved = (weeks_remaining_without - weeks_remaining) * 7
        return max(0, int(days_saved))

    def _estimate_goal_date(
        self,
        current_value: float,
        goal_amount: float,
        monthly_contribution: float,
    ) -> Optional[datetime]:
        """Estimate when the goal will be reached."""
        if current_value >= goal_amount:
            return datetime.utcnow()
        
        if monthly_contribution <= 0:
            return None
        
        # Use future value formula to estimate years
        r = self.assumed_annual_return / 12
        remaining = goal_amount - current_value
        
        # Solve for n: FV = PV(1+r)^n + PMT*((1+r)^n - 1)/r
        # Approximation using log
        try:
            n = math.log(
                (remaining * r / monthly_contribution) + 1
            ) / math.log(1 + r)
            months = max(0, int(n))
            return datetime.utcnow() + timedelta(days=months * 30)
        except (ValueError, ZeroDivisionError):
            return None

    def _generate_highlights(
        self,
        profile: InvestorProfile,
        portfolio_change: float,
        portfolio_change_pct: float,
        contributions: float,
        leaks_redirected: float,
        streak_days: int,
        beat_market: bool,
        sp500_change: float,
        days_closer: int,
    ) -> List[DigestHighlight]:
        """Generate the highlight cards for the digest."""
        highlights = []
        
        # Portfolio growth (always show if positive)
        if portfolio_change > 0:
            highlights.append(DigestHighlight(
                type=DigestHighlightType.PORTFOLIO_GROWTH,
                headline="Portfolio Growth",
                value=f"+${portfolio_change:,.0f}",
                subtext=f"+{portfolio_change_pct:.1f}% this week",
                icon="trending-up",
                color="#10B981",
                is_positive=True,
            ))
        elif portfolio_change < 0:
            # Still show, but reframe it
            highlights.append(DigestHighlight(
                type=DigestHighlightType.PORTFOLIO_GROWTH,
                headline="Market Volatility",
                value=f"${portfolio_change:,.0f}",
                subtext="Short-term noise, long-term signal",
                icon="activity",
                color="#F59E0B",
                is_positive=False,
            ))
        
        # Leak savings (behavioral win)
        if leaks_redirected > 0:
            future_value = self._calculate_future_value(leaks_redirected, 20)
            highlights.append(DigestHighlight(
                type=DigestHighlightType.LEAK_SAVINGS,
                headline="Leaks Redirected",
                value=f"${leaks_redirected:.0f}/mo",
                subtext=f"Worth ${future_value:,.0f} in 20 years",
                icon="shield",
                color="#6366F1",
                is_positive=True,
            ))
        
        # Goal acceleration
        if days_closer > 0:
            highlights.append(DigestHighlight(
                type=DigestHighlightType.GOAL_ACCELERATION,
                headline="Goal Acceleration",
                value=f"{days_closer} days closer",
                subtext="To your millionaire date",
                icon="zap",
                color="#10B981",
                is_positive=True,
            ))
        
        # Beat the market
        if beat_market and portfolio_change_pct > 0:
            diff = portfolio_change_pct - sp500_change
            highlights.append(DigestHighlight(
                type=DigestHighlightType.MARKET_BEAT,
                headline="Beat the Market",
                value=f"+{diff:.1f}%",
                subtext=f"S&P 500 was {sp500_change:+.1f}%",
                icon="award",
                color="#F59E0B",
                is_positive=True,
            ))
        
        # Contribution streak
        if streak_days >= 7:
            highlights.append(DigestHighlight(
                type=DigestHighlightType.CONTRIBUTION_STREAK,
                headline="Contribution Streak",
                value=f"{streak_days} days",
                subtext="Consistency builds wealth",
                icon="flame",
                color="#EF4444",
                is_positive=True,
            ))
        
        # Limit to top 4 highlights
        return highlights[:4]

    def _generate_coaching_message(
        self,
        profile: InvestorProfile,
        portfolio_change: float,
        portfolio_change_pct: float,
        days_closer: int,
        leaks_redirected: float,
        beat_market: bool,
    ) -> Dict[str, str]:
        """Generate personalized coaching message based on archetype."""
        tone = profile.coaching_tone
        
        # Positive week
        if portfolio_change > 0:
            if tone == CoachingTone.THE_GUARDIAN:
                headline = "Your Fortress Grew Stronger"
                message = (
                    f"Your portfolio added ${portfolio_change:,.0f} to your defenses this week. "
                    f"That's {days_closer} days closer to total financial security. "
                    "The walls are rising — keep building."
                )
            elif tone == CoachingTone.THE_ARCHITECT:
                headline = "The System Is Working"
                message = (
                    f"+${portfolio_change:,.0f} this week — the math of compounding in action. "
                    f"You're now {days_closer} days ahead of schedule. "
                    "No intervention needed; the machine is running."
                )
            elif tone == CoachingTone.THE_SCOUT:
                headline = "Gains Captured"
                message = (
                    f"${portfolio_change:,.0f} added to your war chest. "
                    f"{'You beat the market this week — sharp positioning.' if beat_market else ''} "
                    f"{days_closer} days closer to the summit."
                )
            else:  # THE_STABILIZER
                headline = "Steady Progress"
                message = (
                    f"Your portfolio grew ${portfolio_change:,.0f} without any stress or drama. "
                    f"That's {days_closer} days closer to your goal. "
                    "This is what calm, consistent investing looks like."
                )
        
        # Negative week
        elif portfolio_change < 0:
            if tone == CoachingTone.THE_GUARDIAN:
                headline = "Your Foundation Holds"
                message = (
                    f"Markets were choppy, but your fortress stands. "
                    "This volatility is temporary; your emergency fund protects you. "
                    "No action needed — stay protected."
                )
            elif tone == CoachingTone.THE_ARCHITECT:
                headline = "Volatility Within Parameters"
                message = (
                    f"A {abs(portfolio_change_pct):.1f}% pullback — within historical norms. "
                    "The system was designed for weeks like this. "
                    "Continue contributions; buy the dip automatically."
                )
            elif tone == CoachingTone.THE_SCOUT:
                headline = "Opportunity Brewing"
                message = (
                    f"Market down {abs(portfolio_change_pct):.1f}% — that's a discount forming. "
                    "Scouts don't panic; they position. "
                    "Consider this week's contributions a strategic buy."
                )
            else:  # THE_STABILIZER
                headline = "Stay the Course"
                message = (
                    "I know a down week feels uncomfortable. "
                    "But remember: your plan was built for days like this. "
                    "The long-term trend is what matters, not this week's noise."
                )
        
        # Flat week
        else:
            headline = "Holding Steady"
            message = (
                "A quiet week in the markets. "
                "Your portfolio maintained its value. "
                "Consistency over excitement — that's how wealth is built."
            )
        
        # Add leak savings celebration if applicable
        if leaks_redirected > 0:
            future_value = self._calculate_future_value(leaks_redirected, 20)
            message += f" Plus, you redirected ${leaks_redirected:.0f}/mo in leaks — worth ${future_value:,.0f} long-term!"
        
        return {
            "headline": headline,
            "message": message,
        }

    def _get_next_action(
        self,
        profile: InvestorProfile,
        activity_data: Dict[str, Any],
    ) -> Dict[str, str]:
        """Determine the suggested next action."""
        # Check if they haven't taken the quiz
        # Check various activity indicators
        
        # Default suggestions based on maturity
        if profile.maturity_stage == UserMaturityStage.STARTER:
            return {
                "headline": "Find more leaks to redirect",
                "screen": "LeakRedirect",
            }
        elif profile.maturity_stage == UserMaturityStage.BUILDER:
            return {
                "headline": "Review your portfolio allocation",
                "screen": "AIPortfolioBuilder",
            }
        else:
            return {
                "headline": "Check for optimization opportunities",
                "screen": "Reallocate",
            }

    def _calculate_future_value(
        self,
        monthly_amount: float,
        years: int,
    ) -> float:
        """Calculate future value of monthly contributions."""
        r = self.assumed_annual_return / 12
        n = years * 12
        if r == 0:
            return monthly_amount * n
        return monthly_amount * (((1 + r) ** n - 1) / r)


# ══════════════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ══════════════════════════════════════════════════════════════════════════════

wealth_digest_service = WeeklyWealthDigestService()
