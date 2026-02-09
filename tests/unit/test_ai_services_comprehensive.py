"""
Comprehensive unit tests for all AI services in RichesReach AI platform.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone
import json

# Import all AI services
try:
    from backend.backend.core.ai_tutor_service import AITutorService
    from backend.backend.core.assistant_service import AssistantService
    from backend.backend.core.trading_coach_service import TradingCoachService
    from backend.backend.core.ai_trading_coach_service import AITradingCoachService
    from backend.backend.core.dynamic_content_service import DynamicContentService
    from backend.backend.core.genai_education_service import GenAIEducationService
except ModuleNotFoundError:
    pytest.skip("Legacy backend.backend.core module path not available", allow_module_level=True)

class TestAITutorService:
    """Comprehensive tests for AI Tutor Service."""
    
    @pytest.fixture
    def tutor_service(self, mock_ai_router, mock_ml_service):
        """Create AI Tutor Service instance for testing."""
        with patch('backend.backend.core.ai_tutor_service.get_advanced_ai_router', return_value=mock_ai_router):
            with patch('backend.backend.core.ai_tutor_service.MLService', return_value=mock_ml_service):
                return AITutorService()
    
    @pytest.mark.asyncio
    async def test_ask_question_success(self, tutor_service, mock_user_profile):
        """Test successful question asking."""
        question = "What is options trading?"
        user_id = "test_user_123"
        
        result = await tutor_service.ask_question(question, user_id, mock_user_profile)
        
        assert result is not None
        assert "response" in result
        assert "model" in result
        assert "timestamp" in result
        assert result["user_id"] == user_id
        assert result["question"] == question
    
    @pytest.mark.asyncio
    async def test_ask_question_with_context(self, tutor_service, mock_user_profile):
        """Test question asking with additional context."""
        question = "How do I calculate option Greeks?"
        user_id = "test_user_123"
        context = {"topic": "options", "difficulty": "intermediate"}
        
        result = await tutor_service.ask_question(question, user_id, mock_user_profile, context)
        
        assert result is not None
        assert result["context"] == context
    
    @pytest.mark.asyncio
    async def test_explain_concept_success(self, tutor_service, mock_user_profile):
        """Test successful concept explanation."""
        concept = "Black-Scholes model"
        user_id = "test_user_123"
        
        result = await tutor_service.explain_concept(concept, user_id, mock_user_profile)
        
        assert result is not None
        assert "explanation" in result
        assert "examples" in result
        assert "key_points" in result
        assert result["concept"] == concept
    
    @pytest.mark.asyncio
    async def test_generate_quiz_success(self, tutor_service, mock_user_profile):
        """Test successful quiz generation."""
        topic = "Options Trading Basics"
        user_id = "test_user_123"
        difficulty = "intermediate"
        
        result = await tutor_service.generate_quiz(topic, user_id, mock_user_profile, difficulty)
        
        assert result is not None
        assert "quiz_id" in result
        assert "questions" in result
        assert "topic" in result
        assert result["topic"] == topic
        assert result["difficulty"] == difficulty
        assert len(result["questions"]) > 0
    
    @pytest.mark.asyncio
    async def test_generate_regime_adaptive_quiz(self, tutor_service, mock_user_profile):
        """Test regime-adaptive quiz generation."""
        topic = "Market Analysis"
        user_id = "test_user_123"
        
        result = await tutor_service.generate_regime_adaptive_quiz(topic, user_id, mock_user_profile)
        
        assert result is not None
        assert "regime_context" in result
        assert "current_regime" in result["regime_context"]
        assert "regime_confidence" in result["regime_context"]
        assert "relevant_strategies" in result["regime_context"]
    
    @pytest.mark.asyncio
    async def test_evaluate_answer_success(self, tutor_service):
        """Test successful answer evaluation."""
        question = "What is a call option?"
        user_answer = "Right to buy at strike price"
        correct_answer = "Right to buy at strike price"
        
        result = await tutor_service.evaluate_answer(question, user_answer, correct_answer)
        
        assert result is not None
        assert "is_correct" in result
        assert "score" in result
        assert "feedback" in result
        assert result["is_correct"] is True
        assert result["score"] == 100
    
    @pytest.mark.asyncio
    async def test_ai_service_error_handling(self, tutor_service, mock_user_profile):
        """Test error handling when AI service fails."""
        # Mock AI router to raise an exception
        tutor_service.ai_router.route_request = AsyncMock(side_effect=Exception("AI service unavailable"))
        
        with pytest.raises(Exception):
            await tutor_service.ask_question("Test question", "test_user", mock_user_profile)
    
    @pytest.mark.asyncio
    async def test_invalid_input_handling(self, tutor_service, mock_user_profile):
        """Test handling of invalid inputs."""
        # Test empty question
        with pytest.raises(ValueError):
            await tutor_service.ask_question("", "test_user", mock_user_profile)
        
        # Test None user_id
        with pytest.raises(ValueError):
            await tutor_service.ask_question("Test question", None, mock_user_profile)

class TestAssistantService:
    """Comprehensive tests for Assistant Service."""
    
    @pytest.fixture
    def assistant_service(self, mock_ai_router):
        """Create Assistant Service instance for testing."""
        with patch('backend.backend.core.assistant_service.get_advanced_ai_router', return_value=mock_ai_router):
            return AssistantService()
    
    @pytest.mark.asyncio
    async def test_query_success(self, assistant_service, mock_user_profile):
        """Test successful assistant query."""
        query = "What's the best strategy for a bull market?"
        user_id = "test_user_123"
        
        result = await assistant_service.query(query, user_id, mock_user_profile)
        
        assert result is not None
        assert "response" in result
        assert "sources" in result
        assert "confidence" in result
        assert result["user_id"] == user_id
        assert result["query"] == query
    
    @pytest.mark.asyncio
    async def test_query_with_context(self, assistant_service, mock_user_profile):
        """Test assistant query with context."""
        query = "Should I buy AAPL options?"
        user_id = "test_user_123"
        context = {"portfolio": {"AAPL": 100}, "risk_tolerance": "moderate"}
        
        result = await assistant_service.query(query, user_id, mock_user_profile, context)
        
        assert result is not None
        assert result["context"] == context
    
    @pytest.mark.asyncio
    async def test_financial_advice_disclaimer(self, assistant_service, mock_user_profile):
        """Test that financial advice includes proper disclaimers."""
        query = "Should I invest in Tesla?"
        user_id = "test_user_123"
        
        result = await assistant_service.query(query, user_id, mock_user_profile)
        
        assert result is not None
        assert "disclaimer" in result
        assert "not financial advice" in result["disclaimer"].lower()

class TestTradingCoachService:
    """Comprehensive tests for Trading Coach Service."""
    
    @pytest.fixture
    def coach_service(self, mock_ai_router):
        """Create Trading Coach Service instance for testing."""
        with patch('backend.backend.core.trading_coach_service.get_advanced_ai_router', return_value=mock_ai_router):
            return TradingCoachService()
    
    @pytest.mark.asyncio
    async def test_advise_success(self, coach_service, mock_user_profile):
        """Test successful trading advice."""
        situation = "I want to start options trading"
        user_id = "test_user_123"
        
        result = await coach_service.advise(situation, user_id, mock_user_profile)
        
        assert result is not None
        assert "advice" in result
        assert "risk_level" in result
        assert "recommendations" in result
        assert result["user_id"] == user_id
        assert result["situation"] == situation
    
    @pytest.mark.asyncio
    async def test_strategy_recommendation(self, coach_service, mock_user_profile):
        """Test strategy recommendation."""
        market_condition = "bull_market"
        user_id = "test_user_123"
        risk_tolerance = "moderate"
        
        result = await coach_service.strategy(market_condition, user_id, mock_user_profile, risk_tolerance)
        
        assert result is not None
        assert "strategies" in result
        assert "market_condition" in result
        assert result["market_condition"] == market_condition
        assert len(result["strategies"]) > 0
    
    @pytest.mark.asyncio
    async def test_risk_assessment(self, coach_service, mock_user_profile):
        """Test risk assessment functionality."""
        portfolio = {"AAPL": 100, "TSLA": 50}
        user_id = "test_user_123"
        
        result = await coach_service.assess_risk(portfolio, user_id, mock_user_profile)
        
        assert result is not None
        assert "risk_score" in result
        assert "risk_factors" in result
        assert "recommendations" in result
        assert 0 <= result["risk_score"] <= 100

class TestAITradingCoachService:
    """Comprehensive tests for AI Trading Coach Service."""
    
    @pytest.fixture
    def ai_coach_service(self, mock_ai_router):
        """Create AI Trading Coach Service instance for testing."""
        with patch('backend.backend.core.ai_trading_coach_service.AdvancedAIRouter', return_value=mock_ai_router):
            return AITradingCoachService()
    
    @pytest.mark.asyncio
    async def test_get_strategy_recommendations(self, ai_coach_service, mock_user_profile):
        """Test strategy recommendations."""
        user_id = "test_user_123"
        market_data = {"AAPL": {"price": 150, "volatility": 0.25}}
        
        result = await ai_coach_service.get_strategy_recommendations(user_id, mock_user_profile, market_data)
        
        assert result is not None
        assert "recommendations" in result
        assert "confidence_score" in result
        assert "market_analysis" in result
        assert len(result["recommendations"]) > 0
    
    @pytest.mark.asyncio
    async def test_get_real_time_guidance(self, ai_coach_service, mock_user_profile):
        """Test real-time trading guidance."""
        user_id = "test_user_123"
        current_position = {"symbol": "AAPL", "quantity": 100, "entry_price": 145}
        market_data = {"AAPL": {"price": 150, "change": 0.03}}
        
        result = await ai_coach_service.get_real_time_guidance(user_id, current_position, market_data, mock_user_profile)
        
        assert result is not None
        assert "guidance" in result
        assert "action" in result
        assert "confidence" in result
        assert "reasoning" in result
    
    @pytest.mark.asyncio
    async def test_analyze_trade(self, ai_coach_service, mock_user_profile):
        """Test trade analysis."""
        user_id = "test_user_123"
        trade_data = {
            "symbol": "AAPL",
            "action": "buy",
            "quantity": 100,
            "price": 150,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        result = await ai_coach_service.analyze_trade(user_id, trade_data, mock_user_profile)
        
        assert result is not None
        assert "analysis" in result
        assert "strengths" in result
        assert "improvements" in result
        assert "score" in result
    
    @pytest.mark.asyncio
    async def test_build_confidence(self, ai_coach_service, mock_user_profile):
        """Test confidence building."""
        user_id = "test_user_123"
        recent_trades = [
            {"symbol": "AAPL", "profit": 500, "confidence": 0.8},
            {"symbol": "TSLA", "profit": -200, "confidence": 0.6}
        ]
        
        result = await ai_coach_service.build_confidence(user_id, recent_trades, mock_user_profile)
        
        assert result is not None
        assert "confidence_score" in result
        assert "motivational_message" in result
        assert "improvement_areas" in result
        assert "success_celebrations" in result

class TestDynamicContentService:
    """Comprehensive tests for Dynamic Content Service."""
    
    @pytest.fixture
    def content_service(self, mock_ai_router):
        """Create Dynamic Content Service instance for testing."""
        with patch('backend.backend.core.dynamic_content_service.get_advanced_ai_router', return_value=mock_ai_router):
            return DynamicContentService()
    
    @pytest.mark.asyncio
    async def test_generate_module_success(self, content_service, mock_user_profile):
        """Test successful module generation."""
        topic = "Options Trading Strategies"
        user_id = "test_user_123"
        difficulty = "intermediate"
        
        result = await content_service.generate_module(topic, user_id, mock_user_profile, difficulty)
        
        assert result is not None
        assert "module_id" in result
        assert "title" in result
        assert "content" in result
        assert "interactive_elements" in result
        assert result["topic"] == topic
        assert result["difficulty"] == difficulty
    
    @pytest.mark.asyncio
    async def test_generate_market_commentary(self, content_service, mock_user_profile):
        """Test market commentary generation."""
        user_id = "test_user_123"
        horizon = "daily"
        tone = "professional"
        
        result = await content_service.generate_market_commentary(user_id, mock_user_profile, horizon, tone)
        
        assert result is not None
        assert "commentary_id" in result
        assert "headlines" in result
        assert "summary" in result
        assert "key_drivers" in result
        assert "sector_analysis" in result
        assert result["horizon"] == horizon
        assert result["tone"] == tone
    
    @pytest.mark.asyncio
    async def test_adapt_content(self, content_service, mock_user_profile):
        """Test content adaptation."""
        user_id = "test_user_123"
        original_content = {
            "title": "Basic Options Trading",
            "difficulty": "beginner",
            "duration": 30
        }
        user_behavior = {
            "learning_speed": "fast",
            "preferred_format": "interactive"
        }
        
        result = await content_service.adapt_content(user_id, original_content, user_behavior, mock_user_profile)
        
        assert result is not None
        assert "adapted_content" in result
        assert "adaptation_reasoning" in result
        assert "personalization_score" in result

class TestGenAIEducationService:
    """Comprehensive tests for GenAI Education Service."""
    
    @pytest.fixture
    def education_service(self, mock_ai_router):
        """Create GenAI Education Service instance for testing."""
        with patch('backend.backend.core.genai_education_service.get_advanced_ai_router', return_value=mock_ai_router):
            return GenAIEducationService()
    
    @pytest.mark.asyncio
    async def test_create_learning_profile(self, education_service):
        """Test learning profile creation."""
        user_id = "test_user_123"
        user_data = {
            "experience_level": "intermediate",
            "interests": ["options", "portfolio_management"],
            "learning_style": "visual"
        }
        
        result = await education_service.create_learning_profile(user_id, user_data)
        
        assert result is not None
        assert "profile_id" in result
        assert "learning_path" in result
        assert "recommended_modules" in result
        assert result["user_id"] == user_id
    
    @pytest.mark.asyncio
    async def test_generate_learning_path(self, education_service, mock_user_profile):
        """Test learning path generation."""
        user_id = "test_user_123"
        goals = ["master_options_trading", "build_diversified_portfolio"]
        
        result = await education_service.generate_learning_path(user_id, goals, mock_user_profile)
        
        assert result is not None
        assert "path_id" in result
        assert "modules" in result
        assert "estimated_duration" in result
        assert "difficulty_progression" in result
        assert len(result["modules"]) > 0
    
    @pytest.mark.asyncio
    async def test_generate_personalized_questions(self, education_service, mock_user_profile):
        """Test personalized question generation."""
        user_id = "test_user_123"
        topic = "Risk Management"
        difficulty = "intermediate"
        
        result = await education_service.generate_personalized_questions(user_id, topic, difficulty, mock_user_profile)
        
        assert result is not None
        assert "questions" in result
        assert "topic" in result
        assert "difficulty" in result
        assert len(result["questions"]) > 0
        assert all("question" in q for q in result["questions"])

# Integration tests for AI services
class TestAIServicesIntegration:
    """Integration tests for AI services working together."""
    
    @pytest.mark.asyncio
    async def test_tutor_to_coach_workflow(self, mock_ai_router, mock_user_profile):
        """Test workflow from tutor to trading coach."""
        with patch('backend.backend.core.ai_tutor_service.get_advanced_ai_router', return_value=mock_ai_router):
            with patch('backend.backend.core.trading_coach_service.get_advanced_ai_router', return_value=mock_ai_router):
                tutor = AITutorService()
                coach = TradingCoachService()
                
                # User asks tutor about options
                tutor_response = await tutor.ask_question("What are call options?", "test_user", mock_user_profile)
                assert tutor_response is not None
                
                # User then asks coach for strategy
                coach_response = await coach.advise("I want to start with call options", "test_user", mock_user_profile)
                assert coach_response is not None
    
    @pytest.mark.asyncio
    async def test_content_to_quiz_workflow(self, mock_ai_router, mock_user_profile):
        """Test workflow from content generation to quiz creation."""
        with patch('backend.backend.core.dynamic_content_service.get_advanced_ai_router', return_value=mock_ai_router):
            with patch('backend.backend.core.ai_tutor_service.get_advanced_ai_router', return_value=mock_ai_router):
                content_service = DynamicContentService()
                tutor_service = AITutorService()
                
                # Generate content module
                module = await content_service.generate_module("Options Basics", "test_user", mock_user_profile)
                assert module is not None
                
                # Create quiz based on module
                quiz = await tutor_service.generate_quiz("Options Basics", "test_user", mock_user_profile)
                assert quiz is not None

# Performance tests
class TestAIServicesPerformance:
    """Performance tests for AI services."""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_requests(self, mock_ai_router, mock_user_profile):
        """Test handling of concurrent requests."""
        with patch('backend.backend.core.ai_tutor_service.get_advanced_ai_router', return_value=mock_ai_router):
            tutor = AITutorService()
            
            # Create multiple concurrent requests
            tasks = []
            for i in range(10):
                task = tutor.ask_question(f"Question {i}", f"user_{i}", mock_user_profile)
                tasks.append(task)
            
            # Execute all requests concurrently
            results = await asyncio.gather(*tasks)
            
            # Verify all requests completed successfully
            assert len(results) == 10
            assert all(result is not None for result in results)
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_response_time(self, mock_ai_router, mock_user_profile):
        """Test response time for AI services."""
        import time
        
        with patch('backend.backend.core.ai_tutor_service.get_advanced_ai_router', return_value=mock_ai_router):
            tutor = AITutorService()
            start_time = time.time()
            result = await tutor.ask_question("Test question", "test_user", mock_user_profile)
            end_time = time.time()

            response_time = end_time - start_time
            assert response_time < 5.0  # Should respond within 5 seconds
            assert result is not None

# Error handling and edge cases
class TestAIServicesErrorHandling:
    """Test error handling and edge cases for AI services."""
    
    @pytest.mark.asyncio
    async def test_network_timeout(self, mock_user_profile):
        """Test handling of network timeouts."""
        mock_router = AsyncMock()
        mock_router.route_request = AsyncMock(side_effect=asyncio.TimeoutError("Request timeout"))
        
        with patch('backend.backend.core.ai_tutor_service.get_advanced_ai_router', return_value=mock_router):
            tutor = AITutorService()
            
            with pytest.raises(asyncio.TimeoutError):
                await tutor.ask_question("Test question", "test_user", mock_user_profile)
    
    @pytest.mark.asyncio
    async def test_invalid_json_response(self, mock_user_profile):
        """Test handling of invalid JSON responses."""
        mock_router = AsyncMock()
        mock_router.route_request = AsyncMock(return_value="Invalid JSON response")
        
        with patch('backend.backend.core.ai_tutor_service.get_advanced_ai_router', return_value=mock_router):
            tutor = AITutorService()
            
            # Should handle invalid JSON gracefully
            result = await tutor.ask_question("Test question", "test_user", mock_user_profile)
            assert result is not None  # Should have fallback response
    
    @pytest.mark.asyncio
    async def test_empty_response(self, mock_user_profile):
        """Test handling of empty responses."""
        mock_router = AsyncMock()
        mock_router.route_request = AsyncMock(return_value="")
        
        with patch('backend.backend.core.ai_tutor_service.get_advanced_ai_router', return_value=mock_router):
            tutor = AITutorService()
            
            result = await tutor.ask_question("Test question", "test_user", mock_user_profile)
            assert result is not None  # Should have fallback response
