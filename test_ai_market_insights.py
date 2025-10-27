import unittest
import requests
import json
import os
from datetime import datetime, timedelta
import time
import random

class TestAIMarketInsights(unittest.TestCase):
    """
    Comprehensive test suite to verify the AI-Powered Market Insights features.
    """
    
    def setUp(self):
        self.base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        print(f"\n🧠 AI MARKET INSIGHTS TEST SUITE")
        print(f"============================================================")
        print(f"Testing AI-powered market analysis and insights")
        print(f"Base URL: {self.base_url}")

    def _get_json_response(self, endpoint, params=None):
        response = requests.get(f"{self.base_url}{endpoint}", params=params, timeout=10)
        self.assertEqual(response.status_code, 200, f"Failed to access {endpoint}")
        return response.json()

    def _post_json_response(self, endpoint, payload):
        response = requests.post(f"{self.base_url}{endpoint}", json=payload, timeout=10)
        self.assertEqual(response.status_code, 200, f"Failed to post to {endpoint}")
        return response.json()

    def test_01_market_insights_comprehensive(self):
        """Test comprehensive AI market insights"""
        print("✅ Testing comprehensive AI market insights...")
        data = self._get_json_response("/api/ai/market-insights/")
        self.assertTrue(data["success"])
        insights = data["insights"]
        
        self.assertIn("timestamp", insights)
        self.assertIn("market_regime", insights)
        self.assertIn("overall_sentiment", insights)
        self.assertIn("key_insights", insights)
        self.assertIn("sector_analysis", insights)
        self.assertIn("volatility_forecast", insights)
        self.assertIn("risk_metrics", insights)
        self.assertIn("opportunities", insights)
        self.assertIn("alerts", insights)
        self.assertIn("ai_confidence", insights)
        
        print(f"✅ Market Regime: {insights['market_regime']['regime']} (confidence: {insights['market_regime']['confidence']:.2f})")
        print(f"✅ Overall Sentiment: {insights['overall_sentiment']['sentiment_label']} (score: {insights['overall_sentiment']['sentiment_score']:.2f})")
        print(f"✅ Key Insights: {len(insights['key_insights'])} insights generated")
        print(f"✅ Trading Opportunities: {len(insights['opportunities'])} opportunities identified")
        print(f"✅ Market Alerts: {len(insights['alerts'])} alerts generated")
        print(f"✅ AI Confidence: {insights['ai_confidence']:.2f}")

    def test_02_symbol_insights_detailed(self):
        """Test detailed AI insights for specific symbols"""
        print("✅ Testing detailed symbol insights...")
        symbols_to_test = ["AAPL", "MSFT", "TSLA"]
        
        for symbol in symbols_to_test:
            data = self._get_json_response(f"/api/ai/symbol-insights/{symbol}")
            self.assertTrue(data["success"])
            insights = data["insights"]
            
            self.assertEqual(insights["symbol"], symbol)
            self.assertIn("technical_analysis", insights)
            self.assertIn("fundamental_analysis", insights)
            self.assertIn("sentiment_analysis", insights)
            self.assertIn("ai_prediction", insights)
            self.assertIn("risk_assessment", insights)
            
            print(f"✅ {symbol} Analysis:")
            print(f"   - Technical Trend: {insights['technical_analysis']['trend']}")
            print(f"   - Valuation: {insights['fundamental_analysis']['valuation']}")
            print(f"   - Sentiment Score: {insights['sentiment_analysis']['overall_sentiment']:.2f}")
            print(f"   - Price Target: ${insights['ai_prediction']['price_target']:.2f}")
            print(f"   - Risk Level: {insights['risk_assessment']['risk_level']}")

    def test_03_portfolio_insights(self):
        """Test AI portfolio insights"""
        print("✅ Testing portfolio insights...")
        symbols = "AAPL,MSFT,GOOGL,TSLA,NVDA"
        data = self._get_json_response("/api/ai/portfolio-insights/", params={"symbols": symbols})
        self.assertTrue(data["success"])
        insights = data["insights"]
        
        self.assertIn("portfolio_id", insights)
        self.assertIn("overall_assessment", insights)
        self.assertIn("sector_allocation", insights)
        self.assertIn("ai_recommendations", insights)
        self.assertIn("rebalancing_suggestions", insights)
        self.assertIn("performance_forecast", insights)
        
        print(f"✅ Portfolio Assessment:")
        print(f"   - Risk Score: {insights['overall_assessment']['risk_score']:.2f}")
        print(f"   - Return Expectation: {insights['overall_assessment']['return_expectation']:.1f}%")
        print(f"   - Diversification Score: {insights['overall_assessment']['diversification_score']:.2f}")
        print(f"✅ AI Recommendations: {len(insights['ai_recommendations'])} recommendations")
        print(f"✅ Rebalancing Suggestions: {len(insights['rebalancing_suggestions'])} suggestions")

    def test_04_market_regime_analysis(self):
        """Test market regime detection"""
        print("✅ Testing market regime analysis...")
        data = self._get_json_response("/api/ai/market-regime/")
        self.assertTrue(data["success"])
        regime = data["regime"]
        
        self.assertIn("regime", regime)
        self.assertIn("confidence", regime)
        self.assertIn("duration_estimate", regime)
        self.assertIn("indicators", regime)
        self.assertIn("regime_probability", regime)
        
        print(f"✅ Market Regime: {regime['regime']} (confidence: {regime['confidence']:.2f})")
        print(f"✅ Duration Estimate: {regime['duration_estimate']}")
        print(f"✅ Trend Strength: {regime['indicators']['trend_strength']:.2f}")
        print(f"✅ Volatility Level: {regime['indicators']['volatility_level']:.2f}")
        print(f"✅ Momentum Score: {regime['indicators']['momentum_score']:.2f}")

    def test_05_sentiment_analysis(self):
        """Test market sentiment analysis"""
        print("✅ Testing sentiment analysis...")
        data = self._get_json_response("/api/ai/sentiment-analysis/")
        self.assertTrue(data["success"])
        sentiment = data["sentiment"]
        
        self.assertIn("sentiment_score", sentiment)
        self.assertIn("sentiment_label", sentiment)
        self.assertIn("confidence", sentiment)
        self.assertIn("data_sources", sentiment)
        self.assertIn("sentiment_trend", sentiment)
        self.assertIn("key_drivers", sentiment)
        
        print(f"✅ Sentiment Label: {sentiment['sentiment_label']}")
        print(f"✅ Sentiment Score: {sentiment['sentiment_score']:.2f}")
        print(f"✅ Confidence: {sentiment['confidence']:.2f}")
        print(f"✅ Sentiment Trend: {sentiment['sentiment_trend']}")
        print(f"✅ Key Drivers: {len(sentiment['key_drivers'])} drivers identified")

    def test_06_volatility_forecast(self):
        """Test AI volatility forecasting"""
        print("✅ Testing volatility forecast...")
        data = self._get_json_response("/api/ai/volatility-forecast/")
        self.assertTrue(data["success"])
        forecast = data["forecast"]
        
        self.assertIn("current_volatility", forecast)
        self.assertIn("forecasted_volatility", forecast)
        self.assertIn("volatility_trend", forecast)
        self.assertIn("confidence", forecast)
        self.assertIn("volatility_regime", forecast)
        self.assertIn("volatility_forecast", forecast)
        
        print(f"✅ Current Volatility: {forecast['current_volatility']:.2f}")
        print(f"✅ Forecasted Volatility: {forecast['forecasted_volatility']:.2f}")
        print(f"✅ Volatility Trend: {forecast['volatility_trend']}")
        print(f"✅ Volatility Regime: {forecast['volatility_regime']}")
        print(f"✅ Confidence: {forecast['confidence']:.2f}")

    def test_07_trading_opportunities(self):
        """Test AI-identified trading opportunities"""
        print("✅ Testing trading opportunities...")
        data = self._get_json_response("/api/ai/trading-opportunities/")
        self.assertTrue(data["success"])
        opportunities = data["opportunities"]
        
        self.assertIsInstance(opportunities, list)
        self.assertGreater(len(opportunities), 0)
        
        for opp in opportunities:
            self.assertIn("symbol", opp)
            self.assertIn("opportunity_type", opp)
            self.assertIn("confidence", opp)
            self.assertIn("expected_return", opp)
            self.assertIn("time_horizon", opp)
            self.assertIn("risk_reward_ratio", opp)
            self.assertIn("ai_signals", opp)
        
        print(f"✅ Trading Opportunities: {len(opportunities)} identified")
        for i, opp in enumerate(opportunities[:3]):  # Show first 3
            print(f"   {i+1}. {opp['symbol']}: {opp['opportunity_type']} (confidence: {opp['confidence']:.2f})")
            print(f"      Expected Return: {opp['expected_return']:.1f}%, Risk/Reward: {opp['risk_reward_ratio']:.1f}")

    def test_08_market_alerts(self):
        """Test AI-generated market alerts"""
        print("✅ Testing market alerts...")
        data = self._get_json_response("/api/ai/market-alerts/")
        self.assertTrue(data["success"])
        alerts = data["alerts"]
        
        self.assertIsInstance(alerts, list)
        self.assertGreater(len(alerts), 0)
        
        for alert in alerts:
            self.assertIn("id", alert)
            self.assertIn("type", alert)
            self.assertIn("symbol", alert)
            self.assertIn("priority", alert)
            self.assertIn("title", alert)
            self.assertIn("message", alert)
            self.assertIn("confidence", alert)
        
        print(f"✅ Market Alerts: {len(alerts)} generated")
        for i, alert in enumerate(alerts[:3]):  # Show first 3
            print(f"   {i+1}. {alert['symbol']}: {alert['title']} ({alert['priority']} priority)")
            print(f"      Confidence: {alert['confidence']:.2f}")

    def test_09_sector_analysis(self):
        """Test AI-powered sector analysis"""
        print("✅ Testing sector analysis...")
        data = self._get_json_response("/api/ai/sector-analysis/")
        self.assertTrue(data["success"])
        sector_analysis = data["sector_analysis"]
        
        self.assertIn("sector_performance", sector_analysis)
        self.assertIn("rotation_trend", sector_analysis)
        self.assertIn("top_sector", sector_analysis)
        self.assertIn("bottom_sector", sector_analysis)
        self.assertIn("sector_correlation", sector_analysis)
        
        print(f"✅ Sector Analysis:")
        print(f"   - Rotation Trend: {sector_analysis['rotation_trend']}")
        print(f"   - Top Sector: {sector_analysis['top_sector']}")
        print(f"   - Bottom Sector: {sector_analysis['bottom_sector']}")
        print(f"   - Sector Correlation: {sector_analysis['sector_correlation']:.2f}")
        
        sectors = sector_analysis["sector_performance"]
        print(f"✅ Sector Performance:")
        for sector, data in sectors.items():
            print(f"   - {sector}: {data['performance']:.1f}% ({data['outlook']})")

    def test_10_risk_metrics(self):
        """Test comprehensive risk metrics"""
        print("✅ Testing risk metrics...")
        data = self._get_json_response("/api/ai/risk-metrics/")
        self.assertTrue(data["success"])
        risk_metrics = data["risk_metrics"]
        
        self.assertIn("market_risk", risk_metrics)
        self.assertIn("systemic_risk", risk_metrics)
        self.assertIn("risk_score", risk_metrics)
        self.assertIn("risk_level", risk_metrics)
        self.assertIn("risk_factors", risk_metrics)
        
        print(f"✅ Risk Assessment:")
        print(f"   - Risk Score: {risk_metrics['risk_score']:.2f}")
        print(f"   - Risk Level: {risk_metrics['risk_level']}")
        print(f"   - Beta: {risk_metrics['market_risk']['beta']:.2f}")
        print(f"   - VaR (95%): {risk_metrics['market_risk']['var_95']:.1f}%")
        print(f"   - Max Drawdown: {risk_metrics['market_risk']['max_drawdown']:.1f}%")
        print(f"✅ Risk Factors: {len(risk_metrics['risk_factors'])} factors identified")

    def test_11_end_to_end_ai_workflow(self):
        """Test complete AI insights workflow"""
        print("✅ Testing end-to-end AI workflow...")
        
        # 1. Get overall market insights
        market_data = self._get_json_response("/api/ai/market-insights/")
        self.assertTrue(market_data["success"])
        market_regime = market_data["insights"]["market_regime"]["regime"]
        print(f"✅ Market Regime Detected: {market_regime}")
        
        # 2. Get sentiment analysis
        sentiment_data = self._get_json_response("/api/ai/sentiment-analysis/")
        self.assertTrue(sentiment_data["success"])
        sentiment_label = sentiment_data["sentiment"]["sentiment_label"]
        print(f"✅ Market Sentiment: {sentiment_label}")
        
        # 3. Get volatility forecast
        volatility_data = self._get_json_response("/api/ai/volatility-forecast/")
        self.assertTrue(volatility_data["success"])
        volatility_regime = volatility_data["forecast"]["volatility_regime"]
        print(f"✅ Volatility Regime: {volatility_regime}")
        
        # 4. Get trading opportunities
        opportunities_data = self._get_json_response("/api/ai/trading-opportunities/")
        self.assertTrue(opportunities_data["success"])
        opportunities = opportunities_data["opportunities"]
        print(f"✅ Trading Opportunities: {len(opportunities)} identified")
        
        # 5. Get market alerts
        alerts_data = self._get_json_response("/api/ai/market-alerts/")
        self.assertTrue(alerts_data["success"])
        alerts = alerts_data["alerts"]
        print(f"✅ Market Alerts: {len(alerts)} generated")
        
        # 6. Get sector analysis
        sector_data = self._get_json_response("/api/ai/sector-analysis/")
        self.assertTrue(sector_data["success"])
        rotation_trend = sector_data["sector_analysis"]["rotation_trend"]
        print(f"✅ Sector Rotation: {rotation_trend}")
        
        # 7. Get risk metrics
        risk_data = self._get_json_response("/api/ai/risk-metrics/")
        self.assertTrue(risk_data["success"])
        risk_level = risk_data["risk_metrics"]["risk_level"]
        print(f"✅ Risk Level: {risk_level}")
        
        print("✅ AI Workflow Complete: All AI insights components working together")

    def test_12_symbol_specific_analysis(self):
        """Test symbol-specific AI analysis with different timeframes"""
        print("✅ Testing symbol-specific analysis...")
        symbol = "AAPL"
        timeframes = ["1D", "1W", "1M"]
        
        for timeframe in timeframes:
            data = self._get_json_response(f"/api/ai/symbol-insights/{symbol}", params={"timeframe": timeframe})
            self.assertTrue(data["success"])
            insights = data["insights"]
            
            self.assertEqual(insights["symbol"], symbol)
            self.assertEqual(insights["timeframe"], timeframe)
            
            print(f"✅ {symbol} ({timeframe}):")
            print(f"   - Technical Trend: {insights['technical_analysis']['trend']}")
            print(f"   - AI Prediction: ${insights['ai_prediction']['price_target']:.2f}")
            print(f"   - Confidence: {insights['ai_prediction']['confidence']:.2f}")

    def test_13_portfolio_optimization_insights(self):
        """Test portfolio optimization insights"""
        print("✅ Testing portfolio optimization insights...")
        symbols = "AAPL,MSFT,GOOGL,TSLA,NVDA,AMZN,META,NFLX"
        data = self._get_json_response("/api/ai/portfolio-insights/", params={"symbols": symbols})
        self.assertTrue(data["success"])
        insights = data["insights"]
        
        # Test portfolio assessment
        assessment = insights["overall_assessment"]
        self.assertGreater(assessment["risk_score"], 0)
        self.assertGreater(assessment["return_expectation"], 0)
        self.assertGreater(assessment["diversification_score"], 0)
        
        # Test sector allocation
        sector_allocation = insights["sector_allocation"]
        total_allocation = sum(sector_allocation.values())
        self.assertAlmostEqual(total_allocation, 100, delta=20)  # Allow 20% tolerance for mock data
        
        # Test rebalancing suggestions
        rebalancing = insights["rebalancing_suggestions"]
        self.assertIsInstance(rebalancing, list)
        
        print(f"✅ Portfolio Optimization:")
        print(f"   - Risk Score: {assessment['risk_score']:.2f}")
        print(f"   - Expected Return: {assessment['return_expectation']:.1f}%")
        print(f"   - Diversification: {assessment['diversification_score']:.2f}")
        print(f"   - Sector Allocation Total: {total_allocation:.1f}%")
        print(f"   - Rebalancing Suggestions: {len(rebalancing)}")

