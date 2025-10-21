"""
Peer Progress Pulse Service
===========================

Implements anonymous social proof and progress sharing to create a sense of community
and motivation through seeing others' achievements and progress. This creates the
"everyone else is doing it" effect that drives engagement.

Key Features:
- Anonymous progress sharing and achievements
- Social proof through community statistics
- Progress streaks and milestones
- Peer comparison and motivation
- Achievement celebrations and recognition
- Privacy-first approach with opt-in sharing

Dependencies:
- wealth_circles_service: For community context
- notification_service: For progress updates and celebrations
"""

from __future__ import annotations

import asyncio
import json
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, TypedDict
from enum import Enum

from .wealth_circles_service import WealthCirclesService
from .notification_service import NotificationService

logger = logging.getLogger(__name__)

# =============================================================================
# Enums and Types
# =============================================================================

class ProgressType(str, Enum):
    """Types of progress updates."""
    LEARNING_STREAK = "learning_streak"
    INVESTMENT_GOAL = "investment_goal"
    DEBT_REDUCTION = "debt_reduction"
    SAVINGS_MILESTONE = "savings_milestone"
    CAREER_ADVANCEMENT = "career_advancement"
    SKILL_DEVELOPMENT = "skill_development"
    NET_WORTH_GROWTH = "net_worth_growth"

class SharingLevel(str, Enum):
    """Levels of progress sharing."""
    PRIVATE = "private"
    ANONYMOUS = "anonymous"
    COMMUNITY = "community"
    PUBLIC = "public"

class AchievementLevel(str, Enum):
    """Achievement levels."""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"

# =============================================================================
# Typed Payloads
# =============================================================================

class ProgressUpdate(TypedDict, total=False):
    """User progress update."""
    update_id: str
    user_id: str
    progress_type: str
    title: str
    description: str
    value: float
    unit: str
    sharing_level: str
    is_anonymous: bool
    created_at: str
    community_id: Optional[str]
    tags: List[str]
    milestone: Optional[str]

class CommunityStats(TypedDict, total=False):
    """Community progress statistics."""
    community_id: str
    total_members: int
    active_this_week: int
    total_progress_updates: int
    average_streak: float
    top_achievements: List[Dict[str, Any]]
    recent_milestones: List[Dict[str, Any]]
    generated_at: str

class Achievement(TypedDict, total=False):
    """User achievement."""
    achievement_id: str
    user_id: str
    title: str
    description: str
    level: str
    icon: str
    unlocked_at: str
    is_shared: bool
    community_celebration: bool

class PeerComparison(TypedDict, total=False):
    """Peer comparison data."""
    user_id: str
    comparison_type: str
    user_rank: int
    total_peers: int
    percentile: float
    peer_average: float
    user_value: float
    motivation_message: str
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

