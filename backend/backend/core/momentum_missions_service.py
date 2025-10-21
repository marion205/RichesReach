"""
Momentum Missions Service
========================

Implements the gamified daily challenge system that builds 21-day habit loops.
This is a key retention feature that creates daily engagement through progressive challenges.

Key Features:
- Daily "Momentum Missions" with progressive difficulty
- Recovery rituals for missed days
- Streak multipliers and achievement badges
- 21-day habit loop formation
- Social proof and community elements

Dependencies:
- advanced_ai_router: For AI-generated mission content
- ml_service: For regime-based mission adaptation
- genai_education_service: For user personalization
"""

from __future__ import annotations

import asyncio
import json
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, TypedDict
from enum import Enum

from .advanced_ai_router import get_advanced_ai_router, AIRequest, AIResponse, RequestType, AIModel
from .ml_service import MLService
from .genai_education_service import GenAIEducationService, UserLearningProfile, DifficultyLevel

logger = logging.getLogger(__name__)

# =============================================================================
# Enums and Types
# =============================================================================

class MissionType(str, Enum):
    """Types of momentum missions."""
    QUIZ = "quiz"
    SIMULATION = "simulation"
    ANALYSIS = "analysis"
    LEARNING = "learning"
    PRACTICE = "practice"

class MissionDifficulty(str, Enum):
    """Mission difficulty levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class MissionStatus(str, Enum):
    """Mission completion status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"

# =============================================================================
# Typed Payloads
# =============================================================================

class MomentumMission(TypedDict, total=False):
    """Individual momentum mission."""
    mission_id: str
    user_id: str
    day_number: int
    mission_type: str
    title: str
    description: str
    difficulty: str
    estimated_duration: int  # minutes
    content: Dict[str, Any]
    rewards: Dict[str, Any]
    streak_multiplier: float
    created_at: str  # ISO8601 (UTC)
    due_at: str  # ISO8601 (UTC)

class RecoveryRitual(TypedDict, total=False):
    """Recovery ritual for missed missions."""
    ritual_id: str
    user_id: str
    missed_day: int
    ritual_type: str
    title: str
    description: str
    content: Dict[str, Any]
    streak_recovery: bool
    created_at: str  # ISO8601 (UTC)

class UserProgress(TypedDict, total=False):
    """User's momentum mission progress."""
    user_id: str
    current_streak: int
    longest_streak: int
    total_missions_completed: int
    current_mission: Optional[MomentumMission]
    available_recovery: Optional[RecoveryRitual]
    achievements: List[Dict[str, Any]]
    streak_multiplier: float
    last_activity: str  # ISO8601 (UTC)

# =============================================================================
# Utility Functions
# =============================================================================

def _now_iso_utc() -> str:
    """Get current UTC timestamp in ISO8601 format."""
    return datetime.now(timezone.utc).isoformat()

def _safe_json_loads(s: str) -> Optional[Dict[str, Any]]:
    """Safely parse JSON string, returning None on failure."""
    try:
        return json.loads(s)
    except Exception:
        return None

# =============================================================================
# Main Service Class
# =============================================================================

