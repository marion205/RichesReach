#!/usr/bin/env python3
"""
Mobile App Connectivity Test
Tests all new endpoints to ensure the mobile app can connect properly
"""

import requests
import json
import time
from typing import Dict, List, Any

class MobileConnectivityTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[Dict[str, Any]] = []
        
    def test_endpoint(self, name: str, url: str, method: str = "GET", payload: Dict = None) -> Dict[str, Any]:
        """Test a single endpoint"""
        try:
            full_url = f"{self.base_url}{url}"
            
            if method == "GET":
                response = requests.get(full_url, timeout=10)
            elif method == "POST":
                response = requests.post(full_url, json=payload, timeout=10)
            else:
                return {
                    "name": name,
                    "url": url,
                    "method": method,
                    "status": "error",
                    "error": f"Unsupported method: {method}"
                }
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    return {
                        "name": name,
                        "url": url,
                        "method": method,
                        "status": "success",
                        "response": data
                    }
                except json.JSONDecodeError:
                    return {
                        "name": name,
                        "url": url,
                        "method": method,
                        "status": "success",
                        "response": response.text[:100]
                    }
            else:
                return {
                    "name": name,
                    "url": url,
                    "method": method,
                    "status": "error",
                    "error": f"HTTP {response.status_code}: {response.text[:100]}"
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "name": name,
                "url": url,
                "method": method,
                "status": "error",
                "error": str(e)
            }
    
    def run_all_tests(self):
        """Run all endpoint tests"""
        print("🧪 Mobile App Connectivity Test")
        print("=" * 50)
        
        # Define all endpoints to test
        endpoints = [
            # AI Market Insights
            ("AI Market Insights", "/api/ai/market-insights/", "GET"),
            ("AI Symbol Insights (AAPL)", "/api/ai/symbol-insights/AAPL", "GET"),
            ("AI Portfolio Insights", "/api/ai/portfolio-insights/?symbols=AAPL,MSFT,GOOGL", "GET"),
            ("AI Market Regime", "/api/ai/market-regime/", "GET"),
            ("AI Sentiment Analysis", "/api/ai/sentiment-analysis/", "GET"),
            ("AI Volatility Forecast", "/api/ai/volatility-forecast/", "GET"),
            ("AI Trading Opportunities", "/api/ai/trading-opportunities/", "GET"),
            ("AI Market Alerts", "/api/ai/market-alerts/", "GET"),
            ("AI Sector Analysis", "/api/ai/sector-analysis/", "GET"),
            ("AI Risk Metrics", "/api/ai/risk-metrics/", "GET"),
            
            # Advanced Order Management
            ("Place Market Order", "/api/orders/place/", "POST", {"symbol": "AAPL", "side": "buy", "quantity": 10, "order_type": "market"}),
            ("Place Limit Order", "/api/orders/place/", "POST", {"symbol": "MSFT", "side": "buy", "quantity": 5, "order_type": "limit", "price": 300.0}),
            ("Place TWAP Order", "/api/orders/twap/", "POST", {"symbol": "GOOGL", "side": "buy", "quantity": 20, "order_type": "twap", "duration_minutes": 30}),
            ("Place VWAP Order", "/api/orders/vwap/", "POST", {"symbol": "AMZN", "side": "buy", "quantity": 15, "order_type": "vwap", "participation_rate": 0.15}),
            ("Place Iceberg Order", "/api/orders/iceberg/", "POST", {"symbol": "TSLA", "side": "buy", "quantity": 500, "order_type": "iceberg", "display_size": 100}),
            ("Place Bracket Order", "/api/orders/bracket/", "POST", {"symbol": "NVDA", "side": "buy", "quantity": 2, "order_type": "bracket", "price": 3300.0, "take_profit_price": 3500.0, "stop_loss_price": 3200.0}),
            ("Place OCO Order", "/api/orders/oco/", "POST", {"symbol": "META", "side": "buy", "quantity": 10, "order_type": "oco", "price": 380.0, "take_profit_price": 400.0, "stop_loss_price": 350.0}),
            ("Place Trailing Stop", "/api/orders/trailing-stop/", "POST", {"symbol": "NFLX", "side": "sell", "quantity": 3, "order_type": "trailing_stop", "trailing_percent": 0.02, "price": 450.0}),
            ("Get Order Analytics", "/api/orders/analytics/", "GET"),
            ("Get Position Summary", "/api/orders/positions/", "GET"),
            ("Get Risk Checks", "/api/orders/risk-checks/?symbol=AAPL&quantity=10&side=buy", "GET"),
            ("Get Execution Plans", "/api/orders/execution-plans/?order_type=twap", "GET"),
            
            # Education System
            ("Education Progress", "/api/education/progress/", "GET"),
            ("Education Analytics", "/api/education/analytics/", "GET"),
            ("Education League", "/api/education/league/bipoc_wealth_builders", "GET"),
            ("Available Lessons", "/api/education/lessons/", "GET"),
            ("Daily Quest", "/api/education/daily-quest/", "GET"),
            ("Start Lesson", "/api/education/start-lesson/", "POST", {"lesson_id": "lesson_options_basics"}),
            ("Submit Quiz", "/api/education/submit-quiz/", "POST", {"lesson_id": "lesson_options_basics", "answers": {"q1": "A", "q2": "B"}}),
            ("Start Simulation", "/api/education/start-simulation/", "POST", {"simulation_type": "options_trading"}),
            ("Execute Sim Trade", "/api/education/execute-sim-trade/", "POST", {"simulation_id": "sim_001", "action": "buy", "symbol": "AAPL", "quantity": 10}),
            ("Claim Streak Freeze", "/api/education/claim-streak-freeze/", "POST", {"user_id": "user_001"}),
            ("Process Voice Command", "/api/education/process-voice-command/", "POST", {"command": "explain options", "user_id": "user_001"}),
            
            # Compliance & Analytics
            ("Validate Content", "/api/education/compliance/validate-content/", "POST", {"content": "test content", "content_type": "lesson"}),
            ("User Profile", "/api/education/compliance/user-profile/user_001", "GET"),
            ("Check Access", "/api/education/compliance/check-access/", "POST", {"user_id": "user_001", "resource": "lesson_options_basics"}),
            ("Compliance Report", "/api/education/compliance/report/user_001", "GET"),
            ("Analytics Dashboard", "/api/education/analytics/dashboard/", "GET"),
            ("User Analytics", "/api/education/analytics/user-profile/user_001", "GET"),
            ("Content Analytics", "/api/education/analytics/content-analytics/lesson_options_basics", "GET"),
            ("Analytics Trends", "/api/education/analytics/trends/", "GET"),
            
            # Real-Time Notifications
            ("Subscribe Notifications", "/api/notifications/subscribe/", "POST", {"user_id": "user_001", "topics": ["trading", "education"]}),
            ("Get Notification Settings", "/api/notifications/settings/?user_id=user_001", "GET"),
            ("Update Notification Settings", "/api/notifications/settings/", "POST", {"user_id": "user_001", "settings": {"push": True, "email": False}}),
            ("Register Push Token", "/api/notifications/push-token/", "POST", {"user_id": "user_001", "token": "test_token"}),
            ("Send Notification", "/api/notifications/send/", "POST", {"user_id": "user_001", "title": "Test", "message": "Test notification"}),
            ("Get Notification History", "/api/notifications/history/?user_id=user_001&limit=10", "GET"),
            ("Test Push Notification", "/api/notifications/test-push/", "POST", {"user_id": "user_001"}),
            ("Clear All Notifications", "/api/notifications/clear-all/", "POST", {"user_id": "user_001"}),
            
            # Advanced Charting
            ("Candlestick Chart", "/api/charts/candlestick/AAPL", "GET"),
            ("Volume Chart", "/api/charts/volume/AAPL", "GET"),
            ("Line Chart", "/api/charts/line/AAPL", "GET"),
            ("Heatmap", "/api/charts/heatmap", "GET"),
            ("Correlation Matrix", "/api/charts/correlation", "GET"),
            ("Market Depth", "/api/charts/market-depth/AAPL", "GET"),
            ("Technical Indicators", "/api/charts/indicators/AAPL", "GET"),
            ("Chart Screener", "/api/charts/screener", "GET"),
            
            # Social Trading
            ("Trader Profile", "/api/social/trader/trader_001", "GET"),
            ("Leaderboard", "/api/social/leaderboard", "GET"),
            ("Social Feed", "/api/social/feed/user_001", "GET"),
            ("Follow Trader", "/api/social/follow", "POST", {"user_id": "user_001", "trader_id": "trader_001"}),
            ("Unfollow Trader", "/api/social/unfollow", "POST", {"user_id": "user_001", "trader_id": "trader_001"}),
            ("Copy Trade", "/api/social/copy-trade", "POST", {"user_id": "user_001", "trade_id": "trade_001"}),
            ("Search Traders", "/api/social/search-traders", "GET"),
            ("Trade Interactions", "/api/social/trade-interactions/trade_001", "GET"),
            ("Like Trade", "/api/social/like-trade", "POST", {"user_id": "user_001", "trade_id": "trade_001"}),
            ("Comment Trade", "/api/social/comment-trade", "POST", {"user_id": "user_001", "trade_id": "trade_001", "comment": "Great trade!"}),
            ("Trader Stats", "/api/social/trader-stats/trader_001", "GET"),
            ("Trending Traders", "/api/social/trending-traders", "GET"),
            ("Copy Performance", "/api/social/copy-performance/user_001", "GET"),
            
            # Portfolio Analytics
            ("Portfolio Overview", "/api/portfolio/overview/portfolio_001", "GET"),
            ("Portfolio Performance", "/api/portfolio/performance/portfolio_001", "GET"),
            ("Portfolio Risk", "/api/portfolio/risk/portfolio_001", "GET"),
            ("Portfolio Attribution", "/api/portfolio/attribution/portfolio_001", "GET"),
            ("Portfolio Correlation", "/api/portfolio/correlation/portfolio_001", "GET"),
            ("Tax Analysis", "/api/portfolio/tax-analysis/portfolio_001", "GET"),
            ("Rebalancing Suggestions", "/api/portfolio/rebalancing/portfolio_001", "GET"),
            ("Benchmark Comparison", "/api/portfolio/benchmark-comparison/portfolio_001", "GET"),
            ("Scenario Analysis", "/api/portfolio/scenario-analysis/portfolio_001", "GET"),
            ("Portfolio Optimization", "/api/portfolio/optimization/portfolio_001", "GET"),
            
            # HFT System
            ("HFT Performance", "/api/hft/performance/", "GET"),
            ("HFT Positions", "/api/hft/positions/", "GET"),
            ("HFT Strategies", "/api/hft/strategies/", "GET"),
            ("Execute HFT Strategy", "/api/hft/execute-strategy/", "POST", {"strategy": "momentum", "symbol": "AAPL"}),
            ("HFT Place Order", "/api/hft/place-order/", "POST", {"symbol": "AAPL", "side": "buy", "quantity": 100, "order_type": "market"}),
            ("HFT Live Stream", "/api/hft/live-stream/", "GET"),
            
            # Voice AI Trading
            ("Process Voice Command", "/api/voice-trading/process-command/", "POST", {"command": "buy 10 shares of AAPL", "user_id": "user_001"}),
            ("Voice Help Commands", "/api/voice-trading/help-commands/", "GET"),
            ("Create Voice Session", "/api/voice-trading/create-session/", "POST", {"user_id": "user_001"}),
            ("Voice Session", "/api/voice-trading/session/session_001", "GET"),
            ("Parse Voice Command", "/api/voice-trading/parse-command/", "POST", {"command": "buy 10 shares of AAPL"}),
            ("Available Symbols", "/api/voice-trading/available-symbols/", "GET"),
            ("Command Examples", "/api/voice-trading/command-examples/", "GET"),
            
            # AI Regime Detection
            ("Current Regime", "/api/regime-detection/current-regime/", "GET"),
            ("Regime History", "/api/regime-detection/history/", "GET"),
            ("Regime Predictions", "/api/regime-detection/predictions/", "GET"),
            
            # Sentiment Analysis
            ("Sentiment Analysis (AAPL)", "/api/sentiment-analysis/AAPL", "GET"),
            ("Sentiment Analysis (MSFT)", "/api/sentiment-analysis/MSFT", "GET"),
            ("Sentiment Analysis (GOOGL)", "/api/sentiment-analysis/GOOGL", "GET"),
            
            # ML Pick Generation
            ("ML Picks (SAFE)", "/api/ml-picks/generate/SAFE", "GET"),
            ("ML Picks (AGGRESSIVE)", "/api/ml-picks/generate/AGGRESSIVE", "GET"),
            ("ML Picks (CUSTOM)", "/api/ml-picks/generate/CUSTOM", "GET"),
            
            # Advanced Mobile Features
            ("Gesture Trade", "/api/mobile/gesture-trade/", "POST", {"gesture": "swipe_up", "symbol": "AAPL", "action": "buy"}),
            ("Switch Mode", "/api/mobile/switch-mode/", "POST", {"mode": "day_trading"}),
            ("Mobile Settings", "/api/mobile/settings/", "GET"),
            ("Mobile Performance", "/api/mobile/performance/", "GET"),
            
            # Voice AI
            ("Available Voices", "/api/voice-ai/voices/", "GET"),
            ("Synthesize Speech", "/api/voice-ai/synthesize/", "POST", {"text": "Hello, this is a test", "voice": "en-US-Standard-A"}),
            ("Voice Settings", "/api/voice-ai/settings/", "GET"),
            ("Update Voice Settings", "/api/voice-ai/settings/", "POST", {"voice": "en-US-Standard-A", "rate": 1.0, "pitch": 1.0}),
            
            # GraphQL
            ("GraphQL Schema", "/graphql/", "POST", {"query": "{ __schema { types { name } } }"}),
            ("GraphQL Health", "/graphql/", "POST", {"query": "{ health { status } }"}),
        ]
        
        # Run tests
        for i, endpoint in enumerate(endpoints):
            name, url, method = endpoint[:3]
            payload = endpoint[3] if len(endpoint) > 3 else None
            
            print(f"[{i+1:3d}/{len(endpoints)}] Testing {name}...")
            result = self.test_endpoint(name, url, method, payload)
            self.results.append(result)
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.1)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        success_count = sum(1 for r in self.results if r["status"] == "success")
        error_count = sum(1 for r in self.results if r["status"] == "error")
        total_count = len(self.results)
        
        print("\n" + "=" * 50)
        print("📊 MOBILE CONNECTIVITY TEST SUMMARY")
        print("=" * 50)
        print(f"✅ Total Tests: {total_count}")
        print(f"✅ Successful: {success_count}")
        print(f"❌ Errors: {error_count}")
        print(f"✅ Success Rate: {(success_count/total_count)*100:.1f}%")
        
        if error_count > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.results:
                if result["status"] == "error":
                    print(f"   - {result['name']}: {result['error']}")
        
        print("\n🎯 ENDPOINT CATEGORIES TESTED:")
        categories = [
            "AI Market Insights",
            "Advanced Order Management", 
            "Education System",
            "Compliance & Analytics",
            "Real-Time Notifications",
            "Advanced Charting",
            "Social Trading",
            "Portfolio Analytics",
            "HFT System",
            "Voice AI Trading",
            "AI Regime Detection",
            "Sentiment Analysis",
            "ML Pick Generation",
            "Advanced Mobile Features",
            "Voice AI",
            "GraphQL"
        ]
        
        for category in categories:
            print(f"✅ {category}")
        
        if success_count == total_count:
            print("\n🏆 ALL TESTS PASSED!")
            print("📱 Mobile app can connect to all new endpoints!")
        else:
            print(f"\n⚠️  {error_count} tests failed - check server logs")

if __name__ == "__main__":
    tester = MobileConnectivityTester()
    tester.run_all_tests()
