"""
Dynamic Content Adaptation Service
==================================

Implements real-time content personalization that adapts to user behavior,
preferences, and context. This creates hyper-personalized experiences that
evolve with the user's journey.

Key Features:
- Real-time content adaptation
- Context-aware personalization
- A/B testing integration
- Content performance optimization
- Dynamic difficulty adjustment
- Personalized recommendations

Dependencies:
- behavioral_analytics_service: For user behavior insights
- advanced_ai_router: For AI-powered content generation
- ml_service: For recommendation algorithms
"""

from __future__ import annotations

import asyncio
import json
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, TypedDict
from enum import Enum

from .behavioral_analytics_service import BehavioralAnalyticsService
from .advanced_ai_router import AdvancedAIRouter, get_advanced_ai_router
from .ml_service import MLService, get_ml_service
from .ai_service import RequestType

logger = logging.getLogger(__name__)

# =============================================================================
# Enums and Types
# =============================================================================

class ContentType(str, Enum):
    """Types of content."""
    LEARNING_MODULE = "learning_module"
    QUIZ = "quiz"
    TRADING_SIGNAL = "trading_signal"
    MARKET_COMMENTARY = "market_commentary"
    COMMUNITY_POST = "community_post"
    NOTIFICATION = "notification"
    CHALLENGE = "challenge"

class AdaptationType(str, Enum):
    """Types of content adaptation."""
    DIFFICULTY = "difficulty"
    LENGTH = "length"
    TONE = "tone"
    FORMAT = "format"
    TIMING = "timing"
    PERSONALIZATION = "personalization"

