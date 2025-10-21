"""
Behavioral Analytics Service
============================

Implements AI-powered behavioral analytics to understand user patterns, preferences,
and predict future actions. This creates hyper-personalized experiences that adapt
in real-time to user behavior.

Key Features:
- User behavior pattern analysis
- Engagement prediction models
- Churn risk assessment
- Content preference learning
- Optimal timing prediction
- Personalization score calculation

Dependencies:
- advanced_ai_router: For AI-powered analysis
- ml_service: For machine learning models
- notification_service: For personalized notifications
"""

from __future__ import annotations

import asyncio
import json
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, TypedDict
from enum import Enum

from .advanced_ai_router import AdvancedAIRouter, get_advanced_ai_router
from .ml_service import MLService, get_ml_service
from .notification_service import NotificationService
from .ai_service import RequestType

logger = logging.getLogger(__name__)

# =============================================================================
# Enums and Types
# =============================================================================

class BehaviorType(str, Enum):
    """Types of user behaviors."""
    LOGIN = "login"
    LEARNING_SESSION = "learning_session"
    TRADING_ACTION = "trading_action"
    COMMUNITY_INTERACTION = "community_interaction"
    CONTENT_VIEW = "content_view"
    QUIZ_COMPLETION = "quiz_completion"
    GOAL_SETTING = "goal_setting"
    PROGRESS_SHARE = "progress_share"

class EngagementLevel(str, Enum):
    """User engagement levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class ChurnRisk(str, Enum):
    """Churn risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# =============================================================================
# Typed Payloads
# =============================================================================

class UserBehavior(TypedDict, total=False):
    """User behavior event."""
    behavior_id: str
    user_id: str
    behavior_type: str
    timestamp: str
    session_id: str
    duration: Optional[float]
    metadata: Dict[str, Any]
    context: Dict[str, Any]

class BehaviorPattern(TypedDict, total=False):
    """Identified behavior pattern."""
    pattern_id: str
    user_id: str
    pattern_type: str
    frequency: float
    confidence: float
    description: str
    triggers: List[str]
    predicted_actions: List[str]
    created_at: str

class EngagementProfile(TypedDict, total=False):
    """User engagement profile."""
    user_id: str
    engagement_level: str
    engagement_score: float
    preferred_content_types: List[str]
    optimal_session_duration: float
    best_engagement_times: List[str]
    learning_style: str
    interaction_preferences: Dict[str, Any]
    last_updated: str

class ChurnPrediction(TypedDict, total=False):
    """Churn risk prediction."""
    user_id: str
    churn_risk: str
    churn_probability: float
    risk_factors: List[str]
    intervention_recommendations: List[str]
    predicted_churn_date: Optional[str]
    confidence: float
    generated_at: str

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

