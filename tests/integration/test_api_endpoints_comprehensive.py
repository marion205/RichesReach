"""
Comprehensive integration tests for all API endpoints in RichesReach AI platform.
"""

import pytest
import asyncio
import json
from typing import Dict, Any
import httpx
from fastapi.testclient import TestClient

try:
    from test_server_minimal import app
except ModuleNotFoundError:
    pytest.skip("test_server_minimal is not available in this environment", allow_module_level=True)

class TestAuthenticationEndpoints:
    """Comprehensive tests for authentication endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_login_success(self, client):
        """Test successful login."""
        response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "testpass123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user_id" in data
        assert data["user_id"] == "test_user_123"
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post("/auth/login", json={
            "email": "invalid@example.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_login_missing_fields(self, client):
        """Test login with missing fields."""
        response = client.post("/auth/login", json={
            "email": "test@example.com"
            # Missing password
        })
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_login_case_insensitive_email(self, client):
        """Test login with case insensitive email."""
        response = client.post("/auth/login", json={
            "email": "TEST@EXAMPLE.COM",
            "password": "testpass123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

class TestAIServiceEndpoints:
    """Comprehensive tests for AI service endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers."""
        return {"Authorization": "Bearer test_token_123"}
    
    def test_tutor_ask_endpoint(self, client, auth_headers):
        """Test AI Tutor ask endpoint."""
        response = client.post("/tutor/ask", json={
            "question": "What is options trading?",
            "user_id": "test_user_123",
            "user_profile": {
                "experience_level": "intermediate",
                "risk_tolerance": "moderate"
            }
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "model" in data
        assert "timestamp" in data
        assert data["user_id"] == "test_user_123"
    
    def test_tutor_explain_endpoint(self, client, auth_headers):
        """Test AI Tutor explain endpoint."""
        response = client.post("/tutor/explain", json={
            "concept": "Black-Scholes model",
            "user_id": "test_user_123",
            "user_profile": {
                "experience_level": "intermediate"
            }
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "explanation" in data
        assert "examples" in data
        assert "key_points" in data
        assert data["concept"] == "Black-Scholes model"
    
    def test_tutor_quiz_endpoint(self, client, auth_headers):
        """Test AI Tutor quiz endpoint."""
        response = client.post("/tutor/quiz", json={
            "topic": "Options Trading Basics",
            "user_id": "test_user_123",
            "user_profile": {
                "experience_level": "intermediate"
            },
            "difficulty": "intermediate"
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "quiz_id" in data
        assert "questions" in data
        assert "topic" in data
        assert data["topic"] == "Options Trading Basics"
        assert len(data["questions"]) > 0
    
    def test_tutor_regime_adaptive_quiz_endpoint(self, client, auth_headers):
        """Test regime-adaptive quiz endpoint."""
        response = client.post("/tutor/quiz/regime-adaptive", json={
            "topic": "Market Analysis",
            "user_id": "test_user_123",
            "user_profile": {
                "experience_level": "intermediate"
            }
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "regime_context" in data
        assert "current_regime" in data["regime_context"]
        assert "regime_confidence" in data["regime_context"]
        assert "relevant_strategies" in data["regime_context"]
    
    def test_assistant_query_endpoint(self, client, auth_headers):
        """Test AI Assistant query endpoint."""
        response = client.post("/assistant/query", json={
            "query": "What's the best strategy for a bull market?",
            "user_id": "test_user_123",
            "user_profile": {
                "risk_tolerance": "moderate"
            }
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "sources" in data
        assert "confidence" in data
        assert "disclaimer" in data
        assert data["user_id"] == "test_user_123"
    
    def test_coach_advise_endpoint(self, client, auth_headers):
        """Test Trading Coach advise endpoint."""
        response = client.post("/coach/advise", json={
            "situation": "I want to start options trading",
            "user_id": "test_user_123",
            "user_profile": {
                "experience_level": "beginner",
                "risk_tolerance": "conservative"
            }
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "advice" in data
        assert "risk_level" in data
        assert "recommendations" in data
        assert data["user_id"] == "test_user_123"
    
    def test_coach_strategy_endpoint(self, client, auth_headers):
        """Test Trading Coach strategy endpoint."""
        response = client.post("/coach/strategy", json={
            "market_condition": "bull_market",
            "user_id": "test_user_123",
            "user_profile": {
                "risk_tolerance": "moderate"
            },
            "risk_tolerance": "moderate"
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "strategies" in data
        assert "market_condition" in data
        assert data["market_condition"] == "bull_market"
        assert len(data["strategies"]) > 0

class TestPhase1Endpoints:
    """Comprehensive tests for Phase 1 - Enhanced Retention endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers."""
        return {"Authorization": "Bearer test_token_123"}
    
    def test_daily_digest_endpoint(self, client, auth_headers):
        """Test daily voice digest endpoint."""
        response = client.post("/digest/daily", json={
            "user_id": "test_user_123",
            "user_profile": {
                "preferences": {
                    "duration": "short",
                    "focus_areas": ["market_overview"],
                    "tone": "professional"
                }
            }
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "digest_id" in data
        assert "voice_script" in data
        assert "key_insights" in data
        assert "actionable_tips" in data
        assert "duration_estimate" in data
    
    def test_regime_alert_endpoint(self, client, auth_headers):
        """Test regime alert endpoint."""
        response = client.post("/digest/regime-alert", json={
            "user_id": "test_user_123",
            "user_profile": {
                "risk_tolerance": "moderate"
            },
            "old_regime": "bull_market",
            "new_regime": "correction",
            "confidence": 0.85
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "notification_id" in data
        assert "alert_type" in data
        assert "data" in data
        assert data["data"]["old_regime"] == "bull_market"
        assert data["data"]["new_regime"] == "correction"
    
    def test_missions_progress_endpoint(self, client, auth_headers):
        """Test missions progress endpoint."""
        response = client.get("/missions/progress/test_user_123", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "current_streak" in data
        assert "total_missions_completed" in data
        assert "achievements" in data
        assert "next_milestone" in data
    
    def test_daily_mission_endpoint(self, client, auth_headers):
        """Test daily mission endpoint."""
        response = client.post("/missions/daily", json={
            "user_id": "test_user_123",
            "user_profile": {
                "experience_level": "intermediate"
            },
            "day_number": 1
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "mission_id" in data
        assert "title" in data
        assert "description" in data
        assert "difficulty" in data
        assert "estimated_time" in data
        assert "rewards" in data
        assert data["day_number"] == 1
    
    def test_recovery_ritual_endpoint(self, client, auth_headers):
        """Test recovery ritual endpoint."""
        response = client.post("/missions/recovery", json={
            "user_id": "test_user_123",
            "user_profile": {
                "experience_level": "intermediate"
            },
            "missed_day": 3
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "ritual_id" in data
        assert "content" in data
        assert "steps" in data
        assert "motivation_message" in data
        assert "estimated_duration" in data
    
    def test_notification_preferences_endpoint(self, client, auth_headers):
        """Test notification preferences endpoint."""
        response = client.get("/notifications/preferences/test_user_123", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "preferences" in data
        assert "daily_digest_enabled" in data["preferences"]
        assert "regime_alerts_enabled" in data["preferences"]
    
    def test_recent_notifications_endpoint(self, client, auth_headers):
        """Test recent notifications endpoint."""
        response = client.get("/notifications/recent/test_user_123?limit=10", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
        assert isinstance(data["notifications"], list)
        assert len(data["notifications"]) <= 10
    
    def test_regime_monitoring_endpoint(self, client, auth_headers):
        """Test regime monitoring endpoint."""
        response = client.post("/monitoring/regime-check", json={
            "market_data": {
                "spy": {"price": 450, "volume": 50000000},
                "vix": {"price": 18, "change": -0.05}
            }
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "new_regime" in data
        assert "regime_change_detected" in data
        assert "confidence" in data
        assert "change_reasoning" in data
    
    def test_monitoring_status_endpoint(self, client, auth_headers):
        """Test monitoring status endpoint."""
        response = client.get("/monitoring/status", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "active_monitors" in data
        assert "total_events_detected" in data
        assert "last_check" in data

class TestPhase2Endpoints:
    """Comprehensive tests for Phase 2 - Community endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers."""
        return {"Authorization": "Bearer test_token_123"}
    
    def test_create_wealth_circle_endpoint(self, client, auth_headers):
        """Test create wealth circle endpoint."""
        response = client.post("/community/wealth-circles", json={
            "name": "Options Trading Circle",
            "description": "Learn advanced options strategies",
            "creator_id": "test_user_123",
            "is_private": False,
            "tags": ["options", "trading", "education"],
            "focus_area": "investment"
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "circle_id" in data
        assert "name" in data
        assert "moderators" in data
        assert "test_user_123" in data["moderators"]
        assert data["name"] == "Options Trading Circle"
    
    def test_get_wealth_circles_endpoint(self, client, auth_headers):
        """Test get wealth circles endpoint."""
        response = client.get("/community/wealth-circles?user_id=test_user_123&limit=10", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "circles" in data
        assert isinstance(data["circles"], list)
        assert len(data["circles"]) <= 10
        if data["circles"]:
            assert "circle_id" in data["circles"][0]
            assert "name" in data["circles"][0]
    
    def test_create_discussion_post_endpoint(self, client, auth_headers):
        """Test create discussion post endpoint."""
        response = client.post("/community/discussion-posts", json={
            "circle_id": "circle_123",
            "author_id": "test_user_123",
            "title": "Best Options Strategies for Beginners",
            "content": "What are the safest options strategies to start with?",
            "tags": ["beginner", "options", "strategy"],
            "user_id": "test_user_123",
            "post_type": "discussion"
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "post_id" in data
        assert "title" in data
        assert "user_id" in data
        assert data["user_id"] == "test_user_123"
        assert data["title"] == "Best Options Strategies for Beginners"
    
    def test_share_progress_endpoint(self, client, auth_headers):
        """Test share progress endpoint."""
        response = client.post("/community/progress/share", json={
            "user_id": "test_user_123",
            "progress_type": "learning",
            "title": "Completed Options Trading Module",
            "unit": "module",
            "value": 1,
            "description": "Successfully completed the basics of options trading"
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "progress_id" in data
        assert "user_id" in data
        assert "progress_type" in data
        assert data["user_id"] == "test_user_123"
        assert data["progress_type"] == "learning"
    
    def test_community_stats_endpoint(self, client, auth_headers):
        """Test community stats endpoint."""
        response = client.get("/community/progress/stats/community_123", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "community_id" in data
        assert "total_members" in data
        assert "active_this_week" in data
        assert "achievements_shared" in data
    
    def test_create_challenge_endpoint(self, client, auth_headers):
        """Test create challenge endpoint."""
        response = client.post("/community/challenges", json={
            "challenge_type": "prediction",
            "title": "AAPL Price Prediction Challenge",
            "description": "Predict AAPL's price movement for next week",
            "start_date": "2024-01-15T00:00:00Z",
            "end_date": "2024-01-22T23:59:59Z",
            "asset": "AAPL",
            "entry_fee": 10.0,
            "creator_id": "test_user_123"
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "challenge_id" in data
        assert "challenge_type" in data
        assert "creator_id" in data
        assert data["creator_id"] == "test_user_123"
        assert data["challenge_type"] == "prediction"
    
    def test_get_challenges_endpoint(self, client, auth_headers):
        """Test get challenges endpoint."""
        response = client.get("/community/challenges?limit=10", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "challenges" in data
        assert isinstance(data["challenges"], list)
        assert len(data["challenges"]) <= 10
        if data["challenges"]:
            assert "challenge_id" in data["challenges"][0]
            assert "title" in data["challenges"][0]
    
    def test_make_prediction_endpoint(self, client, auth_headers):
        """Test make prediction endpoint."""
        response = client.post("/community/challenges/challenge_123/predictions", json={
            "user_id": "test_user_123",
            "prediction_type": "price_direction",
            "asset": "AAPL",
            "predicted_value": 150.0,
            "confidence": 0.75,
            "reasoning": "Based on technical analysis and market sentiment"
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "prediction_id" in data
        assert "user_id" in data
        assert "challenge_id" in data
        assert data["user_id"] == "test_user_123"
        assert data["challenge_id"] == "challenge_123"
    
    def test_leaderboard_endpoint(self, client, auth_headers):
        """Test leaderboard endpoint."""
        response = client.get("/community/challenges/challenge_123/leaderboard?limit=10", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data
        assert isinstance(data["leaderboard"], list)
        assert len(data["leaderboard"]) <= 10

class TestPhase3Endpoints:
    """Comprehensive tests for Phase 3 - Advanced Personalization endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers."""
        return {"Authorization": "Bearer test_token_123"}
    
    def test_track_behavior_endpoint(self, client, auth_headers):
        """Test track behavior endpoint."""
        response = client.post("/personalization/behavior/track", json={
            "user_id": "test_user_123",
            "behavior_type": "learning",
            "action": "module_completed",
            "context": {
                "module_id": "module_123",
                "topic": "options_trading",
                "duration": 1800,
                "score": 85
            }
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "event_id" in data
        assert "user_id" in data
        assert "behavior_type" in data
        assert data["user_id"] == "test_user_123"
        assert data["behavior_type"] == "learning"
    
    def test_engagement_profile_endpoint(self, client, auth_headers):
        """Test engagement profile endpoint."""
        response = client.get("/personalization/engagement-profile/test_user_123", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "engagement_score" in data
        assert "preferred_content_types" in data
        assert "learning_velocity" in data
        assert "retention_rate" in data
    
    def test_churn_prediction_endpoint(self, client, auth_headers):
        """Test churn prediction endpoint."""
        response = client.get("/personalization/churn-prediction/test_user_123", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "churn_risk" in data
        assert "risk_factors" in data
        assert "intervention_recommendations" in data
        assert 0 <= data["churn_risk"] <= 1
    
    def test_behavior_patterns_endpoint(self, client, auth_headers):
        """Test behavior patterns endpoint."""
        response = client.get("/personalization/behavior-patterns/test_user_123", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "patterns" in data
        assert isinstance(data["patterns"], list)
        if data["patterns"]:
            assert "pattern_type" in data["patterns"][0]
    
    def test_adapt_content_endpoint(self, client, auth_headers):
        """Test adapt content endpoint."""
        response = client.post("/personalization/content/adapt", json={
            "user_id": "test_user_123",
            "original_content": {
                "title": "Options Trading Basics",
                "difficulty": "beginner",
                "duration": 45,
                "format": "text"
            },
            "user_behavior": {
                "learning_speed": "fast",
                "preferred_format": "interactive",
                "attention_span": "short"
            }
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "adapted_content" in data
        assert "adaptation_reasoning" in data
        assert "adaptation_score" in data
        assert "personalization_metrics" in data
    
    def test_generate_personalized_content_endpoint(self, client, auth_headers):
        """Test generate personalized content endpoint."""
        response = client.post("/personalization/content/generate", json={
            "user_id": "test_user_123",
            "content_type": "learning_module",
            "topic": "Risk Management",
            "difficulty": "intermediate",
            "preferences": {
                "format": "interactive",
                "duration": 30,
                "include_examples": True
            }
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "content_id" in data
        assert "personalized_content" in data
        assert "personalization_score" in data
        assert "content_preferences" in data
    
    def test_content_recommendations_endpoint(self, client, auth_headers):
        """Test content recommendations endpoint."""
        response = client.get("/personalization/recommendations/test_user_123?limit=5", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)
        assert len(data["recommendations"]) <= 5
        if data["recommendations"]:
            assert "recommendation_id" in data["recommendations"][0]
    
    def test_personalization_score_endpoint(self, client, auth_headers):
        """Test personalization score endpoint."""
        response = client.get("/personalization/score/test_user_123?content_type=learning_module", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "personalization_score" in data
        assert "content_preferences" in data
        assert "adaptation_history" in data
        assert 0 <= data["personalization_score"] <= 1

class TestErrorHandling:
    """Comprehensive error handling tests."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_404_endpoint_not_found(self, client):
        """Test 404 for non-existent endpoints."""
        response = client.get("/nonexistent/endpoint")
        assert response.status_code == 404
    
    def test_405_method_not_allowed(self, client):
        """Test 405 for wrong HTTP method."""
        response = client.get("/auth/login")  # Should be POST
        assert response.status_code == 405
    
    def test_422_validation_error(self, client):
        """Test 422 for validation errors."""
        response = client.post("/auth/login", json={
            "email": "invalid-email",  # Invalid email format
            "password": "testpass123"
        })
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_401_unauthorized(self, client):
        """Test 401 for unauthorized requests."""
        response = client.post("/tutor/ask", json={
            "question": "Test question",
            "user_id": "test_user_123"
        })  # No authorization header
        assert response.status_code == 401
    
    def test_500_internal_server_error_handling(self, client):
        """Test 500 error handling."""
        # This would require mocking a service to throw an exception
        # For now, we'll test that the server doesn't crash on malformed requests
        response = client.post("/auth/login", json="invalid json")
        assert response.status_code == 422  # FastAPI handles malformed JSON as 422

