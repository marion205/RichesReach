"""
Lesson API
FastAPI endpoints for lesson library and lesson details.
JWT auth via graphql_jwt, progress by lesson ID, pagination.
"""
from fastapi import APIRouter, HTTPException, Request, Query
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
    from core.lesson_models import Lesson
    DJANGO_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Django not available for Lesson API: {e}")
    DJANGO_AVAILABLE = False
    Lesson = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/lessons", tags=["lessons"])


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


class LessonListResponse(BaseModel):
    """Paginated list of lessons with metadata."""
    items: List[LessonResponse]
    total: int
    page: int
    limit: int


async def get_user_from_token(request: Request):
    """
    Resolve user from Authorization header using graphql_jwt (Bearer or Token).
    Returns None if unauthenticated or Django unavailable.
    """
    if not DJANGO_AVAILABLE:
        return None

    auth_header = request.headers.get("Authorization") or ""
    if not auth_header:
        return None

    token = None
    if auth_header.startswith("Token "):
        token = auth_header.replace("Token ", "").strip()
    elif auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "").strip()

    if not token:
        return None

    try:
        from graphql_jwt.shortcuts import get_user_by_token
        User = get_user_model()
        user = await sync_to_async(get_user_by_token)(token)
        return user
    except Exception as e:
        logger.debug("Auth token invalid or expired: %s", e)
        return None

@router.get("/", response_model=LessonListResponse)
async def get_lessons(
    request: Request,
    category: Optional[str] = Query(None, description="Filter by category"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    search: Optional[str] = Query(None, description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
):
    """Get lessons with filtering and pagination; completion status from user progress."""
    if not DJANGO_AVAILABLE or Lesson is None:
        raise HTTPException(status_code=503, detail="Lesson service not available")

    queryset = Lesson.objects.all()
    if category:
        queryset = queryset.filter(category=category)
    if difficulty:
        queryset = queryset.filter(difficulty=difficulty)
    if search:
        from django.db.models import Q
        queryset = queryset.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )
    total_count = await sync_to_async(queryset.count)()

    completed_ids = set()
    user = await get_user_from_token(request)
    if user:
        try:
            progress = await sync_to_async(UserProgress.objects.get)(user=user)
            completed_ids = set(getattr(progress, "completed_lesson_ids", []) or [])
        except UserProgress.DoesNotExist:
            pass

    start = (page - 1) * limit
    paged = await sync_to_async(list)(queryset[start : start + limit])

    result_items = []
    for lesson in paged:
        is_done = lesson.id in completed_ids
        result_items.append({
            "id": lesson.id,
            "title": lesson.title,
            "description": lesson.description,
            "duration_minutes": lesson.duration_minutes,
            "difficulty": lesson.difficulty,
            "category": lesson.category,
            "concepts": list(lesson.concepts) if lesson.concepts else [],
            "completed": is_done,
            "progress_percent": 100 if is_done else 0,
        })

    return {
        "items": result_items,
        "total": total_count,
        "page": page,
        "limit": limit,
    }

@router.get("/{lesson_id}", response_model=LessonDetailResponse)
async def get_lesson_detail(
    request: Request,
    lesson_id: str,
):
    """Get detailed lesson content; completion status from user progress."""
    if not DJANGO_AVAILABLE or Lesson is None:
        raise HTTPException(status_code=503, detail="Lesson service not available")

    lesson = await sync_to_async(Lesson.objects.filter(id=lesson_id).first)()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    completed = False
    user = await get_user_from_token(request)
    if user:
        try:
            progress = await sync_to_async(UserProgress.objects.get)(user=user)
            completed_ids = set(getattr(progress, "completed_lesson_ids", []) or [])
            completed = lesson_id in completed_ids
        except UserProgress.DoesNotExist:
            pass

    return {
        "id": lesson.id,
        "title": lesson.title,
        "description": lesson.description,
        "duration_minutes": lesson.duration_minutes,
        "difficulty": lesson.difficulty,
        "category": lesson.category,
        "concepts": list(lesson.concepts) if lesson.concepts else [],
        "content": lesson.content,
        "key_takeaways": list(lesson.key_takeaways) if lesson.key_takeaways else [],
        "completed": completed,
        "progress_percent": 100 if completed else 0,
    }

@router.post("/{lesson_id}/complete")
async def complete_lesson(
    request: Request,
    lesson_id: str,
):
    """Mark a lesson as completed; tracks by lesson ID to prevent double-counting."""
    if not DJANGO_AVAILABLE:
        raise HTTPException(status_code=503, detail="Lesson service not available")

    user = await get_user_from_token(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    if Lesson is None:
        raise HTTPException(status_code=503, detail="Lesson service not available")
    lesson = await sync_to_async(Lesson.objects.filter(id=lesson_id).first)()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    try:
        progress, _ = await sync_to_async(UserProgress.objects.get_or_create)(user=user)
        current_completed = set(getattr(progress, "completed_lesson_ids", []) or [])

        if lesson_id in current_completed:
            return JSONResponse({
                "success": True,
                "message": "Already completed",
                "achievements_unlocked": [],
            })

        current_completed.add(lesson_id)
        progress.completed_lesson_ids = list(current_completed)
        progress.lessons_completed = len(current_completed)
        concepts_list = list(lesson.concepts) if lesson.concepts else []
        progress.concepts_learned += len(concepts_list)
        await sync_to_async(progress.save)()

        achievements_unlocked = []
        if progress.lessons_completed == 1:
            _, created = await sync_to_async(UserAchievement.objects.get_or_create)(
                user=user,
                achievement_type="first_lesson",
            )
            if created:
                achievements_unlocked.append("first_lesson")

        if progress.lessons_completed == 10:
            _, created = await sync_to_async(UserAchievement.objects.get_or_create)(
                user=user,
                achievement_type="lessons_10",
            )
            if created:
                achievements_unlocked.append("lessons_10")

        return JSONResponse({
            "success": True,
            "message": "Lesson completed",
            "achievements_unlocked": achievements_unlocked,
        })
    except Exception as e:
        logger.error("Progress update failed: %s", e)
        raise HTTPException(status_code=500, detail="Database sync failed")

