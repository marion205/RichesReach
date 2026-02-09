"""
Unit Tests for FSS Robustness Metrics (Regime Robustness & SSR)

Tests edge cases and statistical safeguards:
- Empty data
- Near-zero IC
- Negative IC
- Small samples
- Single regime
- Perfectly flat signals
- Sign flips
- Low coverage
- NaN forward returns
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from core.fss_engine import FSSEngine, get_fss_engine

# Also support pytest-style tests
try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False


class TestRegimeRobustness(unittest.TestCase):
    """Test Regime Robustness Score edge cases"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = get_fss_engine()
        
        # Create base dates
        self.base_date = datetime(2024, 1, 1)
        self.dates = pd.date_range(self.base_date, periods=300, freq='D')
        
    def create_fss_data(self, ticker: str, values: list) -> pd.DataFrame:
        """Helper to create FSS data DataFrame"""
        multi_index = pd.MultiIndex.from_tuples([("FSS", ticker)])
        return pd.DataFrame(
            {("FSS", ticker): values},
            index=self.dates[:len(values)]
        )
    
    def create_prices(self, ticker: str, values: list) -> pd.DataFrame:
        """Helper to create prices DataFrame"""
        return pd.DataFrame(
            {ticker: values},
            index=self.dates[:len(values)]
        )
    
    def create_spy(self, regimes: list) -> pd.Series:
        """Helper to create SPY series with regimes"""
        # Create SPY prices that reflect regimes
        spy_values = []
        for regime in regimes:
            if regime == "Expansion":
                spy_values.append(100 + len(spy_values) * 0.1)  # Upward trend
            elif regime == "Crisis":
                spy_values.append(100 - len(spy_values) * 0.15)  # Downward trend
            elif regime == "Parabolic":
                spy_values.append(100 + len(spy_values) * 0.2)  # Strong upward
            else:  # Deflation
                spy_values.append(100 - len(spy_values) * 0.05)  # Slow decline
        
        return pd.Series(spy_values, index=self.dates[:len(regimes)])
    
    def test_empty_data(self):
        """Test: Empty data should return 0.5 (neutral)"""
        fss_data = self.create_fss_data("AAPL", [])
        prices = self.create_prices("AAPL", [])
        spy = pd.Series([], dtype=float)
        
        result = self.engine.calculate_regime_robustness(
            "AAPL", fss_data, prices, spy
        )
        
        self.assertEqual(result, 0.5, "Empty data should return 0.5")
    
    def test_insufficient_data(self):
        """Test: Less than 60 days should return 0.5"""
        fss_data = self.create_fss_data("AAPL", [50.0] * 30)
        prices = self.create_prices("AAPL", [100.0] * 30)
        spy = self.create_spy(["Expansion"] * 30)
        
        result = self.engine.calculate_regime_robustness(
            "AAPL", fss_data, prices, spy
        )
        
        self.assertEqual(result, 0.5, "Insufficient data should return 0.5")
    
    def test_single_regime(self):
        """Test: Single regime should return 0.5 (can't assess robustness)"""
        n = 100
        fss_data = self.create_fss_data("AAPL", [50.0] * n)
        prices = self.create_prices("AAPL", [100.0] * n)
        spy = self.create_spy(["Expansion"] * n)
        
        result = self.engine.calculate_regime_robustness(
            "AAPL", fss_data, prices, spy
        )
        
        self.assertEqual(result, 0.5, "Single regime should return 0.5")
    
    def test_negative_ic(self):
        """Test: Negative mean IC should return 0.0 (only positive alpha)"""
        n = 150
        # Create data where FSS is negatively correlated with returns
        fss_scores = np.linspace(80, 20, n)  # High to low
        returns = np.linspace(0.1, -0.1, n)  # Positive to negative (opposite)
        prices = [100.0]
        for ret in returns[:-1]:
            prices.append(prices[-1] * (1 + ret))
        
        fss_data = self.create_fss_data("AAPL", fss_scores.tolist())
        prices_df = self.create_prices("AAPL", prices)
        # Create two regimes
        regimes = ["Expansion"] * (n//2) + ["Crisis"] * (n - n//2)
        spy = self.create_spy(regimes)
        
        result = self.engine.calculate_regime_robustness(
            "AAPL", fss_data, prices_df, spy
        )
        
        self.assertEqual(result, 0.0, "Negative IC should return 0.0")
    
    def test_near_zero_ic(self):
        """Test: Near-zero IC should not cause CV explosion"""
        n = 150
        # Create data with near-zero correlation
        np.random.seed(42)
        fss_scores = np.random.normal(50, 5, n)
        returns = np.random.normal(0.001, 0.01, n)  # Random, uncorrelated
        prices = [100.0]
        for ret in returns[:-1]:
            prices.append(prices[-1] * (1 + ret))
        
        fss_data = self.create_fss_data("AAPL", fss_scores.tolist())
        prices_df = self.create_prices("AAPL", prices)
        regimes = ["Expansion"] * (n//2) + ["Crisis"] * (n - n//2)
        spy = self.create_spy(regimes)
        
        result = self.engine.calculate_regime_robustness(
            "AAPL", fss_data, prices_df, spy
        )
        
        # Should return 0.0 (mean IC <= 0) or a bounded value, not NaN/Inf
        self.assertFalse(np.isnan(result), "Result should not be NaN")
        self.assertFalse(np.isinf(result), "Result should not be Inf")
        self.assertGreaterEqual(result, 0.0, "Result should be >= 0")
        self.assertLessEqual(result, 1.0, "Result should be <= 1")
    
    def test_small_samples_per_regime(self):
        """Test: Small samples should be handled with shrinkage"""
        n = 100
        # Create data with very few samples per regime
        fss_scores = np.linspace(50, 70, n)
        returns = np.linspace(0.01, 0.02, n)  # Positive correlation
        prices = [100.0]
        for ret in returns[:-1]:
            prices.append(prices[-1] * (1 + ret))
        
        fss_data = self.create_fss_data("AAPL", fss_scores.tolist())
        prices_df = self.create_prices("AAPL", prices)
        # Create many regimes with few samples each
        regimes = []
        for i in range(10):
            regimes.extend([f"Regime{i}"] * 10)
        spy = self.create_spy(regimes)
        
        result = self.engine.calculate_regime_robustness(
            "AAPL", fss_data, prices_df, spy,
            min_samples_per_regime=30  # Higher threshold
        )
        
        # Should handle gracefully (may return 0.5 if no regimes meet threshold)
        self.assertFalse(np.isnan(result), "Result should not be NaN")
        self.assertGreaterEqual(result, 0.0, "Result should be >= 0")
        self.assertLessEqual(result, 1.0, "Result should be <= 1")
    
    def test_perfectly_flat_signal(self):
        """Test: Perfectly flat FSS (zero variance) should not crash"""
        n = 150
        fss_scores = [50.0] * n  # Perfectly flat
        returns = np.random.normal(0.001, 0.01, n)
        prices = [100.0]
        for ret in returns[:-1]:
            prices.append(prices[-1] * (1 + ret))
        
        fss_data = self.create_fss_data("AAPL", fss_scores)
        prices_df = self.create_prices("AAPL", prices)
        regimes = ["Expansion"] * (n//2) + ["Crisis"] * (n - n//2)
        spy = self.create_spy(regimes)
        
        result = self.engine.calculate_regime_robustness(
            "AAPL", fss_data, prices_df, spy
        )
        
        # Should handle gracefully (correlation will be NaN, should skip)
        self.assertFalse(np.isnan(result), "Result should not be NaN")
        self.assertGreaterEqual(result, 0.0, "Result should be >= 0")
        self.assertLessEqual(result, 1.0, "Result should be <= 1")
    
    def test_positive_robustness(self):
        """Test: Positive IC across regimes should yield positive robustness"""
        n = 200
        # Create data with positive correlation
        np.random.seed(42)
        base_fss = np.linspace(40, 60, n)
        fss_scores = base_fss + np.random.normal(0, 2, n)
        # Returns positively correlated with FSS
        returns = (fss_scores - 50) / 100 + np.random.normal(0, 0.005, n)
        prices = [100.0]
        for ret in returns[:-1]:
            prices.append(prices[-1] * (1 + ret))
        
        fss_data = self.create_fss_data("AAPL", fss_scores.tolist())
        prices_df = self.create_prices("AAPL", prices)
        # Two regimes with sufficient samples
        regimes = ["Expansion"] * 100 + ["Crisis"] * 100
        spy = self.create_spy(regimes)
        
        result = self.engine.calculate_regime_robustness(
            "AAPL", fss_data, prices_df, spy
        )
        
        # Should be positive and bounded
        self.assertGreater(result, 0.0, "Positive IC should yield positive robustness")
        self.assertLessEqual(result, 1.0, "Result should be <= 1")


class TestSignalStabilityRating(unittest.TestCase):
    """Test Signal Stability Rating (SSR) edge cases"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = get_fss_engine()
        self.base_date = datetime(2024, 1, 1)
        self.dates = pd.date_range(self.base_date, periods=300, freq='D')
        
    def create_fss_data(self, ticker: str, values: list) -> pd.DataFrame:
        """Helper to create FSS data DataFrame"""
        return pd.DataFrame(
            {("FSS", ticker): values},
            index=self.dates[:len(values)]
        )
    
    def create_prices(self, ticker: str, values: list) -> pd.DataFrame:
        """Helper to create prices DataFrame"""
        return pd.DataFrame(
            {ticker: values},
            index=self.dates[:len(values)]
        )
    
    def test_empty_data(self):
        """Test: Empty data should return 0.5"""
        fss_data = self.create_fss_data("AAPL", [])
        prices = self.create_prices("AAPL", [])
        
        result = self.engine.calculate_signal_stability_rating(
            "AAPL", fss_data, prices
        )
        
        self.assertEqual(result, 0.5, "Empty data should return 0.5")
    
    def test_insufficient_data(self):
        """Test: Less than 60 days should return 0.5"""
        fss_data = self.create_fss_data("AAPL", [50.0] * 30)
        prices = self.create_prices("AAPL", [100.0] * 30)
        
        result = self.engine.calculate_signal_stability_rating(
            "AAPL", fss_data, prices
        )
        
        self.assertEqual(result, 0.5, "Insufficient data should return 0.5")
    
    def test_low_coverage_penalty(self):
        """Test: Short history should be penalized (coverage < 1)"""
        n = 60  # Less than target_n (100)
        fss_scores = np.linspace(50, 60, n)
        returns = np.linspace(0.01, 0.02, n)
        prices = [100.0]
        for ret in returns[:-1]:
            prices.append(prices[-1] * (1 + ret))
        
        fss_data = self.create_fss_data("AAPL", fss_scores.tolist())
        prices_df = self.create_prices("AAPL", prices)
        
        result = self.engine.calculate_signal_stability_rating(
            "AAPL", fss_data, prices_df,
            target_n=100  # Higher target
        )
        
        # Should be penalized (lower than if coverage was 1.0)
        self.assertGreaterEqual(result, 0.0, "Result should be >= 0")
        self.assertLessEqual(result, 1.0, "Result should be <= 1")
        # Coverage penalty should apply
        self.assertLess(result, 1.0, "Low coverage should penalize SSR")
    
    def test_sign_flip_penalty(self):
        """Test: Sign flips in IC should reduce SSR"""
        n = 150
        # Create data where IC alternates sign
        np.random.seed(42)
        fss_scores = []
        returns = []
        
        for i in range(n):
            if i % 20 < 10:
                # Positive correlation period
                fss_scores.append(50 + i % 10)
                returns.append(0.01 + (i % 10) * 0.001)
            else:
                # Negative correlation period (flip)
                fss_scores.append(50 + i % 10)
                returns.append(-0.01 - (i % 10) * 0.001)
        
        prices = [100.0]
        for ret in returns[:-1]:
            prices.append(prices[-1] * (1 + ret))
        
        fss_data = self.create_fss_data("AAPL", fss_scores)
        prices_df = self.create_prices("AAPL", prices)
        
        result_with_flips = self.engine.calculate_signal_stability_rating(
            "AAPL", fss_data, prices_df
        )
        
        # Create stable version (no flips)
        fss_stable = np.linspace(50, 60, n)
        returns_stable = np.linspace(0.01, 0.02, n)  # Always positive
        prices_stable = [100.0]
        for ret in returns_stable[:-1]:
            prices_stable.append(prices_stable[-1] * (1 + ret))
        
        fss_data_stable = self.create_fss_data("AAPL", fss_stable.tolist())
        prices_df_stable = self.create_prices("AAPL", prices_stable)
        
        result_stable = self.engine.calculate_signal_stability_rating(
            "AAPL", fss_data_stable, prices_df_stable
        )
        
        # Stable version should be higher (or equal)
        self.assertGreaterEqual(result_stable, result_with_flips,
                               "Stable signal should have higher SSR than flipping signal")
    
    def test_persistence_calculation(self):
        """Test: Persistence should measure autocorrelation"""
        n = 150
        # Create highly persistent signal (trending)
        fss_scores = np.linspace(40, 70, n)  # Strong trend
        returns = np.linspace(0.01, 0.02, n)
        prices = [100.0]
        for ret in returns[:-1]:
            prices.append(prices[-1] * (1 + ret))
        
        fss_data = self.create_fss_data("AAPL", fss_scores.tolist())
        prices_df = self.create_prices("AAPL", prices)
        
        result_persistent = self.engine.calculate_signal_stability_rating(
            "AAPL", fss_data, prices_df
        )
        
        # Create non-persistent signal (random)
        np.random.seed(42)
        fss_random = np.random.normal(50, 5, n)
        returns_random = np.random.normal(0.001, 0.01, n)
        prices_random = [100.0]
        for ret in returns_random[:-1]:
            prices_random.append(prices_random[-1] * (1 + ret))
        
        fss_data_random = self.create_fss_data("AAPL", fss_random.tolist())
        prices_df_random = self.create_prices("AAPL", prices_random)
        
        result_random = self.engine.calculate_signal_stability_rating(
            "AAPL", fss_data_random, prices_df_random
        )
        
        # Persistent signal should have higher SSR
        self.assertGreater(result_persistent, result_random,
                          "Persistent signal should have higher SSR")
    
    def test_snr_calculation(self):
        """Test: Signal-to-noise ratio should measure reliability"""
        n = 150
        # High SNR: consistent IC
        np.random.seed(42)
        fss_high_snr = np.linspace(40, 60, n) + np.random.normal(0, 1, n)
        returns_high_snr = (fss_high_snr - 50) / 100 + np.random.normal(0, 0.002, n)
        prices_high_snr = [100.0]
        for ret in returns_high_snr[:-1]:
            prices_high_snr.append(prices_high_snr[-1] * (1 + ret))
        
        fss_data_high_snr = self.create_fss_data("AAPL", fss_high_snr.tolist())
        prices_df_high_snr = self.create_prices("AAPL", prices_high_snr)
        
        result_high_snr = self.engine.calculate_signal_stability_rating(
            "AAPL", fss_data_high_snr, prices_df_high_snr
        )
        
        # Low SNR: noisy IC
        fss_low_snr = np.random.normal(50, 10, n)  # High variance
        returns_low_snr = np.random.normal(0.001, 0.02, n)  # Uncorrelated, high noise
        prices_low_snr = [100.0]
        for ret in returns_low_snr[:-1]:
            prices_low_snr.append(prices_low_snr[-1] * (1 + ret))
        
        fss_data_low_snr = self.create_fss_data("AAPL", fss_low_snr.tolist())
        prices_df_low_snr = self.create_prices("AAPL", prices_low_snr)
        
        result_low_snr = self.engine.calculate_signal_stability_rating(
            "AAPL", fss_data_low_snr, prices_df_low_snr
        )
        
        # High SNR should have higher SSR
        self.assertGreater(result_high_snr, result_low_snr,
                          "High SNR signal should have higher SSR")
    
    def test_perfectly_flat_signal(self):
        """Test: Perfectly flat FSS should not crash"""
        n = 150
        fss_scores = [50.0] * n
        returns = np.random.normal(0.001, 0.01, n)
        prices = [100.0]
        for ret in returns[:-1]:
            prices.append(prices[-1] * (1 + ret))
        
        fss_data = self.create_fss_data("AAPL", fss_scores)
        prices_df = self.create_prices("AAPL", prices)
        
        result = self.engine.calculate_signal_stability_rating(
            "AAPL", fss_data, prices_df
        )
        
        # Should handle gracefully
        self.assertFalse(np.isnan(result), "Result should not be NaN")
        self.assertGreaterEqual(result, 0.0, "Result should be >= 0")
        self.assertLessEqual(result, 1.0, "Result should be <= 1")
    
    def test_bounded_output(self):
        """Test: SSR should always be bounded [0, 1]"""
        n = 200
        # Test with various scenarios
        test_cases = [
            ("trending", np.linspace(40, 70, n), np.linspace(0.01, 0.02, n)),
            ("volatile", np.random.normal(50, 15, n), np.random.normal(0.001, 0.02, n)),
            ("stable", np.random.normal(50, 2, n), np.random.normal(0.001, 0.005, n)),
        ]
        
        for name, fss_vals, ret_vals in test_cases:
            prices = [100.0]
            for ret in ret_vals[:-1]:
                prices.append(prices[-1] * (1 + ret))
            
            fss_data = self.create_fss_data("AAPL", fss_vals.tolist())
            prices_df = self.create_prices("AAPL", prices)
            
            result = self.engine.calculate_signal_stability_rating(
                "AAPL", fss_data, prices_df
            )
            
            self.assertGreaterEqual(result, 0.0,
                                  f"{name} case: Result should be >= 0")
            self.assertLessEqual(result, 1.0,
                               f"{name} case: Result should be <= 1")
            self.assertFalse(np.isnan(result),
                           f"{name} case: Result should not be NaN")
            self.assertFalse(np.isinf(result),
                           f"{name} case: Result should not be Inf")


class TestIntegration(unittest.TestCase):
    """Integration tests for both metrics together"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = get_fss_engine()
        self.base_date = datetime(2024, 1, 1)
        self.dates = pd.date_range(self.base_date, periods=300, freq='D')
        
    def create_fss_data(self, ticker: str, values: list) -> pd.DataFrame:
        """Helper to create FSS data DataFrame"""
        return pd.DataFrame(
            {("FSS", ticker): values},
            index=self.dates[:len(values)]
        )
    
    def create_prices(self, ticker: str, values: list) -> pd.DataFrame:
        """Helper to create prices DataFrame"""
        return pd.DataFrame(
            {ticker: values},
            index=self.dates[:len(values)]
        )
    
    def create_spy(self, regimes: list) -> pd.Series:
        """Helper to create SPY series"""
        spy_values = []
        for regime in regimes:
            if regime == "Expansion":
                spy_values.append(100 + len(spy_values) * 0.1)
            elif regime == "Crisis":
                spy_values.append(100 - len(spy_values) * 0.15)
            else:
                spy_values.append(100 + len(spy_values) * 0.05)
        return pd.Series(spy_values, index=self.dates[:len(regimes)])
    
    def test_both_metrics_realistic_scenario(self):
        """Test: Both metrics should work together in realistic scenario"""
        n = 200
        np.random.seed(42)
        
        # Create realistic data
        fss_scores = np.linspace(45, 65, n) + np.random.normal(0, 3, n)
        returns = (fss_scores - 50) / 200 + np.random.normal(0, 0.005, n)
        prices = [100.0]
        for ret in returns[:-1]:
            prices.append(prices[-1] * (1 + ret))
        
        fss_data = self.create_fss_data("AAPL", fss_scores.tolist())
        prices_df = self.create_prices("AAPL", prices)
        regimes = ["Expansion"] * 100 + ["Crisis"] * 100
        spy = self.create_spy(regimes)
        
        # Calculate both metrics
        robustness = self.engine.calculate_regime_robustness(
            "AAPL", fss_data, prices_df, spy
        )
        ssr = self.engine.calculate_signal_stability_rating(
            "AAPL", fss_data, prices_df
        )
        
        # Both should be bounded and valid
        self.assertGreaterEqual(robustness, 0.0)
        self.assertLessEqual(robustness, 1.0)
        self.assertFalse(np.isnan(robustness))
        self.assertFalse(np.isinf(robustness))
        
        self.assertGreaterEqual(ssr, 0.0)
        self.assertLessEqual(ssr, 1.0)
        self.assertFalse(np.isnan(ssr))
        self.assertFalse(np.isinf(ssr))


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)