class PeerProgressService:
    """
    Peer Progress Pulse Service for social proof and motivation.
    
    Core Functionality:
        - Anonymous progress sharing and achievements
        - Social proof through community statistics
        - Progress streaks and milestones
        - Peer comparison and motivation
        - Achievement celebrations and recognition
        - Privacy-first approach with opt-in sharing
    
    Design Notes:
        - All timestamps in UTC (ISO8601)
        - Privacy-first with anonymous options
        - Positive reinforcement and motivation
        - Community-driven engagement
    """

    def __init__(
        self,
        wealth_circles_service: Optional[WealthCirclesService] = None,
        notification_service: Optional[NotificationService] = None,
    ) -> None:
        self.wealth_circles_service = wealth_circles_service or WealthCirclesService()
        self.notification_service = notification_service or NotificationService()

    # -------------------------------------------------------------------------
    # Public API Methods
    # -------------------------------------------------------------------------

    async def share_progress(
        self,
        user_id: str,
        progress_type: str,
        title: str,
        description: str,
        value: float,
        unit: str,
        *,
        sharing_level: str = "anonymous",
        community_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> ProgressUpdate:
        """
        Share a progress update with the community.
        
        Args:
            user_id: ID of the user sharing progress
            progress_type: Type of progress (learning_streak, investment_goal, etc.)
            title: Progress title
            description: Progress description
            value: Progress value (e.g., 30 days, $5000, etc.)
            unit: Unit of measurement (days, dollars, percentage, etc.)
            sharing_level: Level of sharing (private, anonymous, community, public)
            community_id: Optional community/circle ID
            tags: Optional tags for categorization
            
        Returns:
            ProgressUpdate object
        """
        try:
            update_id = str(uuid.uuid4())
            
            # Determine if this should be anonymous
            is_anonymous = sharing_level in ["anonymous", "community"]
            
            # Check if this is a milestone worth celebrating
            milestone = await self._check_milestone(progress_type, value)
            
            progress_update: ProgressUpdate = {
                "update_id": update_id,
                "user_id": user_id,
                "progress_type": progress_type,
                "title": title,
                "description": description,
                "value": value,
                "unit": unit,
                "sharing_level": sharing_level,
                "is_anonymous": is_anonymous,
                "created_at": _now_iso_utc(),
                "community_id": community_id,
                "tags": tags or [],
                "milestone": milestone
            }
            
            # Trigger community celebration if milestone reached
            if milestone:
                await self._trigger_milestone_celebration(progress_update)
            
            # Update community statistics
            if community_id:
                await self._update_community_stats(community_id)
            
            logger.info(f"Progress shared: {title} by user {user_id} (anonymous: {is_anonymous})")
            return progress_update
            
        except Exception as e:
            logger.error(f"Error sharing progress: {e}")
            raise

    async def get_community_stats(
        self,
        community_id: str,
        *,
        time_period: str = "week",
    ) -> CommunityStats:
        """
        Get community progress statistics for social proof.
        
        Args:
            community_id: ID of the community
            time_period: Time period for stats (day, week, month)
            
        Returns:
            CommunityStats object
        """
        try:
            # In a real system, this would aggregate data from database
            # For now, we'll simulate realistic community stats
            
            stats: CommunityStats = {
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
                    },
                    {
                        "title": "New member completed their first investment!",
                        "timestamp": "2024-01-15T10:45:00Z",
                        "icon": "📈"
                    }
                ],
                "generated_at": _now_iso_utc()
            }
            
            logger.info(f"Generated community stats for {community_id}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting community stats: {e}")
            raise

    async def get_peer_comparison(
        self,
        user_id: str,
        comparison_type: str,
        user_value: float,
        *,
        community_id: Optional[str] = None,
    ) -> PeerComparison:
        """
        Get peer comparison data for motivation.
        
        Args:
            user_id: ID of the user
            comparison_type: Type of comparison (learning_streak, savings, etc.)
            user_value: User's current value
            community_id: Optional community context
            
        Returns:
            PeerComparison object
        """
        try:
            # Simulate peer comparison data
            # In a real system, this would query actual user data
            
            total_peers = 1247
            user_rank = max(1, int(total_peers * (0.3 + (user_value / 100) * 0.4)))  # Simulate rank
            percentile = (total_peers - user_rank + 1) / total_peers * 100
            peer_average = user_value * 0.7  # Simulate peer average
            
            # Generate motivational message based on performance
            if percentile >= 80:
                motivation_message = "You're in the top 20%! Keep up the amazing work! 🚀"
            elif percentile >= 60:
                motivation_message = "You're doing great! You're above average and climbing! 📈"
            elif percentile >= 40:
                motivation_message = "You're making solid progress! Every step counts! 💪"
            else:
                motivation_message = "You're on your journey! Remember, everyone starts somewhere! 🌟"
            
            comparison: PeerComparison = {
                "user_id": user_id,
                "comparison_type": comparison_type,
                "user_rank": user_rank,
                "total_peers": total_peers,
                "percentile": percentile,
                "peer_average": peer_average,
                "user_value": user_value,
                "motivation_message": motivation_message,
                "generated_at": _now_iso_utc()
            }
            
            logger.info(f"Generated peer comparison for user {user_id}: {percentile:.1f}th percentile")
            return comparison
            
        except Exception as e:
            logger.error(f"Error getting peer comparison: {e}")
            raise

    async def unlock_achievement(
        self,
        user_id: str,
        achievement_type: str,
        *,
        community_celebration: bool = True,
    ) -> Achievement:
        """
        Unlock an achievement for a user.
        
        Args:
            user_id: ID of the user
            achievement_type: Type of achievement
            community_celebration: Whether to celebrate in community
            
        Returns:
            Achievement object
        """
        try:
            achievement_id = str(uuid.uuid4())
            
            # Define achievement details based on type
            achievement_details = self._get_achievement_details(achievement_type)
            
            achievement: Achievement = {
                "achievement_id": achievement_id,
                "user_id": user_id,
                "title": achievement_details["title"],
                "description": achievement_details["description"],
                "level": achievement_details["level"],
                "icon": achievement_details["icon"],
                "unlocked_at": _now_iso_utc(),
                "is_shared": community_celebration,
                "community_celebration": community_celebration
            }
            
            # Trigger community celebration if enabled
            if community_celebration:
                await self._trigger_achievement_celebration(achievement)
            
            logger.info(f"Unlocked achievement: {achievement['title']} for user {user_id}")
            return achievement
            
        except Exception as e:
            logger.error(f"Error unlocking achievement: {e}")
            raise

    async def get_recent_community_activity(
        self,
        community_id: str,
        *,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get recent community activity for social proof.
        
        Args:
            community_id: ID of the community
            limit: Maximum number of activities to return
            
        Returns:
            List of recent community activities
        """
        try:
            # Simulate recent community activity
            activities = [
                {
                    "type": "milestone",
                    "title": "Someone reached a 30-day learning streak!",
                    "icon": "🔥",
                    "timestamp": "2024-01-15T14:30:00Z",
                    "is_anonymous": True
                },
                {
                    "type": "achievement",
                    "title": "Community member unlocked 'First Investment' badge!",
                    "icon": "🏆",
                    "timestamp": "2024-01-15T13:15:00Z",
                    "is_anonymous": True
                },
                {
                    "type": "progress",
                    "title": "Someone shared: 'Just saved my first $1,000!'",
                    "icon": "💰",
                    "timestamp": "2024-01-15T12:00:00Z",
                    "is_anonymous": True
                },
                {
                    "type": "milestone",
                    "title": "Community member completed their first trading course!",
                    "icon": "📚",
                    "timestamp": "2024-01-15T11:45:00Z",
                    "is_anonymous": True
                },
                {
                    "type": "achievement",
                    "title": "Someone unlocked 'Debt-Free Journey' badge!",
                    "icon": "🎯",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "is_anonymous": True
                }
            ]
            
            return activities[:limit]
            
        except Exception as e:
            logger.error(f"Error getting community activity: {e}")
            raise

    # -------------------------------------------------------------------------
    # Private Helper Methods
    # -------------------------------------------------------------------------

    async def _check_milestone(
        self,
        progress_type: str,
        value: float
    ) -> Optional[str]:
        """Check if the progress value represents a milestone."""
        milestones = {
            "learning_streak": {
                7: "One Week Strong!",
                14: "Two Weeks of Learning!",
                21: "Habit Formed!",
                30: "One Month Master!",
                50: "Learning Legend!",
                100: "Century Scholar!"
            },
            "savings_milestone": {
                1000: "First $1K Saved!",
                5000: "Halfway to $10K!",
                10000: "Five-Figure Saver!",
                25000: "Quarter Million Path!",
                50000: "Half Century Saver!"
            },
            "debt_reduction": {
                1000: "First $1K Paid Off!",
                5000: "Major Debt Progress!",
                10000: "Five-Figure Freedom!",
                25000: "Quarter Million Clear!"
            }
        }
        
        type_milestones = milestones.get(progress_type, {})
        
        # Find the highest milestone reached
        reached_milestones = [milestone for threshold, milestone in type_milestones.items() if value >= threshold]
        
        return reached_milestones[-1] if reached_milestones else None

    async def _trigger_milestone_celebration(
        self,
        progress_update: ProgressUpdate
    ) -> None:
        """Trigger community celebration for milestone."""
        try:
            # In a real system, this would send notifications and update community feeds
            logger.info(f"Milestone celebration triggered: {progress_update['milestone']}")
            
            # Could trigger notifications, community posts, etc.
            
        except Exception as e:
            logger.error(f"Error triggering milestone celebration: {e}")

    async def _trigger_achievement_celebration(
        self,
        achievement: Achievement
    ) -> None:
        """Trigger community celebration for achievement."""
        try:
            # In a real system, this would send notifications and update community feeds
            logger.info(f"Achievement celebration triggered: {achievement['title']}")
            
            # Could trigger notifications, community posts, etc.
            
        except Exception as e:
            logger.error(f"Error triggering achievement celebration: {e}")

    async def _update_community_stats(
        self,
        community_id: str
    ) -> None:
        """Update community statistics."""
        try:
            # In a real system, this would update database statistics
            logger.info(f"Updated community stats for {community_id}")
            
        except Exception as e:
            logger.error(f"Error updating community stats: {e}")

    def _get_achievement_details(
        self,
        achievement_type: str
    ) -> Dict[str, Any]:
        """Get achievement details based on type."""
        achievements = {
            "first_investment": {
                "title": "First Investment",
                "description": "Made your first investment!",
                "level": "bronze",
                "icon": "📈"
            },
            "learning_streak_7": {
                "title": "Week Warrior",
                "description": "Completed a 7-day learning streak!",
                "level": "bronze",
                "icon": "🔥"
            },
            "learning_streak_30": {
                "title": "Month Master",
                "description": "Completed a 30-day learning streak!",
                "level": "silver",
                "icon": "🔥"
            },
            "savings_1k": {
                "title": "First $1K",
                "description": "Saved your first $1,000!",
                "level": "bronze",
                "icon": "💰"
            },
            "savings_10k": {
                "title": "Five-Figure Saver",
                "description": "Saved $10,000!",
                "level": "gold",
                "icon": "💰"
            },
            "debt_free": {
                "title": "Debt-Free Champion",
                "description": "Eliminated all debt!",
                "level": "platinum",
                "icon": "🎯"
            }
        }
        
        return achievements.get(achievement_type, {
            "title": "Achievement Unlocked",
            "description": "You've unlocked a new achievement!",
            "level": "bronze",
            "icon": "🏆"
        })

# =============================================================================
# Singleton Instance
# =============================================================================

peer_progress_service = PeerProgressService()
