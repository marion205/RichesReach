"""
Futures Policy Engine - Phase 3
Suitability gates, max loss caps, leverage limits

Simple: Check before every trade
"""

import logging
from typing import Dict, Optional, Tuple
from enum import Enum

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
        # Policy limits
        self.max_loss_per_trade = 100.0  # $100 max loss per trade (micro contracts)
        self.max_portfolio_loss = 500.0  # $500 max loss across all positions
        self.max_leverage = 20.0  # 20:1 max leverage
        self.max_concentration = 0.10  # 10% of portfolio max in futures
        
        # Suitability thresholds
        self.suitability_score_min = 70  # Minimum score for futures approval
        self.suitability_experience_min = 2  # Minimum experience level (1-5)
    
    def check_suitability(
        self,
        user_profile: Dict,
        recommendation: Dict,
    ) -> Tuple[SuitabilityLevel, str]:
        """
        Check if user is suitable for this futures trade.
        
        Args:
            user_profile: User's profile with risk tolerance, experience, etc.
            recommendation: The futures recommendation
            
        Returns:
            (SuitabilityLevel, reason_message)
        """
        try:
            # Get user suitability score (simplified)
            suitability_score = user_profile.get("suitability_score", 0)
            experience_level = user_profile.get("futures_experience", 0)
            account_value = user_profile.get("account_value", 0)
            
            # Check minimum requirements
            if suitability_score < self.suitability_score_min:
                return (
                    SuitabilityLevel.BLOCKED,
                    f"Suitability score {suitability_score} below minimum {self.suitability_score_min}",
                )
            
            if experience_level < self.suitability_experience_min:
                return (
                    SuitabilityLevel.RESTRICTED,
                    "Insufficient futures trading experience",
                )
            
            if account_value < 5000:
                return (
                    SuitabilityLevel.RESTRICTED,
                    "Minimum account value $5,000 required for futures",
                )
            
            # Check max loss for this trade
            max_loss = recommendation.get("max_loss", 0)
            if max_loss > self.max_loss_per_trade:
                return (
                    SuitabilityLevel.BLOCKED,
                    f"Max loss ${max_loss} exceeds per-trade limit ${self.max_loss_per_trade}",
                )
            
            # If all checks pass
            if suitability_score >= 85 and experience_level >= 4:
                return (SuitabilityLevel.APPROVED, "Approved for futures trading")
            elif suitability_score >= self.suitability_score_min:
                return (SuitabilityLevel.CAUTION, "Approved with caution - start with micro contracts")
            else:
                return (SuitabilityLevel.RESTRICTED, "Restricted - needs review")
                
        except Exception as e:
            logger.error(f"Error checking suitability: {e}")
            return (SuitabilityLevel.BLOCKED, f"Error: {e}")
    
    def check_guardrails(
        self,
        user_profile: Dict,
        order: Dict,
        existing_positions: List[Dict],
    ) -> Tuple[bool, str]:
        """
        Check guardrails before placing order.
        
        Args:
            user_profile: User profile
            order: Order details (symbol, side, quantity)
            existing_positions: Existing futures positions
            
        Returns:
            (allowed, reason)
        """
        try:
            account_value = user_profile.get("account_value", 0)
            symbol = order.get("symbol", "")
            quantity = order.get("quantity", 0)
            
            # Check leverage limit
            # Simplified: assume $50 margin per micro contract
            total_margin = len(existing_positions) * 50 + quantity * 50
            leverage = (total_margin * 20) / account_value if account_value > 0 else 0  # 20:1 leverage assumption
            
            if leverage > self.max_leverage:
                return (
                    False,
                    f"Leverage {leverage:.1f}:1 exceeds limit {self.max_leverage}:1",
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
                    f"Futures concentration {concentration:.1%} exceeds limit {self.max_concentration:.1%}",
                )
            
            # Check max portfolio loss
            total_pnl = sum(pos.get("pnl", 0) for pos in existing_positions)
            if total_pnl < -self.max_portfolio_loss:
                return (
                    False,
                    f"Portfolio loss ${total_pnl:.2f} exceeds limit ${self.max_portfolio_loss}",
                )
            
            return (True, "Guardrails passed")
            
        except Exception as e:
            logger.error(f"Error checking guardrails: {e}")
            return (False, f"Error: {e}")
    
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
        }


# Global policy engine
_policy_engine: Optional[FuturesPolicyEngine] = None


def get_policy_engine() -> FuturesPolicyEngine:
    """Get global policy engine instance"""
    global _policy_engine
    if _policy_engine is None:
        _policy_engine = FuturesPolicyEngine()
    return _policy_engine

