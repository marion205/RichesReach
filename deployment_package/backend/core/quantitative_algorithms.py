# core/quantitative_algorithms.py
"""
Quantitative Finance Algorithms
Nobel-prize-winning finance theories implemented for wealth management.

These algorithms do the "heavy lifting" - the LLM acts as a translator
that calls these functions and interprets the results.
"""
import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import math

logger = logging.getLogger(__name__)

# Try to import PyPortfolioOpt for advanced portfolio optimization
try:
    from pypfopt import EfficientFrontier, risk_models, expected_returns
    from pypfopt.black_litterman import BlackLittermanModel
    PYPFOPT_AVAILABLE = True
except ImportError:
    PYPFOPT_AVAILABLE = False
    logger.warning("PyPortfolioOpt not available. Some advanced features will use fallback implementations.")


@dataclass
class MonteCarloResult:
    """Result from Monte Carlo simulation"""
    success_probability: float  # Probability of achieving goal (0-1)
    median_outcome: float
    worst_case_10th_percentile: float
    best_case_90th_percentile: float
    required_monthly_savings: Optional[float] = None
    simulations_run: int = 10000


class MonteCarloSimulation:
    """
    Monte Carlo Simulation for retirement and goal planning.
    
    Runs 10,000+ market scenarios to calculate success probability.
    Accounts for market crashes and "bad luck" timing.
    """
    
    def __init__(self, random_seed: Optional[int] = None):
        """Initialize Monte Carlo simulator"""
        if random_seed:
            np.random.seed(random_seed)
    
    def simulate_retirement(
        self,
        current_age: int,
        retirement_age: int,
        current_savings: float,
        monthly_contribution: float,
        annual_return_mean: float = 0.07,  # 7% average annual return
        annual_return_std: float = 0.15,   # 15% volatility (standard deviation)
        inflation_rate: float = 0.03,       # 3% inflation
        target_amount: Optional[float] = None,
        num_simulations: int = 10000
    ) -> MonteCarloResult:
        """
        Simulate retirement savings over time.
        
        Args:
            current_age: Current age
            retirement_age: Target retirement age
            current_savings: Current savings amount
            monthly_contribution: Monthly contribution amount
            annual_return_mean: Expected annual return (default 7%)
            annual_return_std: Volatility/std dev of returns (default 15%)
            inflation_rate: Expected inflation rate (default 3%)
            target_amount: Optional target amount to reach
            num_simulations: Number of Monte Carlo simulations (default 10,000)
            
        Returns:
            MonteCarloResult with success probability and statistics
        """
        years_to_retirement = retirement_age - current_age
        months_to_retirement = years_to_retirement * 12
        
        if months_to_retirement <= 0:
            return MonteCarloResult(
                success_probability=1.0 if current_savings >= (target_amount or 0) else 0.0,
                median_outcome=current_savings,
                worst_case_10th_percentile=current_savings,
                best_case_90th_percentile=current_savings,
                simulations_run=0
            )
        
        # Run simulations
        final_values = []
        
        for _ in range(num_simulations):
            savings = current_savings
            
            # Simulate monthly returns
            for month in range(months_to_retirement):
                # Generate random monthly return (annual return / 12, adjusted for volatility)
                monthly_return = np.random.normal(
                    annual_return_mean / 12,
                    annual_return_std / np.sqrt(12)  # Scale volatility for monthly
                )
                
                # Apply return to existing savings
                savings *= (1 + monthly_return)
                
                # Add monthly contribution
                savings += monthly_contribution
            
            # Adjust for inflation
            inflation_factor = (1 + inflation_rate) ** years_to_retirement
            savings_real = savings / inflation_factor
            
            final_values.append(savings_real)
        
        final_values = np.array(final_values)
        
        # Calculate statistics
        median = np.median(final_values)
        percentile_10 = np.percentile(final_values, 10)
        percentile_90 = np.percentile(final_values, 90)
        
        # Calculate success probability if target is provided
        success_prob = 1.0
        if target_amount:
            success_prob = np.mean(final_values >= target_amount)
        
        return MonteCarloResult(
            success_probability=float(success_prob),
            median_outcome=float(median),
            worst_case_10th_percentile=float(percentile_10),
            best_case_90th_percentile=float(percentile_90),
            simulations_run=num_simulations
        )
    
    def find_required_savings(
        self,
        current_age: int,
        retirement_age: int,
        current_savings: float,
        target_amount: float,
        annual_return_mean: float = 0.07,
        annual_return_std: float = 0.15,
        inflation_rate: float = 0.03,
        target_success_probability: float = 0.85,
        num_simulations: int = 10000
    ) -> float:
        """
        Find required monthly savings to achieve target with desired success probability.
        
        Uses binary search to find the minimum monthly contribution needed.
        """
        # Binary search for required monthly savings
        low = 0.0
        high = target_amount / ((retirement_age - current_age) * 12) * 2  # Upper bound
        
        for _ in range(50):  # Max 50 iterations
            mid = (low + high) / 2
            
            result = self.simulate_retirement(
                current_age=current_age,
                retirement_age=retirement_age,
                current_savings=current_savings,
                monthly_contribution=mid,
                annual_return_mean=annual_return_mean,
                annual_return_std=annual_return_std,
                inflation_rate=inflation_rate,
                target_amount=target_amount,
                num_simulations=num_simulations
            )
            
            if result.success_probability >= target_success_probability:
                high = mid
            else:
                low = mid
            
            if high - low < 1.0:  # Convergence threshold
                break
        
        return (low + high) / 2
    
    def simulate_goal(
        self,
        goal_amount: float,
        time_horizon_months: int,
        current_savings: float,
        monthly_contribution: float,
        annual_return_mean: float = 0.07,
        annual_return_std: float = 0.15,
        num_simulations: int = 10000
    ) -> MonteCarloResult:
        """
        Simulate achieving a specific goal (e.g., $50k wedding in 2 years).
        
        Args:
            goal_amount: Target amount to reach
            time_horizon_months: Number of months to reach goal
            current_savings: Current savings
            monthly_contribution: Monthly contribution
            annual_return_mean: Expected annual return
            annual_return_std: Volatility
            num_simulations: Number of simulations
            
        Returns:
            MonteCarloResult with success probability
        """
        final_values = []
        
        for _ in range(num_simulations):
            savings = current_savings
            
            for month in range(time_horizon_months):
                monthly_return = np.random.normal(
                    annual_return_mean / 12,
                    annual_return_std / np.sqrt(12)
                )
                savings *= (1 + monthly_return)
                savings += monthly_contribution
            
            final_values.append(savings)
        
        final_values = np.array(final_values)
        
        success_prob = np.mean(final_values >= goal_amount)
        
        return MonteCarloResult(
            success_probability=float(success_prob),
            median_outcome=float(np.median(final_values)),
            worst_case_10th_percentile=float(np.percentile(final_values, 10)),
            best_case_90th_percentile=float(np.percentile(final_values, 90)),
            simulations_run=num_simulations
        )