class TestPerformanceAndLoad:
    """Performance and load testing."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.mark.performance
    def test_response_times(self, client):
        """Test that endpoints respond within acceptable time limits."""
        import time
        
        endpoints = [
            ("/auth/login", "POST", {"email": "test@example.com", "password": "testpass123"}),
            ("/tutor/ask", "POST", {"question": "Test question", "user_id": "test_user_123"}),
            ("/digest/daily", "POST", {"user_id": "test_user_123"}),
            ("/community/wealth-circles", "GET", None),
            ("/personalization/engagement-profile/test_user_123", "GET", None)
        ]
        
        for endpoint, method, data in endpoints:
            start_time = time.time()
            
            if method == "POST":
                response = client.post(endpoint, json=data)
            else:
                response = client.get(endpoint)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # All endpoints should respond within 2 seconds
            assert response_time < 2.0, f"{endpoint} took {response_time:.2f}s"
            assert response.status_code in [200, 401, 422], f"{endpoint} returned {response.status_code}"
    
    @pytest.mark.performance
    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests."""
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request():
            try:
                response = client.post("/auth/login", json={
                    "email": "test@example.com",
                    "password": "testpass123"
                })
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))
        
        # Create 10 concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should complete successfully
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10, f"Expected 10 results, got {len(results)}"
        assert all(status == 200 for status in results), f"Not all requests succeeded: {results}"

