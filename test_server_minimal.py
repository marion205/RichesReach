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
import time
from typing import Optional, Dict, Any, List

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

class RegimeAdaptiveQuizRequest(BaseModel):
    user_id: str
    market_data: dict = None
    difficulty: str = "beginner"
    num_questions: int = 3

class DailyDigestRequest(BaseModel):
    user_id: str
    market_data: dict = None
    preferred_time: str = None

class RegimeAlertRequest(BaseModel):
    user_id: str
    regime_change: dict
    urgency: str = "medium"

class DailyMissionRequest(BaseModel):
    user_id: str
    day_number: int
    market_data: dict = None

class RecoveryRitualRequest(BaseModel):
    user_id: str
    missed_day: int

class NotificationPreferencesRequest(BaseModel):
    user_id: str
    daily_digest_enabled: bool = True
    daily_digest_time: str = "08:00"
    regime_alerts_enabled: bool = True
    regime_alert_urgency: str = "medium"
    mission_reminders_enabled: bool = True
    mission_reminder_time: str = "19:00"
    streak_alerts_enabled: bool = True
    achievement_notifications_enabled: bool = True
    recovery_ritual_enabled: bool = True
    quiet_hours_enabled: bool = False
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "07:00"

class RegimeMonitoringRequest(BaseModel):
    user_id: str
    market_data: Optional[Dict[str, Any]] = None

# =============================================================================
# Phase 2: Community Features Models
# =============================================================================

class CreateWealthCircleRequest(BaseModel):
    name: str
    description: str
    focus_area: str
    creator_id: str
    is_private: bool = False
    cultural_focus: Optional[str] = None

class CreateDiscussionPostRequest(BaseModel):
    circle_id: str
    user_id: str
    title: str
    content: str
    post_type: str
    visibility: str = "public"
    is_anonymous: bool = False
    tags: Optional[List[str]] = None

class ShareProgressRequest(BaseModel):
    user_id: str
    progress_type: str
    title: str
    description: str
    value: float
    unit: str
    sharing_level: str = "anonymous"
    community_id: Optional[str] = None
    tags: Optional[List[str]] = None

class CreateChallengeRequest(BaseModel):
    title: str
    description: str
    challenge_type: str
    start_date: str
    end_date: str
    creator_id: str
    entry_fee: float = 0.0
    max_participants: int = 100

class MakePredictionRequest(BaseModel):
    challenge_id: str
    user_id: str
    prediction_type: str
    asset: str
    predicted_value: float
    confidence: float
    reasoning: str

# =============================================================================
# Phase 3: Advanced Personalization Models
# =============================================================================

class TrackBehaviorRequest(BaseModel):
    user_id: str
    behavior_type: str
    session_id: Optional[str] = None
    duration: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None

class AdaptContentRequest(BaseModel):
    user_id: str
    content_type: str
    original_content: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    adaptation_types: Optional[List[str]] = None

class GeneratePersonalizedContentRequest(BaseModel):
    user_id: str
    content_type: str
    topic: str
    length_preference: Optional[str] = None
    difficulty_level: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

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
    if request.email.lower() == "test@example.com" and request.password == "testpass123":
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

