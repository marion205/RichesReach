#!/usr/bin/env python3
"""
Comprehensive Test Suite for Tax Optimization Suite 2.0
Tests all premium tax optimization endpoints
"""

import requests
import json
import time
from datetime import date, timedelta

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE_URL = f"{BASE_URL}"

# Test data
SAMPLE_LOTS = [
    {
        "lot_id": "lot_001",
        "symbol": "AAPL",
        "shares": 100,
        "cost_basis": 150.00,
        "price": 140.00,
        "acquire_date": "2023-01-15",
        "unrealized_gain": -1000.00
    },
    {
        "lot_id": "lot_002", 
        "symbol": "TSLA",
        "shares": 50,
        "cost_basis": 200.00,
        "price": 180.00,
        "acquire_date": "2023-06-20",
        "unrealized_gain": -1000.00
    },
    {
        "lot_id": "lot_003",
        "symbol": "MSFT", 
        "shares": 75,
        "cost_basis": 300.00,
        "price": 320.00,
        "acquire_date": "2022-03-10",
        "unrealized_gain": 1500.00
    },
    {
        "lot_id": "lot_004",
        "symbol": "GOOGL",
        "shares": 25,
        "cost_basis": 2000.00,
        "price": 2500.00,
        "acquire_date": "2021-11-05",
        "unrealized_gain": 12500.00
    }
]

SAMPLE_GAIN_CANDIDATES = [
    {
        "id": "cand_001",
        "symbol": "AAPL",
        "gain": 5000.0,
        "days_to_lt": 0,
        "current_price": 175.0,
        "cost_basis": 150.0,
        "shares": 100,
        "acquire_date": "2023-01-15",
        "priority": "high"
    },
    {
        "id": "cand_002",
        "symbol": "TSLA",
        "gain": 3000.0,
        "days_to_lt": 45,
        "current_price": 250.0,
        "cost_basis": 200.0,
        "shares": 50,
        "acquire_date": "2023-08-15",
        "priority": "medium"
    }
]

def test_endpoint(endpoint, method="GET", data=None, expected_status=200):
    """Test a single endpoint"""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer mock-auth-token"
    }
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        
        status_ok = response.status_code == expected_status
        print(f"{'✅' if status_ok else '❌'} {method} {endpoint} - {response.status_code}")
        
        if not status_ok:
            print(f"   Expected: {expected_status}, Got: {response.status_code}")
            if response.text:
                print(f"   Response: {response.text[:200]}...")
        
        return status_ok, response
        
    except requests.exceptions.RequestException as e:
        print(f"❌ {method} {endpoint} - Connection Error: {e}")
        return False, None

def test_basic_endpoints():
    """Test basic health and configuration endpoints"""
    print("\n🔍 TESTING BASIC ENDPOINTS")
    print("=" * 50)
    
    endpoints = [
        ("/health", "GET", None, 200),
        ("/live", "GET", None, 200),
        ("/ready", "GET", None, 200),
        ("/api/mobile/config", "GET", None, 200),
    ]
    
    results = []
    for endpoint, method, data, expected_status in endpoints:
        success, response = test_endpoint(endpoint, method, data, expected_status)
        results.append(success)
    
    return results

def test_original_tax_endpoints():
    """Test original tax optimization endpoints"""
    print("\n🔍 TESTING ORIGINAL TAX ENDPOINTS")
    print("=" * 50)
    
    endpoints = [
        ("/api/tax/loss-harvesting", "GET", None, 200),
        ("/api/tax/capital-gains-optimization", "GET", None, 200),
        ("/api/tax/efficient-rebalancing", "GET", None, 200),
        ("/api/tax/bracket-analysis", "GET", None, 200),
        ("/api/tax/optimization-summary", "GET", None, 200),
    ]
    
    results = []
    for endpoint, method, data, expected_status in endpoints:
        success, response = test_endpoint(endpoint, method, data, expected_status)
        results.append(success)
    
    return results

