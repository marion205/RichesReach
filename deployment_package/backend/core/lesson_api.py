"""
Lesson API
FastAPI endpoints for lesson library and lesson details
"""
from fastapi import APIRouter, HTTPException, Request, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import os
import sys

# Setup Django
try:
    import django
    if 'DJANGO_SETTINGS_MODULE' not in os.environ:
        backend_path = os.path.join(os.path.dirname(__file__), '..')
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
    django.setup()
    
    from django.contrib.auth import get_user_model
    from django.utils import timezone
    from asgiref.sync import sync_to_async
    from core.daily_brief_models import UserProgress, UserAchievement
    DJANGO_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Django not available for Lesson API: {e}")
    DJANGO_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/lessons", tags=["lessons"])

# Mock lesson data (replace with database in production)
MOCK_LESSONS = [
    {
        "id": "1",
        "title": "What is a Stock?",
        "description": "Learn the fundamentals of stocks and how they work",
        "duration_minutes": 2,
        "difficulty": "beginner",
        "category": "basics",
        "concepts": ["stocks", "equity", "ownership"],
        "content": "A stock represents ownership in a company. When you buy a stock, you're buying a small piece of that company. If the company does well, your stock value increases. If it does poorly, your stock value decreases. Stocks are traded on exchanges like the New York Stock Exchange (NYSE) or NASDAQ.",
        "key_takeaways": [
            "Stocks represent ownership in a company",
            "Stock prices fluctuate based on company performance",
            "Diversification helps reduce risk"
        ],
    },
    {
        "id": "2",
        "title": "Understanding Market Volatility",
        "description": "Why markets go up and down, and what it means for you",
        "duration_minutes": 3,
        "difficulty": "beginner",
        "category": "basics",
        "concepts": ["volatility", "market cycles"],
        "content": "Market volatility refers to how much stock prices fluctuate. High volatility means prices swing widely; low volatility means prices are more stable. Volatility is normal and expected in investing. It's driven by factors like economic news, company earnings, and investor sentiment. For long-term investors, volatility is less concerning than for short-term traders.",
        "key_takeaways": [
            "Volatility is normal in investing",
            "Long-term investors can ride out volatility",
            "Don't make decisions based on daily price swings"
        ],
    },
    {
        "id": "3",
        "title": "Building Your First Portfolio",
        "description": "Step-by-step guide to creating a diversified portfolio",
        "duration_minutes": 5,
        "difficulty": "intermediate",
        "category": "portfolio",
        "concepts": ["diversification", "asset allocation"],
        "content": "A diversified portfolio spreads your investments across different assets, sectors, and geographic regions. This reduces risk because if one investment performs poorly, others may perform well. A good starting portfolio might include: 60% stocks, 30% bonds, and 10% cash or alternatives. As you get older or your goals change, you might shift to more conservative investments.",
        "key_takeaways": [
            "Diversification reduces risk",
            "Asset allocation depends on your goals and timeline",
            "Rebalance your portfolio periodically"
        ],
    },
    {
        "id": "4",
        "title": "Risk vs. Reward",
        "description": "Understanding the relationship between risk and potential returns",
        "duration_minutes": 4,
        "difficulty": "intermediate",
        "category": "risk",
        "concepts": ["risk", "returns", "correlation"],
        "content": "In investing, there's a fundamental relationship: higher potential returns usually come with higher risk. Stocks have historically provided higher returns than bonds, but with more volatility. Bonds are generally safer but offer lower returns. Your risk tolerance depends on your age, financial situation, and goals. Younger investors can typically take more risk because they have time to recover from losses.",
        "key_takeaways": [
            "Higher returns usually mean higher risk",
            "Your risk tolerance depends on your situation",
            "Diversification helps balance risk and reward"
        ],
    },
    {
        "id": "5",
        "title": "Introduction to Bonds",
        "description": "What bonds are and how they work",
        "duration_minutes": 3,
        "difficulty": "beginner",
        "category": "bonds",
        "concepts": ["bonds", "fixed income", "yield"],
        "content": "A bond is essentially a loan you make to a company or government. In return, they pay you interest over time and return your principal when the bond matures. Bonds are generally less risky than stocks but offer lower potential returns. They're a good way to balance risk in your portfolio. Government bonds are the safest, while corporate bonds offer higher yields but more risk.",
        "key_takeaways": [
            "Bonds are loans to companies or governments",
            "Bonds provide steady income through interest payments",
            "Bonds are generally safer but offer lower returns than stocks"
        ],
    },
    {
        "id": "6",
        "title": "Tax-Efficient Investing",
        "description": "How to minimize taxes on your investments",
        "duration_minutes": 4,
        "difficulty": "intermediate",
        "category": "tax",
        "concepts": ["tax", "capital gains", "tax-advantaged accounts"],
        "content": "Tax-efficient investing means structuring your investments to minimize taxes. Key strategies include: using tax-advantaged accounts (401k, IRA), holding investments long-term to qualify for lower capital gains rates, and tax-loss harvesting (selling losing investments to offset gains). Understanding tax implications can significantly improve your after-tax returns over time.",
        "key_takeaways": [
            "Use tax-advantaged accounts when possible",
            "Long-term investments get better tax treatment",
            "Tax-loss harvesting can offset gains"
        ],
    },
]

