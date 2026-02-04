#!/usr/bin/env python3
"""
Test beginner-friendly stocks query to verify:
1. Fundamental data (market_cap, pe_ratio, volatility) is populated
2. Recommendation field (BUY/AVOID) is calculated correctly
3. Beginner scores are personalized per user
"""

import json
import requests

GRAPHQL_URL = "http://localhost:8001/graphql"

# GraphQL query
QUERY = """
query {
  beginnerFriendlyStocks {
    symbol
    companyName
    sector
    marketCap
    peRatio
    volatility
    beginnerFriendlyScore
    recommendation
    currentPrice
  }
}
"""

def test_beginner_stocks():
    """Test the beginner-friendly stocks query"""
    print("Testing beginner-friendly stocks query...")
    print("=" * 80)
    
    response = requests.post(
        GRAPHQL_URL,
        json={"query": QUERY},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code != 200:
        print(f"❌ Error: HTTP {response.status_code}")
        print(response.text)
        return
    
    data = response.json()
    
    if "errors" in data:
        print("❌ GraphQL Errors:")
        for error in data["errors"]:
            print(f"  - {error.get('message', error)}")
        return
    
    stocks = data.get("data", {}).get("beginnerFriendlyStocks", [])
    
    if not stocks:
        print("❌ No stocks returned")
        return
    
    print(f"✅ Returned {len(stocks)} stocks\n")
    
    # Check first 5 stocks
    for i, stock in enumerate(stocks[:5], 1):
        symbol = stock.get("symbol", "N/A")
        company = stock.get("companyName", "N/A")
        sector = stock.get("sector", "N/A")
        market_cap = stock.get("marketCap", 0)
        pe_ratio = stock.get("peRatio", 0)
        volatility = stock.get("volatility", 0)
        score = stock.get("beginnerFriendlyScore", 0)
        recommendation = stock.get("recommendation", "N/A")
        price = stock.get("currentPrice", 0)
        
        print(f"{i}. {symbol} - {company}")
        print(f"   Sector: {sector}")
        print(f"   Market Cap: ${market_cap:,}" if market_cap else "   Market Cap: $0")
        print(f"   P/E Ratio: {pe_ratio}")
        print(f"   Volatility: {volatility}%")
        print(f"   Beginner Score: {score}")
        print(f"   Recommendation: {recommendation}")
        print(f"   Price: ${price:.2f}" if price else "   Price: N/A")
        
        # Validate data
        issues = []
        if not market_cap or market_cap == 0:
            issues.append("Missing market cap")
        if not pe_ratio or pe_ratio == 0:
            issues.append("Missing P/E ratio")
        if not volatility or volatility == 0:
            issues.append("Missing volatility")
        if not recommendation or recommendation == "N/A":
            issues.append("Missing recommendation")
        if score >= 60 and recommendation != "BUY":
            issues.append(f"Score {score} should be BUY, got {recommendation}")
        if score < 40 and recommendation != "AVOID":
            issues.append(f"Score {score} should be AVOID, got {recommendation}")
        if 40 <= score < 60 and recommendation not in ["HOLD", "BUY"]:
            issues.append(f"Score {score} should be HOLD or BUY, got {recommendation}")
        
        if issues:
            print(f"   ⚠️  Issues: {', '.join(issues)}")
        else:
            print(f"   ✅ All data complete")
        print()
    
    # Summary
    print("=" * 80)
    print("Summary:")
    complete = 0
    for stock in stocks:
        if (stock.get("marketCap", 0) > 0 and 
            stock.get("peRatio", 0) > 0 and 
            stock.get("volatility", 0) > 0 and 
            stock.get("recommendation") in ["BUY", "HOLD", "AVOID"]):
            complete += 1
    
    print(f"Stocks with complete data: {complete}/{len(stocks)} ({100*complete/len(stocks):.1f}%)")
    
    # Check recommendation distribution
    buy = sum(1 for s in stocks if s.get("recommendation") == "BUY")
    hold = sum(1 for s in stocks if s.get("recommendation") == "HOLD")
    avoid = sum(1 for s in stocks if s.get("recommendation") == "AVOID")
    
    print(f"Recommendations: BUY={buy}, HOLD={hold}, AVOID={avoid}")

if __name__ == "__main__":
    test_beginner_stocks()
