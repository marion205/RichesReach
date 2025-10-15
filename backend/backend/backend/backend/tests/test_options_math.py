# Unit tests for options math - critical for financial correctness
import pytest
import math
import numpy as np
from options_math import BSParams, bs_price, implied_vol, prob_itm, calculate_greeks

class TestOptionsMath:
    def test_prob_itm_uses_d2_call(self):
        """Test that prob_itm uses N(d2) for calls"""
        p = BSParams(S=100, K=100, T=30/365, r=0.02, q=0.0)
        sigma = 0.2
        prob = prob_itm(p, sigma, "call")
        assert 0.45 < prob < 0.55  # ATM ~50%
        
    def test_prob_itm_uses_neg_d2_put(self):
        """Test that prob_itm uses N(-d2) for puts"""
        p = BSParams(S=100, K=100, T=30/365, r=0.02, q=0.0)
        sigma = 0.2
        prob = prob_itm(p, sigma, "put")
        assert 0.45 < prob < 0.55  # ATM ~50%
        
    def test_iv_solver_round_trip_call(self):
        """Test that IV solver recovers original volatility"""
        p = BSParams(S=100, K=95, T=60/365, r=0.02, q=0.0)
        sig = 0.35
        px = bs_price(p, sig, "call")
        iv = implied_vol(p, "call", px)
        assert iv is not None
        assert abs(iv - sig) < 1e-4
        
    def test_iv_solver_round_trip_put(self):
        """Test that IV solver works for puts"""
        p = BSParams(S=100, K=105, T=60/365, r=0.02, q=0.0)
        sig = 0.25
        px = bs_price(p, sig, "put")
        iv = implied_vol(p, "put", px)
        assert iv is not None
        assert abs(iv - sig) < 1e-4
        
    def test_put_call_parity(self):
        """Test put-call parity"""
        S, K, T, r, q = 100, 100, 30/365, 0.02, 0.01
        p = BSParams(S=S, K=K, T=T, r=r, q=q)
        sigma = 0.2
        
        call_price = bs_price(p, sigma, "call")
        put_price = bs_price(p, sigma, "put")
        
        # Put-call parity: C - P = S*exp(-q*T) - K*exp(-r*T)
        expected_diff = S * math.exp(-q * T) - K * math.exp(-r * T)
        actual_diff = call_price - put_price
        
        assert abs(actual_diff - expected_diff) < 1e-10
        
    def test_greeks_calculation(self):
        """Test that Greeks are calculated correctly"""
        p = BSParams(S=100, K=100, T=30/365, r=0.02, q=0.0)
        sigma = 0.2
        
        greeks = calculate_greeks(p, sigma, "call")
        
        # Check that all Greeks are present
        assert 'delta' in greeks
        assert 'gamma' in greeks
        assert 'theta' in greeks
        assert 'vega' in greeks
        assert 'rho' in greeks
        
        # Check reasonable ranges
        assert 0 <= greeks['delta'] <= 1
        assert greeks['gamma'] > 0
        assert greeks['vega'] > 0
        
    def test_boundary_conditions(self):
        """Test boundary conditions"""
        p = BSParams(S=100, K=100, T=0.001, r=0.02, q=0.0)  # Very short time
        sigma = 0.2
        
        # At very short time, option should be close to intrinsic value
        call_price = bs_price(p, sigma, "call")
        put_price = bs_price(p, sigma, "put")
        
        # For ATM options at expiry, should be close to 0
        assert call_price < 1.0
        assert put_price < 1.0
        
    def test_zero_volatility(self):
        """Test behavior at zero volatility"""
        p = BSParams(S=100, K=100, T=30/365, r=0.02, q=0.0)
        sigma = 0.0
        
        # At zero volatility, option should be worth intrinsic value
        call_price = bs_price(p, sigma, "call")
        put_price = bs_price(p, sigma, "put")
        
        # ATM options at zero vol should be worth 0
        assert abs(call_price) < 1e-10
        assert abs(put_price) < 1e-10
        
    def test_deep_itm_probabilities(self):
        """Test probabilities for deep ITM/OTM options"""
        p = BSParams(S=100, K=50, T=30/365, r=0.02, q=0.0)  # Deep ITM call
        sigma = 0.2
        
        call_prob = prob_itm(p, sigma, "call")
        put_prob = prob_itm(p, sigma, "put")
        
        # Deep ITM call should have high probability
        assert call_prob > 0.99
        # Deep OTM put should have low probability
        assert put_prob < 0.01
        
    def test_iv_solver_edge_cases(self):
        """Test IV solver with edge cases"""
        p = BSParams(S=100, K=100, T=30/365, r=0.02, q=0.0)
        
        # Very low price should give low IV
        low_price = 0.01
        iv = implied_vol(p, "call", low_price)
        assert iv is not None
        assert iv < 0.1
        
        # Very high price should give high IV
        high_price = 50.0
        iv = implied_vol(p, "call", high_price)
        assert iv is not None
        assert iv > 1.0
        
    def test_dividend_yield(self):
        """Test that dividend yield affects option prices correctly"""
        p_no_div = BSParams(S=100, K=100, T=30/365, r=0.02, q=0.0)
        p_with_div = BSParams(S=100, K=100, T=30/365, r=0.02, q=0.05)
        sigma = 0.2
        
        call_no_div = bs_price(p_no_div, sigma, "call")
        call_with_div = bs_price(p_with_div, sigma, "call")
        
        # Call with dividend should be cheaper
        assert call_with_div < call_no_div
        
        put_no_div = bs_price(p_no_div, sigma, "put")
        put_with_div = bs_price(p_with_div, sigma, "put")
        
        # Put with dividend should be more expensive
        assert put_with_div > put_no_div
