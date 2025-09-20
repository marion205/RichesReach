# Unit tests for payoff engine
import pytest
import numpy as np
from payoff_engine import (
    OptionLeg, leg_payoff_at_expiry, strategy_profile, summary_from_profile,
    covered_call, vertical_call_spread, iron_condor, calculate_risk_metrics
)

class TestPayoffEngine:
    def test_leg_payoff_call_buy(self):
        """Test payoff calculation for long call"""
        leg = OptionLeg("call", "buy", 100, 5.0, 1)
        
        # ITM at expiry
        payoff = leg_payoff_at_expiry(110, leg)
        expected = (110 - 100 - 5.0) * 100  # (S - K - premium) * multiplier
        assert abs(payoff - expected) < 1e-10
        
        # OTM at expiry
        payoff = leg_payoff_at_expiry(90, leg)
        expected = (0 - 5.0) * 100  # (0 - premium) * multiplier
        assert abs(payoff - expected) < 1e-10
        
    def test_leg_payoff_put_sell(self):
        """Test payoff calculation for short put"""
        leg = OptionLeg("put", "sell", 100, 3.0, 1)
        
        # ITM at expiry (bad for short put)
        payoff = leg_payoff_at_expiry(90, leg)
        expected = -(100 - 90 - 3.0) * 100  # -(K - S - premium) * multiplier
        assert abs(payoff - expected) < 1e-10
        
        # OTM at expiry (good for short put)
        payoff = leg_payoff_at_expiry(110, leg)
        expected = -(0 - 3.0) * 100  # -(0 - premium) * multiplier
        assert abs(payoff - expected) < 1e-10
        
    def test_strategy_profile(self):
        """Test strategy profile calculation"""
        legs = [
            OptionLeg("call", "buy", 100, 5.0, 1),
            OptionLeg("call", "sell", 110, 2.0, 1)
        ]
        S_grid = np.linspace(90, 120, 11)
        
        profile = strategy_profile(legs, S_grid)
        
        assert "S" in profile
        assert "total" in profile
        assert "leg_0" in profile
        assert "leg_1" in profile
        
        # Check that total is sum of individual legs
        total_calculated = profile["leg_0"] + profile["leg_1"]
        np.testing.assert_array_almost_equal(profile["total"], total_calculated)
        
    def test_summary_from_profile(self):
        """Test summary calculation from profile"""
        S = np.array([90, 95, 100, 105, 110, 115, 120])
        P = np.array([-5, -2, 1, 4, 2, -1, -4])  # Profit profile with max at 105
        profile = {"S": S, "total": P}
        
        summary = summary_from_profile(profile)
        
        assert summary["max_profit"] == 4.0
        assert summary["max_loss"] == -5.0
        assert summary["argmax_S"] == 105.0
        assert summary["argmin_S"] == 90.0
        
    def test_vertical_call_spread(self):
        """Test vertical call spread strategy"""
        profile, summary = vertical_call_spread(
            K_long=100, prem_long=5.0,
            K_short=110, prem_short=2.0,
            qty=1
        )
        
        # Should have limited profit and limited loss
        assert summary["max_profit"] > 0
        assert summary["max_loss"] < 0
        assert len(summary["breakevens"]) >= 1
        
        # Check that profile has expected shape
        assert "S" in profile
        assert "total" in profile
        assert "leg_0" in profile
        assert "leg_1" in profile
        
    def test_covered_call(self):
        """Test covered call strategy"""
        profile, summary = covered_call(
            current_price=100,
            stock_qty=100,
            call_strike=110,
            call_premium=3.0
        )
        
        # Should have limited upside, unlimited downside
        assert summary["max_profit"] > 0
        assert summary["max_loss"] < 0
        
        # Check that profile includes stock P/L
        assert "S" in profile
        assert "total" in profile
        
    def test_iron_condor(self):
        """Test iron condor strategy"""
        profile, summary = iron_condor(
            Kp_buy=90, Kp_sell=95, Kc_sell=105, Kc_buy=110,
            prem_p_buy=1.0, prem_p_sell=2.0, prem_c_sell=2.0, prem_c_buy=1.0,
            qty=1
        )
        
        # Should have limited profit and limited loss
        assert summary["max_profit"] > 0
        assert summary["max_loss"] < 0
        
        # Check that all legs are present
        assert "leg_0" in profile
        assert "leg_1" in profile
        assert "leg_2" in profile
        assert "leg_3" in profile
        
    def test_risk_metrics(self):
        """Test risk metrics calculation"""
        S = np.linspace(90, 110, 21)
        P = np.array([-2, -1, 0, 1, 2, 3, 4, 3, 2, 1, 0, -1, -2, -3, -4, -3, -2, -1, 0, 1, 2])
        profile = {"S": S, "total": P}
        
        metrics = calculate_risk_metrics(profile)
        
        assert "profit_zone_width" in metrics
        assert "prob_profit" in metrics
        assert "expected_value" in metrics
        assert "std_dev" in metrics
        assert "sharpe_ratio" in metrics
        
        # Check reasonable ranges
        assert 0 <= metrics["prob_profit"] <= 1
        assert metrics["std_dev"] >= 0
        
    def test_breakeven_calculation(self):
        """Test breakeven point calculation"""
        # Create a simple strategy with known breakevens
        legs = [
            OptionLeg("call", "buy", 100, 5.0, 1),
            OptionLeg("call", "sell", 110, 2.0, 1)
        ]
        S_grid = np.linspace(95, 115, 201)  # Dense grid for accurate breakevens
        
        profile = strategy_profile(legs, S_grid)
        summary = summary_from_profile(profile)
        
        # Should have breakevens
        assert len(summary["breakevens"]) > 0
        
        # Check that breakevens are reasonable
        for be in summary["breakevens"]:
            assert 95 <= be <= 115
            
    def test_multiple_legs(self):
        """Test strategy with multiple legs"""
        legs = [
            OptionLeg("call", "buy", 100, 5.0, 1),
            OptionLeg("call", "sell", 110, 2.0, 2),  # Sell 2 contracts
            OptionLeg("put", "buy", 90, 3.0, 1)
        ]
        S_grid = np.linspace(80, 120, 21)
        
        profile = strategy_profile(legs, S_grid)
        
        # Check that all legs are included
        assert "leg_0" in profile
        assert "leg_1" in profile
        assert "leg_2" in profile
        
        # Check that total is sum of all legs
        total_calculated = profile["leg_0"] + profile["leg_1"] + profile["leg_2"]
        np.testing.assert_array_almost_equal(profile["total"], total_calculated)
        
    def test_edge_cases(self):
        """Test edge cases"""
        # Test with zero quantity
        leg = OptionLeg("call", "buy", 100, 5.0, 0)
        payoff = leg_payoff_at_expiry(110, leg)
        assert payoff == 0.0
        
        # Test with zero strike
        leg = OptionLeg("call", "buy", 0, 5.0, 1)
        payoff = leg_payoff_at_expiry(10, leg)
        expected = (10 - 0 - 5.0) * 100
        assert abs(payoff - expected) < 1e-10
        
        # Test with very high strike
        leg = OptionLeg("call", "buy", 1000, 5.0, 1)
        payoff = leg_payoff_at_expiry(100, leg)
        expected = (0 - 5.0) * 100  # OTM
        assert abs(payoff - expected) < 1e-10
