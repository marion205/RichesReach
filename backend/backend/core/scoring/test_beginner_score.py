#!/usr/bin/env python3
"""
Quick tests for the new beginner scoring system
"""

from beginner_score import compute_beginner_score

def test_beginner_score_bounds():
    """Test that scores are always between 0-100"""
    s = compute_beginner_score({}, {})
    assert 0 <= s.score <= 100, f"Score {s.score} out of bounds"
    print(f"✅ Bounds test passed: {s.score}")

def test_yield_parsing():
    """Test that dividend yield parsing handles different formats"""
    s1 = compute_beginner_score({"DividendYield": "0.035"}, {"avgDollarVolume": 1e8})
    s2 = compute_beginner_score({"DividendYield": "3.5"},  {"avgDollarVolume": 1e8})
    assert abs(s1.score - s2.score) <= 5, f"Yield parsing inconsistent: {s1.score} vs {s2.score}"
    print(f"✅ Yield parsing test passed: {s1.score} vs {s2.score}")

def test_apple_scoring():
    """Test Apple's scoring with realistic data"""
    apple_overview = {
        "Name": "Apple Inc.",
        "Symbol": "AAPL",
        "Sector": "Technology",
        "MarketCapitalization": "2800000000000",  # $2.8T
        "PERatio": "28.5",
        "DividendYield": "0.0044",  # 0.44%
        "Beta": "1.2",
        "ProfitMargin": "0.25",
        "ReturnOnEquityTTM": "1.47",
        "DebtToEquity": "1.73"
    }
    apple_market = {
        "price": 150.0,
        "avgDollarVolume": 1e9,  # $1B/day
        "annualizedVol": 0.25,   # 25% volatility
        "beta": 1.2
    }
    
    # Test with different budgets
    budgets = [500, 1000, 2000, 5000]
    for budget in budgets:
        result = compute_beginner_score(apple_overview, apple_market, budget)
        print(f"🍎 Apple score (${budget} budget): {result.score}")
        affordability_factor = next((f for f in result.factors if f.name == "Affordability"), None)
        if affordability_factor:
            print(f"   Affordability: {affordability_factor.value:.3f} (contrib: {affordability_factor.contrib:.1f})")
    
    # Use $1000 budget for main test
    result = compute_beginner_score(apple_overview, apple_market, 1000.0)
    print(f"🍎 Apple score: {result.score}")
    print("   Factors:")
    for factor in result.factors:
        print(f"     {factor.name}: {factor.value:.3f} (contrib: {factor.contrib:.1f})")
    
    # Apple should score reasonably high due to size, sector, liquidity
    # (New system is more conservative than old system)
    assert result.score >= 60, f"Apple score too low: {result.score}"
    print(f"✅ Apple scoring test passed: {result.score}")

def test_tesla_scoring():
    """Test Tesla's scoring (should be lower due to volatility)"""
    tesla_overview = {
        "Name": "Tesla, Inc.",
        "Symbol": "TSLA", 
        "Sector": "Automotive",
        "MarketCapitalization": "800000000000",  # $800B
        "PERatio": "65.2",
        "DividendYield": "0",  # No dividend
        "Beta": "2.1",
        "ProfitMargin": "0.10",
        "ReturnOnEquityTTM": "0.19",
        "DebtToEquity": "0.17"
    }
    tesla_market = {
        "price": 200.0,
        "avgDollarVolume": 2e9,  # $2B/day
        "annualizedVol": 0.60,   # 60% volatility (high!)
        "beta": 2.1
    }
    
    # Test with different budgets
    budgets = [500, 1000, 2000, 5000]
    for budget in budgets:
        result = compute_beginner_score(tesla_overview, tesla_market, budget)
        print(f"🚗 Tesla score (${budget} budget): {result.score}")
        affordability_factor = next((f for f in result.factors if f.name == "Affordability"), None)
        if affordability_factor:
            print(f"   Affordability: {affordability_factor.value:.3f} (contrib: {affordability_factor.contrib:.1f})")
    
    # Use $1000 budget for main test
    result = compute_beginner_score(tesla_overview, tesla_market, 1000.0)
    print(f"🚗 Tesla score: {result.score}")
    print("   Factors:")
    for factor in result.factors:
        print(f"     {factor.name}: {factor.value:.3f} (contrib: {factor.contrib:.1f})")
    
    # Tesla should score lower due to high volatility, PE, no dividend
    assert result.score <= 75, f"Tesla score too high: {result.score}"
    print(f"✅ Tesla scoring test passed: {result.score}")

if __name__ == "__main__":
    print("🧪 Testing new beginner scoring system...")
    test_beginner_score_bounds()
    test_yield_parsing()
    test_apple_scoring()
    test_tesla_scoring()
    print("🎉 All tests passed!")
