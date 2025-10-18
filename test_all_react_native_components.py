#!/usr/bin/env python3
"""
Comprehensive GraphQL Testing for All React Native Components
Tests every endpoint that each component might use
"""
import requests
import json
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuration
BASE_URL = "http://192.168.1.236:8000"
GRAPHQL_URL = f"{BASE_URL}/graphql/"
REST_AUTH_URL = f"{BASE_URL}/api/auth/login/"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"

class ComponentTester:
    def __init__(self):
        self.token = None
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "ReactNative-ComponentTest/1.0"
        })
        self.results = {}
    
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def get_clean_token(self):
        """Get a clean JWT token from Django"""
        try:
            result = subprocess.run([
                "python3", "manage.py", "shell", "-c",
                f"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings_dev_real')
import django
django.setup()
from django.contrib.auth import get_user_model
from graphql_jwt.shortcuts import get_token
U = get_user_model()
user = U.objects.get(email='{TEST_EMAIL}')
token = get_token(user)
print(token)
"""
            ], cwd="/Users/marioncollins/RichesReach/backend/backend/backend/backend", 
            capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.startswith('eyJ'):  # JWT tokens start with eyJ
                        return line.strip()
            return None
        except Exception as e:
            self.log(f"Error getting token: {e}", "ERROR")
            return None
    
    def make_request(self, query, variables=None, use_auth=True):
        """Make a GraphQL request"""
        headers = {}
        if use_auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        try:
            response = self.session.post(GRAPHQL_URL, json=payload, headers=headers, timeout=10)
            return response.json(), response.status_code
        except Exception as e:
            self.log(f"Request failed: {e}", "ERROR")
            return None, 0
    
    def test_authentication(self):
        """Test authentication methods"""
        self.log("🔐 Testing Authentication Methods...")
        
        # Test REST authentication
        try:
            response = requests.post(REST_AUTH_URL, json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('token'):
                    self.token = data['token']
                    self.log("✅ REST authentication successful")
                    return True
        except Exception as e:
            self.log(f"REST auth failed: {e}", "ERROR")
        
        # Fallback to Django shell token
        self.token = self.get_clean_token()
        if self.token:
            self.log("✅ Got token via Django shell")
            return True
        
        self.log("❌ All authentication methods failed", "ERROR")
        return False
    
    def test_component(self, component_name: str, queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test all queries for a specific component"""
        self.log(f"\n🧪 Testing {component_name} Component...")
        
        component_results = {
            "component": component_name,
            "queries": [],
            "success_count": 0,
            "total_count": len(queries)
        }
        
        for query_info in queries:
            query_name = query_info["name"]
            query = query_info["query"]
            variables = query_info.get("variables")
            expected_fields = query_info.get("expected_fields", [])
            
            self.log(f"  Testing {query_name}...")
            
            data, status = self.make_request(query, variables)
            
            query_result = {
                "name": query_name,
                "success": False,
                "error": None,
                "data_preview": None
            }
            
            if data and "data" in data and data["data"]:
                query_result["success"] = True
                query_result["data_preview"] = str(data["data"])[:100] + "..." if len(str(data["data"])) > 100 else str(data["data"])
                component_results["success_count"] += 1
                self.log(f"    ✅ {query_name} - SUCCESS")
            else:
                if data and "errors" in data:
                    query_result["error"] = data["errors"][0].get("message", "Unknown error")
                    self.log(f"    ❌ {query_name} - FAILED: {query_result['error']}")
                else:
                    query_result["error"] = "No data returned"
                    self.log(f"    ❌ {query_name} - FAILED: No data returned")
            
            component_results["queries"].append(query_result)
        
        success_rate = (component_results["success_count"] / component_results["total_count"]) * 100
        self.log(f"  📊 {component_name}: {component_results['success_count']}/{component_results['total_count']} queries successful ({success_rate:.1f}%)")
        
        return component_results
    
    def run_all_component_tests(self):
        """Run tests for all React Native components"""
        self.log("🚀 Starting Comprehensive React Native Component Testing")
        self.log("=" * 70)
        
        # Authenticate first
        if not self.test_authentication():
            self.log("❌ Authentication failed, cannot proceed with tests", "ERROR")
            return False
        
        # Define all component tests
        component_tests = {
            "AuthenticationScreen": [
                {
                    "name": "Token Authentication",
                    "query": """
                    mutation TokenAuth($email: String!, $password: String!) {
                        tokenAuth(email: $email, password: $password) {
                            token
                        }
                    }
                    """,
                    "variables": {"email": TEST_EMAIL, "password": TEST_PASSWORD},
                    "expected_fields": ["tokenAuth"]
                },
                {
                    "name": "Verify Token",
                    "query": """
                    mutation VerifyToken($token: String!) {
                        verifyToken(token: $token) {
                            payload
                        }
                    }
                    """,
                    "variables": {"token": self.token},
                    "expected_fields": ["verifyToken"]
                }
            ],
            
            "UserProfileScreen": [
                {
                    "name": "Get User Profile",
                    "query": """
                    query Me {
                        me {
                            id
                            email
                            username
                            name
                            profilePic
                            hasPremiumAccess
                            subscriptionTier
                        }
                    }
                    """,
                    "expected_fields": ["id", "email", "username", "name"]
                },
                {
                    "name": "Alert Preferences",
                    "query": """
                    query AlertPreferences {
                        alertPreferences
                    }
                    """,
                    "expected_fields": ["alertPreferences"]
                }
            ],
            
            "WatchlistScreen": [
                {
                    "name": "Get Watchlist",
                    "query": """
                    query MyWatchlist {
                        myWatchlist {
                            id
                            stock {
                                symbol
                                companyName
                                currentPrice
                                changePercent
                            }
                            notes
                            addedAt
                        }
                    }
                    """,
                    "expected_fields": ["myWatchlist"]
                },
                {
                    "name": "Add to Watchlist",
                    "query": """
                    mutation AddToWatchlist($symbol: String!, $companyName: String, $notes: String) {
                        addToWatchlist(symbol: $symbol, companyName: $companyName, notes: $notes) {
                            success
                            message
                        }
                    }
                    """,
                    "variables": {"symbol": "NVDA", "companyName": "NVIDIA Corporation", "notes": "Component test"},
                    "expected_fields": ["addToWatchlist"]
                },
                {
                    "name": "Remove from Watchlist",
                    "query": """
                    mutation RemoveFromWatchlist($symbol: String!) {
                        removeFromWatchlist(symbol: $symbol) {
                            success
                            message
                        }
                    }
                    """,
                    "variables": {"symbol": "NVDA"},
                    "expected_fields": ["removeFromWatchlist"]
                }
            ],
            
            "StockScreen": [
                {
                    "name": "Get Stock Details",
                    "query": """
                    query StockDetails {
                        stocks {
                            symbol
                            companyName
                            currentPrice
                            changePercent
                            marketCap
                            peRatio
                            dividendYield
                            sector
                        }
                    }
                    """,
                    "expected_fields": ["stocks"]
                },
                {
                    "name": "Get Stock Chart Data",
                    "query": """
                    query StockChartData($symbol: String!, $timeframe: String) {
                        stockChartData(symbol: $symbol, timeframe: $timeframe) {
                            symbol
                            interval
                            limit
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
                            indicators {
                                RSI14
                                MACD
                            }
                        }
                    }
                    """,
                    "variables": {"symbol": "AAPL", "timeframe": "1D"},
                    "expected_fields": ["stockChartData"]
                },
                {
                    "name": "Get Stock Discussions",
                    "query": """
                    query StockDiscussions($limit: Int) {
                        stockDiscussions(limit: $limit) {
                            id
                            type
                            title
                            content
                            user {
                                name
                            }
                            createdAt
                            likesCount
                            commentsCount
                        }
                    }
                    """,
                    "variables": {"limit": 5},
                    "expected_fields": ["stockDiscussions"]
                }
            ],
            
            "PortfolioScreen": [
                {
                    "name": "Get Portfolios",
                    "query": """
                    query MyPortfolios {
                        myPortfolios {
                            totalPortfolios
                            totalValue
                            portfolios {
                                id
                                name
                                totalValue
                                totalReturnPercent
                                holdingsCount
                                holdings {
                                    id
                                    stock {
                                        symbol
                                        companyName
                                    }
                                    shares
                                    averagePrice
                                    currentPrice
                                    totalValue
                                }
                            }
                        }
                    }
                    """,
                    "expected_fields": ["myPortfolios"]
                },
                {
                    "name": "Portfolio Metrics",
                    "query": """
                    query PortfolioMetrics {
                        portfolioMetrics {
                            totalValue
                            totalCost
                            totalReturn
                            totalReturnPercent
                            totalGainLoss
                            totalGainLossPercent
                            dailyChange
                            dailyChangePercent
                            volatility
                            sharpeRatio
                            maxDrawdown
                            beta
                            alpha
                        }
                    }
                    """,
                    "expected_fields": ["portfolioMetrics"]
                }
            ],
            
            "MarketScreen": [
                {
                    "name": "Get Market Data",
                    "query": """
                    query MarketData {
                        marketData {
                            symbol
                            price
                            change
                            changePercent
                            volume
                            marketCap
                        }
                    }
                    """,
                    "expected_fields": ["marketData"]
                },
                {
                    "name": "Get Market News",
                    "query": """
                    query MarketNews($limit: Int) {
                        marketNews(limit: $limit) {
                            id
                            title
                            summary
                            source
                            timestamp
                            sentiment
                            impact
                            relatedSymbols
                            category
                        }
                    }
                    """,
                    "variables": {"limit": 10},
                    "expected_fields": ["marketNews"]
                }
            ],
            
            "AIScreen": [
                {
                    "name": "Get AI Recommendations",
                    "query": """
                    query AIRecommendations {
                        aiRecommendations {
                            buyRecommendations {
                                symbol
                                confidence
                                reasoning
                                targetPrice
                            }
                            sellRecommendations {
                                symbol
                                confidence
                                reasoning
                                targetPrice
                            }
                        }
                    }
                    """,
                    "expected_fields": ["aiRecommendations"]
                },
                {
                    "name": "Get Portfolio Optimization",
                    "query": """
                    query PortfolioOptimization {
                        portfolioOptimization(symbols: ["AAPL", "GOOGL", "MSFT"])
                    }
                    """,
                    "expected_fields": ["portfolioOptimization"]
                }
            ],
            
            "OptionsScreen": [
                {
                    "name": "Get Option Orders",
                    "query": """
                    query OptionOrders {
                        optionOrders {
                            id
                            symbol
                            optionType
                            strike
                            expiration
                            side
                            quantity
                            orderType
                            limitPrice
                            timeInForce
                            status
                            filledPrice
                            filledQuantity
                            createdAt
                        }
                    }
                    """,
                    "expected_fields": ["optionOrders"]
                },
                {
                    "name": "Get AI Recommendations",
                    "query": """
                    query AIRecommendations {
                        aiRecommendations {
                            buyRecommendations {
                                symbol
                                confidence
                                reasoning
                                targetPrice
                            }
                            sellRecommendations {
                                symbol
                                confidence
                                reasoning
                                targetPrice
                            }
                        }
                    }
                    """,
                    "expected_fields": ["aiRecommendations"]
                }
            ],
            
            "CryptoScreen": [
                {
                    "name": "Get Crypto Prices",
                    "query": """
                    query CryptoPrices {
                        cryptoPrices {
                            id
                            cryptocurrency {
                                symbol
                                name
                            }
                            priceUsd
                            priceBtc
                            volume24h
                            marketCap
                            priceChange24h
                            priceChangePercentage24h
                            timestamp
                        }
                    }
                    """,
                    "expected_fields": ["cryptoPrices"]
                },
                {
                    "name": "Get Crypto Price",
                    "query": """
                    query CryptoPrice($symbol: String!) {
                        cryptoPrice(symbol: $symbol) {
                            id
                            cryptocurrency {
                                symbol
                                name
                            }
                            priceUsd
                            priceBtc
                            volume24h
                            marketCap
                            priceChange24h
                            priceChangePercentage24h
                            rsi14
                            macd
                            timestamp
                        }
                    }
                    """,
                    "variables": {"symbol": "BTC"},
                    "expected_fields": ["cryptoPrice"]
                }
            ],
            
            "NotificationsScreen": [
                {
                    "name": "Get Notifications",
                    "query": """
                    query Notifications {
                        notifications {
                            id
                            type
                            title
                            message
                            isRead
                            createdAt
                        }
                    }
                    """,
                    "expected_fields": ["notifications"]
                }
            ],
            
            "SearchScreen": [
                {
                    "name": "Get Stocks",
                    "query": """
                    query Stocks {
                        stocks {
                            symbol
                            companyName
                            currentPrice
                            changePercent
                            marketCap
                            sector
                        }
                    }
                    """,
                    "expected_fields": ["stocks"]
                },
                {
                    "name": "Get Market Data",
                    "query": """
                    query MarketData {
                        marketData {
                            symbol
                            price
                            change
                            changePercent
                            volume
                            marketCap
                        }
                    }
                    """,
                    "expected_fields": ["marketData"]
                }
            ],
            
            "AnalyticsScreen": [
                {
                    "name": "Get Portfolio Metrics",
                    "query": """
                    query PortfolioMetrics {
                        portfolioMetrics {
                            totalValue
                            totalCost
                            totalReturn
                            totalReturnPercent
                            totalGainLoss
                            totalGainLossPercent
                            dailyChange
                            dailyChangePercent
                            volatility
                            sharpeRatio
                            maxDrawdown
                            beta
                            alpha
                        }
                    }
                    """,
                    "expected_fields": ["portfolioMetrics"]
                },
                {
                    "name": "Get Market News",
                    "query": """
                    query MarketNews {
                        marketNews {
                            id
                            title
                            summary
                            source
                            timestamp
                            sentiment
                            impact
                            relatedSymbols
                            category
                        }
                    }
                    """,
                    "expected_fields": ["marketNews"]
                }
            ]
        }
        
        # Run tests for each component
        all_results = []
        total_queries = 0
        total_successful = 0
        
        for component_name, queries in component_tests.items():
            result = self.test_component(component_name, queries)
            all_results.append(result)
            total_queries += result["total_count"]
            total_successful += result["success_count"]
        
        # Generate comprehensive report
        self.generate_report(all_results, total_queries, total_successful)
        
        return total_successful == total_queries
    
    def generate_report(self, results: List[Dict], total_queries: int, total_successful: int):
        """Generate a comprehensive test report"""
        self.log("\n" + "=" * 70)
        self.log("📊 COMPREHENSIVE COMPONENT TEST REPORT")
        self.log("=" * 70)
        
        overall_success_rate = (total_successful / total_queries) * 100 if total_queries > 0 else 0
        
        self.log(f"Overall Success Rate: {total_successful}/{total_queries} ({overall_success_rate:.1f}%)")
        self.log("")
        
        # Component breakdown
        for result in results:
            component_name = result["component"]
            success_count = result["success_count"]
            total_count = result["total_count"]
            success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
            
            status = "✅" if success_count == total_count else "⚠️" if success_rate >= 80 else "❌"
            self.log(f"{status} {component_name}: {success_count}/{total_count} ({success_rate:.1f}%)")
            
            # Show failed queries
            failed_queries = [q for q in result["queries"] if not q["success"]]
            if failed_queries:
                for failed in failed_queries:
                    self.log(f"    ❌ {failed['name']}: {failed['error']}")
        
        self.log("")
        self.log("🔧 RECOMMENDATIONS:")
        
        if overall_success_rate >= 95:
            self.log("🎉 Excellent! Your React Native app should work seamlessly with the local server.")
        elif overall_success_rate >= 80:
            self.log("✅ Good! Most components will work. Fix the failing queries for 100% compatibility.")
        elif overall_success_rate >= 60:
            self.log("⚠️  Moderate. Several components need fixes. Focus on the most critical ones first.")
        else:
            self.log("❌ Poor. Many components need fixes. Start with authentication and core features.")
        
        # Save detailed report to file
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "overall_success_rate": overall_success_rate,
            "total_queries": total_queries,
            "total_successful": total_successful,
            "components": results
        }
        
        with open("/Users/marioncollins/RichesReach/component_test_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        self.log(f"\n📄 Detailed report saved to: component_test_report.json")

def main():
    tester = ComponentTester()
    success = tester.run_all_component_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
