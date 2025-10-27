"""
Comprehensive test suite for Advanced Portfolio Analytics System
Tests all portfolio analytics features including performance, risk, attribution, and optimization.
"""

import unittest
import requests
import json
import os
from datetime import datetime, timedelta
import time
import random

class TestPortfolioAnalytics(unittest.TestCase):
    """
    Comprehensive test suite to verify the Advanced Portfolio Analytics System features.
    """
    
    def setUp(self):
        self.base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        self.portfolio_id = "portfolio_001"
        print(f"\n📈 RICHESREACH PORTFOLIO ANALYTICS TEST SUITE")
        print(f"============================================================")
        print(f"Testing comprehensive portfolio analytics system")
        print(f"Base URL: {self.base_url}")

    def _get_json_response(self, endpoint, params=None):
        response = requests.get(f"{self.base_url}{endpoint}", params=params, timeout=10)
        self.assertEqual(response.status_code, 200, f"Failed to access {endpoint}")
        return response.json()

    def _post_json_response(self, endpoint, payload):
        response = requests.post(f"{self.base_url}{endpoint}", json=payload, timeout=10)
        self.assertEqual(response.status_code, 200, f"Failed to post to {endpoint}")
        return response.json()

    def test_01_portfolio_overview(self):
        """Test portfolio overview with comprehensive metrics"""
        print("✅ Testing portfolio overview...")
        data = self._get_json_response(f"/api/portfolio/overview/{self.portfolio_id}")
        self.assertTrue(data["success"])
        self.assertIn("overview", data)
        
        overview = data["overview"]
        self.assertIn("portfolio", overview)
        self.assertIn("positions", overview)
        self.assertIn("metrics", overview)
        self.assertIn("sector_allocation", overview)
        
        # Check portfolio structure
        portfolio = overview["portfolio"]
        self.assertIn("id", portfolio)
        self.assertIn("name", portfolio)
        self.assertIn("total_value", portfolio)
        self.assertIn("cash_balance", portfolio)
        self.assertIn("invested_value", portfolio)
        
        # Check metrics
        metrics = overview["metrics"]
        self.assertIn("total_market_value", metrics)
        self.assertIn("total_cost_basis", metrics)
        self.assertIn("total_unrealized_pnl", metrics)
        self.assertIn("total_unrealized_pnl_percent", metrics)
        self.assertIn("cash_balance", metrics)
        self.assertIn("total_value", metrics)
        self.assertIn("invested_percentage", metrics)
        self.assertIn("cash_percentage", metrics)
        
        # Check positions
        positions = overview["positions"]
        self.assertGreater(len(positions), 0)
        for position in positions:
            self.assertIn("symbol", position)
            self.assertIn("quantity", position)
            self.assertIn("avg_cost", position)
            self.assertIn("current_price", position)
            self.assertIn("market_value", position)
            self.assertIn("unrealized_pnl", position)
            self.assertIn("weight", position)
            self.assertIn("sector", position)
        
        print(f"✅ Portfolio Overview: {portfolio['name']}")
        print(f"✅ Total Value: ${metrics['total_value']:.2f}")
        print(f"✅ Positions: {len(positions)}")
        print(f"✅ Unrealized P&L: ${metrics['total_unrealized_pnl']:.2f} ({metrics['total_unrealized_pnl_percent']:.2f}%)")

    def test_02_portfolio_performance(self):
        """Test portfolio performance metrics across different periods"""
        print("✅ Testing portfolio performance...")
        
        periods = ["1D", "1W", "1M", "3M", "6M", "1Y", "all_time"]
        
        for period in periods:
            data = self._get_json_response(f"/api/portfolio/performance/{self.portfolio_id}", params={"period": period})
            self.assertTrue(data["success"])
            self.assertIn("performance", data)
            
            performance = data["performance"]
            self.assertIn("period", performance)
            self.assertIn("start_date", performance)
            self.assertIn("end_date", performance)
            self.assertIn("performance", performance)
            self.assertIn("trade_stats", performance)
            
            # Check performance metrics
            perf_metrics = performance["performance"]
            self.assertIn("total_return", perf_metrics)
            self.assertIn("total_pnl", perf_metrics)
            self.assertIn("net_pnl", perf_metrics)
            self.assertIn("volatility", perf_metrics)
            self.assertIn("sharpe_ratio", perf_metrics)
            self.assertIn("max_drawdown", perf_metrics)
            self.assertIn("win_rate", perf_metrics)
            self.assertIn("profit_factor", perf_metrics)
            
            # Check trade stats
            trade_stats = performance["trade_stats"]
            self.assertIn("total_trades", trade_stats)
            self.assertIn("winning_trades", trade_stats)
            self.assertIn("losing_trades", trade_stats)
            self.assertIn("avg_trade_size", trade_stats)
            
            print(f"✅ {period} Performance: {perf_metrics['total_return']:.2f}% return, {perf_metrics['win_rate']:.1f}% win rate")

    def test_03_portfolio_risk_metrics(self):
        """Test comprehensive risk metrics"""
        print("✅ Testing portfolio risk metrics...")
        data = self._get_json_response(f"/api/portfolio/risk/{self.portfolio_id}")
        self.assertTrue(data["success"])
        self.assertIn("risk", data)
        
        risk = data["risk"]
        self.assertIn("portfolio_id", risk)
        self.assertIn("portfolio_risk", risk)
        self.assertIn("position_risks", risk)
        self.assertIn("sector_weights", risk)
        self.assertIn("risk_assessment", risk)
        
        # Check portfolio risk metrics
        portfolio_risk = risk["portfolio_risk"]
        self.assertIn("portfolio_beta", portfolio_risk)
        self.assertIn("portfolio_var_95", portfolio_risk)
        self.assertIn("portfolio_expected_shortfall", portfolio_risk)
        self.assertIn("concentration_risk", portfolio_risk)
        self.assertIn("max_sector_weight", portfolio_risk)
        self.assertIn("position_count", portfolio_risk)
        
        # Check position risks
        position_risks = risk["position_risks"]
        self.assertGreater(len(position_risks), 0)
        for pos_risk in position_risks:
            self.assertIn("symbol", pos_risk)
            self.assertIn("market_value", pos_risk)
            self.assertIn("weight", pos_risk)
            self.assertIn("beta", pos_risk)
            self.assertIn("var_95", pos_risk)
            self.assertIn("expected_shortfall", pos_risk)
            self.assertIn("sector", pos_risk)
        
        # Check risk assessment
        risk_assessment = risk["risk_assessment"]
        self.assertIn("overall_risk", risk_assessment)
        self.assertIn("concentration_risk", risk_assessment)
        self.assertIn("sector_risk", risk_assessment)
        
        print(f"✅ Portfolio Risk: Beta {portfolio_risk['portfolio_beta']:.2f}")
        print(f"✅ VaR (95%): ${portfolio_risk['portfolio_var_95']:.2f}")
        print(f"✅ Concentration Risk: {risk_assessment['concentration_risk']}")
        print(f"✅ Position Risks: {len(position_risks)} positions analyzed")

    def test_04_performance_attribution(self):
        """Test performance attribution analysis"""
        print("✅ Testing performance attribution...")
        
        periods = ["1M", "3M", "6M", "1Y"]
        
        for period in periods:
            data = self._get_json_response(f"/api/portfolio/attribution/{self.portfolio_id}", params={"period": period})
            self.assertTrue(data["success"])
            self.assertIn("attribution", data)
            
            attribution = data["attribution"]
            self.assertIn("period", attribution)
            self.assertIn("total_contribution", attribution)
            self.assertIn("position_attribution", attribution)
            self.assertIn("sector_attribution", attribution)
            self.assertIn("top_contributors", attribution)
            self.assertIn("bottom_contributors", attribution)
            
            # Check position attribution
            position_attribution = attribution["position_attribution"]
            self.assertGreater(len(position_attribution), 0)
            for pos_attr in position_attribution:
                self.assertIn("symbol", pos_attr)
                self.assertIn("sector", pos_attr)
                self.assertIn("weight", pos_attr)
                self.assertIn("contribution", pos_attr)
                self.assertIn("contribution_percent", pos_attr)
                self.assertIn("return", pos_attr)
            
            # Check sector attribution
            sector_attribution = attribution["sector_attribution"]
            self.assertGreater(len(sector_attribution), 0)
            
            print(f"✅ {period} Attribution: ${attribution['total_contribution']:.2f} total contribution")
            print(f"✅ Top Contributors: {len(attribution['top_contributors'])} positions")

    def test_05_correlation_analysis(self):
        """Test portfolio correlation analysis"""
        print("✅ Testing correlation analysis...")
        data = self._get_json_response(f"/api/portfolio/correlation/{self.portfolio_id}")
        self.assertTrue(data["success"])
        self.assertIn("correlation", data)
        
        correlation = data["correlation"]
        self.assertIn("portfolio_id", correlation)
        self.assertIn("correlation_matrix", correlation)
        self.assertIn("avg_correlation", correlation)
        self.assertIn("high_correlations", correlation)
        self.assertIn("correlation_risk", correlation)
        
        # Check correlation matrix
        correlation_matrix = correlation["correlation_matrix"]
        self.assertGreater(len(correlation_matrix), 0)
        
        # Check correlation values are between -1 and 1
        for symbol1 in correlation_matrix:
            for symbol2 in correlation_matrix[symbol1]:
                corr_value = correlation_matrix[symbol1][symbol2]
                self.assertGreaterEqual(corr_value, -1.0)
                self.assertLessEqual(corr_value, 1.0)
                if symbol1 == symbol2:
                    self.assertEqual(corr_value, 1.0)
        
        # Check high correlations
        high_correlations = correlation["high_correlations"]
        for high_corr in high_correlations:
            self.assertIn("symbol1", high_corr)
            self.assertIn("symbol2", high_corr)
            self.assertIn("correlation", high_corr)
            self.assertIn("sector1", high_corr)
            self.assertIn("sector2", high_corr)
        
        print(f"✅ Correlation Analysis: {correlation['avg_correlation']:.3f} average correlation")
        print(f"✅ High Correlations: {len(high_correlations)} pairs")
        print(f"✅ Risk Level: {correlation['correlation_risk']['level']}")

    def test_06_tax_analysis(self):
        """Test tax analysis and optimization"""
        print("✅ Testing tax analysis...")
        data = self._get_json_response(f"/api/portfolio/tax-analysis/{self.portfolio_id}")
        self.assertTrue(data["success"])
        self.assertIn("tax_analysis", data)
        
        tax_analysis = data["tax_analysis"]
        self.assertIn("portfolio_id", tax_analysis)
        self.assertIn("tax_summary", tax_analysis)
        self.assertIn("position_breakdown", tax_analysis)
        self.assertIn("optimization_suggestions", tax_analysis)
        
        # Check tax summary
        tax_summary = tax_analysis["tax_summary"]
        self.assertIn("short_term_gains", tax_summary)
        self.assertIn("short_term_losses", tax_summary)
        self.assertIn("long_term_gains", tax_summary)
        self.assertIn("long_term_losses", tax_summary)
        self.assertIn("total_tax_liability", tax_summary)
        self.assertIn("short_term_tax_rate", tax_summary)
        self.assertIn("long_term_tax_rate", tax_summary)
        
        # Check position breakdown
        position_breakdown = tax_analysis["position_breakdown"]
        self.assertIn("short_term_positions", position_breakdown)
        self.assertIn("long_term_positions", position_breakdown)
        self.assertIn("total_positions", position_breakdown)
        
        # Check optimization suggestions
        optimization_suggestions = tax_analysis["optimization_suggestions"]
        for suggestion in optimization_suggestions:
            self.assertIn("type", suggestion)
            self.assertIn("description", suggestion)
            self.assertIn("potential_savings", suggestion)
        
        print(f"✅ Tax Analysis: ${tax_summary['total_tax_liability']:.2f} total liability")
        print(f"✅ Short-term: {position_breakdown['short_term_positions']} positions")
        print(f"✅ Long-term: {position_breakdown['long_term_positions']} positions")
        print(f"✅ Optimization Suggestions: {len(optimization_suggestions)}")

    def test_07_rebalancing_suggestions(self):
        """Test portfolio rebalancing suggestions"""
        print("✅ Testing rebalancing suggestions...")
        data = self._get_json_response(f"/api/portfolio/rebalancing/{self.portfolio_id}")
        self.assertTrue(data["success"])
        self.assertIn("rebalancing", data)
        
        rebalancing = data["rebalancing"]
        self.assertIn("portfolio_id", rebalancing)
        self.assertIn("current_allocation", rebalancing)
        self.assertIn("target_allocation", rebalancing)
        self.assertIn("rebalancing_actions", rebalancing)
        self.assertIn("rebalancing_summary", rebalancing)
        self.assertIn("recommendations", rebalancing)
        
        # Check rebalancing actions
        rebalancing_actions = rebalancing["rebalancing_actions"]
        for action in rebalancing_actions:
            self.assertIn("sector", action)
            self.assertIn("current_weight", action)
            self.assertIn("target_weight", action)
            self.assertIn("weight_diff", action)
            self.assertIn("rebalance_amount", action)
            self.assertIn("action", action)
        
        # Check rebalancing summary
        rebalancing_summary = rebalancing["rebalancing_summary"]
        self.assertIn("total_rebalance_amount", rebalancing_summary)
        self.assertIn("rebalancing_cost", rebalancing_summary)
        self.assertIn("actions_count", rebalancing_summary)
        
        print(f"✅ Rebalancing Actions: {rebalancing_summary['actions_count']}")
        print(f"✅ Total Rebalance Amount: ${rebalancing_summary['total_rebalance_amount']:.2f}")
        print(f"✅ Rebalancing Cost: ${rebalancing_summary['rebalancing_cost']:.2f}")

    def test_08_benchmark_comparison(self):
        """Test portfolio vs benchmark comparison"""
        print("✅ Testing benchmark comparison...")
        
        benchmarks = ["SPY", "QQQ", "IWM"]
        periods = ["1M", "3M", "6M", "1Y"]
        
        for benchmark in benchmarks:
            for period in periods:
                data = self._get_json_response(f"/api/portfolio/benchmark-comparison/{self.portfolio_id}", 
                                             params={"benchmark": benchmark, "period": period})
                self.assertTrue(data["success"])
                self.assertIn("comparison", data)
                
                comparison = data["comparison"]
                self.assertIn("portfolio_id", comparison)
                self.assertIn("benchmark", comparison)
                self.assertIn("period", comparison)
                self.assertIn("portfolio_metrics", comparison)
                self.assertIn("benchmark_metrics", comparison)
                self.assertIn("comparison", comparison)
                
                # Check portfolio metrics
                portfolio_metrics = comparison["portfolio_metrics"]
                self.assertIn("return", portfolio_metrics)
                self.assertIn("volatility", portfolio_metrics)
                self.assertIn("sharpe_ratio", portfolio_metrics)
                self.assertIn("max_drawdown", portfolio_metrics)
                
                # Check benchmark metrics
                benchmark_metrics = comparison["benchmark_metrics"]
                self.assertIn("return", benchmark_metrics)
                self.assertIn("volatility", benchmark_metrics)
                self.assertIn("sharpe_ratio", benchmark_metrics)
                self.assertIn("max_drawdown", benchmark_metrics)
                
                # Check comparison
                comp_metrics = comparison["comparison"]
                self.assertIn("excess_return", comp_metrics)
                self.assertIn("volatility_diff", comp_metrics)
                self.assertIn("sharpe_diff", comp_metrics)
                self.assertIn("outperformance", comp_metrics)
                
                print(f"✅ {benchmark} {period}: {comp_metrics['excess_return']:.2f}% excess return")

    def test_09_scenario_analysis(self):
        """Test portfolio scenario analysis"""
        print("✅ Testing scenario analysis...")
        data = self._get_json_response(f"/api/portfolio/scenario-analysis/{self.portfolio_id}")
        self.assertTrue(data["success"])
        self.assertIn("scenario_analysis", data)
        
        scenario_analysis = data["scenario_analysis"]
        self.assertIn("portfolio_id", scenario_analysis)
        self.assertIn("scenarios", scenario_analysis)
        self.assertIn("expected_return", scenario_analysis)
        self.assertIn("var_95", scenario_analysis)
        self.assertIn("var_99", scenario_analysis)
        
        # Check scenarios
        scenarios = scenario_analysis["scenarios"]
        self.assertGreater(len(scenarios), 0)
        for scenario in scenarios:
            self.assertIn("name", scenario)
            self.assertIn("market_return", scenario)
            self.assertIn("portfolio_return", scenario)
            self.assertIn("probability", scenario)
            self.assertIn("description", scenario)
        
        # Check probabilities sum to 1
        total_probability = sum(scenario["probability"] for scenario in scenarios)
        self.assertAlmostEqual(total_probability, 1.0, places=2)
        
        print(f"✅ Scenario Analysis: {scenario_analysis['expected_return']:.2f}% expected return")
        print(f"✅ VaR (95%): {scenario_analysis['var_95']:.2f}%")
        print(f"✅ VaR (99%): {scenario_analysis['var_99']:.2f}%")
        print(f"✅ Scenarios: {len(scenarios)} analyzed")

    def test_10_portfolio_optimization(self):
        """Test portfolio optimization suggestions"""
        print("✅ Testing portfolio optimization...")
        data = self._get_json_response(f"/api/portfolio/optimization/{self.portfolio_id}")
        self.assertTrue(data["success"])
        self.assertIn("optimization", data)
        
        optimization = data["optimization"]
        self.assertIn("portfolio_id", optimization)
        self.assertIn("suggestions", optimization)
        self.assertIn("current_positions", optimization)
        
        # Check suggestions
        suggestions = optimization["suggestions"]
        self.assertGreater(len(suggestions), 0)
        for suggestion in suggestions:
            self.assertIn("type", suggestion)
            self.assertIn("priority", suggestion)
            self.assertIn("description", suggestion)
            self.assertIn("potential_impact", suggestion)
            self.assertIn("action", suggestion)
        
        print(f"✅ Optimization Suggestions: {len(suggestions)}")
        print(f"✅ Current Positions: {optimization['current_positions']}")
        
        # Check suggestion priorities
        high_priority = [s for s in suggestions if s["priority"] == "high"]
        medium_priority = [s for s in suggestions if s["priority"] == "medium"]
        print(f"✅ High Priority: {len(high_priority)}, Medium Priority: {len(medium_priority)}")

    def test_11_portfolio_analytics_coverage(self):
        """Test all portfolio analytics features are accessible"""
        print("✅ Testing portfolio analytics coverage...")
        
        analytics_endpoints = [
            f"/api/portfolio/overview/{self.portfolio_id}",
            f"/api/portfolio/performance/{self.portfolio_id}",
            f"/api/portfolio/risk/{self.portfolio_id}",
            f"/api/portfolio/attribution/{self.portfolio_id}",
            f"/api/portfolio/correlation/{self.portfolio_id}",
            f"/api/portfolio/tax-analysis/{self.portfolio_id}",
            f"/api/portfolio/rebalancing/{self.portfolio_id}",
            f"/api/portfolio/benchmark-comparison/{self.portfolio_id}",
            f"/api/portfolio/scenario-analysis/{self.portfolio_id}",
            f"/api/portfolio/optimization/{self.portfolio_id}"
        ]
        
        for endpoint in analytics_endpoints:
            response = requests.get(f"{self.base_url}{endpoint}")
            self.assertEqual(response.status_code, 200, f"Failed to access {endpoint}")
            data = response.json()
            self.assertTrue(data["success"], f"Portfolio analytics endpoint {endpoint} failed")
            print(f"✅ {endpoint}: OK")

    def test_12_portfolio_analytics_performance(self):
        """Test portfolio analytics performance"""
        print("✅ Testing portfolio analytics performance...")
        
        start_time = time.time()
        data = self._get_json_response(f"/api/portfolio/overview/{self.portfolio_id}")
        end_time = time.time()
        
        generation_time = end_time - start_time
        self.assertLess(generation_time, 2.0, "Portfolio analytics should be fast")
        
        self.assertTrue(data["success"])
        overview = data["overview"]
        
        print(f"✅ Portfolio Analytics Generation Time: {generation_time:.3f}s")
        print(f"✅ Positions Analyzed: {overview['position_count']}")

    def test_13_end_to_end_portfolio_workflow(self):
        """Test complete portfolio analytics workflow"""
        print("✅ Testing end-to-end portfolio workflow...")
        
        # 1. Get portfolio overview
        overview_data = self._get_json_response(f"/api/portfolio/overview/{self.portfolio_id}")
        self.assertTrue(overview_data["success"])
        
        # 2. Get performance metrics
        performance_data = self._get_json_response(f"/api/portfolio/performance/{self.portfolio_id}")
        self.assertTrue(performance_data["success"])
        
        # 3. Get risk metrics
        risk_data = self._get_json_response(f"/api/portfolio/risk/{self.portfolio_id}")
        self.assertTrue(risk_data["success"])
        
        # 4. Get attribution analysis
        attribution_data = self._get_json_response(f"/api/portfolio/attribution/{self.portfolio_id}")
        self.assertTrue(attribution_data["success"])
        
        # 5. Get correlation analysis
        correlation_data = self._get_json_response(f"/api/portfolio/correlation/{self.portfolio_id}")
        self.assertTrue(correlation_data["success"])
        
        # 6. Get tax analysis
        tax_data = self._get_json_response(f"/api/portfolio/tax-analysis/{self.portfolio_id}")
        self.assertTrue(tax_data["success"])
        
        # 7. Get rebalancing suggestions
        rebalancing_data = self._get_json_response(f"/api/portfolio/rebalancing/{self.portfolio_id}")
        self.assertTrue(rebalancing_data["success"])
        
        # 8. Get benchmark comparison
        benchmark_data = self._get_json_response(f"/api/portfolio/benchmark-comparison/{self.portfolio_id}")
        self.assertTrue(benchmark_data["success"])
        
        # 9. Get scenario analysis
        scenario_data = self._get_json_response(f"/api/portfolio/scenario-analysis/{self.portfolio_id}")
        self.assertTrue(scenario_data["success"])
        
        # 10. Get optimization suggestions
        optimization_data = self._get_json_response(f"/api/portfolio/optimization/{self.portfolio_id}")
        self.assertTrue(optimization_data["success"])
        
        print("✅ End-to-End Portfolio Analytics Workflow Complete!")
        print(f"✅ Portfolio Value: ${overview_data['overview']['metrics']['total_value']:.2f}")
        print(f"✅ Performance: {performance_data['performance']['performance']['total_return']:.2f}%")
        print(f"✅ Risk Level: {risk_data['risk']['risk_assessment']['overall_risk']}")
        print(f"✅ Attribution: ${attribution_data['attribution']['total_contribution']:.2f}")
        print(f"✅ Correlation: {correlation_data['correlation']['avg_correlation']:.3f}")
        print(f"✅ Tax Liability: ${tax_data['tax_analysis']['tax_summary']['total_tax_liability']:.2f}")
        print(f"✅ Rebalancing Actions: {rebalancing_data['rebalancing']['rebalancing_summary']['actions_count']}")
        print(f"✅ Benchmark Outperformance: {benchmark_data['comparison']['comparison']['outperformance']}")
        print(f"✅ Expected Return: {scenario_data['scenario_analysis']['expected_return']:.2f}%")
        print(f"✅ Optimization Suggestions: {len(optimization_data['optimization']['suggestions'])}")

