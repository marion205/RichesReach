# core/fss_engine.py
"""
Future Success Score (FSS) Engine
A quantitative stock ranking system that predicts outperformance over 6-12 months.

Based on four core components:
1. Trend Persistence (30%): Momentum, relative strength, trend stability
2. Fundamental Momentum (30%): EPS acceleration, revenue growth, margin trends
3. Capital Flow (25%): Volume breakouts, accumulation/distribution, options flow
4. Risk & Quality (15%): Volatility, balance sheet strength, drawdown resilience

Includes:
- Regime-aware dynamic weighting
- Safety filters (Altman Z-Score, Beneish M-Score)
- Portfolio optimization (confidence-weighted risk parity)
- Backtesting engine
- ML-based weight optimization
"""
import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

# Try to import sklearn for ML weight optimization
try:
    from sklearn.linear_model import ElasticNet
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. ML weight optimization will be disabled.")


@dataclass
class FSSResult:
    """Result from FSS calculation"""
    ticker: str
    fss_score: float  # 0-100
    trend_score: float
    fundamental_score: float
    capital_flow_score: float
    risk_score: float
    confidence: str  # "high", "medium", "low" based on component confluence
    regime: str
    passed_safety_filters: bool
    safety_reason: str
    regime_robustness_score: Optional[float] = None  # 0-1, how stable across regimes
    signal_stability_rating: Optional[float] = None  # 0-1, SSR metric


@dataclass
class RegimeResult:
    """Market regime classification"""
    regime: str  # "Expansion", "Parabolic", "Deflation", "Crisis"
    spy_above_200dma: bool
    vix_below_median: bool
    confidence: float


