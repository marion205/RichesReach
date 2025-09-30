#!/usr/bin/env python3
"""
Test GraphQL schema directly without HTTP server
Tests all GraphQL queries to ensure no schema errors
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from graphene.test import Client
from core.schema import schema

class GraphQLSchemaTester:
    def __init__(self):
        self.client = Client(schema)
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, error_msg: str = None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "error": error_msg
        }
        self.test_results.append(result)
        print(f"{status} {test_name}")
        if error_msg:
            print(f"   Error: {error_msg}")
    
    def test_query(self, query: str, variables: dict = None, test_name: str = None):
        """Test a GraphQL query"""
        if not test_name:
            test_name = f"Query: {query[:50]}..."
        
        try:
            result = self.client.execute(query, variables=variables or {})
            
            # Handle different result formats
            if isinstance(result, dict):
                if 'errors' in result and result['errors']:
                    error_msg = "; ".join([str(error) for error in result['errors']])
                    self.log_test(test_name, False, error_msg)
                    return False
                else:
                    self.log_test(test_name, True)
                    return True
            else:
                # Handle graphene.test.Client result format
                if hasattr(result, 'errors') and result.errors:
                    error_msg = "; ".join([str(error) for error in result.errors])
                    self.log_test(test_name, False, error_msg)
                    return False
                else:
                    self.log_test(test_name, True)
                    return True
                
        except Exception as e:
            self.log_test(test_name, False, str(e))
            return False
    
    def test_basic_queries(self):
        """Test basic GraphQL queries"""
        print("\n📊 Testing Basic Queries...")
        
        # Test 1: Ping query
        query = """
        query {
            ping
        }
        """
        self.test_query(query, test_name="Ping Query")
        
        # Test 2: Stocks query
        query = """
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
        """
        self.test_query(query, test_name="Stocks Query")
        
        # Test 3: Beginner Friendly Stocks query
        query = """
        query {
            beginnerFriendlyStocks {
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
        """
        self.test_query(query, test_name="Beginner Friendly Stocks Query")
    
    def test_advanced_queries(self):
        """Test advanced GraphQL queries"""
        print("\n🔍 Testing Advanced Queries...")
        
        # Test 1: Rust Stock Analysis
        query = """
        query {
            rustStockAnalysis(symbol: "AAPL") {
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
                    debtScore
                    dividendScore
                }
                reasoning
            }
        }
        """
        self.test_query(query, test_name="Rust Stock Analysis Query")
        
        # Test 2: Advanced Stock Screening
        query = """
        query {
            advancedStockScreening(sector: "Technology", minMarketCap: 1000000000) {
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
        """
        self.test_query(query, test_name="Advanced Stock Screening Query")
        
        # Test 3: My Watchlist
        query = """
        query {
            myWatchlist {
                id
                symbol
                companyName
                currentPrice
                changePercent
            }
        }
        """
        self.test_query(query, test_name="My Watchlist Query")
    
    def test_new_queries(self):
        """Test newly added queries"""
        print("\n🆕 Testing New Queries...")
        
        # Test 1: Crypto Prices
        query = """
        query {
            cryptoPrices(symbols: ["BTC", "ETH"]) {
                symbol
                price
                change24h
                changePercent24h
            }
        }
        """
        self.test_query(query, test_name="Crypto Prices Query")
        
        # Test 2: Portfolio Analysis
        query = """
        query {
            portfolioAnalysis {
                totalValue
                totalGainLoss
                totalGainLossPercent
                dailyChange
                dailyChangePercent
            }
        }
        """
        self.test_query(query, test_name="Portfolio Analysis Query")
        
        # Test 3: Stock Discussions
        query = """
        query {
            stockDiscussions(stockSymbol: "AAPL", limit: 5) {
                id
                content
                createdAt
                user {
                    username
                }
                stock {
                    symbol
                }
            }
        }
        """
        self.test_query(query, test_name="Stock Discussions Query")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting GraphQL Schema Tests")
        print("=" * 60)
        
        # Test all GraphQL queries
        self.test_basic_queries()
        self.test_advanced_queries()
        self.test_new_queries()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if "✅" in r["status"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if "❌" in result["status"]:
                    print(f"  - {result['test']}")
                    if result.get("error"):
                        print(f"    Error: {result['error']}")
        
        print("\n" + "=" * 60)
        
        if failed_tests == 0:
            print("🎉 ALL SCHEMA TESTS PASSED! Your GraphQL schema is ready!")
        else:
            print(f"⚠️  {failed_tests} schema tests failed. Please review the errors above.")
            sys.exit(1)

def main():
    """Main function"""
    tester = GraphQLSchemaTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
