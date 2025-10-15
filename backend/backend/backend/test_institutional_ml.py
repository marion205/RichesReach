#!/usr/bin/env python3
"""
Test script for institutional-grade ML mutations
Compares performance and functionality against existing systems
"""
import asyncio
import time
import json
import requests
from typing import Dict, List, Any
import statistics

# Test configuration
BACKEND_URL = "http://localhost:8000"
GRAPHQL_ENDPOINT = f"{BACKEND_URL}/graphql/"

# Test data
TEST_USER_PROFILE = {
    "age": 35,
    "income_bracket": "75000-100000",
    "investment_goals": ["retirement", "wealth_building"],
    "risk_tolerance": "Moderate",
    "investment_horizon": "10-20 years"
}

TEST_CONSTRAINTS = {
    "max_weight_per_name": 0.15,
    "max_sector_weight": 0.35,
    "max_turnover": 0.30,
    "min_liquidity_score": 0.0,
    "risk_aversion": 4.0,
    "cost_aversion": 0.8,
    "cvar_confidence": 0.95,
    "long_only": True
}

class MLMutationTester:
    def __init__(self):
        self.results = {}
        self.session = requests.Session()
        
    def make_graphql_request(self, query: str, variables: Dict = None) -> Dict:
        """Make a GraphQL request to the backend"""
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        try:
            response = self.session.post(
                GRAPHQL_ENDPOINT,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e), "data": None}
    
    def test_legacy_ml_mutation(self) -> Dict:
        """Test the legacy ML portfolio recommendation"""
        query = """
        mutation GenerateMLPortfolioRecommendation($useAdvancedMl: Boolean, $includeMarketAnalysis: Boolean, $includeRiskOptimization: Boolean, $idempotencyKey: String) {
            generateMlPortfolioRecommendation(
                useAdvancedMl: $useAdvancedMl
                includeMarketAnalysis: $includeMarketAnalysis
                includeRiskOptimization: $includeRiskOptimization
                idempotencyKey: $idempotencyKey
            ) {
                success
                message
                recommendation {
                    id
                    riskProfile
                    portfolioAllocation
                    expectedPortfolioReturn
                    riskAssessment
                    mlConfidence
                    mlMarketRegime
                    mlExpectedReturnRange
                    mlRiskScore
                    mlOptimizationMethod
                }
                marketAnalysis
                mlInsights
            }
        }
        """
        
        variables = {
            "useAdvancedMl": True,
            "includeMarketAnalysis": True,
            "includeRiskOptimization": True,
            "idempotencyKey": f"test_legacy_{int(time.time())}"
        }
        
        start_time = time.time()
        result = self.make_graphql_request(query, variables)
        end_time = time.time()
        
        return {
            "type": "legacy_ml",
            "duration": end_time - start_time,
            "success": result.get("data", {}).get("generateMlPortfolioRecommendation", {}).get("success", False),
            "message": result.get("data", {}).get("generateMlPortfolioRecommendation", {}).get("message", ""),
            "recommendation": result.get("data", {}).get("generateMlPortfolioRecommendation", {}).get("recommendation"),
            "raw_response": result
        }
    
    def test_institutional_ml_mutation(self) -> Dict:
        """Test the institutional ML portfolio recommendation"""
        query = """
        mutation GenerateInstitutionalPortfolioRecommendation(
            $asOf: Date
            $universe: [String]
            $constraints: OptimizationConstraintsInput
            $modelVersion: String!
            $featureViewVersion: String!
            $idempotencyKey: String
            $includeMarketAnalysis: Boolean
            $dryRun: Boolean
        ) {
            generateInstitutionalPortfolioRecommendation(
                asOf: $asOf
                universe: $universe
                constraints: $constraints
                modelVersion: $modelVersion
                featureViewVersion: $featureViewVersion
                idempotencyKey: $idempotencyKey
                includeMarketAnalysis: $includeMarketAnalysis
                dryRun: $dryRun
            ) {
                success
                message
                recommendation {
                    id
                    riskProfile
                    portfolioAllocation
                    expectedPortfolioReturn
                    riskAssessment
                    mlConfidence
                    mlMarketRegime
                    mlExpectedReturnRange
                    mlRiskScore
                    mlOptimizationMethod
                    auditBlob
                }
                riskMetrics {
                    volatility
                    var95
                    cvar95
                    beta
                    trackingError
                    factorExposures
                    constraintReport
                }
                optimizerStatus
                auditId
            }
        }
        """
        
        variables = {
            "universe": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "SPY", "QQQ", "VTI"],
            "constraints": TEST_CONSTRAINTS,
            "modelVersion": "institutional_v1.0",
            "featureViewVersion": "feature_v1.0",
            "idempotencyKey": f"test_institutional_{int(time.time())}",
            "includeMarketAnalysis": True,
            "dryRun": False
        }
        
        start_time = time.time()
        result = self.make_graphql_request(query, variables)
        end_time = time.time()
        
        return {
            "type": "institutional_ml",
            "duration": end_time - start_time,
            "success": result.get("data", {}).get("generateInstitutionalPortfolioRecommendation", {}).get("success", False),
            "message": result.get("data", {}).get("generateInstitutionalPortfolioRecommendation", {}).get("message", ""),
            "recommendation": result.get("data", {}).get("generateInstitutionalPortfolioRecommendation", {}).get("recommendation"),
            "risk_metrics": result.get("data", {}).get("generateInstitutionalPortfolioRecommendation", {}).get("riskMetrics"),
            "optimizer_status": result.get("data", {}).get("generateInstitutionalPortfolioRecommendation", {}).get("optimizerStatus"),
            "audit_id": result.get("data", {}).get("generateInstitutionalPortfolioRecommendation", {}).get("auditId"),
            "raw_response": result
        }
    
    def test_dry_run_institutional(self) -> Dict:
        """Test institutional ML mutation in dry-run mode"""
        query = """
        mutation GenerateInstitutionalPortfolioRecommendation(
            $constraints: OptimizationConstraintsInput
            $modelVersion: String!
            $featureViewVersion: String!
            $dryRun: Boolean
        ) {
            generateInstitutionalPortfolioRecommendation(
                constraints: $constraints
                modelVersion: $modelVersion
                featureViewVersion: $featureViewVersion
                dryRun: $dryRun
            ) {
                success
                message
                riskMetrics {
                    volatility
                    var95
                    cvar95
                    constraintReport
                }
                optimizerStatus
            }
        }
        """
        
        variables = {
            "constraints": TEST_CONSTRAINTS,
            "modelVersion": "institutional_v1.0",
            "featureViewVersion": "feature_v1.0",
            "dryRun": True
        }
        
        start_time = time.time()
        result = self.make_graphql_request(query, variables)
        end_time = time.time()
        
        return {
            "type": "institutional_dry_run",
            "duration": end_time - start_time,
            "success": result.get("data", {}).get("generateInstitutionalPortfolioRecommendation", {}).get("success", False),
            "message": result.get("data", {}).get("generateInstitutionalPortfolioRecommendation", {}).get("message", ""),
            "risk_metrics": result.get("data", {}).get("generateInstitutionalPortfolioRecommendation", {}).get("riskMetrics"),
            "optimizer_status": result.get("data", {}).get("generateInstitutionalPortfolioRecommendation", {}).get("optimizerStatus"),
            "raw_response": result
        }
    
    def test_market_analysis(self) -> Dict:
        """Test ML market analysis"""
        query = """
        mutation GetMLMarketAnalysis($includeRegimePrediction: Boolean, $includeSectorAnalysis: Boolean, $includeEconomicIndicators: Boolean) {
            getMlMarketAnalysis(
                includeRegimePrediction: $includeRegimePrediction
                includeSectorAnalysis: $includeSectorAnalysis
                includeEconomicIndicators: $includeEconomicIndicators
            ) {
                success
                message
                marketAnalysis
                mlPredictions
            }
        }
        """
        
        variables = {
            "includeRegimePrediction": True,
            "includeSectorAnalysis": True,
            "includeEconomicIndicators": True
        }
        
        start_time = time.time()
        result = self.make_graphql_request(query, variables)
        end_time = time.time()
        
        return {
            "type": "market_analysis",
            "duration": end_time - start_time,
            "success": result.get("data", {}).get("getMlMarketAnalysis", {}).get("success", False),
            "message": result.get("data", {}).get("getMlMarketAnalysis", {}).get("message", ""),
            "market_analysis": result.get("data", {}).get("getMlMarketAnalysis", {}).get("marketAnalysis"),
            "ml_predictions": result.get("data", {}).get("getMlMarketAnalysis", {}).get("mlPredictions"),
            "raw_response": result
        }
    
    def test_service_status(self) -> Dict:
        """Test ML service status"""
        query = """
        mutation GetMLServiceStatus {
            getMlServiceStatus {
                success
                message
                serviceStatus
            }
        }
        """
        
        start_time = time.time()
        result = self.make_graphql_request(query)
        end_time = time.time()
        
        return {
            "type": "service_status",
            "duration": end_time - start_time,
            "success": result.get("data", {}).get("getMlServiceStatus", {}).get("success", False),
            "message": result.get("data", {}).get("getMlServiceStatus", {}).get("message", ""),
            "service_status": result.get("data", {}).get("getMlServiceStatus", {}).get("serviceStatus"),
            "raw_response": result
        }
    
    def run_performance_test(self, test_func, iterations: int = 5) -> Dict:
        """Run a test multiple times to measure performance"""
        results = []
        
        for i in range(iterations):
            print(f"  Running iteration {i+1}/{iterations}...")
            result = test_func()
            results.append(result)
            time.sleep(1)  # Brief pause between requests
        
        durations = [r["duration"] for r in results if "duration" in r]
        success_count = sum(1 for r in results if r.get("success", False))
        
        return {
            "test_type": results[0]["type"] if results else "unknown",
            "iterations": iterations,
            "success_count": success_count,
            "success_rate": success_count / iterations if iterations > 0 else 0,
            "avg_duration": statistics.mean(durations) if durations else 0,
            "min_duration": min(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
            "std_duration": statistics.stdev(durations) if len(durations) > 1 else 0,
            "results": results
        }
    
    def run_comprehensive_test(self):
        """Run comprehensive tests on all ML mutations"""
        print("🚀 Starting Comprehensive ML Mutations Test")
        print("=" * 60)
        
        # Test 1: Service Status
        print("\n1. Testing ML Service Status...")
        status_result = self.test_service_status()
        print(f"   Success: {status_result['success']}")
        print(f"   Duration: {status_result['duration']:.3f}s")
        print(f"   Message: {status_result['message']}")
        
        # Test 2: Market Analysis
        print("\n2. Testing Market Analysis...")
        market_result = self.test_market_analysis()
        print(f"   Success: {market_result['success']}")
        print(f"   Duration: {market_result['duration']:.3f}s")
        print(f"   Message: {market_result['message']}")
        
        # Test 3: Legacy ML Mutation (Performance Test)
        print("\n3. Testing Legacy ML Mutation (Performance Test)...")
        legacy_perf = self.run_performance_test(self.test_legacy_ml_mutation, iterations=3)
        print(f"   Success Rate: {legacy_perf['success_rate']:.1%}")
        print(f"   Avg Duration: {legacy_perf['avg_duration']:.3f}s")
        print(f"   Min Duration: {legacy_perf['min_duration']:.3f}s")
        print(f"   Max Duration: {legacy_perf['max_duration']:.3f}s")
        
        # Test 4: Institutional ML Mutation (Performance Test)
        print("\n4. Testing Institutional ML Mutation (Performance Test)...")
        institutional_perf = self.run_performance_test(self.test_institutional_ml_mutation, iterations=3)
        print(f"   Success Rate: {institutional_perf['success_rate']:.1%}")
        print(f"   Avg Duration: {institutional_perf['avg_duration']:.3f}s")
        print(f"   Min Duration: {institutional_perf['min_duration']:.3f}s")
        print(f"   Max Duration: {institutional_perf['max_duration']:.3f}s")
        
        # Test 5: Dry Run Test
        print("\n5. Testing Institutional Dry Run...")
        dry_run_result = self.test_dry_run_institutional()
        print(f"   Success: {dry_run_result['success']}")
        print(f"   Duration: {dry_run_result['duration']:.3f}s")
        print(f"   Message: {dry_run_result['message']}")
        if dry_run_result.get('risk_metrics'):
            print(f"   Risk Metrics: {dry_run_result['risk_metrics']}")
        
        # Store results
        self.results = {
            "service_status": status_result,
            "market_analysis": market_result,
            "legacy_performance": legacy_perf,
            "institutional_performance": institutional_perf,
            "dry_run": dry_run_result
        }
        
        # Generate comparison report
        self.generate_comparison_report()
    
    def generate_comparison_report(self):
        """Generate a detailed comparison report"""
        print("\n" + "=" * 60)
        print("📊 COMPARISON REPORT")
        print("=" * 60)
        
        # Performance Comparison
        print("\n🏃 PERFORMANCE COMPARISON:")
        print("-" * 40)
        
        legacy_perf = self.results.get("legacy_performance", {})
        institutional_perf = self.results.get("institutional_performance", {})
        
        print(f"Legacy ML Mutation:")
        print(f"  • Success Rate: {legacy_perf.get('success_rate', 0):.1%}")
        print(f"  • Avg Duration: {legacy_perf.get('avg_duration', 0):.3f}s")
        print(f"  • Std Deviation: {legacy_perf.get('std_duration', 0):.3f}s")
        
        print(f"\nInstitutional ML Mutation:")
        print(f"  • Success Rate: {institutional_perf.get('success_rate', 0):.1%}")
        print(f"  • Avg Duration: {institutional_perf.get('avg_duration', 0):.3f}s")
        print(f"  • Std Deviation: {institutional_perf.get('std_duration', 0):.3f}s")
        
        # Feature Comparison
        print("\n🔧 FEATURE COMPARISON:")
        print("-" * 40)
        
        print("Legacy Features:")
        print("  ✓ Basic ML scoring")
        print("  ✓ Simple portfolio allocation")
        print("  ✓ Market analysis integration")
        print("  ✓ Caching and idempotency")
        
        print("\nInstitutional Features:")
        print("  ✓ Point-in-time data discipline")
        print("  ✓ Constrained optimization (CVXPY)")
        print("  ✓ Transaction cost modeling")
        print("  ✓ Advanced risk metrics (VaR/CVaR)")
        print("  ✓ Audit trails and reproducibility")
        print("  ✓ Dry-run capability")
        print("  ✓ Rate limiting and security")
        print("  ✓ Comprehensive constraint reporting")
        
        # Error Analysis
        print("\n❌ ERROR ANALYSIS:")
        print("-" * 40)
        
        for test_name, result in self.results.items():
            if isinstance(result, dict) and "results" in result:
                errors = [r for r in result["results"] if not r.get("success", False)]
                if errors:
                    print(f"\n{test_name.upper()}:")
                    for i, error in enumerate(errors[:3]):  # Show first 3 errors
                        print(f"  {i+1}. {error.get('message', 'Unknown error')}")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        print("-" * 40)
        
        if institutional_perf.get('success_rate', 0) > 0.8:
            print("✅ Institutional ML mutations are working well")
        else:
            print("⚠️  Institutional ML mutations need attention")
        
        if institutional_perf.get('avg_duration', 0) < 5.0:
            print("✅ Performance is acceptable for production use")
        else:
            print("⚠️  Performance may need optimization")
        
        print("\n🎯 NEXT STEPS:")
        print("1. Configure Django settings for ML service")
        print("2. Install CVXPY for advanced optimization")
        print("3. Set up point-in-time data snapshots")
        print("4. Configure rate limiting and security")
        print("5. Add comprehensive monitoring and alerting")

def main():
    """Main test execution"""
    print("🧪 ML Mutations Test Suite")
    print("Testing institutional-grade ML mutations vs legacy systems")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"GraphQL Endpoint: {GRAPHQL_ENDPOINT}")
    
    # Check if backend is running
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print("❌ Backend health check failed")
            return
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return
    
    # Run tests
    tester = MLMutationTester()
    tester.run_comprehensive_test()
    
    print("\n🎉 Test suite completed!")

if __name__ == "__main__":
    main()