def test_smart_lot_optimizer_v1():
    """Test Smart Lot Optimizer V1"""
    print("\n🔍 TESTING SMART LOT OPTIMIZER V1")
    print("=" * 50)
    
    payload = {
        "lots": SAMPLE_LOTS,
        "target_cash": 10000.0,
        "long_term_days": 365,
        "fed_st_rate": 0.24,
        "fed_lt_rate": 0.15,
        "state_st_rate": 0.0,
        "forbid_wash_sale": True,
        "recent_buys_30d": {},
        "max_portfolio_drift": 0.05
    }
    
    success, response = test_endpoint("/api/tax/smart-lot-optimizer", "POST", payload, 200)
    
    if success and response:
        try:
            data = response.json()
            if data.get("status") == "success":
                result = data.get("result", {})
                print(f"   ✅ Cash raised: ${result.get('cash_raised', 0):,.2f}")
                print(f"   ✅ Tax cost: ${result.get('est_tax_cost', 0):,.2f}")
                print(f"   ✅ Sells: {len(result.get('sells', []))}")
            else:
                print(f"   ❌ API returned error: {data.get('message', 'Unknown error')}")
        except json.JSONDecodeError:
            print(f"   ❌ Invalid JSON response")
    
    return [success]

def test_smart_lot_optimizer_v2():
    """Test Smart Lot Optimizer V2"""
    print("\n🔍 TESTING SMART LOT OPTIMIZER V2")
    print("=" * 50)
    
    payload = {
        "lots": SAMPLE_LOTS,
        "target_cash": 10000.0,
        "long_term_days": 365,
        "st_rate": 0.24,
        "lt_rate": 0.15,
        "state_st_rate": 0.0,
        "state_lt_rate": 0.0,
        "loss_budget": 2000.0,
        "recent_buys_30d": {},
        "forbid_wash_sale": True,
        "bracket_target": 0.15,
        "max_portfolio_drift": 0.05,
        "prefer_long_term": True,
        "min_holding_period": 0
    }
    
    success, response = test_endpoint("/api/tax/smart-lot-optimizer-v2", "POST", payload, 200)
    
    if success and response:
        try:
            data = response.json()
            if data.get("status") == "success":
                result = data.get("result", {})
                print(f"   ✅ Cash raised: ${result.get('cash_raised', 0):,.2f}")
                print(f"   ✅ Tax cost: ${result.get('est_tax_cost', 0):,.2f}")
                print(f"   ✅ Losses used: ${result.get('est_losses_used', 0):,.2f}")
                print(f"   ✅ Sells: {len(result.get('sells', []))}")
                
                # Test vs FIFO comparison
                fifo_comparison = result.get("vs_fifo_comparison", {})
                if fifo_comparison:
                    savings = fifo_comparison.get("tax_savings", 0)
                    percentage = fifo_comparison.get("savings_percentage", 0)
                    print(f"   ✅ vs FIFO savings: ${savings:,.2f} ({percentage}%)")
            else:
                print(f"   ❌ API returned error: {data.get('message', 'Unknown error')}")
        except json.JSONDecodeError:
            print(f"   ❌ Invalid JSON response")
    
    return [success]

