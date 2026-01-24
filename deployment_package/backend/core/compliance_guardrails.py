# core/compliance_guardrails.py
"""
Compliance Guardrails for High-Stakes Financial Actions

Ensures "Review & Confirm" flow before executing trades, especially for:
- Tax-Smart Portfolio Transitions (TSPT)
- Large direct indexing allocations
- Significant tax-loss harvesting

This mitigates liability and ensures user understanding.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ActionType(str, Enum):
    """Types of actions requiring review"""
    TSPT_TRANSITION = "tspt_transition"
    DIRECT_INDEX_CREATION = "direct_index_creation"
    LARGE_TAX_LOSS_HARVEST = "large_tax_loss_harvest"
    PORTFOLIO_REBALANCE = "portfolio_rebalance"


class ReviewStatus(str, Enum):
    """Review status"""
    PENDING = "pending"
    REVIEWED = "reviewed"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


@dataclass
class ComplianceReview:
    """Compliance review record"""
    action_type: ActionType
    action_data: Dict[str, Any]
    estimated_tax_impact: float
    estimated_cost: float
    risk_level: str  # "low", "medium", "high"
    requires_confirmation: bool
    review_status: ReviewStatus
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    user_id: Optional[str] = None


class ComplianceGuardrails:
    """
    Compliance guardrails for financial actions.
    
    Ensures:
    - User review before high-stakes actions
    - Clear disclosure of risks and costs
    - Audit trail for regulatory compliance
    """
    
    def __init__(self):
        """Initialize compliance guardrails"""
        self.reviews: Dict[str, ComplianceReview] = {}  # In production, use database
    
    def requires_review(
        self,
        action_type: ActionType,
        action_data: Dict[str, Any],
        portfolio_value: float = 0
    ) -> bool:
        """
        Determine if action requires review and confirmation.
        
        Review required for:
        - TSPT transitions > $50k
        - Direct index creation > $100k
        - Tax-loss harvest > $10k
        - Any action with high risk
        """
        if action_type == ActionType.TSPT_TRANSITION:
            concentrated_value = action_data.get("concentrated_position", {}).get("quantity", 0) * \
                                action_data.get("concentrated_position", {}).get("current_price", 0)
            return concentrated_value > 50000
        
        elif action_type == ActionType.DIRECT_INDEX_CREATION:
            return portfolio_value > 100000
        
        elif action_type == ActionType.LARGE_TAX_LOSS_HARVEST:
            potential_savings = action_data.get("total_tax_savings", 0)
            return potential_savings > 10000
        
        elif action_type == ActionType.PORTFOLIO_REBALANCE:
            rebalance_amount = action_data.get("rebalance_amount", 0)
            return rebalance_amount > 50000
        
        return False
    
    def create_review(
        self,
        action_type: ActionType,
        action_data: Dict[str, Any],
        user_id: Optional[str] = None,
        portfolio_value: float = 0
    ) -> ComplianceReview:
        """
        Create a compliance review record.
        
        Returns review that must be confirmed before execution.
        """
        # Calculate estimated impact
        estimated_tax_impact = self._estimate_tax_impact(action_type, action_data)
        estimated_cost = self._estimate_cost(action_type, action_data)
        risk_level = self._assess_risk_level(action_type, action_data)
        
        review = ComplianceReview(
            action_type=action_type,
            action_data=action_data,
            estimated_tax_impact=estimated_tax_impact,
            estimated_cost=estimated_cost,
            risk_level=risk_level,
            requires_confirmation=True,
            review_status=ReviewStatus.PENDING,
            created_at=datetime.now(),
            user_id=user_id
        )
        
        # Store review (in production, save to database)
        review_id = f"{action_type.value}_{datetime.now().timestamp()}"
        self.reviews[review_id] = review
        
        logger.info(f"Created compliance review: {review_id} for {action_type.value}")
        
        return review
    
    def get_review_summary(self, review: ComplianceReview) -> Dict[str, Any]:
        """
        Get human-readable summary of review for user display.
        
        This is what the user sees in the "Review & Confirm" UI.
        """
        action_descriptions = {
            ActionType.TSPT_TRANSITION: "Tax-Smart Portfolio Transition",
            ActionType.DIRECT_INDEX_CREATION: "Direct Index Portfolio Creation",
            ActionType.LARGE_TAX_LOSS_HARVEST: "Large Tax-Loss Harvesting",
            ActionType.PORTFOLIO_REBALANCE: "Portfolio Rebalancing"
        }
        
        risk_descriptions = {
            "low": "Low risk - Standard portfolio management action",
            "medium": "Medium risk - Tax implications should be reviewed",
            "high": "High risk - Significant tax and portfolio impact"
        }
        
        return {
            "action_name": action_descriptions.get(review.action_type, "Financial Action"),
            "action_type": review.action_type.value,
            "estimated_tax_impact": review.estimated_tax_impact,
            "estimated_cost": review.estimated_cost,
            "risk_level": review.risk_level,
            "risk_description": risk_descriptions.get(review.risk_level, ""),
            "requires_confirmation": review.requires_confirmation,
            "disclosures": self._generate_disclosures(review),
            "created_at": review.created_at.isoformat()
        }
    
    def confirm_review(
        self,
        review_id: str,
        user_confirmation: bool = True
    ) -> bool:
        """
        Confirm a review, allowing action to proceed.
        
        Args:
            review_id: ID of the review
            user_confirmation: Whether user confirmed
            
        Returns:
            True if confirmed, False otherwise
        """
        if review_id not in self.reviews:
            logger.warning(f"Review not found: {review_id}")
            return False
        
        review = self.reviews[review_id]
        
        if user_confirmation:
            review.review_status = ReviewStatus.CONFIRMED
            review.confirmed_at = datetime.now()
            logger.info(f"Review confirmed: {review_id}")
            return True
        else:
            review.review_status = ReviewStatus.REJECTED
            review.reviewed_at = datetime.now()
            logger.info(f"Review rejected: {review_id}")
            return False
    
    def _estimate_tax_impact(
        self,
        action_type: ActionType,
        action_data: Dict[str, Any]
    ) -> float:
        """Estimate tax impact of action"""
        if action_type == ActionType.TSPT_TRANSITION:
            # Get total gains from transition plan
            transition_plan = action_data.get("transition_plan", [])
            total_gains = sum(month.get("gain_on_sale", 0) for month in transition_plan)
            # Estimate tax at 15% (long-term) or 20% (high bracket)
            return total_gains * 0.20  # Conservative estimate
        
        elif action_type == ActionType.DIRECT_INDEX_CREATION:
            # Direct indexing itself doesn't create tax impact
            # But enables future tax savings
            return 0.0
        
        elif action_type == ActionType.LARGE_TAX_LOSS_HARVEST:
            # Tax savings (negative impact = savings)
            return -action_data.get("total_tax_savings", 0)
        
        return 0.0
    
    def _estimate_cost(
        self,
        action_type: ActionType,
        action_data: Dict[str, Any]
    ) -> float:
        """Estimate transaction costs"""
        if action_type == ActionType.TSPT_TRANSITION:
            # Transaction costs for selling
            total_sales = sum(month.get("sale_amount", 0) for month in action_data.get("transition_plan", []))
            return total_sales * 0.001  # 0.1% transaction cost
        
        elif action_type == ActionType.DIRECT_INDEX_CREATION:
            # Initial setup costs
            portfolio_value = action_data.get("portfolio_value", 0)
            return portfolio_value * 0.0005  # 0.05% setup cost
        
        elif action_type == ActionType.LARGE_TAX_LOSS_HARVEST:
            # Transaction costs for harvesting
            opportunities = action_data.get("opportunities", [])
            total_value = sum(opp.get("unrealized_loss", 0) for opp in opportunities)
            return total_value * 0.001  # 0.1% transaction cost
        
        return 0.0
    
    def _assess_risk_level(
        self,
        action_type: ActionType,
        action_data: Dict[str, Any]
    ) -> str:
        """Assess risk level of action"""
        if action_type == ActionType.TSPT_TRANSITION:
            concentrated_value = action_data.get("concentrated_position", {}).get("quantity", 0) * \
                                action_data.get("concentrated_position", {}).get("current_price", 0)
            if concentrated_value > 500000:
                return "high"
            elif concentrated_value > 100000:
                return "medium"
            else:
                return "low"
        
        elif action_type == ActionType.DIRECT_INDEX_CREATION:
            return "low"  # Generally low risk
        
        elif action_type == ActionType.LARGE_TAX_LOSS_HARVEST:
            return "low"  # Tax optimization is low risk
        
        return "medium"
    
    def _generate_disclosures(self, review: ComplianceReview) -> List[str]:
        """Generate compliance disclosures"""
        disclosures = []
        
        if review.action_type == ActionType.TSPT_TRANSITION:
            disclosures.extend([
                "This transition plan involves selling concentrated positions over multiple years.",
                "Tax implications will vary based on your income and tax bracket.",
                "Market conditions may affect the optimal timing of sales.",
                "Consult with a tax professional before executing large transitions."
            ])
        
        elif review.action_type == ActionType.DIRECT_INDEX_CREATION:
            disclosures.extend([
                "Direct indexing involves owning individual stocks instead of an ETF.",
                "Tracking error may result in performance differences vs. the benchmark.",
                "Tax benefits depend on market conditions and loss harvesting opportunities.",
                "Transaction costs may reduce net benefits."
            ])
        
        disclosures.append(
            "This is not personalized tax or investment advice. "
            "Past performance does not guarantee future results."
        )
        
        return disclosures


# Singleton instance
_compliance_guardrails = ComplianceGuardrails()


def get_compliance_guardrails() -> ComplianceGuardrails:
    """Get singleton compliance guardrails instance"""
    return _compliance_guardrails

