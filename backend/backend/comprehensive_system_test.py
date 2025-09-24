#!/usr/bin/env python3
"""
Comprehensive System Test for All GraphQL Endpoints
Tests all UI endpoints to ensure they work with real data
"""
import requests
import json
import time
from datetime import datetime

class GraphQLSystemTester:
    def __init__(self, base_url="http://127.0.0.1:8001/graphql/"):
        self.base_url = base_url
        self.results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
    
    def test_query(self, name, query, variables=None, expected_fields=None):
        """Test a GraphQL query"""
        print(f"\n🧪 Testing: {name}")
        
        try:
            payload = {
                "query": query,
                "variables": variables or {}
            }
            
            response = requests.post(
                self.base_url,
                headers={'Content-Type': 'application/json'},
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'errors' in data and data['errors']:
                    print(f"   ❌ GraphQL Errors: {data['errors']}")
                    self.results['failed'] += 1
                    self.results['errors'].append(f"{name}: {data['errors']}")
                    return False
                
                if 'data' in data:
                    print(f"   ✅ Status: 200 OK")
                    
                    # Check for expected fields
                    if expected_fields:
                        for field in expected_fields:
                            if field in data['data']:
                                print(f"   ✅ Field '{field}': Present")
                            else:
                                print(f"   ⚠️  Field '{field}': Missing")
                    
                    # Show sample data
                    self._show_sample_data(data['data'], name)
                    self.results['passed'] += 1
                    return True
                else:
                    print(f"   ❌ No data in response")
                    self.results['failed'] += 1
                    return False
            else:
                print(f"   ❌ HTTP {response.status_code}: {response.text}")
                self.results['failed'] += 1
                self.results['errors'].append(f"{name}: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            self.results['failed'] += 1
            self.results['errors'].append(f"{name}: {str(e)}")
            return False
    
    def _show_sample_data(self, data, test_name):
        """Show sample data from response"""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, list) and len(value) > 0:
                    print(f"   📊 {key}: {len(value)} items")
                    if len(value) > 0:
                        sample = value[0]
                        if isinstance(sample, dict):
                            sample_keys = list(sample.keys())[:3]  # Show first 3 keys
                            print(f"      Sample: {sample_keys}")
                elif isinstance(value, dict):
                    print(f"   📊 {key}: {list(value.keys())}")
                else:
                    print(f"   📊 {key}: {value}")
    
    def run_all_tests(self):
        """Run all system tests"""
        print("🚀 Starting Comprehensive GraphQL System Test")
        print("=" * 60)
        
        # Test 1: Authentication
        self.test_authentication()
        
        # Test 2: Stock Data Queries
        self.test_stock_queries()
        
        # Test 3: Swing Trading Queries
        self.test_swing_trading_queries()
        
        # Test 4: Backtesting Queries
        self.test_backtesting_queries()
        
        # Test 5: Risk Management Queries
        self.test_risk_management_queries()
        
        # Test 6: Portfolio Queries
        self.test_portfolio_queries()
        
        # Test 7: Watchlist Queries
        self.test_watchlist_queries()
        
        # Test 8: Advanced Screening
        self.test_advanced_screening()
        
        # Test 9: Rust Stock Analysis
        self.test_rust_analysis()
        
        # Test 10: Mutations
        self.test_mutations()
        
        # Print final results
        self.print_final_results()
    
    def test_authentication(self):
        """Test authentication endpoints"""
        print("\n🔐 AUTHENTICATION TESTS")
        print("-" * 30)
        
        # Test GetMe query
        self.test_query(
            "GetMe",
            """
            query GetMe {
                me {
                    id
                    name
                    email
                    hasPremiumAccess
                    subscriptionTier
                }
            }
            """,
            expected_fields=['me']
        )
        
        # Test ping
        self.test_query(
            "Ping",
            """
            query {
                ping
            }
            """,
            expected_fields=['ping']
        )
    
    def test_stock_queries(self):
        """Test stock-related queries"""
        print("\n📈 STOCK QUERIES TESTS")
        print("-" * 30)
        
        # Test GetStocks
        self.test_query(
            "GetStocks",
            """
            query GetStocks {
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
            """,
            expected_fields=['stocks']
        )
        
        # Test GetBeginnerFriendlyStocksAlt
        self.test_query(
            "GetBeginnerFriendlyStocksAlt",
            """
            query GetBeginnerFriendlyStocksAlt {
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
            """,
            expected_fields=['beginnerFriendlyStocks']
        )
    
    def test_swing_trading_queries(self):
        """Test swing trading queries"""
        print("\n🎯 SWING TRADING QUERIES TESTS")
        print("-" * 30)
        
        # Test GetSignals
        self.test_query(
            "GetSignals",
            """
            query GetSignals($minMlScore: Float, $isActive: Boolean, $limit: Int) {
                signals(
                    minMlScore: $minMlScore
                    isActive: $isActive
                    limit: $limit
                ) {
                    id
                    symbol
                    timeframe
                    triggeredAt
                    signalType
                    entryPrice
                    stopPrice
                    targetPrice
                    mlScore
                    thesis
                    riskRewardRatio
                    daysSinceTriggered
                    isLikedByUser
                    userLikeCount
                    features
                    isActive
                    isValidated
                    validationPrice
                    validationTimestamp
                    createdBy {
                        id
                        username
                        name
                    }
                }
            }
            """,
            variables={"minMlScore": 0.5, "isActive": True, "limit": 10},
            expected_fields=['signals']
        )
        
        # Test GetLeaderboard
        self.test_query(
            "GetLeaderboard",
            """
            query GetLeaderboard {
                leaderboard {
                    id
                    username
                    name
                    totalSignals
                    winRate
                    avgReturn
                    totalReturn
                    rank
                    traderScore {
                        id
                        totalSignals
                        winRate
                        avgReturn
                        totalReturn
                        sharpeRatio
                        maxDrawdown
                        lastUpdated
                    }
                }
            }
            """,
            expected_fields=['leaderboard']
        )
    
    def test_backtesting_queries(self):
        """Test backtesting queries"""
        print("\n📊 BACKTESTING QUERIES TESTS")
        print("-" * 30)
        
        # Test GetBacktestStrategies
        self.test_query(
            "GetBacktestStrategies",
            """
            query GetBacktestStrategies {
                backtestStrategies {
                    id
                    name
                    description
                    parameters
                    isActive
                    createdAt
                    updatedAt
                }
            }
            """,
            expected_fields=['backtestStrategies']
        )
        
        # Test GetBacktestResults
        self.test_query(
            "GetBacktestResults",
            """
            query GetBacktestResults {
                backtestResults {
                    id
                    strategyId
                    strategyName
                    startDate
                    endDate
                    initialCapital
                    finalCapital
                    totalReturn
                    totalReturnPercent
                    winRate
                    sharpeRatio
                    maxDrawdown
                    totalTrades
                    winningTrades
                    losingTrades
                    avgWin
                    avgLoss
                    profitFactor
                    createdAt
                }
            }
            """,
            expected_fields=['backtestResults']
        )
    
    def test_risk_management_queries(self):
        """Test risk management queries"""
        print("\n⚠️  RISK MANAGEMENT QUERIES TESTS")
        print("-" * 30)
        
        # Test CalculateTargetPrice
        self.test_query(
            "CalculateTargetPrice",
            """
            query CalculateTargetPrice($entryPrice: Float!, $stopPrice: Float!, $riskRewardRatio: Float) {
                calculateTargetPrice(
                    entryPrice: $entryPrice
                    stopPrice: $stopPrice
                    riskRewardRatio: $riskRewardRatio
                ) {
                    targetPrice
                    riskAmount
                    rewardAmount
                    riskRewardRatio
                    method
                }
            }
            """,
            variables={"entryPrice": 100.0, "stopPrice": 95.0, "riskRewardRatio": 2.0},
            expected_fields=['calculateTargetPrice']
        )
        
        # Test CalculatePositionSize
        self.test_query(
            "CalculatePositionSize",
            """
            query CalculatePositionSize($accountEquity: Float!, $entryPrice: Float!, $stopPrice: Float!, $riskPerTrade: Float) {
                calculatePositionSize(
                    accountEquity: $accountEquity
                    entryPrice: $entryPrice
                    stopPrice: $stopPrice
                    riskPerTrade: $riskPerTrade
                ) {
                    positionSize
                    dollarRisk
                    positionValue
                    positionPct
                    riskPerTradePct
                    method
                    riskPerShare
                    maxSharesFixedRisk
                    maxSharesPosition
                }
            }
            """,
            variables={"accountEquity": 10000.0, "entryPrice": 100.0, "stopPrice": 95.0, "riskPerTrade": 0.01},
            expected_fields=['calculatePositionSize']
        )
        
        # Test CalculateDynamicStop
        self.test_query(
            "CalculateDynamicStop",
            """
            query CalculateDynamicStop($entryPrice: Float!, $atr: Float!, $atrMultiplier: Float) {
                calculateDynamicStop(
                    entryPrice: $entryPrice
                    atr: $atr
                    atrMultiplier: $atrMultiplier
                ) {
                    stopPrice
                    stopDistance
                    riskPercentage
                    method
                    atrStop
                    srStop
                    pctStop
                }
            }
            """,
            variables={"entryPrice": 100.0, "atr": 2.0, "atrMultiplier": 1.5},
            expected_fields=['calculateDynamicStop']
        )
    
    def test_portfolio_queries(self):
        """Test portfolio queries"""
        print("\n💼 PORTFOLIO QUERIES TESTS")
        print("-" * 30)
        
        # Test GetPortfolioMetrics
        self.test_query(
            "GetPortfolioMetrics",
            """
            query GetPortfolioMetrics {
                portfolioMetrics {
                    totalValue
                    totalCost
                    totalReturn
                    totalReturnPercent
                    holdings {
                        symbol
                        companyName
                        shares
                        currentPrice
                        totalValue
                        costBasis
                        returnAmount
                        returnPercent
                        sector
                    }
                }
            }
            """,
            expected_fields=['portfolioMetrics']
        )
    
    def test_watchlist_queries(self):
        """Test watchlist queries"""
        print("\n👀 WATCHLIST QUERIES TESTS")
        print("-" * 30)
        
        # Test GetMyWatchlist
        self.test_query(
            "GetMyWatchlist",
            """
            query GetMyWatchlist {
                myWatchlist {
                    id
                    stock {
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
                    addedAt
                    notes
                    targetPrice
                }
            }
            """,
            expected_fields=['myWatchlist']
        )
    
    def test_advanced_screening(self):
        """Test advanced screening queries"""
        print("\n🔍 ADVANCED SCREENING TESTS")
        print("-" * 30)
        
        # Test GetAdvancedStockScreening
        self.test_query(
            "GetAdvancedStockScreening",
            """
            query GetAdvancedStockScreening($sector: String, $minMarketCap: Float, $minBeginnerScore: Int) {
                advancedStockScreening(
                    sector: $sector
                    minMarketCap: $minMarketCap
                    minBeginnerScore: $minBeginnerScore
                ) {
                    id
                    symbol
                    companyName
                    sector
                    currentPrice
                    marketCap
                    peRatio
                    dividendYield
                    volatility
                    debtRatio
                    beginnerFriendlyScore
                    dividendScore
                    reasoning
                    score
                    mlScore
                }
            }
            """,
            variables={"sector": "Technology", "minMarketCap": 1000000000, "minBeginnerScore": 80},
            expected_fields=['advancedStockScreening']
        )
    
    def test_rust_analysis(self):
        """Test Rust stock analysis queries"""
        print("\n🦀 RUST ANALYSIS TESTS")
        print("-" * 30)
        
        # Test GetRustStockAnalysis
        self.test_query(
            "GetRustStockAnalysis",
            """
            query GetRustStockAnalysis($symbol: String!) {
                rustStockAnalysis(symbol: $symbol) {
                    symbol
                    beginnerFriendlyScore
                    riskLevel
                    recommendation
                    technicalIndicators {
                        rsi
                        macd
                        macdSignal
                        macdHistogram
                        sma20
                        sma50
                        ema12
                        ema26
                        bollingerUpper
                        bollingerLower
                        bollingerMiddle
                    }
                    fundamentalAnalysis {
                        valuationScore
                        growthScore
                        stabilityScore
                        dividendScore
                        debtScore
                    }
                    reasoning
                }
            }
            """,
            variables={"symbol": "AAPL"},
            expected_fields=['rustStockAnalysis']
        )
    
    def test_mutations(self):
        """Test mutations"""
        print("\n🔄 MUTATION TESTS")
        print("-" * 30)
        
        # Test RunBacktest mutation
        self.test_query(
            "RunBacktest",
            """
            mutation RunBacktest($config: BacktestConfigType!) {
                runBacktest(config: $config) {
                    success
                    result {
                        id
                        strategyId
                        strategyName
                        startDate
                        endDate
                        initialCapital
                        finalCapital
                        totalReturn
                        totalReturnPercent
                        winRate
                        sharpeRatio
                        maxDrawdown
                        totalTrades
                        winningTrades
                        losingTrades
                        avgWin
                        avgLoss
                        profitFactor
                        equityCurve
                        dailyReturns
                        createdAt
                    }
                    error
                }
            }
            """,
            variables={
                "config": {
                    "strategyId": "1",
                    "startDate": "2023-01-01T00:00:00Z",
                    "endDate": "2023-12-31T23:59:59Z",
                    "initialCapital": 10000.0,
                    "commissionPerTrade": 1.0,
                    "slippagePct": 0.001,
                    "maxPositionSize": 0.1,
                    "riskPerTrade": 0.02,
                    "maxTradesPerDay": 5,
                    "maxOpenPositions": 3,
                    "parameters": {
                        "rsiPeriod": 14,
                        "oversoldThreshold": 30,
                        "overboughtThreshold": 70,
                        "stopLoss": 0.05,
                        "takeProfit": 0.10
                    }
                }
            },
            expected_fields=['runBacktest']
        )
    
    def print_final_results(self):
        """Print final test results"""
        print("\n" + "=" * 60)
        print("🎯 COMPREHENSIVE SYSTEM TEST RESULTS")
        print("=" * 60)
        
        total_tests = self.results['passed'] + self.results['failed']
        success_rate = (self.results['passed'] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        if self.results['errors']:
            print(f"\n🚨 Errors Found:")
            for error in self.results['errors']:
                print(f"   • {error}")
        
        if success_rate >= 95:
            print(f"\n🎉 EXCELLENT! System is ready for production!")
        elif success_rate >= 85:
            print(f"\n✅ GOOD! Minor issues to address before release.")
        else:
            print(f"\n⚠️  NEEDS WORK! Significant issues before release.")
        
        print(f"\n📅 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    tester = GraphQLSystemTester()
    tester.run_all_tests()
