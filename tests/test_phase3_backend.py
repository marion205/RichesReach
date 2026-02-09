"""
Unit tests for Phase 3 backend services:
- Behavioral Analytics
- Dynamic Content Adaptation
- Advanced Personalization
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Import the services
try:
    from backend.backend.core.behavioral_analytics_service import BehavioralAnalyticsService
    from backend.backend.core.dynamic_content_service import DynamicContentService
except ModuleNotFoundError:
    pytest.skip("Legacy backend.backend.core module path not available", allow_module_level=True)


class TestBehavioralAnalyticsService:
    """Test Behavioral Analytics Service"""
    
    @pytest.fixture
    def service(self):
        return BehavioralAnalyticsService()
    
    @pytest.fixture
    def mock_behavior_data(self):
        return {
            "user_id": "user_123",
            "event_type": "module_completed",
            "event_data": {
                "module_id": "options_basics",
                "completion_time": 1800,  # 30 minutes
                "score": 85,
                "attempts": 2
            },
            "timestamp": datetime.now(),
            "session_id": "session_456",
            "device_type": "mobile"
        }
    
    @pytest.fixture
    def mock_engagement_profile(self):
        return {
            "user_id": "user_123",
            "learning_style": "visual_auditory",
            "risk_tolerance": "moderate",
            "investment_horizon": "medium_term",
            "preferred_content_types": ["interactive", "video", "quizzes"],
            "active_days_last_30": 25,
            "modules_completed": 12,
            "quizzes_passed": 8,
            "average_session_duration": 1800,
            "peak_activity_hours": [9, 14, 20],
            "engagement_score": 0.85
        }
    
    @pytest.mark.asyncio
    async def test_track_behavior(self, service, mock_behavior_data):
        """Test tracking user behavior"""
        with patch.object(service, '_save_behavior_event', return_value="event_789"):
            result = await service.track_behavior(mock_behavior_data)
            
            assert result is not None
            assert "event_id" in result
            assert result["user_id"] == "user_123"
            assert result["event_type"] == "module_completed"
    
    @pytest.mark.asyncio
    async def test_get_engagement_profile(self, service, mock_engagement_profile):
        """Test getting user engagement profile"""
        with patch.object(service, '_analyze_user_behavior', return_value=mock_engagement_profile):
            result = await service.get_engagement_profile("user_123")
            
            assert result is not None
            assert result["user_id"] == "user_123"
            assert result["learning_style"] == "visual_auditory"
            assert result["engagement_score"] == 0.85
            assert "preferred_content_types" in result
    
    @pytest.mark.asyncio
    async def test_get_churn_prediction(self, service):
        """Test getting churn prediction"""
        mock_churn_data = {
            "user_id": "user_123",
            "risk_level": "low",
            "confidence": 0.92,
            "risk_factors": [],
            "retention_strategies": [
                "Continue personalized content delivery",
                "Offer advanced learning paths"
            ],
            "predicted_retention_days": 90
        }
        
        with patch.object(service, '_predict_churn', return_value=mock_churn_data):
            result = await service.get_churn_prediction("user_123")
            
            assert result is not None
            assert result["user_id"] == "user_123"
            assert result["risk_level"] == "low"
            assert result["confidence"] == 0.92
            assert "retention_strategies" in result
    
    @pytest.mark.asyncio
    async def test_get_behavior_patterns(self, service):
        """Test getting behavior patterns"""
        mock_patterns = [
            {
                "pattern_id": "pattern_1",
                "name": "Passive Learner",
                "description": "Prefers consuming content over interactive exercises",
                "impact": "Slower skill application",
                "recommendation": "Suggest interactive quizzes after modules",
                "confidence": 0.85,
                "frequency": 0.75
            },
            {
                "pattern_id": "pattern_2",
                "name": "Risk-Averse Explorer",
                "description": "Frequently views risk management content but rarely engages in simulated trading",
                "impact": "Missed opportunities for practical application",
                "recommendation": "Offer low-stakes trade challenges with guided scenarios",
                "confidence": 0.78,
                "frequency": 0.60
            }
        ]
        
        with patch.object(service, '_identify_patterns', return_value=mock_patterns):
            result = await service.get_behavior_patterns("user_123")
            
            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["name"] == "Passive Learner"
            assert result[1]["confidence"] == 0.78
    
    @pytest.mark.asyncio
    async def test_get_behavioral_insights(self, service):
        """Test getting comprehensive behavioral insights"""
        mock_insights = {
            "user_id": "user_123",
            "engagement_trends": {
                "daily_active_time": "2.5 hours",
                "weekly_engagement": "increasing",
                "preferred_content_length": "15-30 minutes"
            },
            "learning_effectiveness": {
                "best_performing_content_types": ["interactive", "video"],
                "optimal_learning_times": ["morning", "evening"],
                "knowledge_retention_rate": 0.78
            },
            "risk_indicators": {
                "potential_dropout_risk": "low",
                "engagement_decline": False,
                "content_satisfaction": "high"
            }
        }
        
        with patch.object(service, '_generate_insights', return_value=mock_insights):
            result = await service.get_behavioral_insights("user_123")
            
            assert result is not None
            assert result["user_id"] == "user_123"
            assert "engagement_trends" in result
            assert "learning_effectiveness" in result
            assert "risk_indicators" in result


class TestDynamicContentService:
    """Test Dynamic Content Service"""
    
    @pytest.fixture
    def service(self):
        return DynamicContentService()
    
    @pytest.fixture
    def mock_content_request(self):
        return {
            "user_id": "user_123",
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
                "format_preference": "interactive",
                "length_preference": "medium"
            }
        }
    
    @pytest.mark.asyncio
    async def test_adapt_content(self, service, mock_content_request):
        """Test content adaptation"""
        with patch.object(service, '_analyze_user_preferences', return_value={"preferred_format": "interactive"}):
            with patch.object(service, '_generate_adapted_content', return_value="Adapted content"):
                result = await service.adapt_content(mock_content_request)
                
                assert result is not None
                assert "adapted_content_id" in result
                assert result["user_id"] == "user_123"
                assert result["content_type"] == "learning_module"
                assert "adaptation_reason" in result
    
    @pytest.mark.asyncio
    async def test_generate_personalized_content(self, service):
        """Test personalized content generation"""
        content_request = {
            "user_id": "user_123",
            "content_type": "quiz",
            "topic": "risk_management",
            "user_profile": {
                "risk_tolerance": "moderate",
                "learning_style": "visual",
                "experience_level": "intermediate"
            }
        }
        
        with patch.object(service, '_generate_ai_content', return_value="Personalized quiz content"):
            result = await service.generate_personalized_content(content_request)
            
            assert result is not None
            assert "content_id" in result
            assert result["user_id"] == "user_123"
            assert result["content_type"] == "quiz"
            assert "personalization_score" in result
    
    @pytest.mark.asyncio
    async def test_get_content_recommendations(self, service):
        """Test getting content recommendations"""
        mock_recommendations = [
            {
                "content_id": "rec_1",
                "title": "Advanced Options Strategies",
                "type": "learning_module",
                "match_score": 0.92,
                "engagement_prediction": 0.88,
                "reason": "Matches your interest in options trading"
            },
            {
                "content_id": "rec_2",
                "title": "Risk Management Quiz",
                "type": "quiz",
                "match_score": 0.85,
                "engagement_prediction": 0.80,
                "reason": "Based on your recent learning patterns"
            }
        ]
        
        with patch.object(service, '_generate_recommendations', return_value=mock_recommendations):
            result = await service.get_content_recommendations("user_123", limit=5)
            
            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["match_score"] == 0.92
            assert result[1]["type"] == "quiz"
    
    @pytest.mark.asyncio
    async def test_get_personalization_score(self, service):
        """Test getting personalization score"""
        mock_score = {
            "user_id": "user_123",
            "overall_score": 0.87,
            "content_adaptation_score": 0.90,
            "recommendation_accuracy": 0.85,
            "engagement_improvement": 0.88,
            "satisfaction_score": 0.85,
            "last_updated": datetime.now()
        }
        
        with patch.object(service, '_calculate_personalization_score', return_value=mock_score):
            result = await service.get_personalization_score("user_123")
            
            assert result is not None
            assert result["user_id"] == "user_123"
            assert result["overall_score"] == 0.87
            assert "content_adaptation_score" in result
            assert "recommendation_accuracy" in result
    
    @pytest.mark.asyncio
    async def test_update_content_preferences(self, service):
        """Test updating content preferences"""
        preferences = {
            "preferred_content_types": ["interactive", "video"],
            "preferred_difficulty": "intermediate",
            "preferred_length": "medium",
            "learning_goals": ["options_trading", "risk_management"]
        }
        
        with patch.object(service, '_save_preferences', return_value=True):
            result = await service.update_content_preferences("user_123", preferences)
            
            assert result is not None
            assert result["success"] is True
            assert result["user_id"] == "user_123"
            assert "updated_preferences" in result
    
    @pytest.mark.asyncio
    async def test_get_content_analytics(self, service):
        """Test getting content analytics"""
        mock_analytics = {
            "user_id": "user_123",
            "content_interaction_stats": {
                "total_content_viewed": 45,
                "average_engagement_time": 1200,
                "completion_rate": 0.78,
                "favorite_content_types": ["interactive", "video"]
            },
            "adaptation_effectiveness": {
                "adapted_content_engagement": 0.85,
                "original_content_engagement": 0.72,
                "improvement_percentage": 18.1
            },
            "recommendation_performance": {
                "click_through_rate": 0.65,
                "completion_rate": 0.80,
                "satisfaction_score": 4.2
            }
        }
        
        with patch.object(service, '_analyze_content_performance', return_value=mock_analytics):
            result = await service.get_content_analytics("user_123")
            
            assert result is not None
            assert result["user_id"] == "user_123"
            assert "content_interaction_stats" in result
            assert "adaptation_effectiveness" in result
            assert "recommendation_performance" in result


# Integration tests for Phase 3 services
class TestPhase3Integration:
    """Integration tests for Phase 3 services working together"""
    
    @pytest.mark.asyncio
    async def test_behavioral_analytics_with_dynamic_content(self):
        """Test behavioral analytics driving dynamic content adaptation"""
        analytics_service = BehavioralAnalyticsService()
        content_service = DynamicContentService()
        
        # Track behavior
        behavior_data = {
            "user_id": "user_123",
            "event_type": "content_interaction",
            "event_data": {
                "content_id": "module_1",
                "interaction_type": "skip",
                "time_spent": 30
            }
        }
        
        with patch.object(analytics_service, '_save_behavior_event', return_value="event_123"):
            behavior_result = await analytics_service.track_behavior(behavior_data)
            
            assert behavior_result is not None
            
            # Get engagement profile
            mock_profile = {
                "user_id": "user_123",
                "learning_style": "visual",
                "preferred_content_types": ["video", "interactive"],
                "engagement_score": 0.75
            }
            
            with patch.object(analytics_service, '_analyze_user_behavior', return_value=mock_profile):
                profile = await analytics_service.get_engagement_profile("user_123")
                
                assert profile is not None
                
                # Adapt content based on profile
                content_request = {
                    "user_id": "user_123",
                    "content_type": "learning_module",
                    "topic": "options_basics",
                    "user_context": {
                        "learning_style": profile["learning_style"],
                        "preferred_format": profile["preferred_content_types"][0]
                    }
                }
                
                with patch.object(content_service, '_analyze_user_preferences', return_value=profile):
                    with patch.object(content_service, '_generate_adapted_content', return_value="Adapted content"):
                        adapted_content = await content_service.adapt_content(content_request)
                        
                        assert adapted_content is not None
                        assert adapted_content["user_id"] == "user_123"
    
    @pytest.mark.asyncio
    async def test_personalization_score_calculation(self):
        """Test personalization score calculation with multiple data points"""
        analytics_service = BehavioralAnalyticsService()
        content_service = DynamicContentService()
        
        # Get behavior patterns
        mock_patterns = [
            {
                "name": "Visual Learner",
                "confidence": 0.90,
                "impact": "positive"
            }
        ]
        
        with patch.object(analytics_service, '_identify_patterns', return_value=mock_patterns):
            patterns = await analytics_service.get_behavior_patterns("user_123")
            
            assert patterns is not None
            
            # Get content recommendations
            mock_recommendations = [
                {
                    "content_id": "rec_1",
                    "match_score": 0.95,
                    "engagement_prediction": 0.90
                }
            ]
            
            with patch.object(content_service, '_generate_recommendations', return_value=mock_recommendations):
                recommendations = await content_service.get_content_recommendations("user_123")
                
                assert recommendations is not None
                
                # Calculate personalization score
                mock_score = {
                    "user_id": "user_123",
                    "overall_score": 0.92,
                    "content_adaptation_score": 0.95,
                    "recommendation_accuracy": 0.90,
                    "engagement_improvement": 0.88
                }
                
                with patch.object(content_service, '_calculate_personalization_score', return_value=mock_score):
                    score = await content_service.get_personalization_score("user_123")
                    
                    assert score is not None
                    assert score["overall_score"] == 0.92
                    assert score["content_adaptation_score"] == 0.95
    
    @pytest.mark.asyncio
    async def test_churn_prediction_with_retention_strategies(self):
        """Test churn prediction with dynamic retention strategies"""
        analytics_service = BehavioralAnalyticsService()
        content_service = DynamicContentService()
        
        # Get churn prediction
        mock_churn = {
            "user_id": "user_123",
            "risk_level": "medium",
            "confidence": 0.75,
            "risk_factors": ["decreasing_engagement", "content_skipping"],
            "retention_strategies": ["personalized_content", "engagement_boost"]
        }
        
        with patch.object(analytics_service, '_predict_churn', return_value=mock_churn):
            churn_result = await analytics_service.get_churn_prediction("user_123")
            
            assert churn_result is not None
            assert churn_result["risk_level"] == "medium"
            
            # Generate personalized content based on retention strategies
            if churn_result["risk_level"] in ["medium", "high"]:
                content_request = {
                    "user_id": "user_123",
                    "content_type": "engagement_boost",
                    "topic": "motivational_content",
                    "user_context": {
                        "risk_factors": churn_result["risk_factors"],
                        "retention_strategies": churn_result["retention_strategies"]
                    }
                }
                
                with patch.object(content_service, '_generate_ai_content', return_value="Retention-focused content"):
                    retention_content = await content_service.generate_personalized_content(content_request)
                    
                    assert retention_content is not None
                    assert retention_content["user_id"] == "user_123"
                    assert retention_content["content_type"] == "engagement_boost"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