def test_two_year_gains_planner():
    """Test Two-Year Gains Planner"""
    print("\n🔍 TESTING TWO-YEAR GAINS PLANNER")
    print("=" * 50)
    
    payload = {
        "candidates": SAMPLE_GAIN_CANDIDATES,
        "year1_cap_room": 10000.0,
        "year2_cap_room": 15000.0,
        "prefer_lt": True,
        "current_income": 75000.0,
        "filing_status": "single",
        "state_tax_rate": 0.0,
        "risk_tolerance": "moderate"
    }
    
    success, response = test_endpoint("/api/tax/two-year-gains-planner", "POST", payload, 200)
    
    if success and response:
        try:
            data = response.json()
            if data.get("status") == "success":
                result = data.get("result", {})
                sell_now = result.get("sell_now", [])
                defer_next_year = result.get("defer_to_next_year", [])
                print(f"   ✅ Sell now: {len(sell_now)} candidates")
                print(f"   ✅ Defer to next year: {len(defer_next_year)} candidates")
                
                tax_impact = result.get("tax_impact", {})
                if tax_impact:
                    year1_tax = tax_impact.get("year1_tax", 0)
                    year2_tax = tax_impact.get("year2_tax", 0)
                    print(f"   ✅ Year 1 tax: ${year1_tax:,.2f}")
                    print(f"   ✅ Year 2 tax: ${year2_tax:,.2f}")
            else:
                print(f"   ❌ API returned error: {data.get('message', 'Unknown error')}")
        except json.JSONDecodeError:
            print(f"   ❌ Invalid JSON response")
    
    return [success]

def test_wash_sale_guard_v1():
    """Test Wash-Sale Guard V1"""
    print("\n🔍 TESTING WASH-SALE GUARD V1")
    print("=" * 50)
    
    payload = {
        "symbol": "AAPL",
        "unrealized_pnl": -1000.0,
        "shares_to_sell": 50,
        "recent_buys_30d": {"AAPL": 25},
        "recent_sells_30d": {},
        "portfolio_positions": {"AAPL": 100, "IVV": 0},
        "wash_sale_threshold": 0.0
    }
    
    success, response = test_endpoint("/api/tax/wash-sale-guard", "POST", payload, 200)
    
    if success and response:
        try:
            data = response.json()
            if data.get("status") == "success":
                result = data.get("result", {})
                allowed = result.get("allowed", False)
                substitutes = result.get("suggested_substitutes", [])
                print(f"   ✅ Trade allowed: {allowed}")
                print(f"   ✅ Substitutes suggested: {len(substitutes)}")
                if substitutes:
                    for sub in substitutes[:2]:  # Show first 2
                        print(f"      - {sub.get('symbol', 'N/A')} (correlation: {sub.get('correlation_score', 0):.3f})")
            else:
                print(f"   ❌ API returned error: {data.get('message', 'Unknown error')}")
        except json.JSONDecodeError:
            print(f"   ❌ Invalid JSON response")
    
    return [success]

def test_wash_sale_guard_v2():
    """Test Wash-Sale Guard V2"""
    print("\n🔍 TESTING WASH-SALE GUARD V2")
    print("=" * 50)
    
    payload = {
        "symbol": "VOO",
        "unrealized_pnl": -1500.0,
        "shares_to_sell": 100,
        "recent_buys_30d": {"VOO": 50},
        "recent_sells_30d": {},
        "portfolio_positions": {"VOO": 200, "IVV": 0, "SPY": 0},
        "wash_sale_threshold": 0.0,
        "correlation_threshold": 0.95,
        "risk_tolerance": "moderate"
    }
    
    success, response = test_endpoint("/api/tax/wash-sale-guard-v2", "POST", payload, 200)
    
    if success and response:
        try:
            data = response.json()
            if data.get("status") == "success":
                result = data.get("result", {})
                allowed = result.get("allowed", False)
                substitutes = result.get("suggested_substitutes", [])
                risk_assessment = result.get("risk_assessment", {})
                print(f"   ✅ Trade allowed: {allowed}")
                print(f"   ✅ Substitutes suggested: {len(substitutes)}")
                print(f"   ✅ Risk level: {risk_assessment.get('risk_level', 'Unknown')}")
                if substitutes:
                    for sub in substitutes[:2]:  # Show first 2
                        print(f"      - {sub.get('symbol', 'N/A')} (correlation: {sub.get('correlation_score', 0):.3f}, score: {sub.get('substitute_score', 0):.3f})")
            else:
                print(f"   ❌ API returned error: {data.get('message', 'Unknown error')}")
        except json.JSONDecodeError:
            print(f"   ❌ Invalid JSON response")
    
    return [success]