class LessonResponse(BaseModel):
    id: str
    title: str
    description: str
    duration_minutes: int
    difficulty: str
    category: str
    concepts: List[str]
    completed: bool = False
    progress_percent: int = 0

class LessonDetailResponse(LessonResponse):
    content: str
    key_takeaways: List[str]

async def get_user_from_token(request: Request):
    """Extract user from authorization token"""
    if not DJANGO_AVAILABLE:
        return None
    
    try:
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        # TODO: Implement proper JWT token validation
        # For now, return None (will need proper auth implementation)
        return None
    except Exception as e:
        logger.error(f"Error getting user from token: {e}")
        return None

@router.get("/", response_model=List[LessonResponse])
async def get_lessons(
    request: Request,
    category: Optional[str] = Query(None, description="Filter by category"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    search: Optional[str] = Query(None, description="Search query"),
):
    """Get all lessons with optional filtering"""
    if not DJANGO_AVAILABLE:
        # Return mock data if Django not available
        lessons = MOCK_LESSONS.copy()
    else:
        user = await get_user_from_token(request)
        # TODO: Fetch from database when lesson models are created
        lessons = MOCK_LESSONS.copy()
        
        # Mark lessons as completed based on user progress
        if user:
            try:
                progress = await sync_to_async(UserProgress.objects.get)(user=user)
                # For now, we'll use a simple check - in production, track individual lesson completion
            except:
                pass
    
    # Apply filters
    if category:
        lessons = [l for l in lessons if l['category'] == category]
    
    if difficulty:
        lessons = [l for l in lessons if l['difficulty'] == difficulty]
    
    if search:
        search_lower = search.lower()
        lessons = [
            l for l in lessons
            if search_lower in l['title'].lower() or
               search_lower in l['description'].lower() or
               any(search_lower in c.lower() for c in l['concepts'])
        ]
    
    # Format response
    result = []
    for lesson in lessons:
        result.append({
            "id": lesson["id"],
            "title": lesson["title"],
            "description": lesson["description"],
            "duration_minutes": lesson["duration_minutes"],
            "difficulty": lesson["difficulty"],
            "category": lesson["category"],
            "concepts": lesson["concepts"],
            "completed": False,  # TODO: Check user progress
            "progress_percent": 0,  # TODO: Calculate from user progress
        })
    
    return result

@router.get("/{lesson_id}", response_model=LessonDetailResponse)
async def get_lesson_detail(
    request: Request,
    lesson_id: str,
):
    """Get detailed lesson content"""
    if not DJANGO_AVAILABLE:
        # Return mock data if Django not available
        lesson = next((l for l in MOCK_LESSONS if l['id'] == lesson_id), None)
    else:
        user = await get_user_from_token(request)
        # TODO: Fetch from database when lesson models are created
        lesson = next((l for l in MOCK_LESSONS if l['id'] == lesson_id), None)
    
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    return {
        "id": lesson["id"],
        "title": lesson["title"],
        "description": lesson["description"],
        "duration_minutes": lesson["duration_minutes"],
        "difficulty": lesson["difficulty"],
        "category": lesson["category"],
        "concepts": lesson["concepts"],
        "content": lesson["content"],
        "key_takeaways": lesson["key_takeaways"],
        "completed": False,  # TODO: Check user progress
        "progress_percent": 0,  # TODO: Calculate from user progress
    }

@router.post("/{lesson_id}/complete")
async def complete_lesson(
    request: Request,
    lesson_id: str,
):
    """Mark a lesson as completed"""
    if not DJANGO_AVAILABLE:
        raise HTTPException(status_code=503, detail="Lesson service not available")
    
    user = await get_user_from_token(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Verify lesson exists
    lesson = next((l for l in MOCK_LESSONS if l['id'] == lesson_id), None)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Update user progress
    try:
        progress, _ = await sync_to_async(UserProgress.objects.get_or_create)(user=user)
        progress.lessons_completed += 1
        progress.concepts_learned += len(lesson.get('concepts', []))
        await sync_to_async(progress.save)()
        
        # Check for achievements
        achievements_unlocked = []
        if progress.lessons_completed == 1:
            achievement, created = await sync_to_async(UserAchievement.objects.get_or_create)(
                user=user,
                achievement_type='first_lesson',
            )
            if created:
                achievements_unlocked.append('first_lesson')
        
        if progress.lessons_completed == 10:
            achievement, created = await sync_to_async(UserAchievement.objects.get_or_create)(
                user=user,
                achievement_type='lessons_10',
            )
            if created:
                achievements_unlocked.append('lessons_10')
        
        return JSONResponse({
            "success": True,
            "message": "Lesson completed",
            "achievements_unlocked": achievements_unlocked,
        })
    except Exception as e:
        logger.error(f"Error completing lesson: {e}")
        raise HTTPException(status_code=500, detail="Failed to complete lesson")

