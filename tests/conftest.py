"""
Comprehensive testing configuration and fixtures for RichesReach AI platform.
"""

import pytest
import asyncio
import json
from typing import Dict, Any, Generator
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient
import tempfile
import os

# Test configuration
pytest_plugins = ["pytest_asyncio"]

# Global test configuration
TEST_CONFIG = {
    "BASE_URL": "http://127.0.0.1:8000",
    "TEST_USER_EMAIL": "test@example.com",
    "TEST_USER_PASSWORD": "testpass123",
    "TEST_USER_ID": "test_user_123",
    "MOCK_AI_RESPONSES": True,
    "USE_REAL_AI": False,
    "TEST_TIMEOUT": 30,
    "MAX_CONCURRENT_TESTS": 10
}

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_config():
    """Provide test configuration."""
    return TEST_CONFIG

@pytest.fixture
def mock_ai_router():
    """Mock AI router for testing without real AI services."""
    mock_router = Mock()
    mock_router.route_request = AsyncMock(return_value={
        "response": "Mock AI response for testing",
        "model": "gpt-4o-mini",
        "tokens_used": 100,
        "cost": 0.001
    })
    return mock_router

@pytest.fixture
def mock_ml_service():
    """Mock ML service for testing."""
    mock_service = Mock()
    mock_service.predict_market_regime = Mock(return_value={
        "regime": "bull_market",
        "confidence": 0.85,
        "features": ["high_volume", "positive_sentiment"]
    })
    mock_service.is_available = Mock(return_value=True)
    return mock_service

@pytest.fixture
def mock_market_data():
    """Mock market data for testing."""
    return {
        "AAPL": {
            "symbol": "AAPL",
            "price": 150.25,
            "change": 2.15,
            "change_percent": 1.45,
            "volume": 50000000,
            "market_cap": 2500000000000
        },
        "TSLA": {
            "symbol": "TSLA",
            "price": 245.80,
            "change": -5.20,
            "change_percent": -2.07,
            "volume": 30000000,
            "market_cap": 780000000000
        }
    }

@pytest.fixture
def mock_user_profile():
    """Mock user profile for testing."""
    return {
        "user_id": "test_user_123",
        "email": "test@example.com",
        "name": "Test User",
        "risk_tolerance": "moderate",
        "investment_goals": ["growth", "income"],
        "experience_level": "intermediate",
        "preferred_assets": ["stocks", "options"],
        "learning_preferences": {
            "difficulty": "intermediate",
            "topics": ["options_trading", "portfolio_management"],
            "format": "interactive"
        }
    }

@pytest.fixture
def mock_quiz_data():
    """Mock quiz data for testing."""
    return {
        "quiz_id": "quiz_123",
        "topic": "Options Trading Basics",
        "difficulty": "intermediate",
        "questions": [
            {
                "question_id": "q1",
                "question": "What is a call option?",
                "options": [
                    "Right to buy at strike price",
                    "Right to sell at strike price",
                    "Obligation to buy at strike price",
                    "Obligation to sell at strike price"
                ],
                "correct_answer": 0,
                "explanation": "A call option gives the holder the right to buy the underlying asset at the strike price."
            }
        ],
        "time_limit": 300,
        "passing_score": 70
    }

@pytest.fixture
def mock_community_data():
    """Mock community data for testing."""
    return {
        "wealth_circles": [
            {
                "circle_id": "circle_123",
                "name": "Options Trading Circle",
                "description": "Learn options trading strategies",
                "members": 150,
                "moderators": ["user_1", "user_2"],
                "focus_area": "options_trading",
                "is_private": False
            }
        ],
        "discussion_posts": [
            {
                "post_id": "post_123",
                "title": "Best Options Strategies for Beginners",
                "content": "What are the safest options strategies to start with?",
                "author_id": "user_123",
                "circle_id": "circle_123",
                "likes": 25,
                "replies": 8
            }
        ]
    }

@pytest.fixture
def mock_personalization_data():
    """Mock personalization data for testing."""
    return {
        "engagement_profile": {
            "user_id": "test_user_123",
            "engagement_score": 0.85,
            "preferred_content_types": ["interactive", "video"],
            "learning_velocity": "fast",
            "retention_rate": 0.92
        },
        "behavior_patterns": [
            {
                "pattern_id": "pattern_1",
                "pattern_type": "learning_preference",
                "description": "Prefers interactive content over text",
                "confidence": 0.88,
                "frequency": "daily"
            }
        ],
        "recommendations": [
            {
                "recommendation_id": "rec_1",
                "type": "content",
                "title": "Advanced Options Strategies",
                "reason": "Based on your learning progress",
                "confidence": 0.92
            }
        ]
    }

@pytest.fixture
def auth_headers():
    """Provide authentication headers for API testing."""
    return {
        "Authorization": "Bearer test_token_123",
        "Content-Type": "application/json",
        "X-Request-ID": "test_request_123"
    }

@pytest.fixture
def test_client():
    """Create a test client for API testing."""
    from test_server_minimal import app
    return TestClient(app)