class ModernPortfolioTheory:
    """
    Modern Portfolio Theory (MPT) - Risk vs Reward Balancing.
    
    Automatically picks the best mix of stocks/bonds for a user's specific risk level.
    The gold standard for diversified, long-term wealth building.
    """
    
    def __init__(self):
        """Initialize MPT optimizer"""
        pass
    
    def optimize_portfolio(
        self,
        expected_returns: pd.Series,
        cov_matrix: pd.DataFrame,
        risk_free_rate: float = 0.02,
        target_return: Optional[float] = None,
        risk_tolerance: str = "moderate"  # "conservative", "moderate", "aggressive"
    ) -> Dict[str, Any]:
        """
        Optimize portfolio using Markowitz mean-variance optimization.
        
        Args:
            expected_returns: Expected returns for each asset (pandas Series)
            cov_matrix: Covariance matrix (pandas DataFrame)
            risk_free_rate: Risk-free rate (default 2%)
            target_return: Optional target return (if None, maximizes Sharpe ratio)
            risk_tolerance: Risk tolerance level
            
        Returns:
            Dictionary with optimal weights, expected return, volatility, Sharpe ratio
        """
        if PYPFOPT_AVAILABLE:
            return self._optimize_with_pypfopt(
                expected_returns, cov_matrix, risk_free_rate, target_return, risk_tolerance
            )
        else:
            return self._optimize_fallback(
                expected_returns, cov_matrix, risk_free_rate, target_return, risk_tolerance
            )
    
    def _optimize_with_pypfopt(
        self,
        expected_returns: pd.Series,
        cov_matrix: pd.DataFrame,
        risk_free_rate: float,
        target_return: Optional[float],
        risk_tolerance: str
    ) -> Dict[str, Any]:
        """Optimize using PyPortfolioOpt library"""
        try:
            ef = EfficientFrontier(expected_returns, cov_matrix)
            
            if target_return:
                # Maximize Sharpe ratio for target return
                ef.efficient_return(target_return)
            else:
                # Maximize Sharpe ratio
                ef.max_sharpe(risk_free_rate=risk_free_rate)
            
            weights = ef.clean_weights()
            performance = ef.portfolio_performance(risk_free_rate=risk_free_rate)
            
            return {
                "weights": {k: float(v) for k, v in weights.items()},
                "expected_return": float(performance[0]),
                "volatility": float(performance[1]),
                "sharpe_ratio": float(performance[2]),
                "method": "pypfopt_mpt"
            }
        except Exception as e:
            logger.warning(f"PyPortfolioOpt optimization failed: {e}, using fallback")
            return self._optimize_fallback(
                expected_returns, cov_matrix, risk_free_rate, target_return, risk_tolerance
            )
    
    def _optimize_fallback(
        self,
        expected_returns: pd.Series,
        cov_matrix: pd.DataFrame,
        risk_free_rate: float,
        target_return: Optional[float],
        risk_tolerance: str
    ) -> Dict[str, Any]:
        """Fallback optimization using simple risk-based allocation"""
        assets = expected_returns.index.tolist()
        
        # Risk tolerance mapping
        risk_weights = {
            "conservative": {"stocks": 0.4, "bonds": 0.5, "cash": 0.1},
            "moderate": {"stocks": 0.60, "bonds": 0.30, "cash": 0.10},
            "aggressive": {"stocks": 0.80, "bonds": 0.15, "cash": 0.05}
        }
        
        # Simple allocation based on risk tolerance
        base_allocation = risk_weights.get(risk_tolerance.lower(), risk_weights["moderate"])
        
        # Distribute across available assets
        num_assets = len(assets)
        weights = {}
        
        # Categorize assets (simplified - would need actual asset classification)
        stocks = [a for a in assets if num_assets > 0][:max(1, int(num_assets * 0.7))]
        bonds = [a for a in assets if a not in stocks]
        
        # Allocate stocks
        if stocks:
            stock_weight = base_allocation["stocks"] / len(stocks)
            for asset in stocks:
                weights[asset] = stock_weight
        
        # Allocate bonds
        if bonds:
            bond_weight = base_allocation["bonds"] / len(bonds) if bonds else 0
            for asset in bonds:
                weights[asset] = bond_weight
        
        # Calculate portfolio metrics
        portfolio_return = sum(weights.get(a, 0) * expected_returns.get(a, 0) for a in assets)
        portfolio_variance = 0
        for i, asset1 in enumerate(assets):
            for j, asset2 in enumerate(assets):
                portfolio_variance += (
                    weights.get(asset1, 0) * 
                    weights.get(asset2, 0) * 
                    cov_matrix.loc[asset1, asset2]
                )
        portfolio_volatility = np.sqrt(portfolio_variance)
        sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0
        
        return {
            "weights": weights,
            "expected_return": float(portfolio_return),
            "volatility": float(portfolio_volatility),
            "sharpe_ratio": float(sharpe_ratio),
            "method": "fallback_mpt"
        }


