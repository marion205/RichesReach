"""
Futures Policy Engine - Phase 3
Suitability gates, max loss caps, leverage limits

Simple: Check before every trade
"""

import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum

from core.futures.why_not import WhyNotResponse, why_not_guardrail, why_not_suitability

logger = logging.getLogger(__name__)


class SuitabilityLevel(Enum):
    APPROVED = "approved"
    CAUTION = "caution"
    RESTRICTED = "restricted"
    BLOCKED = "blocked"


class FuturesPolicyEngine:
    """
    Policy engine for futures trading.
    
    Enforces:
    - Suitability gates
    - Max loss caps
    - Leverage limits
    - Concentration limits
    """
    
    def __init__(self):
        # Policy limits (will be made dynamic)
        self.max_loss_per_trade_base = 100.0  # Base max loss per trade
        self.max_portfolio_loss = 500.0  # $500 max loss across all positions
        self.max_leverage = 20.0  # 20:1 max leverage
        self.max_concentration = 0.10  # 10% of portfolio max in futures
        
        # Suitability thresholds
        self.suitability_score_min = 70  # Minimum score for futures approval
        self.suitability_experience_min = 2  # Minimum experience level (1-5)
    
    def dynamic_max_loss(self, equity_usd: float, realized_vol: float = 0.15) -> float:
        """
        Calculate dynamic max loss based on equity and volatility.
        
        Args:
            equity_usd: Account equity in USD
            realized_vol: Realized volatility (0-1)
            
        Returns:
            Dynamic max loss limit
        """
        # Base: min($100, 0.5% of equity)
        base = min(self.max_loss_per_trade_base, 0.005 * equity_usd)
        
        # Volatility adjustment: shrink when vol ↑
        vol_adjustment = max(0.5, 1.5 - 5 * realized_vol)
        
        dynamic = base * vol_adjustment
        return round(dynamic, 2)
    
    def check_suitability(
        self,
        user_profile: Dict,
        recommendation: Dict,
    ) -> Tuple[SuitabilityLevel, Optional[WhyNotResponse]]:
        """
        Check if user is suitable for this futures trade.
        
        Args:
            user_profile: User's profile with risk tolerance, experience, etc.
            recommendation: The futures recommendation
            
        Returns:
            (SuitabilityLevel, why_not_response) - why_not is None if approved
        """
        try:
            # Get user suitability score (simplified)
            suitability_score = user_profile.get("suitability_score", 0)
            experience_level = user_profile.get("futures_experience", 0)
            account_value = user_profile.get("account_value", 0)
            realized_vol = user_profile.get("realized_volatility", 0.15)
            
            # Check minimum requirements
            if suitability_score < self.suitability_score_min or experience_level < self.suitability_experience_min:
                return (
                    SuitabilityLevel.BLOCKED,
                    why_not_suitability(suitability_score, self.suitability_score_min, experience_level, self.suitability_experience_min),
                )
            
            if account_value < 5000:
                return (
                    SuitabilityLevel.RESTRICTED,
                    why_not_guardrail(
                        "margin",
                        account_value,
                        5000.0,
                        "Increase account value to $5,000+",
                    ),
                )
            
            # Check max loss for this trade (dynamic)
            max_loss = recommendation.get("max_loss", 0)
            dynamic_max = self.dynamic_max_loss(account_value, realized_vol)
            if max_loss > dynamic_max:
                return (
                    SuitabilityLevel.BLOCKED,
                    why_not_guardrail(
                        "max_loss",
                        max_loss,
                        dynamic_max,
                        f"Reduce size to ${dynamic_max:.2f} or less",
                    ),
                )
            
            # If all checks pass
            if suitability_score >= 85 and experience_level >= 4:
                return (SuitabilityLevel.APPROVED, None)
            elif suitability_score >= self.suitability_score_min:
                return (SuitabilityLevel.CAUTION, None)  # Approved with caution
            else:
                return (
                    SuitabilityLevel.RESTRICTED,
                    WhyNotResponse(
                        blocked=True,
                        reason="Account restricted - needs review",
                        fix="Contact support or complete additional education",
                    ),
                )
                
        except Exception as e:
            logger.error(f"Error checking suitability: {e}")
            return (
                SuitabilityLevel.BLOCKED,
                WhyNotResponse(
                    blocked=True,
                    reason=f"Error: {e}",
                    fix="Please try again or contact support",
                ),
            )
    
    def check_guardrails(
        self,
        user_profile: Dict,
        order: Dict,
        existing_positions: List[Dict],
        recommendation: Optional[Dict] = None,
    ) -> Tuple[bool, Optional[WhyNotResponse]]:
        """
        Check guardrails before placing order.
        
        Args:
            user_profile: User profile
            order: Order details (symbol, side, quantity)
            existing_positions: Existing futures positions
            recommendation: Optional recommendation with max_loss
            
        Returns:
            (allowed, why_not_response) - why_not is None if allowed
        """
        try:
            account_value = user_profile.get("account_value", 0)
            realized_vol = user_profile.get("realized_volatility", 0.15)
            symbol = order.get("symbol", "")
            quantity = order.get("quantity", 0)
            
            # Dynamic max loss
            max_loss = self.dynamic_max_loss(account_value, realized_vol)
            
            # Check max loss for this trade
            if recommendation:
                trade_max_loss = recommendation.get("max_loss", 0)
                if trade_max_loss > max_loss:
                    return (
                        False,
                        why_not_guardrail(
                            "max_loss",
                            trade_max_loss,
                            max_loss,
                            f"Reduce size to ${max_loss:.2f} or less",
                        ),
                    )
            
            # Check leverage limit
            # Simplified: assume $50 margin per micro contract
            total_margin = len(existing_positions) * 50 + quantity * 50
            leverage = (total_margin * 20) / account_value if account_value > 0 else 0  # 20:1 leverage assumption
            
            if leverage > self.max_leverage:
                return (
                    False,
                    why_not_guardrail(
                        "leverage",
                        leverage,
                        self.max_leverage,
                        "Reduce position size or add cash",
                    ),
                )
            
            # Check concentration limit
            futures_notional = sum(
                pos.get("quantity", 0) * pos.get("entry_price", 0) * 50  # Simplified
                for pos in existing_positions
            )
            futures_notional += quantity * 5000 * 50  # New position estimate
            
            concentration = futures_notional / account_value if account_value > 0 else 0
            
            if concentration > self.max_concentration:
                return (
                    False,
                    why_not_guardrail(
                        "concentration",
                        concentration,
                        self.max_concentration,
                        "Reduce futures exposure or increase account value",
                    ),
                )
            
            # Check max portfolio loss
            total_pnl = sum(pos.get("pnl", 0) for pos in existing_positions)
            if total_pnl < -self.max_portfolio_loss:
                return (
                    False,
                    why_not_guardrail(
                        "portfolio_loss",
                        abs(total_pnl),
                        self.max_portfolio_loss,
                        "Close losing positions or add cash",
                    ),
                )
            
            return (True, None)  # All checks passed
            
        except Exception as e:
            logger.error(f"Error checking guardrails: {e}")
            return (
                False,
                WhyNotResponse(
                    blocked=True,
                    reason=f"Error checking guardrails: {e}",
                    fix="Please try again or contact support",
                ),
            )
    
    def get_user_profile(self, user_id: int) -> Dict:
        """
        Get user profile for policy checks.
        
        In production, this would query the database.
        For now, return a mock profile.
        """
        # TODO: Query database for actual user profile
        return {
            "user_id": user_id,
            "suitability_score": 75,  # Mock score
            "futures_experience": 3,  # Mock experience (1-5)
            "account_value": 10000.0,  # Mock account value
            "risk_tolerance": "medium",
            "realized_volatility": 0.15,  # Mock volatility (15% annualized)
        }


# Global policy engine
_policy_engine: Optional[FuturesPolicyEngine] = None


def get_policy_engine() -> FuturesPolicyEngine:
    """Get global policy engine instance"""
    global _policy_engine
    if _policy_engine is None:
        _policy_engine = FuturesPolicyEngine()
    return _policy_engine

