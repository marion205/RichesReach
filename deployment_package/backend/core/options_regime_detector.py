"""
RegimeDetector: Deterministic market condition classification.

Classifies the market environment (CRASH_PANIC, TREND_UP, MEAN_REVERSION, etc.)
based on momentum, volatility, and acceleration indicators. Includes hysteresis
to prevent flickering and data quality gates for robustness.

This is the foundation of the Strategy Router—regime determines which playbooks
are eligible, which constrains strategy selection.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple, List
import json
import logging

logger = logging.getLogger(__name__)


class RegimeDetector:
    """
    Detects market regimes to drive strategy selection.
    
    Regimes:
    - CRASH_PANIC: Market crashing, realized vol spiking, fear premium
    - TREND_UP: Sustained uptrend, price above MAs, IV stable or declining
    - TREND_DOWN: Sustained downtrend, price below MAs, short bias
    - BREAKOUT_EXPANSION: IV rising, momentum accelerating, directional uncertainty
    - MEAN_REVERSION: Choppy action, price oscillating around MA, low momentum
    - POST_EVENT_CRUSH: Post-earnings/economic event, IV crush beginning
    """
    
    # Regime thresholds and hysteresis
    LOOKBACK_PERIOD = 20  # Days for SMA calculations
    CONFIRMATION_BARS = 3  # Regime must be stable for N bars before flipping
    MIN_DATA_POINTS = 60  # Minimum bars needed for reliable indicators
    
    # Regime-specific thresholds
    RV_SPIKE_THRESHOLD = 1.2  # RV increase multiplier to trigger CRASH_PANIC
    PRICE_CRASH_THRESHOLD = -0.03  # Price distance from SMA20 (3% below)
    TREND_STRENGTH_THRESHOLD = 0.02  # Price distance from SMA (2% above/below)
    IV_EXPANSION_THRESHOLD = 1.1  # IV daily change multiplier
    IV_RANK_HIGH = 0.7  # IV rank percentile for mean reversion signal
    IV_RANK_LOW = 0.3  # IV rank percentile for low-IV signals
    PRICE_FLAT_THRESHOLD = 0.015  # Distance from SMA for choppy/range-bound
    
    # Flight Manual descriptions (why this regime matters to traders)
    REGIME_DESCRIPTIONS = {
        "CRASH_PANIC": "Market in freefall—protective puts and spreads active. Selling volatility is high-risk.",
        "TREND_UP": "Sustained rally—directional bullish strategies (calls, bull spreads) favor upside.",
        "TREND_DOWN": "Downtrend confirmed—bearish spreads and short-premium strategies are trapped.",
        "BREAKOUT_EXPANSION": "Volatility expanding, breakout forming—long gamma (straddles, strangles) have edge.",
        "MEAN_REVERSION": "Choppy range-bound action—sell premium (iron condors) exploits mean reversion.",
        "POST_EVENT_CRUSH": "IV crush underway post-event—short volatility strategies collect decay.",
        "NEUTRAL": "No clear regime—default to fundamentals and user risk tolerance.",
    }
    
    def __init__(self, lookback_period: int = LOOKBACK_PERIOD, 
                 confirmation_bars: int = CONFIRMATION_BARS):
        """
        Initialize RegimeDetector with hysteresis parameters.
        
        Args:
            lookback_period: Number of bars for SMA and indicator calculations
            confirmation_bars: Number of bars regime must be stable before switching
        """
        self.lookback = lookback_period
        self.confirmation_bars = confirmation_bars
        
        # State tracking for hysteresis
        self.previous_regime: Optional[str] = None
        self.regime_candidate: Optional[str] = None
        self.candidate_bar_count: int = 0
        self.current_regime: str = "NEUTRAL"
        
        logger.info(f"RegimeDetector initialized: lookback={lookback_period}, "
                   f"confirmation_bars={confirmation_bars}")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators for regime classification.
        
        Expected columns: ['close', 'high', 'low', 'iv', 'rv', 'volume']
        
        Returns indicators added to dataframe:
        - sma_20, sma_50: Simple moving averages
        - price_dist_sma20: Distance of price from SMA20 (% basis)
        - iv_rank: IV percentile over 252-day window
        - iv_rv_spread: IV minus RV (volatility premium)
        - rv_acceleration: Change in realized vol
        - atr: Average True Range (volatility measure)
        - returns: Daily returns
        - adx: Average Directional Index (trend strength)
        - skew_z: Skew z-score (if skew data available)
        """
        df = df.copy()
        
        # Data validation
        required_cols = ['close', 'high', 'low', 'iv', 'rv', 'volume']
        if not all(col in df.columns for col in required_cols):
            logger.warning(f"Missing required columns. Expected: {required_cols}, "
                         f"Got: {df.columns.tolist()}")
            return df
        
        # 1. Moving Averages & Price Distance
        df['sma_20'] = df['close'].rolling(self.lookback).mean()
        df['sma_50'] = df['close'].rolling(50).mean()
        df['price_dist_sma20'] = (df['close'] - df['sma_20']) / df['close']
        df['price_dist_sma50'] = (df['close'] - df['sma_50']) / df['close']
        df['sma20_slope'] = df['sma_20'] / df['sma_20'].shift(5) - 1.0

        # 1b. Daily returns
        df['returns'] = df['close'].pct_change()
        df['returns_3d'] = df['close'].pct_change(3)
        df['returns_5d'] = df['close'].pct_change(5)
        df['returns_60d'] = df['close'].pct_change(60)
        
        # 2. IV Rank (IV percentile over 252-day window)
        iv_high_252 = df['iv'].rolling(252, min_periods=20).max()
        iv_low_252 = df['iv'].rolling(252, min_periods=20).min()
        iv_range = iv_high_252 - iv_low_252
        df['iv_rank'] = (df['iv'] - iv_low_252) / iv_range.replace(0, 1)
        df['iv_rank'] = df['iv_rank'].clip(0, 1).fillna(0.5)

        # 2b. IV acceleration and z-score
        iv_mean_5 = df['iv'].rolling(5).mean()
        df['iv_accel'] = (df['iv'] / iv_mean_5).replace([np.inf, -np.inf], 1.0).fillna(1.0)
        iv_mean_20 = df['iv'].rolling(20).mean()
        iv_std_20 = df['iv'].rolling(20).std().replace(0, np.nan)
        df['iv_z'] = ((df['iv'] - iv_mean_20) / iv_std_20).replace([np.inf, -np.inf], 0.0).fillna(0.0)

        # 2c. Skew dynamics (optional)
        if 'skew' in df.columns:
            skew_mean_20 = df['skew'].rolling(20).mean()
            skew_std_20 = df['skew'].rolling(20).std().replace(0, np.nan)
            df['skew_z'] = ((df['skew'] - skew_mean_20) / skew_std_20).replace([np.inf, -np.inf], 0.0).fillna(0.0)
            df['skew_change'] = (df['skew'] / df['skew'].shift(1)).replace([np.inf, -np.inf], 1.0).fillna(1.0)
        else:
            df['skew_z'] = 0.0
            df['skew_change'] = 1.0
        
        # 3. Volatility Premium (IV - Realized Vol)
        df['iv_rv_spread'] = df['iv'] - df['rv']
        
        # 4. Realized Vol Acceleration (change over last 5 days)
        df['rv_acceleration'] = df['rv'] / df['rv'].shift(5)
        df['rv_acceleration'] = df['rv_acceleration'].replace([np.inf, -np.inf], 1.0)
        rv_mean_20 = df['rv'].rolling(20).mean()
        rv_std_20 = df['rv'].rolling(20).std().replace(0, np.nan)
        df['rv_z'] = ((df['rv'] - rv_mean_20) / rv_std_20).replace([np.inf, -np.inf], 0.0).fillna(0.0)
        
        # 5. Average True Range (volatility measure)
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                np.abs(df['high'] - df['close'].shift(1)),
                np.abs(df['low'] - df['close'].shift(1))
            )
        )
        df['atr'] = df['tr'].rolling(14).mean()

        # 5b. ADX (trend strength)
        up_move = df['high'].diff()
        down_move = -df['low'].diff()
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
        plus_di = 100 * (pd.Series(plus_dm, index=df.index).rolling(14).mean() / df['atr'])
        minus_di = 100 * (pd.Series(minus_dm, index=df.index).rolling(14).mean() / df['atr'])
        dx = (np.abs(plus_di - minus_di) / (plus_di + minus_di)).replace([np.inf, -np.inf], np.nan) * 100
        df['adx'] = dx.rolling(14).mean().fillna(0.0)
        
        # 6. Daily IV change
        df['iv_change'] = df['iv'] / df['iv'].shift(1)
        df['iv_change'] = df['iv_change'].replace([np.inf, -np.inf], 1.0)
        
        return df
    
    def _is_data_quality_ok(self, df: pd.DataFrame) -> bool:
        """
        Check if data is fresh and complete enough for regime detection.
        
        Returns False if:
        - IV or RV data is stale (NaN/zero in last 5 bars)
        - Less than MIN_DATA_POINTS available
        - IV/RV values appear corrupted
        """
        if len(df) < self.MIN_DATA_POINTS:
            logger.warning(f"Insufficient data: {len(df)} bars < {self.MIN_DATA_POINTS}")
            return False
        
        # Check for stale/missing data in last 5 bars
        recent = df.tail(5)
        if recent['iv'].isna().any() or recent['rv'].isna().any():
            logger.warning("Missing IV or RV data in recent bars")
            return False
        
        if (recent['iv'] == 0).any() or (recent['rv'] == 0).any():
            logger.warning("Zero IV or RV in recent bars (data error)")
            return False
        
        # Check for extreme outliers (data corruption)
        if recent['iv'].max() > 2.0 or recent['rv'].max() > 2.0:
            logger.warning("Extreme IV/RV values detected—possible data corruption")
            return False
        
        return True
    
    def _classify_regime_candidate(self, df: pd.DataFrame) -> str:
        """
        Classify current market regime based on latest bar.
        
        This is the core regime detection logic. Returns a regime candidate
        that must be confirmed for N bars before becoming the active regime.
        """
        if len(df) < self.MIN_DATA_POINTS:
            return "NEUTRAL"
        
        latest = df.iloc[-1]
        
        # Fallback if indicators not calculated
        if pd.isna(latest.get('rv_acceleration', np.nan)):
            return "NEUTRAL"
        
        # Extract indicator values
        rv_accel = latest['rv_acceleration']
        price_dist = latest['price_dist_sma20']
        iv_rank = latest['iv_rank']
        iv_rv_spread = latest['iv_rv_spread']
        iv_change = latest['iv_change']
        sma_20 = latest['sma_20']
        sma_50 = latest['sma_50']
        close = latest['close']
        returns = latest.get('returns', 0.0)
        returns_3d = latest.get('returns_3d', 0.0)
        returns_5d = latest.get('returns_5d', 0.0)
        returns_60d = latest.get('returns_60d', 0.0)
        adx = latest.get('adx', 0.0)
        sma20_slope = latest.get('sma20_slope', 0.0)
        iv_accel = latest.get('iv_accel', 1.0)
        iv_z = latest.get('iv_z', 0.0)
        rv_z = latest.get('rv_z', 0.0)
        skew_z = latest.get('skew_z', 0.0)
        skew_change = latest.get('skew_change', 1.0)
        
        # Recovery override: V-bottom rebound despite high IV
        if returns_3d > 0.04 and returns_5d > 0.08 and iv_accel < 1.05 and price_dist > -0.05:
            return "TREND_UP"

        # --- CRASH_PANIC: Aggressive detection ---
        # Price significantly below SMA20 WITH stress signals
        crash_stress = (
            (returns_3d < -0.03 and iv_accel > 1.1 and rv_z > 0.5) or
            (price_dist < -0.06 and rv_z > 1.2) or
            (iv_z > 1.2 and rv_z > 0.7 and returns_5d < 0.02) or
            (iv_z > 1.8 and returns < -0.02) or
            (skew_z > 1.0 and skew_change > 1.05 and iv_accel > 1.05 and returns_3d < 0.01)
        )
        if crash_stress:
            return "CRASH_PANIC"

        # Recovery override: strong rebound after crash conditions
        if returns_5d > 0.10 and iv_accel < 1.05:
            return "TREND_UP"

        if returns_5d > 0.03 and price_dist > 0.02:
            return "TREND_UP"

        # --- BREAKOUT_EXPANSION: IV expanding + Strong directional move ---
        if (rv_z > 1.0 and abs(returns_5d) > 0.04) or (rv_z > 0.8 and abs(returns_3d) > 0.02) or (iv_accel > 1.08 and (abs(returns_5d) > 0.04 or abs(price_dist) > 0.012)):
            return "BREAKOUT_EXPANSION"

        # --- POST_EVENT_CRUSH: IV dropping sharply from elevated highs ---
        if iv_rank < 0.20 and iv_accel < 1.0 and abs(returns_5d) < 0.02:
            return "POST_EVENT_CRUSH"

        # --- MEAN_REVERSION: Low trend + low vol ---
        if iv_rank < 0.20 and abs(returns_5d) < 0.01:
            return "MEAN_REVERSION"

        if adx < 25 and abs(returns_5d) < 0.02 and abs(price_dist) < 0.02:
            return "MEAN_REVERSION"

        # --- TREND_UP / TREND_DOWN: Persistent moves (ADX) ---
        if adx > 18:
            if (returns_60d < -0.02 or (sma20_slope < -0.003 and returns_5d < -0.01)) and price_dist < 0.05:
                return "TREND_DOWN"
            if (returns_60d > 0.03 or sma20_slope > 0.003) and price_dist > -0.015:
                return "TREND_UP"
        
        # Default
        return "NEUTRAL"
    
    def detect_regime(self, df: pd.DataFrame) -> Tuple[str, bool, str]:
        """
        Detect current market regime with hysteresis (confirmation logic).
        
        This method tracks regime candidates and only flips the active regime
        when the candidate is stable for CONFIRMATION_BARS consecutive bars.
        Prevents flickering between regimes on noise.
        
        Args:
            df: DataFrame with OHLCV + iv, rv columns (already calculated indicators)
        
        Returns:
            Tuple of:
            - regime: Current active regime (or NEUTRAL if insufficient data)
            - is_regime_shift: Boolean flag if regime changed from previous
            - description: Human-readable explanation of regime
        """
        # Data quality gate
        if not self._is_data_quality_ok(df):
            logger.warning("Data quality check failed—defaulting to NEUTRAL")
            return "NEUTRAL", False, self.REGIME_DESCRIPTIONS["NEUTRAL"]
        
        # Classify candidate for this bar
        candidate = self._classify_regime_candidate(df)

        # V-bottom recovery override: fast reversal out of crash
        latest = df.iloc[-1]
        if (
            self.current_regime == "CRASH_PANIC"
            and candidate == "TREND_UP"
            and latest.get("returns_3d", 0.0) > 0.04
            and latest.get("returns_5d", 0.0) > 0.08
            and latest.get("iv_accel", 1.0) < 1.05
            and latest.get("price_dist_sma20", 0.0) > -0.05
        ):
            self.previous_regime = self.current_regime
            self.current_regime = "TREND_UP"
            self.regime_candidate = "TREND_UP"
            self.candidate_bar_count = self.confirmation_bars
            logger.info("✓ REGIME SHIFT: CRASH_PANIC → TREND_UP (V-bottom override)")
            description = self.REGIME_DESCRIPTIONS.get(
                self.current_regime,
                self.REGIME_DESCRIPTIONS["NEUTRAL"]
            )
            return self.current_regime, True, description
        
        is_regime_shift = False
        
        # Hysteresis override for crash panic
        confirmation_bars = 1 if candidate == "CRASH_PANIC" else self.confirmation_bars

        # Hysteresis logic: track candidate stability
        if candidate == self.regime_candidate:
            # Same candidate as previous bar—increment counter
            self.candidate_bar_count += 1
            
            # If confirmed (N bars stable), activate the regime
            if self.candidate_bar_count >= confirmation_bars:
                if candidate != self.current_regime:
                    self.previous_regime = self.current_regime
                    self.current_regime = candidate
                    is_regime_shift = True
                    logger.info(f"✓ REGIME SHIFT: {self.previous_regime} → {self.current_regime} "
                               f"(confirmed after {confirmation_bars} bars)")
        else:
            # Different candidate—reset counter
            self.regime_candidate = candidate
            self.candidate_bar_count = 1

            # Immediate shift for crash panic
            if candidate == "CRASH_PANIC" and self.current_regime != candidate:
                self.previous_regime = self.current_regime
                self.current_regime = candidate
                is_regime_shift = True
                logger.info(f"✓ REGIME SHIFT: {self.previous_regime} → {self.current_regime} "
                           "(immediate crash override)")

            logger.debug(f"Regime candidate changed to {candidate} (bar 1 of {confirmation_bars})")
        
        description = self.REGIME_DESCRIPTIONS.get(
            self.current_regime,
            self.REGIME_DESCRIPTIONS["NEUTRAL"]
        )
        
        return self.current_regime, is_regime_shift, description
    
    def get_regime_state(self) -> Dict:
        """
        Return current regime state for logging/diagnostics.
        
        Returns:
            Dict with:
            - current_regime: Active regime
            - previous_regime: Prior regime
            - regime_candidate: Candidate (not yet confirmed)
            - candidate_bar_count: Bars candidate has been stable
            - description: Human explanation
        """
        return {
            "current_regime": self.current_regime,
            "previous_regime": self.previous_regime,
            "regime_candidate": self.regime_candidate,
            "candidate_bar_count": self.candidate_bar_count,
            "description": self.REGIME_DESCRIPTIONS.get(
                self.current_regime,
                self.REGIME_DESCRIPTIONS["NEUTRAL"]
            ),
        }
    
    def reset_regime(self):
        """Reset internal state (useful for testing different symbols)."""
        self.previous_regime = None
        self.regime_candidate = None
        self.candidate_bar_count = 0
        self.current_regime = "NEUTRAL"


