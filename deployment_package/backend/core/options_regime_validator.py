"""
RegimeDetector Validation Suite

Tests regime detection against 10 historical stress periods to ensure
classifications are reasonable and the detector isn't overfitting or lagging.

Historical test periods:
1. Feb 2020 - COVID crash (should → CRASH_PANIC)
2. Mar 2020 - Recovery rally (should → TREND_UP)
3. Apr 2020 - Continued rally (should → TREND_UP)
4. Mar 2022 - Fed rate hikes (should → TREND_DOWN)
5. Sep 2022 - Energy crisis (should → CRASH_PANIC)
6. Oct 2022 - Recovery (should → MEAN_REVERSION)
7. Jan 2023 - AI rally begins (should → BREAKOUT_EXPANSION)
8. Mar 2023 - SVB crisis (should → CRASH_PANIC)
9. Jun 2023 - Post-FOMC stability (should → POST_EVENT_CRUSH)
10. Nov 2023 - Pre-election (should → MEAN_REVERSION)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
import argparse
from datetime import timedelta

from .options_regime_detector import RegimeDetector

logger = logging.getLogger(__name__)

# Optional yfinance import for historical validation
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except Exception:
    YFINANCE_AVAILABLE = False


class RegimeDetectorValidator:
    """
    Validates RegimeDetector against historical market data and known outcomes.
    """
    
    # Historical periods with expected regime outcomes
    HISTORICAL_TEST_CASES = {
        "covid_crash_feb2020": {
            "period": ("2020-02-15", "2020-02-28"),
            "expected_regime": "CRASH_PANIC",
            "description": "COVID-19 market crash—fastest bear market ever"
        },
        "covid_recovery_mar2020": {
            "period": ("2020-03-20", "2020-03-31"),
            "expected_regime": "TREND_UP",
            "description": "V-shaped recovery bounce off COVID lows"
        },
        "fed_hiking_cycle_mar2022": {
            "period": ("2022-03-10", "2022-03-31"),
            "expected_regime": "TREND_DOWN",
            "description": "Fed rate hikes causing downtrend"
        },
        "uk_energy_crisis_sep2022": {
            "period": ("2022-09-15", "2022-09-30"),
            "expected_regime": "CRASH_PANIC",
            "description": "Energy crisis + pound collapse + volatility spike"
        },
        "recovery_oct2022": {
            "period": ("2022-10-10", "2022-10-31"),
            "expected_regime": "TREND_UP",
            "description": "Dead-cat bounce off Oct lows"
        },
        "ai_breakout_jan2023": {
            "period": ("2023-01-15", "2023-01-31"),
            "expected_regime": "BREAKOUT_EXPANSION",
            "description": "ChatGPT rally—breakout expansion with IV rising"
        },
        "svb_crisis_mar2023": {
            "period": ("2023-03-08", "2023-03-15"),
            "expected_regime": "CRASH_PANIC",
            "description": "SVB collapse—regional bank panic"
        },
        "post_fomc_jun2023": {
            "period": ("2023-06-15", "2023-06-30"),
            "expected_regime": "POST_EVENT_CRUSH",
            "description": "FOMC meeting done—IV crush underway"
        },
        "pre_election_nov2023": {
            "period": ("2023-11-01", "2023-11-30"),
            "expected_regime": "MEAN_REVERSION",
            "description": "Election-driven chop and sideways action"
        },
        "rate_expectations_aug2024": {
            "period": ("2024-08-01", "2024-08-15"),
            "expected_regime": "BREAKOUT_EXPANSION",
            "description": "Volatility spike from Jackson Hole speech expectations"
        },
    }
    
    def __init__(self):
        self.detector = RegimeDetector()
        self.test_results: List[Dict] = []
    
    def validate_on_historical_data(self, df: pd.DataFrame,
                                   expected_regime: str,
                                   eval_start: Optional[str] = None,
                                   eval_end: Optional[str] = None) -> Tuple[bool, Dict]:
        """
        Validate regime detection on a historical period.
        
        Args:
            df: DataFrame with OHLCV + iv, rv for a specific period
            expected_regime: What we expect the detector to classify
        
        Returns:
            Tuple of (is_correct, details)
        """
        # Calculate indicators
        df = self.detector.calculate_indicators(df)

        # Reset detector state for clean evaluation
        self.detector.reset_regime()

        # Run detector across the series to allow hysteresis to settle
        detected_regime = "NEUTRAL"
        description = self.detector.REGIME_DESCRIPTIONS["NEUTRAL"]
        regime_series: List[str] = []
        eval_start_dt = pd.to_datetime(eval_start) if eval_start else None
        eval_end_dt = pd.to_datetime(eval_end) if eval_end else None
        start_idx = max(self.detector.MIN_DATA_POINTS, 1)
        for i in range(start_idx, len(df) + 1):
            window_df = df.iloc[:i]
            detected_regime, _, description = self.detector.detect_regime(window_df)
            if eval_start_dt is None and eval_end_dt is None:
                regime_series.append(detected_regime)
            else:
                current_dt = window_df.index[-1]
                if ((eval_start_dt is None or current_dt >= eval_start_dt) and
                        (eval_end_dt is None or current_dt <= eval_end_dt)):
                    regime_series.append(detected_regime)

        # Use the most frequent regime in the last 5 bars (prefer non-neutral)
        if regime_series:
            recent_series = regime_series[-5:] if len(regime_series) >= 5 else regime_series
            counts = pd.Series(recent_series).value_counts()
            if len(counts) > 1 and "NEUTRAL" in counts.index:
                counts = counts.drop("NEUTRAL")
            detected_regime = counts.idxmax() if not counts.empty else "NEUTRAL"
        
        # Check correctness (exact match OR "close call")
        is_exact_match = detected_regime == expected_regime
        is_close_call = self._is_close_call(detected_regime, expected_regime)
        is_correct = is_exact_match or is_close_call
        
        result = {
            "expected": expected_regime,
            "detected": detected_regime,
            "exact_match": is_exact_match,
            "close_call": is_close_call,
            "correct": is_correct,
            "bars_analyzed": len(regime_series),
            "detector_state": self.detector.get_regime_state(),
        }
        
        return is_correct, result
    
    @staticmethod
    def _is_close_call(detected: str, expected: str) -> bool:
        """
        Define "close calls" where detection is not exact but reasonable.
        
        Examples:
        - Detected BREAKOUT_EXPANSION when expected TREND_UP (not wrong, just riskier)
        - Detected MEAN_REVERSION when expected NEUTRAL (conservative, acceptable)
        """
        close_call_pairs = [
            ("BREAKOUT_EXPANSION", "TREND_UP"),
            ("TREND_UP", "BREAKOUT_EXPANSION"),
            ("MEAN_REVERSION", "NEUTRAL"),
            ("NEUTRAL", "MEAN_REVERSION"),
            ("TREND_DOWN", "CRASH_PANIC"),
            ("POST_EVENT_CRUSH", "MEAN_REVERSION"),
        ]
        
        return (detected, expected) in close_call_pairs
    
    def generate_validation_report(self) -> Dict:
        """
        Generate a summary report of validation results.
        
        Returns:
            Dict with accuracy stats, failure analysis, recommendations
        """
        if not self.test_results:
            return {"error": "No test results available"}
        
        total = len(self.test_results)
        correct = sum(1 for r in self.test_results if r["correct"])
        exact_matches = sum(1 for r in self.test_results if r["exact_match"])
        close_calls = sum(1 for r in self.test_results if r["close_call"])
        failures = [r for r in self.test_results if not r["correct"]]
        
        accuracy = (correct / total * 100) if total > 0 else 0
        
        report = {
            "total_tests": total,
            "exact_matches": exact_matches,
            "close_calls": close_calls,
            "failures": len(failures),
            "overall_accuracy": f"{accuracy:.1f}%",
            "test_results": self.test_results,
        }
        
        # Analysis of failures
        if failures:
            report["failure_analysis"] = {
                "count": len(failures),
                "failures": [
                    {
                        "expected": f["expected"],
                        "detected": f["detected"],
                        "bars": f["bars_analyzed"],
                    }
                    for f in failures
                ],
                "recommendations": self._analyze_failure_patterns(failures),
            }
        
        return report

    @staticmethod
    def _analyze_failure_patterns(failures: List[Dict]) -> List[str]:
        """
        Analyze failure patterns and suggest improvements.
        """
        recommendations = []

        # Count failure types
        missed_crashes = sum(1 for f in failures if f["expected"] == "CRASH_PANIC")
        missed_trends = sum(1 for f in failures if "TREND" in f["expected"])
        false_positives = sum(1 for f in failures if f["detected"] != "NEUTRAL"
                             and f["expected"] == "NEUTRAL")

        if missed_crashes > 0:
            recommendations.append(
                f"⚠️  Missed {missed_crashes} crash detections—lower RV_SPIKE_THRESHOLD "
                "or add price acceleration as primary signal"
            )

        if missed_trends > 0:
            recommendations.append(
                f"⚠️  Missed {missed_trends} trend detections—verify SMA slope logic "
                "and price distance thresholds"
            )

        if false_positives > 0:
            recommendations.append(
                f"⚠️  {false_positives} false positives—regime candidates may need "
                "longer confirmation period (increase CONFIRMATION_BARS)"
            )

        if not recommendations:
            recommendations.append("✅ No systemic patterns detected—detector is performing well")

        return recommendations


def _compute_realized_volatility(close_prices: pd.Series, window: int = 20) -> pd.Series:
    """Compute rolling annualized realized volatility from close prices."""
    log_returns = np.log(close_prices / close_prices.shift(1))
    daily_vol = log_returns.rolling(window).std()
    return daily_vol * np.sqrt(252)


def fetch_historical_market_data(
    ticker: str,
    start_date: str,
    end_date: str,
    padding_days: int = 90
) -> Optional[pd.DataFrame]:
    """
    Fetch historical OHLCV data and attach IV/RV proxies.

    - Price data: {ticker}
    - IV proxy: VIX (converted to decimal)
    - RV: 20-day realized volatility
    """
    if not YFINANCE_AVAILABLE:
        logger.error("yfinance not available. Install with: pip install yfinance")
        return None

    start_dt = pd.to_datetime(start_date) - timedelta(days=padding_days)
    end_dt = pd.to_datetime(end_date)

    try:
        price = yf.Ticker(ticker).history(start=start_dt, end=end_dt, auto_adjust=True)
        vix = yf.Ticker("^VIX").history(start=start_dt, end=end_dt, auto_adjust=True)
        skew = yf.Ticker("^SKEW").history(start=start_dt, end=end_dt, auto_adjust=True)
    except Exception as e:
        logger.error(f"Failed to fetch historical data: {e}")
        return None

    if price.empty:
        logger.error(f"No price data returned for {ticker}")
        return None

    # Normalize index
    if price.index.tz is not None:
        price.index = price.index.tz_localize(None)
    if not vix.empty and vix.index.tz is not None:
        vix.index = vix.index.tz_localize(None)
    if not skew.empty and skew.index.tz is not None:
        skew.index = skew.index.tz_localize(None)

    # Build dataframe
    df = pd.DataFrame({
        "date": price.index,
        "open": price["Open"],
        "high": price["High"],
        "low": price["Low"],
        "close": price["Close"],
        "volume": price["Volume"],
    }).set_index("date")

    # IV proxy: VIX / 100 (if available), else fallback to rolling RV
    if not vix.empty and "Close" in vix.columns:
        iv = (vix["Close"] / 100.0).reindex(df.index).ffill()
    else:
        iv = pd.Series(index=df.index, dtype=float)

    # Skew proxy: CBOE SKEW / 100 (if available)
    if not skew.empty and "Close" in skew.columns:
        skew_series = (skew["Close"] / 100.0).reindex(df.index).ffill()
    else:
        skew_series = pd.Series(index=df.index, dtype=float)

    rv = _compute_realized_volatility(df["close"]).reindex(df.index)

    if iv.isna().all():
        iv = rv.copy()

    df["iv"] = iv.ffill().fillna(0.2)
    df["rv"] = rv.ffill().fillna(0.15)
    df["skew"] = skew_series.ffill().fillna(0.0)

    return df


def run_historical_stress_validation(ticker: str = "SPY") -> Dict:
    """Run regime detection against the 10 historical stress periods."""
    validator = RegimeDetectorValidator()

    for key, case in validator.HISTORICAL_TEST_CASES.items():
        start_date, end_date = case["period"]
        expected = case["expected_regime"]
        description = case["description"]

        logger.info(f"Testing {key}: {description} ({start_date} → {end_date})")
        df = fetch_historical_market_data(ticker, start_date, end_date)
        if df is None or df.empty:
            validator.test_results.append({
                "test_case": key,
                "expected": expected,
                "detected": "NO_DATA",
                "exact_match": False,
                "close_call": False,
                "correct": False,
                "bars_analyzed": 0,
                "detector_state": {},
            })
            continue

        # Use padding + target window to satisfy indicator history
        window_df = df.loc[:end_date].copy().tail(180)
        if window_df.empty:
            validator.test_results.append({
                "test_case": key,
                "expected": expected,
                "detected": "NO_DATA",
                "exact_match": False,
                "close_call": False,
                "correct": False,
                "bars_analyzed": 0,
                "detector_state": {},
            })
            continue

        is_correct, result = validator.validate_on_historical_data(
            window_df,
            expected_regime=expected,
            eval_start=start_date,
            eval_end=end_date
        )
        validator.test_results.append({
            "test_case": key,
            **result
        })

        logger.info(
            f"{key}: detected={result['detected']} expected={expected} "
            f"→ {'PASS' if is_correct else 'FAIL'}"
        )

    return validator.generate_validation_report()


# --- Helper function for external validation ---

def generate_mock_market_data(
    regime_type: str,
    num_days: int = 20,
    base_price: float = 100.0
) -> pd.DataFrame:
    """
    Generate mock OHLCV + IV/RV data for a given regime type.
    
    Useful for testing detector without historical data fetch.
    
    Args:
        regime_type: One of ["CRASH_PANIC", "TREND_UP", "TREND_DOWN", "MEAN_REVERSION", "BREAKOUT_EXPANSION", "POST_EVENT_CRUSH"]
        num_days: Number of days to generate
        base_price: Starting price
    
    Returns:
        DataFrame with realistic OHLCV + iv, rv
    """
    np.random.seed(42)  # Reproducible
    
    dates = pd.date_range(end=pd.Timestamp.now(), periods=num_days, freq='D')
    
    # Generate base price series with regime-appropriate characteristics
    if regime_type == "CRASH_PANIC":
        # Sharp downtrend + volatility spike
        returns = np.random.normal(-0.03, 0.08, num_days)  # Negative returns + high vol
        iv_series = np.linspace(0.20, 0.60, num_days)  # IV spiking
        rv_series = np.linspace(0.15, 0.50, num_days)  # RV spiking
    
    elif regime_type == "TREND_UP":
        # Steady uptrend + stable volatility
        returns = np.random.normal(0.01, 0.015, num_days)  # Positive returns + low vol
        iv_series = np.linspace(0.15, 0.12, num_days)  # IV declining
        rv_series = np.linspace(0.10, 0.12, num_days)  # RV stable/low
    
    elif regime_type == "TREND_DOWN":
        # Steady downtrend
        returns = np.random.normal(-0.01, 0.015, num_days)  # Negative returns + low vol
        iv_series = np.linspace(0.12, 0.20, num_days)  # IV rising slightly
        rv_series = np.linspace(0.10, 0.18, num_days)  # RV rising
    
    elif regime_type == "MEAN_REVERSION":
        # Choppy oscillation around mean
        returns = np.random.normal(0, 0.012, num_days)
        iv_series = np.ones(num_days) * 0.25  # Elevated IV
        rv_series = np.ones(num_days) * 0.15  # Lower than IV (premium)
    
    elif regime_type == "BREAKOUT_EXPANSION":
        # IV expanding + directional move
        returns = np.random.normal(0.02, 0.025, num_days)
        iv_series = np.linspace(0.15, 0.35, num_days)  # IV sharply rising
        rv_series = np.linspace(0.12, 0.30, num_days)  # RV rising
    
    elif regime_type == "POST_EVENT_CRUSH":
        # IV declining from elevated + stable prices
        returns = np.random.normal(0, 0.008, num_days)
        iv_series = np.linspace(0.35, 0.18, num_days)  # IV declining
        rv_series = np.ones(num_days) * 0.15  # RV stable
    
    else:
        # NEUTRAL
        returns = np.random.normal(0, 0.012, num_days)
        iv_series = np.ones(num_days) * 0.18
        rv_series = np.ones(num_days) * 0.12
    
    # Generate price series
    prices = np.exp(np.cumsum(returns)) * base_price
    
    # Generate OHLCV (simplified)
    df = pd.DataFrame({
        "date": dates,
        "close": prices,
        "open": prices * (1 + np.random.normal(0, 0.003, num_days)),
        "high": prices * (1 + np.abs(np.random.normal(0, 0.015, num_days))),
        "low": prices * (1 - np.abs(np.random.normal(0, 0.015, num_days))),
        "volume": np.random.randint(1000000, 10000000, num_days),
        "iv": iv_series,
        "rv": rv_series,
    })
    
    return df


# --- Example usage ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RegimeDetector validation suite")
    parser.add_argument("--historical", action="store_true", help="Run historical stress-period validation")
    parser.add_argument("--ticker", default="SPY", help="Ticker to validate (default: SPY)")
    args = parser.parse_args()

    if args.historical:
        report = run_historical_stress_validation(ticker=args.ticker)
        print("\n📋 HISTORICAL VALIDATION REPORT:")
        print(f"  Accuracy: {report['overall_accuracy']}")
        print(f"  Exact matches: {report['exact_matches']} / {report['total_tests']}")
        print(f"  Close calls: {report['close_calls']} / {report['total_tests']}")
        print(f"  Failures: {report['failures']} / {report['total_tests']}")

        if "failure_analysis" in report:
            print("\n⚠️  FAILURE ANALYSIS:")
            for rec in report["failure_analysis"]["recommendations"]:
                print(f"  {rec}")
    else:
        # Example: Test detector on mock data
        validator = RegimeDetectorValidator()

        for regime_type in ["CRASH_PANIC", "TREND_UP", "MEAN_REVERSION"]:
            print(f"\n📊 Testing {regime_type}...")
            df = generate_mock_market_data(regime_type, num_days=30)

            is_correct, result = validator.validate_on_historical_data(
                df,
                expected_regime=regime_type
            )

            validator.test_results.append({
                "test_case": regime_type,
                **result
            })

            print(f"  Detected: {result['detected']} (expected: {result['expected']})")
            print(f"  Result: {'✅ PASS' if is_correct else '❌ FAIL'}")

        # Print report
        report = validator.generate_validation_report()
        print("\n📋 VALIDATION REPORT:")
        print(f"  Accuracy: {report['overall_accuracy']}")
        print(f"  Exact matches: {report['exact_matches']} / {report['total_tests']}")
        print(f"  Close calls: {report['close_calls']} / {report['total_tests']}")

        if "failure_analysis" in report:
            print("\n⚠️  FAILURE ANALYSIS:")
            for rec in report["failure_analysis"]["recommendations"]:
                print(f"  {rec}")
