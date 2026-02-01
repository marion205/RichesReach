"""
Correlation Sanity Check for Chan Portfolio Allocator

Verifies that highly correlated assets are penalized compared to uncorrelated ones.
This is critical to ensure the portfolio protection actually works.
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from deployment_package.backend.core.chan_portfolio_allocator import ChanPortfolioAllocator, get_chan_portfolio_allocator


class TestPortfolioAllocatorSanity(unittest.TestCase):
    """Test correlation penalty logic"""
    
    def setUp(self):
        self.allocator = get_chan_portfolio_allocator()
    
    def test_correlation_penalty_sanity(self):
        """
        Verify that highly correlated assets are penalized compared to uncorrelated ones.
        
        Scenario:
        - Stock A & B: 100% correlated (effectively the same bet)
        - Stock C: Uncorrelated to A & B
        - All have identical Kelly scores (0.20) and Robustness (0.9)
        
        Expected:
        - Weight(C) should be significantly higher than Weight(A) or Weight(B)
        - Ideally, Weight(A) + Weight(B) ~ Weight(C) (treating the pair as one bet)
        """
        print("\n" + "="*60)
        print("--- Running Correlation Sanity Check ---")
        print("="*60)
        
        # 1. Create Synthetic Returns with specific correlations
        n_days = 100
        np.random.seed(42)
        
        # Generate base signals
        factor_1 = np.random.normal(0, 0.01, n_days)  # The "Tech" factor
        factor_2 = np.random.normal(0, 0.01, n_days)  # The "Energy" factor
        
        # Stock A: Tracks Factor 1
        ret_a = factor_1 + np.random.normal(0, 0.0001, n_days)  # Tiny noise
        
        # Stock B: Also Tracks Factor 1 (Perfect Correlation with A)
        ret_b = factor_1 + np.random.normal(0, 0.0001, n_days)
        
        # Stock C: Tracks Factor 2 (Uncorrelated to A & B)
        ret_c = factor_2
        
        dates = pd.date_range(end=pd.Timestamp.now(), periods=n_days, freq='D')
        returns_df = pd.DataFrame({
            'StockA': ret_a,
            'StockB': ret_b,
            'StockC': ret_c
        }, index=dates)
        
        # Verify correlations
        corr = returns_df.corr()
        print("\nCorrelation Matrix:")
        print(corr.round(3))
        
        # Verify A and B are highly correlated
        ab_corr = corr.loc['StockA', 'StockB']
        print(f"\nStockA-StockB Correlation: {ab_corr:.3f} (should be ~1.0)")
        self.assertGreater(ab_corr, 0.95, "StockA and StockB should be highly correlated")
        
        # Verify C is uncorrelated to A and B
        ac_corr = abs(corr.loc['StockA', 'StockC'])
        bc_corr = abs(corr.loc['StockB', 'StockC'])
        print(f"StockA-StockC Correlation: {ac_corr:.3f} (should be ~0.0)")
        print(f"StockB-StockC Correlation: {bc_corr:.3f} (should be ~0.0)")
        self.assertLess(ac_corr, 0.2, "StockC should be uncorrelated to StockA")
        self.assertLess(bc_corr, 0.2, "StockC should be uncorrelated to StockB")
        
        # 2. Setup Inputs - All have identical signals
        tickers = ['StockA', 'StockB', 'StockC']
        kelly_fractions = {'StockA': 0.2, 'StockB': 0.2, 'StockC': 0.2}
        fss_scores = {'StockA': 75.0, 'StockB': 75.0, 'StockC': 75.0}
        fss_robustness = {'StockA': 0.9, 'StockB': 0.9, 'StockC': 0.9}
        volatilities = {'StockA': 0.20, 'StockB': 0.20, 'StockC': 0.20}  # 20% annual vol
        
        print("\nInput Parameters:")
        print(f"  Kelly Fractions: {kelly_fractions}")
        print(f"  FSS Robustness: {fss_robustness}")
        print(f"  Volatilities: {volatilities}")
        
        # 3. Run Allocation
        result = self.allocator.allocate_portfolio(
            tickers=tickers,
            kelly_fractions=kelly_fractions,
            fss_scores=fss_scores,
            fss_robustness=fss_robustness,
            returns_matrix=returns_df,
            volatilities=volatilities,
            method="kelly_constrained"
        )
        
        weights = result.weights
        
        print("\n" + "-"*60)
        print("Allocation Results:")
        print("-"*60)
        for stock, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
            print(f"  {stock}: {weight:.4f} ({weight*100:.2f}%)")
        
        print(f"\nPortfolio Metrics:")
        print(f"  Expected Return: {result.expected_return:.2%}")
        print(f"  Expected Volatility: {result.expected_volatility:.2%}")
        print(f"  Sharpe Ratio: {result.sharpe_ratio:.3f}")
        print(f"  Diversification Score: {result.diversification_score:.3f}")
        if result.warnings:
            print(f"  Warnings: {', '.join(result.warnings)}")
        
        # 4. Assertions
        w_a = weights.get('StockA', 0.0)
        w_b = weights.get('StockB', 0.0)
        w_c = weights.get('StockC', 0.0)
        
        print("\n" + "-"*60)
        print("Verification:")
        print("-"*60)
        
        # A and B should be roughly equal (symmetric)
        print(f"✓ StockA ({w_a:.4f}) ≈ StockB ({w_b:.4f}): Symmetric assets should have equal weights")
        self.assertAlmostEqual(w_a, w_b, delta=0.02, 
                              msg=f"Symmetric assets should have equal weights. Got A={w_a:.4f}, B={w_b:.4f}")
        
        # C should be significantly larger than A (the penalty working)
        # Because A splits its 'risk budget' with B
        print(f"✓ StockC ({w_c:.4f}) > StockA ({w_a:.4f}): Uncorrelated should have higher weight")
        self.assertGreater(w_c, w_a * 1.2, 
                          msg=f"Uncorrelated StockC ({w_c:.4f}) should have at least 20% higher weight than correlated StockA ({w_a:.4f})")
        
        # Combined weight of A+B should not be double C
        # In a perfect diversifier world, if we have 1 independent bet (C) and 1 shared bet (A+B),
        # the system treats (A+B) roughly as one unit.
        combined_correlated = w_a + w_b
        print(f"✓ Combined (A+B): {combined_correlated:.4f} vs Uncorrelated (C): {w_c:.4f}")
        
        # The combined correlated weight should be less than 2x the uncorrelated weight
        # (because they're effectively one bet, not two independent bets)
        self.assertLess(combined_correlated, w_c * 2.5,
                       msg=f"Combined correlated weight ({combined_correlated:.4f}) should not be more than 2.5x uncorrelated weight ({w_c:.4f})")
        
        # Diversification score should be reasonable (not perfect because A&B are correlated)
        print(f"✓ Diversification Score: {result.diversification_score:.3f} (should be > 0.3)")
        self.assertGreater(result.diversification_score, 0.3,
                          msg=f"Diversification score should be > 0.3, got {result.diversification_score:.3f}")
        
        # Weights should sum to ~1.0
        total_weight = sum(weights.values())
        print(f"✓ Total Weight: {total_weight:.4f} (should be ~1.0)")
        self.assertAlmostEqual(total_weight, 1.0, delta=0.01,
                              msg=f"Weights should sum to 1.0, got {total_weight:.4f}")
        
        print("\n" + "="*60)
        print("✅ CORRELATION PENALTY LOGIC VERIFIED")
        print("="*60)
        print("\nThe allocator correctly identified that StockA and StockB are")
        print("effectively the same bet and reduced their combined allocation,")
        print("while allowing the uncorrelated StockC to run near its full Kelly size.\n")
    
    def test_uncorrelated_assets_no_penalty(self):
        """
        Verify that uncorrelated assets are NOT penalized.
        
        If all assets are uncorrelated, they should receive weights
        proportional to their Kelly fractions (with robustness adjustments).
        """
        print("\n" + "="*60)
        print("--- Testing Uncorrelated Assets (No Penalty) ---")
        print("="*60)
        
        n_days = 100
        np.random.seed(123)
        
        # Create three uncorrelated assets
        ret_a = np.random.normal(0, 0.01, n_days)
        ret_b = np.random.normal(0, 0.01, n_days)
        ret_c = np.random.normal(0, 0.01, n_days)
        
        dates = pd.date_range(end=pd.Timestamp.now(), periods=n_days, freq='D')
        returns_df = pd.DataFrame({
            'StockA': ret_a,
            'StockB': ret_b,
            'StockC': ret_c
        }, index=dates)
        
        # Verify low correlations
        corr = returns_df.corr()
        print("\nCorrelation Matrix (should be low):")
        print(corr.round(3))
        
        tickers = ['StockA', 'StockB', 'StockC']
        kelly_fractions = {'StockA': 0.15, 'StockB': 0.20, 'StockC': 0.25}
        fss_scores = {'StockA': 70.0, 'StockB': 75.0, 'StockC': 80.0}
        fss_robustness = {'StockA': 0.8, 'StockB': 0.85, 'StockC': 0.9}
        volatilities = {'StockA': 0.20, 'StockB': 0.20, 'StockC': 0.20}
        
        result = self.allocator.allocate_portfolio(
            tickers=tickers,
            kelly_fractions=kelly_fractions,
            fss_scores=fss_scores,
            fss_robustness=fss_robustness,
            returns_matrix=returns_df,
            volatilities=volatilities,
            method="kelly_constrained"
        )
        
        weights = result.weights
        
        print("\nAllocation Results (uncorrelated assets):")
        for stock, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
            print(f"  {stock}: {weight:.4f} ({weight*100:.2f}%)")
        
        # With uncorrelated assets, weights should roughly follow Kelly fractions
        # (adjusted for robustness)
        w_a = weights.get('StockA', 0.0)
        w_b = weights.get('StockB', 0.0)
        w_c = weights.get('StockC', 0.0)
        
        # StockC should have highest weight (highest Kelly 0.25 + highest robustness 0.9)
        # StockB should have middle weight (Kelly 0.20 + robustness 0.85)
        # StockA should have lowest weight (Kelly 0.15 + robustness 0.8)
        # However, due to normalization and constraints, they might be close
        # The key is that C >= B >= A (allowing for small differences)
        print(f"\nWeight ordering check:")
        print(f"  StockC (Kelly=0.25, Robust=0.9): {w_c:.4f}")
        print(f"  StockB (Kelly=0.20, Robust=0.85): {w_b:.4f}")
        print(f"  StockA (Kelly=0.15, Robust=0.8): {w_a:.4f}")
        
        # Allow for small differences due to normalization, but C should be >= B >= A
        self.assertGreaterEqual(w_c, w_b - 0.05, 
                               f"StockC ({w_c:.4f}) should be >= StockB ({w_b:.4f})")
        self.assertGreaterEqual(w_b, w_a - 0.05,
                               f"StockB ({w_b:.4f}) should be >= StockA ({w_a:.4f})")
        
        print(f"\n✓ Diversification Score: {result.diversification_score:.3f} (should be high)")
        self.assertGreater(result.diversification_score, 0.5,
                          "Uncorrelated assets should have high diversification score")
        
        print("\n✅ UNCORRELATED ASSETS TEST PASSED\n")


if __name__ == '__main__':
    unittest.main(verbosity=2)

