#!/usr/bin/env python3
"""
Comprehensive Endpoint Testing Suite
====================================

Tests all GenAI endpoints, GraphQL operations, and UI field mappings
to ensure 100% functionality without 400/500 errors.
"""

import requests
import json
import time
from typing import Dict, Any, List, Optional
import sys

# Configuration
BASE_URL = "http://127.0.0.1:8124"
GRAPHQL_URL = "http://127.0.0.1:8123/graphql"  # Main server GraphQL
TIMEOUT = 30

class EndpointTester:
    def __init__(self):
        self.results = {
            "genai_endpoints": {},
            "graphql_queries": {},
            "graphql_mutations": {},
            "ui_field_validation": {},
            "summary": {}
        }
        self.test_user_id = "test_user_123"
        
    def test_genai_endpoint(self, endpoint: str, payload: Dict[str, Any], expected_fields: List[str] = None) -> Dict[str, Any]:
        """Test a single GenAI endpoint"""
        url = f"{BASE_URL}{endpoint}"
        
        try:
            response = requests.post(url, json=payload, timeout=TIMEOUT)
            
            result = {
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "has_expected_fields": True,
                "missing_fields": [],
                "response_size": len(response.text)
            }
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    result["response_data"] = data
                    
                    # Check for expected fields
                    if expected_fields:
                        missing = [field for field in expected_fields if field not in data]
                        result["missing_fields"] = missing
                        result["has_expected_fields"] = len(missing) == 0
                        
                except json.JSONDecodeError:
                    result["success"] = False
                    result["error"] = "Invalid JSON response"
            else:
                result["error"] = response.text
                
        except requests.exceptions.RequestException as e:
            result = {
                "status_code": 0,
                "success": False,
                "error": str(e),
                "response_time_ms": 0
            }
            
        return result
    
    def test_graphql_query(self, query: str, variables: Dict[str, Any] = None, expected_fields: List[str] = None) -> Dict[str, Any]:
        """Test a GraphQL query"""
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        try:
            response = requests.post(GRAPHQL_URL, json=payload, timeout=TIMEOUT)
            
            result = {
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "has_expected_fields": True,
                "missing_fields": [],
                "graphql_errors": []
            }
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    result["response_data"] = data
                    
                    # Check for GraphQL errors
                    if "errors" in data:
                        result["graphql_errors"] = data["errors"]
                        result["success"] = False
                    
                    # Check for expected fields in data
                    if expected_fields and "data" in data:
                        missing = [field for field in expected_fields if field not in data["data"]]
                        result["missing_fields"] = missing
                        result["has_expected_fields"] = len(missing) == 0
                        
                except json.JSONDecodeError:
                    result["success"] = False
                    result["error"] = "Invalid JSON response"
            else:
                result["error"] = response.text
                
        except requests.exceptions.RequestException as e:
            result = {
                "status_code": 0,
                "success": False,
                "error": str(e),
                "response_time_ms": 0
            }
            
        return result
    
    def test_all_genai_endpoints(self):
        """Test all GenAI endpoints"""
        print("🧪 Testing GenAI Endpoints...")
        print("=" * 50)
        
        # Test data for each endpoint
        genai_tests = [
            {
                "endpoint": "/tutor/ask",
                "payload": {
                    "user_id": self.test_user_id,
                    "question": "What is compound interest and how does it work?"
                },
                "expected_fields": ["response", "confidence_score"]
            },
            {
                "endpoint": "/tutor/explain",
                "payload": {
                    "user_id": self.test_user_id,
                    "concept": "dollar cost averaging"
                },
                "expected_fields": ["concept", "explanation", "examples", "generated_at"]
            },
            {
                "endpoint": "/tutor/quiz",
                "payload": {
                    "user_id": self.test_user_id,
                    "topic": "Options Trading",
                    "difficulty": "beginner",
                    "num_questions": 3
                },
                "expected_fields": ["topic", "difficulty", "questions", "generated_at"]
            },
            {
                "endpoint": "/tutor/module",
                "payload": {
                    "user_id": self.test_user_id,
                    "topic": "Risk Management",
                    "difficulty": "intermediate"
                },
                "expected_fields": ["title", "sections", "estimated_time"]
            },
            {
                "endpoint": "/tutor/market-commentary",
                "payload": {
                    "user_id": self.test_user_id,
                    "horizon": "daily",
                    "tone": "neutral"
                },
                "expected_fields": ["headline", "summary", "drivers", "generated_at"]
            },
            {
                "endpoint": "/assistant/query",
                "payload": {
                    "user_id": self.test_user_id,
                    "prompt": "How should I diversify my investment portfolio?"
                },
                "expected_fields": ["answer", "disclaimer", "generated_at"]
            },
            {
                "endpoint": "/coach/advise",
                "payload": {
                    "user_id": self.test_user_id,
                    "goal": "Build wealth for retirement",
                    "risk_tolerance": "medium",
                    "horizon": "long"
                },
                "expected_fields": ["overview", "risk_considerations", "controls", "next_steps", "disclaimer"]
            },
            {
                "endpoint": "/coach/strategy",
                "payload": {
                    "user_id": self.test_user_id,
                    "objective": "Generate passive income",
                    "market_view": "bullish"
                },
                "expected_fields": ["strategies", "disclaimer", "generated_at"]
            }
        ]
        
        for test in genai_tests:
            print(f"Testing {test['endpoint']}...")
            result = self.test_genai_endpoint(
                test["endpoint"], 
                test["payload"], 
                test["expected_fields"]
            )
            
            self.results["genai_endpoints"][test["endpoint"]] = result
            
            if result["success"]:
                print(f"  ✅ Status: {result['status_code']} | Time: {result['response_time_ms']:.1f}ms")
                if not result["has_expected_fields"]:
                    print(f"  ⚠️  Missing fields: {result['missing_fields']}")
            else:
                print(f"  ❌ Status: {result['status_code']} | Error: {result.get('error', 'Unknown')}")
            
            time.sleep(0.5)  # Rate limiting
    
    def test_graphql_operations(self):
        """Test GraphQL queries and mutations"""
        print("\n🔍 Testing GraphQL Operations...")
        print("=" * 50)
        
        # Test GraphQL queries
        graphql_queries = [
            {
                "name": "Get User Profile",
                "query": """
                    query GetUserProfile($userId: String!) {
                        userProfile(userId: $userId) {
                            id
                            email
                            firstName
                            lastName
                            riskTolerance
                            investmentGoals
                        }
                    }
                """,
                "variables": {"userId": self.test_user_id},
                "expected_fields": ["userProfile"]
            },
            {
                "name": "Get Watchlist",
                "query": """
                    query GetWatchlist($userId: String!) {
                        watchlist(userId: $userId) {
                            id
                            symbol
                            name
                            price
                            change
                            changePercent
                        }
                    }
                """,
                "variables": {"userId": self.test_user_id},
                "expected_fields": ["watchlist"]
            },
            {
                "name": "Get Portfolio",
                "query": """
                    query GetPortfolio($userId: String!) {
                        portfolio(userId: $userId) {
                            id
                            symbol
                            quantity
                            averagePrice
                            currentPrice
                            totalValue
                            gainLoss
                            gainLossPercent
                        }
                    }
                """,
                "variables": {"userId": self.test_user_id},
                "expected_fields": ["portfolio"]
            }
        ]
        
        for query_test in graphql_queries:
            print(f"Testing GraphQL Query: {query_test['name']}...")
            result = self.test_graphql_query(
                query_test["query"],
                query_test["variables"],
                query_test["expected_fields"]
            )
            
            self.results["graphql_queries"][query_test["name"]] = result
            
            if result["success"] and not result["graphql_errors"]:
                print(f"  ✅ Status: {result['status_code']} | Time: {result['response_time_ms']:.1f}ms")
                if not result["has_expected_fields"]:
                    print(f"  ⚠️  Missing fields: {result['missing_fields']}")
            else:
                print(f"  ❌ Status: {result['status_code']} | Errors: {result.get('graphql_errors', result.get('error', 'Unknown'))}")
        
        # Test GraphQL mutations
        graphql_mutations = [
            {
                "name": "Add to Watchlist",
                "query": """
                    mutation AddToWatchlist($userId: String!, $symbol: String!) {
                        addToWatchlist(userId: $userId, symbol: $symbol) {
                            success
                            message
                            watchlistItem {
                                id
                                symbol
                                name
                            }
                        }
                    }
                """,
                "variables": {"userId": self.test_user_id, "symbol": "AAPL"},
                "expected_fields": ["addToWatchlist"]
            },
            {
                "name": "Update User Profile",
                "query": """
                    mutation UpdateUserProfile($userId: String!, $input: UserProfileInput!) {
                        updateUserProfile(userId: $userId, input: $input) {
                            success
                            message
                            userProfile {
                                id
                                riskTolerance
                                investmentGoals
                            }
                        }
                    }
                """,
                "variables": {
                    "userId": self.test_user_id,
                    "input": {
                        "riskTolerance": "medium",
                        "investmentGoals": ["retirement", "wealth_building"]
                    }
                },
                "expected_fields": ["updateUserProfile"]
            }
        ]
        
        for mutation_test in graphql_mutations:
            print(f"Testing GraphQL Mutation: {mutation_test['name']}...")
            result = self.test_graphql_query(
                mutation_test["query"],
                mutation_test["variables"],
                mutation_test["expected_fields"]
            )
            
            self.results["graphql_mutations"][mutation_test["name"]] = result
            
            if result["success"] and not result["graphql_errors"]:
                print(f"  ✅ Status: {result['status_code']} | Time: {result['response_time_ms']:.1f}ms")
                if not result["has_expected_fields"]:
                    print(f"  ⚠️  Missing fields: {result['missing_fields']}")
            else:
                print(f"  ❌ Status: {result['status_code']} | Errors: {result.get('graphql_errors', result.get('error', 'Unknown'))}")
    
    def validate_ui_field_mappings(self):
        """Validate UI field mappings against API responses"""
        print("\n📱 Validating UI Field Mappings...")
        print("=" * 50)
        
        # UI field mappings for each screen
        ui_mappings = {
            "TutorAskExplainScreen": {
                "endpoint": "/tutor/ask",
                "ui_fields": ["response", "model", "confidence_score"],
                "api_fields": ["response", "confidence_score"]
            },
            "TutorQuizScreen": {
                "endpoint": "/tutor/quiz", 
                "ui_fields": ["topic", "difficulty", "questions", "generated_at"],
                "api_fields": ["topic", "difficulty", "questions", "generated_at"]
            },
            "TutorModuleScreen": {
                "endpoint": "/tutor/module",
                "ui_fields": ["title", "sections", "estimated_time", "difficulty"],
                "api_fields": ["title", "sections", "estimated_time", "difficulty"]
            },
            "MarketCommentaryScreen": {
                "endpoint": "/tutor/market-commentary",
                "ui_fields": ["headline", "summary", "drivers", "sectors", "risks", "opportunities"],
                "api_fields": ["headline", "summary", "drivers", "sectors", "risks", "opportunities"]
            },
            "AssistantChatScreen": {
                "endpoint": "/assistant/query",
                "ui_fields": ["answer", "response", "model", "confidence_score"],
                "api_fields": ["answer", "response", "model", "confidence_score"]
            },
            "TradingCoachScreen": {
                "endpoint": "/coach/advise",
                "ui_fields": ["overview", "risk_considerations", "controls", "next_steps", "disclaimer"],
                "api_fields": ["overview", "risk_considerations", "controls", "next_steps", "disclaimer"]
            }
        }
        
        for screen_name, mapping in ui_mappings.items():
            print(f"Validating {screen_name}...")
            
            # Test the endpoint to get actual response
            test_payload = {
                "user_id": self.test_user_id,
                "question": "test" if "ask" in mapping["endpoint"] else "test",
                "concept": "test" if "explain" in mapping["endpoint"] else None,
                "topic": "test" if "quiz" in mapping["endpoint"] or "module" in mapping["endpoint"] else None,
                "prompt": "test" if "assistant" in mapping["endpoint"] else None,
                "goal": "test" if "coach" in mapping["endpoint"] else None,
                "risk_tolerance": "medium" if "coach" in mapping["endpoint"] else None,
                "horizon": "medium" if "coach" in mapping["endpoint"] else None
            }
            
            # Remove None values
            test_payload = {k: v for k, v in test_payload.items() if v is not None}
            
            result = self.test_genai_endpoint(mapping["endpoint"], test_payload)
            
            validation_result = {
                "endpoint_working": result["success"],
                "ui_fields_covered": [],
                "missing_ui_fields": [],
                "extra_api_fields": []
            }
            
            if result["success"] and "response_data" in result:
                api_data = result["response_data"]
                api_fields = list(api_data.keys())
                
                # Check which UI fields are covered by API
                for ui_field in mapping["ui_fields"]:
                    if ui_field in api_fields:
                        validation_result["ui_fields_covered"].append(ui_field)
                    else:
                        validation_result["missing_ui_fields"].append(ui_field)
                
                # Check for extra API fields not in UI
                for api_field in api_fields:
                    if api_field not in mapping["ui_fields"]:
                        validation_result["extra_api_fields"].append(api_field)
            
            self.results["ui_field_validation"][screen_name] = validation_result
            
            if validation_result["endpoint_working"]:
                coverage = len(validation_result["ui_fields_covered"]) / len(mapping["ui_fields"]) * 100
                print(f"  ✅ Endpoint working | UI Coverage: {coverage:.1f}%")
                if validation_result["missing_ui_fields"]:
                    print(f"  ⚠️  Missing UI fields: {validation_result['missing_ui_fields']}")
                if validation_result["extra_api_fields"]:
                    print(f"  ℹ️  Extra API fields: {validation_result['extra_api_fields']}")
            else:
                print(f"  ❌ Endpoint not working")
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n📊 Test Summary...")
        print("=" * 50)
        
        # GenAI endpoints summary
        genai_success = sum(1 for r in self.results["genai_endpoints"].values() if r["success"])
        genai_total = len(self.results["genai_endpoints"])
        
        # GraphQL queries summary
        graphql_success = sum(1 for r in self.results["graphql_queries"].values() if r["success"] and not r["graphql_errors"])
        graphql_total = len(self.results["graphql_queries"])
        
        # GraphQL mutations summary
        mutation_success = sum(1 for r in self.results["graphql_mutations"].values() if r["success"] and not r["graphql_errors"])
        mutation_total = len(self.results["graphql_mutations"])
        
        # UI validation summary
        ui_working = sum(1 for r in self.results["ui_field_validation"].values() if r["endpoint_working"])
        ui_total = len(self.results["ui_field_validation"])
        
        self.results["summary"] = {
            "genai_endpoints": {"success": genai_success, "total": genai_total, "rate": genai_success/genai_total*100},
            "graphql_queries": {"success": graphql_success, "total": graphql_total, "rate": graphql_success/graphql_total*100 if graphql_total > 0 else 0},
            "graphql_mutations": {"success": mutation_success, "total": mutation_total, "rate": mutation_success/mutation_total*100 if mutation_total > 0 else 0},
            "ui_validation": {"working": ui_working, "total": ui_total, "rate": ui_working/ui_total*100}
        }
        
        print(f"GenAI Endpoints: {genai_success}/{genai_total} ({genai_success/genai_total*100:.1f}%)")
        print(f"GraphQL Queries: {graphql_success}/{graphql_total} ({graphql_success/graphql_total*100:.1f}%)")
        print(f"GraphQL Mutations: {mutation_success}/{mutation_total} ({mutation_success/mutation_total*100:.1f}%)")
        print(f"UI Field Validation: {ui_working}/{ui_total} ({ui_working/ui_total*100:.1f}%)")
        
        # Overall health
        overall_success = (genai_success + graphql_success + mutation_success + ui_working)
        overall_total = (genai_total + graphql_total + mutation_total + ui_total)
        overall_rate = overall_success / overall_total * 100
        
        print(f"\n🎯 Overall Health: {overall_success}/{overall_total} ({overall_rate:.1f}%)")
        
        if overall_rate >= 90:
            print("🎉 Excellent! System is production-ready!")
        elif overall_rate >= 75:
            print("✅ Good! Minor issues to address.")
        elif overall_rate >= 50:
            print("⚠️  Fair. Several issues need attention.")
        else:
            print("❌ Poor. Major issues require immediate attention.")
    
    def save_results(self, filename: str = "comprehensive_test_results.json"):
        """Save test results to file"""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\n💾 Results saved to {filename}")

def main():
    """Main test execution"""
    print("🚀 Comprehensive Endpoint Testing Suite")
    print("=" * 60)
    
    tester = EndpointTester()
    
    try:
        # Test all components
        tester.test_all_genai_endpoints()
        tester.test_graphql_operations()
        tester.validate_ui_field_mappings()
        tester.generate_summary()
        tester.save_results()
        
    except KeyboardInterrupt:
        print("\n⏹️  Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
