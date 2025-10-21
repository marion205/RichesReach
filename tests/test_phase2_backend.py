"""
Unit tests for Phase 2 backend services:
- Wealth Circles (BIPOC Community)
- Peer Progress Pulse
- Trade Simulator Challenges
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Import the services
from backend.backend.core.wealth_circles_service import WealthCirclesService
from backend.backend.core.peer_progress_service import PeerProgressService
from backend.backend.core.trade_simulator_service import TradeSimulatorService


class TestWealthCirclesService:
    """Test Wealth Circles Service"""
    
    @pytest.fixture
    def service(self):
        return WealthCirclesService()
    
    @pytest.fixture
    def mock_wealth_circle(self):
        return {
            "circle_id": "circle_123",
            "name": "Q4 Wealth Building Goals",
            "description": "Building wealth for the future",
            "creator_id": "user_123",
            "member_count": 15,
            "created_at": datetime.now(),
            "is_private": False,
            "tags": ["wealth_building", "goals", "community"]
        }
    
    @pytest.mark.asyncio
    async def test_create_wealth_circle(self, service):
        """Test creating a wealth circle"""
        circle_data = {
            "name": "Test Circle",
            "description": "Test description",
            "creator_id": "user_123",
            "is_private": False,
            "tags": ["test", "community"]
        }
        
        with patch.object(service, '_save_circle', return_value="circle_456"):
            result = await service.create_wealth_circle(circle_data)
            
            assert result is not None
            assert "circle_id" in result
            assert result["name"] == "Test Circle"
            assert result["creator_id"] == "user_123"
    
    @pytest.mark.asyncio
    async def test_get_wealth_circles(self, service, mock_wealth_circle):
        """Test getting wealth circles"""
        with patch.object(service, '_fetch_circles', return_value=[mock_wealth_circle]):
            result = await service.get_wealth_circles(user_id="user_123", limit=10)
            
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["circle_id"] == "circle_123"
    
    @pytest.mark.asyncio
    async def test_join_wealth_circle(self, service):
        """Test joining a wealth circle"""
        with patch.object(service, '_add_member', return_value=True):
            result = await service.join_wealth_circle("circle_123", "user_456")
            
            assert result is not None
            assert result["success"] is True
            assert result["circle_id"] == "circle_123"
            assert result["user_id"] == "user_456"
    
    @pytest.mark.asyncio
    async def test_create_discussion_post(self, service):
        """Test creating a discussion post"""
        post_data = {
            "circle_id": "circle_123",
            "author_id": "user_123",
            "title": "Investment Strategy Discussion",
            "content": "What are your thoughts on DCA?",
            "tags": ["investment", "strategy"]
        }
        
        with patch.object(service, '_save_post', return_value="post_789"):
            result = await service.create_discussion_post(post_data)
            
            assert result is not None
            assert "post_id" in result
            assert result["title"] == "Investment Strategy Discussion"
            assert result["author_id"] == "user_123"
    
    @pytest.mark.asyncio
    async def test_get_discussion_posts(self, service):
        """Test getting discussion posts"""
        mock_posts = [
            {
                "post_id": "post_1",
                "title": "Post 1",
                "content": "Content 1",
                "author_id": "user_1",
                "created_at": datetime.now()
            },
            {
                "post_id": "post_2", 
                "title": "Post 2",
                "content": "Content 2",
                "author_id": "user_2",
                "created_at": datetime.now()
            }
        ]
        
        with patch.object(service, '_fetch_posts', return_value=mock_posts):
            result = await service.get_discussion_posts("circle_123", limit=10)
            
            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["post_id"] == "post_1"


class TestPeerProgressService:
    """Test Peer Progress Service"""
    
    @pytest.fixture
    def service(self):
        return PeerProgressService()
    
    @pytest.fixture
    def mock_progress_update(self):
        return {
            "user_id": "user_123",
            "achievement_type": "module_completed",
            "description": "Completed Options Trading Basics",
            "points_earned": 50,
            "timestamp": datetime.now(),
            "is_anonymous": True
        }
    
    @pytest.mark.asyncio
    async def test_share_progress(self, service, mock_progress_update):
        """Test sharing progress update"""
        with patch.object(service, '_save_progress_update', return_value="update_456"):
            result = await service.share_progress(mock_progress_update)
            
            assert result is not None
            assert "update_id" in result
            assert result["user_id"] == "user_123"
            assert result["achievement_type"] == "module_completed"
    
    @pytest.mark.asyncio
    async def test_get_community_stats(self, service):
        """Test getting community statistics"""
        mock_stats = {
            "total_members": 1250,
            "active_today": 230,
            "new_achievements": 87,
            "top_achievement_types": ["module_completed", "quiz_passed", "streak_milestone"]
        }
        
        with patch.object(service, '_fetch_community_stats', return_value=mock_stats):
            result = await service.get_community_stats("community_123")
            
            assert result is not None
            assert result["total_members"] == 1250
            assert result["active_today"] == 230
            assert "top_achievement_types" in result
    
    @pytest.mark.asyncio
    async def test_get_recent_achievements(self, service):
        """Test getting recent achievements"""
        mock_achievements = [
            {
                "user_id": "user_1",
                "achievement": "Completed Risk Management Module",
                "timestamp": datetime.now() - timedelta(hours=1),
                "is_anonymous": True
            },
            {
                "user_id": "user_2",
                "achievement": "Scored 95% on Options Quiz",
                "timestamp": datetime.now() - timedelta(hours=2),
                "is_anonymous": True
            }
        ]
        
        with patch.object(service, '_fetch_recent_achievements', return_value=mock_achievements):
            result = await service.get_recent_achievements("community_123", limit=10)
            
            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["achievement"] == "Completed Risk Management Module"


class TestTradeSimulatorService:
    """Test Trade Simulator Service"""
    
    @pytest.fixture
    def service(self):
        return TradeSimulatorService()
    
    @pytest.fixture
    def mock_challenge(self):
        return {
            "challenge_id": "challenge_123",
            "title": "AAPL Earnings Prediction",
            "description": "Predict AAPL stock movement after earnings",
            "type": "prediction",
            "asset": "AAPL",
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(days=7),
            "reward": "500 points",
            "participant_count": 150,
            "status": "active"
        }
    
    @pytest.mark.asyncio
    async def test_create_challenge(self, service):
        """Test creating a trading challenge"""
        challenge_data = {
            "title": "Test Challenge",
            "description": "Test description",
            "type": "simulation",
            "asset": "SPY",
            "duration_days": 5,
            "reward": "100 points",
            "creator_id": "user_123"
        }
        
        with patch.object(service, '_save_challenge', return_value="challenge_456"):
            result = await service.create_challenge(challenge_data)
            
            assert result is not None
            assert "challenge_id" in result
            assert result["title"] == "Test Challenge"
            assert result["type"] == "simulation"
    
    @pytest.mark.asyncio
    async def test_get_active_challenges(self, service, mock_challenge):
        """Test getting active challenges"""
        with patch.object(service, '_fetch_challenges', return_value=[mock_challenge]):
            result = await service.get_active_challenges(limit=10)
            
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["challenge_id"] == "challenge_123"
            assert result[0]["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_make_prediction(self, service):
        """Test making a prediction for a challenge"""
        prediction_data = {
            "challenge_id": "challenge_123",
            "user_id": "user_456",
            "prediction": "AAPL will increase by 3%",
            "confidence": 0.85,
            "reasoning": "Strong earnings expected"
        }
        
        with patch.object(service, '_save_prediction', return_value="prediction_789"):
            result = await service.make_prediction(prediction_data)
            
            assert result is not None
            assert "prediction_id" in result
            assert result["challenge_id"] == "challenge_123"
            assert result["user_id"] == "user_456"
            assert result["confidence"] == 0.85
    
    @pytest.mark.asyncio
    async def test_get_challenge_leaderboard(self, service):
        """Test getting challenge leaderboard"""
        mock_leaderboard = [
            {"user_id": "user_1", "score": 1250, "rank": 1, "username": "EliteTrader"},
            {"user_id": "user_2", "score": 1180, "rank": 2, "username": "AlphaSeeker"},
            {"user_id": "user_3", "score": 1050, "rank": 3, "username": "QuantKing"}
        ]
        
        with patch.object(service, '_fetch_leaderboard', return_value=mock_leaderboard):
            result = await service.get_challenge_leaderboard("challenge_123", limit=10)
            
            assert isinstance(result, list)
            assert len(result) == 3
            assert result[0]["rank"] == 1
            assert result[0]["score"] == 1250
    
    @pytest.mark.asyncio
    async def test_join_challenge(self, service):
        """Test joining a challenge"""
        with patch.object(service, '_add_participant', return_value=True):
            result = await service.join_challenge("challenge_123", "user_456")
            
            assert result is not None
            assert result["success"] is True
            assert result["challenge_id"] == "challenge_123"
            assert result["user_id"] == "user_456"


# Integration tests for Phase 2 services
class TestPhase2Integration:
    """Integration tests for Phase 2 services working together"""
    
    @pytest.mark.asyncio
    async def test_wealth_circle_with_discussions(self):
        """Test wealth circle creation with discussion posts"""
        circles_service = WealthCirclesService()
        
        # Create a wealth circle
        circle_data = {
            "name": "Integration Test Circle",
            "description": "Testing integration",
            "creator_id": "user_123",
            "is_private": False
        }
        
        with patch.object(circles_service, '_save_circle', return_value="circle_integration"):
            circle = await circles_service.create_wealth_circle(circle_data)
            
            assert circle is not None
            
            # Create a discussion post in the circle
            post_data = {
                "circle_id": circle["circle_id"],
                "author_id": "user_123",
                "title": "Welcome to our circle!",
                "content": "Let's discuss our wealth building strategies"
            }
            
            with patch.object(circles_service, '_save_post', return_value="post_integration"):
                post = await circles_service.create_discussion_post(post_data)
                
                assert post is not None
                assert post["circle_id"] == circle["circle_id"]
    
    @pytest.mark.asyncio
    async def test_challenge_with_predictions_and_leaderboard(self):
        """Test challenge creation with predictions and leaderboard"""
        simulator_service = TradeSimulatorService()
        
        # Create a challenge
        challenge_data = {
            "title": "Integration Test Challenge",
            "description": "Testing challenge integration",
            "type": "prediction",
            "asset": "TSLA",
            "duration_days": 3,
            "creator_id": "user_123"
        }
        
        with patch.object(simulator_service, '_save_challenge', return_value="challenge_integration"):
            challenge = await simulator_service.create_challenge(challenge_data)
            
            assert challenge is not None
            
            # Make a prediction
            prediction_data = {
                "challenge_id": challenge["challenge_id"],
                "user_id": "user_456",
                "prediction": "TSLA will increase by 5%",
                "confidence": 0.80
            }
            
            with patch.object(simulator_service, '_save_prediction', return_value="prediction_integration"):
                prediction = await simulator_service.make_prediction(prediction_data)
                
                assert prediction is not None
                
                # Get leaderboard
                mock_leaderboard = [
                    {"user_id": "user_456", "score": 800, "rank": 1}
                ]
                
                with patch.object(simulator_service, '_fetch_leaderboard', return_value=mock_leaderboard):
                    leaderboard = await simulator_service.get_challenge_leaderboard(challenge["challenge_id"])
                    
                    assert isinstance(leaderboard, list)
                    assert leaderboard[0]["user_id"] == "user_456"
    
    @pytest.mark.asyncio
    async def test_progress_sharing_with_community_stats(self):
        """Test progress sharing with community statistics"""
        progress_service = PeerProgressService()
        
        # Share progress
        progress_data = {
            "user_id": "user_123",
            "achievement_type": "integration_test",
            "description": "Completed integration test",
            "points_earned": 100
        }
        
        with patch.object(progress_service, '_save_progress_update', return_value="update_integration"):
            progress = await progress_service.share_progress(progress_data)
            
            assert progress is not None
            
            # Get community stats
            mock_stats = {
                "total_members": 1000,
                "active_today": 50,
                "new_achievements": 10
            }
            
            with patch.object(progress_service, '_fetch_community_stats', return_value=mock_stats):
                stats = await progress_service.get_community_stats("community_123")
                
                assert stats is not None
                assert stats["total_members"] == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