@pytest.fixture
async def async_client():
    """Create an async test client for API testing."""
    from test_server_minimal import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test data")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def mock_redis():
    """Mock Redis for caching tests."""
    mock_redis = Mock()
    mock_redis.get = Mock(return_value=None)
    mock_redis.set = Mock(return_value=True)
    mock_redis.delete = Mock(return_value=True)
    mock_redis.exists = Mock(return_value=False)
    return mock_redis

@pytest.fixture
def mock_database():
    """Mock database for testing."""
    mock_db = Mock()
    mock_db.execute = AsyncMock()
    mock_db.fetch_one = AsyncMock()
    mock_db.fetch_all = AsyncMock()
    return mock_db

@pytest.fixture
def sample_error_responses():
    """Sample error responses for testing error handling."""
    return {
        "validation_error": {
            "detail": [
                {
                    "loc": ["body", "email"],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ]
        },
        "authentication_error": {
            "detail": "Invalid credentials"
        },
        "not_found_error": {
            "detail": "Resource not found"
        },
        "rate_limit_error": {
            "detail": "Rate limit exceeded"
        }
    }

@pytest.fixture
def performance_metrics():
    """Performance metrics for testing."""
    return {
        "response_time_threshold": 2.0,  # seconds
        "memory_usage_threshold": 100,   # MB
        "cpu_usage_threshold": 80,       # percentage
        "concurrent_users_threshold": 1000
    }

# Test data generators
@pytest.fixture
def generate_test_users():
    """Generate test user data."""
    def _generate(count: int = 10):
        users = []
        for i in range(count):
            users.append({
                "user_id": f"test_user_{i}",
                "email": f"test{i}@example.com",
                "name": f"Test User {i}",
                "risk_tolerance": ["conservative", "moderate", "aggressive"][i % 3],
                "experience_level": ["beginner", "intermediate", "advanced"][i % 3]
            })
        return users
    return _generate

@pytest.fixture
def generate_test_quizzes():
    """Generate test quiz data."""
    def _generate(count: int = 5):
        quizzes = []
        topics = ["Options Trading", "Portfolio Management", "Risk Management", "Market Analysis", "Technical Analysis"]
        for i in range(count):
            quizzes.append({
                "quiz_id": f"quiz_{i}",
                "topic": topics[i % len(topics)],
                "difficulty": ["beginner", "intermediate", "advanced"][i % 3],
                "question_count": 5 + (i % 5),
                "time_limit": 300 + (i * 60)
            })
        return quizzes
    return _generate

# Async test utilities
@pytest.fixture
async def async_test_helper():
    """Async test helper utilities."""
    class AsyncTestHelper:
        async def wait_for_condition(self, condition_func, timeout=5):
            """Wait for a condition to be true."""
            import asyncio
            start_time = asyncio.get_event_loop().time()
            while asyncio.get_event_loop().time() - start_time < timeout:
                if await condition_func():
                    return True
                await asyncio.sleep(0.1)
            return False
        
        async def retry_async_call(self, func, max_retries=3, delay=1):
            """Retry an async function call."""
            for attempt in range(max_retries):
                try:
                    return await func()
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    await asyncio.sleep(delay)
    
    return AsyncTestHelper()

# Test markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "api: API tests")
    config.addinivalue_line("markers", "mobile: Mobile tests")
    config.addinivalue_line("markers", "ai: AI service tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "phase1: Phase 1 features")
    config.addinivalue_line("markers", "phase2: Phase 2 features")
    config.addinivalue_line("markers", "phase3: Phase 3 features")

# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add markers based on test file names
        if "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        if "api" in item.nodeid:
            item.add_marker(pytest.mark.api)
        if "mobile" in item.nodeid:
            item.add_marker(pytest.mark.mobile)
        if "ai" in item.nodeid:
            item.add_marker(pytest.mark.ai)
        if "performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)
        
        # Add phase markers
        if "phase1" in item.nodeid:
            item.add_marker(pytest.mark.phase1)
        if "phase2" in item.nodeid:
            item.add_marker(pytest.mark.phase2)
        if "phase3" in item.nodeid:
            item.add_marker(pytest.mark.phase3)
        
        # Mark slow tests
        if "slow" in item.name or "load" in item.name:
            item.add_marker(pytest.mark.slow)

# Test reporting
def pytest_html_report_title(report):
    """Customize HTML report title."""
    report.title = "RichesReach AI - Comprehensive Test Report"

def pytest_html_results_summary(prefix, summary, postfix):
    """Customize HTML report summary."""
    prefix.extend([
        "<h2>Test Summary</h2>",
        "<p>Comprehensive testing of RichesReach AI platform including:</p>",
        "<ul>",
        "<li>Backend services and API endpoints</li>",
        "<li>Mobile UI components and screens</li>",
        "<li>AI features and machine learning models</li>",
        "<li>User workflows and integrations</li>",
        "<li>Performance and load testing</li>",
        "</ul>"
    ])
