# Unit tests for options math - critical for financial correctness
import pytest
import math
from options_math import prob_ITM, bs_price, implied_vol, payoff_at_expiry, Leg

class TestOptionsMath:
    def test_prob_ITM_calls(self):
        """Test that prob_ITM uses N(d2) for calls"""
        # ATM call with 20% vol, 30 days
        prob = prob_ITM(100, 100, 0.01, 0.2, 30/365, "call")
        assert 0.49 < prob < 0.51  # Should be close to 0.5 for ATM
        
    def test_prob_ITM_puts(self):
        """Test that prob_ITM uses N(-d2) for puts"""
        # ATM put with 20% vol, 30 days
        prob = prob_ITM(100, 100, 0.01, 0.2, 30/365, "put")
        assert 0.49 < prob < 0.51  # Should be close to 0.5 for ATM
        
    def test_bs_price_put_call_parity(self):
        """Test put-call parity"""
        S, K, r, sigma, T = 100, 100, 0.01, 0.2, 30/365
        call_price = bs_price(S, K, r, sigma, T, "call")
        put_price = bs_price(S, K, r, sigma, T, "put")
        
        # Put-call parity: C - P = S - K*exp(-r*T)
        expected_diff = S - K * math.exp(-r * T)
        actual_diff = call_price - put_price
        
        assert abs(actual_diff - expected_diff) < 1e-10
        
    def test_implied_vol_roundtrip(self):
        """Test that implied vol recovers original vol"""
        S, K, r, sigma, T = 100, 105, 0.01, 0.25, 30/365
        price = bs_price(S, K, r, sigma, T, "call")
        recovered_vol = implied_vol(price, S, K, r, T, "call")
        
        assert abs(recovered_vol - sigma) < 1e-6
        
    def test_payoff_at_expiry(self):
        """Test payoff calculation at expiry"""
        # Long call at 100, short call at 110 (bull spread)
        legs = [
            Leg("call", "buy", 100, 1, 5.0, 30/365),
            Leg("call", "sell", 110, 1, 2.0, 30/365),
        ]
        
        # At 105: long call worth 5, short call worth 0
        payoff = payoff_at_expiry(105, legs)
        expected = (5.0 - 2.0) * 100 - 1.3  # Premium diff - fees
        assert abs(payoff - expected) < 1e-6
        
        # At 115: long call worth 15, short call worth 5
        payoff = payoff_at_expiry(115, legs)
        expected = (15.0 - 5.0) * 100 + (2.0 - 5.0) * 100 - 1.3  # Intrinsic diff + premium diff - fees
        assert abs(payoff - expected) < 1e-6
        
    def test_prob_ITM_boundary_conditions(self):
        """Test prob_ITM at extreme values"""
        # Deep ITM call
        prob = prob_ITM(200, 100, 0.01, 0.2, 30/365, "call")
        assert prob > 0.99
        
        # Deep OTM call
        prob = prob_ITM(50, 100, 0.01, 0.2, 30/365, "call")
        assert prob < 0.01
        
        # Zero time to expiry
        prob = prob_ITM(100, 100, 0.01, 0.2, 0, "call")
        assert prob == 0.5  # ATM at expiry
        
    def test_bs_price_boundary_conditions(self):
        """Test BS price at boundary conditions"""
        # Zero time to expiry (intrinsic value)
        price = bs_price(105, 100, 0.01, 0.2, 0, "call")
        assert abs(price - 5.0) < 1e-10  # Intrinsic value
        
        # Zero volatility
        price = bs_price(105, 100, 0.01, 0, 30/365, "call")
        expected = max(0, 105 - 100 * math.exp(-0.01 * 30/365))
        assert abs(price - expected) < 1e-10
        
    def test_implied_vol_edge_cases(self):
        """Test implied vol with edge cases"""
        S, K, r, T = 100, 100, 0.01, 30/365
        
        # Very low price (should give low vol)
        low_price = 0.01
        vol = implied_vol(low_price, S, K, r, T, "call")
        assert vol > 0 and vol < 0.1
        
        # Very high price (should give high vol)
        high_price = 50.0
        vol = implied_vol(high_price, S, K, r, T, "call")
        assert vol > 1.0
        
    def test_payoff_curve_shape(self):
        """Test that payoff curve has expected shape"""
        # Long call
        legs = [Leg("call", "buy", 100, 1, 5.0, 30/365)]
        xs, ys = payoff_at_expiry(100, legs, span=(0.5, 1.5))
        
        # Should be flat below strike, then linear above
        assert len(xs) == 101
        assert len(ys) == 101
        
        # Below strike: payoff should be negative (premium paid)
        assert ys[0] < 0
        
        # Above strike: payoff should increase linearly
        for i in range(50, 100):
            if xs[i] > 100:
                expected_payoff = (xs[i] - 100) * 100 - 5.0 * 100 - 0.65
                assert abs(ys[i] - expected_payoff) < 1e-6
