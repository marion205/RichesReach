"""
Identity Gap Service
=====================
Compares user's quiz-stated behavior to their actual behavior.
Triggers interventions when there's a significant gap.

Example: User says they're a "Steady Builder" but checks the app 10x/day during a dip.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from .investor_profile_types import (
    InvestorProfile,
    InvestorArchetype,
    CoachingTone,
    BiasType,
)
from .ai_coaching_service import ai_coaching_service, CoachingMessage


class GapType(Enum):
    """Types of identity gaps that can be detected."""
    ANXIETY_GAP = "anxiety_gap"           # Claims calm but shows anxiety
    ACTIVITY_GAP = "activity_gap"         # Claims passive but trades frequently
    RISK_GAP = "risk_gap"                 # Claims risk-tolerant but sells during dips
    CONCENTRATION_GAP = "concentration_gap"  # Claims diversified but concentrates
    CONSISTENCY_GAP = "consistency_gap"   # Claims systematic but is erratic


class GapSeverity(Enum):
    """Severity levels for identity gaps."""
    MILD = "mild"           # Slight deviation, gentle nudge
    MODERATE = "moderate"   # Notable deviation, coaching message
    SEVERE = "severe"       # Major deviation, intervention needed


@dataclass
class IdentityGap:
    """A detected gap between stated and actual behavior."""
    gap_type: GapType
    severity: GapSeverity
    
    # What they said vs what they did
    stated_behavior: str
    actual_behavior: str
    
    # Metrics
    gap_score: float  # 0-100, higher = bigger gap
    
    # Intervention
    headline: str
    message: str
    suggested_action: str
    action_screen: str
    
    detected_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gap_type": self.gap_type.value,
            "severity": self.severity.value,
            "stated_behavior": self.stated_behavior,
            "actual_behavior": self.actual_behavior,
            "gap_score": self.gap_score,
            "headline": self.headline,
            "message": self.message,
            "suggested_action": self.suggested_action,
            "action_screen": self.action_screen,
            "detected_at": self.detected_at.isoformat(),
        }


@dataclass
class BehaviorMetrics:
    """User's actual behavior metrics for gap detection."""
    # Activity
    app_opens_7d: int = 0
    app_opens_during_volatility: int = 0  # Opens when market is down >2%
    trades_30d: int = 0
    
    # Reactions
    sells_during_dips: int = 0  # Sells when position down >10%
    buys_during_rallies: int = 0  # Buys when position up >20%
    panic_sell_count: int = 0
    
    # Portfolio behavior
    concentration_percent: float = 0.0  # % in top 3 holdings
    sector_concentration: float = 0.0
    turnover_rate: float = 0.0  # Annual turnover
    
    # Consistency
    contribution_streak_days: int = 0
    missed_contributions: int = 0
    strategy_changes_30d: int = 0


