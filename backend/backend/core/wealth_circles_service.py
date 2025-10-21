"""
BIPOC Wealth Circles Service
============================

Implements AI-moderated community discussions for BIPOC users to share experiences,
strategies, and support each other's wealth-building journey. This is a key differentiator
that creates a safe, supportive space for underrepresented communities.

Key Features:
- AI-moderated discussions with cultural sensitivity
- Anonymous sharing options for privacy
- Mentorship matching and peer support
- Cultural context in financial advice
- Community challenges and achievements
- Safe space policies and moderation

Dependencies:
- advanced_ai_router: For AI moderation and content generation
- notification_service: For community updates and alerts
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
from .notification_service import NotificationService
from .ai_service import RequestType

logger = logging.getLogger(__name__)

# =============================================================================
# Enums and Types
# =============================================================================

class DiscussionType(str, Enum):
    """Types of community discussions."""
    GENERAL = "general"
    INVESTMENT_STRATEGY = "investment_strategy"
    CAREER_ADVICE = "career_advice"
    ENTREPRENEURSHIP = "entrepreneurship"
    REAL_ESTATE = "real_estate"
    DEBT_MANAGEMENT = "debt_management"
    FAMILY_FINANCES = "family_finances"
    MENTAL_HEALTH = "mental_health"

class PostVisibility(str, Enum):
    """Post visibility levels."""
    PUBLIC = "public"
    CIRCLE_ONLY = "circle_only"
    ANONYMOUS = "anonymous"
    PRIVATE = "private"

class ModerationAction(str, Enum):
    """AI moderation actions."""
    APPROVE = "approve"
    FLAG = "flag"
    HIDE = "hide"
    DELETE = "delete"
    ESCALATE = "escalate"

# =============================================================================
# Typed Payloads
# =============================================================================

class WealthCircle(TypedDict, total=False):
    """Wealth circle community."""
    circle_id: str
    name: str
    description: str
    focus_area: str
    member_count: int
    created_at: str
    is_private: bool
    cultural_focus: Optional[str]
    rules: List[str]
    moderators: List[str]

class DiscussionPost(TypedDict, total=False):
    """Community discussion post."""
    post_id: str
    circle_id: str
    user_id: str
    title: str
    content: str
    post_type: str
    visibility: str
    is_anonymous: bool
    tags: List[str]
    likes: int
    replies: int
    created_at: str
    updated_at: str
    moderation_status: str
    cultural_context: Optional[Dict[str, Any]]

class MentorshipMatch(TypedDict, total=False):
    """Mentorship matching."""
    match_id: str
    mentor_id: str
    mentee_id: str
    match_score: float
    shared_interests: List[str]
    cultural_connection: Optional[str]
    created_at: str
    status: str

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

class WealthCirclesService:
    """
    BIPOC Wealth Circles Service for community building and support.
    
    Core Functionality:
        - AI-moderated community discussions
        - Cultural context in financial advice
        - Mentorship matching and peer support
        - Anonymous sharing for privacy
        - Community challenges and achievements
        - Safe space policies and moderation
    
    Design Notes:
        - All timestamps in UTC (ISO8601)
        - Cultural sensitivity in AI moderation
        - Privacy-first approach with anonymous options
        - Community-driven content and support
    """

    def __init__(
        self,
        ai_router: Optional[AdvancedAIRouter] = None,
        notification_service: Optional[NotificationService] = None,
    ) -> None:
        self.ai_router = ai_router or get_advanced_ai_router()
        self.notification_service = notification_service or NotificationService()

    # -------------------------------------------------------------------------
    # Public API Methods
    # -------------------------------------------------------------------------

    async def create_wealth_circle(
        self,
        name: str,
        description: str,
        focus_area: str,
        creator_id: str,
        *,
        is_private: bool = False,
        cultural_focus: Optional[str] = None,
    ) -> WealthCircle:
        """
        Create a new wealth circle community.
        
        Args:
            name: Circle name
            description: Circle description
            focus_area: Primary focus area (investment, career, etc.)
            creator_id: User ID of the creator
            is_private: Whether the circle is private
            cultural_focus: Optional cultural focus (e.g., "African American", "Latino", etc.)
            
        Returns:
            WealthCircle object
        """
        try:
            circle_id = str(uuid.uuid4())
            
            # Generate community rules using AI
            rules = await self._generate_community_rules(focus_area, cultural_focus)
            
            circle: WealthCircle = {
                "circle_id": circle_id,
                "name": name,
                "description": description,
                "focus_area": focus_area,
                "member_count": 1,  # Creator is first member
                "created_at": _now_iso_utc(),
                "is_private": is_private,
                "cultural_focus": cultural_focus,
                "rules": rules,
                "moderators": [creator_id]
            }
            
            logger.info(f"Created wealth circle: {name} (ID: {circle_id})")
            return circle
            
        except Exception as e:
            logger.error(f"Error creating wealth circle: {e}")
            raise

    async def moderate_post(
        self,
        post_content: str,
        post_type: str,
        *,
        cultural_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        AI-moderate a community post for appropriateness and cultural sensitivity.
        
        Args:
            post_content: The post content to moderate
            post_type: Type of post (discussion, question, etc.)
            cultural_context: Optional cultural context for moderation
            
        Returns:
            Moderation result with action and reasoning
        """
        try:
            # Build AI prompt for cultural sensitivity
            prompt = self._build_moderation_prompt(post_content, post_type, cultural_context)
            
            # Get AI moderation decision
            ai_response = await self.ai_router.route_request(
                request_type=RequestType.GENERAL_CHAT,
                prompt=prompt,
                user_id="moderation_system",
                model_preference="claude-3-5-sonnet",  # Best for nuanced moderation
                temperature=0.3,  # Low temperature for consistent moderation
                max_tokens=500
            )
            
            # Parse AI response
            moderation_result = _safe_json_loads(ai_response) or self._default_moderation_result()
            
            logger.info(f"Post moderated: {moderation_result.get('action', 'unknown')}")
            return moderation_result
            
        except Exception as e:
            logger.error(f"Error moderating post: {e}")
            return self._default_moderation_result()

    async def create_discussion_post(
        self,
        circle_id: str,
        user_id: str,
        title: str,
        content: str,
        post_type: str,
        *,
        visibility: str = "public",
        is_anonymous: bool = False,
        tags: Optional[List[str]] = None,
    ) -> DiscussionPost:
        """
        Create a new discussion post in a wealth circle.
        
        Args:
            circle_id: ID of the wealth circle
            user_id: ID of the user creating the post
            title: Post title
            content: Post content
            post_type: Type of post
            visibility: Post visibility level
            is_anonymous: Whether to post anonymously
            tags: Optional tags for the post
            
        Returns:
            DiscussionPost object
        """
        try:
            # Moderate the post first
            moderation_result = await self.moderate_post(content, post_type)
            
            if moderation_result.get("action") == "delete":
                raise ValueError("Post rejected by moderation")
            
            post_id = str(uuid.uuid4())
            
            post: DiscussionPost = {
                "post_id": post_id,
                "circle_id": circle_id,
                "user_id": user_id if not is_anonymous else "anonymous",
                "title": title,
                "content": content,
                "post_type": post_type,
                "visibility": visibility,
                "is_anonymous": is_anonymous,
                "tags": tags or [],
                "likes": 0,
                "replies": 0,
                "created_at": _now_iso_utc(),
                "updated_at": _now_iso_utc(),
                "moderation_status": moderation_result.get("action", "approve"),
                "cultural_context": moderation_result.get("cultural_context")
            }
            
            logger.info(f"Created discussion post: {title} (ID: {post_id})")
            return post
            
        except Exception as e:
            logger.error(f"Error creating discussion post: {e}")
            raise

    async def find_mentorship_matches(
        self,
        user_id: str,
        *,
        user_profile: Optional[Dict[str, Any]] = None,
    ) -> List[MentorshipMatch]:
        """
        Find potential mentorship matches for a user.
        
        Args:
            user_id: ID of the user seeking mentorship
            user_profile: Optional user profile information
            
        Returns:
            List of potential mentorship matches
        """
        try:
            # In a real system, this would use ML matching algorithms
            # For now, we'll simulate matches based on common interests
            
            matches = []
            
            # Simulate finding mentors with similar backgrounds/interests
            potential_mentors = [
                {
                    "mentor_id": "mentor_001",
                    "name": "Sarah Johnson",
                    "background": "Tech Executive",
                    "cultural_connection": "African American",
                    "interests": ["technology", "leadership", "real_estate"],
                    "match_score": 0.92
                },
                {
                    "mentor_id": "mentor_002", 
                    "name": "Carlos Rodriguez",
                    "background": "Investment Advisor",
                    "cultural_connection": "Latino",
                    "interests": ["investing", "entrepreneurship", "family_finances"],
                    "match_score": 0.88
                },
                {
                    "mentor_id": "mentor_003",
                    "name": "Priya Patel",
                    "background": "Financial Planner",
                    "cultural_connection": "South Asian",
                    "interests": ["financial_planning", "debt_management", "career_advice"],
                    "match_score": 0.85
                }
            ]
            
            for mentor in potential_mentors:
                match: MentorshipMatch = {
                    "match_id": str(uuid.uuid4()),
                    "mentor_id": mentor["mentor_id"],
                    "mentee_id": user_id,
                    "match_score": mentor["match_score"],
                    "shared_interests": mentor["interests"][:2],  # Top 2 interests
                    "cultural_connection": mentor["cultural_connection"],
                    "created_at": _now_iso_utc(),
                    "status": "pending"
                }
                matches.append(match)
            
            logger.info(f"Found {len(matches)} mentorship matches for user {user_id}")
            return matches
            
        except Exception as e:
            logger.error(f"Error finding mentorship matches: {e}")
            raise

    async def generate_cultural_financial_advice(
        self,
        user_question: str,
        cultural_context: Dict[str, Any],
        *,
        user_id: str = "anonymous",
    ) -> Dict[str, Any]:
        """
        Generate culturally-aware financial advice.
        
        Args:
            user_question: The user's financial question
            cultural_context: Cultural context (background, values, etc.)
            user_id: User ID for personalization
            
        Returns:
            Culturally-aware financial advice
        """
        try:
            # Build AI prompt with cultural context
            prompt = self._build_cultural_advice_prompt(user_question, cultural_context)
            
            # Get AI response
            ai_response = await self.ai_router.route_request(
                request_type=RequestType.GENERAL_CHAT,
                prompt=prompt,
                user_id=user_id,
                model_preference="claude-3-5-sonnet",  # Best for nuanced cultural advice
                temperature=0.7,
                max_tokens=800
            )
            
            # Parse and structure the response
            advice = _safe_json_loads(ai_response) or self._default_advice_response()
            
            logger.info(f"Generated cultural financial advice for user {user_id}")
            return advice
            
        except Exception as e:
            logger.error(f"Error generating cultural financial advice: {e}")
            return self._default_advice_response()

    # -------------------------------------------------------------------------
    # Private Helper Methods
    # -------------------------------------------------------------------------

    async def _generate_community_rules(
        self,
        focus_area: str,
        cultural_focus: Optional[str] = None
    ) -> List[str]:
        """Generate community rules using AI."""
        try:
            prompt = f"""
            Generate 5-7 community rules for a wealth-building circle focused on {focus_area}.
            {f"The community has a {cultural_focus} cultural focus." if cultural_focus else ""}
            
            Rules should be:
            - Encouraging and supportive
            - Culturally sensitive
            - Focused on financial education and empowerment
            - Inclusive and respectful
            
            Return as a JSON array of rule strings.
            """
            
            ai_response = await self.ai_router.route_request(
                request_type=RequestType.GENERAL_CHAT,
                prompt=prompt,
                user_id="system",
                model_preference="claude-3-5-sonnet",
                temperature=0.5,
                max_tokens=300
            )
            
            rules = _safe_json_loads(ai_response) or []
            return rules if isinstance(rules, list) else self._default_community_rules()
            
        except Exception as e:
            logger.error(f"Error generating community rules: {e}")
            return self._default_community_rules()

    def _build_moderation_prompt(
        self,
        post_content: str,
        post_type: str,
        cultural_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build AI prompt for post moderation."""
        cultural_context_str = ""
        if cultural_context:
            cultural_context_str = f"\nCultural Context: {json.dumps(cultural_context)}"
        
        return f"""
        You are an AI moderator for a BIPOC wealth-building community. Your task is to review this post for appropriateness, cultural sensitivity, and community guidelines.

        Post Type: {post_type}
        Post Content: {post_content}
        {cultural_context_str}

        Evaluate the post and return a JSON response with:
        {{
            "action": "approve|flag|hide|delete|escalate",
            "reasoning": "Brief explanation of the decision",
            "cultural_sensitivity_score": 0.0-1.0,
            "community_guidelines_violation": true/false,
            "suggested_improvements": ["suggestion1", "suggestion2"]
        }}

        Guidelines:
        - Be culturally sensitive and aware of different perspectives
        - Encourage financial education and empowerment
        - Maintain a supportive, inclusive environment
        - Flag potentially harmful financial advice
        - Respect privacy and anonymity
        """

    def _build_cultural_advice_prompt(
        self,
        user_question: str,
        cultural_context: Dict[str, Any]
    ) -> str:
        """Build AI prompt for cultural financial advice."""
        return f"""
        You are a culturally-aware financial advisor for BIPOC communities. Provide thoughtful, empathetic financial advice that considers cultural context and values.

        User Question: {user_question}
        Cultural Context: {json.dumps(cultural_context)}

        Provide advice that:
        - Acknowledges cultural values and family dynamics
        - Considers historical and systemic factors
        - Offers practical, actionable steps
        - Is empowering and non-judgmental
        - Respects different approaches to wealth building

        Return a JSON response with:
        {{
            "advice": "Main advice text",
            "cultural_considerations": "How cultural context affects the advice",
            "action_steps": ["step1", "step2", "step3"],
            "resources": ["resource1", "resource2"],
            "encouragement": "Motivational message"
        }}
        """

    def _default_moderation_result(self) -> Dict[str, Any]:
        """Default moderation result for fallback."""
        return {
            "action": "approve",
            "reasoning": "Post appears appropriate",
            "cultural_sensitivity_score": 0.8,
            "community_guidelines_violation": False,
            "suggested_improvements": []
        }

    def _default_advice_response(self) -> Dict[str, Any]:
        """Default advice response for fallback."""
        return {
            "advice": "I'd be happy to help with your financial question. Could you provide more details?",
            "cultural_considerations": "Every family's financial situation is unique.",
            "action_steps": ["Gather more information", "Consider your goals", "Seek professional advice if needed"],
            "resources": ["Community resources", "Financial education materials"],
            "encouragement": "You're taking an important step by seeking financial guidance!"
        }

    def _default_community_rules(self) -> List[str]:
        """Default community rules for fallback."""
        return [
            "Be respectful and supportive of all members",
            "Share knowledge and experiences to help others",
            "Maintain confidentiality and respect privacy",
            "Focus on financial education and empowerment",
            "No spam, self-promotion, or harmful advice",
            "Celebrate each other's successes and learn from challenges"
        ]

# =============================================================================
# Singleton Instance
# =============================================================================

wealth_circles_service = WealthCirclesService()
