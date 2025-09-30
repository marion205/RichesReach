#!/usr/bin/env python3
"""
Comprehensive test script to test every GraphQL endpoint that the React Native UI needs.
This will help identify all missing fields and 400 errors.
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"
GRAPHQL_URL = f"{BASE_URL}/graphql/"

def test_endpoint(name, query, variables=None, expected_fields=None):
    """Test a GraphQL endpoint and return detailed results."""
    try:
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
            
        response = requests.post(GRAPHQL_URL, json=payload, timeout=10)
        
        print(f"\n{'='*60}")
        print(f"🧪 Testing: {name}")
        print(f"{'='*60}")
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                print(f"❌ GraphQL Errors:")
                for error in data["errors"]:
                    print(f"   - {error.get('message', 'Unknown error')}")
                    if 'locations' in error:
                        print(f"     Location: {error['locations']}")
                return False, data["errors"]
            else:
                print(f"✅ Success!")
                if "data" in data:
                    # Check if expected fields are present
                    if expected_fields:
                        missing_fields = []
                        for field in expected_fields:
                            if field not in str(data["data"]):
                                missing_fields.append(field)
                        if missing_fields:
                            print(f"⚠️  Missing expected fields: {missing_fields}")
                        else:
                            print(f"✅ All expected fields present: {expected_fields}")
                    
                    # Show sample data
                    data_str = json.dumps(data["data"], indent=2)
                    if len(data_str) > 500:
                        print(f"📊 Sample data (truncated):\n{data_str[:500]}...")
                    else:
                        print(f"📊 Data:\n{data_str}")
                return True, data
        else:
            print(f"❌ HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False, response.text
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False, str(e)

def main():
    print("🚀 Comprehensive GraphQL Endpoint Testing")
    print("=" * 60)
    print(f"Testing against: {GRAPHQL_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test all the endpoints the UI needs
    tests = [
        # 1. Authentication & User
        ("User Profile (me)", """
            query {
                me {
                    id
                    email
                    name
                    username
                    hasPremiumAccess
                    subscriptionTier
                    incomeProfile
                    followedTickers
                }
            }
        """, None, ["id", "email", "name"]),
        
        # 2. Stocks - Main queries
        ("Stocks Query", """
            query {
                stocks {
                    id
                    symbol
                    companyName
                    sector
                    currentPrice
                    marketCap
                    peRatio
                    dividendYield
                    beginnerFriendlyScore
                    dividendScore
                }
            }
        """, None, ["companyName", "currentPrice", "beginnerFriendlyScore"]),
        
        ("Beginner Friendly Stocks", """
            query {
                beginnerFriendlyStocks {
                    id
                    symbol
                    companyName
                    sector
                    currentPrice
                    beginnerFriendlyScore
                    dividendScore
                }
            }
        """, None, ["companyName", "beginnerFriendlyScore"]),
        
        ("Advanced Stock Screening", """
            query {
                advancedStockScreening {
                    id
                    symbol
                    companyName
                    sector
                    currentPrice
                    beginnerFriendlyScore
                    dividendScore
                }
            }
        """, None, ["companyName", "beginnerFriendlyScore"]),
        
        # 3. Watchlist
        ("Watchlist", """
            query {
                myWatchlist {
                    id
                    addedAt
                    notes
                    targetPrice
                    stock {
                        id
                        symbol
                        companyName
                        sector
                        currentPrice
                        beginnerFriendlyScore
                    }
                }
            }
        """, None, ["stock", "targetPrice"]),
        
        # 4. Portfolio
        ("Portfolio Analysis", """
            query {
                portfolioAnalysis {
                    totalValue
                    dailyChange
                    dailyChangePercent
                    totalReturn
                    totalReturnPercent
                    holdings {
                        symbol
                        shares
                        marketValue
                        returnPercent
                    }
                }
            }
        """, None, ["totalValue", "dailyChange"]),
        
        # 5. Trading & Signals
        ("Signals", """
            query {
                signals {
                    id
                    symbol
                    timeframe
                    signalType
                    entryPrice
                    targetPrice
                    stopPrice
                    mlScore
                    thesis
                    riskRewardRatio
                    isActive
                    isValidated
                    daysSinceTriggered
                    isLikedByUser
                    userLikeCount
                }
            }
        """, None, ["symbol", "signalType", "entryPrice"]),
        
        ("Day Trading Picks", """
            query {
                dayTradingPicks(mode: "aggressive") {
                    asOf
                    mode
                    picks {
                        symbol
                        side
                        score
                        features {
                            momentum15m
                            rvol10m
                            vwapDist
                            breakoutPct
                            spreadBps
                            catalystScore
                        }
                        risk {
                            atr5m
                            sizeShares
                            stop
                            targets
                            timeStopMin
                        }
                        notes
                    }
                    universeSize
                    qualityThreshold
                }
            }
        """, None, ["picks", "mode"]),
        
        # 6. Options
        ("Option Orders", """
            query {
                optionOrders
            }
        """, None, []),
        
        # 7. Crypto
        ("Crypto Prices", """
            query {
                cryptoPrices {
                    symbol
                    price
                    change24h
                    changePercent24h
                }
            }
        """, None, ["symbol", "price"]),
        
        ("Crypto ML Signal", """
            query {
                cryptoMlSignal(symbol: "BTC") {
                    symbol
                    probability
                    confidenceLevel
                    features
                    timestamp
                }
            }
        """, None, ["symbol", "probability"]),
        
        ("Crypto Recommendations", """
            query {
                cryptoRecommendations {
                    symbol
                    recommendation
                    confidenceLevel
                    rationale
                }
            }
        """, None, ["symbol", "recommendation"]),
        
        ("Supported Currencies", """
            query {
                supportedCurrencies {
                    symbol
                    name
                    priceUsd
                    change24h
                }
            }
        """, None, ["symbol", "name"]),
        
        ("Crypto Portfolio", """
            query {
                cryptoPortfolio {
                    totalValueUsd
                    totalGainLoss
                    holdings {
                        cryptocurrency {
                            symbol
                            name
                        }
                        quantity
                        valueUsd
                    }
                }
            }
        """, None, ["totalValueUsd"]),
        
        # 8. Research & Analysis
        ("Research Hub", """
            query {
                researchHub(symbol: "AAPL") {
                    symbol
                    snapshot {
                        name
                        sector
                        country
                    }
                    quote {
                        price
                        chg
                    }
                    technical {
                        resistanceLevel
                    }
                }
            }
        """, None, ["symbol"]),
        
        ("Stock Chart Data", """
            query {
                stockChartData(symbol: "AAPL") {
                    symbol
                    currentPrice
                    change
                    changePercent
                    data {
                        timestamp
                        open
                        high
                        low
                        close
                        volume
                    }
                }
            }
        """, None, ["symbol", "data"]),
        
        ("Rust Stock Analysis", """
            query {
                rustStockAnalysis(symbol: "AAPL") {
                    symbol
                    beginnerFriendlyScore
                    riskLevel
                    recommendation
                    technicalIndicators {
                        rsi
                        macd
                        sma20
                        sma50
                    }
                    fundamentalAnalysis {
                        valuationScore
                        growthScore
                        stabilityScore
                        debtScore
                        dividendScore
                        peRatio
                        marketCap
                    }
                    reasoning
                }
            }
        """, None, ["symbol", "recommendation"]),
        
        # 9. Discussions
        ("Stock Discussions", """
            query {
                stockDiscussions(stockSymbol: "AAPL") {
                    id
                    title
                    content
                    author
                    createdAt
                    score
                    commentCount
                }
            }
        """, None, ["id", "content", "author"]),
        
        # 10. Swing Trading
        ("Swing Trading Signals", """
            query {
                signals {
                    id
                    symbol
                    timeframe
                    signalType
                    entryPrice
                    targetPrice
                    stopPrice
                    mlScore
                }
            }
        """, None, ["symbol", "signalType"]),
        
        # 11. Risk Management
        ("Calculate Position Size", """
            query {
                calculatePositionSize(
                    accountBalance: 10000.0
                    riskPercentage: 2.0
                    entryPrice: 150.0
                    stopPrice: 145.0
                ) {
                    positionSize
                    riskAmount
                    shares
                }
            }
        """, None, ["positionSize", "riskAmount"]),
        
        ("Calculate Target Price", """
            query {
                calculateTargetPrice(
                    entryPrice: 150.0
                    riskRewardRatio: 2.0
                    stopPrice: 145.0
                ) {
                    targetPrice
                    riskAmount
                    rewardAmount
                }
            }
        """, None, ["targetPrice", "riskAmount"]),
        
        ("Calculate Dynamic Stop", """
            query {
                calculateDynamicStop(
                    entryPrice: 150.0
                    atr: 2.0
                    atrMultiplier: 2.0
                ) {
                    stopPrice
                }
            }
        """, None, ["stopPrice"]),
    ]
    
    passed = 0
    failed = 0
    results = []
    
    for name, query, variables, expected_fields in tests:
        success, result = test_endpoint(name, query, variables, expected_fields)
        results.append((name, success, result))
        
        if success:
            passed += 1
        else:
            failed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 TEST SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if failed > 0:
        print(f"\n❌ FAILED TESTS:")
        for name, success, result in results:
            if not success:
                print(f"   - {name}")
    
    print(f"\n🎯 Next Steps:")
    if failed == 0:
        print("   🎉 All endpoints are working! Your app should be fully functional.")
    else:
        print("   🔧 Fix the failed endpoints above to resolve all 400 errors.")
        print("   📝 Check the error messages to see what fields are missing.")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
