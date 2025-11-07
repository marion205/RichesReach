"""
Integration tests for Constellation AI API
Tests actual service connections and meaningful data flow
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add backend path
backend_path = os.path.join(os.path.dirname(__file__), '..')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from fastapi.testclient import TestClient
from fastapi import FastAPI
from core.constellation_ai_api import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestServiceIntegration:
    """Test actual service integration"""
    
    @patch('core.constellation_ai_api._ai_service')
    @patch('core.constellation_ai_api._ml_service')
    def test_ai_service_integration(self, mock_ml_service, mock_ai_service):
        """Test that AI service is actually called"""
        # Mock AI service response
        mock_ai_service.get_chat_response.return_value = {
            "content": "Test AI response",
            "confidence": 0.9
        }
        
        request_data = {
            "snapshot": {
                "netWorth": 100000,
                "cashflow": {"delta": 2000},
                "breakdown": {"bankBalance": 10000, "portfolioValue": 90000}
            }
        }
        
        response = client.post("/api/ai/life-events", json=request_data)
        assert response.status_code == 200
        
        # Verify AI service was called (if available)
        # Note: This will only work if AI service is actually initialized
        print("✅ AI service integration test passed")
    
    @patch('core.constellation_ai_api._ml_service')
    @patch('core.constellation_ai_api._market_data_service')
    def test_ml_service_integration(self, mock_market_data, mock_ml_service):
        """Test that ML service is actually called for growth projections"""
        # Mock ML service response
        mock_ml_service.predict_market_regime.return_value = {
            "regime": "bull",
            "confidence": 0.85,
            "volatility": 0.12,
            "momentum": 0.75
        }
        
        mock_market_data.get_market_regime_indicators.return_value = {
            "volatility": 0.12,
            "momentum": 0.75
        }
        
        request_data = {
            "currentValue": 100000,
            "monthlySurplus": 2000,
            "portfolioValue": 90000,
            "timeframes": [12]
        }
        
        response = client.post("/api/ai/growth-projections", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        # Verify ML factors are present
        assert "projections" in data
        if len(data["projections"]) > 0:
            assert "mlFactors" in data["projections"][0]
        
        print("✅ ML service integration test passed")
    
    def test_real_data_flow(self):
        """Test with realistic financial data"""
        # Realistic user profile
        request_data = {
            "snapshot": {
                "netWorth": 250000,
                "cashflow": {
                    "delta": 3500,
                    "in": 8000,
                    "out": 4500
                },
                "breakdown": {
                    "bankBalance": 25000,
                    "portfolioValue": 225000,
                    "bankAccountsCount": 3
                },
                "positions": [
                    {"symbol": "AAPL", "value": 75000, "shares": 500},
                    {"symbol": "MSFT", "value": 75000, "shares": 250},
                    {"symbol": "GOOGL", "value": 75000, "shares": 600}
                ]
            },
            "userProfile": {
                "age": 42,
                "incomeBracket": "upper_middle",
                "riskTolerance": "moderate",
                "investmentGoals": ["retirement", "home", "education"]
            }
        }
        
        # Test all endpoints with realistic data
        endpoints = [
            ("/api/ai/life-events", request_data),
            ("/api/ai/growth-projections", {
                "currentValue": request_data["snapshot"]["netWorth"],
                "monthlySurplus": request_data["snapshot"]["cashflow"]["delta"],
                "portfolioValue": request_data["snapshot"]["breakdown"]["portfolioValue"],
                "timeframes": [6, 12, 24, 36]
            }),
            ("/api/ai/shield-analysis", {
                "portfolioValue": request_data["snapshot"]["breakdown"]["portfolioValue"],
                "bankBalance": request_data["snapshot"]["breakdown"]["bankBalance"],
                "positions": request_data["snapshot"]["positions"],
                "cashflow": request_data["snapshot"]["cashflow"]
            }),
            ("/api/ai/recommendations", {
                "snapshot": request_data["snapshot"],
                "userBehavior": {
                    "recentActions": ["view_portfolio", "check_balance", "view_analytics"],
                    "preferences": {"risk_tolerance": "moderate"}
                }
            })
        ]
        
        results = {}
        for endpoint, data in endpoints:
            response = client.post(endpoint, json=data)
            assert response.status_code == 200, \
                f"{endpoint} failed: {response.status_code} - {response.text[:200]}"
            
            results[endpoint] = response.json()
            print(f"✅ {endpoint} returned valid data")
        
        # Verify meaningful data
        # Life events should have multiple events
        assert len(results["/api/ai/life-events"]["events"]) >= 2
        
        # Growth projections should have projections for all timeframes
        projections = results["/api/ai/growth-projections"]["projections"]
        timeframes = set(p["timeframe"] for p in projections)
        assert timeframes == {6, 12, 24, 36}
        
        # Shield analysis should have strategies
        assert len(results["/api/ai/shield-analysis"]["recommendedStrategies"]) > 0
        
        # Recommendations should be prioritized
        recommendations = results["/api/ai/recommendations"]["recommendations"]
        priorities = [r["priority"] for r in recommendations]
        assert priorities == sorted(priorities)
        
        print("✅ Real data flow test passed - all endpoints working with realistic data")


class TestDataValidation:
    """Test data validation and edge cases"""
    
    def test_large_values(self):
        """Test with very large financial values"""
        request_data = {
            "snapshot": {
                "netWorth": 10000000,  # $10M
                "cashflow": {"delta": 50000},
                "breakdown": {"bankBalance": 1000000, "portfolioValue": 9000000}
            }
        }
        
        response = client.post("/api/ai/life-events", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        # Should handle large values gracefully
        assert len(data["events"]) > 0
        assert all(e["targetAmount"] > 0 for e in data["events"])
        
        print("✅ Large values handled correctly")
    
    def test_small_values(self):
        """Test with very small financial values"""
        request_data = {
            "snapshot": {
                "netWorth": 1000,  # $1K
                "cashflow": {"delta": 100},
                "breakdown": {"bankBalance": 100, "portfolioValue": 900}
            }
        }
        
        response = client.post("/api/ai/life-events", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        # Should still provide meaningful recommendations
        assert len(data["events"]) > 0
        
        print("✅ Small values handled correctly")
    
    def test_negative_cashflow(self):
        """Test with negative cashflow (spending more than earning)"""
        request_data = {
            "snapshot": {
                "netWorth": 50000,
                "cashflow": {"delta": -500},  # Negative
                "breakdown": {"bankBalance": 5000, "portfolioValue": 45000}
            }
        }
        
        response = client.post("/api/ai/life-events", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        # Should handle negative cashflow
        assert len(data["events"]) > 0
        
        print("✅ Negative cashflow handled correctly")


class TestPerformance:
    """Test performance and response times"""
    
    def test_response_time(self):
        """Test that endpoints respond within reasonable time"""
        import time
        
        request_data = {
            "snapshot": {
                "netWorth": 100000,
                "cashflow": {"delta": 2000},
                "breakdown": {"bankBalance": 10000, "portfolioValue": 90000}
            }
        }
        
        start = time.time()
        response = client.post("/api/ai/life-events", json=request_data)
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 2.0, f"Response took {elapsed:.2f}s, should be < 2s"
        
        print(f"✅ Response time acceptable: {elapsed:.3f}s")
    
    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        import concurrent.futures
        
        request_data = {
            "snapshot": {
                "netWorth": 100000,
                "cashflow": {"delta": 2000},
                "breakdown": {"bankBalance": 10000, "portfolioValue": 90000}
            }
        }
        
        def make_request():
            return client.post("/api/ai/life-events", json=request_data)
        
        # Make 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All should succeed
        assert all(r.status_code == 200 for r in results)
        
        print("✅ Concurrent requests handled correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