class BehavioralAnalyticsService:
    """
    Behavioral Analytics Service for hyper-personalization.
    
    Core Functionality:
        - User behavior pattern analysis
        - Engagement prediction models
        - Churn risk assessment
        - Content preference learning
        - Optimal timing prediction
        - Personalization score calculation
    
    Design Notes:
        - All timestamps in UTC (ISO8601)
        - Real-time behavior analysis
        - Privacy-first approach
        - ML-driven insights
    """

    def __init__(
        self,
        ai_router: Optional[AdvancedAIRouter] = None,
        ml_service: Optional[MLService] = None,
        notification_service: Optional[NotificationService] = None,
    ) -> None:
        self.ai_router = ai_router or get_advanced_ai_router()
        self.ml_service = ml_service or get_ml_service()
        self.notification_service = notification_service or NotificationService()

    # -------------------------------------------------------------------------
    # Public API Methods
    # -------------------------------------------------------------------------

    async def track_behavior(
        self,
        user_id: str,
        behavior_type: str,
        *,
        session_id: Optional[str] = None,
        duration: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> UserBehavior:
        """
        Track a user behavior event.
        
        Args:
            user_id: ID of the user
            behavior_type: Type of behavior
            session_id: Optional session ID
            duration: Optional duration in seconds
            metadata: Optional behavior metadata
            context: Optional context information
            
        Returns:
            UserBehavior object
        """
        try:
            behavior_id = str(uuid.uuid4())
            
            behavior: UserBehavior = {
                "behavior_id": behavior_id,
                "user_id": user_id,
                "behavior_type": behavior_type,
                "timestamp": _now_iso_utc(),
                "session_id": session_id or f"session_{user_id}_{int(datetime.now().timestamp())}",
                "duration": duration,
                "metadata": metadata or {},
                "context": context or {}
            }
            
            # Trigger real-time analysis
            await self._analyze_behavior_pattern(behavior)
            
            logger.info(f"Tracked behavior: {behavior_type} for user {user_id}")
            return behavior
            
        except Exception as e:
            logger.error(f"Error tracking behavior: {e}")
            raise

    async def analyze_engagement_profile(
        self,
        user_id: str,
        *,
        time_period: str = "30d",
    ) -> EngagementProfile:
        """
        Analyze user engagement profile.
        
        Args:
            user_id: ID of the user
            time_period: Time period for analysis (7d, 30d, 90d)
            
        Returns:
            EngagementProfile object
        """
        try:
            # In a real system, this would analyze actual behavior data
            # For now, we'll simulate engagement analysis
            
            # Simulate engagement analysis using AI
            engagement_analysis = await self._ai_analyze_engagement(user_id, time_period)
            
            profile: EngagementProfile = {
                "user_id": user_id,
                "engagement_level": engagement_analysis.get("engagement_level", "medium"),
                "engagement_score": engagement_analysis.get("engagement_score", 0.7),
                "preferred_content_types": engagement_analysis.get("preferred_content_types", ["learning", "trading"]),
                "optimal_session_duration": engagement_analysis.get("optimal_session_duration", 25.0),
                "best_engagement_times": engagement_analysis.get("best_engagement_times", ["09:00", "19:00"]),
                "learning_style": engagement_analysis.get("learning_style", "visual"),
                "interaction_preferences": engagement_analysis.get("interaction_preferences", {}),
                "last_updated": _now_iso_utc()
            }
            
            logger.info(f"Analyzed engagement profile for user {user_id}: {profile['engagement_level']}")
            return profile
            
        except Exception as e:
            logger.error(f"Error analyzing engagement profile: {e}")
            raise

    async def predict_churn_risk(
        self,
        user_id: str,
        *,
        lookback_days: int = 30,
    ) -> ChurnPrediction:
        """
        Predict user churn risk.
        
        Args:
            user_id: ID of the user
            lookback_days: Days to look back for analysis
            
        Returns:
            ChurnPrediction object
        """
        try:
            # Simulate churn prediction using AI
            churn_analysis = await self._ai_predict_churn(user_id, lookback_days)
            
            prediction: ChurnPrediction = {
                "user_id": user_id,
                "churn_risk": churn_analysis.get("churn_risk", "low"),
                "churn_probability": churn_analysis.get("churn_probability", 0.15),
                "risk_factors": churn_analysis.get("risk_factors", []),
                "intervention_recommendations": churn_analysis.get("intervention_recommendations", []),
                "predicted_churn_date": churn_analysis.get("predicted_churn_date"),
                "confidence": churn_analysis.get("confidence", 0.8),
                "generated_at": _now_iso_utc()
            }
            
            # Trigger intervention if high risk
            if prediction["churn_risk"] in ["high", "critical"]:
                await self._trigger_churn_intervention(prediction)
            
            logger.info(f"Predicted churn risk for user {user_id}: {prediction['churn_risk']}")
            return prediction
            
        except Exception as e:
            logger.error(f"Error predicting churn risk: {e}")
            raise

    async def get_personalization_score(
        self,
        user_id: str,
        content_type: str,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate personalization score for content.
        
        Args:
            user_id: ID of the user
            content_type: Type of content
            context: Optional context information
            
        Returns:
            Personalization score and recommendations
        """
        try:
            # Get user engagement profile
            engagement_profile = await self.analyze_engagement_profile(user_id)
            
            # Calculate personalization score
            score = await self._calculate_personalization_score(
                user_id, content_type, engagement_profile, context
            )
            
            result = {
                "user_id": user_id,
                "content_type": content_type,
                "personalization_score": score.get("score", 0.7),
                "recommendations": score.get("recommendations", []),
                "optimal_timing": score.get("optimal_timing"),
                "content_preferences": score.get("content_preferences", {}),
                "generated_at": _now_iso_utc()
            }
            
            logger.info(f"Calculated personalization score for user {user_id}: {result['personalization_score']}")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating personalization score: {e}")
            raise

    async def identify_behavior_patterns(
        self,
        user_id: str,
        *,
        pattern_types: Optional[List[str]] = None,
    ) -> List[BehaviorPattern]:
        """
        Identify behavior patterns for a user.
        
        Args:
            user_id: ID of the user
            pattern_types: Optional specific pattern types to analyze
            
        Returns:
            List of identified behavior patterns
        """
        try:
            # Simulate pattern identification using AI
            patterns = await self._ai_identify_patterns(user_id, pattern_types)
            
            behavior_patterns = []
            for pattern_data in patterns:
                pattern: BehaviorPattern = {
                    "pattern_id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "pattern_type": pattern_data.get("pattern_type", "general"),
                    "frequency": pattern_data.get("frequency", 0.5),
                    "confidence": pattern_data.get("confidence", 0.8),
                    "description": pattern_data.get("description", ""),
                    "triggers": pattern_data.get("triggers", []),
                    "predicted_actions": pattern_data.get("predicted_actions", []),
                    "created_at": _now_iso_utc()
                }
                behavior_patterns.append(pattern)
            
            logger.info(f"Identified {len(behavior_patterns)} behavior patterns for user {user_id}")
            return behavior_patterns
            
        except Exception as e:
            logger.error(f"Error identifying behavior patterns: {e}")
            raise

    # -------------------------------------------------------------------------
    # Private Helper Methods
    # -------------------------------------------------------------------------

    async def _analyze_behavior_pattern(
        self,
        behavior: UserBehavior
    ) -> None:
        """Analyze behavior pattern in real-time."""
        try:
            # In a real system, this would update ML models and trigger actions
            logger.debug(f"Analyzing behavior pattern: {behavior['behavior_type']}")
            
        except Exception as e:
            logger.error(f"Error analyzing behavior pattern: {e}")

    async def _ai_analyze_engagement(
        self,
        user_id: str,
        time_period: str
    ) -> Dict[str, Any]:
        """Use AI to analyze user engagement."""
        try:
            prompt = f"""
            Analyze user engagement for user {user_id} over {time_period}.
            
            Consider:
            - Session frequency and duration
            - Content interaction patterns
            - Learning progress and completion rates
            - Community participation
            - Feature usage patterns
            
            Return a JSON response with:
            {{
                "engagement_level": "low|medium|high|very_high",
                "engagement_score": 0.0-1.0,
                "preferred_content_types": ["type1", "type2"],
                "optimal_session_duration": minutes,
                "best_engagement_times": ["HH:MM", "HH:MM"],
                "learning_style": "visual|auditory|kinesthetic|reading",
                "interaction_preferences": {{"key": "value"}}
            }}
            """
            
            ai_response = await self.ai_router.route_request(
                request_type=RequestType.GENERAL_CHAT,
                prompt=prompt,
                user_id=user_id,
                model_preference="claude-3-5-sonnet",
                temperature=0.3,
                max_tokens=500
            )
            
            return _safe_json_loads(ai_response) or self._default_engagement_analysis()
            
        except Exception as e:
            logger.error(f"Error in AI engagement analysis: {e}")
            return self._default_engagement_analysis()

    async def _ai_predict_churn(
        self,
        user_id: str,
        lookback_days: int
    ) -> Dict[str, Any]:
        """Use AI to predict churn risk."""
        try:
            prompt = f"""
            Predict churn risk for user {user_id} based on {lookback_days} days of data.
            
            Consider:
            - Login frequency decline
            - Session duration reduction
            - Feature usage drop-off
            - Community engagement decrease
            - Learning progress stagnation
            
            Return a JSON response with:
            {{
                "churn_risk": "low|medium|high|critical",
                "churn_probability": 0.0-1.0,
                "risk_factors": ["factor1", "factor2"],
                "intervention_recommendations": ["action1", "action2"],
                "predicted_churn_date": "YYYY-MM-DD" or null,
                "confidence": 0.0-1.0
            }}
            """
            
            ai_response = await self.ai_router.route_request(
                request_type=RequestType.GENERAL_CHAT,
                prompt=prompt,
                user_id=user_id,
                model_preference="claude-3-5-sonnet",
                temperature=0.2,
                max_tokens=400
            )
            
            return _safe_json_loads(ai_response) or self._default_churn_prediction()
            
        except Exception as e:
            logger.error(f"Error in AI churn prediction: {e}")
            return self._default_churn_prediction()

    async def _calculate_personalization_score(
        self,
        user_id: str,
        content_type: str,
        engagement_profile: EngagementProfile,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate personalization score for content."""
        try:
            # Simulate personalization score calculation
            base_score = 0.7
            
            # Adjust based on engagement profile
            if content_type in engagement_profile.get("preferred_content_types", []):
                base_score += 0.2
            
            # Adjust based on engagement level
            engagement_multiplier = {
                "low": 0.8,
                "medium": 1.0,
                "high": 1.2,
                "very_high": 1.3
            }
            base_score *= engagement_multiplier.get(engagement_profile.get("engagement_level", "medium"), 1.0)
            
            return {
                "score": min(base_score, 1.0),
                "recommendations": [
                    f"Optimize for {engagement_profile.get('learning_style', 'visual')} learning style",
                    f"Best engagement time: {engagement_profile.get('best_engagement_times', ['09:00'])[0]}"
                ],
                "optimal_timing": engagement_profile.get("best_engagement_times", ["09:00"])[0],
                "content_preferences": engagement_profile.get("interaction_preferences", {})
            }
            
        except Exception as e:
            logger.error(f"Error calculating personalization score: {e}")
            return {"score": 0.7, "recommendations": [], "optimal_timing": "09:00", "content_preferences": {}}

    async def _ai_identify_patterns(
        self,
        user_id: str,
        pattern_types: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Use AI to identify behavior patterns."""
        try:
            prompt = f"""
            Identify behavior patterns for user {user_id}.
            {f"Focus on pattern types: {pattern_types}" if pattern_types else ""}
            
            Look for:
            - Daily/weekly usage patterns
            - Content preference patterns
            - Learning behavior patterns
            - Engagement timing patterns
            - Feature usage patterns
            
            Return a JSON array of patterns:
            [
                {{
                    "pattern_type": "usage_timing|content_preference|learning_style",
                    "frequency": 0.0-1.0,
                    "confidence": 0.0-1.0,
                    "description": "Pattern description",
                    "triggers": ["trigger1", "trigger2"],
                    "predicted_actions": ["action1", "action2"]
                }}
            ]
            """
            
            ai_response = await self.ai_router.route_request(
                request_type=RequestType.GENERAL_CHAT,
                prompt=prompt,
                user_id=user_id,
                model_preference="claude-3-5-sonnet",
                temperature=0.4,
                max_tokens=600
            )
            
            patterns = _safe_json_loads(ai_response)
            return patterns if isinstance(patterns, list) else self._default_behavior_patterns()
            
        except Exception as e:
            logger.error(f"Error in AI pattern identification: {e}")
            return self._default_behavior_patterns()

    async def _trigger_churn_intervention(
        self,
        prediction: ChurnPrediction
    ) -> None:
        """Trigger churn intervention actions."""
        try:
            # In a real system, this would trigger personalized interventions
            logger.info(f"Triggering churn intervention for user {prediction['user_id']}")
            
            # Could trigger notifications, personalized content, etc.
            
        except Exception as e:
            logger.error(f"Error triggering churn intervention: {e}")

    def _default_engagement_analysis(self) -> Dict[str, Any]:
        """Default engagement analysis for fallback."""
        return {
            "engagement_level": "medium",
            "engagement_score": 0.7,
            "preferred_content_types": ["learning", "trading"],
            "optimal_session_duration": 25.0,
            "best_engagement_times": ["09:00", "19:00"],
            "learning_style": "visual",
            "interaction_preferences": {"notifications": True, "community": True}
        }

    def _default_churn_prediction(self) -> Dict[str, Any]:
        """Default churn prediction for fallback."""
        return {
            "churn_risk": "low",
            "churn_probability": 0.15,
            "risk_factors": [],
            "intervention_recommendations": ["Continue current engagement"],
            "predicted_churn_date": None,
            "confidence": 0.8
        }

    def _default_behavior_patterns(self) -> List[Dict[str, Any]]:
        """Default behavior patterns for fallback."""
        return [
            {
                "pattern_type": "usage_timing",
                "frequency": 0.6,
                "confidence": 0.7,
                "description": "User typically engages in morning sessions",
                "triggers": ["morning_time", "weekday"],
                "predicted_actions": ["morning_notification", "morning_content"]
            }
        ]

# =============================================================================
# Singleton Instance
# =============================================================================

behavioral_analytics_service = BehavioralAnalyticsService()
