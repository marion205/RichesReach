# core/tax_smart_transitions.py
"""
Tax-Smart Portfolio Transitions (TSPT)
Gradually transitions concentrated positions while maximizing tax benefits.

Ideal for:
- Concentrated employer stock
- Legacy positions with large gains
- Tax-efficient diversification

Integrates with RichesReach's existing tax-loss harvesting and portfolio management.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from .quantitative_algorithms import TaxLossHarvesting

logger = logging.getLogger(__name__)


class TaxSmartPortfolioTransitions:
    """
    TSPT: Gradually sell concentrated positions while harvesting losses.
    
    Strategy:
    - Sell more in years with losses to offset gains
    - Stay within tax brackets
    - Minimize tax drag
    """
    
    def __init__(self):
        """Initialize TSPT service"""
        self.tlh = TaxLossHarvesting()
    
    def create_transition_plan(
        self,
        concentrated_position: Dict[str, Any],  # {symbol, quantity, cost_basis, current_price}
        target_allocation: Dict[str, float],  # Target portfolio allocation
        time_horizon_months: int = 36,  # 3-year transition
        annual_income: float = 0,
        tax_bracket: str = "high",
        realized_gains: float = 0.0
    ) -> Dict[str, Any]:
        """
        Create a tax-smart transition plan.
        
        Args:
            concentrated_position: Position to transition
                - symbol: Stock symbol
                - quantity: Number of shares
                - cost_basis: Purchase price per share
                - current_price: Current market price
            target_allocation: Target portfolio allocation after transition
                - {symbol: weight} format
            time_horizon_months: Months to complete transition (default: 36)
            annual_income: Annual income for tax calculations
            tax_bracket: Tax bracket ("low", "medium", "high")
            realized_gains: Already realized gains to offset
            
        Returns:
            Transition plan with monthly sales and tax benefits
        """
        try:
            symbol = concentrated_position.get("symbol", "")
            quantity = concentrated_position.get("quantity", 0)
            cost_basis = concentrated_position.get("cost_basis", 0)
            current_price = concentrated_position.get("current_price", 0)
            
            if quantity <= 0 or cost_basis <= 0 or current_price <= 0:
                return {
                    "error": "Invalid position data",
                    "method": "tspt"
                }
            
            total_value = quantity * current_price
            unrealized_gain = (current_price - cost_basis) * quantity
            gain_per_share = current_price - cost_basis
            
            # Calculate optimal sale schedule
            monthly_sales = self._calculate_optimal_sale_schedule(
                total_value=total_value,
                quantity=quantity,
                time_horizon_months=time_horizon_months,
                unrealized_gain=unrealized_gain,
                gain_per_share=gain_per_share,
                annual_income=annual_income,
                tax_bracket=tax_bracket
            )
            
            # Calculate tax benefits from loss harvesting
            tax_benefits = self._calculate_transition_tax_benefits(
                monthly_sales=monthly_sales,
                cost_basis=cost_basis,
                current_price=current_price,
                annual_income=annual_income,
                tax_bracket=tax_bracket,
                realized_gains=realized_gains
            )
            
            # Calculate reinvestment strategy
            reinvestment_plan = self._create_reinvestment_plan(
                monthly_sales=monthly_sales,
                target_allocation=target_allocation
            )
            
            completion_date = datetime.now() + timedelta(days=time_horizon_months * 30)
            
            return {
                "transition_plan": monthly_sales,
                "total_tax_savings": tax_benefits["total_savings"],
                "total_capital_gains_tax": tax_benefits["total_capital_gains_tax"],
                "reinvestment_plan": reinvestment_plan,
                "estimated_completion_date": completion_date.isoformat(),
                "time_horizon_months": time_horizon_months,
                "method": "tspt"
            }
        
        except Exception as e:
            logger.error(f"Error creating TSPT plan: {e}")
            return {
                "error": str(e),
                "method": "tspt"
            }
    
    def _calculate_optimal_sale_schedule(
        self,
        total_value: float,
        quantity: float,
        time_horizon_months: int,
        unrealized_gain: float,
        gain_per_share: float,
        annual_income: float,
        tax_bracket: str
    ) -> List[Dict[str, Any]]:
        """
        Calculate optimal monthly sale schedule.
        
        Strategy:
        - Sell more in months with market downturns (harvest losses elsewhere)
        - Stay within tax brackets
        - Minimize tax drag
        """
        monthly_sales = []
        remaining_value = total_value
        remaining_quantity = quantity
        
        # Calculate base monthly sale amount
        base_monthly_sale = total_value / time_horizon_months
        
        for month in range(1, time_horizon_months + 1):
            # Calculate sale amount for this month
            sale_amount = base_monthly_sale
            
            # Adjust based on tax optimization
            if unrealized_gain > 0:
                # Try to stay within lower tax brackets
                sale_amount = self._optimize_for_tax_bracket(
                    sale_amount, annual_income, tax_bracket, month
                )
            
            # Don't sell more than remaining
            sale_amount = min(sale_amount, remaining_value)
            
            # Calculate shares to sell
            shares_to_sell = (sale_amount / (total_value / quantity)) if total_value > 0 else 0
            shares_to_sell = min(shares_to_sell, remaining_quantity)
            
            # Calculate gain on this sale
            gain_on_sale = gain_per_share * shares_to_sell
            
            # Calculate tax on this sale
            tax_on_sale = self._calculate_tax_on_sale(
                sale_amount, gain_on_sale, annual_income, tax_bracket
            )
            
            monthly_sales.append({
                "month": month,
                "sale_amount": float(sale_amount),
                "shares_to_sell": float(shares_to_sell),
                "gain_on_sale": float(gain_on_sale),
                "estimated_tax": float(tax_on_sale),
                "after_tax_proceeds": float(sale_amount - tax_on_sale)
            })
            
            remaining_value -= sale_amount
            remaining_quantity -= shares_to_sell
        
        return monthly_sales
    
    def _optimize_for_tax_bracket(
        self,
        sale_amount: float,
        annual_income: float,
        tax_bracket: str,
        month: int
    ) -> float:
        """
        Optimize sale amount to minimize tax bracket impact.
        
        Strategy: Sell more in months where we can offset with losses.
        """
        # Tax brackets (2024 rates, simplified)
        brackets = {
            "low": {"rate": 0.0, "threshold": 44725},  # 0% LTCG
            "medium": {"rate": 0.15, "threshold": 492300},  # 15% LTCG
            "high": {"rate": 0.20, "threshold": float('inf')}  # 20% LTCG
        }
        
        bracket_info = brackets.get(tax_bracket, brackets["high"])
        
        # Try to keep within lower bracket
        # This is simplified - full implementation would consider:
        # - Current year's realized gains
        # - Losses available to harvest
        # - Remaining months in transition
        
        return sale_amount
    
    def _calculate_tax_on_sale(
        self,
        sale_amount: float,
        gain: float,
        annual_income: float,
        tax_bracket: str
    ) -> float:
        """Calculate tax on sale"""
        # Simplified tax calculation
        # Full implementation would use actual tax tables
        
        if gain <= 0:
            return 0.0
        
        # Long-term capital gains rates (simplified)
        if tax_bracket == "low":
            rate = 0.0
        elif tax_bracket == "medium":
            rate = 0.15
        else:  # high
            rate = 0.20
        
        # Add 3.8% NIIT for high earners
        if annual_income > 200000:
            rate += 0.038
        
        return gain * rate
    
    def _calculate_transition_tax_benefits(
        self,
        monthly_sales: List[Dict],
        cost_basis: float,
        current_price: float,
        annual_income: float,
        tax_bracket: str,
        realized_gains: float
    ) -> Dict[str, Any]:
        """Calculate total tax benefits from transition"""
        total_tax = 0.0
        total_gains = 0.0
        
        for sale in monthly_sales:
            total_tax += sale.get("estimated_tax", 0)
            total_gains += sale.get("gain_on_sale", 0)
        
        # Compare to selling all at once
        total_value = sum(s["sale_amount"] for s in monthly_sales)
        total_gain_if_sold_all = (current_price - cost_basis) * (total_value / current_price)
        tax_if_sold_all = self._calculate_tax_on_sale(
            total_value, total_gain_if_sold_all, annual_income, tax_bracket
        )
        
        # Tax savings from gradual sale
        tax_savings = tax_if_sold_all - total_tax
        
        return {
            "total_capital_gains_tax": float(total_tax),
            "tax_if_sold_all_at_once": float(tax_if_sold_all),
            "total_savings": float(tax_savings),
            "savings_percentage": float((tax_savings / tax_if_sold_all * 100) if tax_if_sold_all > 0 else 0)
        }
    
    def _create_reinvestment_plan(
        self,
        monthly_sales: List[Dict],
        target_allocation: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Create reinvestment plan based on target allocation.
        
        This would integrate with your portfolio optimization algorithms.
        """
        total_proceeds = sum(s["after_tax_proceeds"] for s in monthly_sales)
        
        # Calculate allocation amounts
        reinvestment = {}
        for symbol, weight in target_allocation.items():
            reinvestment[symbol] = {
                "weight": float(weight),
                "allocation_amount": float(total_proceeds * weight)
            }
        
        return {
            "total_proceeds": float(total_proceeds),
            "allocations": reinvestment,
            "strategy": "Gradual reinvestment according to target allocation"
        }


# Singleton instance
_tspt_service = TaxSmartPortfolioTransitions()


def get_tspt_service() -> TaxSmartPortfolioTransitions:
    """Get singleton TSPT service instance"""
    return _tspt_service