@app.post("/api/auth/login/")
async def mock_auth_api(request: LoginRequest):
    """Mock authentication endpoint for mobile app compatibility"""
    # Accept demo credentials that the mobile app is using
    if (request.email.lower() == "demo@example.com" and request.password == "demo123") or \
       (request.email.lower() == "test@example.com" and request.password == "testpass123"):
        return {
            "access_token": "mock_token_12345",
            "user": {
                "id": "demo-user-123",
                "email": request.email,
                "name": "Demo User"
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

@app.post("/tutor/quiz/regime-adaptive")
async def mock_regime_adaptive_quiz(request: RegimeAdaptiveQuizRequest):
    """Mock Regime-Adaptive Quiz endpoint - the key differentiator!"""
    # Simulate different market regimes
    regimes = [
        "early_bull_market",
        "late_bull_market", 
        "bear_market",
        "sideways_consolidation",
        "high_volatility"
    ]
    
    # Mock regime detection (in real app, this would use ML models)
    import random
    current_regime = random.choice(regimes)
    regime_confidence = round(random.uniform(0.7, 0.95), 2)
    
    regime_context = {
        "current_regime": current_regime,
        "regime_confidence": regime_confidence,
        "regime_description": f"Market is in {current_regime.replace('_', ' ')} phase",
        "relevant_strategies": [
            "Risk management",
            "Position sizing", 
            "Market timing"
        ],
        "common_mistakes": [
            "Emotional trading",
            "Poor risk management",
            "Ignoring market conditions"
        ]
    }
    
    return {
        "questions": [
            {
                "id": "q1",
                "question": f"In a {current_regime.replace('_', ' ')} market, what is the most important consideration?",
                "options": [
                    "Maximize returns at all costs",
                    "Manage risk appropriately", 
                    "Follow the crowd",
                    "Ignore market conditions"
                ],
                "correct_answer": "Manage risk appropriately",
                "explanation": f"In {current_regime.replace('_', ' ')} markets, risk management is crucial for capital preservation and long-term success.",
                "hints": ["Think about what changes in different market conditions", "Consider the importance of capital preservation"]
            },
            {
                "id": "q2",
                "question": f"Which strategy is most effective during {current_regime.replace('_', ' ')}?",
                "options": [
                    "Buy and hold everything",
                    "Active trading with tight stops",
                    "Dollar-cost averaging",
                    "Market timing"
                ],
                "correct_answer": "Dollar-cost averaging",
                "explanation": f"Dollar-cost averaging helps reduce the impact of volatility in {current_regime.replace('_', ' ')} markets.",
                "hints": ["Consider strategies that work in volatile conditions", "Think about reducing timing risk"]
            }
        ],
        "topic": f"Market Regime: {current_regime.replace('_', ' ').title()}",
        "difficulty": request.difficulty,
        "generated_at": "2024-01-15T10:30:00Z",
        "regime_context": regime_context
    }

@app.post("/digest/daily")
async def mock_daily_digest(request: DailyDigestRequest):
    """Mock Daily Voice Digest endpoint - Phase 1 key feature!"""
    import random
    from datetime import datetime, timezone, timedelta
    
    # Simulate different market regimes
    regimes = [
        "early_bull_market",
        "late_bull_market", 
        "bear_market",
        "sideways_consolidation",
        "high_volatility"
    ]
    
    current_regime = random.choice(regimes)
    regime_confidence = round(random.uniform(0.75, 0.95), 2)
    
    regime_context = {
        "current_regime": current_regime,
        "regime_confidence": regime_confidence,
        "regime_description": f"Market is in {current_regime.replace('_', ' ')} phase with moderate volatility",
        "relevant_strategies": [
            "Risk management",
            "Position sizing", 
            "Market timing"
        ],
        "common_mistakes": [
            "Emotional trading",
            "Poor risk management",
            "Ignoring market conditions"
        ]
    }
    
    # Generate regime-specific voice script
    voice_scripts = {
        "early_bull_market": "Good morning! Today's market is in early bull phase with 85% confidence. [HAPTIC: gentle] Here's what you need to know: Growth stocks are showing strong momentum, and the trend is your friend. [HAPTIC: strong] Focus on quality companies with strong fundamentals. Remember, even in bull markets, risk management is crucial.",
        "late_bull_market": "Good morning! Today's market is in late bull phase with 78% confidence. [HAPTIC: gentle] Here's what you need to know: Valuations are getting stretched, and volatility is increasing. [HAPTIC: strong] Consider taking some profits and rebalancing your portfolio. This is not the time to chase momentum.",
        "bear_market": "Good morning! Today's market is in bear phase with 82% confidence. [HAPTIC: gentle] Here's what you need to know: Market sentiment is negative, and defensive positioning is key. [HAPTIC: strong] Focus on capital preservation and consider dollar-cost averaging into quality stocks.",
        "sideways_consolidation": "Good morning! Today's market is in sideways consolidation with 70% confidence. [HAPTIC: gentle] Here's what you need to know: Range-bound trading is likely, and patience is key. [HAPTIC: strong] Consider options strategies and focus on dividend-paying stocks.",
        "high_volatility": "Good morning! Today's market shows high volatility with 88% confidence. [HAPTIC: gentle] Here's what you need to know: Expect sharp moves in both directions. [HAPTIC: strong] Reduce position sizes and focus on risk management above all else."
    }
    
    voice_script = voice_scripts.get(current_regime, voice_scripts["sideways_consolidation"])
    
    # Generate key insights based on regime
    insights = {
        "early_bull_market": [
            "Growth stocks are leading the market higher",
            "Momentum indicators are bullish",
            "Risk-on sentiment is driving flows"
        ],
        "late_bull_market": [
            "Valuations are approaching historical highs",
            "Volatility is increasing as uncertainty grows",
            "Defensive sectors are starting to outperform"
        ],
        "bear_market": [
            "Selling pressure is overwhelming buying interest",
            "Defensive positioning is crucial",
            "Quality stocks are being sold indiscriminately"
        ],
        "sideways_consolidation": [
            "Market is range-bound with no clear direction",
            "Volatility is compressed",
            "Breakout potential is building"
        ],
        "high_volatility": [
            "Sharp intraday moves are common",
            "Risk management is paramount",
            "Opportunities exist for nimble traders"
        ]
    }
    
    # Generate actionable tips
    tips = {
        "early_bull_market": [
            "Consider adding growth exposure to your portfolio",
            "Watch for pullbacks as buying opportunities"
        ],
        "late_bull_market": [
            "Take some profits on extended positions",
            "Rebalance towards more defensive assets"
        ],
        "bear_market": [
            "Focus on capital preservation",
            "Consider dollar-cost averaging into quality"
        ],
        "sideways_consolidation": [
            "Use range-bound strategies",
            "Be patient and wait for clear direction"
        ],
        "high_volatility": [
            "Reduce position sizes",
            "Use stop-losses religiously"
        ]
    }
    
    # Schedule for tomorrow 8 AM
    tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
    scheduled_time = tomorrow.replace(hour=8, minute=0, second=0, microsecond=0).isoformat()
    
    return {
        "digest_id": f"digest_{random.randint(1000, 9999)}",
        "user_id": request.user_id,
        "regime_context": regime_context,
        "voice_script": voice_script,
        "key_insights": insights.get(current_regime, insights["sideways_consolidation"]),
        "actionable_tips": tips.get(current_regime, tips["sideways_consolidation"]),
        "pro_teaser": "Pro members get real-time regime alerts and advanced strategy recommendations. Upgrade now for 50% off!",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scheduled_for": scheduled_time
    }

@app.post("/digest/regime-alert")
async def mock_regime_alert(request: RegimeAlertRequest):
    """Mock Regime Alert endpoint - Real-time notifications!"""
    import random
    from datetime import datetime, timezone
    
    old_regime = request.regime_change.get("old_regime", "sideways_consolidation")
    new_regime = request.regime_change.get("new_regime", "early_bull_market")
    confidence = request.regime_change.get("confidence", 0.85)
    urgency = request.urgency
    
    # Create urgency-based alert
    if urgency == "high":
        title = "🚨 URGENT: Market Regime Alert"
        body = f"CRITICAL: Market shifted from {old_regime.replace('_', ' ')} to {new_regime.replace('_', ' ')}. Confidence: {confidence:.0%}. Immediate action recommended."
    elif urgency == "medium":
        title = "⚠️ Market Regime Alert"
        body = f"Market shifted from {old_regime.replace('_', ' ')} to {new_regime.replace('_', ' ')}. Confidence: {confidence:.0%}. Review your strategy."
    else:
        title = "📊 Market Regime Update"
        body = f"Market regime changed from {old_regime.replace('_', ' ')} to {new_regime.replace('_', ' ')}. Confidence: {confidence:.0%}."
    
    return {
        "notification_id": f"alert_{random.randint(1000, 9999)}",
        "user_id": request.user_id,
        "title": title,
        "body": body,
        "data": {
            "type": "regime_alert",
            "old_regime": old_regime,
            "new_regime": new_regime,
            "confidence": confidence,
            "urgency": urgency
        },
        "scheduled_for": datetime.now(timezone.utc).isoformat(),
        "type": "regime_alert"
    }

@app.get("/missions/progress/{user_id}")
async def mock_user_progress(user_id: str, include_current_mission: bool = True):
    """Mock User Progress endpoint - Gamification system!"""
    import random
    from datetime import datetime, timezone
    
    # Mock progress data
    current_streak = random.randint(0, 15)
    longest_streak = max(current_streak, random.randint(5, 21))
    total_completed = random.randint(10, 50)
    streak_multiplier = 1.0 + (current_streak * 0.1)
    
    # Generate achievements
    achievements = []
    if current_streak >= 7:
        achievements.append({
            "id": "week_streak",
            "name": "Week Warrior",
            "description": "Maintained a 7-day streak",
            "icon": "🔥",
            "unlocked_at": datetime.now(timezone.utc).isoformat()
        })
    if current_streak >= 21:
        achievements.append({
            "id": "habit_hero",
            "name": "Habit Hero",
            "description": "Completed the full 21-day habit loop",
            "icon": "🏆",
            "unlocked_at": datetime.now(timezone.utc).isoformat()
        })
    if total_completed >= 50:
        achievements.append({
            "id": "dedication",
            "name": "Dedication Master",
            "description": "Completed 50+ missions",
            "icon": "💎",
            "unlocked_at": datetime.now(timezone.utc).isoformat()
        })
    
    # Generate current mission if streak is active
    current_mission = None
    if include_current_mission and current_streak > 0 and current_streak < 21:
        current_mission = {
            "mission_id": f"mission_{random.randint(1000, 9999)}",
            "user_id": user_id,
            "day_number": current_streak + 1,
            "mission_type": "quiz" if current_streak <= 7 else "analysis" if current_streak <= 14 else "simulation",
            "title": f"Day {current_streak + 1}: Momentum Mission",
            "description": f"Complete your Day {current_streak + 1} challenge to maintain your streak!",
            "difficulty": "beginner" if current_streak <= 7 else "intermediate" if current_streak <= 14 else "advanced",
            "estimated_duration": 5,
            "content": {
                "challenge": f"Apply your knowledge to Day {current_streak + 1} concepts",
                "instructions": "Think through the challenge step by step",
                "learning_objectives": ["Market analysis", "Risk management", "Strategy application"],
                "regime_context": "This challenge adapts to current market conditions",
                "success_criteria": "Complete the challenge with thoughtful analysis"
            },
            "rewards": {
                "points": 10 + (current_streak * 2),
                "badges": ["momentum_maker"] if current_streak % 5 == 0 else [],
                "streak_bonus": (current_streak + 1) * 2,
                "experience": (10 + (current_streak * 2)) * 2
            },
            "streak_multiplier": streak_multiplier,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "due_at": (datetime.now(timezone.utc).replace(hour=23, minute=59, second=59)).isoformat()
        }
    
    # Generate recovery ritual if streak is broken
    available_recovery = None
    if current_streak == 0:
        available_recovery = {
            "ritual_id": f"recovery_{random.randint(1000, 9999)}",
            "user_id": user_id,
            "missed_day": 1,
            "ritual_type": "recovery",
            "title": "Recovery Ritual: Quick Win",
            "description": "A simple challenge to get back on track",
            "content": {
                "challenge": "Review one key financial concept",
                "encouragement": "Every expert was once a beginner. You've got this!",
                "next_steps": "Complete this quick challenge to rebuild your momentum"
            },
            "streak_recovery": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    
    return {
        "user_id": user_id,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "total_missions_completed": total_completed,
        "current_mission": current_mission,
        "available_recovery": available_recovery,
        "achievements": achievements,
        "streak_multiplier": streak_multiplier,
        "last_activity": datetime.now(timezone.utc).isoformat()
    }

@app.post("/missions/daily")
async def mock_daily_mission(request: DailyMissionRequest):
    """Mock Daily Mission endpoint - Progressive challenges!"""
    import random
    from datetime import datetime, timezone, timedelta
    
    day_number = request.day_number
    user_id = request.user_id
    
    # Determine mission type and difficulty based on day
    if day_number <= 7:
        mission_type = "quiz"
        difficulty = "beginner"
    elif day_number <= 14:
        mission_type = "analysis"
        difficulty = "intermediate"
    elif day_number <= 21:
        mission_type = "simulation"
        difficulty = "advanced"
    else:
        mission_type = "practice"
        difficulty = "expert"
    
    # Generate mission content
    mission_titles = {
        "quiz": f"Day {day_number}: Knowledge Check",
        "analysis": f"Day {day_number}: Market Analysis",
        "simulation": f"Day {day_number}: Strategy Simulation",
        "practice": f"Day {day_number}: Advanced Practice"
    }
    
    mission_descriptions = {
        "quiz": f"Test your knowledge with Day {day_number} concepts",
        "analysis": f"Analyze market conditions for Day {day_number}",
        "simulation": f"Simulate trading strategies for Day {day_number}",
        "practice": f"Practice advanced techniques for Day {day_number}"
    }
    
    # Calculate rewards
    base_points = 10
    difficulty_multiplier = {"beginner": 1.0, "intermediate": 1.5, "advanced": 2.0, "expert": 2.5}
    points = int(base_points * difficulty_multiplier[difficulty] * (1 + day_number * 0.1))
    
    # Generate badges
    badges = []
    if day_number == 1:
        badges.append("first_step")
    elif day_number == 7:
        badges.append("week_warrior")
    elif day_number == 14:
        badges.append("momentum_master")
    elif day_number == 21:
        badges.append("habit_hero")
    elif day_number % 5 == 0:
        badges.append("milestone_maker")
    
    # Calculate streak multiplier
    streak_multiplier = 1.0 + (day_number * 0.1)
    
    # Set due time (tomorrow at 11:59 PM)
    due_time = datetime.now(timezone.utc) + timedelta(days=1)
    due_time = due_time.replace(hour=23, minute=59, second=59)
    
    return {
        "mission_id": f"mission_{random.randint(1000, 9999)}",
        "user_id": user_id,
        "day_number": day_number,
        "mission_type": mission_type,
        "title": mission_titles[mission_type],
        "description": mission_descriptions[mission_type],
        "difficulty": difficulty,
        "estimated_duration": 5,
        "content": {
            "challenge": f"Complete your Day {day_number} {mission_type} challenge",
            "instructions": "Follow the step-by-step guidance to complete this mission",
            "learning_objectives": ["Market analysis", "Risk management", "Strategy application"],
            "regime_context": "This mission adapts to current market conditions",
            "success_criteria": "Complete the challenge with thoughtful analysis and learning"
        },
        "rewards": {
            "points": points,
            "badges": badges,
            "streak_bonus": day_number * 2,
            "experience": points * 2
        },
        "streak_multiplier": streak_multiplier,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "due_at": due_time.isoformat()
    }

@app.post("/missions/recovery")
async def mock_recovery_ritual(request: RecoveryRitualRequest):
    """Mock Recovery Ritual endpoint - Get back on track!"""
    import random
    from datetime import datetime, timezone
    
    missed_day = request.missed_day
    user_id = request.user_id
    
    # Generate encouraging recovery content
    recovery_titles = [
        "Recovery Ritual: Quick Win",
        "Recovery Ritual: Momentum Builder",
        "Recovery Ritual: Confidence Boost",
        "Recovery Ritual: Fresh Start"
    ]
    
    recovery_challenges = [
        "Review one key financial concept",
        "Complete a quick knowledge check",
        "Analyze a simple market scenario",
        "Practice a basic trading concept"
    ]
    
    encouragements = [
        "Every expert was once a beginner. You've got this!",
        "Momentum is built one step at a time. Let's get back on track!",
        "Consistency beats perfection. You're doing great!",
        "Every day is a new opportunity to learn and grow!"
    ]
    
    next_steps = [
        "Complete this quick challenge to rebuild your momentum",
        "Use this as a stepping stone to restart your streak",
        "Take this opportunity to refresh your knowledge",
        "Let this be the foundation for your next streak"
    ]
    
    return {
        "ritual_id": f"recovery_{random.randint(1000, 9999)}",
        "user_id": user_id,
        "missed_day": missed_day,
        "ritual_type": "recovery",
        "title": random.choice(recovery_titles),
        "description": "A simple challenge to get back on track",
        "content": {
            "challenge": random.choice(recovery_challenges),
            "encouragement": random.choice(encouragements),
            "next_steps": random.choice(next_steps)
        },
        "streak_recovery": True,
        "created_at": datetime.now(timezone.utc).isoformat()
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

# =============================================================================
# Enhanced Phase 1 Features - Notifications & Monitoring
# =============================================================================

@app.post("/notifications/preferences")
async def update_notification_preferences(request: NotificationPreferencesRequest):
    """Update user notification preferences."""
    return {
        "user_id": request.user_id,
        "preferences": {
            "daily_digest_enabled": request.daily_digest_enabled,
            "daily_digest_time": request.daily_digest_time,
            "regime_alerts_enabled": request.regime_alerts_enabled,
            "regime_alert_urgency": request.regime_alert_urgency,
            "mission_reminders_enabled": request.mission_reminders_enabled,
            "mission_reminder_time": request.mission_reminder_time,
            "streak_alerts_enabled": request.streak_alerts_enabled,
            "achievement_notifications_enabled": request.achievement_notifications_enabled,
            "recovery_ritual_enabled": request.recovery_ritual_enabled,
            "quiet_hours_enabled": request.quiet_hours_enabled,
            "quiet_hours_start": request.quiet_hours_start,
            "quiet_hours_end": request.quiet_hours_end
        },
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

@app.get("/notifications/preferences/{user_id}")
async def get_notification_preferences(user_id: str):
    """Get user notification preferences."""
    return {
        "user_id": user_id,
        "preferences": {
            "daily_digest_enabled": True,
            "daily_digest_time": "08:00",
            "regime_alerts_enabled": True,
            "regime_alert_urgency": "medium",
            "mission_reminders_enabled": True,
            "mission_reminder_time": "19:00",
            "streak_alerts_enabled": True,
            "achievement_notifications_enabled": True,
            "recovery_ritual_enabled": True,
            "quiet_hours_enabled": False,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "07:00"
        }
    }

@app.get("/notifications/recent/{user_id}")
async def get_recent_notifications(user_id: str):
    """Get recent notifications for a user."""
    return {
        "user_id": user_id,
        "notifications": [
            {
                "id": "1",
                "type": "regime_alert",
                "title": "📊 Market Regime Alert",
                "body": "Market shifted from sideways consolidation to early bull market. Confidence: 85%.",
                "timestamp": "2024-01-15T10:30:00Z",
                "read": False,
                "priority": "medium"
            },
            {
                "id": "2",
                "type": "daily_digest",
                "title": "🎙️ Your Daily Market Briefing",
                "body": "Your personalized 60-second market digest is ready! Tap to listen.",
                "timestamp": "2024-01-15T08:00:00Z",
                "read": True,
                "priority": "normal"
            },
            {
                "id": "3",
                "type": "mission_reminder",
                "title": "🎯 Day 5 Mission Ready",
                "body": "Your daily momentum mission is waiting! Take 5 minutes to complete it.",
                "timestamp": "2024-01-14T19:00:00Z",
                "read": True,
                "priority": "normal"
            }
        ]
    }

@app.post("/monitoring/regime-check")
async def check_regime_change(request: RegimeMonitoringRequest):
    """Check for regime changes based on market data."""
    return {
        "regime_change_detected": True,
        "old_regime": "sideways_consolidation",
        "new_regime": "early_bull_market",
        "confidence": 0.85,
        "severity": "moderate",
        "change_factors": [
            "High volatility (VIX > 25)",
            "Strong technology sector performance",
            "High trading volume"
        ],
        "impact_assessment": {
            "risk_level": "medium",
            "opportunity_level": "high",
            "expected_duration": "medium-term"
        },
        "recommended_actions": [
            "Review and rebalance portfolio",
            "Consider adjusting risk management parameters",
            "Monitor market conditions closely"
        ],
        "timestamp": "2024-01-15T10:30:00Z"
    }

@app.get("/monitoring/status")
async def get_monitoring_status():
    """Get real-time monitoring service status."""
    return {
        "service_id": "regime_monitor_001",
        "status": "active",
        "uptime_seconds": 86400,  # 24 hours
        "total_events_detected": 15,
        "events_last_hour": 2,
        "average_confidence": 0.82,
        "false_positive_rate": 0.05,
        "last_regime_change": "2024-01-15T10:30:00Z",
        "active_monitors": 1,
        "error_count": 0,
        "last_error": None
    }

# =============================================================================
# Phase 2: Community Features Endpoints
# =============================================================================

@app.post("/community/wealth-circles")
async def create_wealth_circle(request: CreateWealthCircleRequest):
    """Create a new wealth circle community."""
    return {
        "circle_id": f"circle_{request.creator_id}_{int(time.time())}",
        "name": request.name,
        "description": request.description,
        "focus_area": request.focus_area,
        "member_count": 1,
        "created_at": "2024-01-15T10:30:00Z",
        "is_private": request.is_private,
        "cultural_focus": request.cultural_focus,
        "rules": [
            "Be respectful and supportive of all members",
            "Share knowledge and experiences to help others",
            "Maintain confidentiality and respect privacy",
            "Focus on financial education and empowerment"
        ],
        "moderators": [request.creator_id]
    }

@app.get("/community/wealth-circles")
async def get_wealth_circles():
    """Get all wealth circles."""
    return {
        "circles": [
            {
                "circle_id": "circle_001",
                "name": "BIPOC Investment Strategies",
                "description": "Sharing investment strategies and experiences within our community",
                "focus_area": "investment_strategy",
                "member_count": 1247,
                "cultural_focus": "BIPOC",
                "is_private": False,
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "circle_id": "circle_002",
                "name": "First-Gen Wealth Builders",
                "description": "Supporting first-generation wealth builders on their journey",
                "focus_area": "family_finances",
                "member_count": 892,
                "cultural_focus": "First Generation",
                "is_private": False,
                "created_at": "2024-01-05T00:00:00Z"
            },
            {
                "circle_id": "circle_003",
                "name": "Tech Career & Finance",
                "description": "Navigating tech careers while building wealth",
                "focus_area": "career_advice",
                "member_count": 634,
                "cultural_focus": "Tech Professionals",
                "is_private": False,
                "created_at": "2024-01-10T00:00:00Z"
            }
        ]
    }

@app.post("/community/discussion-posts")
async def create_discussion_post(request: CreateDiscussionPostRequest):
    """Create a new discussion post in a wealth circle."""
    return {
        "post_id": f"post_{request.user_id}_{int(time.time())}",
        "circle_id": request.circle_id,
        "user_id": request.user_id if not request.is_anonymous else "anonymous",
        "title": request.title,
        "content": request.content,
        "post_type": request.post_type,
        "visibility": request.visibility,
        "is_anonymous": request.is_anonymous,
        "tags": request.tags or [],
        "likes": 0,
        "replies": 0,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
        "moderation_status": "approved"
    }

@app.get("/community/discussion-posts/{circle_id}")
async def get_discussion_posts(circle_id: str):
    """Get discussion posts for a wealth circle."""
    return {
        "posts": [
            {
                "post_id": "post_001",
                "title": "Just hit my first $10K savings goal!",
                "content": "After 6 months of disciplined saving, I finally reached my first major milestone. The key was automating my savings and cutting unnecessary expenses.",
                "author": "Anonymous",
                "likes": 23,
                "replies": 8,
                "created_at": "2024-01-15T14:30:00Z",
                "is_anonymous": True
            },
            {
                "post_id": "post_002",
                "title": "Real estate investment advice needed",
                "content": "Looking to buy my first rental property. Any advice on getting started with real estate investing?",
                "author": "Anonymous",
                "likes": 15,
                "replies": 12,
                "created_at": "2024-01-15T12:15:00Z",
                "is_anonymous": True
            }
        ]
    }

@app.post("/community/progress/share")
async def share_progress(request: ShareProgressRequest):
    """Share progress with the community."""
    return {
        "update_id": f"progress_{request.user_id}_{int(time.time())}",
        "user_id": request.user_id,
        "progress_type": request.progress_type,
        "title": request.title,
        "description": request.description,
        "value": request.value,
        "unit": request.unit,
        "sharing_level": request.sharing_level,
        "is_anonymous": request.sharing_level in ["anonymous", "community"],
        "created_at": "2024-01-15T10:30:00Z",
        "community_id": request.community_id,
        "tags": request.tags or [],
        "milestone": "First $1K Saved!" if request.value >= 1000 else None
    }

@app.get("/community/progress/stats/{community_id}")
async def get_community_stats(community_id: str):
    """Get community progress statistics."""
    return {
        "community_id": community_id,
        "total_members": 1247,
        "active_this_week": 89,
        "total_progress_updates": 156,
        "average_streak": 12.3,
        "top_achievements": [
            {
                "title": "30-Day Learning Streak",
                "count": 23,
                "icon": "🔥"
            },
            {
                "title": "First $1K Saved",
                "count": 18,
                "icon": "💰"
            },
            {
                "title": "Debt-Free Journey Started",
                "count": 15,
                "icon": "🎯"
            }
        ],
        "recent_milestones": [
            {
                "title": "Someone just hit a 50-day learning streak!",
                "timestamp": "2024-01-15T14:30:00Z",
                "icon": "🔥"
            },
            {
                "title": "Community member reached $10K savings goal!",
                "timestamp": "2024-01-15T12:15:00Z",
                "icon": "💰"
            }
        ],
        "generated_at": "2024-01-15T10:30:00Z"
    }

@app.post("/community/challenges")
async def create_challenge(request: CreateChallengeRequest):
    """Create a new trading challenge."""
    return {
        "challenge_id": f"challenge_{request.creator_id}_{int(time.time())}",
        "title": request.title,
        "description": request.description,
        "challenge_type": request.challenge_type,
        "status": "upcoming",
        "start_date": request.start_date,
        "end_date": request.end_date,
        "entry_fee": request.entry_fee,
        "prize_pool": request.entry_fee * request.max_participants * 0.8,
        "max_participants": request.max_participants,
        "current_participants": 0,
        "rules": [
            "Follow community guidelines",
            "Respect other participants",
            "Have fun and learn!"
        ],
        "created_by": request.creator_id,
        "created_at": "2024-01-15T10:30:00Z"
    }

@app.get("/community/challenges")
async def get_active_challenges():
    """Get active trading challenges."""
    return {
        "challenges": [
            {
                "challenge_id": "challenge_001",
                "title": "Daily AAPL Prediction",
                "description": "Predict Apple's closing price today!",
                "challenge_type": "daily_prediction",
                "status": "active",
                "start_date": "2024-01-15T09:30:00Z",
                "end_date": "2024-01-15T16:00:00Z",
                "entry_fee": 10.0,
                "prize_pool": 800.0,
                "max_participants": 100,
                "current_participants": 67
            },
            {
                "challenge_id": "challenge_002",
                "title": "Weekly Market Direction",
                "description": "Predict if S&P 500 will be up or down this week!",
                "challenge_type": "weekly_competition",
                "status": "active",
                "start_date": "2024-01-15T09:30:00Z",
                "end_date": "2024-01-19T16:00:00Z",
                "entry_fee": 25.0,
                "prize_pool": 2000.0,
                "max_participants": 100,
                "current_participants": 43
            }
        ]
    }

@app.post("/community/challenges/{challenge_id}/predictions")
async def make_prediction(challenge_id: str, request: MakePredictionRequest):
    """Make a prediction in a trading challenge."""
    return {
        "prediction_id": f"prediction_{request.user_id}_{int(time.time())}",
        "challenge_id": challenge_id,
        "user_id": request.user_id,
        "prediction_type": request.prediction_type,
        "asset": request.asset,
        "predicted_value": request.predicted_value,
        "confidence": request.confidence,
        "reasoning": request.reasoning,
        "created_at": "2024-01-15T10:30:00Z",
        "result": None
    }

@app.get("/community/challenges/{challenge_id}/leaderboard")
async def get_challenge_leaderboard(challenge_id: str):
    """Get challenge leaderboard."""
    return {
        "challenge_id": challenge_id,
        "leaderboard": [
            {
                "user_id": "user_001",
                "username": "Trader001",
                "score": 95.5,
                "rank": 1,
                "total_predictions": 10,
                "correct_predictions": 9,
                "accuracy": 0.9,
                "total_winnings": 400.0,
                "is_anonymous": False
            },
            {
                "user_id": "user_015",
                "username": "Anonymous",
                "score": 92.3,
                "rank": 2,
                "total_predictions": 8,
                "correct_predictions": 7,
                "accuracy": 0.875,
                "total_winnings": 200.0,
                "is_anonymous": True
            },
            {
                "user_id": "user_042",
                "username": "Anonymous",
                "score": 89.7,
                "rank": 3,
                "total_predictions": 12,
                "correct_predictions": 10,
                "accuracy": 0.833,
                "total_winnings": 100.0,
                "is_anonymous": True
            }
        ]
    }

# =============================================================================
# Phase 3: Advanced Personalization Endpoints
# =============================================================================

@app.post("/personalization/behavior/track")
async def track_behavior(request: TrackBehaviorRequest):
    """Track user behavior for analytics."""
    return {
        "behavior_id": f"behavior_{request.user_id}_{int(time.time())}",
        "user_id": request.user_id,
        "behavior_type": request.behavior_type,
        "timestamp": "2024-01-15T10:30:00Z",
        "session_id": request.session_id or f"session_{request.user_id}_{int(time.time())}",
        "duration": request.duration,
        "metadata": request.metadata or {},
        "context": request.context or {}
    }

@app.get("/personalization/engagement-profile/{user_id}")
async def get_engagement_profile(user_id: str):
    """Get user engagement profile."""
    return {
        "user_id": user_id,
        "engagement_level": "high",
        "engagement_score": 0.85,
        "preferred_content_types": ["learning", "trading", "community"],
        "optimal_session_duration": 25.0,
        "best_engagement_times": ["09:00", "19:00"],
        "learning_style": "visual",
        "interaction_preferences": {
            "notifications": True,
            "community": True,
            "gamification": True
        },
        "last_updated": "2024-01-15T10:30:00Z"
    }

@app.get("/personalization/churn-prediction/{user_id}")
async def get_churn_prediction(user_id: str):
    """Get churn risk prediction."""
    return {
        "user_id": user_id,
        "churn_risk": "low",
        "churn_probability": 0.15,
        "risk_factors": [],
        "intervention_recommendations": ["Continue current engagement"],
        "predicted_churn_date": None,
        "confidence": 0.85,
        "generated_at": "2024-01-15T10:30:00Z"
    }

@app.get("/personalization/behavior-patterns/{user_id}")
async def get_behavior_patterns(user_id: str):
    """Get identified behavior patterns."""
    return {
        "patterns": [
            {
                "pattern_id": "pattern_001",
                "user_id": user_id,
                "pattern_type": "usage_timing",
                "frequency": 0.8,
                "confidence": 0.9,
                "description": "User typically engages in morning learning sessions",
                "triggers": ["morning_time", "weekday"],
                "predicted_actions": ["morning_notification", "morning_content"],
                "created_at": "2024-01-15T10:30:00Z"
            },
            {
                "pattern_id": "pattern_002",
                "user_id": user_id,
                "pattern_type": "content_preference",
                "frequency": 0.7,
                "confidence": 0.85,
                "description": "User prefers visual learning with interactive elements",
                "triggers": ["visual_content", "interactive_elements"],
                "predicted_actions": ["visual_content_priority", "interactive_enhancement"],
                "created_at": "2024-01-15T10:30:00Z"
            }
        ]
    }

@app.post("/personalization/content/adapt")
async def adapt_content(request: AdaptContentRequest):
    """Adapt content for user personalization."""
    return {
        "adaptation_id": f"adaptation_{request.user_id}_{int(time.time())}",
        "user_id": request.user_id,
        "original_content": request.original_content,
        "adapted_content": {
            **request.original_content,
            "personalized": True,
            "adaptation_notes": "Content adapted for visual learner with high engagement"
        },
        "adaptation_type": "comprehensive",
        "adaptation_reason": "Personalized for visual learner",
        "confidence": 0.85,
        "performance_prediction": "high",
        "created_at": "2024-01-15T10:30:00Z"
    }

@app.post("/personalization/content/generate")
async def generate_personalized_content(request: GeneratePersonalizedContentRequest):
    """Generate personalized content."""
    return {
        "content_id": f"content_{request.user_id}_{int(time.time())}",
        "user_id": request.user_id,
        "content_type": request.content_type,
        "title": f"Personalized {request.content_type}: {request.topic}",
        "content": f"This is personalized {request.content_type} content about {request.topic}, tailored to your learning preferences and engagement patterns.",
        "metadata": {
            "difficulty": request.difficulty_level or "intermediate",
            "length": request.length_preference or "medium",
            "style": "visual",
            "personalized": True
        },
        "personalization_factors": [
            "learning_style_visual",
            "engagement_level_high",
            "optimal_duration_25min"
        ],
        "adaptation_score": 0.85,
        "created_at": "2024-01-15T10:30:00Z"
    }

@app.get("/personalization/recommendations/{user_id}")
async def get_content_recommendations(user_id: str):
    """Get personalized content recommendations."""
    return {
        "recommendations": [
            {
                "recommendation_id": "rec_001",
                "user_id": user_id,
                "content_type": "learning_module",
                "title": "Advanced Options Strategies",
                "description": "Perfect for your visual learning style and current skill level",
                "relevance_score": 0.92,
                "confidence": 0.88,
                "reasoning": "Matches your learning patterns and interests",
                "created_at": "2024-01-15T10:30:00Z"
            },
            {
                "recommendation_id": "rec_002",
                "user_id": user_id,
                "content_type": "trading_signal",
                "title": "Tech Sector Analysis",
                "description": "Based on your trading history and market preferences",
                "relevance_score": 0.87,
                "confidence": 0.82,
                "reasoning": "Aligns with your trading behavior patterns",
                "created_at": "2024-01-15T10:30:00Z"
            },
            {
                "recommendation_id": "rec_003",
                "user_id": user_id,
                "content_type": "community_post",
                "title": "BIPOC Investment Strategies Discussion",
                "description": "Active community discussion matching your interests",
                "relevance_score": 0.79,
                "confidence": 0.75,
                "reasoning": "Based on your community engagement patterns",
                "created_at": "2024-01-15T10:30:00Z"
            }
        ]
    }

@app.get("/personalization/score/{user_id}")
async def get_personalization_score(user_id: str, content_type: str):
    """Get personalization score for content."""
    return {
        "user_id": user_id,
        "content_type": content_type,
        "personalization_score": 0.85,
        "recommendations": [
            "Optimize for visual learning style",
            "Best engagement time: 09:00"
        ],
        "optimal_timing": "09:00",
        "content_preferences": {
            "notifications": True,
            "community": True,
            "gamification": True
        },
        "generated_at": "2024-01-15T10:30:00Z"
    }

@app.get("/api/oracle/insights/")
async def get_oracle_insights():
    """Get Oracle AI insights for market analysis."""
    return {
        "insights": [
            {
                "type": "market_trend",
                "title": "Tech Sector Momentum Building",
                "description": "AI-powered analysis indicates strong momentum in tech sector with particular strength in semiconductor and cloud computing stocks.",
                "confidence": 0.87,
                "impact": "high",
                "timeframe": "2-4 weeks",
                "symbols": ["NVDA", "AMD", "MSFT", "GOOGL"],
                "timestamp": "2024-01-15T10:30:00Z",
                "source": "oracle_ai",
                "category": "market_trend",
                "priority": "high",
                "actionable": True,
                "metadata": {
                    "model_version": "2.0",
                    "data_quality": "high",
                    "last_updated": "2024-01-15T10:30:00Z"
                }
            },
            {
                "type": "volatility_alert",
                "title": "Market Volatility Expected",
                "description": "Technical indicators suggest increased volatility in the coming days. Consider adjusting position sizes and risk management strategies.",
                "confidence": 0.82,
                "impact": "medium",
                "timeframe": "1-2 weeks",
                "symbols": ["SPY", "QQQ", "VIX"],
                "timestamp": "2024-01-15T10:30:00Z",
                "source": "oracle_ai",
                "category": "volatility_alert",
                "priority": "medium",
                "actionable": True,
                "metadata": {
                    "model_version": "2.0",
                    "data_quality": "high",
                    "last_updated": "2024-01-15T10:30:00Z"
                }
            },
            {
                "type": "earnings_opportunity",
                "title": "Earnings Season Opportunities",
                "description": "Upcoming earnings reports show potential for significant moves in financial and healthcare sectors.",
                "confidence": 0.79,
                "impact": "high",
                "timeframe": "1-3 weeks",
                "symbols": ["JPM", "BAC", "JNJ", "PFE"],
                "timestamp": "2024-01-15T10:30:00Z",
                "source": "oracle_ai",
                "category": "earnings_opportunity",
                "priority": "high",
                "actionable": True,
                "metadata": {
                    "model_version": "2.0",
                    "data_quality": "high",
                    "last_updated": "2024-01-15T10:30:00Z"
                }
            }
        ],
        "total_insights": 3,
        "last_updated": "2024-01-15T10:30:00Z",
        "next_update": "2024-01-15T16:30:00Z"
    }

@app.post("/api/voice/process/")
async def process_voice_audio():
    """Process voice audio and return AI response."""
    return {
        "success": True,
        "response": {
            "transcription": "What are the best investment opportunities right now?",
            "text": "Based on current market conditions, I recommend focusing on technology stocks, particularly in AI and cloud computing sectors. Companies like NVIDIA, Microsoft, and Amazon are showing strong fundamentals. However, always remember to diversify your portfolio and consider your risk tolerance.",
            "confidence": 0.92,
            "suggestions": [
                "Consider dollar-cost averaging into tech ETFs",
                "Look at renewable energy stocks for long-term growth",
                "Review your portfolio allocation quarterly"
            ],
            "insights": [
                {
                    "title": "Tech Sector Analysis",
                    "value": "Strong Buy",
                    "description": "Technology stocks showing strong momentum"
                }
            ]
        },
        "timestamp": "2024-01-15T10:30:00Z"
    }

@app.post("/api/transcribe-audio/")
async def transcribe_audio():
    """Transcribe audio to text."""
    return {
        "transcription": "I want to learn about options trading strategies for beginners",
        "audioUrl": "https://example.com/transcribed-audio.wav",
        "confidence": 0.89,
        "timestamp": "2024-01-15T10:30:00Z"
    }

@app.get("/api/voice-ai/voices/")
async def get_available_voices():
    """Get available voice options for text-to-speech."""
    return {
        "voices": {
            "alloy": {
                "name": "Alloy",
                "description": "Neutral, professional voice",
                "gender": "neutral",
                "accent": "american",
                "emotions": ["neutral", "confident", "friendly"]
            },
            "echo": {
                "name": "Echo", 
                "description": "Warm, conversational voice",
                "gender": "male",
                "accent": "american",
                "emotions": ["warm", "encouraging", "professional"]
            },
            "fable": {
                "name": "Fable",
                "description": "Clear, authoritative voice",
                "gender": "male", 
                "accent": "british",
                "emotions": ["authoritative", "confident", "wise"]
            },
            "onyx": {
                "name": "Onyx",
                "description": "Deep, serious voice",
                "gender": "male",
                "accent": "american", 
                "emotions": ["serious", "analytical", "professional"]
            },
            "nova": {
                "name": "Nova",
                "description": "Bright, energetic voice",
                "gender": "female",
                "accent": "american",
                "emotions": ["energetic", "optimistic", "engaging"]
            },
            "shimmer": {
                "name": "Shimmer",
                "description": "Soft, empathetic voice", 
                "gender": "female",
                "accent": "american",
                "emotions": ["empathetic", "calm", "supportive"]
            }
        }
    }

@app.post("/api/voice-ai/synthesize/")
async def synthesize_speech(request: dict):
    """Synthesize text to speech with specified voice and settings."""
    # Don't return audio_url to trigger fallback to device speech with voice parameters
    return {
        "success": True,
        # "audio_url": "http://localhost:8000/api/voice-ai/audio/sample-response.wav",  # Commented out to use device speech
        "duration": 15.2,
        "voice_used": request.get("voice", "alloy"),
        "emotion": request.get("emotion", "neutral"),
        "speed": request.get("speed", 1.0),
        "text_length": len(request.get("text", "")),
        "timestamp": "2024-01-15T10:30:00Z"
    }

@app.post("/api/voice-ai/preview/")
async def preview_voice(request: dict):
    """Preview a voice with sample text."""
    # For demo purposes, don't return audio_url to trigger fallback to basic speech
    return {
        "success": True,
        # "audio_url": "http://localhost:8000/api/voice-ai/audio/sample-preview.wav",  # Commented out to trigger fallback
        "duration": 8.5,
        "voice_used": request.get("voice", "alloy"),
        "emotion": request.get("emotion", "neutral"),
        "speed": request.get("speed", 1.0),
        "preview_text": "This is a preview of the selected voice.",
        "timestamp": "2024-01-15T10:30:00Z"
    }

@app.get("/api/voice-ai/audio/sample-response.wav")
async def get_sample_audio():
    """Serve a sample audio file for voice synthesis."""
    from fastapi.responses import FileResponse
    import os
    
    # Check if the audio file exists
    audio_file_path = "sample-response.wav"
    if os.path.exists(audio_file_path):
        return FileResponse(
            audio_file_path,
            media_type="audio/wav",
            filename="sample-response.wav"
        )
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Audio file not found")

@app.get("/api/voice-ai/audio/sample-preview.wav")
async def get_sample_preview():
    """Serve a sample preview audio file."""
    # Return a simple audio file response
    # In a real implementation, this would be a generated audio file
    # For now, we'll return a 404 to trigger fallback to basic speech
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Preview audio file not found - using fallback speech")

@app.get("/api/market/quotes")
async def get_market_quotes(symbols: str):
    """Get market quotes for multiple symbols."""
    symbol_list = symbols.split(',')
    quotes = {}
    
    for symbol in symbol_list:
        quotes[symbol] = {
            "symbol": symbol,
            "price": round(150.0 + (hash(symbol) % 1000) / 10, 2),
            "change": round((hash(symbol) % 20 - 10) / 10, 2),
            "change_percent": round((hash(symbol) % 20 - 10) / 100, 2),
            "volume": hash(symbol) % 1000000,
            "market_cap": hash(symbol) % 1000000000000,
            "timestamp": "2024-01-15T10:30:00Z",
            "name": f"{symbol} Inc.",
            "currency": "USD",
            "exchange": "NASDAQ"
        }
    
    return {
        "success": True,
        "data": quotes,
        "timestamp": "2024-01-15T10:30:00Z"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": "2024-01-15T10:30:00Z"}

@app.post("/graphql/")
async def graphql_endpoint(request: dict = None):
    """GraphQL endpoint for Apollo Client."""
    # Handle mutations
    if request and "query" in str(request):
        query_str = str(request.get("query", ""))
        
        # Handle updateSecurity mutation
        if "updateSecurity" in query_str:
            return {
                "data": {
                    "updateSecurity": {
                        "success": True,
                        "message": "Security settings updated successfully",
                        "security": {
                            "twoFactorEnabled": True,
                            "biometricEnabled": True,
                            "lastPasswordChange": "2024-01-15T10:30:00Z"
                        }
                    }
                }
            }
        
        # Handle updateProfile mutation
        if "updateProfile" in query_str:
            return {
                "data": {
                    "updateProfile": {
                        "success": True,
                        "message": "Profile updated successfully",
                        "user": {
                            "id": "demo-user-123",
                            "name": "Demo User",
                            "email": "demo@example.com",
                            "phone": "+1-555-0123",
                            "dateOfBirth": "1990-01-15",
                            "address": {
                                "street": "123 Main St",
                                "city": "San Francisco",
                                "state": "CA",
                                "zipCode": "94105",
                                "country": "USA"
                            }
                        }
                    }
                }
            }
        
        # Handle updatePreferences mutation
        if "updatePreferences" in query_str:
            return {
                "data": {
                    "updatePreferences": {
                        "success": True,
                        "message": "Preferences updated successfully",
                        "preferences": {
                            "theme": "light",
                            "notifications": True,
                            "privacy": "public",
                            "language": "en"
                        }
                    }
                }
            }
        
        # Handle changePassword mutation
        if "changePassword" in query_str:
            return {
                "data": {
                    "changePassword": {
                        "success": True,
                        "message": "Password changed successfully"
                    }
                }
            }
    
    # Default query response
    return {
        "data": {
            "me": {
                "id": "demo-user-123",
                "email": "demo@example.com",
                "name": "Demo User",
                "username": "demo",
                "hasPremiumAccess": False,
                "subscriptionTier": "free",
                "profilePic": "https://via.placeholder.com/150",
                "followersCount": 42,
                "followingCount": 128,
                "isFollowingUser": False,
                "isFollowedByUser": False,
                "phone": "+1-555-0123",
                "dateOfBirth": "1990-01-15",
                "address": {
                    "street": "123 Main St",
                    "city": "San Francisco",
                    "state": "CA",
                    "zipCode": "94105",
                    "country": "USA"
                },
                    "preferences": {
                        "theme": "light",
                        "notifications": True,
                        "privacy": "public",
                        "language": "en"
                    },
                    "security": {
                        "twoFactorEnabled": False,
                        "biometricEnabled": True,
                        "lastPasswordChange": "2024-01-01T00:00:00Z"
                    }
            },
            "availableBenchmarks": [
                {
                    "id": "sp500",
                    "name": "S&P 500",
                    "symbol": "^GSPC",
                    "description": "Standard & Poor's 500 Index"
                },
                {
                    "id": "nasdaq",
                    "name": "NASDAQ",
                    "symbol": "^IXIC", 
                    "description": "NASDAQ Composite Index"
                },
                {
                    "id": "dow",
                    "name": "Dow Jones",
                    "symbol": "^DJI",
                    "description": "Dow Jones Industrial Average"
                }
            ],
            "benchmarkSeries": [
                {
                    "benchmarkId": "sp500",
                    "symbol": "^GSPC",
                    "name": "S&P 500",
                    "timeframe": "1Y",
                    "dataPoints": [
                        {"date": "2024-01-01", "value": 4769.83, "timestamp": "2024-01-01T00:00:00Z", "change": 0, "changePercent": 0},
                        {"date": "2024-01-02", "value": 4772.50, "timestamp": "2024-01-02T00:00:00Z", "change": 2.67, "changePercent": 0.056},
                        {"date": "2024-01-03", "value": 4781.18, "timestamp": "2024-01-03T00:00:00Z", "change": 8.68, "changePercent": 0.182},
                        {"date": "2024-01-04", "value": 4789.83, "timestamp": "2024-01-04T00:00:00Z", "change": 8.65, "changePercent": 0.181},
                        {"date": "2024-01-05", "value": 4795.83, "timestamp": "2024-01-05T00:00:00Z", "change": 6.00, "changePercent": 0.125}
                    ],
                    "data": [
                        {"date": "2024-01-01", "value": 4769.83, "timestamp": "2024-01-01T00:00:00Z", "change": 0, "changePercent": 0},
                        {"date": "2024-01-02", "value": 4772.50, "timestamp": "2024-01-02T00:00:00Z", "change": 2.67, "changePercent": 0.056},
                        {"date": "2024-01-03", "value": 4781.18, "timestamp": "2024-01-03T00:00:00Z", "change": 8.68, "changePercent": 0.182},
                        {"date": "2024-01-04", "value": 4789.83, "timestamp": "2024-01-04T00:00:00Z", "change": 8.65, "changePercent": 0.181},
                        {"date": "2024-01-05", "value": 4795.83, "timestamp": "2024-01-05T00:00:00Z", "change": 6.00, "changePercent": 0.125}
                    ],
                    "startValue": 4769.83,
                    "endValue": 4795.83,
                    "totalReturn": 26.00,
                    "totalReturnPercent": 0.55,
                    "volatility": 0.12
                }
            ],
            "myWatchlist": [
                {
                    "id": "watch_001",
                    "symbol": "AAPL",
                    "name": "Apple Inc.",
                    "price": 185.92,
                    "change": 2.15,
                    "changePercent": 1.17,
                    "stock": {
                        "symbol": "AAPL",
                        "name": "Apple Inc.",
                        "price": 185.92,
                        "change": 2.15,
                        "changePercent": 1.17
                    },
                    "notes": "Strong fundamentals, good for long-term hold",
                    "targetPrice": 200.00,
                    "addedAt": "2024-01-15T10:30:00Z"
                },
                {
                    "id": "watch_002", 
                    "symbol": "MSFT",
                    "name": "Microsoft Corporation",
                    "price": 378.85,
                    "change": -1.25,
                    "changePercent": -0.33,
                    "stock": {
                        "symbol": "MSFT",
                        "name": "Microsoft Corporation",
                        "price": 378.85,
                        "change": -1.25,
                        "changePercent": -0.33
                    },
                    "notes": "Cloud growth story continues",
                    "targetPrice": 400.00,
                    "addedAt": "2024-01-15T10:30:00Z"
                },
                {
                    "id": "watch_003",
                    "symbol": "TSLA", 
                    "name": "Tesla, Inc.",
                    "price": 248.50,
                    "change": 5.20,
                    "changePercent": 2.14,
                    "stock": {
                        "symbol": "TSLA",
                        "name": "Tesla, Inc.",
                        "price": 248.50,
                        "change": 5.20,
                        "changePercent": 2.14
                    },
                    "notes": "EV leader with strong growth potential",
                    "targetPrice": 300.00,
                    "addedAt": "2024-01-15T10:30:00Z"
                }
            ],
            "myPortfolios": [
                {
                    "id": "portfolio_001",
                    "name": "Growth Portfolio",
                    "value": 125000.00,
                    "change": 2500.00,
                    "changePercent": 2.04,
                    "totalPortfolios": 1,
                    "totalValue": 125000.00,
                    "holdingsCount": 2,
                    "portfolios": [
                        {
                            "id": "portfolio_001",
                            "name": "Growth Portfolio",
                            "value": 125000.00,
                            "change": 2500.00,
                            "changePercent": 2.04,
                            "totalValue": 125000.00,
                            "holdingsCount": 2,
                            "holdings": [
                                {
                                    "id": "holding_001",
                                    "symbol": "AAPL",
                                    "shares": 100,
                                    "value": 18592.00,
                                    "weight": 14.87,
                                    "stock": {
                                        "symbol": "AAPL",
                                        "name": "Apple Inc.",
                                        "price": 185.92,
                                        "change": 2.15,
                                        "changePercent": 1.17
                                    },
                                    "averagePrice": 180.00,
                                    "currentPrice": 185.92,
                                    "totalValue": 18592.00
                                },
                                {
                                    "id": "holding_002",
                                    "symbol": "MSFT", 
                                    "shares": 50,
                                    "value": 18942.50,
                                    "weight": 15.15,
                                    "stock": {
                                        "symbol": "MSFT",
                                        "name": "Microsoft Corporation",
                                        "price": 378.85,
                                        "change": -1.25,
                                        "changePercent": -0.33
                                    },
                                    "averagePrice": 375.00,
                                    "currentPrice": 378.85,
                                    "totalValue": 18942.50
                                }
                            ]
                        }
                    ],
                    "holdings": [
                        {
                            "id": "holding_001",
                            "symbol": "AAPL",
                            "shares": 100,
                            "value": 18592.00,
                            "weight": 14.87,
                            "stock": {
                                "symbol": "AAPL",
                                "name": "Apple Inc.",
                                "price": 185.92,
                                "change": 2.15,
                                "changePercent": 1.17
                            },
                            "averagePrice": 180.00,
                            "currentPrice": 185.92,
                            "totalValue": 18592.00
                        },
                        {
                            "id": "holding_002",
                            "symbol": "MSFT", 
                            "shares": 50,
                            "value": 18942.50,
                            "weight": 15.15,
                            "stock": {
                                "symbol": "MSFT",
                                "name": "Microsoft Corporation",
                                "price": 378.85,
                                "change": -1.25,
                                "changePercent": -0.33
                            },
                            "averagePrice": 375.00,
                            "currentPrice": 378.85,
                            "totalValue": 18942.50
                        }
                    ]
                }
            ]
        }
    }

@app.get("/api/wealth-circles/")
async def get_wealth_circles():
    """Get wealth circles for community features."""
    return {
        "circles": [
            {
                "id": "circle_001",
                "name": "Tech Investors",
                "description": "Discussion about technology investments",
                "member_count": 1250,
                "is_private": False,
                "created_at": "2024-01-15T10:30:00Z"
            },
            {
                "id": "circle_002", 
                "name": "BIPOC Wealth Builders",
                "description": "Building wealth in the BIPOC community",
                "member_count": 890,
                "is_private": False,
                "created_at": "2024-01-15T10:30:00Z"
            }
        ]
    }

@app.get("/api/wealth-circles/{circle_id}/posts/")
async def get_circle_posts(circle_id: str):
    """Get posts from a wealth circle."""
    return {
        "posts": [
            {
                "id": "post_001",
                "title": "Market Analysis for Q1 2024",
                "content": "Here's my analysis of the current market conditions...",
                "author": "demo_user",
                "created_at": "2024-01-15T10:30:00Z",
                "likes": 45,
                "comments": 12
            }
        ]
    }

# Voice Trading Endpoints
@app.post("/api/voice-trading/parse-command/")
async def parse_voice_command(request: dict):
    """Parse voice command into structured order data"""
    transcript = request.get("transcript", "")
    voice_name = request.get("voice_name", "Nova")
    
    # Mock voice command parsing
    mock_parsed_order = {
        "symbol": "AAPL",
        "side": "buy",
        "quantity": 100,
        "order_type": "limit",
        "price": 150.0,
        "confidence": 0.85,
        "confirmation_message": f"{voice_name} confirming: buy 100 AAPL at $150. Proceeding?"
    }
    
    return {
        "success": True,
        "parsed_order": mock_parsed_order,
        "message": "Voice command parsed successfully"
    }

@app.post("/api/voice-trading/place-order/")
async def place_voice_order(request: dict):
    """Place order from voice command"""
    symbol = request.get("symbol", "AAPL")
    side = request.get("side", "buy")
    quantity = request.get("quantity", 100)
    order_type = request.get("order_type", "market")
    price = request.get("price")
    
    # Mock order placement
    mock_order = {
        "id": f"voice_order_{int(time.time())}",
        "symbol": symbol,
        "side": side,
        "order_type": order_type,
        "quantity": quantity,
        "status": "filled",
        "limit_price": price,
        "created_at": datetime.now().isoformat()
    }
    
    return {
        "success": True,
        "order": mock_order,
        "message": f"Order placed successfully: {side} {quantity} {symbol}"
    }

@app.get("/api/voice-trading/status/")
async def get_trading_status():
    """Get current trading status"""
    return {
        "account": {
            "buying_power": 100000.0,
            "portfolio_value": 100000.0,
            "day_trade_count": 0,
            "pattern_day_trader": False
        },
        "positions": [],
        "open_orders": [],
        "streaming": {
            "active": True,
            "symbols": ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
        }
    }

@app.post("/api/voice-trading/cancel-order/")
async def cancel_voice_order(request: dict):
    """Cancel an order"""
    order_id = request.get("order_id")
    
    return {
        "success": True,
        "message": f"Order {order_id} cancelled successfully"
    }

# Live Data Endpoints
@app.get("/api/live-data/universe/{mode}")
async def get_live_universe(mode: str):
    """Get live trading universe for mode"""
    # Mock universe data
    universe_data = {
        "SAFE": [
            {
                "symbol": "AAPL",
                "price": 175.50,
                "volume": 2500000,
                "avg_volume": 2000000,
                "volatility": 0.025,
                "momentum": 0.015,
                "spread_bps": 2.5,
                "score": 0.85
            },
            {
                "symbol": "MSFT",
                "price": 380.25,
                "volume": 1800000,
                "avg_volume": 1500000,
                "volatility": 0.022,
                "momentum": 0.012,
                "spread_bps": 3.1,
                "score": 0.82
            },
            {
                "symbol": "GOOGL",
                "price": 142.80,
                "volume": 1200000,
                "avg_volume": 1000000,
                "volatility": 0.028,
                "momentum": 0.018,
                "spread_bps": 2.8,
                "score": 0.78
            }
        ],
        "AGGRESSIVE": [
            {
                "symbol": "TSLA",
                "price": 245.75,
                "volume": 3500000,
                "avg_volume": 2000000,
                "volatility": 0.045,
                "momentum": 0.025,
                "spread_bps": 4.2,
                "score": 0.88
            },
            {
                "symbol": "NVDA",
                "price": 485.30,
                "volume": 2800000,
                "avg_volume": 1800000,
                "volatility": 0.038,
                "momentum": 0.022,
                "spread_bps": 3.8,
                "score": 0.85
            },
            {
                "symbol": "META",
                "price": 325.40,
                "volume": 2200000,
                "avg_volume": 1500000,
                "volatility": 0.032,
                "momentum": 0.019,
                "spread_bps": 3.5,
                "score": 0.81
            }
        ]
    }
    
    return {
        "mode": mode,
        "universe": universe_data.get(mode, universe_data["SAFE"]),
        "timestamp": datetime.now().isoformat(),
        "total_symbols": len(universe_data.get(mode, universe_data["SAFE"]))
    }

@app.get("/api/live-data/features/{symbol}")
async def get_live_features(symbol: str):
    """Get real-time features for a symbol"""
    # Mock feature calculation
    features = {
        "symbol": symbol,
        "timestamp": datetime.now().isoformat(),
        "momentum_15m": 0.015,
        "momentum_5m": 0.008,
        "momentum_1m": 0.003,
        "rvol_10m": 1.8,
        "rvol_5m": 2.1,
        "volume_spike": 1.5,
        "rsi_14": 65.5,
        "macd_signal": 0.12,
        "bollinger_position": 0.75,
        "vwap_distance": 0.008,
        "spread_bps": 2.8,
        "bid_ask_ratio": 0.999,
        "order_flow_imbalance": 0.15,
        "atr_5m": 1.25,
        "atr_15m": 1.45,
        "volatility_regime": "NORMAL",
        "breakout_pct": 0.012,
        "resistance_level": 180.50,
        "support_level": 172.30,
        "news_sentiment": 0.3,
        "earnings_proximity": 0.1,
        "catalyst_score": 0.4,
        "composite_score": 0.78
    }
    
    return features

@app.get("/api/live-data/picks/{mode}")
async def get_live_picks(mode: str):
    """Get live day trading picks"""
    # Mock picks generation
    picks_data = {
        "SAFE": [
            {
                "symbol": "AAPL",
                "side": "LONG",
                "score": 0.85,
                "confidence": 0.88,
                "features": {
                    "momentum_15m": 0.015,
                    "rvol_10m": 1.8,
                    "vwap_dist": 0.008,
                    "breakout_pct": 0.012,
                    "spread_bps": 2.5,
                    "catalyst_score": 0.4
                },
                "risk": {
                    "atr_5m": 1.25,
                    "size_shares": 200,
                    "stop": 172.50,
                    "targets": [178.50, 181.50],
                    "time_stop_min": 60
                },
                "market_regime": "BULL",
                "volatility_regime": "NORMAL",
                "entry_time": datetime.now().isoformat(),
                "oracle_insight": "Oracle: AAPL showing strong bullish momentum with 1.8x volume spike",
                "notes": "High volume spike: 1.8x; Breakout: 1.20%; Tight spreads - good liquidity"
            }
        ],
        "AGGRESSIVE": [
            {
                "symbol": "TSLA",
                "side": "LONG",
                "score": 0.88,
                "confidence": 0.92,
                "features": {
                    "momentum_15m": 0.025,
                    "rvol_10m": 2.1,
                    "vwap_dist": 0.015,
                    "breakout_pct": 0.018,
                    "spread_bps": 4.2,
                    "catalyst_score": 0.6
                },
                "risk": {
                    "atr_5m": 2.15,
                    "size_shares": 150,
                    "stop": 240.50,
                    "targets": [251.00, 256.50],
                    "time_stop_min": 30
                },
                "market_regime": "VOLATILE",
                "volatility_regime": "HIGH",
                "entry_time": datetime.now().isoformat(),
                "oracle_insight": "Oracle: TSLA breaking above resistance with RSI 68.2 - bullish continuation likely",
                "notes": "High volume spike: 2.1x; Breakout: 1.80%; Strong catalyst support"
            }
        ]
    }
    
    return {
        "mode": mode,
        "picks": picks_data.get(mode, picks_data["SAFE"]),
        "asOf": datetime.now().isoformat(),
        "universeSize": 50,
        "qualityThreshold": 0.7 if mode == "SAFE" else 0.6
    }

@app.get("/api/live-data/market-status/")
async def get_market_status():
    """Get current market status"""
    return {
        "market_open": True,
        "pre_market": False,
        "after_hours": False,
        "session": "REGULAR",
        "time_until_close": "2h 15m",
        "volatility_regime": "NORMAL",
        "market_regime": "BULL",
        "vix_level": 18.5,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/live-data/top-movers/")
async def get_top_movers():
    """Get top moving symbols"""
    return {
        "gainers": [
            {"symbol": "TSLA", "change": 0.025, "volume": 3500000},
            {"symbol": "NVDA", "change": 0.022, "volume": 2800000},
            {"symbol": "META", "change": 0.019, "volume": 2200000}
        ],
        "losers": [
            {"symbol": "AAPL", "change": -0.012, "volume": 2500000},
            {"symbol": "MSFT", "change": -0.008, "volume": 1800000},
            {"symbol": "GOOGL", "change": -0.005, "volume": 1200000}
        ],
        "volume_leaders": [
            {"symbol": "TSLA", "volume": 3500000, "change": 0.025},
            {"symbol": "AAPL", "volume": 2500000, "change": -0.012},
            {"symbol": "NVDA", "volume": 2800000, "change": 0.022}
        ],
        "timestamp": datetime.now().isoformat()
    }

# Phase 2: Advanced Trading Endpoints
@app.get("/api/advanced-features/{symbol}")
async def get_advanced_features(symbol: str):
    """Get advanced technical features for a symbol"""
    return {
        "symbol": symbol,
        "timestamp": datetime.now().isoformat(),
        "price_momentum": {
            "momentum_5": 0.015,
            "momentum_10": 0.012,
            "momentum_20": 0.008,
            "momentum_ma_5": 100.5,
            "momentum_ma_10": 100.2,
            "momentum_ma_20": 99.8
        },
        "volatility_features": {
            "volatility_5": 0.025,
            "volatility_10": 0.028,
            "volatility_20": 0.030,
            "volatility_annualized_5": 0.15,
            "volatility_annualized_10": 0.18,
            "volatility_annualized_20": 0.20
        },
        "trend_features": {
            "trend_slope": 0.001,
            "trend_r_squared": 0.75,
            "price_position": 0.65
        },
        "volume_profile": {
            "vwap_5": 100.3,
            "vwap_10": 100.5,
            "vwap_20": 100.2,
            "vwap_distance_5": 0.005,
            "vwap_distance_10": 0.008,
            "vwap_distance_20": 0.012,
            "volume_profile_skew": 0.2,
            "volume_profile_kurtosis": 2.1
        },
        "order_flow": {
            "buy_sell_ratio": 1.2,
            "net_order_flow": 0.15
        },
        "liquidity_features": {
            "volume_stability": 0.8,
            "volume_trend": 0.05
        },
        "oscillators": {
            "rsi_14": 65.5,
            "rsi_21": 68.2,
            "rsi_34": 70.1,
            "stoch_k": 75.0,
            "stoch_d": 72.0,
            "williams_r": -25.0
        },
        "trend_indicators": {
            "macd_line": 0.12,
            "macd_signal": 0.08,
            "macd_histogram": 0.04,
            "bb_upper": 102.5,
            "bb_middle": 100.0,
            "bb_lower": 97.5,
            "bb_position": 0.75,
            "bb_width": 0.15
        },
        "volatility_indicators": {
            "atr": 1.25,
            "atr_percent": 1.25,
            "atrp": 1.25
        },
        "microstructure": {
            "price_volume_correlation": 0.65
        },
        "spread_analysis": {
            "spread_absolute": 0.05,
            "spread_bps": 5.0,
            "spread_percent": 0.05,
            "effective_spread_ratio": 0.8
        },
        "depth_analysis": {
            "bid_depth": 1000,
            "ask_depth": 1200,
            "depth_imbalance": -0.09
        },
        "ml_features": {
            "price_skewness": 0.2,
            "price_kurtosis": 2.1,
            "volume_skewness": 0.8,
            "volume_kurtosis": 3.2
        },
        "anomaly_scores": {
            "isolation_forest": 1
        },
        "pattern_recognition": {
            "support_distance": 0.05,
            "resistance_distance": 0.08,
            "breakout_strength": 0.012
        },
        "sector_correlation": {
            "tech_correlation": 0.75,
            "finance_correlation": 0.45,
            "energy_correlation": 0.30
        },
        "market_regime": {
            "vix_level": 18.5,
            "treasury_yield": 4.2,
            "dollar_strength": 0.02
        },
        "macro_features": {
            "economic_sentiment": 0.65,
            "risk_appetite": 0.7,
            "liquidity_conditions": 0.8
        },
        "composite_score": 0.78,
        "confidence_score": 0.85,
        "risk_score": 0.22
    }

@app.get("/api/enhanced-scoring/{symbol}")
async def get_enhanced_score(symbol: str, side: str = "LONG"):
    """Get enhanced ML-based scoring for a symbol"""
    return {
        "symbol": symbol,
        "side": side,
        "base_score": 0.75,
        "confidence_score": 0.82,
        "risk_score": 0.18,
        "ml_score": 0.78,
        "ensemble_score": 0.76,
        "score_lower_bound": 0.68,
        "score_upper_bound": 0.84,
        "feature_contributions": {
            "momentum": 0.3,
            "volume": 0.25,
            "technical": 0.25,
            "microstructure": 0.2
        },
        "model_used": "ensemble_model",
        "prediction_confidence": 0.85,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/risk-assessment/{symbol}")
async def get_risk_assessment(symbol: str, mode: str = "SAFE"):
    """Get comprehensive risk assessment for a position"""
    return {
        "symbol": symbol,
        "side": "LONG",
        "quantity": 100,
        "entry_price": 100.0,
        "current_price": 102.5,
        "unrealized_pnl": 250.0,
        "unrealized_pnl_percent": 0.025,
        "risk_amount": 250.0,
        "risk_percent": 0.025,
        "position_value": 10250.0,
        "position_percent": 0.05,
        "leverage": 1.0,
        "stop_loss": 95.0,
        "take_profit": 110.0,
        "stop_loss_distance": 7.5,
        "take_profit_distance": 7.5,
        "time_in_position": 45,
        "time_risk_score": 0.375,
        "volatility_risk": 0.02,
        "atr_risk": 0.04,
        "overall_risk_score": 0.35,
        "risk_level": "MEDIUM",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/portfolio-risk/")
async def get_portfolio_risk(mode: str = "SAFE"):
    """Get portfolio-level risk assessment"""
    return {
        "total_value": 100000.0,
        "cash": 50000.0,
        "buying_power": 75000.0,
        "total_risk": 2500.0,
        "total_exposure": 50000.0,
        "portfolio_beta": 1.1,
        "position_count": 5,
        "sector_diversification": {
            "Technology": 0.4,
            "Finance": 0.2,
            "Healthcare": 0.15,
            "Energy": 0.1,
            "Other": 0.15
        },
        "correlation_risk": 0.65,
        "daily_pnl": 1250.0,
        "daily_pnl_percent": 0.0125,
        "max_drawdown": 0.03,
        "sharpe_ratio": 1.8,
        "risk_limit_status": {
            "daily_loss_limit": True,
            "drawdown_limit": True,
            "position_size_limit": True,
            "sector_exposure_limit": True
        },
        "risk_alerts": [],
        "timestamp": datetime.now().isoformat()
    }

# Advanced Order Endpoints
@app.post("/api/advanced-orders/bracket/")
async def place_bracket_order(request: dict):
    """Place a bracket order"""
    return {
        "success": True,
        "order_id": f"BRACKET_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "message": f"Bracket order placed for {request.get('symbol')}",
        "execution_details": {
            "symbol": request.get("symbol"),
            "side": request.get("side"),
            "quantity": request.get("quantity"),
            "entry_price": request.get("entry_price"),
            "stop_loss": request.get("stop_loss"),
            "take_profit_1": request.get("take_profit_1"),
            "take_profit_2": request.get("take_profit_2"),
            "status": "SUBMITTED",
            "created_at": datetime.now().isoformat()
        }
    }

@app.post("/api/advanced-orders/oco/")
async def place_oco_order(request: dict):
    """Place an OCO (One-Cancels-Other) order"""
    return {
        "success": True,
        "order_id": f"OCO_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "message": f"OCO order placed for {request.get('symbol')}",
        "execution_details": {
            "symbol": request.get("symbol"),
            "side": request.get("side"),
            "quantity": request.get("quantity"),
            "order_1_price": request.get("order_1_price"),
            "order_1_type": request.get("order_1_type"),
            "order_2_price": request.get("order_2_price"),
            "order_2_type": request.get("order_2_type"),
            "status": "SUBMITTED",
            "created_at": datetime.now().isoformat()
        }
    }

@app.post("/api/advanced-orders/iceberg/")
async def place_iceberg_order(request: dict):
    """Place an iceberg order"""
    return {
        "success": True,
        "order_id": f"ICEBERG_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "message": f"Iceberg order placed for {request.get('symbol')}",
        "execution_details": {
            "symbol": request.get("symbol"),
            "side": request.get("side"),
            "total_quantity": request.get("total_quantity"),
            "visible_quantity": request.get("visible_quantity"),
            "price": request.get("price"),
            "status": "SUBMITTED",
            "created_at": datetime.now().isoformat()
        }
    }

@app.post("/api/advanced-orders/trailing-stop/")
async def place_trailing_stop(request: dict):
    """Place a trailing stop order"""
    return {
        "success": True,
        "order_id": f"TRAILING_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "message": f"Trailing stop placed for {request.get('symbol')}",
        "execution_details": {
            "symbol": request.get("symbol"),
            "side": request.get("side"),
            "quantity": request.get("quantity"),
            "trail_amount": request.get("trail_amount"),
            "trail_percent": request.get("trail_percent"),
            "status": "SUBMITTED",
            "created_at": datetime.now().isoformat()
        }
    }

@app.post("/api/advanced-orders/twap/")
async def execute_twap_order(request: dict):
    """Execute TWAP (Time-Weighted Average Price) order"""
    symbol = request.get("symbol")
    total_quantity = request.get("total_quantity", 1000)
    duration_minutes = request.get("duration_minutes", 30)
    
    # Simulate TWAP execution
    intervals = min(10, duration_minutes // 2)
    quantity_per_interval = total_quantity // intervals
    
    execution_results = []
    total_filled = 0
    average_price = 0.0
    
    for i in range(intervals):
        price = 100.0 + (i * 0.5)  # Simulate price movement
        fill_quantity = quantity_per_interval
        
        execution_results.append({
            "interval": i + 1,
            "quantity": fill_quantity,
            "price": price,
            "order_id": f"TWAP_{i}_{datetime.now().strftime('%H%M%S')}",
            "timestamp": datetime.now().isoformat()
        })
        
        total_filled += fill_quantity
        average_price += price * fill_quantity
    
    average_price = average_price / total_filled if total_filled > 0 else 0
    
    return {
        "symbol": symbol,
        "side": request.get("side"),
        "total_quantity": total_quantity,
        "total_filled": total_filled,
        "average_price": average_price,
        "duration_minutes": duration_minutes,
        "execution_results": execution_results,
        "completed_at": datetime.now().isoformat()
    }

@app.post("/api/advanced-orders/vwap/")
async def execute_vwap_order(request: dict):
    """Execute VWAP (Volume-Weighted Average Price) order"""
    symbol = request.get("symbol")
    total_quantity = request.get("total_quantity", 1000)
    duration_minutes = request.get("duration_minutes", 30)
    
    # Simulate VWAP execution
    intervals = min(10, duration_minutes)
    base_quantity = total_quantity // intervals
    
    execution_results = []
    total_filled = 0
    average_price = 0.0
    
    for i in range(intervals):
        volume_weight = 1.0 + (i * 0.1)  # Simulate volume pattern
        price = 100.0 + (i * 0.3)  # Simulate price movement
        fill_quantity = int(base_quantity * volume_weight)
        
        execution_results.append({
            "interval": i + 1,
            "quantity": fill_quantity,
            "price": price,
            "volume_weight": volume_weight,
            "order_id": f"VWAP_{i}_{datetime.now().strftime('%H%M%S')}",
            "timestamp": datetime.now().isoformat()
        })
        
        total_filled += fill_quantity
        average_price += price * fill_quantity
    
    average_price = average_price / total_filled if total_filled > 0 else 0
    
    return {
        "symbol": symbol,
        "side": request.get("side"),
        "total_quantity": total_quantity,
        "total_filled": total_filled,
        "average_price": average_price,
        "duration_minutes": duration_minutes,
        "execution_results": execution_results,
        "completed_at": datetime.now().isoformat()
    }

@app.post("/api/advanced-orders/cancel/")
async def cancel_advanced_order(request: dict):
    """Cancel an advanced order"""
    order_id = request.get("order_id")
    return {
        "success": True,
        "order_id": order_id,
        "message": f"Order {order_id} cancelled successfully"
    }

# Oracle AI Endpoints
@app.get("/api/oracle-insights/{symbol}")
async def get_oracle_insights(symbol: str, side: str = "LONG"):
    """Get Oracle AI insights for a symbol"""
    return {
        "symbol": symbol,
        "side": side,
        "insights": [
            {
                "insight_type": "MOMENTUM",
                "insight_text": f"Oracle: {symbol} showing strong bullish momentum acceleration. 5m momentum 1.5% exceeds 10m 1.2%, indicating increasing buying pressure.",
                "confidence": 0.85,
                "impact_score": 15.0,
                "time_horizon": "SHORT",
                "supporting_evidence": [
                    "5m momentum: 1.50%",
                    "10m momentum: 1.20%",
                    "20m momentum: 0.80%",
                    "Momentum trend: ACCELERATING"
                ],
                "timestamp": datetime.now().isoformat()
            },
            {
                "insight_type": "VOLUME",
                "insight_text": f"Oracle: {symbol} showing strong volume confirmation for bullish move. 1.8x relative volume with price above VWAP by 0.8%, indicating institutional buying.",
                "confidence": 0.82,
                "impact_score": 18.0,
                "time_horizon": "SHORT",
                "supporting_evidence": [
                    "Relative volume: 1.8x",
                    "Volume spike: 1.5x",
                    "VWAP distance: 0.80%",
                    "Volume confirmation: True"
                ],
                "timestamp": datetime.now().isoformat()
            },
            {
                "insight_type": "TECHNICAL",
                "insight_text": f"Oracle: {symbol} showing Bollinger Band bounce setup. Price at 75% of BB range with MACD confirmation, suggesting mean reversion opportunity.",
                "confidence": 0.80,
                "impact_score": 25.0,
                "time_horizon": "MEDIUM",
                "supporting_evidence": [
                    "RSI(14): 65.5",
                    "MACD signal: 0.120",
                    "BB position: 75%",
                    "RSI extreme: False"
                ],
                "timestamp": datetime.now().isoformat()
            }
        ],
        "oracle_score": 0.78,
        "oracle_confidence": 0.82,
        "market_regime": "BULL",
        "adaptive_adjustments": {
            "market_regime": 0.02,
            "volatility": -0.01,
            "liquidity": -0.005
        },
        "adaptive_score": 0.79,
        "confidence_interval": [0.72, 0.86],
        "timestamp": datetime.now().isoformat()
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