class IdentityGapService:
    """
    Detects gaps between stated identity (quiz) and actual behavior.
    
    This is the "Behavioral Coaching Engine" that provides gentle
    interventions when users deviate from their stated profile.
    """

    def __init__(self):
        # Thresholds for gap detection
        self.anxiety_app_opens_threshold = 21  # >3x/day for 7 days
        self.high_activity_trades_threshold = 8  # >8 trades/month
        self.panic_sell_threshold = 2  # >2 panic sells triggers alert
        self.concentration_threshold = 50  # >50% in top 3

    def detect_gaps(
        self,
        profile: InvestorProfile,
        metrics: BehaviorMetrics,
        market_context: Optional[Dict[str, Any]] = None,
    ) -> List[IdentityGap]:
        """
        Analyze user behavior and detect identity gaps.
        
        Returns list of gaps sorted by severity.
        """
        gaps: List[IdentityGap] = []
        
        # 1. Anxiety Gap
        anxiety_gap = self._detect_anxiety_gap(profile, metrics, market_context)
        if anxiety_gap:
            gaps.append(anxiety_gap)
        
        # 2. Activity Gap
        activity_gap = self._detect_activity_gap(profile, metrics)
        if activity_gap:
            gaps.append(activity_gap)
        
        # 3. Risk Gap
        risk_gap = self._detect_risk_gap(profile, metrics)
        if risk_gap:
            gaps.append(risk_gap)
        
        # 4. Concentration Gap
        concentration_gap = self._detect_concentration_gap(profile, metrics)
        if concentration_gap:
            gaps.append(concentration_gap)
        
        # 5. Consistency Gap
        consistency_gap = self._detect_consistency_gap(profile, metrics)
        if consistency_gap:
            gaps.append(consistency_gap)
        
        # Sort by severity (most severe first)
        severity_order = {
            GapSeverity.SEVERE: 0,
            GapSeverity.MODERATE: 1,
            GapSeverity.MILD: 2,
        }
        gaps.sort(key=lambda g: severity_order[g.severity])
        
        return gaps

    def _detect_anxiety_gap(
        self,
        profile: InvestorProfile,
        metrics: BehaviorMetrics,
        market_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[IdentityGap]:
        """
        Detect if user is showing more anxiety than their profile suggests.
        
        Signal: High app opens, especially during market volatility.
        """
        # Expected anxiety based on quiz loss_aversion score
        expected_anxiety = profile.dimensions.loss_aversion / 100  # 0-1
        
        # Actual anxiety signal
        daily_opens = metrics.app_opens_7d / 7
        volatility_opens = metrics.app_opens_during_volatility
        
        # Calculate anxiety score (0-100)
        anxiety_score = min(100, (daily_opens / 5) * 50 + (volatility_opens * 10))
        
        # Expected vs actual
        gap_score = max(0, anxiety_score - (expected_anxiety * 100))
        
        if gap_score < 20:
            return None  # No significant gap
        
        severity = self._get_severity(gap_score)
        
        # Get archetype-appropriate messaging
        messages = self._get_anxiety_messages(profile, daily_opens, gap_score)
        
        return IdentityGap(
            gap_type=GapType.ANXIETY_GAP,
            severity=severity,
            stated_behavior=f"Loss aversion: {profile.dimensions.loss_aversion:.0f}/100 (quiz)",
            actual_behavior=f"Checking app {daily_opens:.1f}x/day, {volatility_opens} times during volatility",
            gap_score=gap_score,
            headline=messages["headline"],
            message=messages["message"],
            suggested_action="See your 20-year projection",
            action_screen="WealthArrival",
        )

    def _detect_activity_gap(
        self,
        profile: InvestorProfile,
        metrics: BehaviorMetrics,
    ) -> Optional[IdentityGap]:
        """
        Detect if user is trading more than their profile suggests.
        
        Steady Builders shouldn't be active traders.
        """
        # Expected activity based on archetype
        expected_activity = {
            InvestorArchetype.CAUTIOUS_PROTECTOR: 2,  # trades/month
            InvestorArchetype.STEADY_BUILDER: 1,
            InvestorArchetype.OPPORTUNITY_HUNTER: 8,
            InvestorArchetype.REACTIVE_TRADER: 4,  # They may trade more but we want to help
        }
        
        expected = expected_activity.get(profile.archetype, 2)
        actual = metrics.trades_30d
        
        if actual <= expected * 1.5:
            return None  # Within expected range
        
        gap_score = min(100, ((actual - expected) / expected) * 50)
        severity = self._get_severity(gap_score)
        
        messages = self._get_activity_messages(profile, actual, expected)
        
        return IdentityGap(
            gap_type=GapType.ACTIVITY_GAP,
            severity=severity,
            stated_behavior=f"Archetype: {profile.archetype_title} (~{expected} trades/month typical)",
            actual_behavior=f"{actual} trades in the last 30 days",
            gap_score=gap_score,
            headline=messages["headline"],
            message=messages["message"],
            suggested_action="Review your automated strategy",
            action_screen="AIPortfolioBuilder",
        )

    def _detect_risk_gap(
        self,
        profile: InvestorProfile,
        metrics: BehaviorMetrics,
    ) -> Optional[IdentityGap]:
        """
        Detect if user sells during dips despite claiming high risk tolerance.
        """
        if profile.dimensions.risk_tolerance < 50:
            return None  # They said they're risk-averse, selling is expected
        
        if metrics.panic_sell_count < 2:
            return None  # No significant pattern
        
        gap_score = min(100, metrics.panic_sell_count * 30)
        severity = self._get_severity(gap_score)
        
        return IdentityGap(
            gap_type=GapType.RISK_GAP,
            severity=severity,
            stated_behavior=f"Risk tolerance: {profile.dimensions.risk_tolerance:.0f}/100 (quiz)",
            actual_behavior=f"{metrics.panic_sell_count} panic sells during market dips",
            gap_score=gap_score,
            headline="Your Actions Don't Match Your Plan",
            message=(
                f"Your quiz said you could handle volatility (risk tolerance: {profile.dimensions.risk_tolerance:.0f}/100). "
                f"But you've sold {metrics.panic_sell_count} times during dips. "
                "This 'sell low' behavior can significantly hurt long-term returns. "
                "Let's revisit your risk comfort level."
            ),
            suggested_action="Retake the investor quiz",
            action_screen="InvestorQuiz",
        )

    def _detect_concentration_gap(
        self,
        profile: InvestorProfile,
        metrics: BehaviorMetrics,
    ) -> Optional[IdentityGap]:
        """
        Detect if user concentrates despite claiming to prefer diversification.
        """
        # Check if they indicated preference for diversification in quiz
        # (This would come from their archetype and quiz answers)
        if profile.archetype == InvestorArchetype.OPPORTUNITY_HUNTER:
            return None  # Concentration is expected for this archetype
        
        if metrics.concentration_percent < 40:
            return None  # Reasonably diversified
        
        gap_score = min(100, (metrics.concentration_percent - 30) * 2)
        severity = self._get_severity(gap_score)
        
        return IdentityGap(
            gap_type=GapType.CONCENTRATION_GAP,
            severity=severity,
            stated_behavior=f"Archetype: {profile.archetype_title} (prefers diversification)",
            actual_behavior=f"{metrics.concentration_percent:.0f}% of portfolio in top 3 holdings",
            gap_score=gap_score,
            headline="Your Portfolio Doesn't Match Your Profile",
            message=(
                f"As a {profile.archetype_title}, diversification aligns with your goals. "
                f"But {metrics.concentration_percent:.0f}% of your portfolio is in just 3 holdings. "
                "Consider directing future contributions to broader funds."
            ),
            suggested_action="Explore rebalancing options",
            action_screen="Reallocate",
        )

    def _detect_consistency_gap(
        self,
        profile: InvestorProfile,
        metrics: BehaviorMetrics,
    ) -> Optional[IdentityGap]:
        """
        Detect if user is inconsistent despite claiming to be systematic.
        """
        if profile.archetype != InvestorArchetype.STEADY_BUILDER:
            return None  # Only applies to Steady Builders
        
        # Check for inconsistency signals
        inconsistency_score = (
            metrics.missed_contributions * 10 +
            metrics.strategy_changes_30d * 20 -
            min(30, metrics.contribution_streak_days)  # Streak reduces score
        )
        
        if inconsistency_score < 20:
            return None  # Reasonably consistent
        
        gap_score = min(100, inconsistency_score)
        severity = self._get_severity(gap_score)
        
        return IdentityGap(
            gap_type=GapType.CONSISTENCY_GAP,
            severity=severity,
            stated_behavior="Archetype: Steady Builder (values consistency and automation)",
            actual_behavior=(
                f"{metrics.missed_contributions} missed contributions, "
                f"{metrics.strategy_changes_30d} strategy changes in 30 days"
            ),
            gap_score=gap_score,
            headline="Your System Needs Attention",
            message=(
                "As a Steady Builder, your strength is consistency. "
                "But recent activity shows some deviation from your system. "
                "Let's get your automated contributions back on track."
            ),
            suggested_action="Review automated investments",
            action_screen="AIPortfolioBuilder",
        )

    def _get_severity(self, gap_score: float) -> GapSeverity:
        """Determine severity based on gap score."""
        if gap_score >= 60:
            return GapSeverity.SEVERE
        elif gap_score >= 35:
            return GapSeverity.MODERATE
        else:
            return GapSeverity.MILD

    def _get_anxiety_messages(
        self,
        profile: InvestorProfile,
        daily_opens: float,
        gap_score: float,
    ) -> Dict[str, str]:
        """Get archetype-appropriate anxiety intervention messages."""
        
        tone = profile.coaching_tone
        
        if tone == CoachingTone.THE_GUARDIAN:
            return {
                "headline": "Your Fortress Is Safe",
                "message": (
                    f"I've noticed you're checking your portfolio more often ({daily_opens:.0f}x/day). "
                    "Remember: your emergency fund is your shield. "
                    "Market noise can't break through your defenses. "
                    "Your fortress was built for days like this."
                ),
            }
        elif tone == CoachingTone.THE_ARCHITECT:
            return {
                "headline": "System Check: Anxiety Detected",
                "message": (
                    f"Data shows {daily_opens:.0f} app opens per day — above your baseline. "
                    "This pattern often indicates anxiety overriding your systematic approach. "
                    "The math hasn't changed. Your 20-year projection is still on track. "
                    "Consider reducing check frequency to once per week."
                ),
            }
        elif tone == CoachingTone.THE_SCOUT:
            return {
                "headline": "Easy, Scout",
                "message": (
                    f"You're checking the app {daily_opens:.0f}x/day. "
                    "Real opportunity doesn't require constant monitoring. "
                    "Set your positions and let the market come to you. "
                    "Over-watching leads to over-trading."
                ),
            }
        else:  # THE_STABILIZER
            return {
                "headline": "Take a Breath",
                "message": (
                    f"I see you've been checking your portfolio {daily_opens:.0f} times per day. "
                    "It's natural to feel anxious during volatility. "
                    "But remember: your quiz said you're building for the long term. "
                    "This moment will pass. Your plan is still working."
                ),
            }

    def _get_activity_messages(
        self,
        profile: InvestorProfile,
        actual_trades: int,
        expected_trades: int,
    ) -> Dict[str, str]:
        """Get archetype-appropriate activity intervention messages."""
        
        tone = profile.coaching_tone
        
        if tone == CoachingTone.THE_GUARDIAN:
            return {
                "headline": "Protect Your Returns",
                "message": (
                    f"You've made {actual_trades} trades this month — "
                    f"more than expected for a Protector ({expected_trades}/month). "
                    "Each trade has costs and tax implications. "
                    "Your fortress grows stronger through patience, not activity."
                ),
            }
        elif tone == CoachingTone.THE_ARCHITECT:
            return {
                "headline": "System Deviation Alert",
                "message": (
                    f"{actual_trades} trades this month vs {expected_trades} expected. "
                    "Research shows retail traders who trade more often underperform. "
                    "Your automated system was designed to minimize this friction. "
                    "Consider letting the machine run."
                ),
            }
        elif tone == CoachingTone.THE_SCOUT:
            return {
                "headline": "Over-Trading Alert",
                "message": (
                    f"{actual_trades} trades this month is high, even for a Scout. "
                    "Activity can feel productive, but transaction costs compound against you. "
                    "The best scouts are patient — they wait for the right opportunity."
                ),
            }
        else:  # THE_STABILIZER
            return {
                "headline": "Slow Down",
                "message": (
                    f"You've made {actual_trades} trades this month. "
                    "High activity often comes from anxiety, not strategy. "
                    "Your long-term plan doesn't require frequent adjustments. "
                    "Less action often means better results."
                ),
            }

    def generate_intervention(
        self,
        profile: InvestorProfile,
        gap: IdentityGap,
    ) -> CoachingMessage:
        """
        Generate a full coaching intervention for a detected gap.
        """
        return CoachingMessage(
            headline=gap.headline,
            body=gap.message,
            tone=profile.coaching_tone.value,
            cta_text=gap.suggested_action,
            cta_action=gap.action_screen,
        )


# ══════════════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ══════════════════════════════════════════════════════════════════════════════

identity_gap_service = IdentityGapService()
