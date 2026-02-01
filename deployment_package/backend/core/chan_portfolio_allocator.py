"""
Chan-Style Portfolio Allocator

Implements portfolio allocation following Ernest Chan's principles:
1. Kelly Criterion for individual position sizing
2. Correlation-aware diversification (prevents correlated crash)
3. Risk Parity base with FSS confidence tilt
4. Regime-aware constraints

Key insight: Individual Kelly sizing can lead to massive drawdowns if all positions
are correlated (e.g., 5 tech stocks all crashing together).
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PortfolioAllocationResult:
    """Result from portfolio allocation"""
    weights: Dict[str, float]  # {ticker: weight}
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
    max_drawdown_estimate: float
    diversification_score: float  # 0-1, how well diversified
    method: str  # "mvo", "risk_parity", "kelly_constrained"
    warnings: List[str]


class ChanPortfolioAllocator:
    """
    Portfolio allocator following Chan's quantitative trading principles.
    
    Combines:
    - Individual Kelly sizing (from ChanQuantSignalEngine)
    - Correlation-aware diversification
    - Risk parity base
    - FSS confidence weighting
    """
    
    def __init__(
        self,
        max_position_size: float = 0.15,  # Max 15% per position
        min_position_size: float = 0.01,  # Min 1% per position
        target_correlation: float = 0.3,  # Penalize correlations > 0.3
        risk_free_rate: float = 0.04  # 4% risk-free rate
    ):
        """
        Initialize portfolio allocator.
        
        Args:
            max_position_size: Maximum weight per position (default: 15%)
            min_position_size: Minimum weight per position (default: 1%)
            target_correlation: Target correlation threshold (default: 0.3)
            risk_free_rate: Risk-free rate for Sharpe calculation
        """
        self.max_position_size = max_position_size
        self.min_position_size = min_position_size
        self.target_correlation = target_correlation
        self.risk_free_rate = risk_free_rate
    
    def allocate_portfolio(
        self,
        tickers: List[str],
        kelly_fractions: Dict[str, float],  # From ChanQuantSignalEngine
        fss_scores: Dict[str, float],
        fss_robustness: Dict[str, float],  # Regime robustness scores
        returns_matrix: pd.DataFrame,  # Historical returns (for correlation)
        volatilities: Dict[str, float],
        method: str = "kelly_constrained"  # "mvo", "risk_parity", "kelly_constrained"
    ) -> PortfolioAllocationResult:
        """
        Allocate portfolio using Chan-style methodology.
        
        Args:
            tickers: List of stock symbols
            kelly_fractions: Kelly-optimal position sizes (from Chan engine)
            fss_scores: FSS scores for each ticker
            fss_robustness: Regime robustness scores (0-1)
            returns_matrix: Historical returns DataFrame (columns = tickers)
            volatilities: Annualized volatilities
            method: Allocation method ("mvo", "risk_parity", "kelly_constrained")
            
        Returns:
            PortfolioAllocationResult with weights and metrics
        """
        if not tickers:
            return PortfolioAllocationResult(
                weights={},
                expected_return=0.0,
                expected_volatility=0.0,
                sharpe_ratio=0.0,
                max_drawdown_estimate=0.0,
                diversification_score=0.0,
                method=method,
                warnings=["No tickers provided"]
            )
        
        # Filter tickers that have all required data
        valid_tickers = [
            t for t in tickers
            if t in kelly_fractions
            and t in fss_scores
            and t in fss_robustness
            and t in volatilities
            and t in returns_matrix.columns
        ]
        
        if len(valid_tickers) < 2:
            return PortfolioAllocationResult(
                weights={t: 1.0 / len(valid_tickers) if valid_tickers else 0.0 for t in valid_tickers},
                expected_return=0.0,
                expected_volatility=0.0,
                sharpe_ratio=0.0,
                max_drawdown_estimate=0.0,
                diversification_score=0.0,
                method=method,
                warnings=["Insufficient data for portfolio allocation"]
            )
        
        # Calculate correlation matrix
        corr_matrix = returns_matrix[valid_tickers].corr()
        
        if method == "kelly_constrained":
            weights = self._kelly_constrained_allocation(
                valid_tickers, kelly_fractions, fss_scores, fss_robustness,
                corr_matrix, volatilities
            )
        elif method == "risk_parity":
            weights = self._risk_parity_allocation(
                valid_tickers, fss_scores, fss_robustness, corr_matrix, volatilities
            )
        elif method == "mvo":
            weights = self._mean_variance_optimization(
                valid_tickers, fss_scores, fss_robustness, corr_matrix, volatilities
            )
        else:
            # Fallback to equal weight
            weights = {t: 1.0 / len(valid_tickers) for t in valid_tickers}
        
        # Calculate portfolio metrics
        portfolio_metrics = self._calculate_portfolio_metrics(
            valid_tickers, weights, returns_matrix, volatilities, corr_matrix
        )
        
        return PortfolioAllocationResult(
            weights=weights,
            expected_return=portfolio_metrics["expected_return"],
            expected_volatility=portfolio_metrics["volatility"],
            sharpe_ratio=portfolio_metrics["sharpe_ratio"],
            max_drawdown_estimate=portfolio_metrics["max_drawdown"],
            diversification_score=portfolio_metrics["diversification_score"],
            method=method,
            warnings=portfolio_metrics["warnings"]
        )
    
    def _kelly_constrained_allocation(
        self,
        tickers: List[str],
        kelly_fractions: Dict[str, float],
        fss_scores: Dict[str, float],
        fss_robustness: Dict[str, float],
        corr_matrix: pd.DataFrame,
        volatilities: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Kelly-constrained allocation with correlation penalties.
        
        Strategy:
        1. Start with individual Kelly fractions
        2. Apply correlation penalty (reduce weights of highly correlated assets)
        3. Apply robustness filter (prefer high robustness)
        4. Enforce position size constraints
        """
        # Start with Kelly fractions
        raw_weights = np.array([kelly_fractions.get(t, 0.0) for t in tickers])
        
        # Apply robustness filter (prefer high robustness)
        robustness_multiplier = np.array([
            fss_robustness.get(t, 0.5) for t in tickers
        ])
        raw_weights = raw_weights * (0.5 + robustness_multiplier)  # Scale by robustness
        
        # Apply correlation penalty
        # For each ticker, penalize if it's highly correlated with others
        correlation_penalties = np.ones(len(tickers))
        for i, ticker_i in enumerate(tickers):
            # Find maximum correlation with other tickers (worst case)
            other_tickers = [t for t in tickers if t != ticker_i]
            if other_tickers:
                max_corr = corr_matrix.loc[ticker_i, other_tickers].abs().max()
                if max_corr > self.target_correlation:
                    # Stronger penalty: reduce weight more aggressively for high correlation
                    # Penalty = 1.0 when corr = target, 0.0 when corr = 1.0
                    penalty = 1.0 - ((max_corr - self.target_correlation) / (1.0 - self.target_correlation))
                    # Apply stronger penalty for very high correlations
                    if max_corr > 0.8:
                        penalty = penalty * 0.5  # Additional penalty for very high correlation
                    correlation_penalties[i] = max(0.1, penalty)  # Allow stronger penalty (down to 10%)
        
        raw_weights = raw_weights * correlation_penalties
        
        # Normalize
        total = raw_weights.sum()
        if total > 0:
            weights = raw_weights / total
        else:
            # Fallback to equal weight
            weights = np.ones(len(tickers)) / len(tickers)
        
        # Apply position size constraints
        weights = np.clip(weights, self.min_position_size, self.max_position_size)
        
        # Renormalize after constraints
        total = weights.sum()
        if total > 0:
            weights = weights / total
        
        return dict(zip(tickers, weights))
    
    def _risk_parity_allocation(
        self,
        tickers: List[str],
        fss_scores: Dict[str, float],
        fss_robustness: Dict[str, float],
        corr_matrix: pd.DataFrame,
        volatilities: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Risk parity allocation with FSS confidence tilt.
        
        Strategy:
        1. Start with inverse volatility (risk parity base)
        2. Apply FSS confidence tilt
        3. Apply robustness filter
        4. Account for correlations
        """
        # Inverse volatility (risk parity base)
        inv_vol = np.array([1.0 / (volatilities.get(t, 0.20) + 1e-12) for t in tickers])
        
        # FSS confidence tilt (normalize FSS to 0.5-1.5 multiplier)
        fss_tilt = np.array([
            0.5 + (fss_scores.get(t, 50) / 100.0) for t in tickers
        ])
        
        # Robustness multiplier
        robustness_mult = np.array([
            0.7 + 0.3 * fss_robustness.get(t, 0.5) for t in tickers
        ])
        
        # Raw weights
        raw_weights = inv_vol * fss_tilt * robustness_mult
        
        # Apply correlation penalty
        correlation_penalties = np.ones(len(tickers))
        for i, ticker_i in enumerate(tickers):
            avg_corr = corr_matrix.loc[ticker_i, tickers].drop(ticker_i).abs().mean()
            if avg_corr > self.target_correlation:
                penalty = 1.0 - (avg_corr - self.target_correlation) / (1.0 - self.target_correlation)
                correlation_penalties[i] = max(0.3, penalty)
        
        raw_weights = raw_weights * correlation_penalties
        
        # Normalize
        total = raw_weights.sum()
        if total > 0:
            weights = raw_weights / total
        else:
            weights = np.ones(len(tickers)) / len(tickers)
        
        # Apply constraints
        weights = np.clip(weights, self.min_position_size, self.max_position_size)
        total = weights.sum()
        if total > 0:
            weights = weights / total
        
        return dict(zip(tickers, weights))
    
    def _mean_variance_optimization(
        self,
        tickers: List[str],
        fss_scores: Dict[str, float],
        fss_robustness: Dict[str, float],
        corr_matrix: pd.DataFrame,
        volatilities: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Mean-variance optimization with FSS-based expected returns.
        
        Strategy:
        1. Estimate expected returns from FSS scores
        2. Build covariance matrix from correlations and volatilities
        3. Optimize for maximum Sharpe ratio
        """
        # Estimate expected returns from FSS scores
        # FSS score 50 = market return, 100 = high return, 0 = low return
        # Assume FSS maps to expected annual return: 0% to 20%
        expected_returns = np.array([
            (fss_scores.get(t, 50) / 100.0) * 0.20 * fss_robustness.get(t, 0.5)
            for t in tickers
        ])
        
        # Build covariance matrix
        vol_array = np.array([volatilities.get(t, 0.20) for t in tickers])
        cov_matrix = np.outer(vol_array, vol_array) * corr_matrix.values
        
        # Simple MVO: maximize Sharpe ratio
        # Sharpe = (expected_return - risk_free) / volatility
        # We'll use a simplified optimization (full MVO would use scipy.optimize)
        
        # Start with equal weights
        n = len(tickers)
        weights = np.ones(n) / n
        
        # Iterative improvement (simplified - full MVO would use quadratic programming)
        # Tilt toward higher Sharpe assets
        portfolio_return = np.dot(weights, expected_returns)
        portfolio_vol = np.sqrt(weights @ cov_matrix @ weights)
        portfolio_sharpe = (portfolio_return - self.risk_free_rate) / (portfolio_vol + 1e-12)
        
        # Tilt weights toward assets with better risk-adjusted returns
        asset_sharpes = (expected_returns - self.risk_free_rate) / (vol_array + 1e-12)
        sharpe_tilt = asset_sharpes / (asset_sharpes.sum() + 1e-12)
        
        # Blend equal weight with Sharpe tilt
        weights = 0.5 * weights + 0.5 * sharpe_tilt
        
        # Apply constraints
        weights = np.clip(weights, self.min_position_size, self.max_position_size)
        total = weights.sum()
        if total > 0:
            weights = weights / total
        
        return dict(zip(tickers, weights))
    
    def _calculate_portfolio_metrics(
        self,
        tickers: List[str],
        weights: Dict[str, float],
        returns_matrix: pd.DataFrame,
        volatilities: Dict[str, float],
        corr_matrix: pd.DataFrame
    ) -> Dict[str, any]:
        """Calculate portfolio-level metrics"""
        weight_array = np.array([weights.get(t, 0.0) for t in tickers])
        
        # Expected return (simplified: use historical mean)
        if len(returns_matrix) > 0:
            mean_returns = returns_matrix[tickers].mean()
            expected_return = float(np.dot(weight_array, mean_returns.values) * 252)  # Annualized
        else:
            expected_return = 0.0
        
        # Portfolio volatility
        vol_array = np.array([volatilities.get(t, 0.20) for t in tickers])
        cov_matrix = np.outer(vol_array, vol_array) * corr_matrix.values
        portfolio_vol = float(np.sqrt(weight_array @ cov_matrix @ weight_array))
        
        # Sharpe ratio
        sharpe_ratio = (expected_return - self.risk_free_rate) / (portfolio_vol + 1e-12)
        
        # Max drawdown estimate (simplified: use volatility)
        max_drawdown = portfolio_vol * 2.5  # Rough estimate (2.5 sigma)
        
        # Diversification score (lower correlation = better diversification)
        # Calculate average pairwise correlation
        n = len(tickers)
        if n > 1:
            # Get upper triangle of correlation matrix (excluding diagonal)
            corr_values = []
            for i in range(n):
                for j in range(i + 1, n):
                    corr_values.append(abs(corr_matrix.iloc[i, j]))
            avg_corr = np.mean(corr_values) if corr_values else 0.5
            # Diversification score: 1.0 = no correlation, 0.0 = perfect correlation
            diversification_score = 1.0 - avg_corr
        else:
            diversification_score = 0.0
        
        # Warnings
        warnings = []
        if diversification_score < 0.3:
            warnings.append(f"Low diversification (score: {diversification_score:.2f}) - portfolio may be over-concentrated")
        if portfolio_vol > 0.30:
            warnings.append(f"High portfolio volatility ({portfolio_vol:.1%})")
        if max(weights.values()) > 0.20:
            warnings.append("Large position size detected - consider reducing concentration")
        
        return {
            "expected_return": expected_return,
            "volatility": portfolio_vol,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "diversification_score": diversification_score,
            "warnings": warnings
        }


# Singleton instance
_chan_allocator = None


def get_chan_portfolio_allocator() -> ChanPortfolioAllocator:
    """Get singleton Chan portfolio allocator instance"""
    global _chan_allocator
    if _chan_allocator is None:
        _chan_allocator = ChanPortfolioAllocator()
    return _chan_allocator

