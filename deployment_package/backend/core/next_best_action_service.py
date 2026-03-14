"""
Next Best Action (NBA) Service
==============================
The "Traffic Controller" that prioritizes which action the user should see.
Implements the Hierarchy of Financial Needs (The Simple Path logic).
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import math

from .investor_profile_types import (
    InvestorProfile,
    UserMaturityStage,
    DefaultStrategy,
    InvestorArchetype,
)


class ActionPriority(Enum):
    """Priority levels in the financial needs hierarchy."""
    CRITICAL = 1       # Stop financial bleeding
    SAFETY_NET = 2     # Build emergency fund
    DEBT_REDUCTION = 3 # Kill high-interest debt
    FOUNDATION = 4     # Tax-advantaged accounts, employer match
    GROWTH = 5         # Long-term investing
    OPTIMIZATION = 6   # Portfolio optimization, tax strategies
    ADVANCED = 7       # Alternative investments, advanced strategies


class ActionType(Enum):
    """Types of actions the NBA engine can suggest."""
    CANCEL_LEAK = "cancel_leak"
    BUILD_EMERGENCY_FUND = "build_emergency_fund"
    PAY_DEBT = "pay_debt"
    CAPTURE_MATCH = "capture_match"
    START_INVESTING = "start_investing"
    INCREASE_CONTRIBUTION = "increase_contribution"
    REBALANCE = "rebalance"
    REDUCE_CONCENTRATION = "reduce_concentration"
    TAX_LOSS_HARVEST = "tax_loss_harvest"
    REDUCE_FEES = "reduce_fees"
    REDIRECT_SAVINGS = "redirect_savings"


@dataclass
class NextBestAction:
    """A recommended action for the user."""
    id: str
    action_type: ActionType
    priority: ActionPriority
    priority_score: float  # 0-100, higher = more urgent
    
    # Display content
    headline: str
    description: str
    impact_text: str
    
    # The numbers
    monthly_amount: float = 0.0
    total_impact: float = 0.0
    time_impact_days: int = 0  # Days closer to millionaire date
    
    # Action details
    action_label: str = "Take Action"
    action_screen: str = ""
    action_params: Dict[str, Any] = field(default_factory=dict)
    
    # Coaching context
    reasoning: str = ""
    
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "action_type": self.action_type.value,
            "priority": self.priority.value,
            "priority_score": self.priority_score,
            "headline": self.headline,
            "description": self.description,
            "impact_text": self.impact_text,
            "monthly_amount": self.monthly_amount,
            "total_impact": self.total_impact,
            "time_impact_days": self.time_impact_days,
            "action_label": self.action_label,
            "action_screen": self.action_screen,
            "action_params": self.action_params,
            "reasoning": self.reasoning,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class UserFinancialState:
    """Current financial state used for NBA calculations."""
    # Assets
    total_assets: float = 0.0
    liquid_cash: float = 0.0
    invested_assets: float = 0.0
    retirement_accounts: float = 0.0
    
    # Income & Expenses
    monthly_income: float = 0.0
    monthly_expenses: float = 0.0
    monthly_savings: float = 0.0
    
    # Debt
    total_debt: float = 0.0
    high_interest_debt: float = 0.0  # APR > 8%
    highest_debt_apr: float = 0.0
    
    # Emergency fund
    emergency_fund_months: float = 0.0
    emergency_fund_target: float = 0.0  # 3-6 months expenses
    
    # Employer benefits
    has_401k_match: bool = False
    match_percent: float = 0.0
    current_401k_contribution_percent: float = 0.0
    annual_match_left_on_table: float = 0.0
    
    # Leaks
    total_monthly_leaks: float = 0.0
    leak_count: int = 0
    leaks: List[Dict[str, Any]] = field(default_factory=list)
    
    # Portfolio
    portfolio_concentration_score: float = 0.0
    portfolio_fee_drag: float = 0.0
    has_rebalancing_opportunity: bool = False
    
    # Goals
    millionaire_target_date: Optional[datetime] = None
    years_to_goal: float = 0.0


class NextBestActionService:
    """
    The NBA Engine — decides what action the user should focus on.
    
    Uses the "Waterfall" priority system:
    1. Critical Leaks (>$20/mo, low usage)
    2. Safety Net (Emergency Fund < 3 months)
    3. High-Interest Debt (APR > 8%)
    4. Employer Match (free money!)
    5. Millionaire Path (automated investing)
    6. Portfolio Optimization (fees, concentration, rebalancing)
    """

    def __init__(self):
        # Investment assumptions
        self.assumed_annual_return = 0.07  # 7% average return
        self.monthly_return = self.assumed_annual_return / 12

    def calculate_future_value(
        self,
        monthly_amount: float,
        years: float,
        annual_rate: float = 0.07,
    ) -> float:
        """Calculate future value of monthly contributions."""
        r = annual_rate / 12
        n = int(years * 12)
        if r == 0:
            return monthly_amount * n
        return monthly_amount * (((1 + r) ** n - 1) / r)

    def calculate_time_impact(
        self,
        monthly_amount: float,
        current_savings_rate: float,
        goal_amount: float = 1_000_000,
        current_portfolio: float = 0,
    ) -> int:
        """
        Calculate how many days closer to the goal this monthly amount gets you.
        
        Returns days saved toward the millionaire date.
        """
        if current_savings_rate <= 0:
            return 0
        
        # Time to goal without the extra amount
        remaining = goal_amount - current_portfolio
        if remaining <= 0:
            return 0
        
        # Approximate using simple compound growth
        r = self.assumed_annual_return
        
        # With current rate
        years_current = math.log(
            (remaining * r / (current_savings_rate * 12)) + 1
        ) / math.log(1 + r) if current_savings_rate > 0 else 100
        
        # With additional amount
        new_rate = current_savings_rate + monthly_amount
        years_new = math.log(
            (remaining * r / (new_rate * 12)) + 1
        ) / math.log(1 + r) if new_rate > 0 else 100
        
        days_saved = (years_current - years_new) * 365
        return max(0, int(days_saved))

    def get_next_best_actions(
        self,
        profile: InvestorProfile,
        state: UserFinancialState,
        max_actions: int = 3,
    ) -> List[NextBestAction]:
        """
        Generate prioritized list of recommended actions.
        
        Returns up to max_actions, sorted by priority.
        """
        actions: List[NextBestAction] = []
        
        # ── Priority 1: Critical Leaks ─────────────────────────────────────
        if state.total_monthly_leaks > 20:
            leak_fv = self.calculate_future_value(
                state.total_monthly_leaks,
                20,  # 20 years
            )
            time_impact = self.calculate_time_impact(
                state.total_monthly_leaks,
                state.monthly_savings,
                current_portfolio=state.invested_assets,
            )
            
            actions.append(NextBestAction(
                id="leak_critical",
                action_type=ActionType.CANCEL_LEAK,
                priority=ActionPriority.CRITICAL,
                priority_score=95,
                headline=f"Stop ${state.total_monthly_leaks:.0f}/mo in leaks",
                description=f"We found {state.leak_count} subscriptions draining your wealth.",
                impact_text=f"Worth ${leak_fv:,.0f} in 20 years",
                monthly_amount=state.total_monthly_leaks,
                total_impact=leak_fv,
                time_impact_days=time_impact,
                action_label="Review Leaks",
                action_screen="LeakDetector",
                reasoning="These recurring charges are the easiest money to redirect. "
                          "Cancel what you don't use and watch your millionaire date move closer.",
            ))
        
        # ── Priority 2: Emergency Fund ─────────────────────────────────────
        if state.emergency_fund_months < 3:
            gap = (3 - state.emergency_fund_months) * state.monthly_expenses
            monthly_needed = gap / 12  # Fill gap in 1 year
            
            # Suppress investment suggestions if no safety net
            priority_score = 90 if state.emergency_fund_months < 1 else 80
            
            actions.append(NextBestAction(
                id="emergency_fund",
                action_type=ActionType.BUILD_EMERGENCY_FUND,
                priority=ActionPriority.SAFETY_NET,
                priority_score=priority_score,
                headline="Build your financial fortress",
                description=f"You have {state.emergency_fund_months:.1f} months of expenses saved. "
                            f"Target: 3-6 months.",
                impact_text=f"Need ${gap:,.0f} to hit 3-month target",
                monthly_amount=monthly_needed,
                total_impact=gap,
                action_label="Start Saving",
                action_screen="FinancialHealth",
                reasoning="Before aggressive investing, you need a safety net. "
                          "This protects you from having to sell investments at the worst time.",
            ))
        
        # ── Priority 3: High-Interest Debt ─────────────────────────────────
        if state.high_interest_debt > 0 and state.highest_debt_apr > 8:
            # This is a "guaranteed" return equal to the APR
            guaranteed_return = state.high_interest_debt * (state.highest_debt_apr / 100)
            
            actions.append(NextBestAction(
                id="debt_payoff",
                action_type=ActionType.PAY_DEBT,
                priority=ActionPriority.DEBT_REDUCTION,
                priority_score=85,
                headline=f"Kill ${state.high_interest_debt:,.0f} in high-interest debt",
                description=f"Your {state.highest_debt_apr:.1f}% APR debt is a 'guaranteed' negative return.",
                impact_text=f"Saves ${guaranteed_return:,.0f}/year in interest",
                monthly_amount=state.high_interest_debt / 12,
                total_impact=guaranteed_return,
                action_label="Debt Snowball",
                action_screen="FinancialHealth",
                reasoning="Paying off high-interest debt IS investing — "
                          f"you're earning a guaranteed {state.highest_debt_apr:.1f}% return.",
            ))
        
        # ── Priority 4: Employer Match ─────────────────────────────────────
        if state.has_401k_match and state.annual_match_left_on_table > 0:
            actions.append(NextBestAction(
                id="capture_match",
                action_type=ActionType.CAPTURE_MATCH,
                priority=ActionPriority.FOUNDATION,
                priority_score=82,
                headline=f"Capture ${state.annual_match_left_on_table:,.0f}/year in free money",
                description="Your employer match is the best 'investment' you'll ever make — "
                            "it's an instant 50-100% return.",
                impact_text="100% guaranteed return",
                monthly_amount=state.annual_match_left_on_table / 12,
                total_impact=state.annual_match_left_on_table * 20,  # 20 years of match
                action_label="Increase 401k",
                action_screen="FinancialHealth",
                reasoning="Never leave free money on the table. "
                          "Increase your 401k contribution to at least capture the full match.",
            ))
        
        # ── Priority 5: Millionaire Path (Start/Increase Investing) ────────
        # Only suggest if safety net + debt are handled
        if (
            state.emergency_fund_months >= 3
            and state.high_interest_debt == 0
            and state.monthly_savings > 0
        ):
            # Calculate optimal additional investment
            suggested_increase = min(
                state.monthly_savings * 0.2,  # 20% of current savings
                500,  # Cap at $500/mo suggestion
            )
            
            fv = self.calculate_future_value(suggested_increase, 20)
            time_impact = self.calculate_time_impact(
                suggested_increase,
                state.monthly_savings,
                current_portfolio=state.invested_assets,
            )
            
            actions.append(NextBestAction(
                id="increase_investing",
                action_type=ActionType.INCREASE_CONTRIBUTION,
                priority=ActionPriority.GROWTH,
                priority_score=70,
                headline=f"Add ${suggested_increase:.0f}/mo to your wealth engine",
                description="Your foundation is solid. Time to accelerate.",
                impact_text=f"Worth ${fv:,.0f} in 20 years | {time_impact} days closer to goal",
                monthly_amount=suggested_increase,
                total_impact=fv,
                time_impact_days=time_impact,
                action_label="Boost Investment",
                action_screen="AIPortfolioBuilder",
                reasoning="With your safety net in place and debt cleared, "
                          "every extra dollar you invest now has decades to compound.",
            ))
        
        # ── Priority 6: Portfolio Optimization ─────────────────────────────
        # Concentration issues
        if state.portfolio_concentration_score > 60:
            actions.append(NextBestAction(
                id="reduce_concentration",
                action_type=ActionType.REDUCE_CONCENTRATION,
                priority=ActionPriority.OPTIMIZATION,
                priority_score=55,
                headline="Diversify your concentrated positions",
                description="Your portfolio is heavily weighted in a few names. "
                            "This increases risk without necessarily increasing return.",
                impact_text="Reduce single-point-of-failure risk",
                action_label="Rebalance",
                action_screen="Reallocate",
                reasoning="Concentration feels like conviction, but it's also concentrated risk. "
                          "Consider redirecting future contributions to broader funds.",
            ))
        
        # Fee drag
        if state.portfolio_fee_drag > 0.5:  # >0.5% annual fees
            annual_fee_cost = state.invested_assets * (state.portfolio_fee_drag / 100)
            
            actions.append(NextBestAction(
                id="reduce_fees",
                action_type=ActionType.REDUCE_FEES,
                priority=ActionPriority.OPTIMIZATION,
                priority_score=50,
                headline=f"Save ${annual_fee_cost:,.0f}/year in fees",
                description=f"Your portfolio's {state.portfolio_fee_drag:.2f}% fee drag "
                            "compounds against you over time.",
                impact_text=f"~${annual_fee_cost * 20:,.0f} saved over 20 years",
                total_impact=annual_fee_cost * 20,
                action_label="Lower Fees",
                action_screen="Reallocate",
                reasoning="Low fees are one of the few 'free lunches' in investing. "
                          "A 1% fee difference can cost you 25% of your wealth over 30 years.",
            ))
        
        # ── Sort by priority score and return top N ────────────────────────
        actions.sort(key=lambda a: a.priority_score, reverse=True)
        return actions[:max_actions]

    def get_leak_redirect_suggestion(
        self,
        profile: InvestorProfile,
        leak_amount: float,
        state: UserFinancialState,
    ) -> NextBestAction:
        """
        When user cancels a leak, where should that money go?
        
        Follows the Simple Path priority:
        1. Emergency fund if under target
        2. Debt reduction if APR high
        3. Recurring ETF contribution otherwise
        """
        # Calculate future value of the redirect
        fv = self.calculate_future_value(leak_amount, 20)
        time_impact = self.calculate_time_impact(
            leak_amount,
            state.monthly_savings,
            current_portfolio=state.invested_assets,
        )
        
        # Priority 1: Emergency Fund
        if state.emergency_fund_months < 3:
            return NextBestAction(
                id="redirect_to_emergency",
                action_type=ActionType.REDIRECT_SAVINGS,
                priority=ActionPriority.SAFETY_NET,
                priority_score=90,
                headline=f"Redirect ${leak_amount:.0f}/mo to your fortress",
                description="Let's strengthen your emergency fund before investing.",
                impact_text=f"Reach 3-month target {int(leak_amount / state.monthly_expenses * 30)} days sooner",
                monthly_amount=leak_amount,
                action_label="Redirect to Savings",
                action_screen="FinancialHealth",
                reasoning="Your safety net comes first. Once you have 3 months of expenses saved, "
                          "we'll redirect this to investments.",
            )
        
        # Priority 2: High-Interest Debt
        if state.high_interest_debt > 0 and state.highest_debt_apr > 8:
            monthly_interest_saved = (state.high_interest_debt * state.highest_debt_apr / 100) / 12
            payoff_months = state.high_interest_debt / leak_amount
            
            return NextBestAction(
                id="redirect_to_debt",
                action_type=ActionType.REDIRECT_SAVINGS,
                priority=ActionPriority.DEBT_REDUCTION,
                priority_score=85,
                headline=f"Redirect ${leak_amount:.0f}/mo to crush your debt",
                description=f"This accelerates your debt payoff by {payoff_months:.0f} months.",
                impact_text=f"Saves ~${monthly_interest_saved:.0f}/mo in interest",
                monthly_amount=leak_amount,
                action_label="Attack Debt",
                action_screen="FinancialHealth",
                reasoning=f"Your {state.highest_debt_apr:.1f}% APR debt is costing you. "
                          "Paying it off IS investing — a guaranteed return equal to the APR.",
            )
        
        # Priority 3: Investing (The Simple Path)
        # Get suggested ETF based on archetype
        suggested_etf = self._get_default_etf(profile)
        
        return NextBestAction(
            id="redirect_to_invest",
            action_type=ActionType.REDIRECT_SAVINGS,
            priority=ActionPriority.GROWTH,
            priority_score=75,
            headline=f"Redirect ${leak_amount:.0f}/mo to your Millionaire Path",
            description=f"This becomes ${fv:,.0f} over 20 years.",
            impact_text=f"Moves your goal {time_impact} days closer",
            monthly_amount=leak_amount,
            total_impact=fv,
            time_impact_days=time_impact,
            action_label=f"Invest in {suggested_etf}",
            action_screen="AIPortfolioBuilder",
            action_params={"suggested_etf": suggested_etf, "amount": leak_amount},
            reasoning=f"Your foundation is solid. {suggested_etf} is a low-cost way to "
                      "capture broad market growth — the 'Simple Path' to wealth.",
        )

    def _get_default_etf(self, profile: InvestorProfile) -> str:
        """Get the default ETF suggestion based on user archetype."""
        etf_map = {
            DefaultStrategy.SIMPLE_PATH_CORE: "VTI",
            DefaultStrategy.INCOME_STABILITY: "SCHD",
            DefaultStrategy.GROWTH_INNOVATION: "QQQM",
            DefaultStrategy.HIGH_CONVICTION: "VTI",  # Still recommend diversified
        }
        return etf_map.get(profile.default_strategy, "VTI")


# ══════════════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ══════════════════════════════════════════════════════════════════════════════

next_best_action_service = NextBestActionService()
