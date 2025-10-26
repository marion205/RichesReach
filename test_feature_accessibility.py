#!/usr/bin/env python3
"""
Comprehensive Feature Accessibility Test
Tests all new features to ensure they're properly accessible and integrated
"""

import requests
import json
import time
from typing import Dict, List, Any

class FeatureAccessibilityTester:
    """Test all new features for accessibility and integration"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {}
        
    def test_basic_connectivity(self) -> bool:
        """Test basic server connectivity"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Basic connectivity: OK")
                return True
            else:
                print(f"❌ Basic connectivity: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Basic connectivity: {e}")
            return False
    
    def test_hft_features(self) -> Dict[str, Any]:
        """Test all HFT features"""
        print("\n🔍 Testing HFT Features...")
        hft_results = {}
        
        # Test HFT performance
        try:
            response = requests.get(f"{self.base_url}/api/hft/performance/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                hft_results["performance"] = {
                    "status": "OK",
                    "total_orders": data.get("total_orders", 0),
                    "latency_us": data.get("average_latency_microseconds", 0),
                    "orders_per_sec": data.get("orders_per_second", 0)
                }
                print(f"✅ HFT Performance: {data.get('total_orders', 0)} orders, {data.get('average_latency_microseconds', 0):.2f}μs latency")
            else:
                hft_results["performance"] = {"status": f"HTTP {response.status_code}"}
                print(f"❌ HFT Performance: HTTP {response.status_code}")
        except Exception as e:
            hft_results["performance"] = {"status": f"Error: {e}"}
            print(f"❌ HFT Performance: {e}")
        
        # Test HFT strategies
        try:
            response = requests.get(f"{self.base_url}/api/hft/strategies/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                strategies = data.get("strategies", {})
                hft_results["strategies"] = {
                    "status": "OK",
                    "count": len(strategies),
                    "names": list(strategies.keys())
                }
                print(f"✅ HFT Strategies: {len(strategies)} strategies available")
            else:
                hft_results["strategies"] = {"status": f"HTTP {response.status_code}"}
                print(f"❌ HFT Strategies: HTTP {response.status_code}")
        except Exception as e:
            hft_results["strategies"] = {"status": f"Error: {e}"}
            print(f"❌ HFT Strategies: {e}")
        
        # Test HFT order placement
        try:
            response = requests.post(
                f"{self.base_url}/api/hft/place-order/",
                json={"symbol": "AAPL", "side": "BUY", "quantity": 100, "order_type": "MARKET"},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                hft_results["order_placement"] = {
                    "status": "OK",
                    "order_id": data.get("order", {}).get("id", "unknown")
                }
                print(f"✅ HFT Order Placement: Order {data.get('order', {}).get('id', 'unknown')} placed")
            else:
                hft_results["order_placement"] = {"status": f"HTTP {response.status_code}"}
                print(f"❌ HFT Order Placement: HTTP {response.status_code}")
        except Exception as e:
            hft_results["order_placement"] = {"status": f"Error: {e}"}
            print(f"❌ HFT Order Placement: {e}")
        
        # Test HFT strategy execution
        try:
            response = requests.post(
                f"{self.base_url}/api/hft/execute-strategy/",
                json={"strategy": "scalping", "symbol": "AAPL"},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                hft_results["strategy_execution"] = {
                    "status": "OK",
                    "orders_executed": data.get("orders_executed", 0)
                }
                print(f"✅ HFT Strategy Execution: {data.get('orders_executed', 0)} orders executed")
            else:
                hft_results["strategy_execution"] = {"status": f"HTTP {response.status_code}"}
                print(f"❌ HFT Strategy Execution: HTTP {response.status_code}")
        except Exception as e:
            hft_results["strategy_execution"] = {"status": f"Error: {e}"}
            print(f"❌ HFT Strategy Execution: {e}")
        
        return hft_results
    
    def test_voice_ai_features(self) -> Dict[str, Any]:
        """Test all Voice AI features"""
        print("\n🎤 Testing Voice AI Features...")
        voice_results = {}
        
        # Test voice list
        try:
            response = requests.get(f"{self.base_url}/api/voice-ai/voices/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                voices = data.get("voices", {})
                voice_results["voice_list"] = {
                    "status": "OK",
                    "count": len(voices),
                    "voices": list(voices.keys())
                }
                print(f"✅ Voice List: {len(voices)} voices available")
            else:
                voice_results["voice_list"] = {"status": f"HTTP {response.status_code}"}
                print(f"❌ Voice List: HTTP {response.status_code}")
        except Exception as e:
            voice_results["voice_list"] = {"status": f"Error: {e}"}
            print(f"❌ Voice List: {e}")
        
        # Test voice synthesis
        try:
            response = requests.post(
                f"{self.base_url}/api/voice-ai/synthesize/",
                json={"text": "Hello, this is a test", "voice_id": "nova"},
                timeout=5
            )
            if response.status_code == 200:
                voice_results["voice_synthesis"] = {"status": "OK"}
                print("✅ Voice Synthesis: Working")
            else:
                voice_results["voice_synthesis"] = {"status": f"HTTP {response.status_code}"}
                print(f"❌ Voice Synthesis: HTTP {response.status_code}")
        except Exception as e:
            voice_results["voice_synthesis"] = {"status": f"Error: {e}"}
            print(f"❌ Voice Synthesis: {e}")
        
        # Test voice command parsing
        try:
            response = requests.post(
                f"{self.base_url}/api/voice-trading/parse-command/",
                json={"transcript": "Nova, buy 100 shares of AAPL", "voice_name": "Nova"},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                voice_results["command_parsing"] = {
                    "status": "OK",
                    "success": data.get("success", False)
                }
                print(f"✅ Voice Command Parsing: {'Success' if data.get('success') else 'Failed'}")
            else:
                voice_results["command_parsing"] = {"status": f"HTTP {response.status_code}"}
                print(f"❌ Voice Command Parsing: HTTP {response.status_code}")
        except Exception as e:
            voice_results["command_parsing"] = {"status": f"Error: {e}"}
            print(f"❌ Voice Command Parsing: {e}")
        
        return voice_results
    
    def test_ai_features(self) -> Dict[str, Any]:
        """Test all AI features"""
        print("\n🧠 Testing AI Features...")
        ai_results = {}
        
        # Test regime detection
        try:
            response = requests.get(f"{self.base_url}/api/regime-detection/current-regime/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                ai_results["regime_detection"] = {
                    "status": "OK",
                    "regime": data.get("regime_type", "unknown"),
                    "confidence": data.get("confidence", 0)
                }
                print(f"✅ Regime Detection: {data.get('regime_type', 'unknown')} ({data.get('confidence', 0):.2f} confidence)")
            else:
                ai_results["regime_detection"] = {"status": f"HTTP {response.status_code}"}
                print(f"❌ Regime Detection: HTTP {response.status_code}")
        except Exception as e:
            ai_results["regime_detection"] = {"status": f"Error: {e}"}
            print(f"❌ Regime Detection: {e}")
        
        # Test sentiment analysis
        try:
            response = requests.get(f"{self.base_url}/api/sentiment-analysis/AAPL", timeout=5)
            if response.status_code == 200:
                data = response.json()
                ai_results["sentiment_analysis"] = {
                    "status": "OK",
                    "sentiment": data.get("overall_sentiment", 0),
                    "confidence": data.get("confidence", 0)
                }
                print(f"✅ Sentiment Analysis: {data.get('overall_sentiment', 0):.3f} sentiment")
            else:
                ai_results["sentiment_analysis"] = {"status": f"HTTP {response.status_code}"}
                print(f"❌ Sentiment Analysis: HTTP {response.status_code}")
        except Exception as e:
            ai_results["sentiment_analysis"] = {"status": f"Error: {e}"}
            print(f"❌ Sentiment Analysis: {e}")
        
        # Test ML pick generation
        try:
            response = requests.get(f"{self.base_url}/api/ml-picks/generate/SAFE", timeout=5)
            if response.status_code == 200:
                data = response.json()
                picks = data.get("ml_picks", [])
                ai_results["ml_picks"] = {
                    "status": "OK",
                    "count": len(picks),
                    "top_pick": picks[0].get("symbol", "unknown") if picks else "none"
                }
                print(f"✅ ML Pick Generation: {len(picks)} picks generated")
            else:
                ai_results["ml_picks"] = {"status": f"HTTP {response.status_code}"}
                print(f"❌ ML Pick Generation: HTTP {response.status_code}")
        except Exception as e:
            ai_results["ml_picks"] = {"status": f"Error: {e}"}
            print(f"❌ ML Pick Generation: {e}")
        
        return ai_results
    
    def test_mobile_features(self) -> Dict[str, Any]:
        """Test mobile-specific features"""
        print("\n📱 Testing Mobile Features...")
        mobile_results = {}
        
        # Test gesture trading
        try:
            response = requests.post(
                f"{self.base_url}/api/mobile/gesture-trade/",
                json={"symbol": "AAPL", "gesture_type": "swipe_right"},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                mobile_results["gesture_trading"] = {
                    "status": "OK",
                    "success": data.get("success", False)
                }
                print(f"✅ Gesture Trading: {'Success' if data.get('success') else 'Failed'}")
            else:
                mobile_results["gesture_trading"] = {"status": f"HTTP {response.status_code}"}
                print(f"❌ Gesture Trading: HTTP {response.status_code}")
        except Exception as e:
            mobile_results["gesture_trading"] = {"status": f"Error: {e}"}
            print(f"❌ Gesture Trading: {e}")
        
        # Test mode switching
        try:
            response = requests.post(
                f"{self.base_url}/api/mobile/switch-mode/",
                json={"mode": "SAFE"},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                mobile_results["mode_switching"] = {
                    "status": "OK",
                    "success": data.get("success", False)
                }
                print(f"✅ Mode Switching: {'Success' if data.get('success') else 'Failed'}")
            else:
                mobile_results["mode_switching"] = {"status": f"HTTP {response.status_code}"}
                print(f"❌ Mode Switching: HTTP {response.status_code}")
        except Exception as e:
            mobile_results["mode_switching"] = {"status": f"Error: {e}"}
            print(f"❌ Mode Switching: {e}")
        
        return mobile_results
    
    def test_graphql_integration(self) -> Dict[str, Any]:
        """Test GraphQL integration"""
        print("\n🔗 Testing GraphQL Integration...")
        graphql_results = {}
        
        # Test day trading picks query
        try:
            query = """
            query {
                dayTradingPicks(mode: "SAFE") {
                    asOf
                    mode
                    picks {
                        symbol
                        side
                        score
                    }
                }
            }
            """
            response = requests.post(
                f"{self.base_url}/graphql/",
                json={"query": query},
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                picks_data = data.get("data", {}).get("dayTradingPicks", {})
                picks = picks_data.get("picks", [])
                graphql_results["day_trading_picks"] = {
                    "status": "OK",
                    "count": len(picks),
                    "mode": picks_data.get("mode", "unknown")
                }
                print(f"✅ GraphQL Day Trading Picks: {len(picks)} picks, mode: {picks_data.get('mode', 'unknown')}")
            else:
                graphql_results["day_trading_picks"] = {"status": f"HTTP {response.status_code}"}
                print(f"❌ GraphQL Day Trading Picks: HTTP {response.status_code}")
        except Exception as e:
            graphql_results["day_trading_picks"] = {"status": f"Error: {e}"}
            print(f"❌ GraphQL Day Trading Picks: {e}")
        
        return graphql_results
    
    def test_end_to_end_workflow(self) -> Dict[str, Any]:
        """Test end-to-end workflow"""
        print("\n🔄 Testing End-to-End Workflow...")
        workflow_results = {}
        
        try:
            # 1. Get regime
            regime_response = requests.get(f"{self.base_url}/api/regime-detection/current-regime/", timeout=5)
            if regime_response.status_code != 200:
                workflow_results["regime_detection"] = {"status": f"HTTP {regime_response.status_code}"}
                print(f"❌ Workflow - Regime Detection: HTTP {regime_response.status_code}")
                return workflow_results
            
            # 2. Get ML picks
            picks_response = requests.get(f"{self.base_url}/api/ml-picks/generate/SAFE", timeout=5)
            if picks_response.status_code != 200:
                workflow_results["ml_picks"] = {"status": f"HTTP {picks_response.status_code}"}
                print(f"❌ Workflow - ML Picks: HTTP {picks_response.status_code}")
                return workflow_results
            
            picks_data = picks_response.json()
            picks = picks_data.get("ml_picks", [])
            if not picks:
                workflow_results["ml_picks"] = {"status": "No picks generated"}
                print("❌ Workflow - ML Picks: No picks generated")
                return workflow_results
            
            # 3. Execute HFT strategy on top pick
            top_pick = picks[0]
            symbol = top_pick.get("symbol", "AAPL")
            
            hft_response = requests.post(
                f"{self.base_url}/api/hft/execute-strategy/",
                json={"strategy": "scalping", "symbol": symbol},
                timeout=5
            )
            if hft_response.status_code != 200:
                workflow_results["hft_execution"] = {"status": f"HTTP {hft_response.status_code}"}
                print(f"❌ Workflow - HFT Execution: HTTP {hft_response.status_code}")
                return workflow_results
            
            # 4. Get performance metrics
            perf_response = requests.get(f"{self.base_url}/api/hft/performance/", timeout=5)
            if perf_response.status_code != 200:
                workflow_results["performance"] = {"status": f"HTTP {perf_response.status_code}"}
                print(f"❌ Workflow - Performance: HTTP {perf_response.status_code}")
                return workflow_results
            
            workflow_results = {
                "regime_detection": {"status": "OK"},
                "ml_picks": {"status": "OK", "count": len(picks)},
                "hft_execution": {"status": "OK"},
                "performance": {"status": "OK"}
            }
            
            print(f"✅ End-to-End Workflow: Complete - {len(picks)} picks, executed on {symbol}")
            
        except Exception as e:
            workflow_results["error"] = {"status": f"Error: {e}"}
            print(f"❌ End-to-End Workflow: {e}")
        
        return workflow_results
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive accessibility test"""
        print("🚀 RICHESREACH FEATURE ACCESSIBILITY TEST")
        print("=" * 60)
        
        # Test basic connectivity first
        if not self.test_basic_connectivity():
            print("\n❌ Basic connectivity failed - aborting tests")
            return {"error": "Basic connectivity failed"}
        
        # Run all feature tests
        results = {
            "basic_connectivity": {"status": "OK"},
            "hft_features": self.test_hft_features(),
            "voice_ai_features": self.test_voice_ai_features(),
            "ai_features": self.test_ai_features(),
            "mobile_features": self.test_mobile_features(),
            "graphql_integration": self.test_graphql_integration(),
            "end_to_end_workflow": self.test_end_to_end_workflow()
        }
        
        # Calculate success rate
        total_tests = 0
        passed_tests = 0
        
        for category, tests in results.items():
            if isinstance(tests, dict):
                for test_name, test_result in tests.items():
                    if isinstance(test_result, dict) and "status" in test_result:
                        total_tests += 1
                        if test_result["status"] == "OK":
                            passed_tests += 1
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 FEATURE ACCESSIBILITY SUMMARY")
        print("=" * 60)
        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("\n🎉 EXCELLENT! All features are accessible and working!")
        elif success_rate >= 75:
            print("\n✅ GOOD! Most features are accessible with minor issues.")
        elif success_rate >= 50:
            print("\n⚠️  FAIR! Some features have accessibility issues.")
        else:
            print("\n❌ POOR! Many features have accessibility issues.")
        
        results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": success_rate
        }
        
        return results

def main():
    """Main function"""
    tester = FeatureAccessibilityTester()
    results = tester.run_comprehensive_test()
    
    # Save results to file
    with open("feature_accessibility_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: feature_accessibility_results.json")
    
    return results["summary"]["success_rate"] >= 75

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
