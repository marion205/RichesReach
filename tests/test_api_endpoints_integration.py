"""
Comprehensive integration tests for all new API endpoints across Phase 1, 2, and 3
"""

import pytest
import asyncio
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List


class TestPhase1APIEndpoints:
    """Test Phase 1 API endpoints"""
    
    BASE_URL = "http://127.0.0.1:8000"
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        login_data = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        response = requests.post(f"{self.BASE_URL}/auth/login", json=login_data)
        assert response.status_code == 200
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_daily_voice_digest_endpoints(self, auth_headers):
        """Test Daily Voice Digest endpoints"""
        # Test daily digest generation
        digest_data = {
            "user_id": "test_user_123",
            "user_profile": {
                "risk_tolerance": "moderate",
                "investment_goals": ["retirement", "wealth_building"],
                "preferred_content_types": ["market_analysis", "educational"]
            }
        }
        
        response = requests.post(
            f"{self.BASE_URL}/digest/daily",
            json=digest_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "digest_id" in data
        assert "voice_script" in data
        assert "key_insights" in data
        assert "actionable_tips" in data
        assert data["user_id"] == "test_user_123"
        
        # Test regime alert creation
        regime_alert_data = {
            "user_id": "test_user_123",
            "regime_change": {
                "from_regime": "sideways",
                "to_regime": "bull_market",
                "confidence": 0.92,
                "trigger_indicators": ["breakout_volume", "momentum_shift"]
            }
        }
        
        response = requests.post(
            f"{self.BASE_URL}/digest/regime-alert",
            json=regime_alert_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "notification_id" in data
        assert "data" in data
        assert data["data"]["old_regime"] == "sideways_consolidation"
    
    def test_momentum_missions_endpoints(self, auth_headers):
        """Test Momentum Missions endpoints"""
        # Test getting user progress
        response = requests.get(
            f"{self.BASE_URL}/missions/progress/test_user_123",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "current_streak" in data
        assert "total_missions_completed" in data
        
        # Test generating daily mission
        mission_data = {
            "user_id": "test_user_123",
            "mission_type": "learning",
            "difficulty": "intermediate",
            "day_number": 1
        }
        
        response = requests.post(
            f"{self.BASE_URL}/missions/daily",
            json=mission_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "mission_id" in data
        assert "title" in data
        assert "description" in data
        assert data["user_id"] == "test_user_123"
        
        # Test generating recovery ritual
        recovery_data = {
            "user_id": "test_user_123",
            "missed_day": 3
        }
        
        response = requests.post(
            f"{self.BASE_URL}/missions/recovery",
            json=recovery_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "ritual_id" in data
        assert "title" in data
        assert "content" in data
    
    def test_notification_endpoints(self, auth_headers):
        """Test Notification endpoints"""
        # Test getting notification preferences
        response = requests.get(
            f"{self.BASE_URL}/notifications/preferences/test_user_123",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "preferences" in data
        assert "daily_digest_enabled" in data["preferences"]
        assert "regime_alerts_enabled" in data["preferences"]
        
        # Test getting recent notifications
        response = requests.get(
            f"{self.BASE_URL}/notifications/recent/test_user_123?limit=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
        assert isinstance(data["notifications"], list)
        assert len(data["notifications"]) > 0
    
    def test_regime_monitoring_endpoints(self, auth_headers):
        """Test Regime Monitoring endpoints"""
        # Test regime change check
        regime_check_data = {
            "user_id": "test_user_123",
            "market_data": {
                "spy": {"price": 450.25, "volume": 45000000},
                "vix": {"price": 18.75}
            }
        }
        
        response = requests.post(
            f"{self.BASE_URL}/monitoring/regime-check",
            json=regime_check_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "new_regime" in data
        assert "confidence" in data
        assert "regime_change_detected" in data
        
        # Test getting monitoring status
        response = requests.get(
            f"{self.BASE_URL}/monitoring/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "active_monitors" in data
        assert "total_events_detected" in data


class TestPhase2APIEndpoints:
    """Test Phase 2 API endpoints"""
    
    BASE_URL = "http://127.0.0.1:8000"
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        login_data = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        response = requests.post(f"{self.BASE_URL}/auth/login", json=login_data)
        assert response.status_code == 200
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_wealth_circles_endpoints(self, auth_headers):
        """Test Wealth Circles endpoints"""
        # Test creating wealth circle
        circle_data = {
            "name": "Test Wealth Circle",
            "description": "Test description",
            "creator_id": "test_user_123",
            "is_private": False,
            "tags": ["test", "community"],
            "focus_area": "investment"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/community/wealth-circles",
            json=circle_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "circle_id" in data
        assert data["name"] == "Test Wealth Circle"
        assert "test_user_123" in data["moderators"]
        
        # Test getting wealth circles
        response = requests.get(
            f"{self.BASE_URL}/community/wealth-circles?user_id=test_user_123&limit=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "circles" in data
        assert isinstance(data["circles"], list)
        assert len(data["circles"]) > 0
        assert "circle_id" in data["circles"][0]
        assert "name" in data["circles"][0]
        
        # Test creating discussion post
        post_data = {
            "circle_id": "circle_123",
            "author_id": "test_user_123",
            "title": "Test Discussion",
            "content": "Test post content",
            "tags": ["test", "discussion"],
            "user_id": "test_user_123",
            "post_type": "discussion"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/community/discussion-posts",
            json=post_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "post_id" in data
        assert data["title"] == "Test Discussion"
        assert data["user_id"] == "test_user_123"
        
        # Note: GET discussion posts endpoint not implemented in mock server
    
    def test_peer_progress_endpoints(self, auth_headers):
        """Test Peer Progress endpoints"""
        # Test sharing progress
        progress_data = {
            "user_id": "test_user_123",
            "achievement_type": "module_completed",
            "description": "Completed Options Trading Basics",
            "points_earned": 50,
            "is_anonymous": True,
            "progress_type": "learning",
            "title": "Options Trading Basics",
            "unit": "module",
            "value": 1
        }
        
        response = requests.post(
            f"{self.BASE_URL}/community/progress/share",
            json=progress_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "update_id" in data
        assert data["user_id"] == "test_user_123"
        assert data["progress_type"] == "learning"
        
        # Test getting community stats
        response = requests.get(
            f"{self.BASE_URL}/community/progress/stats/community_123",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_members" in data
        assert "active_this_week" in data
        assert "top_achievements" in data
    
    def test_trade_simulator_endpoints(self, auth_headers):
        """Test Trade Simulator endpoints"""
        # Test creating challenge
        challenge_data = {
            "title": "Test Trading Challenge",
            "description": "Test challenge description",
            "type": "prediction",
            "asset": "AAPL",
            "duration_days": 7,
            "reward": "100 points",
            "creator_id": "test_user_123",
            "challenge_type": "prediction",
            "start_date": "2024-01-15T00:00:00Z",
            "end_date": "2024-01-22T23:59:59Z"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/community/challenges",
            json=challenge_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "challenge_id" in data
        assert data["title"] == "Test Trading Challenge"
        assert data["challenge_type"] == "prediction"
        
        # Test getting active challenges
        response = requests.get(
            f"{self.BASE_URL}/community/challenges?limit=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "challenges" in data
        assert isinstance(data["challenges"], list)
        assert len(data["challenges"]) > 0
        assert "challenge_id" in data["challenges"][0]
        
        # Test making prediction
        prediction_data = {
            "challenge_id": "challenge_123",
            "user_id": "test_user_123",
            "prediction": "AAPL will increase by 3%",
            "confidence": 0.85,
            "reasoning": "Strong earnings expected",
            "prediction_type": "price_direction",
            "asset": "AAPL",
            "predicted_value": 150.0
        }
        
        response = requests.post(
            f"{self.BASE_URL}/community/challenges/challenge_123/predictions",
            json=prediction_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "prediction_id" in data
        assert data["challenge_id"] == "challenge_123"
        assert data["confidence"] == 0.85
        
        # Test getting leaderboard
        response = requests.get(
            f"{self.BASE_URL}/community/challenges/challenge_123/leaderboard?limit=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data
        assert isinstance(data["leaderboard"], list)
        assert len(data["leaderboard"]) > 0
        assert "user_id" in data["leaderboard"][0]


class TestPhase3APIEndpoints:
    """Test Phase 3 API endpoints"""
    
    BASE_URL = "http://127.0.0.1:8000"
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        login_data = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        response = requests.post(f"{self.BASE_URL}/auth/login", json=login_data)
        assert response.status_code == 200
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_behavioral_analytics_endpoints(self, auth_headers):
        """Test Behavioral Analytics endpoints"""
        # Test tracking behavior
        behavior_data = {
            "user_id": "test_user_123",
            "event_type": "module_completed",
            "event_data": {
                "module_id": "options_basics",
                "completion_time": 1800,
                "score": 85,
                "attempts": 2
            },
            "session_id": "session_456",
            "device_type": "mobile",
            "behavior_type": "learning"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/personalization/behavior/track",
            json=behavior_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "behavior_id" in data
        assert data["user_id"] == "test_user_123"
        assert data["behavior_type"] == "learning"
        
        # Test getting engagement profile
        response = requests.get(
            f"{self.BASE_URL}/personalization/engagement-profile/test_user_123",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "learning_style" in data
        assert "engagement_score" in data
        
        # Test getting churn prediction
        response = requests.get(
            f"{self.BASE_URL}/personalization/churn-prediction/test_user_123",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "churn_risk" in data
        assert "confidence" in data
        assert "intervention_recommendations" in data
        
        # Test getting behavior patterns
        response = requests.get(
            f"{self.BASE_URL}/personalization/behavior-patterns/test_user_123",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "patterns" in data
        assert isinstance(data["patterns"], list)
        if data["patterns"]:  # If patterns exist
            assert "pattern_type" in data["patterns"][0]
            assert "confidence" in data["patterns"][0]
    
    def test_dynamic_content_endpoints(self, auth_headers):
        """Test Dynamic Content endpoints"""
        # Test content adaptation
        adaptation_data = {
            "user_id": "test_user_123",
            "content_type": "learning_module",
            "topic": "options_trading",
            "user_context": {
                "learning_level": "intermediate",
                "preferred_format": "interactive",
                "time_available": 30,
                "device_type": "mobile"
            },
            "adaptation_requirements": {
                "difficulty_level": "adaptive",
                "format_preference": "interactive"
            },
            "original_content": {
                "title": "Options Trading Basics",
                "difficulty": "beginner",
                "duration": 45
            }
        }
        
        response = requests.post(
            f"{self.BASE_URL}/personalization/content/adapt",
            json=adaptation_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "adaptation_id" in data
        assert data["user_id"] == "test_user_123"
        assert data["adaptation_type"] == "comprehensive"
        
        # Test generating personalized content
        content_data = {
            "user_id": "test_user_123",
            "content_type": "quiz",
            "topic": "risk_management",
            "user_profile": {
                "risk_tolerance": "moderate",
                "learning_style": "visual",
                "experience_level": "intermediate"
            }
        }
        
        response = requests.post(
            f"{self.BASE_URL}/personalization/content/generate",
            json=content_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "content_id" in data
        assert data["user_id"] == "test_user_123"
        assert data["content_type"] == "quiz"
        assert "adaptation_score" in data
        
        # Test getting content recommendations
        response = requests.get(
            f"{self.BASE_URL}/personalization/recommendations/test_user_123?limit=5",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)
        if data["recommendations"]:  # If recommendations exist
            assert "recommendation_id" in data["recommendations"][0]
            assert "relevance_score" in data["recommendations"][0]
        
        # Test getting personalization score
        response = requests.get(
            f"{self.BASE_URL}/personalization/score/test_user_123?content_type=learning_module",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "personalization_score" in data
        assert "content_preferences" in data


class TestCrossPhaseIntegration:
    """Test integration across all phases"""
    
    BASE_URL = "http://127.0.0.1:8000"
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        login_data = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        response = requests.post(f"{self.BASE_URL}/auth/login", json=login_data)
        assert response.status_code == 200
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_complete_user_journey(self, auth_headers):
        """Test complete user journey across all phases"""
        user_id = "integration_test_user"
        
        # Phase 1: Generate daily digest
        digest_data = {
            "user_id": user_id,
            "user_profile": {
                "risk_tolerance": "moderate",
                "preferred_content_types": ["market_analysis"]
            }
        }
        
        response = requests.post(
            f"{self.BASE_URL}/digest/daily",
            json=digest_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        digest = response.json()
        
        # Phase 2: Share progress about digest completion
        progress_data = {
            "user_id": user_id,
            "achievement_type": "digest_completed",
            "description": f"Completed daily digest: {digest['digest_id']}",
            "points_earned": 25,
            "progress_type": "learning",
            "title": "Daily Digest Completed",
            "unit": "digest",
            "value": 1
        }
        
        response = requests.post(
            f"{self.BASE_URL}/community/progress/share",
            json=progress_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        progress = response.json()
        
        # Phase 3: Track behavior and get recommendations
        behavior_data = {
            "user_id": user_id,
            "event_type": "digest_completed",
            "event_data": {
                "digest_id": digest["digest_id"],
                "completion_time": 120,
                "engagement_score": 0.85
            },
            "behavior_type": "learning"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/personalization/behavior/track",
            json=behavior_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        behavior = response.json()
        
        # Get personalized recommendations based on behavior
        response = requests.get(
            f"{self.BASE_URL}/personalization/recommendations/{user_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        recommendations = response.json()
        
        # Verify the complete flow
        assert digest["user_id"] == user_id
        assert progress["user_id"] == user_id
        assert behavior["user_id"] == user_id
        assert "recommendations" in recommendations
        assert isinstance(recommendations["recommendations"], list)
    
    def test_regime_change_triggering_notifications_and_content(self, auth_headers):
        """Test regime change triggering notifications and content adaptation"""
        user_id = "regime_test_user"
        
        # Detect regime change
        regime_data = {
            "user_id": user_id,
            "market_data": {
                "spy": {"price": 450.25, "volume": 50000000},
                "vix": {"price": 15.25}
            }
        }
        
        response = requests.post(
            f"{self.BASE_URL}/monitoring/regime-check",
            json=regime_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        regime_result = response.json()
        
        if regime_result.get("change_detected"):
            # Create regime alert
            alert_data = {
                "user_id": user_id,
                "regime_change": {
                    "from_regime": regime_result.get("previous_regime", "unknown"),
                    "to_regime": regime_result["current_regime"],
                    "confidence": regime_result["confidence"]
                }
            }
            
            response = requests.post(
                f"{self.BASE_URL}/digest/regime-alert",
                json=alert_data,
                headers=auth_headers
            )
            assert response.status_code == 200
            alert = response.json()
            
            # Adapt content based on new regime
            content_data = {
                "user_id": user_id,
                "content_type": "market_commentary",
                "topic": "regime_analysis",
                "user_context": {
                    "current_regime": regime_result["current_regime"],
                    "regime_confidence": regime_result["confidence"]
                }
            }
            
            response = requests.post(
                f"{self.BASE_URL}/personalization/content/adapt",
                json=content_data,
                headers=auth_headers
            )
            assert response.status_code == 200
            adapted_content = response.json()
            
            # Verify integration
            assert alert["user_id"] == user_id
            assert adapted_content["user_id"] == user_id
    
    def test_community_engagement_driving_personalization(self, auth_headers):
        """Test community engagement driving personalization"""
        user_id = "community_test_user"
        
        # Create wealth circle
        circle_data = {
            "name": "Integration Test Circle",
            "description": "Testing community integration",
            "creator_id": user_id,
            "is_private": False,
            "focus_area": "investment"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/community/wealth-circles",
            json=circle_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        circle = response.json()
        
        # Create discussion post
        post_data = {
            "circle_id": circle["circle_id"],
            "author_id": user_id,
            "title": "Integration Test Discussion",
            "content": "Testing community features",
            "user_id": user_id,
            "post_type": "discussion"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/community/discussion-posts",
            json=post_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        post = response.json()
        
        # Track community engagement behavior
        behavior_data = {
            "user_id": user_id,
            "event_type": "community_engagement",
            "event_data": {
                "circle_id": circle["circle_id"],
                "post_id": post["post_id"],
                "engagement_type": "post_created",
                "engagement_duration": 300
            },
            "behavior_type": "social"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/personalization/behavior/track",
            json=behavior_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        behavior = response.json()
        
        # Get updated engagement profile
        response = requests.get(
            f"{self.BASE_URL}/personalization/engagement-profile/{user_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        profile = response.json()
        
        # Get personalized content based on community engagement
        content_data = {
            "user_id": user_id,
            "content_type": "community_content",
            "topic": "wealth_building",
            "user_context": {
                "community_engagement": "high",
                "preferred_community_types": ["wealth_circles"]
            }
        }
        
        response = requests.post(
            f"{self.BASE_URL}/personalization/content/generate",
            json=content_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        personalized_content = response.json()
        
        # Verify complete integration
        assert user_id in circle["moderators"]
        assert post["user_id"] == user_id
        assert behavior["user_id"] == user_id
        assert profile["user_id"] == user_id
        assert personalized_content["user_id"] == user_id


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
