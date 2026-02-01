# core/chan_quant_signal_engine.py
"""
Chan Quantitative Signal Engine
Translates Ernest P. Chan's algorithmic primitives into RichesReach explainable signals.

Core Philosophy:
- Don't auto-trade → Generate explainable intelligence
- Mean Reversion → Reversion Probability Score
- Momentum → Timing Confidence Indicator
- Risk Management → Capital Safety Score
- Backtesting → Regime Robustness Score

Based on "Quantitative Trading" by Ernest P. Chan
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


@dataclass
class MeanReversionSignal:
    """Mean reversion signal with explainable metrics"""
    symbol: str
    current_price: float
    mean_price: float
    deviation_sigma: float  # How many standard deviations from mean
    reversion_probability: float  # 0-1, probability of reversion within timeframe
    expected_drawdown: float  # Expected max drawdown before reversion
    timeframe_days: int  # Expected reversion timeframe
    confidence: str  # "high", "medium", "low"
    explanation: str  # Human-readable explanation


@dataclass
class MomentumSignal:
    """Momentum signal with multi-timeframe confirmation"""
    symbol: str
    current_price: float
    momentum_alignment: Dict[str, bool]  # {"daily": True, "weekly": True, "monthly": False}
    trend_persistence_half_life: float  # Days until momentum decays by 50%
    momentum_decay_probability: float  # Probability momentum decays in next 7 days
    timing_confidence: float  # 0-1, overall timing confidence
    confidence: str  # "high", "medium", "low"
    explanation: str  # Human-readable explanation


@dataclass
class KellyPositionSize:
    """Kelly Criterion-based position sizing"""
    symbol: str
    win_rate: float  # Historical win rate (0-1)
    avg_win: float  # Average win amount
    avg_loss: float  # Average loss amount
    kelly_fraction: float  # Optimal Kelly fraction (0-1)
    recommended_fraction: float  # Conservative Kelly (usually Kelly * 0.25)
    max_drawdown_risk: float  # Expected max drawdown with this position size
    explanation: str  # Human-readable explanation


@dataclass
class RegimeRobustnessScore:
    """Signal stability across market regimes"""
    symbol: str
    signal_type: str  # "mean_reversion" or "momentum"
    regimes_tested: List[str]  # ["Expansion", "Crisis", "Deflation", etc.]
    robustness_score: float  # 0-1, how stable across regimes
    worst_regime_performance: float  # Worst Sharpe/return in any regime
    best_regime_performance: float  # Best Sharpe/return in any regime
    explanation: str  # Human-readable explanation


class ChanQuantSignalEngine:
    """
    Chan Quantitative Signal Engine
    
    Translates Chan's strategies into explainable RichesReach signals.
    """
    
    def __init__(self, lookback_days: int = 252):
        """
        Initialize Chan signal engine.
        
        Args:
            lookback_days: Historical lookback period for calculations
        """
        self.lookback_days = lookback_days
    
    def calculate_mean_reversion_signal(
        self,
        symbol: str,
        prices: pd.Series,
        lookback_window: int = 20,  # Chan uses 20-day for Bollinger Bands
        reversion_horizon: int = 10,
        num_std: float = 2.0  # Bollinger Bands typically use 2 standard deviations
    ) -> MeanReversionSignal:
        """
        Calculate mean reversion signal using Bollinger Bands (Chan's method).
        
        Chan's Approach:
        - Uses Bollinger Bands: MA ± (num_std × std)
        - Entry when price touches lower/upper band (oversold/overbought)
        - Exit when price returns to mean
        - Based on "Quantitative Trading" Chapter 2
        
        Returns:
            MeanReversionSignal with explainable metrics
        """
        if len(prices) < lookback_window:
            return MeanReversionSignal(
                symbol=symbol,
                current_price=float(prices.iloc[-1]) if len(prices) > 0 else 0.0,
                mean_price=0.0,
                deviation_sigma=0.0,
                reversion_probability=0.5,
                expected_drawdown=0.0,
                timeframe_days=reversion_horizon,
                confidence="low",
                explanation=f"Insufficient data for {symbol} mean reversion analysis"
            )
        
        # Bollinger Bands calculation (Chan's method)
        # Rolling mean and std (using lookback_window)
        rolling_mean = prices.rolling(window=lookback_window, min_periods=1).mean()
        rolling_std = prices.rolling(window=lookback_window, min_periods=1).std()
        
        # Current values
        mean_price = float(rolling_mean.iloc[-1])
        std_price = float(rolling_std.iloc[-1])
        current_price = float(prices.iloc[-1])
        
        # Bollinger Bands
        upper_band = mean_price + (num_std * std_price)
        lower_band = mean_price - (num_std * std_price)
        
        # Deviation in standard deviations (Bollinger Band %B)
        if std_price > 0:
            # %B = (Price - Lower Band) / (Upper Band - Lower Band)
            # When %B = 0, price is at lower band; %B = 1, price is at upper band
            bb_percent = (current_price - lower_band) / (upper_band - lower_band) if (upper_band - lower_band) > 0 else 0.5
            # Convert to sigma deviation from mean
            deviation_sigma = (current_price - mean_price) / std_price
        else:
            deviation_sigma = 0.0
            bb_percent = 0.5
        
        # Historical reversion probability using Bollinger Bands approach
        # Chan's method: look at past instances where price touched bands
        reversion_prob = self._calculate_bollinger_reversion_probability(
            prices, lookback_window, reversion_horizon, num_std, abs(deviation_sigma)
        )
        
        # Expected drawdown before reversion
        # Use historical worst-case scenarios when price was at bands
        expected_drawdown = self._estimate_expected_drawdown(
            prices, lookback_window, abs(deviation_sigma)
        )
        
        # Confidence based on Bollinger Band position (Chan's method)
        # High confidence when price is at or beyond bands (oversold/overbought)
        if abs(deviation_sigma) >= num_std and reversion_prob > 0.65:
            confidence = "high"
        elif abs(deviation_sigma) >= (num_std * 0.75) and reversion_prob > 0.55:
            confidence = "medium"
        else:
            confidence = "low"
        
        # Generate explanation using Bollinger Bands terminology
        if current_price <= lower_band:
            band_status = f"at lower Bollinger Band (oversold)"
        elif current_price >= upper_band:
            band_status = f"at upper Bollinger Band (overbought)"
        else:
            band_status = f"{abs(deviation_sigma):.2f}σ from {lookback_window}-day mean"
        
        direction = "below" if deviation_sigma < 0 else "above"
        explanation = (
            f"{symbol} is {band_status} (${current_price:.2f} vs mean ${mean_price:.2f}). "
            f"Historical reversion probability within {reversion_horizon} days: {reversion_prob*100:.1f}%. "
            f"Expected max drawdown before reversion: {expected_drawdown*100:.1f}%."
        )
        
        return MeanReversionSignal(
            symbol=symbol,
            current_price=current_price,
            mean_price=float(mean_price),
            deviation_sigma=float(deviation_sigma),
            reversion_probability=float(reversion_prob),
            expected_drawdown=float(expected_drawdown),
            timeframe_days=reversion_horizon,
            confidence=confidence,
            explanation=explanation
        )
    
    def calculate_momentum_signal(
        self,
        symbol: str,
        prices: pd.Series,
        spy: Optional[pd.Series] = None
    ) -> MomentumSignal:
        """
        Calculate momentum signal (Chan Strategy B).
        
        Core Logic:
        - Trends persist longer than intuition suggests
        - Multi-timeframe confirmation increases confidence
        - Regime-aware momentum (risk-on vs risk-off)
        
        Returns:
            MomentumSignal with explainable metrics
        """
        if len(prices) < 126:  # Need at least 6 months
            return MomentumSignal(
                symbol=symbol,
                current_price=float(prices.iloc[-1]) if len(prices) > 0 else 0.0,
                momentum_alignment={"daily": False, "weekly": False, "monthly": False},
                trend_persistence_half_life=0.0,
                momentum_decay_probability=0.5,
                timing_confidence=0.5,
                confidence="low",
                explanation=f"Insufficient data for {symbol} momentum analysis"
            )
        
        current_price = float(prices.iloc[-1])
        
        # Chan's Momentum Method: Time-series momentum
        # Uses multiple lookback periods and relative strength vs benchmark
        daily_mom = self._calculate_momentum(prices, 21)  # 1 month
        weekly_mom = self._calculate_momentum(prices, 63)  # 3 months
        monthly_mom = self._calculate_momentum(prices, 126)  # 6 months
        
        # Relative strength vs SPY (if available) - Chan emphasizes this
        relative_strength = None
        if spy is not None and len(spy) >= 126:
            spy_mom = self._calculate_momentum(spy, 126)
            if spy_mom != 0:
                relative_strength = monthly_mom / abs(spy_mom) if abs(spy_mom) > 0.01 else 1.0
        
        momentum_alignment = {
            "daily": daily_mom > 0,
            "weekly": weekly_mom > 0,
            "monthly": monthly_mom > 0
        }
        
        # Trend persistence half-life (Chan's method: uses autocorrelation)
        trend_persistence_half_life = self._estimate_trend_persistence(prices)
        
        # Momentum decay probability (next 7 days)
        momentum_decay_prob = self._estimate_momentum_decay_probability(prices)
        
        # Timing confidence (0-1) - Chan weights longer timeframes more
        # Monthly momentum gets 50% weight, weekly 30%, daily 20%
        alignment_weights = {
            "daily": 0.2,
            "weekly": 0.3,
            "monthly": 0.5
        }
        timing_confidence = sum(
            alignment_weights[tf] if momentum_alignment[tf] else 0
            for tf in momentum_alignment.keys()
        )
        
        # Boost confidence if relative strength is positive
        if relative_strength is not None and relative_strength > 1.0:
            timing_confidence = min(1.0, timing_confidence * 1.15)
        
        # Adjust for trend persistence (Chan: strong trends persist)
        if trend_persistence_half_life > 18:  # Strong persistence
            timing_confidence = min(1.0, timing_confidence * 1.2)
        
        # Confidence label
        if timing_confidence >= 0.75 and momentum_decay_prob < 0.25:
            confidence = "high"
        elif timing_confidence >= 0.5 and momentum_decay_prob < 0.4:
            confidence = "medium"
        else:
            confidence = "low"
        
        # Generate explanation with relative strength if available
        aligned = [k for k, v in momentum_alignment.items() if v]
        misaligned = [k for k, v in momentum_alignment.items() if not v]
        
        if aligned:
            explanation = (
                f"{symbol} momentum alignment: {', '.join([k.capitalize() + ' ✅' for k in aligned])}"
            )
            if misaligned:
                explanation += f" | {', '.join([k.capitalize() + ' ❌' for k in misaligned])}"
        else:
            explanation = f"{symbol} shows no momentum alignment across timeframes"
        
        if relative_strength is not None:
            explanation += f" Relative strength vs SPY: {relative_strength:.2f}x."
        
        explanation += (
            f" Trend persistence half-life: {trend_persistence_half_life:.0f} trading days. "
            f"Momentum decay probability next 7 days: {momentum_decay_prob*100:.1f}%."
        )
        
        return MomentumSignal(
            symbol=symbol,
            current_price=current_price,
            momentum_alignment=momentum_alignment,
            trend_persistence_half_life=float(trend_persistence_half_life),
            momentum_decay_probability=float(momentum_decay_prob),
            timing_confidence=float(timing_confidence),
            confidence=confidence,
            explanation=explanation
        )
    
    def calculate_kelly_position_size(
        self,
        symbol: str,
        historical_returns: pd.Series,
        win_threshold: float = 0.0  # Returns > 0 considered wins
    ) -> KellyPositionSize:
        """
        Calculate Kelly Criterion position sizing (Chan Risk Management).
        
        Core Logic:
        - Optimal position size = (win_rate * avg_win - loss_rate * avg_loss) / avg_win
        - Conservative Kelly = Kelly * 0.25 (to avoid over-leverage)
        
        Returns:
            KellyPositionSize with explainable metrics
        """
        if len(historical_returns) < 20:
            return KellyPositionSize(
                symbol=symbol,
                win_rate=0.5,
                avg_win=0.0,
                avg_loss=0.0,
                kelly_fraction=0.0,
                recommended_fraction=0.0,
                max_drawdown_risk=0.0,
                explanation=f"Insufficient data for {symbol} Kelly calculation"
            )
        
        # Calculate win rate and average win/loss
        wins = historical_returns[historical_returns > win_threshold]
        losses = historical_returns[historical_returns <= win_threshold]
        
        win_rate = len(wins) / len(historical_returns) if len(historical_returns) > 0 else 0.5
        avg_win = wins.mean() if len(wins) > 0 else 0.02  # Default 2% win
        avg_loss = abs(losses.mean()) if len(losses) > 0 else 0.01  # Default 1% loss
        
        # Kelly Criterion: f = (p * b - q) / b
        # where p = win rate, q = loss rate, b = avg_win / avg_loss
        if avg_loss > 0:
            b = avg_win / avg_loss  # Win/loss ratio
            kelly_fraction = (win_rate * b - (1 - win_rate)) / b
            kelly_fraction = max(0.0, min(1.0, kelly_fraction))  # Clamp to [0, 1]
        else:
            kelly_fraction = 0.0
        
        # Conservative Kelly (25% of full Kelly to avoid over-leverage)
        recommended_fraction = kelly_fraction * 0.25
        
        # Estimate max drawdown risk with this position size
        # Simplified: use historical volatility scaled by position size
        volatility = historical_returns.std()
        max_drawdown_risk = recommended_fraction * volatility * 2.0  # 2-sigma estimate
        
        # Generate explanation
        explanation = (
            f"Based on historical win-rate ({win_rate*100:.1f}%) and risk/reward (avg win {avg_win*100:.1f}%, "
            f"avg loss {avg_loss*100:.1f}%), optimal Kelly fraction is {kelly_fraction*100:.1f}%. "
            f"Conservative recommendation: {recommended_fraction*100:.1f}% of equity. "
            f"Expected max drawdown risk: {max_drawdown_risk*100:.1f}%."
        )
        
        return KellyPositionSize(
            symbol=symbol,
            win_rate=float(win_rate),
            avg_win=float(avg_win),
            avg_loss=float(avg_loss),
            kelly_fraction=float(kelly_fraction),
            recommended_fraction=float(recommended_fraction),
            max_drawdown_risk=float(max_drawdown_risk),
            explanation=explanation
        )
    
    def calculate_regime_robustness(
        self,
        symbol: str,
        signal_type: str,
        prices: pd.Series,
        regime_series: pd.Series,  # Date-indexed series with regime labels
        lookback_days: int = 252
    ) -> RegimeRobustnessScore:
        """
        Calculate regime robustness score (Chan Backtesting).
        
        Core Logic:
        - Signal should work across multiple market regimes
        - Avoid overfitting to single regime
        - Walk-forward validation
        
        Returns:
            RegimeRobustnessScore with explainable metrics
        """
        if len(prices) < lookback_days or len(regime_series) < lookback_days:
            return RegimeRobustnessScore(
                symbol=symbol,
                signal_type=signal_type,
                regimes_tested=[],
                robustness_score=0.5,
                worst_regime_performance=0.0,
                best_regime_performance=0.0,
                explanation=f"Insufficient data for {symbol} regime robustness analysis"
            )
        
        # Align prices and regime series
        common_dates = prices.index.intersection(regime_series.index)
        if len(common_dates) < 60:
            return RegimeRobustnessScore(
                symbol=symbol,
                signal_type=signal_type,
                regimes_tested=[],
                robustness_score=0.5,
                worst_regime_performance=0.0,
                best_regime_performance=0.0,
                explanation=f"Insufficient overlapping data for {symbol} regime analysis"
            )
        
        prices_aligned = prices.loc[common_dates]
        regime_aligned = regime_series.loc[common_dates]
        
        # Calculate performance by regime
        returns = prices_aligned.pct_change().dropna()
        regime_returns = {}
        
        for regime in regime_aligned.unique():
            regime_mask = regime_aligned == regime
            regime_ret = returns[regime_mask]
            if len(regime_ret) > 10:  # Need at least 10 data points
                # Calculate Sharpe-like metric
                if regime_ret.std() > 0:
                    sharpe_like = regime_ret.mean() / regime_ret.std() * np.sqrt(252)
                else:
                    sharpe_like = 0.0
                regime_returns[regime] = sharpe_like
        
        if not regime_returns:
            return RegimeRobustnessScore(
                symbol=symbol,
                signal_type=signal_type,
                regimes_tested=[],
                robustness_score=0.5,
                worst_regime_performance=0.0,
                best_regime_performance=0.0,
                explanation=f"No valid regime data for {symbol}"
            )
        
        regimes_tested = list(regime_returns.keys())
        worst_performance = min(regime_returns.values())
        best_performance = max(regime_returns.values())
        
        # Robustness score: how consistent across regimes
        # Higher score = more consistent (lower variance in performance)
        if len(regime_returns) > 1:
            performance_values = list(regime_returns.values())
            performance_std = np.std(performance_values)
            performance_mean = np.mean(performance_values)
            
            # Normalize to 0-1 (lower std = higher robustness)
            # Use inverse of coefficient of variation
            if abs(performance_mean) > 0.01:
                cv = performance_std / abs(performance_mean)
                robustness_score = 1.0 / (1.0 + cv)  # Maps to [0, 1]
            else:
                robustness_score = 0.5
        else:
            robustness_score = 0.5  # Can't assess robustness with one regime
        
        # Generate explanation
        explanation = (
            f"{symbol} {signal_type} signal tested across {len(regimes_tested)} regimes: "
            f"{', '.join(regimes_tested)}. Performance range: {worst_performance:.2f} to {best_performance:.2f} "
            f"(Sharpe-like). Robustness score: {robustness_score*100:.1f}% "
            f"({'High' if robustness_score > 0.7 else 'Medium' if robustness_score > 0.5 else 'Low'} consistency)."
        )
        
        return RegimeRobustnessScore(
            symbol=symbol,
            signal_type=signal_type,
            regimes_tested=regimes_tested,
            robustness_score=float(robustness_score),
            worst_regime_performance=float(worst_performance),
            best_regime_performance=float(best_performance),
            explanation=explanation
        )
    
    # ========== Helper Methods ==========
    
    def _calculate_bollinger_reversion_probability(
        self,
        prices: pd.Series,
        lookback_window: int,
        reversion_horizon: int,
        num_std: float,
        current_sigma: float
    ) -> float:
        """
        Calculate historical reversion probability using Bollinger Bands method (Chan's approach).
        
        Looks at past instances where price touched Bollinger Bands and measures
        how often it reverted to the mean within the horizon.
        """
        if len(prices) < lookback_window + reversion_horizon:
            return 0.5  # Default neutral
        
        reversion_count = 0
        total_count = 0
        
        for i in range(lookback_window, len(prices) - reversion_horizon):
            # Calculate Bollinger Bands at this point in time
            window_prices = prices.iloc[i-lookback_window:i]
            mean_price = window_prices.mean()
            std_price = window_prices.std()
            
            if std_price > 0:
                current_price_at_i = prices.iloc[i]
                upper_band = mean_price + (num_std * std_price)
                lower_band = mean_price - (num_std * std_price)
                
                # Check if price was at or beyond bands (similar to current situation)
                sigma_at_i = abs((current_price_at_i - mean_price) / std_price)
                
                # Match if sigma is close to current sigma (within 20%)
                if abs(sigma_at_i - current_sigma) / max(current_sigma, 0.1) <= 0.2:
                    total_count += 1
                    
                    # Check if price reverted to mean within horizon
                    future_prices = prices.iloc[i:i+reversion_horizon]
                    future_mean = window_prices.mean()  # Use same mean for consistency
                    future_std = window_prices.std()
                    
                    if future_std > 0:
                        # Check if price moved back toward mean
                        future_sigma = abs((future_prices.iloc[-1] - future_mean) / future_std)
                        # Reversion: future sigma is significantly less than current
                        if future_sigma < sigma_at_i * 0.7:  # Reverted by at least 30%
                            reversion_count += 1
        
        return reversion_count / total_count if total_count > 0 else 0.5
    
    def _estimate_expected_drawdown(
        self,
        prices: pd.Series,
        lookback_window: int,
        sigma_threshold: float
    ) -> float:
        """Estimate expected drawdown before reversion"""
        if len(prices) < lookback_window + 20:
            return 0.05  # Default 5%
        
        drawdowns = []
        
        for i in range(lookback_window, len(prices) - 20):
            window_prices = prices.iloc[i-lookback_window:i]
            mean_price = window_prices.mean()
            std_price = window_prices.std()
            
            if std_price > 0:
                current_sigma = abs((prices.iloc[i] - mean_price) / std_price)
                
                if current_sigma >= sigma_threshold * 0.8:
                    # Calculate max drawdown in next 20 days
                    future_prices = prices.iloc[i:i+20]
                    peak = future_prices.max()
                    trough = future_prices.min()
                    if peak > 0:
                        drawdown = (peak - trough) / peak
                        drawdowns.append(drawdown)
        
        return np.mean(drawdowns) if drawdowns else 0.05
    
    def _calculate_momentum(self, prices: pd.Series, days: int) -> float:
        """Calculate momentum over N days"""
        if len(prices) < days:
            return 0.0
        return float((prices.iloc[-1] / prices.iloc[-days] - 1.0))
    
    def _estimate_trend_persistence(self, prices: pd.Series) -> float:
        """Estimate trend persistence half-life in days"""
        if len(prices) < 60:
            return 10.0  # Default
        
        # Use autocorrelation of returns to estimate persistence
        returns = prices.pct_change().dropna()
        if len(returns) < 30:
            return 10.0
        
        # Simple estimate: how many days until momentum correlation drops to 0.5
        # This is a simplified approach
        autocorr = returns.autocorr(lag=1)
        if autocorr > 0:
            # Rough estimate: half-life ≈ -ln(0.5) / ln(autocorr)
            half_life = -np.log(0.5) / np.log(max(0.01, autocorr))
            return float(min(half_life, 60.0))  # Cap at 60 days
        
        return 10.0  # Default
    
    def _estimate_momentum_decay_probability(self, prices: pd.Series) -> float:
        """Estimate probability momentum decays in next 7 days"""
        if len(prices) < 30:
            return 0.5  # Default neutral
        
        # Look at historical momentum reversals
        returns = prices.pct_change().dropna()
        if len(returns) < 20:
            return 0.5
        
        # Count how often positive momentum (last 21 days) reverses in next 7 days
        momentum_21d = prices.pct_change(21)
        momentum_7d_future = prices.shift(-7).pct_change(7)
        
        # Align indices
        common_idx = momentum_21d.index.intersection(momentum_7d_future.index)
        if len(common_idx) < 10:
            return 0.5
        
        momentum_21d_aligned = momentum_21d.loc[common_idx]
        momentum_7d_future_aligned = momentum_7d_future.loc[common_idx]
        
        # Count reversals (positive momentum → negative future, or vice versa)
        positive_mom = momentum_21d_aligned > 0
        negative_future = momentum_7d_future_aligned < 0
        
        reversals = (positive_mom & negative_future).sum()
        total_positive = positive_mom.sum()
        
        if total_positive > 0:
            decay_prob = reversals / total_positive
        else:
            decay_prob = 0.5
        
        return float(decay_prob)

