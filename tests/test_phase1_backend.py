"""
Unit tests for Phase 1 backend services:
- Daily Voice Digest
- Momentum Missions  
- Push Notifications
- Real-time Regime Monitoring
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Import the services
try:
    from backend.backend.core.daily_voice_digest_service import DailyVoiceDigestService
    from backend.backend.core.momentum_missions_service import MomentumMissionsService
    from backend.backend.core.notification_service import NotificationService
    from backend.backend.core.regime_monitor_service import RegimeMonitorService
except ModuleNotFoundError:
    pytest.skip("Legacy backend.backend.core module path not available", allow_module_level=True)


class TestDailyVoiceDigestService:
    """Test Daily Voice Digest Service"""
    
    @pytest.fixture
    def service(self):
        return DailyVoiceDigestService()
    
    @pytest.fixture
    def mock_user_profile(self):
        return {
            "user_id": "test_user_123",
            "risk_tolerance": "moderate",
            "investment_goals": ["retirement", "wealth_building"],
            "preferred_content_types": ["market_analysis", "educational"],
            "timezone": "America/New_York"
        }
    
    @pytest.fixture
    def mock_market_data(self):
        return {
            "spy": {"price": 450.25, "change": 2.15, "change_percent": 0.48},
            "qqq": {"price": 380.50, "change": -1.25, "change_percent": -0.33},
            "vix": {"price": 18.75, "change": -0.85, "change_percent": -4.34}
        }
    
    @pytest.mark.asyncio
    async def test_generate_daily_digest_success(self, service, mock_user_profile, mock_market_data):
        """Test successful daily digest generation"""
        with patch.object(service, '_get_market_data', return_value=mock_market_data):
            with patch.object(service, '_generate_ai_content', return_value="Mock AI content"):
                result = await service.generate_daily_digest(
                    user_id="test_user_123",
                    user_profile=mock_user_profile,
                    market_data=mock_market_data
                )
                
                assert result is not None
                assert "digest_id" in result
                assert "content" in result
                assert "audio_url" in result
                assert "duration_seconds" in result
                assert result["user_id"] == "test_user_123"
    
    @pytest.mark.asyncio
    async def test_generate_daily_digest_with_regime_context(self, service, mock_user_profile):
        """Test daily digest generation with regime context"""
        regime_context = {
            "current_regime": "bull_market",
            "confidence": 0.85,
            "key_indicators": ["low_volatility", "upward_trend"]
        }
        
        with patch.object(service, '_get_market_data', return_value={}):
            with patch.object(service, '_generate_ai_content', return_value="Regime-aware content"):
                result = await service.generate_daily_digest(
                    user_id="test_user_123",
                    user_profile=mock_user_profile,
                    regime_context=regime_context
                )
                
                assert result is not None
                assert "regime_context" in result
                assert result["regime_context"]["current_regime"] == "bull_market"
    
    @pytest.mark.asyncio
    async def test_create_regime_alert(self, service):
        """Test regime change alert creation"""
        regime_change = {
            "from_regime": "sideways",
            "to_regime": "bull_market",
            "confidence": 0.92,
            "trigger_indicators": ["breakout_volume", "momentum_shift"]
        }
        
        result = await service.create_regime_alert(
            user_id="test_user_123",
            regime_change=regime_change
        )
        
        assert result is not None
        assert "alert_id" in result
        assert "regime_change" in result
        assert result["regime_change"]["from_regime"] == "sideways"
        assert result["regime_change"]["to_regime"] == "bull_market"


class TestMomentumMissionsService:
    """Test Momentum Missions Service"""
    
    @pytest.fixture
    def service(self):
        return MomentumMissionsService()
    
    @pytest.fixture
    def mock_user_progress(self):
        return {
            "user_id": "test_user_123",
            "current_streak": 5,
            "longest_streak": 12,
            "total_missions_completed": 25,
            "last_activity": datetime.now() - timedelta(hours=2),
            "preferred_mission_types": ["learning", "trading_simulation"]
        }
    
    @pytest.mark.asyncio
    async def test_get_user_progress(self, service, mock_user_progress):
        """Test getting user progress"""
        with patch.object(service, '_fetch_user_data', return_value=mock_user_progress):
            result = await service.get_user_progress("test_user_123")
            
            assert result is not None
            assert result["user_id"] == "test_user_123"
            assert "current_streak" in result
            assert "longest_streak" in result
            assert "total_missions_completed" in result
    
    @pytest.mark.asyncio
    async def test_generate_daily_mission(self, service, mock_user_progress):
        """Test daily mission generation"""
        with patch.object(service, '_fetch_user_data', return_value=mock_user_progress):
            with patch.object(service, '_generate_mission_content', return_value="Mock mission content"):
                result = await service.generate_daily_mission("test_user_123")
                
                assert result is not None
                assert "mission_id" in result
                assert "title" in result
                assert "description" in result
                assert "difficulty" in result
                assert "estimated_duration" in result
                assert result["user_id"] == "test_user_123"
    
    @pytest.mark.asyncio
    async def test_generate_recovery_ritual(self, service):
        """Test recovery ritual generation for broken streaks"""
        result = await service.generate_recovery_ritual("test_user_123")
        
        assert result is not None
        assert "ritual_id" in result
        assert "title" in result
        assert "steps" in result
        assert "motivation_message" in result
        assert result["user_id"] == "test_user_123"


class TestNotificationService:
    """Test Push Notification Service"""
    
    @pytest.fixture
    def service(self):
        return NotificationService()
    
    @pytest.fixture
    def mock_notification_preferences(self):
        return {
            "user_id": "test_user_123",
            "push_enabled": True,
            "email_enabled": False,
            "digest_reminders": True,
            "regime_alerts": True,
            "mission_reminders": True,
            "quiet_hours": {"start": "22:00", "end": "08:00"},
            "timezone": "America/New_York"
        }
    
    @pytest.mark.asyncio
    async def test_get_notification_preferences(self, service, mock_notification_preferences):
        """Test getting notification preferences"""
        with patch.object(service, '_fetch_user_preferences', return_value=mock_notification_preferences):
            result = await service.get_notification_preferences("test_user_123")
            
            assert result is not None
            assert result["user_id"] == "test_user_123"
            assert result["push_enabled"] is True
            assert result["regime_alerts"] is True
    
    @pytest.mark.asyncio
    async def test_update_notification_preferences(self, service):
        """Test updating notification preferences"""
        new_preferences = {
            "push_enabled": False,
            "regime_alerts": False,
            "digest_reminders": True
        }
        
        with patch.object(service, '_save_user_preferences', return_value=True):
            result = await service.update_notification_preferences("test_user_123", new_preferences)
            
            assert result is not None
            assert result["user_id"] == "test_user_123"
            assert result["push_enabled"] is False
            assert result["regime_alerts"] is False
    
    @pytest.mark.asyncio
    async def test_send_notification(self, service):
        """Test sending a notification"""
        notification_payload = {
            "title": "Market Regime Change Alert",
            "body": "Market has shifted to bull market regime",
            "type": "regime_alert",
            "priority": "high"
        }
        
        with patch.object(service, '_send_push_notification', return_value=True):
            result = await service.send_notification("test_user_123", notification_payload)
            
            assert result is not None
            assert result["notification_id"] is not None
            assert result["status"] == "sent"
    
    @pytest.mark.asyncio
    async def test_get_recent_notifications(self, service):
        """Test getting recent notifications"""
        with patch.object(service, '_fetch_recent_notifications', return_value=[]):
            result = await service.get_recent_notifications("test_user_123", limit=10)
            
            assert isinstance(result, list)


class TestRegimeMonitorService:
    """Test Real-time Regime Monitoring Service"""
    
    @pytest.fixture
    def service(self):
        return RegimeMonitorService()
    
    @pytest.fixture
    def mock_market_data(self):
        return {
            "spy": {"price": 450.25, "volume": 45000000, "volatility": 0.15},
            "vix": {"price": 18.75},
            "treasury_10y": {"yield": 4.25},
            "dollar_index": {"value": 103.5}
        }
    
    @pytest.mark.asyncio
    async def test_check_regime_change(self, service, mock_market_data):
        """Test regime change detection"""
        with patch.object(service, '_get_current_market_data', return_value=mock_market_data):
            with patch.object(service, '_predict_regime', return_value={"regime": "bull_market", "confidence": 0.85}):
                result = await service.check_regime_change()
                
                assert result is not None
                assert "current_regime" in result
                assert "confidence" in result
                assert "change_detected" in result
    
    @pytest.mark.asyncio
    async def test_get_monitoring_status(self, service):
        """Test getting monitoring status"""
        result = await service.get_monitoring_status()
        
        assert result is not None
        assert "is_monitoring" in result
        assert "last_check" in result
        assert "total_alerts_sent" in result
        assert "active_regime" in result
    
    @pytest.mark.asyncio
    async def test_start_monitoring(self, service):
        """Test starting regime monitoring"""
        with patch.object(service, '_start_background_task', return_value=True):
            result = await service.start_monitoring()
            
            assert result is not None
            assert result["status"] == "started"
            assert "monitoring_id" in result
    
    @pytest.mark.asyncio
    async def test_stop_monitoring(self, service):
        """Test stopping regime monitoring"""
        with patch.object(service, '_stop_background_task', return_value=True):
            result = await service.stop_monitoring()
            
            assert result is not None
            assert result["status"] == "stopped"


# Integration tests for Phase 1 services
class TestPhase1Integration:
    """Integration tests for Phase 1 services working together"""
    
    @pytest.mark.asyncio
    async def test_daily_digest_with_notifications(self):
        """Test daily digest generation with notification sending"""
        digest_service = DailyVoiceDigestService()
        notification_service = NotificationService()
        
        user_profile = {
            "user_id": "test_user_123",
            "risk_tolerance": "moderate",
            "preferred_content_types": ["market_analysis"]
        }
        
        with patch.object(digest_service, '_get_market_data', return_value={}):
            with patch.object(digest_service, '_generate_ai_content', return_value="Mock content"):
                digest = await digest_service.generate_daily_digest("test_user_123", user_profile)
                
                assert digest is not None
                
                # Test notification for digest completion
                with patch.object(notification_service, '_send_push_notification', return_value=True):
                    notification = await notification_service.send_notification(
                        "test_user_123",
                        {
                            "title": "Daily Digest Ready",
                            "body": "Your personalized market digest is ready",
                            "type": "digest_ready"
                        }
                    )
                    
                    assert notification is not None
                    assert notification["status"] == "sent"
    
    @pytest.mark.asyncio
    async def test_regime_change_alert_flow(self):
        """Test complete regime change alert flow"""
        regime_service = RegimeMonitorService()
        notification_service = NotificationService()
        
        # Simulate regime change detection
        with patch.object(regime_service, '_get_current_market_data', return_value={}):
            with patch.object(regime_service, '_predict_regime', return_value={"regime": "bear_market", "confidence": 0.90}):
                regime_result = await regime_service.check_regime_change()
                
                if regime_result.get("change_detected"):
                    # Send alert notification
                    with patch.object(notification_service, '_send_push_notification', return_value=True):
                        alert = await notification_service.send_notification(
                            "test_user_123",
                            {
                                "title": "Market Regime Change",
                                "body": f"Market regime changed to {regime_result['current_regime']}",
                                "type": "regime_alert",
                                "priority": "high"
                            }
                        )
                        
                        assert alert is not None
                        assert alert["status"] == "sent"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
