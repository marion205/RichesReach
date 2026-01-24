# core/direct_indexing.py
"""
Direct Indexing Service
Allows users to customize portfolios by owning individual stocks instead of ETFs,
enabling tax-loss harvesting at the individual stock level.

This integrates seamlessly with RichesReach's existing portfolio management and AI orchestrator.
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .quantitative_algorithms import ModernPortfolioTheory, TaxLossHarvesting
from .etf_holdings_provider import get_etf_holdings_provider

logger = logging.getLogger(__name__)


class DirectIndexingService:
    """
    Direct Indexing for Tax-Efficient Customization
    
    Replaces ETF holdings with individual stocks to enable:
    - Tax-loss harvesting at stock level
    - Customization (exclude specific stocks)
    - Tax-efficient rebalancing
    
    Integrates with:
    - ModernPortfolioTheory for optimization
    - TaxLossHarvesting for tax benefits
    - PortfolioService for portfolio management
    """
    
    def __init__(self):
        """Initialize Direct Indexing Service"""
        self.mpt = ModernPortfolioTheory()
        self.tlh = TaxLossHarvesting()
        self.etf_provider = get_etf_holdings_provider()
    
    def create_direct_index(
        self,
        target_etf: str,  # e.g., "SPY" for S&P 500
        portfolio_value: float,
        excluded_stocks: Optional[List[str]] = None,
        tax_optimization: bool = True,
        min_stock_weight: float = 0.001,  # Minimum 0.1% per stock
        max_stocks: int = 100  # Maximum number of stocks
    ) -> Dict[str, Any]:
        """
        Create a direct index portfolio that tracks an ETF.
        
        Args:
            target_etf: ETF to replicate (e.g., "SPY", "QQQ")
            portfolio_value: Total portfolio value
            excluded_stocks: Stocks to exclude (e.g., user's employer stock)
            tax_optimization: Enable tax-loss harvesting optimization
            min_stock_weight: Minimum weight per stock
            max_stocks: Maximum number of stocks to include
            
        Returns:
            Dictionary with stock allocations and tax benefits
        """
        try:
            # Get ETF holdings from real-time provider
            etf_holdings = self.etf_provider.get_etf_holdings(target_etf)
            
            if not etf_holdings:
                return {
                    "error": f"Could not retrieve holdings for {target_etf}",
                    "method": "direct_indexing"
                }
            
            # Filter out excluded stocks
            if excluded_stocks:
                etf_holdings = [
                    h for h in etf_holdings 
                    if h.get('symbol', '').upper() not in [s.upper() for s in excluded_stocks]
                ]
            
            # Limit to max_stocks (top holdings by weight)
            etf_holdings = sorted(etf_holdings, key=lambda x: x.get('weight', 0), reverse=True)[:max_stocks]
            
            # Calculate allocations
            if tax_optimization:
                allocations = self._optimize_for_tax_loss_harvesting(
                    etf_holdings, portfolio_value
                )
            else:
                allocations = self._replicate_etf_weights(etf_holdings, portfolio_value)
            
            # Calculate expected tax benefits
            tax_benefits = self._calculate_tax_benefits(allocations, portfolio_value)
            
            # Estimate tracking error
            tracking_error = self._estimate_tracking_error(allocations, target_etf)
            
            return {
                "allocations": allocations,
                "target_etf": target_etf,
                "total_stocks": len(allocations),
                "tracking_error": tracking_error,
                "expected_tax_benefits": tax_benefits,
                "portfolio_value": portfolio_value,
                "excluded_stocks": excluded_stocks or [],
                "method": "direct_indexing"
            }
        
        except Exception as e:
            logger.error(f"Error creating direct index: {e}")
            return {
                "error": str(e),
                "method": "direct_indexing"
            }
    
    
    def _replicate_etf_weights(
        self,
        etf_holdings: List[Dict[str, Any]],
        portfolio_value: float
    ) -> List[Dict[str, Any]]:
        """Replicate ETF weights directly"""
        allocations = []
        total_weight = sum(h.get('weight', 0) for h in etf_holdings)
        
        # Normalize weights if they don't sum to 1
        if total_weight > 0:
            for holding in etf_holdings:
                weight = holding.get('weight', 0) / total_weight
                allocation_value = portfolio_value * weight
                
                allocations.append({
                    "symbol": holding.get('symbol', ''),
                    "weight": float(weight),
                    "allocation_value": float(allocation_value),
                    "shares": None  # Would calculate based on current price
                })
        
        return allocations
    
    def _optimize_for_tax_loss_harvesting(
        self,
        holdings: List[Dict],
        portfolio_value: float
    ) -> List[Dict]:
        """
        Optimize allocations to maximize tax-loss harvesting opportunities.
        
        Prioritizes stocks with:
        1. High volatility (more TLH opportunities)
        2. Low correlation (better diversification)
        3. Current losses (immediate TLH)
        """
        # For now, use simple replication
        # Full implementation would:
        # 1. Get current prices and calculate unrealized gains/losses
        # 2. Prioritize stocks with losses for immediate TLH
        # 3. Use MPT to optimize for diversification
        
        allocations = self._replicate_etf_weights(holdings, portfolio_value)
        
        # Sort by potential TLH benefit (would use actual price data)
        # For now, just return allocations
        return allocations
    
    def _calculate_tax_benefits(
        self,
        allocations: List[Dict[str, Any]],
        portfolio_value: float
    ) -> Dict[str, Any]:
        """
        Calculate expected tax benefits from direct indexing.
        
        Benefits include:
        - Tax-loss harvesting at stock level (vs ETF level)
        - Customization (exclude employer stock)
        - More granular control
        """
        # Estimate annual tax savings
        # Assumptions:
        # - Average 2% of portfolio in losses per year
        # - 15% long-term capital gains rate
        # - Direct indexing enables 3x more TLH opportunities than ETF
        
        estimated_annual_losses = portfolio_value * 0.02  # 2% in losses
        tax_rate = 0.15  # Long-term capital gains
        tlh_multiplier = 3.0  # Direct indexing enables more TLH
        
        estimated_annual_savings = estimated_annual_losses * tax_rate * tlh_multiplier
        
        return {
            "estimated_annual_tax_savings": float(estimated_annual_savings),
            "estimated_annual_savings_pct": float(estimated_annual_savings / portfolio_value * 100),
            "method": "direct_indexing_tax_benefits"
        }
    
    def _estimate_tracking_error(
        self,
        allocations: List[Dict[str, Any]],
        target_etf: str
    ) -> Dict[str, Any]:
        """
        Estimate tracking error vs target ETF.
        
        Tracking error comes from:
        - Limited number of stocks (vs full ETF)
        - Excluded stocks
        - Rebalancing frequency
        """
        # Simplified tracking error estimate
        num_stocks = len(allocations)
        
        # More stocks = lower tracking error
        if num_stocks >= 50:
            tracking_error_pct = 0.5  # 0.5% annual tracking error
        elif num_stocks >= 20:
            tracking_error_pct = 1.0  # 1.0% annual tracking error
        else:
            tracking_error_pct = 2.0  # 2.0% annual tracking error
        
        return {
            "estimated_annual_tracking_error_pct": tracking_error_pct,
            "num_stocks": num_stocks,
            "note": "Tracking error estimated based on number of stocks"
        }


# Singleton instance
_direct_indexing_service = DirectIndexingService()


def get_direct_indexing_service() -> DirectIndexingService:
    """Get singleton direct indexing service instance"""
    return _direct_indexing_service