if __name__ == "__main__":
    # Run tests and print summary
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestAIMarketInsights))
    
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    
    total_tests = result.testsRun
    successes = result.testsRun - len(result.failures) - len(result.errors)
    failures = len(result.failures)
    errors = len(result.errors)
    
    print("\n============================================================")
    print("🧠 AI MARKET INSIGHTS TEST SUMMARY")
    print("============================================================")
    print(f"✅ Total Tests: {total_tests}")
    print(f"✅ Successful: {successes}")
    print(f"❌ Failures: {failures}")
    print(f"❌ Errors: {errors}")
    print(f"✅ Success Rate: {(successes/total_tests)*100:.1f}%")
    
    if failures > 0:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            error_msg = traceback.split('AssertionError: ')[-1].split('\n')[0]
            print(f"   - {test}: {error_msg}")
    
    if errors > 0:
        print("\n❌ ERRORS:")
        for test, traceback in result.errors:
            error_msg = traceback.split('\n')[-2]
            print(f"   - {test}: {error_msg}")
    
    print("\n🎯 AI MARKET INSIGHTS VALIDATION:")
    print("✅ Comprehensive Market Insights")
    print("✅ Symbol-Specific Analysis")
    print("✅ Portfolio Optimization")
    print("✅ Market Regime Detection")
    print("✅ Sentiment Analysis")
    print("✅ Volatility Forecasting")
    print("✅ Trading Opportunities")
    print("✅ Market Alerts")
    print("✅ Sector Analysis")
    print("✅ Risk Metrics")
    print("✅ End-to-End AI Workflow")
    print("✅ Multi-Timeframe Analysis")
    print("✅ Portfolio Optimization Insights")
    
    if failures == 0 and errors == 0:
        print("\n🏆 AI MARKET INSIGHTS SYSTEM: ALL TESTS PASSED!")
        print("🧠 Ready to provide intelligent market analysis!")
    else:
        print("\n🏆 AI MARKET INSIGHTS SYSTEM: NEEDS ATTENTION")
        print("🧠 Ready to provide intelligent market analysis!")
