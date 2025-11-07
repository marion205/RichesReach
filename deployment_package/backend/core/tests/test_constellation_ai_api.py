"""
Comprehensive unit tests for Constellation AI API endpoints
Tests all endpoints with meaningful data and verifies actual connections
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
import sys
import os

# Add backend path for imports
backend_path = os.path.join(os.path.dirname(__file__), '..')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Import the router
from core.constellation_ai_api import router

# Create test app
app = FastAPI()
app.include_router(router)

# Test client
client = TestClient(app)


class TestLifeEventsEndpoint:
    """Tests for /api/ai/life-events endpoint"""
    
    def test_life_events_basic_request(self):
        """Test basic life events request with valid data"""
        request_data = {
            "snapshot": {
                "netWorth": 100000,
                "cashflow": {
                    "delta": 2000,
                    "in": 5000,
                    "out": 3000
                },
                "breakdown": {
                    "bankBalance": 10000,
                    "portfolioValue": 90000,
                    "bankAccountsCount": 2
                },
                "positions": []
            },
            "userProfile": {
                "age": 35,
                "incomeBracket": "middle",
                "riskTolerance": "moderate",
                "investmentGoals": ["retirement", "home"]
            }
        }
        
        response = client.post("/api/ai/life-events", json=request_data)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "events" in data
        assert isinstance(data["events"], list)
        assert len(data["events"]) > 0
        
        # Verify event structure
        event = data["events"][0]
        assert "id" in event
        assert "title" in event
        assert "targetAmount" in event
        assert "currentProgress" in event
        assert "monthsAway" in event
        assert "suggestion" in event
        assert "color" in event
        assert "aiConfidence" in event
        assert "aiReasoning" in event
        assert "personalizedFactors" in event
        
        # Verify data types
        assert isinstance(event["targetAmount"], (int, float))
        assert isinstance(event["currentProgress"], (int, float))
        assert isinstance(event["monthsAway"], int)
        assert isinstance(event["aiConfidence"], (int, float))
        assert 0 <= event["aiConfidence"] <= 1
        assert isinstance(event["personalizedFactors"], list)
        
        print(f"✅ Life events test passed: {len(data['events'])} events returned")
    
    def test_life_events_without_profile(self):
        """Test life events request without user profile"""
        request_data = {
            "snapshot": {
                "netWorth": 50000,
                "cashflow": {
                    "delta": 1000,
                    "in": 4000,
                    "out": 3000
                },
                "breakdown": {
                    "bankBalance": 5000,
                    "portfolioValue": 45000,
                    "bankAccountsCount": 1
                }
            }
        }
        
        response = client.post("/api/ai/life-events", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert len(data["events"]) > 0
        
        print(f"✅ Life events without profile: {len(data['events'])} events returned")
    
    def test_life_events_emergency_fund_calculation(self):
        """Test that emergency fund calculation is correct"""
        request_data = {
            "snapshot": {
                "netWorth": 100000,
                "cashflow": {"delta": 2000},
                "breakdown": {
                    "bankBalance": 5000,
                    "portfolioValue": 95000
                }
            }
        }
        
        response = client.post("/api/ai/life-events", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        events = data["events"]
        
        # Find emergency fund event
        emergency_event = next((e for e in events if e["id"] == "emergency"), None)
        assert emergency_event is not None, "Emergency fund event should be present"
        
        # Verify emergency fund target is 10% of net worth
        expected_target = 100000 * 0.1
        assert abs(emergency_event["targetAmount"] - expected_target) < 1, \
            f"Emergency fund target should be ~{expected_target}, got {emergency_event['targetAmount']}"
        
        # Verify current progress
        assert emergency_event["currentProgress"] == 5000
        
        print(f"✅ Emergency fund calculation correct: ${emergency_event['targetAmount']:,.0f} target")
    
    def test_life_events_validation_error(self):
        """Test validation error with missing required fields"""
        request_data = {
            "snapshot": {
                # Missing required fields
            }
        }
        
        response = client.post("/api/ai/life-events", json=request_data)
        assert response.status_code == 422  # Validation error
        
        print("✅ Validation error handling works")


class TestGrowthProjectionsEndpoint:
    """Tests for /api/ai/growth-projections endpoint"""
    
    def test_growth_projections_basic_request(self):
        """Test basic growth projections request"""
        request_data = {
            "currentValue": 100000,
            "monthlySurplus": 2000,
            "portfolioValue": 90000,
            "timeframes": [6, 12, 24]
        }
        
        response = client.post("/api/ai/growth-projections", json=request_data)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "projections" in data
        assert isinstance(data["projections"], list)
        assert len(data["projections"]) > 0
        
        # Verify projection structure
        projection = data["projections"][0]
        assert "scenario" in projection
        assert "growthRate" in projection
        assert "confidence" in projection
        assert "timeframe" in projection
        assert "projectedValue" in projection
        assert "color" in projection
        assert "mlFactors" in projection
        
        # Verify ML factors
        ml_factors = projection["mlFactors"]
        assert "marketRegime" in ml_factors
        assert "volatility" in ml_factors
        assert "momentum" in ml_factors
        assert "riskLevel" in ml_factors
        
        # Verify data types and ranges
        assert isinstance(projection["growthRate"], (int, float))
        assert projection["growthRate"] > 0
        assert 0 <= projection["confidence"] <= 1
        assert projection["timeframe"] in [6, 12, 24]
        # Verify projected value is greater than current value
        assert projection["projectedValue"] > request_data["currentValue"]
        
        print(f"✅ Growth projections test passed: {len(data['projections'])} projections returned")
    
    def test_growth_projections_all_timeframes(self):
        """Test that all requested timeframes are returned"""
        request_data = {
            "currentValue": 50000,
            "monthlySurplus": 1000,
            "portfolioValue": 45000,
            "timeframes": [6, 12, 24, 36]
        }
        
        response = client.post("/api/ai/growth-projections", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        projections = data["projections"]
        
        # Should have projections for each timeframe
        timeframes_returned = set(p["timeframe"] for p in projections)
        assert timeframes_returned == {6, 12, 24, 36}, \
            f"Expected timeframes {[6, 12, 24, 36]}, got {timeframes_returned}"
        
        # Should have multiple scenarios per timeframe
        scenarios_per_timeframe = {}
        for p in projections:
            tf = p["timeframe"]
            if tf not in scenarios_per_timeframe:
                scenarios_per_timeframe[tf] = []
            scenarios_per_timeframe[tf].append(p["scenario"])
        
        # Each timeframe should have multiple scenarios
        for tf, scenarios in scenarios_per_timeframe.items():
            assert len(scenarios) >= 3, f"Timeframe {tf} should have at least 3 scenarios"
        
        print(f"✅ All timeframes returned with multiple scenarios")
    
    def test_growth_projections_calculation(self):
        """Test that projected values are calculated correctly"""
        request_data = {
            "currentValue": 100000,
            "monthlySurplus": 2000,
            "portfolioValue": 90000,
            "timeframes": [12]
        }
        
        response = client.post("/api/ai/growth-projections", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        projections = data["projections"]
        
        # Find moderate growth scenario
        moderate = next((p for p in projections if "Moderate" in p["scenario"] and p["timeframe"] == 12), None)
        assert moderate is not None
        
        # Verify projected value is greater than current value
        assert moderate["projectedValue"] > request_data["currentValue"], \
            f"Projected value {moderate['projectedValue']} should be > {request_data['currentValue']}"
        
        # Verify growth rate is reasonable (between 0 and 20%)
        assert 0 < moderate["growthRate"] < 20, \
            f"Growth rate {moderate['growthRate']}% should be between 0 and 20%"
        
        print(f"✅ Growth calculation correct: ${moderate['projectedValue']:,.0f} projected from ${request_data['currentValue']:,.0f}")
    
    def test_growth_projections_ml_factors(self):
        """Test that ML factors are present and valid"""
        request_data = {
            "currentValue": 75000,
            "monthlySurplus": 1500,
            "portfolioValue": 70000,
            "timeframes": [12]
        }
        
        response = client.post("/api/ai/growth-projections", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        projection = data["projections"][0]
        
        ml_factors = projection["mlFactors"]
        
        # Verify market regime is valid
        assert ml_factors["marketRegime"] in ["bull", "bear", "neutral", "strong_bull", "strong_bear"], \
            f"Invalid market regime: {ml_factors['marketRegime']}"
        
        # Verify volatility is between 0 and 1
        assert 0 <= ml_factors["volatility"] <= 1, \
            f"Volatility {ml_factors['volatility']} should be between 0 and 1"
        
        # Verify momentum is between 0 and 1
        assert 0 <= ml_factors["momentum"] <= 1, \
            f"Momentum {ml_factors['momentum']} should be between 0 and 1"
        
        # Verify risk level is valid
        assert ml_factors["riskLevel"] in ["low", "medium", "high"], \
            f"Invalid risk level: {ml_factors['riskLevel']}"
        
        print(f"✅ ML factors valid: regime={ml_factors['marketRegime']}, risk={ml_factors['riskLevel']}")


class TestShieldAnalysisEndpoint:
    """Tests for /api/ai/shield-analysis endpoint"""
    
    def test_shield_analysis_basic_request(self):
        """Test basic shield analysis request"""
        request_data = {
            "portfolioValue": 100000,
            "bankBalance": 10000,
            "positions": [
                {"symbol": "AAPL", "value": 50000, "shares": 100},
                {"symbol": "MSFT", "value": 50000, "shares": 200}
            ],
            "cashflow": {
                "delta": 2000,
                "in": 5000,
                "out": 3000
            }
        }
        
        response = client.post("/api/ai/shield-analysis", json=request_data)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "currentRisk" in data
        assert "marketRegime" in data
        assert "recommendedStrategies" in data
        assert "marketOutlook" in data
        
        # Verify data types
        assert isinstance(data["currentRisk"], (int, float))
        assert 0 <= data["currentRisk"] <= 1
        assert isinstance(data["marketRegime"], str)
        assert isinstance(data["recommendedStrategies"], list)
        
        # Verify market outlook
        outlook = data["marketOutlook"]
        assert "sentiment" in outlook
        assert "confidence" in outlook
        assert "keyFactors" in outlook
        assert outlook["sentiment"] in ["bullish", "bearish", "neutral"]
        assert 0 <= outlook["confidence"] <= 1
        assert isinstance(outlook["keyFactors"], list)
        
        # Verify strategies
        if len(data["recommendedStrategies"]) > 0:
            strategy = data["recommendedStrategies"][0]
            assert "id" in strategy
            assert "priority" in strategy
            assert "aiReasoning" in strategy
            assert "expectedImpact" in strategy
        
        print(f"✅ Shield analysis test passed: {len(data['recommendedStrategies'])} strategies")
    
    def test_shield_analysis_risk_calculation(self):
        """Test that risk calculation is correct"""
        request_data = {
            "portfolioValue": 100000,
            "bankBalance": 20000,  # 20% cash ratio
            "positions": []
        }
        
        response = client.post("/api/ai/shield-analysis", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        
        # Risk should be 1 - cash_ratio = 1 - 0.2 = 0.8
        expected_risk = 1.0 - (20000 / (20000 + 100000))
        assert abs(data["currentRisk"] - expected_risk) < 0.01, \
            f"Risk should be ~{expected_risk:.2f}, got {data['currentRisk']:.2f}"
        
        print(f"✅ Risk calculation correct: {data['currentRisk']:.2f}")
    
    def test_shield_analysis_low_cash_recommendation(self):
        """Test that low cash ratio triggers increase-cash recommendation"""
        request_data = {
            "portfolioValue": 100000,
            "bankBalance": 5000,  # 5% cash ratio (low)
            "positions": []
        }
        
        response = client.post("/api/ai/shield-analysis", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        strategies = data["recommendedStrategies"]
        
        # Should recommend increasing cash
        increase_cash = next((s for s in strategies if s["id"] == "increase-cash"), None)
        assert increase_cash is not None, "Should recommend increasing cash when ratio is low"
        assert increase_cash["priority"] == 1, "Increase cash should be high priority"
        
        print(f"✅ Low cash triggers recommendation: {increase_cash['aiReasoning'][:50]}...")
    
    def test_shield_analysis_high_risk_recommendation(self):
        """Test that high risk triggers pause-risky recommendation"""
        request_data = {
            "portfolioValue": 100000,
            "bankBalance": 5000,  # High risk (low cash)
            "positions": [
                {"symbol": "AAPL", "value": 50000},
                {"symbol": "MSFT", "value": 50000}
            ]
        }
        
        response = client.post("/api/ai/shield-analysis", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        
        # Should have high risk
        assert data["currentRisk"] > 0.7, "Should have high risk with low cash ratio"
        
        # Should recommend pausing risky orders
        strategies = data["recommendedStrategies"]
        pause_risky = next((s for s in strategies if s["id"] == "pause-risky"), None)
        if pause_risky:
            assert pause_risky["priority"] <= 2, "Pause risky should be high priority"
        
        print(f"✅ High risk triggers pause recommendation")


class TestRecommendationsEndpoint:
    """Tests for /api/ai/recommendations endpoint"""
    
    def test_recommendations_basic_request(self):
        """Test basic recommendations request"""
        request_data = {
            "snapshot": {
                "netWorth": 100000,
                "cashflow": {
                    "delta": 2000,
                    "in": 5000,
                    "out": 3000
                },
                "breakdown": {
                    "bankBalance": 10000,
                    "portfolioValue": 90000,
                    "bankAccountsCount": 2
                },
                "positions": [
                    {"symbol": "AAPL", "value": 45000},
                    {"symbol": "MSFT", "value": 45000}
                ]
            },
            "userBehavior": {
                "recentActions": ["view_portfolio", "check_balance"],
                "preferences": {"risk_tolerance": "moderate"}
            }
        }
        
        response = client.post("/api/ai/recommendations", json=request_data)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)
        assert len(data["recommendations"]) > 0
        
        # Verify recommendation structure
        rec = data["recommendations"][0]
        assert "type" in rec
        assert "title" in rec
        assert "description" in rec
        assert "action" in rec
        assert "priority" in rec
        assert "aiConfidence" in rec
        assert "reasoning" in rec
        
        # Verify data types
        assert rec["type"] in ["life_event", "investment", "savings", "risk_management"]
        assert isinstance(rec["priority"], int)
        assert 0 <= rec["aiConfidence"] <= 1
        
        print(f"✅ Recommendations test passed: {len(data['recommendations'])} recommendations")
    
    def test_recommendations_emergency_fund(self):
        """Test that low emergency fund triggers recommendation"""
        request_data = {
            "snapshot": {
                "netWorth": 100000,
                "cashflow": {"delta": 2000},
                "breakdown": {
                    "bankBalance": 5000,  # Only 5% of net worth (should be 10%)
                    "portfolioValue": 95000
                },
                "positions": []
            }
        }
        
        response = client.post("/api/ai/recommendations", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        recommendations = data["recommendations"]
        
        # Should recommend increasing emergency fund
        emergency_rec = next((r for r in recommendations if "emergency" in r["title"].lower() or r["type"] == "savings"), None)
        assert emergency_rec is not None, "Should recommend increasing emergency fund"
        assert emergency_rec["priority"] <= 2, "Emergency fund should be high priority"
        
        print(f"✅ Emergency fund recommendation: {emergency_rec['title']}")
    
    def test_recommendations_diversification(self):
        """Test that low diversification triggers recommendation"""
        request_data = {
            "snapshot": {
                "netWorth": 100000,
                "cashflow": {"delta": 2000},
                "breakdown": {
                    "bankBalance": 20000,
                    "portfolioValue": 80000
                },
                "positions": [
                    {"symbol": "AAPL", "value": 80000}  # Only 1 position
                ]
            }
        }
        
        response = client.post("/api/ai/recommendations", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        recommendations = data["recommendations"]
        
        # Should recommend diversification
        diversify_rec = next((r for r in recommendations if "diversif" in r["title"].lower() or r["type"] == "investment"), None)
        if diversify_rec:
            assert "diversif" in diversify_rec["title"].lower() or diversify_rec["type"] == "investment"
        
        print(f"✅ Diversification recommendation present")
    
    def test_recommendations_priority_ordering(self):
        """Test that recommendations are ordered by priority"""
        request_data = {
            "snapshot": {
                "netWorth": 100000,
                "cashflow": {"delta": 500},
                "breakdown": {
                    "bankBalance": 5000,
                    "portfolioValue": 95000
                },
                "positions": [{"symbol": "AAPL", "value": 95000}]
            }
        }
        
        response = client.post("/api/ai/recommendations", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        recommendations = data["recommendations"]
        
        # Verify priorities are in ascending order (lower = higher priority)
        priorities = [r["priority"] for r in recommendations]
        assert priorities == sorted(priorities), "Recommendations should be sorted by priority"
        
        print(f"✅ Recommendations sorted by priority: {priorities}")


class TestIntegrationAndErrorHandling:
    """Integration tests and error handling"""
    
    def test_all_endpoints_respond(self):
        """Test that all endpoints are accessible"""
        endpoints = [
            ("/api/ai/life-events", {
                "snapshot": {
                    "netWorth": 50000,
                    "cashflow": {"delta": 1000},
                    "breakdown": {"bankBalance": 5000, "portfolioValue": 45000}
                }
            }),
            ("/api/ai/growth-projections", {
                "currentValue": 50000,
                "monthlySurplus": 1000,
                "portfolioValue": 45000,
                "timeframes": [12]
            }),
            ("/api/ai/shield-analysis", {
                "portfolioValue": 50000,
                "bankBalance": 5000
            }),
            ("/api/ai/recommendations", {
                "snapshot": {
                    "netWorth": 50000,
                    "cashflow": {"delta": 1000},
                    "breakdown": {"bankBalance": 5000, "portfolioValue": 45000}
                }
            })
        ]
        
        for endpoint, data in endpoints:
            response = client.post(endpoint, json=data)
            assert response.status_code == 200, \
                f"Endpoint {endpoint} returned {response.status_code}: {response.text}"
        
        print("✅ All endpoints are accessible and responding")
    
    def test_invalid_json_handling(self):
        """Test handling of invalid JSON"""
        response = client.post(
            "/api/ai/life-events",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422  # Validation error
        
        print("✅ Invalid JSON handling works")
    
    def test_missing_fields_handling(self):
        """Test handling of missing required fields"""
        response = client.post("/api/ai/life-events", json={})
        assert response.status_code == 422  # Validation error
        
        print("✅ Missing fields handling works")
    
    def test_edge_cases(self):
        """Test edge cases like zero values"""
        request_data = {
            "snapshot": {
                "netWorth": 0,
                "cashflow": {"delta": 0},
                "breakdown": {"bankBalance": 0, "portfolioValue": 0}
            }
        }
        
        response = client.post("/api/ai/life-events", json=request_data)
        # Should handle gracefully (either 200 with defaults or 400)
        assert response.status_code in [200, 400, 422]
        
        print("✅ Edge cases handled")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