class ContentPerformance(str, Enum):
    """Content performance levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXCELLENT = "excellent"

# =============================================================================
# Typed Payloads
# =============================================================================

class ContentAdaptation(TypedDict, total=False):
    """Content adaptation result."""
    adaptation_id: str
    user_id: str
    original_content: Dict[str, Any]
    adapted_content: Dict[str, Any]
    adaptation_type: str
    adaptation_reason: str
    confidence: float
    performance_prediction: str
    created_at: str

class PersonalizedContent(TypedDict, total=False):
    """Personalized content."""
    content_id: str
    user_id: str
    content_type: str
    title: str
    content: str
    metadata: Dict[str, Any]
    personalization_factors: List[str]
    adaptation_score: float
    created_at: str

class ContentRecommendation(TypedDict, total=False):
    """Content recommendation."""
    recommendation_id: str
    user_id: str
    content_type: str
    title: str
    description: str
    relevance_score: float
    confidence: float
    reasoning: str
    created_at: str

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

class DynamicContentService:
    """
    Dynamic Content Adaptation Service for hyper-personalization.
    
    Core Functionality:
        - Real-time content adaptation
        - Context-aware personalization
        - A/B testing integration
        - Content performance optimization
        - Dynamic difficulty adjustment
        - Personalized recommendations
    
    Design Notes:
        - All timestamps in UTC (ISO8601)
        - Real-time adaptation
        - Performance-driven optimization
        - Privacy-first approach
    """

    def __init__(
        self,
        behavioral_analytics: Optional[BehavioralAnalyticsService] = None,
        ai_router: Optional[AdvancedAIRouter] = None,
        ml_service: Optional[MLService] = None,
    ) -> None:
        self.behavioral_analytics = behavioral_analytics or BehavioralAnalyticsService()
        self.ai_router = ai_router or get_advanced_ai_router()
        self.ml_service = ml_service or get_ml_service()

    # -------------------------------------------------------------------------
    # Public API Methods
    # -------------------------------------------------------------------------

    async def adapt_content(
        self,
        user_id: str,
        content_type: str,
        original_content: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
        adaptation_types: Optional[List[str]] = None,
    ) -> ContentAdaptation:
        """
        Adapt content for a specific user.
        
        Args:
            user_id: ID of the user
            content_type: Type of content
            original_content: Original content to adapt
            context: Optional context information
            adaptation_types: Optional specific adaptation types
            
        Returns:
            ContentAdaptation object
        """
        try:
            # Get user behavior insights
            engagement_profile = await self.behavioral_analytics.analyze_engagement_profile(user_id)
            personalization_score = await self.behavioral_analytics.get_personalization_score(
                user_id, content_type, context
            )
            
            # Generate adapted content using AI
            adapted_content = await self._ai_adapt_content(
                user_id, content_type, original_content, engagement_profile, personalization_score, context
            )
            
            adaptation: ContentAdaptation = {
                "adaptation_id": str(uuid.uuid4()),
                "user_id": user_id,
                "original_content": original_content,
                "adapted_content": adapted_content,
                "adaptation_type": "comprehensive",
                "adaptation_reason": f"Personalized for {engagement_profile.get('learning_style', 'visual')} learner",
                "confidence": personalization_score.get("personalization_score", 0.7),
                "performance_prediction": self._predict_performance(adapted_content, engagement_profile),
                "created_at": _now_iso_utc()
            }
            
            logger.info(f"Adapted content for user {user_id}: {content_type}")
            return adaptation
            
        except Exception as e:
            logger.error(f"Error adapting content: {e}")
            raise

    async def generate_personalized_content(
        self,
        user_id: str,
        content_type: str,
        topic: str,
        *,
        length_preference: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> PersonalizedContent:
        """
        Generate personalized content for a user.
        
        Args:
            user_id: ID of the user
            content_type: Type of content to generate
            topic: Content topic
            length_preference: Optional length preference
            difficulty_level: Optional difficulty level
            context: Optional context information
            
        Returns:
            PersonalizedContent object
        """
        try:
            # Get user preferences and behavior
            engagement_profile = await self.behavioral_analytics.analyze_engagement_profile(user_id)
            personalization_score = await self.behavioral_analytics.get_personalization_score(
                user_id, content_type, context
            )
            
            # Generate personalized content using AI
            content = await self._ai_generate_personalized_content(
                user_id, content_type, topic, engagement_profile, personalization_score,
                length_preference, difficulty_level, context
            )
            
            personalized_content: PersonalizedContent = {
                "content_id": str(uuid.uuid4()),
                "user_id": user_id,
                "content_type": content_type,
                "title": content.get("title", f"Personalized {content_type}"),
                "content": content.get("content", ""),
                "metadata": content.get("metadata", {}),
                "personalization_factors": [
                    f"learning_style_{engagement_profile.get('learning_style', 'visual')}",
                    f"engagement_level_{engagement_profile.get('engagement_level', 'medium')}",
                    f"optimal_duration_{engagement_profile.get('optimal_session_duration', 25)}min"
                ],
                "adaptation_score": personalization_score.get("personalization_score", 0.7),
                "created_at": _now_iso_utc()
            }
            
            logger.info(f"Generated personalized content for user {user_id}: {content_type}")
            return personalized_content
            
        except Exception as e:
            logger.error(f"Error generating personalized content: {e}")
            raise

    async def get_content_recommendations(
        self,
        user_id: str,
        *,
        content_types: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[ContentRecommendation]:
        """
        Get personalized content recommendations.
        
        Args:
            user_id: ID of the user
            content_types: Optional content types to filter
            limit: Maximum number of recommendations
            
        Returns:
            List of content recommendations
        """
        try:
            # Get user behavior insights
            engagement_profile = await self.behavioral_analytics.analyze_engagement_profile(user_id)
            behavior_patterns = await self.behavioral_analytics.identify_behavior_patterns(user_id)
            
            # Generate recommendations using AI
            recommendations = await self._ai_generate_recommendations(
                user_id, engagement_profile, behavior_patterns, content_types, limit
            )
            
            content_recommendations = []
            for rec_data in recommendations:
                recommendation: ContentRecommendation = {
                    "recommendation_id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "content_type": rec_data.get("content_type", "learning_module"),
                    "title": rec_data.get("title", "Recommended Content"),
                    "description": rec_data.get("description", ""),
                    "relevance_score": rec_data.get("relevance_score", 0.7),
                    "confidence": rec_data.get("confidence", 0.8),
                    "reasoning": rec_data.get("reasoning", "Based on your learning patterns"),
                    "created_at": _now_iso_utc()
                }
                content_recommendations.append(recommendation)
            
            logger.info(f"Generated {len(content_recommendations)} recommendations for user {user_id}")
            return content_recommendations
            
        except Exception as e:
            logger.error(f"Error getting content recommendations: {e}")
            raise

    async def optimize_content_performance(
        self,
        content_id: str,
        user_feedback: Dict[str, Any],
        *,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Optimize content based on user feedback.
        
        Args:
            content_id: ID of the content
            user_feedback: User feedback data
            user_id: Optional user ID for personalization
            
        Returns:
            Optimization results
        """
        try:
            # Analyze feedback and optimize content
            optimization = await self._analyze_feedback_and_optimize(
                content_id, user_feedback, user_id
            )
            
            result = {
                "content_id": content_id,
                "optimization_applied": optimization.get("optimization_applied", False),
                "optimization_type": optimization.get("optimization_type", "none"),
                "performance_improvement": optimization.get("performance_improvement", 0.0),
                "recommendations": optimization.get("recommendations", []),
                "optimized_at": _now_iso_utc()
            }
            
            logger.info(f"Optimized content {content_id}: {result['optimization_type']}")
            return result
            
        except Exception as e:
            logger.error(f"Error optimizing content performance: {e}")
            raise

    # -------------------------------------------------------------------------
    # Private Helper Methods
    # -------------------------------------------------------------------------

    async def _ai_adapt_content(
        self,
        user_id: str,
        content_type: str,
        original_content: Dict[str, Any],
        engagement_profile: Dict[str, Any],
        personalization_score: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Use AI to adapt content for user."""
        try:
            prompt = f"""
            Adapt this {content_type} content for a user with the following profile:
            
            User Profile:
            - Learning Style: {engagement_profile.get('learning_style', 'visual')}
            - Engagement Level: {engagement_profile.get('engagement_level', 'medium')}
            - Optimal Session Duration: {engagement_profile.get('optimal_session_duration', 25)} minutes
            - Preferred Content Types: {engagement_profile.get('preferred_content_types', [])}
            - Personalization Score: {personalization_score.get('personalization_score', 0.7)}
            
            Original Content:
            {json.dumps(original_content, indent=2)}
            
            Context: {json.dumps(context or {}, indent=2)}
            
            Adapt the content to:
            1. Match the user's learning style
            2. Optimize for their engagement level
            3. Fit their optimal session duration
            4. Include their preferred content types
            5. Maximize personalization score
            
            Return the adapted content in the same format as the original.
            """
            
            ai_response = await self.ai_router.route_request(
                request_type=RequestType.GENERAL_CHAT,
                prompt=prompt,
                user_id=user_id,
                model_preference="claude-3-5-sonnet",
                temperature=0.6,
                max_tokens=1000
            )
            
            adapted_content = _safe_json_loads(ai_response) or original_content
            return adapted_content
            
        except Exception as e:
            logger.error(f"Error in AI content adaptation: {e}")
            return original_content

    async def _ai_generate_personalized_content(
        self,
        user_id: str,
        content_type: str,
        topic: str,
        engagement_profile: Dict[str, Any],
        personalization_score: Dict[str, Any],
        length_preference: Optional[str],
        difficulty_level: Optional[str],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Use AI to generate personalized content."""
        try:
            prompt = f"""
            Generate personalized {content_type} content about "{topic}" for a user with:
            
            User Profile:
            - Learning Style: {engagement_profile.get('learning_style', 'visual')}
            - Engagement Level: {engagement_profile.get('engagement_level', 'medium')}
            - Optimal Session Duration: {engagement_profile.get('optimal_session_duration', 25)} minutes
            - Preferred Content Types: {engagement_profile.get('preferred_content_types', [])}
            
            Preferences:
            - Length: {length_preference or 'medium'}
            - Difficulty: {difficulty_level or 'intermediate'}
            - Personalization Score: {personalization_score.get('personalization_score', 0.7)}
            
            Context: {json.dumps(context or {}, indent=2)}
            
            Generate content that:
            1. Matches their learning style
            2. Is appropriate for their engagement level
            3. Fits their optimal session duration
            4. Includes their preferred content types
            5. Is personalized and engaging
            
            Return JSON with: title, content, metadata
            """
            
            ai_response = await self.ai_router.route_request(
                request_type=RequestType.GENERAL_CHAT,
                prompt=prompt,
                user_id=user_id,
                model_preference="claude-3-5-sonnet",
                temperature=0.7,
                max_tokens=1200
            )
            
            content = _safe_json_loads(ai_response) or self._default_personalized_content(topic)
            return content
            
        except Exception as e:
            logger.error(f"Error in AI personalized content generation: {e}")
            return self._default_personalized_content(topic)

    async def _ai_generate_recommendations(
        self,
        user_id: str,
        engagement_profile: Dict[str, Any],
        behavior_patterns: List[Dict[str, Any]],
        content_types: Optional[List[str]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Use AI to generate content recommendations."""
        try:
            prompt = f"""
            Generate {limit} personalized content recommendations for a user with:
            
            Engagement Profile:
            - Level: {engagement_profile.get('engagement_level', 'medium')}
            - Learning Style: {engagement_profile.get('learning_style', 'visual')}
            - Preferred Content Types: {engagement_profile.get('preferred_content_types', [])}
            - Optimal Session Duration: {engagement_profile.get('optimal_session_duration', 25)} minutes
            
            Behavior Patterns:
            {json.dumps(behavior_patterns[:3], indent=2)}  # Top 3 patterns
            
            Content Types Filter: {content_types or 'all'}
            
            Generate recommendations that:
            1. Match their engagement level and learning style
            2. Align with their behavior patterns
            3. Fit their optimal session duration
            4. Include their preferred content types
            5. Are diverse and engaging
            
            Return JSON array with: content_type, title, description, relevance_score, confidence, reasoning
            """
            
            ai_response = await self.ai_router.route_request(
                request_type=RequestType.GENERAL_CHAT,
                prompt=prompt,
                user_id=user_id,
                model_preference="claude-3-5-sonnet",
                temperature=0.6,
                max_tokens=800
            )
            
            recommendations = _safe_json_loads(ai_response)
            return recommendations if isinstance(recommendations, list) else self._default_recommendations(limit)
            
        except Exception as e:
            logger.error(f"Error in AI recommendation generation: {e}")
            return self._default_recommendations(limit)

    async def _analyze_feedback_and_optimize(
        self,
        content_id: str,
        user_feedback: Dict[str, Any],
        user_id: Optional[str]
    ) -> Dict[str, Any]:
        """Analyze user feedback and optimize content."""
        try:
            # Simulate feedback analysis and optimization
            feedback_score = user_feedback.get("rating", 3.0)  # 1-5 scale
            completion_rate = user_feedback.get("completion_rate", 0.7)
            engagement_time = user_feedback.get("engagement_time", 0.0)
            
            optimization_applied = False
            optimization_type = "none"
            performance_improvement = 0.0
            recommendations = []
            
            if feedback_score < 3.0:
                optimization_applied = True
                optimization_type = "difficulty_reduction"
                performance_improvement = 0.2
                recommendations.append("Reduce content difficulty")
            
            if completion_rate < 0.6:
                optimization_applied = True
                optimization_type = "length_optimization"
                performance_improvement = 0.15
                recommendations.append("Shorten content length")
            
            if engagement_time < 5.0:  # Less than 5 minutes
                optimization_applied = True
                optimization_type = "engagement_enhancement"
                performance_improvement = 0.1
                recommendations.append("Add interactive elements")
            
            return {
                "optimization_applied": optimization_applied,
                "optimization_type": optimization_type,
                "performance_improvement": performance_improvement,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Error analyzing feedback: {e}")
            return {"optimization_applied": False, "optimization_type": "none", "performance_improvement": 0.0, "recommendations": []}

    def _predict_performance(
        self,
        content: Dict[str, Any],
        engagement_profile: Dict[str, Any]
    ) -> str:
        """Predict content performance based on user profile."""
        try:
            # Simple performance prediction based on engagement profile
            engagement_level = engagement_profile.get("engagement_level", "medium")
            learning_style = engagement_profile.get("learning_style", "visual")
            
            if engagement_level in ["high", "very_high"] and learning_style == "visual":
                return "excellent"
            elif engagement_level == "medium":
                return "high"
            else:
                return "medium"
                
        except Exception as e:
            logger.error(f"Error predicting performance: {e}")
            return "medium"

    def _default_personalized_content(self, topic: str) -> Dict[str, Any]:
        """Default personalized content for fallback."""
        return {
            "title": f"Personalized Content: {topic}",
            "content": f"This is personalized content about {topic}, tailored to your learning preferences.",
            "metadata": {"difficulty": "intermediate", "length": "medium", "style": "visual"}
        }

    def _default_recommendations(self, limit: int) -> List[Dict[str, Any]]:
        """Default recommendations for fallback."""
        return [
            {
                "content_type": "learning_module",
                "title": "Recommended Learning Module",
                "description": "Based on your learning patterns",
                "relevance_score": 0.7,
                "confidence": 0.8,
                "reasoning": "Matches your learning style"
            }
        ] * min(limit, 3)

# =============================================================================
# Singleton Instance
# =============================================================================

dynamic_content_service = DynamicContentService()