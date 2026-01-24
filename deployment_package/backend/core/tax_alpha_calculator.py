# core/tax_alpha_calculator.py
"""
Tax Alpha Calculator
Calculates the real-time tax benefits of Direct Indexing vs. standard ETF holdings.

This makes the "invisible" tax savings visible to users through the Tax Alpha Dashboard.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class TaxAlphaMetrics:
    """Tax alpha metrics for dashboard visualization"""
    total_tax_liabilities_offset: float  # Total $ saved in taxes
    annual_tax_alpha_pct: float  # Annual tax alpha as % of portfolio
    harvested_losses_ytd: float  # Losses harvested year-to-date
    potential_harvestable_losses: float  # Current unrealized losses available
    tracking_error_pct: float  # Tracking error vs benchmark
    net_alpha: float  # Tax alpha minus tracking error
    comparison_etf_value: float  # Hypothetical value if held in ETF
    direct_index_value: float  # Actual direct index value
    divergence: float  # Difference between ETF and Direct Index


class TaxAlphaCalculator:
    """
    Calculates tax alpha from Direct Indexing.
    
    Key Metrics:
    - Tax Liabilities Offset: Real-time $ amount saved
    - Annual Tax Alpha: % return boost from tax savings
    - Tracking Error: Cost of replication
    - Net Alpha: Tax alpha minus tracking error
    """
    
    def __init__(self):
        """Initialize Tax Alpha Calculator"""
        pass
    
    def calculate_tax_alpha(
        self,
        direct_index_positions: List[Dict[str, Any]],
        benchmark_etf: str,
        portfolio_value: float,
        tax_rate_long_term: float = 0.15,
        tax_rate_short_term: float = 0.37
    ) -> TaxAlphaMetrics:
        """
        Calculate tax alpha metrics for dashboard.
        
        Args:
            direct_index_positions: List of positions in direct index
                - symbol: Stock symbol
                - quantity: Number of shares
                - cost_basis: Purchase price
                - current_price: Current market price
                - purchase_date: Date purchased
            benchmark_etf: ETF being replicated (e.g., "SPY")
            portfolio_value: Current total portfolio value
            tax_rate_long_term: Long-term capital gains rate
            tax_rate_short_term: Short-term capital gains rate
            
        Returns:
            TaxAlphaMetrics with all calculated values
        """
        try:
            # Calculate harvested losses (already realized)
            harvested_losses_ytd = self._calculate_harvested_losses_ytd(
                direct_index_positions, tax_rate_long_term, tax_rate_short_term
            )
            
            # Calculate potential harvestable losses (unrealized)
            potential_losses = self._calculate_potential_harvestable_losses(
                direct_index_positions, tax_rate_long_term, tax_rate_short_term
            )
            
            # Total tax liabilities offset
            total_tax_offset = harvested_losses_ytd + potential_losses
            
            # Calculate annual tax alpha as % of portfolio
            annual_tax_alpha_pct = (total_tax_offset / portfolio_value * 100) if portfolio_value > 0 else 0
            
            # Estimate tracking error (would use actual market data)
            tracking_error_pct = self._estimate_tracking_error(
                direct_index_positions, benchmark_etf
            )
            
            # Net alpha = tax alpha - tracking error
            net_alpha = annual_tax_alpha_pct - tracking_error_pct
            
            # Calculate hypothetical ETF value vs actual direct index value
            comparison_etf_value, direct_index_value, divergence = self._calculate_value_comparison(
                direct_index_positions, portfolio_value, benchmark_etf
            )
            
            return TaxAlphaMetrics(
                total_tax_liabilities_offset=float(total_tax_offset),
                annual_tax_alpha_pct=float(annual_tax_alpha_pct),
                harvested_losses_ytd=float(harvested_losses_ytd),
                potential_harvestable_losses=float(potential_losses),
                tracking_error_pct=float(tracking_error_pct),
                net_alpha=float(net_alpha),
                comparison_etf_value=float(comparison_etf_value),
                direct_index_value=float(direct_index_value),
                divergence=float(divergence)
            )
        
        except Exception as e:
            logger.error(f"Error calculating tax alpha: {e}")
            # Return zero metrics on error
            return TaxAlphaMetrics(
                total_tax_liabilities_offset=0.0,
                annual_tax_alpha_pct=0.0,
                harvested_losses_ytd=0.0,
                potential_harvestable_losses=0.0,
                tracking_error_pct=0.0,
                net_alpha=0.0,
                comparison_etf_value=portfolio_value,
                direct_index_value=portfolio_value,
                divergence=0.0
            )
    
    def _calculate_harvested_losses_ytd(
        self,
        positions: List[Dict[str, Any]],
        tax_rate_long_term: float,
        tax_rate_short_term: float
    ) -> float:
        """
        Calculate losses already harvested this year.
        
        This would integrate with your transaction history to find
        realized losses from tax-loss harvesting.
        """
        # Placeholder: Would query transaction history
        # For now, estimate based on positions with losses
        
        harvested_tax_savings = 0.0
        current_date = datetime.now()
        
        for position in positions:
            # Check if position was sold (realized loss)
            if position.get("realized_loss"):
                loss = position["realized_loss"]
                is_long_term = position.get("is_long_term", False)
                tax_rate = tax_rate_long_term if is_long_term else tax_rate_short_term
                harvested_tax_savings += loss * tax_rate
        
        return harvested_tax_savings
    
    def _calculate_potential_harvestable_losses(
        self,
        positions: List[Dict[str, Any]],
        tax_rate_long_term: float,
        tax_rate_short_term: float
    ) -> float:
        """Calculate potential tax savings from current unrealized losses"""
        potential_savings = 0.0
        current_date = datetime.now()
        
        for position in positions:
            cost_basis = position.get("cost_basis", 0)
            current_price = position.get("current_price", 0)
            quantity = position.get("quantity", 0)
            purchase_date = position.get("purchase_date")
            
            if cost_basis <= 0 or current_price <= 0 or quantity <= 0:
                continue
            
            # Calculate unrealized loss
            unrealized_loss = (cost_basis - current_price) * quantity
            
            if unrealized_loss > 0:  # Only losses
                # Determine if long-term or short-term
                is_long_term = False
                if purchase_date:
                    if isinstance(purchase_date, str):
                        purchase_date = datetime.fromisoformat(purchase_date.replace('Z', '+00:00'))
                    days_held = (current_date - purchase_date.replace(tzinfo=None)).days
                    is_long_term = days_held >= 365
                
                tax_rate = tax_rate_long_term if is_long_term else tax_rate_short_term
                potential_savings += unrealized_loss * tax_rate
        
        return potential_savings
    
    def _estimate_tracking_error(
        self,
        positions: List[Dict[str, Any]],
        benchmark_etf: str
    ) -> float:
        """
        Estimate tracking error vs benchmark ETF.
        
        Tracking error comes from:
        - Limited number of stocks (vs full index)
        - Rebalancing frequency
        - Dividend capture differences
        - Transaction costs
        """
        num_stocks = len(positions)
        
        # More stocks = lower tracking error
        if num_stocks >= 100:
            base_error = 0.3  # 0.3% annual tracking error
        elif num_stocks >= 50:
            base_error = 0.5  # 0.5% annual tracking error
        elif num_stocks >= 20:
            base_error = 1.0  # 1.0% annual tracking error
        else:
            base_error = 2.0  # 2.0% annual tracking error
        
        # Add rebalancing cost estimate (0.1% per rebalance, assume 2x/year)
        rebalancing_cost = 0.2
        
        # Add dividend capture difference (estimated)
        dividend_drag = 0.1
        
        total_tracking_error = base_error + rebalancing_cost + dividend_drag
        
        return total_tracking_error
    
    def _calculate_value_comparison(
        self,
        positions: List[Dict[str, Any]],
        portfolio_value: float,
        benchmark_etf: str
    ) -> tuple[float, float, float]:
        """
        Calculate hypothetical ETF value vs actual direct index value.
        
        Returns:
            (comparison_etf_value, direct_index_value, divergence)
        """
        # Actual direct index value
        direct_index_value = portfolio_value
        
        # Hypothetical ETF value (would use actual ETF performance)
        # For now, estimate based on tracking error
        tracking_error_pct = self._estimate_tracking_error(positions, benchmark_etf)
        
        # If tracking error is positive, ETF would be worth more
        # If tracking error is negative (unlikely), direct index outperforms
        comparison_etf_value = portfolio_value * (1 + tracking_error_pct / 100)
        
        # Divergence = difference between ETF and Direct Index
        divergence = direct_index_value - comparison_etf_value
        
        return comparison_etf_value, direct_index_value, divergence
    
    def get_dashboard_data(
        self,
        direct_index_positions: List[Dict[str, Any]],
        benchmark_etf: str,
        portfolio_value: float
    ) -> Dict[str, Any]:
        """
        Get formatted data for Tax Alpha Dashboard.
        
        Returns data structure ready for frontend visualization.
        """
        metrics = self.calculate_tax_alpha(
            direct_index_positions=direct_index_positions,
            benchmark_etf=benchmark_etf,
            portfolio_value=portfolio_value
        )
        
        return {
            "tax_alpha": {
                "total_tax_savings": metrics.total_tax_liabilities_offset,
                "annual_tax_alpha_pct": metrics.annual_tax_alpha_pct,
                "harvested_losses_ytd": metrics.harvested_losses_ytd,
                "potential_harvestable_losses": metrics.potential_harvestable_losses,
                "net_alpha": metrics.net_alpha
            },
            "performance": {
                "comparison_etf_value": metrics.comparison_etf_value,
                "direct_index_value": metrics.direct_index_value,
                "divergence": metrics.divergence,
                "tracking_error_pct": metrics.tracking_error_pct
            },
            "visualization": {
                "chart_data": self._generate_chart_data(metrics),
                "summary": self._generate_summary(metrics)
            }
        }
    
    def _generate_chart_data(self, metrics: TaxAlphaMetrics) -> Dict[str, Any]:
        """Generate chart data for visualization"""
        return {
            "etf_value": metrics.comparison_etf_value,
            "direct_index_value": metrics.direct_index_value,
            "tax_alpha_contribution": metrics.total_tax_liabilities_offset,
            "tracking_error_cost": metrics.tracking_error_pct * metrics.direct_index_value / 100
        }
    
    def _generate_summary(self, metrics: TaxAlphaMetrics) -> str:
        """Generate human-readable summary"""
        if metrics.net_alpha > 0:
            return (
                f"Your Direct Index portfolio is generating {metrics.annual_tax_alpha_pct:.2f}% "
                f"annual tax alpha, offsetting {metrics.tracking_error_pct:.2f}% tracking error "
                f"for a net benefit of {metrics.net_alpha:.2f}%. "
                f"This translates to ${metrics.total_tax_liabilities_offset:,.2f} in tax savings."
            )
        else:
            return (
                f"Your Direct Index portfolio has {metrics.tracking_error_pct:.2f}% tracking error. "
                f"Tax alpha of {metrics.annual_tax_alpha_pct:.2f}% partially offsets this."
            )


# Singleton instance
_tax_alpha_calculator = TaxAlphaCalculator()


def get_tax_alpha_calculator() -> TaxAlphaCalculator:
    """Get singleton tax alpha calculator instance"""
    return _tax_alpha_calculator

