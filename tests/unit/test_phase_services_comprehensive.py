"""
Comprehensive unit tests for all Phase 1, 2, and 3 services in RichesReach AI platform.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta
import json

# Import Phase 1 services
from backend.backend.core.daily_voice_digest_service import DailyVoiceDigestService
from backend.backend.core.momentum_missions_service import MomentumMissionsService
from backend.backend.core.notification_service import NotificationService
from backend.backend.core.regime_monitor_service import RegimeMonitorService

# Import Phase 2 services
from backend.backend.core.wealth_circles_service import WealthCirclesService
from backend.backend.core.peer_progress_service import PeerProgressService
from backend.backend.core.trade_simulator_service import TradeSimulatorService

# Import Phase 3 services
from backend.backend.core.behavioral_analytics_service import BehavioralAnalyticsService
from backend.backend.core.dynamic_content_service import DynamicContentService

class TestPhase1Services:
    """Comprehensive tests for Phase 1 - Enhanced Retention services."""
    
    class TestDailyVoiceDigestService:
        """Tests for Daily Voice Digest Service."""
        
        @pytest.fixture
        def digest_service(self, mock_ai_router, mock_ml_service):
            """Create Daily Voice Digest Service instance for testing."""
            with patch('backend.backend.core.daily_voice_digest_service.get_advanced_ai_router', return_value=mock_ai_router):
                with patch('backend.backend.core.daily_voice_digest_service.MLService', return_value=mock_ml_service):
                    return DailyVoiceDigestService()
        
        @pytest.mark.asyncio
        async def test_generate_daily_digest_success(self, digest_service, mock_user_profile):
            """Test successful daily digest generation."""
            user_id = "test_user_123"
            preferences = {
                "duration": "short",
                "focus_areas": ["market_overview", "portfolio_insights"],
                "tone": "professional"
            }
            
            result = await digest_service.generate_daily_digest(user_id, mock_user_profile, preferences)
            
            assert result is not None
            assert "digest_id" in result
            assert "voice_script" in result
            assert "key_insights" in result
            assert "actionable_tips" in result
            assert "duration_estimate" in result
            assert result["user_id"] == user_id
        
        @pytest.mark.asyncio
        async def test_generate_daily_digest_with_regime_context(self, digest_service, mock_user_profile):
            """Test daily digest generation with regime context."""
            user_id = "test_user_123"
            preferences = {"duration": "medium", "include_regime_analysis": True}
            
            result = await digest_service.generate_daily_digest(user_id, mock_user_profile, preferences)
            
            assert result is not None
            assert "regime_context" in result
            assert "current_regime" in result["regime_context"]
            assert "regime_confidence" in result["regime_context"]
        
        @pytest.mark.asyncio
        async def test_create_regime_alert(self, digest_service, mock_user_profile):
            """Test regime alert creation."""
            user_id = "test_user_123"
            old_regime = "bull_market"
            new_regime = "correction"
            confidence = 0.85
            
            result = await digest_service.create_regime_alert(user_id, old_regime, new_regime, confidence, mock_user_profile)
            
            assert result is not None
            assert "notification_id" in result
            assert "alert_type" in result
            assert "data" in result
            assert result["data"]["old_regime"] == old_regime
            assert result["data"]["new_regime"] == new_regime
    
    class TestMomentumMissionsService:
        """Tests for Momentum Missions Service."""
        
        @pytest.fixture
        def missions_service(self, mock_ai_router):
            """Create Momentum Missions Service instance for testing."""
            with patch('backend.backend.core.momentum_missions_service.get_advanced_ai_router', return_value=mock_ai_router):
                return MomentumMissionsService()
        
        @pytest.mark.asyncio
        async def test_get_user_progress_success(self, missions_service, mock_user_profile):
            """Test successful user progress retrieval."""
            user_id = "test_user_123"
            
            result = await missions_service.get_user_progress(user_id, mock_user_profile)
            
            assert result is not None
            assert "user_id" in result
            assert "current_streak" in result
            assert "total_missions_completed" in result
            assert "achievements" in result
            assert "next_milestone" in result
        
        @pytest.mark.asyncio
        async def test_generate_daily_mission_success(self, missions_service, mock_user_profile):
            """Test successful daily mission generation."""
            user_id = "test_user_123"
            day_number = 1
            
            result = await missions_service.generate_daily_mission(user_id, mock_user_profile, day_number)
            
            assert result is not None
            assert "mission_id" in result
            assert "title" in result
            assert "description" in result
            assert "difficulty" in result
            assert "estimated_time" in result
            assert "rewards" in result
            assert result["day_number"] == day_number
        
        @pytest.mark.asyncio
        async def test_generate_recovery_ritual(self, missions_service, mock_user_profile):
            """Test recovery ritual generation."""
            user_id = "test_user_123"
            missed_days = 3
            
            result = await missions_service.generate_recovery_ritual(user_id, mock_user_profile, missed_days)
            
            assert result is not None
            assert "ritual_id" in result
            assert "content" in result
            assert "steps" in result
            assert "motivation_message" in result
            assert "estimated_duration" in result
    
    class TestNotificationService:
        """Tests for Notification Service."""
        
        @pytest.fixture
        def notification_service(self):
            """Create Notification Service instance for testing."""
            return NotificationService()
        
        @pytest.mark.asyncio
        async def test_get_notification_preferences_success(self, notification_service):
            """Test successful notification preferences retrieval."""
            user_id = "test_user_123"
            
            result = await notification_service.get_notification_preferences(user_id)
            
            assert result is not None
            assert "user_id" in result
            assert "preferences" in result
            assert "daily_digest_enabled" in result["preferences"]
            assert "regime_alerts_enabled" in result["preferences"]
        
        @pytest.mark.asyncio
        async def test_update_notification_preferences(self, notification_service):
            """Test notification preferences update."""
            user_id = "test_user_123"
            preferences = {
                "daily_digest_enabled": True,
                "regime_alerts_enabled": False,
                "push_notifications": True
            }
            
            result = await notification_service.update_notification_preferences(user_id, preferences)
            
            assert result is not None
            assert "success" in result
            assert result["success"] is True
        
        @pytest.mark.asyncio
        async def test_get_recent_notifications(self, notification_service):
            """Test recent notifications retrieval."""
            user_id = "test_user_123"
            limit = 10
            
            result = await notification_service.get_recent_notifications(user_id, limit)
            
            assert result is not None
            assert "notifications" in result
            assert isinstance(result["notifications"], list)
            assert len(result["notifications"]) <= limit
    
    class TestRegimeMonitorService:
        """Tests for Regime Monitor Service."""
        
        @pytest.fixture
        def monitor_service(self, mock_ml_service):
            """Create Regime Monitor Service instance for testing."""
            with patch('backend.backend.core.regime_monitor_service.MLService', return_value=mock_ml_service):
                return RegimeMonitorService()
        
        @pytest.mark.asyncio
        async def test_check_regime_change_success(self, monitor_service):
            """Test successful regime change check."""
            market_data = {
                "spy": {"price": 450, "volume": 50000000, "volatility": 0.15},
                "vix": {"price": 18, "change": -0.05}
            }
            
            result = await monitor_service.check_regime_change(market_data)
            
            assert result is not None
            assert "new_regime" in result
            assert "regime_change_detected" in result
            assert "confidence" in result
            assert "change_reasoning" in result
        
        @pytest.mark.asyncio
        async def test_get_monitoring_status(self, monitor_service):
            """Test monitoring status retrieval."""
            result = await monitor_service.get_monitoring_status()
            
            assert result is not None
            assert "status" in result
            assert "active_monitors" in result
            assert "total_events_detected" in result
            assert "last_check" in result

class TestPhase2Services:
    """Comprehensive tests for Phase 2 - Community services."""
    
    class TestWealthCirclesService:
        """Tests for Wealth Circles Service."""
        
        @pytest.fixture
        def circles_service(self, mock_ai_router):
            """Create Wealth Circles Service instance for testing."""
            with patch('backend.backend.core.wealth_circles_service.get_advanced_ai_router', return_value=mock_ai_router):
                return WealthCirclesService()
        
        @pytest.mark.asyncio
        async def test_create_wealth_circle_success(self, circles_service, mock_user_profile):
            """Test successful wealth circle creation."""
            user_id = "test_user_123"
            circle_data = {
                "name": "Options Trading Circle",
                "description": "Learn advanced options strategies",
                "focus_area": "options_trading",
                "is_private": False,
                "tags": ["options", "trading", "education"]
            }
            
            result = await circles_service.create_wealth_circle(user_id, circle_data, mock_user_profile)
            
            assert result is not None
            assert "circle_id" in result
            assert "name" in result
            assert "moderators" in result
            assert user_id in result["moderators"]
            assert result["name"] == circle_data["name"]
        
        @pytest.mark.asyncio
        async def test_get_wealth_circles(self, circles_service):
            """Test wealth circles retrieval."""
            user_id = "test_user_123"
            limit = 10
            
            result = await circles_service.get_wealth_circles(user_id, limit)
            
            assert result is not None
            assert "circles" in result
            assert isinstance(result["circles"], list)
            assert len(result["circles"]) <= limit
        
        @pytest.mark.asyncio
        async def test_create_discussion_post(self, circles_service, mock_user_profile):
            """Test discussion post creation."""
            user_id = "test_user_123"
            post_data = {
                "circle_id": "circle_123",
                "title": "Best Options Strategies for Beginners",
                "content": "What are the safest options strategies to start with?",
                "post_type": "discussion",
                "tags": ["beginner", "options", "strategy"]
            }
            
            result = await circles_service.create_discussion_post(user_id, post_data, mock_user_profile)
            
            assert result is not None
            assert "post_id" in result
            assert "title" in result
            assert "user_id" in result
            assert result["user_id"] == user_id
            assert result["title"] == post_data["title"]
    
    class TestPeerProgressService:
        """Tests for Peer Progress Service."""
        
        @pytest.fixture
        def progress_service(self):
            """Create Peer Progress Service instance for testing."""
            return PeerProgressService()
        
        @pytest.mark.asyncio
        async def test_share_progress_success(self, progress_service, mock_user_profile):
            """Test successful progress sharing."""
            user_id = "test_user_123"
            progress_data = {
                "progress_type": "learning",
                "title": "Completed Options Trading Module",
                "unit": "module",
                "value": 1,
                "description": "Successfully completed the basics of options trading"
            }
            
            result = await progress_service.share_progress(user_id, progress_data, mock_user_profile)
            
            assert result is not None
            assert "progress_id" in result
            assert "user_id" in result
            assert "progress_type" in result
            assert result["user_id"] == user_id
            assert result["progress_type"] == progress_data["progress_type"]
        
        @pytest.mark.asyncio
        async def test_get_community_stats(self, progress_service):
            """Test community stats retrieval."""
            community_id = "community_123"
            
            result = await progress_service.get_community_stats(community_id)
            
            assert result is not None
            assert "community_id" in result
            assert "total_members" in result
            assert "active_this_week" in result
            assert "achievements_shared" in result
    
    class TestTradeSimulatorService:
        """Tests for Trade Simulator Service."""
        
        @pytest.fixture
        def simulator_service(self, mock_ai_router):
            """Create Trade Simulator Service instance for testing."""
            with patch('backend.backend.core.trade_simulator_service.get_advanced_ai_router', return_value=mock_ai_router):
                return TradeSimulatorService()
        
        @pytest.mark.asyncio
        async def test_create_challenge_success(self, simulator_service, mock_user_profile):
            """Test successful challenge creation."""
            user_id = "test_user_123"
            challenge_data = {
                "challenge_type": "prediction",
                "title": "AAPL Price Prediction Challenge",
                "description": "Predict AAPL's price movement for next week",
                "start_date": "2024-01-15T00:00:00Z",
                "end_date": "2024-01-22T23:59:59Z",
                "asset": "AAPL",
                "entry_fee": 10.0
            }
            
            result = await simulator_service.create_challenge(user_id, challenge_data, mock_user_profile)
            
            assert result is not None
            assert "challenge_id" in result
            assert "challenge_type" in result
            assert "creator_id" in result
            assert result["creator_id"] == user_id
            assert result["challenge_type"] == challenge_data["challenge_type"]
        
        @pytest.mark.asyncio
        async def test_get_active_challenges(self, simulator_service):
            """Test active challenges retrieval."""
            limit = 10
            
            result = await simulator_service.get_active_challenges(limit)
            
            assert result is not None
            assert "challenges" in result
            assert isinstance(result["challenges"], list)
            assert len(result["challenges"]) <= limit
        
        @pytest.mark.asyncio
        async def test_make_prediction(self, simulator_service, mock_user_profile):
            """Test prediction making."""
            user_id = "test_user_123"
            challenge_id = "challenge_123"
            prediction_data = {
                "prediction_type": "price_direction",
                "asset": "AAPL",
                "predicted_value": 150.0,
                "confidence": 0.75,
                "reasoning": "Based on technical analysis and market sentiment"
            }
            
            result = await simulator_service.make_prediction(user_id, challenge_id, prediction_data, mock_user_profile)
            
            assert result is not None
            assert "prediction_id" in result
            assert "user_id" in result
            assert "challenge_id" in result
            assert result["user_id"] == user_id
            assert result["challenge_id"] == challenge_id
        
        @pytest.mark.asyncio
        async def test_get_challenge_leaderboard(self, simulator_service):
            """Test challenge leaderboard retrieval."""
            challenge_id = "challenge_123"
            limit = 10
            
            result = await simulator_service.get_challenge_leaderboard(challenge_id, limit)
            
            assert result is not None
            assert "leaderboard" in result
            assert isinstance(result["leaderboard"], list)
            assert len(result["leaderboard"]) <= limit

class TestPhase3Services:
    """Comprehensive tests for Phase 3 - Advanced Personalization services."""
    
    class TestBehavioralAnalyticsService:
        """Tests for Behavioral Analytics Service."""
        
        @pytest.fixture
        def analytics_service(self, mock_ai_router):
            """Create Behavioral Analytics Service instance for testing."""
            with patch('backend.backend.core.behavioral_analytics_service.get_advanced_ai_router', return_value=mock_ai_router):
                return BehavioralAnalyticsService()
        
        @pytest.mark.asyncio
        async def test_track_behavior_success(self, analytics_service, mock_user_profile):
            """Test successful behavior tracking."""
            user_id = "test_user_123"
            behavior_data = {
                "behavior_type": "learning",
                "action": "module_completed",
                "context": {
                    "module_id": "module_123",
                    "topic": "options_trading",
                    "duration": 1800,
                    "score": 85
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            result = await analytics_service.track_behavior(user_id, behavior_data, mock_user_profile)
            
            assert result is not None
            assert "event_id" in result
            assert "user_id" in result
            assert "behavior_type" in result
            assert result["user_id"] == user_id
            assert result["behavior_type"] == behavior_data["behavior_type"]
        
        @pytest.mark.asyncio
        async def test_get_engagement_profile(self, analytics_service):
            """Test engagement profile retrieval."""
            user_id = "test_user_123"
            
            result = await analytics_service.get_engagement_profile(user_id)
            
            assert result is not None
            assert "user_id" in result
            assert "engagement_score" in result
            assert "preferred_content_types" in result
            assert "learning_velocity" in result
            assert "retention_rate" in result
        
        @pytest.mark.asyncio
        async def test_get_churn_prediction(self, analytics_service):
            """Test churn prediction retrieval."""
            user_id = "test_user_123"
            
            result = await analytics_service.get_churn_prediction(user_id)
            
            assert result is not None
            assert "user_id" in result
            assert "churn_risk" in result
            assert "risk_factors" in result
            assert "intervention_recommendations" in result
            assert 0 <= result["churn_risk"] <= 1
        
        @pytest.mark.asyncio
        async def test_get_behavior_patterns(self, analytics_service):
            """Test behavior patterns retrieval."""
            user_id = "test_user_123"
            
            result = await analytics_service.get_behavior_patterns(user_id)
            
            assert result is not None
            assert "patterns" in result
            assert isinstance(result["patterns"], list)
            assert all("pattern_type" in pattern for pattern in result["patterns"])
    
    class TestDynamicContentService:
        """Tests for Dynamic Content Service (Phase 3 version)."""
        
        @pytest.fixture
        def content_service(self, mock_ai_router):
            """Create Dynamic Content Service instance for testing."""
            with patch('backend.backend.core.dynamic_content_service.get_advanced_ai_router', return_value=mock_ai_router):
                return DynamicContentService()
        
        @pytest.mark.asyncio
        async def test_adapt_content_success(self, content_service, mock_user_profile):
            """Test successful content adaptation."""
            user_id = "test_user_123"
            original_content = {
                "title": "Options Trading Basics",
                "difficulty": "beginner",
                "duration": 45,
                "format": "text"
            }
            user_behavior = {
                "learning_speed": "fast",
                "preferred_format": "interactive",
                "attention_span": "short"
            }
            
            result = await content_service.adapt_content(user_id, original_content, user_behavior, mock_user_profile)
            
            assert result is not None
            assert "adapted_content" in result
            assert "adaptation_reasoning" in result
            assert "adaptation_score" in result
            assert "personalization_metrics" in result
        
        @pytest.mark.asyncio
        async def test_generate_personalized_content(self, content_service, mock_user_profile):
            """Test personalized content generation."""
            user_id = "test_user_123"
            content_request = {
                "content_type": "learning_module",
                "topic": "Risk Management",
                "difficulty": "intermediate",
                "preferences": {
                    "format": "interactive",
                    "duration": 30,
                    "include_examples": True
                }
            }
            
            result = await content_service.generate_personalized_content(user_id, content_request, mock_user_profile)
            
            assert result is not None
            assert "content_id" in result
            assert "personalized_content" in result
            assert "personalization_score" in result
            assert "content_preferences" in result
        
        @pytest.mark.asyncio
        async def test_get_content_recommendations(self, content_service):
            """Test content recommendations retrieval."""
            user_id = "test_user_123"
            limit = 5
            
            result = await content_service.get_content_recommendations(user_id, limit)
            
            assert result is not None
            assert "recommendations" in result
            assert isinstance(result["recommendations"], list)
            assert len(result["recommendations"]) <= limit
            assert all("recommendation_id" in rec for rec in result["recommendations"])
        
        @pytest.mark.asyncio
        async def test_get_personalization_score(self, content_service):
            """Test personalization score retrieval."""
            user_id = "test_user_123"
            content_type = "learning_module"
            
            result = await content_service.get_personalization_score(user_id, content_type)
            
            assert result is not None
            assert "user_id" in result
            assert "personalization_score" in result
            assert "content_preferences" in result
            assert "adaptation_history" in result
            assert 0 <= result["personalization_score"] <= 1

# Integration tests across phases
class TestCrossPhaseIntegration:
    """Integration tests across all phases."""
    
    @pytest.mark.asyncio
    async def test_phase1_to_phase2_integration(self, mock_ai_router, mock_user_profile):
        """Test integration from Phase 1 to Phase 2."""
        with patch('backend.backend.core.daily_voice_digest_service.get_advanced_ai_router', return_value=mock_ai_router):
            with patch('backend.backend.core.wealth_circles_service.get_advanced_ai_router', return_value=mock_ai_router):
                digest_service = DailyVoiceDigestService()
                circles_service = WealthCirclesService()
                
                # Generate daily digest
                digest = await digest_service.generate_daily_digest("test_user", mock_user_profile)
                assert digest is not None
                
                # Share progress in community
                progress_data = {
                    "progress_type": "learning",
                    "title": "Completed Daily Digest",
                    "unit": "digest",
                    "value": 1
                }
                progress_service = PeerProgressService()
                progress = await progress_service.share_progress("test_user", progress_data, mock_user_profile)
                assert progress is not None
    
    @pytest.mark.asyncio
    async def test_phase2_to_phase3_integration(self, mock_ai_router, mock_user_profile):
        """Test integration from Phase 2 to Phase 3."""
        with patch('backend.backend.core.wealth_circles_service.get_advanced_ai_router', return_value=mock_ai_router):
            with patch('backend.backend.core.behavioral_analytics_service.get_advanced_ai_router', return_value=mock_ai_router):
                circles_service = WealthCirclesService()
                analytics_service = BehavioralAnalyticsService()
                
                # Create wealth circle
                circle_data = {
                    "name": "Test Circle",
                    "description": "Test description",
                    "focus_area": "investment",
                    "is_private": False
                }
                circle = await circles_service.create_wealth_circle("test_user", circle_data, mock_user_profile)
                assert circle is not None
                
                # Track behavior from community engagement
                behavior_data = {
                    "behavior_type": "social",
                    "action": "circle_joined",
                    "context": {"circle_id": circle["circle_id"]}
                }
                behavior = await analytics_service.track_behavior("test_user", behavior_data, mock_user_profile)
                assert behavior is not None
    
    @pytest.mark.asyncio
    async def test_complete_user_journey(self, mock_ai_router, mock_user_profile):
        """Test complete user journey across all phases."""
        with patch('backend.backend.core.daily_voice_digest_service.get_advanced_ai_router', return_value=mock_ai_router):
            with patch('backend.backend.core.wealth_circles_service.get_advanced_ai_router', return_value=mock_ai_router):
                with patch('backend.backend.core.behavioral_analytics_service.get_advanced_ai_router', return_value=mock_ai_router):
                    # Phase 1: Daily digest
                    digest_service = DailyVoiceDigestService()
                    digest = await digest_service.generate_daily_digest("test_user", mock_user_profile)
                    assert digest is not None
                    
                    # Phase 2: Community engagement
                    circles_service = WealthCirclesService()
                    circle_data = {
                        "name": "Journey Circle",
                        "description": "Complete journey test",
                        "focus_area": "investment",
                        "is_private": False
                    }
                    circle = await circles_service.create_wealth_circle("test_user", circle_data, mock_user_profile)
                    assert circle is not None
                    
                    # Phase 3: Personalization
                    analytics_service = BehavioralAnalyticsService()
                    behavior_data = {
                        "behavior_type": "learning",
                        "action": "journey_completed",
                        "context": {"phases_completed": ["phase1", "phase2", "phase3"]}
                    }
                    behavior = await analytics_service.track_behavior("test_user", behavior_data, mock_user_profile)
                    assert behavior is not None

# Performance tests for all phases
class TestPhaseServicesPerformance:
    """Performance tests for all phase services."""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_phase1_requests(self, mock_ai_router, mock_user_profile):
        """Test concurrent Phase 1 service requests."""
        with patch('backend.backend.core.daily_voice_digest_service.get_advanced_ai_router', return_value=mock_ai_router):
            digest_service = DailyVoiceDigestService()
            
            tasks = []
            for i in range(5):
                task = digest_service.generate_daily_digest(f"user_{i}", mock_user_profile)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            assert len(results) == 5
            assert all(result is not None for result in results)
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_phase2_requests(self, mock_ai_router, mock_user_profile):
        """Test concurrent Phase 2 service requests."""
        with patch('backend.backend.core.wealth_circles_service.get_advanced_ai_router', return_value=mock_ai_router):
            circles_service = WealthCirclesService()
            
            tasks = []
            for i in range(5):
                circle_data = {
                    "name": f"Circle {i}",
                    "description": f"Test circle {i}",
                    "focus_area": "investment",
                    "is_private": False
                }
                task = circles_service.create_wealth_circle(f"user_{i}", circle_data, mock_user_profile)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            assert len(results) == 5
            assert all(result is not None for result in results)
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_phase3_requests(self, mock_ai_router, mock_user_profile):
        """Test concurrent Phase 3 service requests."""
        with patch('backend.backend.core.behavioral_analytics_service.get_advanced_ai_router', return_value=mock_ai_router):
            analytics_service = BehavioralAnalyticsService()
            
            tasks = []
            for i in range(5):
                behavior_data = {
                    "behavior_type": "learning",
                    "action": f"test_action_{i}",
                    "context": {"test": True}
                }
                task = analytics_service.track_behavior(f"user_{i}", behavior_data, mock_user_profile)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            assert len(results) == 5
            assert all(result is not None for result in results)