def test_borrow_vs_sell_advisor():
    """Test Borrow-vs-Sell Advisor"""
    print("\n🔍 TESTING BORROW-VS-SELL ADVISOR")
    print("=" * 50)
    
    payload = {
        "needed_cash": 50000.0,
        "est_cap_gain": 10000.0,
        "cap_gain_rate": 0.15,
        "borrow_rate": 0.06,
        "horizon_years": 1.0,
        "ltv": 0.5,
        "fees_rate": 0.0,
        "portfolio_value": 200000.0,
        "risk_tolerance": "moderate",
        "tax_bracket": 0.22,
        "state_tax_rate": 0.0,
        "inflation_rate": 0.03,
        "opportunity_cost_rate": 0.07
    }
    
    success, response = test_endpoint("/api/tax/borrow-vs-sell", "POST", payload, 200)
    
    if success and response:
        try:
            data = response.json()
            if data.get("status") == "success":
                result = data.get("result", {})
                recommendation = result.get("recommendation", "Unknown")
                sell_net_cash = result.get("sell_net_cash", 0)
                borrow_cost_total = result.get("borrow_cost_total", 0)
                print(f"   ✅ Recommendation: {recommendation}")
                print(f"   ✅ Sell net cash: ${sell_net_cash:,.2f}")
                print(f"   ✅ Borrow cost total: ${borrow_cost_total:,.2f}")
                
                scenarios = result.get("scenarios", [])
                if scenarios:
                    print(f"   ✅ Scenarios analyzed: {len(scenarios)}")
            else:
                print(f"   ❌ API returned error: {data.get('message', 'Unknown error')}")
        except json.JSONDecodeError:
            print(f"   ❌ Invalid JSON response")
    
    return [success]

def test_other_endpoints():
    """Test other production endpoints"""
    print("\n🔍 TESTING OTHER PRODUCTION ENDPOINTS")
    print("=" * 50)
    
    endpoints = [
        ("/api/ai-portfolio/optimize", "GET", None, 200),
        ("/api/ml/status", "GET", None, 200),
        ("/api/crypto/prices", "GET", None, 200),
        ("/api/defi/account", "GET", None, 200),
        ("/rust/analyze", "GET", None, 200),
        ("/api/market-data/stocks", "GET", None, 200),
        ("/api/market-data/options", "GET", None, 200),
        ("/api/market-data/news", "GET", None, 200),
        ("/api/sbloc/banks", "GET", None, 200),
    ]
    
    results = []
    for endpoint, method, data, expected_status in endpoints:
        success, response = test_endpoint(endpoint, method, data, expected_status)
        results.append(success)
    
    return results

def main():
    """Run all tests"""
    print("🚀 RICHESREACH TAX OPTIMIZATION SUITE 2.0 - BACKEND TEST")
    print("=" * 60)
    print(f"Testing against: {API_BASE_URL}")
    print(f"Test started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_results = []
    
    # Run all test suites
    all_results.extend(test_basic_endpoints())
    all_results.extend(test_original_tax_endpoints())
    all_results.extend(test_smart_lot_optimizer_v1())
    all_results.extend(test_smart_lot_optimizer_v2())
    all_results.extend(test_two_year_gains_planner())
    all_results.extend(test_wash_sale_guard_v1())
    all_results.extend(test_wash_sale_guard_v2())
    all_results.extend(test_borrow_vs_sell_advisor())
    all_results.extend(test_other_endpoints())
    
    # Summary
    total_tests = len(all_results)
    passed_tests = sum(all_results)
    failed_tests = total_tests - passed_tests
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
    
    if failed_tests == 0:
        print("\n🎉 ALL TESTS PASSED! Backend is ready for production!")
    else:
        print(f"\n⚠️  {failed_tests} tests failed. Please check the errors above.")
    
    print(f"\nTest completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