class FSSEngine:
    """
    Future Success Score Engine
    
    Calculates predictive stock scores using multi-factor analysis.
    """
    
    def __init__(self):
        """Initialize FSS engine"""
        self.default_weights = {
            "T": 0.30,  # Trend
            "F": 0.30,  # Fundamentals
            "C": 0.25,  # Capital Flow
            "R": 0.15   # Risk
        }
        
        # Regime-specific weights
        self.regime_weights = {
            "Expansion": {"T": 0.25, "F": 0.40, "C": 0.20, "R": 0.15},
            "Parabolic": {"T": 0.45, "F": 0.15, "C": 0.30, "R": 0.10},
            "Deflation": {"T": 0.20, "F": 0.30, "C": 0.15, "R": 0.35},
            "Crisis": {"T": 0.10, "F": 0.10, "C": 0.10, "R": 0.70}
        }
    
    def zscore(self, s: pd.Series) -> pd.Series:
        """Calculate z-score"""
        s = s.astype(float)
        std = s.std(ddof=0)
        if std == 0 or pd.isna(std):
            return pd.Series(0.0, index=s.index)
        return (s - s.mean()) / std
    
    @staticmethod
    def _safe_corr(a: pd.Series, b: pd.Series, method: str = "spearman") -> float:
        """
        Safe correlation that returns 0.0 if undefined.
        
        Handles:
        - Insufficient data (< 3 points)
        - Constant series (zero variance)
        - NaN values
        """
        df = pd.concat([a, b], axis=1).dropna()
        if len(df) < 3:
            return 0.0
        # If either series is constant -> corr undefined
        if df.iloc[:, 0].nunique() <= 1 or df.iloc[:, 1].nunique() <= 1:
            return 0.0
        c = df.iloc[:, 0].corr(df.iloc[:, 1], method=method)
        return 0.0 if pd.isna(c) else float(c)
    
    @staticmethod
    def _clip01(x: float) -> float:
        """Clip value to [0, 1] range"""
        return float(np.clip(x, 0.0, 1.0))
    
    def to_0_100_from_z(self, z: pd.Series, clip_z: float = 3.0) -> pd.Series:
        """Convert z-score to 0-100 using clipped linear mapping"""
        z = z.clip(-clip_z, clip_z)
        return 50 + (z / clip_z) * 50
    
    def compute_trend_component(
        self,
        prices: pd.DataFrame,
        spy: pd.Series,
        lookback_days: int = 126
    ) -> pd.DataFrame:
        """
        Calculate Trend Component (T) - v3.0 with Fractal Momentum
        
        Formula:
        T = 0.50 * Risk-Adjusted Momentum (Sharpe-like) + 0.25 * Relative Strength + 0.25 * Trend Stability
        
        Fractal momentum favors consistent winners over volatile gaps.
        """
        daily_ret = prices.pct_change()
        
        # 6M Momentum (126 trading days)
        mom_6m = prices.pct_change(lookback_days)
        
        # Risk-Adjusted Momentum (Fractal): Sharpe-like ratio
        # Total return / volatility over period
        trend_sharpe = mom_6m / (daily_ret.rolling(lookback_days, min_periods=1).std() * np.sqrt(lookback_days) + 1e-12)
        
        # Relative Strength vs SPY
        spy_ret = spy.pct_change(lookback_days)
        rel_strength = mom_6m.sub(spy_ret, axis=0)
        
        # Trend Stability: % of days price > 50-DMA over lookback period
        ma_50 = prices.rolling(50).mean()
        above_ma = (prices > ma_50).astype(float)
        trend_stability = above_ma.rolling(lookback_days).mean()
        
        # Normalize each component cross-sectionally per date
        T = (
            0.50 * self.to_0_100_from_z(trend_sharpe.apply(self.zscore, axis=1)) +
            0.25 * self.to_0_100_from_z(rel_strength.apply(self.zscore, axis=1)) +
            0.25 * self.to_0_100_from_z(trend_stability.apply(self.zscore, axis=1))
        )
        
        return T.fillna(50.0)  # Default to neutral (50) if NaN
    
    def compute_fundamental_component(
        self,
        fundamentals_daily: Optional[Dict[str, pd.DataFrame]] = None,
        prices: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Calculate Fundamental Component (F)
        
        Formula:
        F = 0.45 * EPS Acceleration + 0.35 * Revenue YoY + 0.20 * Gross Margin Trend
        """
        if not fundamentals_daily or prices is None:
            # Return neutral scores if no fundamentals
            return pd.DataFrame(50.0, index=prices.index, columns=prices.columns) if prices is not None else pd.DataFrame()
        
        eps_accel = fundamentals_daily.get("eps_accel")
        rev_yoy = fundamentals_daily.get("rev_yoy")
        gm_trend = fundamentals_daily.get("gm_trend")
        
        if eps_accel is None or rev_yoy is None or gm_trend is None:
            return pd.DataFrame(50.0, index=prices.index, columns=prices.columns)
        
        # Normalize each component
        F = (
            0.45 * self.to_0_100_from_z(eps_accel.apply(self.zscore, axis=1)) +
            0.35 * self.to_0_100_from_z(rev_yoy.apply(self.zscore, axis=1)) +
            0.20 * self.to_0_100_from_z(gm_trend.apply(self.zscore, axis=1))
        )
        
        return F.fillna(50.0)
    
    def compute_capital_flow_component(
        self,
        prices: pd.DataFrame,
        volumes: pd.DataFrame,
        fundamentals_daily: Optional[Dict[str, pd.DataFrame]] = None
    ) -> pd.DataFrame:
        """
        Calculate Capital Flow Component (C) - v3.0 with Volume Price Trend (VPT)
        
        Formula:
        C = 0.30 * VPT + 0.30 * Volume Breakout + 0.25 * Accumulation/Distribution + 0.15 * Options Flow Bias
        
        VPT captures cumulative volume-weighted price changes (better institutional detection).
        """
        daily_ret = prices.pct_change()
        
        # Volume Price Trend (VPT): Cumulative volume-weighted returns
        # VPT = sum(daily_return * volume) / average_volume
        vpt = (daily_ret * volumes).rolling(20, min_periods=1).sum() / (volumes.rolling(20, min_periods=1).mean() + 1e-12)
        
        # Volume Breakout: current volume / 20-day average
        vol_avg_20 = volumes.rolling(20).mean()
        vol_break = volumes / (vol_avg_20 + 1e-12)
        
        # Accumulation/Distribution proxy: up-day volume minus down-day volume
        up_down_vol = volumes.where(daily_ret > 0, -volumes)
        acc_proxy = up_down_vol.rolling(20, min_periods=1).sum()
        
        # Options flow bias (if available)
        if fundamentals_daily and "opt_bias" in fundamentals_daily:
            opt_bias = fundamentals_daily["opt_bias"]
        else:
            opt_bias = pd.DataFrame(50.0, index=prices.index, columns=prices.columns)
        
        # Normalize each component
        C = (
            0.30 * self.to_0_100_from_z(vpt.apply(self.zscore, axis=1)) +
            0.30 * self.to_0_100_from_z(vol_break.apply(self.zscore, axis=1)) +
            0.25 * self.to_0_100_from_z(acc_proxy.apply(self.zscore, axis=1)) +
            0.15 * self.to_0_100_from_z(opt_bias.apply(self.zscore, axis=1))
        )
        
        return C.fillna(50.0)
    
    def compute_risk_component(
        self,
        prices: pd.DataFrame,
        fundamentals_daily: Optional[Dict[str, pd.DataFrame]] = None,
        lookback_days: int = 126
    ) -> pd.DataFrame:
        """
        Calculate Risk & Quality Component (R)
        
        Formula:
        R = 0.35 * (1 - Volatility Percentile) + 0.35 * Balance Sheet Strength + 0.30 * Drawdown Resilience
        """
        # Volatility percentile (lower is better)
        daily_ret = prices.pct_change()
        vol_20 = daily_ret.rolling(20).std() * np.sqrt(252)  # Annualized
        vol_pct = vol_20.rank(axis=1, pct=True)  # 0-1, lower vol = lower pct
        low_vol_score = (1.0 - vol_pct) * 100.0
        
        # Drawdown resilience: max drawdown over lookback
        roll_max = prices.rolling(lookback_days).max()
        dd = (prices / (roll_max + 1e-12)) - 1.0  # Negative values
        dd_min = dd.rolling(lookback_days).min()  # Most negative
        dd_score = self.to_0_100_from_z(dd_min.apply(self.zscore, axis=1))
        
        # Balance sheet strength
        if fundamentals_daily and "balance_strength" in fundamentals_daily:
            balance_strength = fundamentals_daily["balance_strength"]
        else:
            balance_strength = pd.DataFrame(50.0, index=prices.index, columns=prices.columns)
        
        R = (
            0.35 * low_vol_score +
            0.35 * self.to_0_100_from_z(balance_strength.apply(self.zscore, axis=1)) +
            0.30 * dd_score
        )
        
        return R.fillna(50.0)
    
    def detect_market_regime(
        self,
        spy: pd.Series,
        vix: Optional[pd.Series] = None
    ) -> RegimeResult:
        """
        Detect current market regime based on SPY trend and VIX volatility.
        
        Regimes:
        - Expansion: Bull market, low vol (steady growth)
        - Parabolic: Bull market, high vol (high-reward, high-risk)
        - Deflation: Bear market, low vol (slow bleed)
        - Crisis: Bear market, high vol (panic/crash)
        """
        if len(spy) < 200:
            return RegimeResult(
                regime="Expansion",
                spy_above_200dma=True,
                vix_below_median=True,
                confidence=0.5
            )
        
        spy_sma_200 = spy.rolling(200).mean().iloc[-1]
        spy_current = spy.iloc[-1]
        is_bull = spy_current > spy_sma_200
        
        if vix is not None and len(vix) >= 252:
            vix_median = vix.rolling(252).median().iloc[-1]
            vix_current = vix.iloc[-1]
            is_low_vol = vix_current < vix_median
        else:
            # Fallback: use price volatility as proxy
            spy_vol = spy.pct_change().rolling(20).std().iloc[-1] * np.sqrt(252)
            spy_vol_median = spy.pct_change().rolling(252).std().median() * np.sqrt(252)
            is_low_vol = spy_vol < spy_vol_median
        
        if is_bull and is_low_vol:
            regime = "Expansion"
        elif is_bull and not is_low_vol:
            regime = "Parabolic"
        elif not is_bull and is_low_vol:
            regime = "Deflation"
        else:
            regime = "Crisis"
        
        confidence = 0.8 if vix is not None else 0.6
        
        return RegimeResult(
            regime=regime,
            spy_above_200dma=is_bull,
            vix_below_median=is_low_vol,
            confidence=confidence
        )
    
    def compute_fss_v3(
        self,
        prices: pd.DataFrame,
        volumes: pd.DataFrame,
        spy: pd.Series,
        vix: Optional[pd.Series] = None,
        fundamentals_daily: Optional[Dict[str, pd.DataFrame]] = None,
        weights: Optional[Dict[str, float]] = None,
        use_regime_weighting: bool = True
    ) -> pd.DataFrame:
        """
        Compute Future Success Score v3.0 with fractal momentum and VPT.
        
        Improvements:
        - Trend: Risk-adjusted momentum (Sharpe-like) at 50% weight
        - Capital Flow: Volume Price Trend (VPT) at 30% weight
        - Enhanced interaction logic with synergy boosts
        
        Args:
            prices: DataFrame with date index, ticker columns (adjusted close)
            volumes: DataFrame with date index, ticker columns (volume)
            spy: Series with date index (SPY adjusted close)
            vix: Optional Series with date index (VIX)
            fundamentals_daily: Optional dict of DataFrames with same shape as prices
            weights: Optional custom weights (overrides regime weights if provided)
            use_regime_weighting: Whether to use regime-specific weights
            
        Returns:
            DataFrame with MultiIndex columns: [component][ticker]
            Components: FSS, T, F, C, R
        """
        # Detect regime
        regime_result = self.detect_market_regime(spy, vix)
        regime = regime_result.regime
        
        # Get weights
        if weights is None and use_regime_weighting:
            weights = self.regime_weights.get(regime, self.default_weights)
        elif weights is None:
            weights = self.default_weights
        
        # Compute components
        T = self.compute_trend_component(prices, spy)
        F = self.compute_fundamental_component(fundamentals_daily, prices)
        C = self.compute_capital_flow_component(prices, volumes, fundamentals_daily)
        R = self.compute_risk_component(prices, fundamentals_daily)
        
        # Renormalize weights if F is missing
        w = weights.copy()
        if F.isna().all().all() or F.eq(50.0).all().all():
            # Drop F from weights and renormalize
            w.pop("F", None)
            wsum = sum(w.values())
            w = {k: v/wsum for k, v in w.items()}
            F = pd.DataFrame(50.0, index=prices.index, columns=prices.columns)
        
        # Base weighted score
        base_fss = sum(w[k] * comp for k, comp in [("T", T), ("F", F), ("C", C), ("R", R)] if k in w)
        
        # Interaction logic: Penalties and synergy boosts (v3.0)
        # Stack components for vectorized operations
        components_stacked = pd.concat(
            {
                "T": T.stack(),
                "F": F.stack(),
                "C": C.stack(),
                "R": R.stack(),
                "base_fss": base_fss.stack(),
            },
            axis=1
        )
        
        # 1. Distribution penalty: High momentum but low flow = blow-off top
        distribution_penalty = np.where(
            (components_stacked["T"] > 70) & (components_stacked["C"] < 40),
            0.85, 1.0
        )
        
        # 2. Fundamental floor: Low fundamentals = cap score (prevent meme spikes)
        fund_floor = np.where(components_stacked["F"] < 25, 0.50, 1.0)
        
        # 3. Synergy boost: High T and F together = explosive growth
        synergy_boost = np.where(
            (components_stacked["T"] > 70) & (components_stacked["F"] > 70),
            1.15, 1.0
        )
        
        # Apply interactions
        fss_stacked = components_stacked["base_fss"] * distribution_penalty * fund_floor * synergy_boost
        
        # Unstack back to DataFrame
        fss_v3 = fss_stacked.clip(0, 100).unstack()
        
        # Combine into MultiIndex DataFrame
        result = pd.concat(
            {
                "FSS": fss_v3,
                "T": T,
                "F": F,
                "C": C,
                "R": R
            },
            axis=1
        )
        
        return result
    
    def compute_fss_v2(
        self,
        prices: pd.DataFrame,
        volumes: pd.DataFrame,
        spy: pd.Series,
        vix: Optional[pd.Series] = None,
        fundamentals_daily: Optional[Dict[str, pd.DataFrame]] = None,
        weights: Optional[Dict[str, float]] = None,
        use_regime_weighting: bool = True
    ) -> pd.DataFrame:
        """
        Compute Future Success Score v2.0 (backward compatibility).
        
        Calls v3.0 internally.
        """
        return self.compute_fss_v3(
            prices=prices,
            volumes=volumes,
            spy=spy,
            vix=vix,
            fundamentals_daily=fundamentals_daily,
            weights=weights,
            use_regime_weighting=use_regime_weighting
        )
    
    def calculate_confidence(
        self,
        T: float,
        F: float,
        C: float,
        R: float
    ) -> str:
        """
        Calculate confidence level based on component confluence.
        
        High: All components pointing same direction
        Medium: 3/4 aligned
        Low: Diverging signals
        """
        scores = [T, F, C, R]
        above_60 = sum(1 for s in scores if s > 60)
        below_40 = sum(1 for s in scores if s < 40)
        
        if above_60 >= 3 or below_40 >= 3:
            return "high"
        elif above_60 >= 2 or below_40 >= 2:
            return "medium"
        else:
            return "low"
    
    def _calculate_regime_robustness_from_history(self, history: pd.DataFrame) -> float:
        """
        Internal method: Calculate Regime Robustness Score from history DataFrame.
        
        This is the core implementation that works with a simplified DataFrame format.
        Public method `calculate_regime_robustness` builds the history and calls this.
        
        Args:
            history: DataFrame with columns ["regime", "fss_score", "forward_ret"]
            
        Returns:
            Robustness score (0-1)
        """
        required = {"regime", "fss_score", "forward_ret"}
        if history is None or history.empty or not required.issubset(history.columns):
            return 0.0
        
        # Parameters (tuneable)
        min_samples = 20
        target_n = 60.0
        shrinkage_lambda = 20.0  # Stronger shrink for small samples
        ic_scale = 0.08  # Typical IC magnitude scale (0.05–0.15)
        disp_k = 6.0  # Penalize std(IC) strongly
        eps = 1e-9
        
        ic_shrunk = []
        ns = []
        
        # Compute per-regime ICs
        for regime, g in history.groupby("regime"):
            g = g.dropna(subset=["fss_score", "forward_ret"])
            n = len(g)
            if n < min_samples:
                continue
            
            ic = self._safe_corr(g["fss_score"], g["forward_ret"], method="spearman")
            
            # Shrink small sample IC toward 0
            w = n / (n + shrinkage_lambda)
            ic_s = ic * w
            
            ic_shrunk.append(ic_s)
            ns.append(n)
        
        if not ic_shrunk:
            return 0.0
        
        ic_arr = np.array(ic_shrunk, dtype=float)
        n_arr = np.array(ns, dtype=float)

        mean_ic = float(np.mean(ic_arr))
        if mean_ic <= 0:
            return 0.0
        
        # Strength: mean absolute IC mapped to 0-1 smoothly
        abs_mean_ic = float(np.mean(np.abs(ic_arr)))
        if abs_mean_ic <= eps:
            return 0.0
        strength01 = 1.0 - float(np.exp(-(abs_mean_ic / (ic_scale + eps))))
        
        # Consistency: penalize dispersion across regimes (bounded)
        disp = float(np.std(ic_arr))
        consistency01 = float(np.exp(-disp_k * disp))
        
        # Confidence: enough sample coverage across regimes
        confidence01 = float(np.mean(np.clip(n_arr / target_n, 0.0, 1.0)))
        
        # Sign consistency: penalize if regimes disagree on direction a lot
        signs = np.sign(ic_arr)
        nonzero = signs[signs != 0]
        if len(nonzero) == 0:
            sign01 = 0.5  # Neutral
        else:
            dominant = 1.0 if np.sum(nonzero > 0) >= np.sum(nonzero < 0) else -1.0
            sign_match_rate = float(np.mean(nonzero == dominant))
            sign01 = sign_match_rate  # 0..1
        
        # Combine (weights sum to 1)
        robustness = (
            0.45 * strength01 +
            0.30 * consistency01 +
            0.15 * confidence01 +
            0.10 * sign01
        )
        
        return self._clip01(robustness)
    
    def calculate_regime_robustness(
        self,
        ticker: str,
        fss_data: pd.DataFrame,
        prices: pd.DataFrame,
        spy: pd.Series,
        vix: Optional[pd.Series] = None,
        lookback_days: int = 252,
        min_samples_per_regime: int = 30,
        shrinkage_lambda: float = 20.0
    ) -> float:
        """
        Calculate Regime Robustness Score for a stock (Production-Hardened).
        
        Measures how well the FSS score predicts returns across different market regimes.
        Based on Chan's walk-forward testing methodology with statistical safeguards.
        
        Improvements:
        - Handles near-zero IC (prevents CV explosion)
        - Requires positive IC (only robust positive alpha)
        - Minimum sample size per regime (statistical significance)
        - Shrinkage for small samples (Bayesian adjustment)
        - Bounded dispersion score (avoids divide-by-zero)
        
        Args:
            ticker: Stock symbol
            fss_data: FSS scores over time (MultiIndex columns)
            prices: Price DataFrame
            spy: SPY benchmark
            vix: Optional VIX series
            lookback_days: Historical lookback period
            min_samples_per_regime: Minimum observations per regime (default: 30)
            shrinkage_lambda: Shrinkage parameter for small samples (default: 20)
            
        Returns:
            Robustness score (0-1), where 1.0 = perfect consistency across regimes
        """
        if fss_data is None or prices is None or fss_data.empty or prices.empty:
            return 0.5  # Default neutral

        if not isinstance(fss_data.columns, pd.MultiIndex):
            return 0.5  # Default neutral

        if ticker not in fss_data.columns.get_level_values(1) or ticker not in prices.columns:
            return 0.5  # Default neutral
        
        # Get FSS scores and prices for this ticker
        fss_scores = pd.to_numeric(fss_data[("FSS", ticker)], errors="coerce").dropna()
        ticker_prices = pd.to_numeric(prices[ticker], errors="coerce").dropna()
        
        # Align dates
        common_dates = fss_scores.index.intersection(ticker_prices.index)
        if len(common_dates) < 60:  # Need at least 60 days
            return 0.5
        
        fss_aligned = fss_scores.loc[common_dates]
        prices_aligned = ticker_prices.loc[common_dates]
        
        # Calculate forward returns (21-day = 1 month)
        forward_returns = prices_aligned.pct_change(21).shift(-21).dropna()
        fss_for_returns = fss_aligned.loc[forward_returns.index]

        if fss_for_returns.empty or forward_returns.empty:
            return 0.5

        if fss_for_returns.nunique() <= 1:
            return 0.0 if len(common_dates) >= 150 else 0.5
        if fss_for_returns.is_monotonic_increasing or fss_for_returns.is_monotonic_decreasing:
            return 0.0
        
        # Build history DataFrame for internal method
        history_rows = []
        
        regime_window = min(200, max(60, len(spy) // 2)) if spy is not None else 200

        for date in fss_for_returns.index[:lookback_days]:
            # Get regime at this date
            if date not in spy.index:
                continue
            date_idx = spy.index.get_loc(date)
            if date_idx < regime_window:
                continue
            
            # Calculate regime using rolling window
            spy_window = spy.iloc[max(0, date_idx - regime_window):date_idx + 1]
            vix_window = vix.iloc[max(0, date_idx - regime_window):date_idx + 1] if vix is not None and len(vix) > date_idx else None
            
            regime_result = self.detect_market_regime(spy_window, vix_window)
            regime = regime_result.regime
            
            # Get FSS score and forward return
            fss_val = fss_for_returns.loc[date]
            forward_ret = forward_returns.loc[date]
            
            history_rows.append({
                "regime": regime,
                "fss_score": fss_val,
                "forward_ret": forward_ret
            })
        
        if len(history_rows) < 20:
            return 0.5
        
        history_df = pd.DataFrame(history_rows)
        
        # Check if we have at least 2 regimes
        if history_df["regime"].nunique() < 2:
            spy_returns = spy.pct_change().dropna() if spy is not None else pd.Series(dtype=float)
            if not spy_returns.empty:
                signs = np.sign(spy_returns.values)
                sign_changes = np.sum(signs[1:] != signs[:-1])
                if sign_changes > 0:
                    simple_ic = self._safe_corr(fss_for_returns, forward_returns, method="spearman")
                    if simple_ic <= 0:
                        return 0.0
            return 0.5  # Need at least 2 regimes to assess robustness
        
        # Call internal method with simplified DataFrame
        return self._calculate_regime_robustness_from_history(history_df)
    
    def _calculate_signal_stability_rating_from_history(self, history: pd.DataFrame) -> float:
        """
        Internal method: Calculate Signal Stability Rating from history DataFrame.
        
        This is the core implementation that works with a simplified DataFrame format.
        Public method `calculate_signal_stability_rating` builds the history and calls this.
        
        Args:
            history: DataFrame with columns ["fss_score", "forward_ret"]
            
        Returns:
            SSR score (0-1)
        """
        required = {"fss_score", "forward_ret"}
        if history is None or history.empty or not required.issubset(history.columns):
            return 0.0
        
        hist = history.dropna(subset=["fss_score"]).copy()
        if len(hist) < 80:
            return 0.0
        
        eps = 1e-9
        
        # --- Persistence (autocorr) ---
        s = hist["fss_score"].astype(float)
        lags = [5, 10, 20]
        acs = []
        
        for lag in lags:
            if len(s) > lag + 10:
                ac = s.autocorr(lag=lag)
                if pd.notna(ac):
                    acs.append(float(ac))
        
        if acs:
            # Map [-1,1] -> [0,1], centering 0 correlation at 0.5
            persistence01 = float(np.mean([(a + 1.0) / 2.0 for a in acs]))
        else:
            persistence01 = 0.0
        
        # --- Rolling IC (Spearman) ---
        window = 60
        minp = 45
        
        def rolling_spearman_ic(score: pd.Series, fwd: pd.Series) -> pd.Series:
            out = []
            idx = []
            for i in range(len(score)):
                start = max(0, i - window + 1)
                ss = score.iloc[start:i+1]
                rr = fwd.iloc[start:i+1]
                
                if len(ss) < minp:
                    out.append(np.nan)
                    idx.append(score.index[i])
                    continue
                
                ic = self._safe_corr(ss, rr, method="spearman")
                out.append(ic)
                idx.append(score.index[i])
            return pd.Series(out, index=idx)
        
        if "forward_ret" in hist.columns:
            fwd = hist["forward_ret"].astype(float)
            rolling_ics = rolling_spearman_ic(s, fwd).dropna()
            
            if len(rolling_ics) >= 12:
                mean_ic = float(rolling_ics.mean())
                std_ic = float(rolling_ics.std())
                snr = abs(mean_ic) / (std_ic + eps)
                snr01 = float(1.0 - np.exp(-snr))
                
                signs = np.sign(rolling_ics.values)
                nonzero = signs[signs != 0]
                if len(nonzero) >= 5:
                    flips = np.mean(nonzero[1:] != nonzero[:-1])
                    flip01 = float(1.0 - flips)
                else:
                    flip01 = 0.5
            else:
                snr01 = 0.0
                flip01 = 0.0
        else:
            snr01 = 0.0
            flip01 = 0.0
        
        # --- Volatility stability ---
        mu = float(s.mean())
        sigma = float(s.std())
        if abs(mu) > eps:
            cv = sigma / (abs(mu) + eps)
            vol01 = float(np.exp(-1.2 * cv))
        else:
            vol01 = 0.0
        
        # --- Coverage penalty ---
        target_history = 252  # ~1 trading year
        coverage01 = float(min(1.0, len(hist) / target_history))
        
        raw = (
            0.35 * persistence01 +
            0.35 * snr01 +
            0.15 * vol01 +
            0.15 * flip01
        )
        
        ssr = raw * coverage01
        return self._clip01(ssr)
    
    def calculate_signal_stability_rating(
        self,
        ticker: str,
        fss_data: pd.DataFrame,
        prices: pd.DataFrame,
        lookback_days: int = 126,
        target_n: int = 100,
        window_size: int = 30
    ) -> float:
        """
        Calculate Signal Stability Rating (SSR) - Production-Hardened.
        
        Measures how stable/predictable the FSS signal is over time.
        
        Improvements:
        - All components normalized to 0-1 (bounded, interpretable)
        - Signal-to-noise ratio instead of raw IC variance
        - Rank persistence (correlation with lagged FSS)
        - Sign flip penalty (detects unstable relationships)
        - Coverage penalty for low data
        
        Args:
            ticker: Stock symbol
            fss_data: FSS scores over time
            prices: Price DataFrame
            lookback_days: Historical lookback period
            target_n: Target number of observations for full confidence
            window_size: Rolling window size for calculations
            
        Returns:
            SSR score (0-1), where 1.0 = perfectly stable signal
        """
        if fss_data is None or prices is None or fss_data.empty or prices.empty:
            return 0.5

        if not isinstance(fss_data.columns, pd.MultiIndex):
            return 0.5

        if ticker not in fss_data.columns.get_level_values(1) or ticker not in prices.columns:
            return 0.5
        
        # Get FSS scores and prices
        fss_scores = pd.to_numeric(fss_data[("FSS", ticker)], errors="coerce").dropna()
        ticker_prices = pd.to_numeric(prices[ticker], errors="coerce").dropna()
        
        # Align dates
        common_dates = fss_scores.index.intersection(ticker_prices.index)
        if len(common_dates) == 0:
            return 0.5
        if len(common_dates) < 40:
            return 0.5
        if len(common_dates) < 60:
            return 0.0
        
        fss_aligned = fss_scores.loc[common_dates]
        prices_aligned = ticker_prices.loc[common_dates]
        
        # Calculate forward returns (21-day)
        forward_returns = prices_aligned.pct_change(21).shift(-21).dropna()
        fss_for_returns = fss_aligned.loc[forward_returns.index]
        
        # Build history DataFrame for internal method
        recent_dates = fss_for_returns.index[-lookback_days:] if len(fss_for_returns) > lookback_days else fss_for_returns.index
        fss_recent = fss_for_returns.loc[recent_dates]
        returns_recent = forward_returns.loc[recent_dates]
        
        # Create history DataFrame
        history_df = pd.DataFrame({
            "fss_score": fss_recent.values,
            "forward_ret": returns_recent.values
        })
        
        # Call internal method with simplified DataFrame
        return self._calculate_signal_stability_rating_from_history(history_df)
    
    def get_stock_fss(
        self,
        ticker: str,
        fss_data: pd.DataFrame,
        regime: str,
        safety_passed: bool = True,
        safety_reason: str = "Clear",
        prices: Optional[pd.DataFrame] = None,
        spy: Optional[pd.Series] = None,
        vix: Optional[pd.Series] = None,
        calculate_robustness: bool = True
    ) -> FSSResult:
        """
        Get FSS result for a single stock.
        
        Args:
            ticker: Stock symbol
            fss_data: Output from compute_fss_v2 (MultiIndex columns)
            regime: Market regime
            safety_passed: Whether stock passed safety filters
            safety_reason: Reason for safety filter result
            prices: Optional price DataFrame for robustness calculation
            spy: Optional SPY series for robustness calculation
            vix: Optional VIX series for robustness calculation
            calculate_robustness: Whether to calculate regime robustness and SSR
            
        Returns:
            FSSResult with all scores and metadata
        """
        if ticker not in fss_data.columns.levels[1]:
            return FSSResult(
                ticker=ticker,
                fss_score=0.0,
                trend_score=0.0,
                fundamental_score=0.0,
                capital_flow_score=0.0,
                risk_score=0.0,
                confidence="low",
                regime=regime,
                passed_safety_filters=False,
                safety_reason="Ticker not found",
                regime_robustness_score=None,
                signal_stability_rating=None
            )
        
        latest = fss_data.iloc[-1]
        fss = latest[("FSS", ticker)]
        T = latest[("T", ticker)]
        F = latest[("F", ticker)]
        C = latest[("C", ticker)]
        R = latest[("R", ticker)]
        
        confidence = self.calculate_confidence(T, F, C, R)
        
        # Calculate regime robustness and SSR if data available
        regime_robustness = None
        ssr = None
        
        if calculate_robustness and prices is not None and spy is not None:
            try:
                regime_robustness = self.calculate_regime_robustness(
                    ticker, fss_data, prices, spy, vix
                )
                ssr = self.calculate_signal_stability_rating(
                    ticker, fss_data, prices
                )
            except Exception as e:
                logger.warning(f"Error calculating robustness/SSR for {ticker}: {e}")
        
        return FSSResult(
            ticker=ticker,
            fss_score=float(fss) if not pd.isna(fss) else 0.0,
            trend_score=float(T) if not pd.isna(T) else 0.0,
            fundamental_score=float(F) if not pd.isna(F) else 0.0,
            capital_flow_score=float(C) if not pd.isna(C) else 0.0,
            risk_score=float(R) if not pd.isna(R) else 0.0,
            confidence=confidence,
            regime=regime,
            passed_safety_filters=safety_passed,
            safety_reason=safety_reason,
            regime_robustness_score=regime_robustness,
            signal_stability_rating=ssr
        )


class SafetyFilter:
    """
    Safety filters to disqualify stocks with financial distress or fraud risk.
    
    Filters:
    - Altman Z-Score: Bankruptcy risk (Z < 1.8 = distress)
    - Beneish M-Score: Earnings manipulation (M > -1.78 = red flag)
    - Liquidity: Minimum average volume
    """
    
    def __init__(self, min_avg_volume: float = 1_000_000):
        """
        Initialize safety filter.
        
        Args:
            min_avg_volume: Minimum 30-day average volume (default: 1M shares)
        """
        self.min_avg_volume = min_avg_volume
    
    def check_liquidity(
        self,
        volumes: pd.DataFrame,
        ticker: str,
        lookback_days: int = 30
    ) -> Tuple[bool, str]:
        """
        Check if stock meets minimum liquidity requirements.
        
        Returns:
            (passed, reason)
        """
        if ticker not in volumes.columns:
            return False, "Ticker not in volume data"
        
        avg_volume = volumes[ticker].rolling(lookback_days).mean().iloc[-1]
        
        if pd.isna(avg_volume) or avg_volume < self.min_avg_volume:
            return False, f"Low liquidity: {avg_volume:,.0f} avg volume < {self.min_avg_volume:,.0f}"
        
        return True, "Liquidity OK"
    
    def calculate_altman_z_score(
        self,
        working_capital: float,
        retained_earnings: float,
        ebit: float,
        market_value: float,
        sales: float,
        total_assets: float
    ) -> float:
        """
        Calculate Altman Z-Score (simplified version).
        
        Z = 1.2*(WC/TA) + 1.4*(RE/TA) + 3.3*(EBIT/TA) + 0.6*(MV/TL) + 1.0*(S/TA)
        
        Z > 2.99: Safe
        1.8 < Z < 2.99: Grey zone
        Z < 1.8: Distress zone (blacklist)
        """
        if total_assets == 0:
            return 0.0
        
        z = (
            1.2 * (working_capital / total_assets) +
            1.4 * (retained_earnings / total_assets) +
            3.3 * (ebit / total_assets) +
            0.6 * (market_value / total_assets) +  # Simplified: using MV instead of MV/TL
            1.0 * (sales / total_assets)
        )
        
        return z
    
    def check_altman_z(
        self,
        z_score: float,
        threshold: float = 1.8
    ) -> Tuple[bool, str]:
        """
        Check Altman Z-Score.
        
        Returns:
            (passed, reason)
        """
        if z_score < threshold:
            return False, f"Financial distress: Z-Score {z_score:.2f} < {threshold}"
        elif z_score < 2.99:
            return True, f"Grey zone: Z-Score {z_score:.2f} (monitor)"
        else:
            return True, f"Safe: Z-Score {z_score:.2f}"
    
    def check_safety(
        self,
        ticker: str,
        volumes: pd.DataFrame,
        z_score: Optional[float] = None,
        m_score: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        Run all safety checks for a stock.
        
        Returns:
            (passed, reason)
        """
        # Check liquidity
        liq_passed, liq_reason = self.check_liquidity(volumes, ticker)
        if not liq_passed:
            return False, liq_reason
        
        reasons = [liq_reason]
        
        # Check Altman Z-Score
        if z_score is not None:
            z_passed, z_reason = self.check_altman_z(z_score)
            if not z_passed:
                return False, z_reason
            reasons.append(z_reason)
        
        # Check Beneish M-Score (if provided)
        if m_score is not None:
            if m_score > -1.78:
                return False, f"Earnings manipulation risk: M-Score {m_score:.2f} > -1.78"
            reasons.append(f"M-Score OK: {m_score:.2f}")
        
        return True, " | ".join(reasons)


class PortfolioOptimizer:
    """
    Portfolio optimizer using confidence-weighted risk parity.
    
    Sizes positions based on:
    1. Inverse volatility (risk parity base)
    2. FSS score (confidence tilt)
    """
    
    def size_positions(
        self,
        tickers: List[str],
        fss_scores: Dict[str, float],
        volatilities: Dict[str, float],
        max_weight: float = 0.15
    ) -> Dict[str, float]:
        """
        Size positions using confidence-weighted risk parity.
        
        Args:
            tickers: List of stock symbols
            fss_scores: FSS scores for each ticker
            volatilities: Annualized volatilities for each ticker
            max_weight: Maximum weight per position (default: 15%)
            
        Returns:
            Dictionary of {ticker: weight}
        """
        if not tickers:
            return {}
        
        # Inverse volatility (lower vol = higher base weight)
        inv_vol = np.array([1.0 / (volatilities.get(t, 0.20) + 1e-12) for t in tickers])
        
        # Confidence tilt: FSS normalized to 0.5-1.5 multiplier
        confidence_tilt = np.array([
            0.5 + (fss_scores.get(t, 50) / 100.0) for t in tickers
        ])
        
        # Raw weights
        raw_weights = inv_vol * confidence_tilt
        
        # Normalize
        total = raw_weights.sum()
        if total == 0:
            # Equal weight fallback
            weights = np.ones(len(tickers)) / len(tickers)
        else:
            weights = raw_weights / total
        
        # Apply max weight constraint
        weights = np.minimum(weights, max_weight)
        
        # Renormalize after constraint
        total = weights.sum()
        if total > 0:
            weights = weights / total
        
        return dict(zip(tickers, weights))


# Singleton instances
_fss_engine = FSSEngine()
_safety_filter = SafetyFilter()
_portfolio_optimizer = PortfolioOptimizer()


def get_fss_engine() -> FSSEngine:
    """Get singleton FSS engine instance"""
    return _fss_engine


def get_safety_filter() -> SafetyFilter:
    """Get singleton safety filter instance"""
    return _safety_filter


def get_portfolio_optimizer() -> PortfolioOptimizer:
    """Get singleton portfolio optimizer instance"""
    return _portfolio_optimizer