class MomentumMissionsService:
    """
    Momentum Missions Service for gamified daily challenges.
    
    Core Functionality:
        - Daily progressive challenges (Day 1: RSI quiz, Day 7: Trade simulation)
        - Recovery rituals for missed days
        - Streak multipliers and achievement system
        - 21-day habit loop formation
        - Regime-adaptive mission content
    
    Design Notes:
        - All timestamps in UTC (ISO8601)
        - Progressive difficulty over 21 days
        - Regime-specific mission content
        - Social proof and community elements
    """

    # Configuration Defaults
    DEFAULT_MISSION_TOKENS = 600
    DEFAULT_TIMEOUT_SECONDS = 20
    HABIT_LOOP_DAYS = 21
    STREAK_MULTIPLIER_BASE = 1.0
    STREAK_MULTIPLIER_INCREMENT = 0.1

    def __init__(
        self,
        ai_router: Optional["AdvancedAIRouter"] = None,
        ml_service: Optional[MLService] = None,
        education_service: Optional[GenAIEducationService] = None,
        *,
        default_model: AIModel = AIModel.GPT_4O,
        request_timeout_s: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.ai_router = ai_router or get_advanced_ai_router()
        self.ml_service = ml_service or MLService()
        self.education_service = education_service or GenAIEducationService()
        self.default_model = default_model
        self.request_timeout_s = request_timeout_s

    # -------------------------------------------------------------------------
    # Public API Methods
    # -------------------------------------------------------------------------

    async def get_user_progress(
        self,
        user_id: str,
        *,
        include_current_mission: bool = True,
    ) -> UserProgress:
        """
        Get user's momentum mission progress and current status.
        
        Args:
            user_id: User identifier
            include_current_mission: Whether to include current mission details
            
        Returns:
            UserProgress with streak, achievements, and current mission
        """
        try:
            # In production, this would fetch from database
            # For now, we'll generate mock progress
            current_streak = 3  # Mock current streak
            longest_streak = 7  # Mock longest streak
            total_completed = 15  # Mock total completed
            
            # Calculate streak multiplier
            streak_multiplier = self.STREAK_MULTIPLIER_BASE + (current_streak * self.STREAK_MULTIPLIER_INCREMENT)
            
            # Get current mission if requested
            current_mission = None
            if include_current_mission and current_streak < self.HABIT_LOOP_DAYS:
                current_mission = await self._generate_current_mission(user_id, current_streak + 1)
            
            # Get available recovery ritual if streak was broken
            available_recovery = None
            if current_streak == 0:
                available_recovery = await self._generate_recovery_ritual(user_id)
            
            # Generate achievements
            achievements = self._generate_achievements(current_streak, total_completed)
            
            progress: UserProgress = {
                "user_id": user_id,
                "current_streak": current_streak,
                "longest_streak": longest_streak,
                "total_missions_completed": total_completed,
                "current_mission": current_mission,
                "available_recovery": available_recovery,
                "achievements": achievements,
                "streak_multiplier": streak_multiplier,
                "last_activity": _now_iso_utc(),
            }
            
            logger.info(f"Retrieved momentum mission progress for user {user_id}: {current_streak} day streak")
            return progress
            
        except Exception as e:
            logger.error(f"Error getting user progress: {e}")
            raise

    async def generate_daily_mission(
        self,
        user_id: str,
        day_number: int,
        *,
        market_data: Optional[Dict[str, Any]] = None,
        max_tokens: int = DEFAULT_MISSION_TOKENS,
        model: Optional[AIModel] = None,
    ) -> MomentumMission:
        """
        Generate a daily momentum mission for the specified day.
        
        This creates progressive challenges that build over 21 days:
        - Days 1-7: Basic concepts and quizzes
        - Days 8-14: Intermediate analysis and simulations
        - Days 15-21: Advanced strategies and real-world application
        
        Args:
            user_id: User identifier
            day_number: Day number in the 21-day cycle (1-21)
            market_data: Current market data for regime adaptation
            max_tokens: Maximum tokens for AI response
            model: AI model to use for generation
            
        Returns:
            MomentumMission with progressive challenge content
        """
        try:
            # Validate day number
            if day_number < 1 or day_number > self.HABIT_LOOP_DAYS:
                raise ValueError(f"Day number must be between 1 and {self.HABIT_LOOP_DAYS}")
            
            # Get current market regime
            regime_prediction = self.ml_service.predict_market_regime(market_data or {})
            current_regime = regime_prediction.get('regime', 'sideways_consolidation')
            regime_confidence = regime_prediction.get('confidence', 0.5)
            
            # Get user learning profile
            user_profile = await self.education_service.get_user_learning_profile(user_id)
            base_difficulty = user_profile.get('preferred_difficulty', DifficultyLevel.INTERMEDIATE)
            
            # Determine mission type and difficulty based on day
            mission_type, difficulty = self._get_mission_progression(day_number, base_difficulty)
            
            # Create regime context
            regime_context = {
                'current_regime': current_regime,
                'regime_confidence': regime_confidence,
                'regime_description': self._get_regime_description(current_regime),
                'day_number': day_number,
                'mission_type': mission_type.value,
                'difficulty': difficulty.value,
                'user_difficulty': base_difficulty.value
            }
            
            # Generate mission content using AI
            prompt = self._build_mission_prompt(regime_context, user_profile)
            
            request = AIRequest(
                prompt=prompt,
                max_tokens=max_tokens,
                model=model or self.default_model,
                request_type=RequestType.GENERAL_CHAT,
                temperature=0.8,
            )
            
            resp = await self.ai_router.route_request(request)
            if not resp or not resp.response:
                raise ValueError("Failed to generate momentum mission")
            
            # Parse and structure the response
            parsed = _safe_json_loads(resp.response)
            if not parsed:
                # Fallback to structured generation
                parsed = await self._generate_fallback_mission(regime_context)
            
            # Calculate rewards and streak multiplier
            rewards = self._calculate_mission_rewards(day_number, difficulty)
            streak_multiplier = self.STREAK_MULTIPLIER_BASE + (day_number * self.STREAK_MULTIPLIER_INCREMENT)
            
            # Build mission payload
            mission_id = str(uuid.uuid4())
            due_time = datetime.now(timezone.utc) + timedelta(days=1)
            
            mission: MomentumMission = {
                "mission_id": mission_id,
                "user_id": user_id,
                "day_number": day_number,
                "mission_type": mission_type.value,
                "title": parsed.get('title', f'Day {day_number} Mission'),
                "description": parsed.get('description', 'Complete your daily momentum mission'),
                "difficulty": difficulty.value,
                "estimated_duration": parsed.get('estimated_duration', 5),
                "content": parsed.get('content', {}),
                "rewards": rewards,
                "streak_multiplier": streak_multiplier,
                "created_at": _now_iso_utc(),
                "due_at": due_time.isoformat(),
            }
            
            logger.info(f"Generated momentum mission for user {user_id}, day {day_number}: {mission_type.value}")
            return mission
            
        except Exception as e:
            logger.error(f"Error generating momentum mission: {e}")
            raise

    async def generate_recovery_ritual(
        self,
        user_id: str,
        missed_day: int,
        *,
        max_tokens: int = 400,
        model: Optional[AIModel] = None,
    ) -> RecoveryRitual:
        """
        Generate a recovery ritual for a missed mission.
        
        Recovery rituals help users get back on track after missing a day,
        providing a shorter, easier challenge to rebuild momentum.
        
        Args:
            user_id: User identifier
            missed_day: The day number that was missed
            max_tokens: Maximum tokens for AI response
            model: AI model to use for generation
            
        Returns:
            RecoveryRitual with easy challenge to rebuild streak
        """
        try:
            # Generate recovery ritual content
            prompt = self._build_recovery_prompt(missed_day)
            
            request = AIRequest(
                prompt=prompt,
                max_tokens=max_tokens,
                model=model or self.default_model,
                request_type=RequestType.GENERAL_CHAT,
                temperature=0.7,
            )
            
            resp = await self.ai_router.route_request(request)
            if not resp or not resp.response:
                raise ValueError("Failed to generate recovery ritual")
            
            # Parse response
            parsed = _safe_json_loads(resp.response)
            if not parsed:
                parsed = await self._generate_fallback_recovery(missed_day)
            
            # Build recovery ritual payload
            ritual_id = str(uuid.uuid4())
            
            ritual: RecoveryRitual = {
                "ritual_id": ritual_id,
                "user_id": user_id,
                "missed_day": missed_day,
                "ritual_type": "recovery",
                "title": parsed.get('title', 'Recovery Ritual'),
                "description": parsed.get('description', 'Get back on track with this quick challenge'),
                "content": parsed.get('content', {}),
                "streak_recovery": True,
                "created_at": _now_iso_utc(),
            }
            
            logger.info(f"Generated recovery ritual for user {user_id}, missed day {missed_day}")
            return ritual
            
        except Exception as e:
            logger.error(f"Error generating recovery ritual: {e}")
            raise

    # -------------------------------------------------------------------------
    # Private Helper Methods
    # -------------------------------------------------------------------------

    def _get_mission_progression(self, day_number: int, base_difficulty: DifficultyLevel) -> tuple[MissionType, MissionDifficulty]:
        """Get mission type and difficulty based on day number."""
        if day_number <= 7:
            # Week 1: Basic concepts
            mission_type = MissionType.QUIZ
            difficulty = MissionDifficulty.BEGINNER
        elif day_number <= 14:
            # Week 2: Intermediate analysis
            mission_type = MissionType.ANALYSIS
            difficulty = MissionDifficulty.INTERMEDIATE
        elif day_number <= 21:
            # Week 3: Advanced strategies
            mission_type = MissionType.SIMULATION
            difficulty = MissionDifficulty.ADVANCED
        else:
            # Beyond 21 days: Expert level
            mission_type = MissionType.PRACTICE
            difficulty = MissionDifficulty.EXPERT
        
        return mission_type, difficulty

    def _get_regime_description(self, regime: str) -> str:
        """Get human-readable description of market regime."""
        descriptions = {
            'early_bull_market': 'Strong growth phase with low volatility and rising prices',
            'late_bull_market': 'High growth phase with increasing volatility and potential overvaluation',
            'correction': 'Temporary pullback in an overall bull market trend',
            'bear_market': 'Sustained decline with high volatility and negative sentiment',
            'sideways_consolidation': 'Range-bound market with low volatility and uncertain direction',
            'high_volatility': 'Uncertain market conditions with elevated volatility',
            'recovery': 'Market bouncing back from a previous decline',
            'bubble_formation': 'Excessive optimism with high valuations and speculation'
        }
        return descriptions.get(regime, 'Uncertain market conditions')

    def _build_mission_prompt(self, regime_context: Dict[str, Any], user_profile: Dict[str, Any]) -> str:
        """Build a comprehensive prompt for momentum mission generation."""
        day_number = regime_context['day_number']
        mission_type = regime_context['mission_type']
        difficulty = regime_context['difficulty']
        regime = regime_context['current_regime']
        
        return f"""
You are a financial education expert creating a Day {day_number} momentum mission for a {regime_context['user_difficulty']} level investor.

MISSION TYPE: {mission_type.upper()}
DIFFICULTY: {difficulty.upper()}
MARKET REGIME: {regime.replace('_', ' ').title()}

Create a progressive challenge that:
1. Builds on previous days' learning
2. Is appropriate for day {day_number} of a 21-day habit loop
3. Adapts to the current {regime} market regime
4. Takes 3-7 minutes to complete
5. Provides immediate feedback and learning

Format your response as JSON:
{{
    "title": "Day {day_number}: [Specific Challenge Title]",
    "description": "Brief description of what the user will learn/do",
    "estimated_duration": 5,
    "content": {{
        "challenge": "Specific task or question",
        "instructions": "Step-by-step guidance",
        "learning_objectives": ["What they'll learn"],
        "regime_context": "How this relates to {regime} markets",
        "success_criteria": "How to know they succeeded"
    }}
}}

Make it engaging, educational, and progressively challenging.
"""

    def _build_recovery_prompt(self, missed_day: int) -> str:
        """Build a prompt for recovery ritual generation."""
        return f"""
You are a financial education expert creating a recovery ritual for someone who missed Day {missed_day} of their momentum mission.

Create a quick, easy challenge that:
1. Takes 2-3 minutes to complete
2. Helps rebuild momentum and confidence
3. Relates to the missed day's content
4. Provides encouragement and motivation

Format your response as JSON:
{{
    "title": "Recovery Ritual: [Encouraging Title]",
    "description": "Quick challenge to get back on track",
    "content": {{
        "challenge": "Simple, achievable task",
        "encouragement": "Motivational message",
        "next_steps": "How to continue the streak"
    }}
}}

Make it supportive and confidence-building.
"""

    def _calculate_mission_rewards(self, day_number: int, difficulty: MissionDifficulty) -> Dict[str, Any]:
        """Calculate rewards for mission completion."""
        base_points = 10
        difficulty_multiplier = {
            MissionDifficulty.BEGINNER: 1.0,
            MissionDifficulty.INTERMEDIATE: 1.5,
            MissionDifficulty.ADVANCED: 2.0,
            MissionDifficulty.EXPERT: 2.5
        }
        
        points = int(base_points * difficulty_multiplier[difficulty] * (1 + day_number * 0.1))
        
        return {
            "points": points,
            "badges": self._get_mission_badges(day_number),
            "streak_bonus": day_number * 2,
            "experience": points * 2
        }

    def _get_mission_badges(self, day_number: int) -> List[str]:
        """Get badges for mission completion."""
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
        
        return badges

    def _generate_achievements(self, current_streak: int, total_completed: int) -> List[Dict[str, Any]]:
        """Generate user achievements based on progress."""
        achievements = []
        
        if current_streak >= 7:
            achievements.append({
                "id": "week_streak",
                "name": "Week Warrior",
                "description": "Maintained a 7-day streak",
                "icon": "🔥",
                "unlocked_at": _now_iso_utc()
            })
        
        if current_streak >= 21:
            achievements.append({
                "id": "habit_hero",
                "name": "Habit Hero",
                "description": "Completed the full 21-day habit loop",
                "icon": "🏆",
                "unlocked_at": _now_iso_utc()
            })
        
        if total_completed >= 50:
            achievements.append({
                "id": "dedication",
                "name": "Dedication Master",
                "description": "Completed 50+ missions",
                "icon": "💎",
                "unlocked_at": _now_iso_utc()
            })
        
        return achievements

    async def _generate_current_mission(self, user_id: str, day_number: int) -> MomentumMission:
        """Generate current mission for user progress."""
        return await self.generate_daily_mission(user_id, day_number)

    async def _generate_recovery_ritual(self, user_id: str) -> RecoveryRitual:
        """Generate recovery ritual for user progress."""
        return await self.generate_recovery_ritual(user_id, 1)  # Mock missed day

    async def _generate_fallback_mission(self, regime_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback mission when AI fails."""
        day_number = regime_context['day_number']
        mission_type = regime_context['mission_type']
        regime = regime_context['current_regime']
        
        return {
            "title": f"Day {day_number}: {mission_type.title()} Challenge",
            "description": f"Complete this {mission_type} challenge adapted for {regime} market conditions",
            "estimated_duration": 5,
            "content": {
                "challenge": f"Apply your knowledge to {regime.replace('_', ' ')} market conditions",
                "instructions": "Think through the challenge step by step",
                "learning_objectives": ["Market analysis", "Risk management", "Strategy application"],
                "regime_context": f"This challenge is adapted for {regime} market conditions",
                "success_criteria": "Complete the challenge with thoughtful analysis"
            }
        }

    async def _generate_fallback_recovery(self, missed_day: int) -> Dict[str, Any]:
        """Generate fallback recovery ritual when AI fails."""
        return {
            "title": "Recovery Ritual: Quick Win",
            "description": "A simple challenge to get back on track",
            "content": {
                "challenge": "Review one key financial concept",
                "encouragement": "Every expert was once a beginner. You've got this!",
                "next_steps": "Complete this quick challenge to rebuild your momentum"
            }
        }

# =============================================================================
# Singleton Instance
# =============================================================================

momentum_missions_service = MomentumMissionsService()