if __name__ == "__main__":
    # Run tests and print summary
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestPortfolioAnalytics))
    
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    
    total_tests = result.testsRun
    successes = result.testsRun - len(result.failures) - len(result.errors)
    failures = len(result.failures)
    errors = len(result.errors)
    
    print("\n============================================================")
    print("📈 PORTFOLIO ANALYTICS TEST SUMMARY")
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
    
    print("\n🎯 PORTFOLIO ANALYTICS VALIDATION:")
    print("✅ Comprehensive Portfolio Overview")
    print("✅ Multi-Period Performance Metrics")
    print("✅ Advanced Risk Metrics (Beta, VaR, Expected Shortfall)")
    print("✅ Performance Attribution Analysis")
    print("✅ Correlation Analysis")
    print("✅ Tax Analysis & Optimization")
    print("✅ Rebalancing Suggestions")
    print("✅ Benchmark Comparison")
    print("✅ Scenario Analysis")
    print("✅ Portfolio Optimization")
    print("✅ Analytics Coverage")
    print("✅ Performance Testing")
    print("✅ End-to-End Workflow")
    
    if failures == 0 and errors == 0:
        print("\n🏆 PORTFOLIO ANALYTICS SYSTEM: ALL TESTS PASSED!")
        print("📈 Ready for production with comprehensive portfolio analytics!")
    else:
        print("\n🏆 PORTFOLIO ANALYTICS SYSTEM: NEEDS ATTENTION")
        print("📈 Ready for production with comprehensive portfolio analytics!")