# --- Helper function for Alert Integration ---

def get_flight_manual_for_regime(regime: str) -> Dict[str, str]:
    """
    Return Flight Manual template hints for a given regime.
    
    This helps alert_notifications render context-appropriate user alerts.
    Maps each regime to a brief summary of:
    - What it means
    - Which strategies are active
    - Why traders should care
    
    Args:
        regime: Regime string (e.g., "CRASH_PANIC")
    
    Returns:
        Dict with 'summary' and 'action' keys
    """
    flight_manuals = {
        "CRASH_PANIC": {
            "summary": "Market in freefall—fear premium at peak",
            "active_strategies": ["Protective Puts", "Put Spreads"],
            "action": "🛡️ Hedging mode active—selling volatility is prohibited",
        },
        "TREND_UP": {
            "summary": "Sustained rally—bull market conditions",
            "active_strategies": ["Bull Spreads", "Covered Calls", "Long Calls"],
            "action": "📈 Directional bullish strategies have edge—buy dips",
        },
        "TREND_DOWN": {
            "summary": "Downtrend confirmed—bear market conditions",
            "active_strategies": ["Bear Spreads", "Short Calls", "Put Debit Spreads"],
            "action": "📉 Bearish strategies profitable—avoid long calls",
        },
        "BREAKOUT_EXPANSION": {
            "summary": "Volatility expanding—directional breakout forming",
            "active_strategies": ["Long Straddles", "Long Strangles", "Calendar Spreads"],
            "action": "💥 Long gamma strategies (options buyers) have edge—volatility will pay",
        },
        "MEAN_REVERSION": {
            "summary": "Choppy range-bound—premium selling optimal",
            "active_strategies": ["Iron Condors", "Short Strangles", "Credit Spreads"],
            "action": "🔄 Range-bound playbooks active—sell premium at range extremes",
        },
        "POST_EVENT_CRUSH": {
            "summary": "IV crush underway—volatility premium collapsing",
            "active_strategies": ["Iron Condors", "Short Strangles", "Credit Spreads"],
            "action": "💨 IV crush accelerating—short volatility strategies collect theta decay",
        },
        "NEUTRAL": {
            "summary": "No clear regime—fundamentals and fundamentals dominate",
            "active_strategies": [],
            "action": "⚖️ Use fundamental analysis—no regime edge available",
        },
    }
    
    return flight_manuals.get(
        regime,
        {
            "summary": "Unknown regime",
            "active_strategies": [],
            "action": "Check data quality"
        }
    )