class TestDataValidation:
    """Comprehensive data validation tests."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_required_fields_validation(self, client):
        """Test validation of required fields."""
        # Test missing required fields
        response = client.post("/auth/login", json={})
        assert response.status_code == 422
        
        response = client.post("/tutor/ask", json={
            "question": "Test question"
            # Missing user_id
        })
        assert response.status_code == 422
    
    def test_field_type_validation(self, client):
        """Test validation of field types."""
        # Test wrong field types
        response = client.post("/auth/login", json={
            "email": 123,  # Should be string
            "password": "testpass123"
        })
        assert response.status_code == 422
        
        response = client.post("/tutor/quiz", json={
            "topic": "Test Topic",
            "user_id": "test_user_123",
            "difficulty": 123  # Should be string
        })
        assert response.status_code == 422
    
    def test_field_length_validation(self, client):
        """Test validation of field lengths."""
        # Test extremely long strings
        long_string = "a" * 10000
        response = client.post("/tutor/ask", json={
            "question": long_string,
            "user_id": "test_user_123"
        })
        # Should either accept or reject gracefully
        assert response.status_code in [200, 422]
    
    def test_enum_validation(self, client):
        """Test validation of enum values."""
        # Test invalid enum values
        response = client.post("/coach/strategy", json={
            "market_condition": "invalid_condition",  # Invalid enum value
            "user_id": "test_user_123",
            "risk_tolerance": "moderate"
        })
        assert response.status_code == 422

class TestSecurity:
    """Security testing."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_sql_injection_protection(self, client):
        """Test protection against SQL injection."""
        malicious_input = "'; DROP TABLE users; --"
        response = client.post("/auth/login", json={
            "email": malicious_input,
            "password": "testpass123"
        })
        # Should not crash or execute malicious code
        assert response.status_code in [401, 422]
    
    def test_xss_protection(self, client):
        """Test protection against XSS."""
        xss_payload = "<script>alert('xss')</script>"
        response = client.post("/tutor/ask", json={
            "question": xss_payload,
            "user_id": "test_user_123"
        })
        # Should not execute script
        assert response.status_code in [200, 401, 422]
    
    def test_authentication_bypass_attempts(self, client):
        """Test various authentication bypass attempts."""
        # Test with fake token
        response = client.post("/tutor/ask", json={
            "question": "Test question",
            "user_id": "test_user_123"
        }, headers={"Authorization": "Bearer fake_token"})
        assert response.status_code == 401
        
        # Test with malformed token
        response = client.post("/tutor/ask", json={
            "question": "Test question",
            "user_id": "test_user_123"
        }, headers={"Authorization": "InvalidFormat"})
        assert response.status_code == 401