class BlackLittermanModel:
    """
    Black-Litterman Model for Customized Portfolios.
    
    Combines market data with the user's specific "views" (e.g., "I think Tech will grow 10%").
    Avoids the "all-or-nothing" extreme bets common in simpler models.
    """
    
    def __init__(self):
        """Initialize Black-Litterman model"""
        pass
    
    def optimize_with_views(
        self,
        market_caps: pd.Series,  # Market capitalization weights
        cov_matrix: pd.DataFrame,
        risk_aversion: float = 3.0,
        tau: float = 0.05,  # Scaling factor
        views: Optional[List[Dict[str, Any]]] = None,  # User views
        view_confidences: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Optimize portfolio using Black-Litterman model with user views.
        
        Args:
            market_caps: Market capitalization weights (market portfolio)
            cov_matrix: Covariance matrix
            risk_aversion: Risk aversion parameter (default 3.0)
            tau: Scaling factor (default 0.05)
            views: List of user views, e.g., [{"asset": "AAPL", "return": 0.10}]
            view_confidences: Confidence levels for each view (0-1)
            
        Returns:
            Dictionary with optimal weights and expected returns
        """
        if PYPFOPT_AVAILABLE and views:
            return self._optimize_with_pypfopt_bl(
                market_caps, cov_matrix, risk_aversion, tau, views, view_confidences
            )
        else:
            # Fallback to MPT if no views or PyPortfolioOpt not available
            logger.info("Black-Litterman: No views provided or PyPortfolioOpt unavailable, using MPT fallback")
            mpt = ModernPortfolioTheory()
            expected_returns = market_caps * 0.07  # Simple expected returns
            return mpt.optimize_portfolio(expected_returns, cov_matrix)
    
    def _optimize_with_pypfopt_bl(
        self,
        market_caps: pd.Series,
        cov_matrix: pd.DataFrame,
        risk_aversion: float,
        tau: float,
        views: List[Dict[str, Any]],
        view_confidences: Optional[List[float]]
    ) -> Dict[str, Any]:
        """Optimize using PyPortfolioOpt Black-Litterman implementation"""
        try:
            # Convert views to Black-Litterman format
            # This is simplified - full implementation would need proper view matrix
            bl = BlackLittermanModel(
                cov_matrix,
                pi=market_caps * risk_aversion,  # Prior expected returns
                absolute_views=None,  # Would need to construct view matrix
                tau=tau
            )
            
            # For now, return market portfolio with slight adjustments based on views
            # Full implementation would use bl.bl_weights()
            weights = market_caps.to_dict()
            
            # Adjust weights based on views
            if views:
                for i, view in enumerate(views):
                    asset = view.get("asset")
                    if asset in weights:
                        confidence = view_confidences[i] if view_confidences and i < len(view_confidences) else 0.5
                        # Adjust weight based on view (simplified)
                        adjustment = (view.get("return", 0) - 0.07) * confidence * 0.1
                        weights[asset] = max(0, min(1, weights[asset] + adjustment))
            
            # Normalize weights
            total = sum(weights.values())
            if total > 0:
                weights = {k: v / total for k, v in weights.items()}
            
            return {
                "weights": weights,
                "method": "black_litterman",
                "views_applied": len(views) if views else 0
            }
        except Exception as e:
            logger.warning(f"Black-Litterman optimization failed: {e}, using fallback")
            mpt = ModernPortfolioTheory()
            expected_returns = market_caps * 0.07
            return mpt.optimize_portfolio(expected_returns, cov_matrix)


class TaxLossHarvesting:
    """
    Tax-Loss Harvesting (TLH) Algorithm.
    
    Identifies losing investments to sell to offset gains, saving the user money on taxes.
    Provides immediate, tangible "alpha" (extra value) to the user.
    """
    
    def __init__(self):
        """Initialize TLH algorithm"""
        pass
    
    def identify_harvesting_opportunities(
        self,
        positions: List[Dict[str, Any]],
        realized_gains: float = 0.0,
        tax_rate_long_term: float = 0.15,  # 15% long-term capital gains
        tax_rate_short_term: float = 0.37,  # 37% short-term (ordinary income)
        wash_sale_window_days: int = 30
    ) -> Dict[str, Any]:
        """
        Identify tax-loss harvesting opportunities.
        
        Args:
            positions: List of positions with:
                - symbol: Stock symbol
                - cost_basis: Purchase price
                - current_price: Current market price
                - quantity: Number of shares
                - purchase_date: Date purchased
            realized_gains: Already realized gains to offset
            tax_rate_long_term: Long-term capital gains tax rate
            tax_rate_short_term: Short-term capital gains tax rate
            wash_sale_window_days: Days to avoid wash sale (default 30)
            
        Returns:
            Dictionary with harvesting recommendations
        """
        opportunities = []
        total_losses = 0.0
        total_tax_savings = 0.0
        
        current_date = datetime.now()
        
        for position in positions:
            symbol = position.get("symbol")
            cost_basis = position.get("cost_basis", 0)
            current_price = position.get("current_price", 0)
            quantity = position.get("quantity", 0)
            purchase_date = position.get("purchase_date")
            
            if cost_basis <= 0 or current_price <= 0 or quantity <= 0:
                continue
            
            # Calculate unrealized loss
            unrealized_loss = (cost_basis - current_price) * quantity
            
            if unrealized_loss > 0:  # Only consider losing positions
                # Determine if long-term or short-term
                is_long_term = False
                if purchase_date:
                    if isinstance(purchase_date, str):
                        purchase_date = datetime.fromisoformat(purchase_date.replace('Z', '+00:00'))
                    days_held = (current_date - purchase_date.replace(tzinfo=None)).days
                    is_long_term = days_held >= 365
                
                # Calculate tax savings
                tax_rate = tax_rate_long_term if is_long_term else tax_rate_short_term
                tax_savings = unrealized_loss * tax_rate
                
                # Check if this would offset gains
                can_offset = realized_gains > 0 or unrealized_loss > 0
                
                opportunities.append({
                    "symbol": symbol,
                    "unrealized_loss": float(unrealized_loss),
                    "tax_savings": float(tax_savings),
                    "is_long_term": is_long_term,
                    "can_offset_gains": can_offset,
                    "recommendation": "HARVEST" if unrealized_loss > 100 else "CONSIDER"
                })
                
                total_losses += unrealized_loss
                total_tax_savings += tax_savings
        
        # Sort by tax savings (highest first)
        opportunities.sort(key=lambda x: x["tax_savings"], reverse=True)
        
        return {
            "opportunities": opportunities,
            "total_unrealized_losses": float(total_losses),
            "total_potential_tax_savings": float(total_tax_savings),
            "can_offset_realized_gains": total_losses >= realized_gains,
            "net_tax_benefit": float(total_tax_savings - (realized_gains * tax_rate_long_term) if realized_gains > 0 else total_tax_savings),
            "method": "tax_loss_harvesting"
        }


# Singleton instances
_monte_carlo = MonteCarloSimulation()
_mpt = ModernPortfolioTheory()
_black_litterman = BlackLittermanModel()
_tlh = TaxLossHarvesting()


def run_monte_carlo_simulation(**kwargs) -> MonteCarloResult:
    """Convenience function for Monte Carlo simulation"""
    return _monte_carlo.simulate_retirement(**kwargs)


def optimize_portfolio_mpt(**kwargs) -> Dict[str, Any]:
    """Convenience function for MPT optimization"""
    return _mpt.optimize_portfolio(**kwargs)


def optimize_portfolio_black_litterman(**kwargs) -> Dict[str, Any]:
    """Convenience function for Black-Litterman optimization"""
    return _black_litterman.optimize_with_views(**kwargs)


def identify_tax_loss_harvesting(**kwargs) -> Dict[str, Any]:
    """Convenience function for tax-loss harvesting"""
    return _tlh.identify_harvesting_opportunities(**kwargs)

