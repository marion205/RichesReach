#!/usr/bin/env python3
"""
Minimal test server for endpoint testing
Runs without AI services to test basic functionality
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RichesReach Test Server",
    description="Minimal server for testing endpoints",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request bodies
class LoginRequest(BaseModel):
    email: str
    password: str

class TutorAskRequest(BaseModel):
    user_id: str
    question: str

class TutorQuizRequest(BaseModel):
    user_id: str
    topic: str

class AssistantQueryRequest(BaseModel):
    user_id: str
    prompt: str

class CoachAdviseRequest(BaseModel):
    user_id: str
    goal: str
    risk_tolerance: str
    horizon: str

class CoachStrategyRequest(BaseModel):
    user_id: str
    asset: str
    risk_tolerance: str
    goals: list

class TutorModuleRequest(BaseModel):
    user_id: str
    topic: str

class MarketCommentaryRequest(BaseModel):
    user_id: str
    horizon: str
    tone: str

@app.get("/healthz")
async def health_check():
    """Basic health check"""
    return {"ok": True, "status": "healthy"}

@app.get("/health/detailed")
async def detailed_health():
    """Detailed health check"""
    return {
        "ok": True,
        "status": "healthy",
        "services": {
            "ai_router": {"available": False, "reason": "API keys not configured"},
            "ai_tutor": {"available": False, "reason": "API keys not configured"},
            "ai_assistant": {"available": False, "reason": "API keys not configured"},
            "trading_coach": {"available": False, "reason": "API keys not configured"},
            "market_data": {"available": True, "reason": "Mock data available"},
            "auth": {"available": True, "reason": "Mock auth available"}
        }
    }

@app.post("/auth/login")
async def mock_auth(request: LoginRequest):
    """Mock authentication endpoint"""
    if request.email == "test@example.com" and request.password == "testpass123":
        return {
            "access_token": "mock_token_12345",
            "user": {
                "id": "test-user-123",
                "email": request.email,
                "name": "Test User"
            }
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/market/quote/{symbol}")
async def mock_market_data(symbol: str):
    """Mock market data endpoint"""
    mock_prices = {
        "AAPL": 150.25,
        "GOOGL": 2800.50,
        "MSFT": 350.75,
        "TSLA": 200.00,
        "NVDA": 450.30
    }
    
    price = mock_prices.get(symbol.upper(), 100.00)
    return {
        "symbol": symbol.upper(),
        "price": price,
        "change": 1.25,
        "change_percent": 0.84,
        "volume": 1000000,
        "timestamp": "2024-01-15T10:30:00Z"
    }

@app.post("/tutor/ask")
async def mock_tutor_ask(request: TutorAskRequest):
    """Mock AI Tutor ask endpoint"""
    return {
        "response": f"Mock response to: {request.question}. This is a test response from the AI Tutor. The question was about financial topics and I'm providing educational information.",
        "model": "mock-gpt-4",
        "confidence_score": 0.85,
        "timestamp": "2024-01-15T10:30:00Z"
    }

@app.post("/tutor/quiz")
async def mock_tutor_quiz(request: TutorQuizRequest):
    """Mock AI Tutor quiz endpoint"""
    return {
        "questions": [
            {
                "id": "q1",
                "question": f"What is the main principle of {request.topic}?",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_answer": 0,
                "explanation": "This is the correct answer because..."
            },
            {
                "id": "q2", 
                "question": f"How does {request.topic} affect investment decisions?",
                "options": ["Positively", "Negatively", "Neutrally", "Depends"],
                "correct_answer": 3,
                "explanation": "The impact depends on various factors..."
            }
        ],
        "topic": request.topic,
        "difficulty": "intermediate",
        "timestamp": "2024-01-15T10:30:00Z"
    }

@app.post("/assistant/query")
async def mock_assistant_query(request: AssistantQueryRequest):
    """Mock AI Assistant query endpoint"""
    return {
        "answer": f"Mock AI Assistant response to: {request.prompt}. This is a comprehensive answer about financial topics, providing educational information and guidance.",
        "model": "mock-claude-3.5",
        "confidence": 0.90,
        "timestamp": "2024-01-15T10:30:00Z"
    }

@app.post("/coach/advise")
async def mock_coach_advise(request: CoachAdviseRequest):
    """Mock Trading Coach advise endpoint"""
    return {
        "advice": f"Mock trading advice for {request.goal} with {request.risk_tolerance} risk tolerance over a {request.horizon} horizon. Consider diversifying your portfolio and maintaining a long-term perspective.",
        "risk_level": request.risk_tolerance,
        "recommended_actions": [
            "Diversify across asset classes",
            "Set clear investment goals",
            "Monitor market conditions",
            "Review portfolio regularly"
        ],
        "timestamp": "2024-01-15T10:30:00Z"
    }

@app.post("/coach/strategy")
async def mock_coach_strategy(request: CoachStrategyRequest):
    """Mock Trading Coach strategy endpoint"""
    return {
        "strategies": [
            {
                "name": f"Conservative {request.asset} Strategy",
                "description": f"A conservative approach to {request.asset} investing",
                "risk_level": "low",
                "expected_return": "5-8%",
                "time_horizon": "long-term"
            },
            {
                "name": f"Moderate {request.asset} Strategy", 
                "description": f"A balanced approach to {request.asset} investing",
                "risk_level": "medium",
                "expected_return": "8-12%",
                "time_horizon": "medium-term"
            }
        ],
        "asset": request.asset,
        "risk_tolerance": request.risk_tolerance,
        "goals": request.goals,
        "timestamp": "2024-01-15T10:30:00Z"
    }

@app.post("/tutor/module")
async def mock_tutor_module(request: TutorModuleRequest):
    """Mock Dynamic Content module endpoint"""
    return {
        "content": f"Mock educational module about {request.topic}. This comprehensive module covers all the essential concepts, provides practical examples, and includes interactive elements to enhance learning.",
        "topic": request.topic,
        "difficulty": "intermediate",
        "estimated_time": "15 minutes",
        "sections": [
            "Introduction",
            "Key Concepts", 
            "Practical Examples",
            "Summary"
        ],
        "timestamp": "2024-01-15T10:30:00Z"
    }

@app.post("/tutor/market-commentary")
async def mock_market_commentary(request: MarketCommentaryRequest):
    """Mock Market Commentary endpoint"""
    return {
        "commentary": f"Mock {request.tone} market commentary for {request.horizon} horizon. The markets are showing mixed signals with technology stocks leading gains while energy sectors face headwinds. Investors should remain cautious but optimistic about long-term prospects.",
        "horizon": request.horizon,
        "tone": request.tone,
        "key_points": [
            "Technology stocks performing well",
            "Energy sector under pressure", 
            "Mixed economic indicators",
            "Long-term outlook remains positive"
        ],
        "timestamp": "2024-01-15T10:30:00Z"
    }

if __name__ == "__main__":
    print("🚀 Starting RichesReach Test Server...")
    print("📡 Server will be available at: http://127.0.0.1:8000")
    print("📚 API docs will be available at: http://127.0.0.1:8000/docs")
    print("🧪 This is a mock server for testing - no real AI services")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )
