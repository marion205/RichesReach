"""
Push Notification Service
========================

Implements real-time push notifications for regime alerts, daily digests, and momentum missions.
This is a key enhancement to Phase 1 that creates immediate engagement through timely notifications.

Key Features:
- Real-time regime change alerts
- Scheduled daily voice digest notifications
- Momentum mission reminders and streak alerts
- Personalized timing preferences
- Cross-platform push delivery (iOS/Android)

Dependencies:
- daily_voice_digest_service: For digest scheduling
- momentum_missions_service: For mission reminders
- ml_service: For regime change detection
"""

from __future__ import annotations

import asyncio
import json
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, TypedDict
from enum import Enum

from .daily_voice_digest_service import DailyVoiceDigestService
from .momentum_missions_service import MomentumMissionsService
from .ml_service import MLService

logger = logging.getLogger(__name__)

# =============================================================================
# Enums and Types
# =============================================================================

class NotificationType(str, Enum):
    """Types of notifications."""
    REGIME_ALERT = "regime_alert"
    DAILY_DIGEST = "daily_digest"
    MISSION_REMINDER = "mission_reminder"
    STREAK_ALERT = "streak_alert"
    ACHIEVEMENT = "achievement"
    RECOVERY_RITUAL = "recovery_ritual"

class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class DeliveryStatus(str, Enum):
    """Notification delivery status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"

# =============================================================================
# Typed Payloads
# =============================================================================

class PushNotification(TypedDict, total=False):
    """Push notification payload."""
    notification_id: str
    user_id: str
    type: str
    priority: str
    title: str
    body: str
    data: Dict[str, Any]
    scheduled_for: str  # ISO8601 (UTC)
    expires_at: str  # ISO8601 (UTC)
    delivery_status: str
    created_at: str  # ISO8601 (UTC)
    sent_at: Optional[str]  # ISO8601 (UTC)

class NotificationPreferences(TypedDict, total=False):
    """User notification preferences."""
    user_id: str
    daily_digest_enabled: bool
    daily_digest_time: str  # HH:MM format
    regime_alerts_enabled: bool
    regime_alert_urgency: str  # low, medium, high
    mission_reminders_enabled: bool
    mission_reminder_time: str  # HH:MM format
    streak_alerts_enabled: bool
    achievement_notifications_enabled: bool
    recovery_ritual_enabled: bool
    quiet_hours_start: Optional[str]  # HH:MM format
    quiet_hours_end: Optional[str]  # HH:MM format
    timezone: str  # IANA timezone

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

class NotificationService:
    """
    Push Notification Service for real-time engagement.
    
    Core Functionality:
        - Real-time regime change alerts
        - Scheduled daily voice digest notifications
        - Momentum mission reminders and streak alerts
        - Achievement and recovery ritual notifications
        - Personalized timing and preference management
    
    Design Notes:
        - All timestamps in UTC (ISO8601)
        - Cross-platform push delivery
        - Intelligent scheduling with quiet hours
        - Priority-based delivery
    """

    # Configuration Defaults
    DEFAULT_QUIET_HOURS_START = "22:00"
    DEFAULT_QUIET_HOURS_END = "07:00"
    DEFAULT_DIGEST_TIME = "08:00"
    DEFAULT_MISSION_REMINDER_TIME = "19:00"
    NOTIFICATION_EXPIRY_HOURS = 24

    def __init__(
        self,
        digest_service: Optional[DailyVoiceDigestService] = None,
        missions_service: Optional[MomentumMissionsService] = None,
        ml_service: Optional[MLService] = None,
    ) -> None:
        self.digest_service = digest_service or DailyVoiceDigestService()
        self.missions_service = missions_service or MomentumMissionsService()
        self.ml_service = ml_service or MLService()

    # -------------------------------------------------------------------------
    # Public API Methods
    # -------------------------------------------------------------------------

    async def schedule_daily_digest_notification(
        self,
        user_id: str,
        *,
        preferred_time: Optional[str] = None,
        timezone: str = "UTC",
    ) -> PushNotification:
        """
        Schedule a daily voice digest notification.
        
        This creates a scheduled notification that will trigger the daily
        voice digest generation and delivery at the user's preferred time.
        
        Args:
            user_id: User identifier
            preferred_time: Preferred digest time (HH:MM format)
            timezone: User's timezone (IANA format)
            
        Returns:
            PushNotification for daily digest
        """
        try:
            # Get user preferences (in production, from database)
            preferences = await self._get_user_preferences(user_id)
            
            # Determine digest time
            digest_time = preferred_time or preferences.get('daily_digest_time', self.DEFAULT_DIGEST_TIME)
            
            # Calculate next scheduled time
            scheduled_time = self._calculate_next_scheduled_time(digest_time, timezone)
            
            # Create notification payload
            notification_id = str(uuid.uuid4())
            expires_at = scheduled_time + timedelta(hours=self.NOTIFICATION_EXPIRY_HOURS)
            
            notification: PushNotification = {
                "notification_id": notification_id,
                "user_id": user_id,
                "type": NotificationType.DAILY_DIGEST.value,
                "priority": NotificationPriority.NORMAL.value,
                "title": "🎙️ Your Daily Market Briefing",
                "body": "Your personalized 60-second market digest is ready! Tap to listen.",
                "data": {
                    "action": "open_daily_digest",
                    "digest_time": digest_time,
                    "timezone": timezone
                },
                "scheduled_for": scheduled_time.isoformat(),
                "expires_at": expires_at.isoformat(),
                "delivery_status": DeliveryStatus.PENDING.value,
                "created_at": _now_iso_utc(),
                "sent_at": None,
            }
            
            # Schedule the notification (in production, this would use a job queue)
            await self._schedule_notification(notification)
            
            logger.info(f"Scheduled daily digest notification for user {user_id} at {scheduled_time}")
            return notification
            
        except Exception as e:
            logger.error(f"Error scheduling daily digest notification: {e}")
            raise

    async def create_regime_alert_notification(
        self,
        user_id: str,
        regime_change: Dict[str, Any],
        *,
        urgency: str = "medium",
    ) -> PushNotification:
        """
        Create an immediate regime change alert notification.
        
        This sends an immediate notification when market regime changes
        significantly, helping users adapt their strategies in real-time.
        
        Args:
            user_id: User identifier
            regime_change: Details about the regime change
            urgency: Alert urgency level (low, medium, high, urgent)
            
        Returns:
            PushNotification for regime alert
        """
        try:
            # Get user preferences
            preferences = await self._get_user_preferences(user_id)
            
            # Check if regime alerts are enabled
            if not preferences.get('regime_alerts_enabled', True):
                raise ValueError("Regime alerts are disabled for this user")
            
            # Check urgency threshold
            min_urgency = preferences.get('regime_alert_urgency', 'medium')
            if not self._meets_urgency_threshold(urgency, min_urgency):
                raise ValueError(f"Alert urgency {urgency} below user threshold {min_urgency}")
            
            # Create regime-specific alert content
            old_regime = regime_change.get('old_regime', 'unknown')
            new_regime = regime_change.get('new_regime', 'unknown')
            confidence = regime_change.get('confidence', 0.5)
            
            title, body = self._create_regime_alert_content(old_regime, new_regime, confidence, urgency)
            
            # Create notification payload
            notification_id = str(uuid.uuid4())
            scheduled_time = datetime.now(timezone.utc)
            expires_at = scheduled_time + timedelta(hours=self.NOTIFICATION_EXPIRY_HOURS)
            
            notification: PushNotification = {
                "notification_id": notification_id,
                "user_id": user_id,
                "type": NotificationType.REGIME_ALERT.value,
                "priority": urgency,
                "title": title,
                "body": body,
                "data": {
                    "action": "open_regime_analysis",
                    "old_regime": old_regime,
                    "new_regime": new_regime,
                    "confidence": confidence,
                    "urgency": urgency
                },
                "scheduled_for": scheduled_time.isoformat(),
                "expires_at": expires_at.isoformat(),
                "delivery_status": DeliveryStatus.PENDING.value,
                "created_at": _now_iso_utc(),
                "sent_at": None,
            }
            
            # Send immediately (in production, this would use push service)
            await self._send_notification(notification)
            
            logger.info(f"Created regime alert notification for user {user_id}: {old_regime} → {new_regime}")
            return notification
            
        except Exception as e:
            logger.error(f"Error creating regime alert notification: {e}")
            raise

    async def create_mission_reminder_notification(
        self,
        user_id: str,
        mission: Dict[str, Any],
        *,
        reminder_type: str = "daily",
    ) -> PushNotification:
        """
        Create a momentum mission reminder notification.
        
        This sends reminders for daily missions, streak alerts, and recovery rituals
        to help users maintain their 21-day habit loop.
        
        Args:
            user_id: User identifier
            mission: Mission details
            reminder_type: Type of reminder (daily, streak, recovery)
            
        Returns:
            PushNotification for mission reminder
        """
        try:
            # Get user preferences
            preferences = await self._get_user_preferences(user_id)
            
            # Check if mission reminders are enabled
            if not preferences.get('mission_reminders_enabled', True):
                raise ValueError("Mission reminders are disabled for this user")
            
            # Create mission-specific content
            title, body = self._create_mission_reminder_content(mission, reminder_type)
            
            # Determine priority and scheduling
            priority = NotificationPriority.HIGH if reminder_type == "streak" else NotificationPriority.NORMAL
            scheduled_time = self._calculate_mission_reminder_time(preferences)
            
            # Create notification payload
            notification_id = str(uuid.uuid4())
            expires_at = scheduled_time + timedelta(hours=self.NOTIFICATION_EXPIRY_HOURS)
            
            notification: PushNotification = {
                "notification_id": notification_id,
                "user_id": user_id,
                "type": NotificationType.MISSION_REMINDER.value,
                "priority": priority.value,
                "title": title,
                "body": body,
                "data": {
                    "action": "open_momentum_missions",
                    "mission_id": mission.get('mission_id'),
                    "day_number": mission.get('day_number'),
                    "reminder_type": reminder_type
                },
                "scheduled_for": scheduled_time.isoformat(),
                "expires_at": expires_at.isoformat(),
                "delivery_status": DeliveryStatus.PENDING.value,
                "created_at": _now_iso_utc(),
                "sent_at": None,
            }
            
            # Schedule the notification
            await self._schedule_notification(notification)
            
            logger.info(f"Created mission reminder notification for user {user_id}: {reminder_type}")
            return notification
            
        except Exception as e:
            logger.error(f"Error creating mission reminder notification: {e}")
            raise

    async def create_achievement_notification(
        self,
        user_id: str,
        achievement: Dict[str, Any],
    ) -> PushNotification:
        """
        Create an achievement notification.
        
        This sends immediate notifications when users unlock achievements,
        providing positive reinforcement and social proof.
        
        Args:
            user_id: User identifier
            achievement: Achievement details
            
        Returns:
            PushNotification for achievement
        """
        try:
            # Get user preferences
            preferences = await self._get_user_preferences(user_id)
            
            # Check if achievement notifications are enabled
            if not preferences.get('achievement_notifications_enabled', True):
                raise ValueError("Achievement notifications are disabled for this user")
            
            # Create achievement-specific content
            title = f"🏆 {achievement.get('name', 'Achievement Unlocked!')}"
            body = f"Congratulations! {achievement.get('description', 'You\'ve unlocked a new achievement!')}"
            
            # Create notification payload
            notification_id = str(uuid.uuid4())
            scheduled_time = datetime.now(timezone.utc)
            expires_at = scheduled_time + timedelta(hours=self.NOTIFICATION_EXPIRY_HOURS)
            
            notification: PushNotification = {
                "notification_id": notification_id,
                "user_id": user_id,
                "type": NotificationType.ACHIEVEMENT.value,
                "priority": NotificationPriority.NORMAL.value,
                "title": title,
                "body": body,
                "data": {
                    "action": "open_achievements",
                    "achievement_id": achievement.get('id'),
                    "achievement_name": achievement.get('name'),
                    "icon": achievement.get('icon')
                },
                "scheduled_for": scheduled_time.isoformat(),
                "expires_at": expires_at.isoformat(),
                "delivery_status": DeliveryStatus.PENDING.value,
                "created_at": _now_iso_utc(),
                "sent_at": None,
            }
            
            # Send immediately
            await self._send_notification(notification)
            
            logger.info(f"Created achievement notification for user {user_id}: {achievement.get('name')}")
            return notification
            
        except Exception as e:
            logger.error(f"Error creating achievement notification: {e}")
            raise

    # -------------------------------------------------------------------------
    # Private Helper Methods
    # -------------------------------------------------------------------------

    async def _get_user_preferences(self, user_id: str) -> NotificationPreferences:
        """Get user notification preferences."""
        # In production, this would fetch from database
        # For now, return default preferences
        return {
            "user_id": user_id,
            "daily_digest_enabled": True,
            "daily_digest_time": self.DEFAULT_DIGEST_TIME,
            "regime_alerts_enabled": True,
            "regime_alert_urgency": "medium",
            "mission_reminders_enabled": True,
            "mission_reminder_time": self.DEFAULT_MISSION_REMINDER_TIME,
            "streak_alerts_enabled": True,
            "achievement_notifications_enabled": True,
            "recovery_ritual_enabled": True,
            "quiet_hours_start": self.DEFAULT_QUIET_HOURS_START,
            "quiet_hours_end": self.DEFAULT_QUIET_HOURS_END,
            "timezone": "UTC"
        }

    def _calculate_next_scheduled_time(self, time_str: str, timezone: str) -> datetime:
        """Calculate next scheduled time for a daily notification."""
        # Parse time string (HH:MM format)
        hour, minute = map(int, time_str.split(':'))
        
        # Get current time in user's timezone
        now = datetime.now(timezone.utc)
        
        # Calculate next occurrence
        next_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_time <= now:
            next_time += timedelta(days=1)
        
        return next_time

    def _meets_urgency_threshold(self, alert_urgency: str, user_threshold: str) -> bool:
        """Check if alert urgency meets user's threshold."""
        urgency_levels = {
            "low": 1,
            "medium": 2,
            "high": 3,
            "urgent": 4
        }
        
        alert_level = urgency_levels.get(alert_urgency, 2)
        threshold_level = urgency_levels.get(user_threshold, 2)
        
        return alert_level >= threshold_level

    def _create_regime_alert_content(self, old_regime: str, new_regime: str, confidence: float, urgency: str) -> tuple[str, str]:
        """Create regime alert title and body."""
        old_display = old_regime.replace('_', ' ').title()
        new_display = new_regime.replace('_', ' ').title()
        confidence_pct = f"{confidence:.0%}"
        
        if urgency == "urgent":
            title = f"🚨 URGENT: Market Regime Alert"
            body = f"CRITICAL: Market shifted from {old_display} to {new_display}. Confidence: {confidence_pct}. Immediate action recommended."
        elif urgency == "high":
            title = f"⚠️ High Priority: Market Regime Alert"
            body = f"Market shifted from {old_display} to {new_display}. Confidence: {confidence_pct}. Review your strategy now."
        elif urgency == "medium":
            title = f"📊 Market Regime Alert"
            body = f"Market regime changed from {old_display} to {new_display}. Confidence: {confidence_pct}. Consider adjusting your approach."
        else:
            title = f"📈 Market Update"
            body = f"Market regime shifted from {old_display} to {new_display}. Confidence: {confidence_pct}."
        
        return title, body

    def _create_mission_reminder_content(self, mission: Dict[str, Any], reminder_type: str) -> tuple[str, str]:
        """Create mission reminder title and body."""
        if reminder_type == "streak":
            title = "🔥 Streak Alert!"
            body = "Your momentum streak is at risk! Complete today's mission to keep it going."
        elif reminder_type == "recovery":
            title = "💪 Recovery Ritual Available"
            body = "Get back on track with a quick recovery challenge. Every step counts!"
        else:
            day_number = mission.get('day_number', 1)
            title = f"🎯 Day {day_number} Mission Ready"
            body = f"Your daily momentum mission is waiting! Take 5 minutes to complete it."
        
        return title, body

    def _calculate_mission_reminder_time(self, preferences: NotificationPreferences) -> datetime:
        """Calculate mission reminder time based on user preferences."""
        reminder_time = preferences.get('mission_reminder_time', self.DEFAULT_MISSION_REMINDER_TIME)
        return self._calculate_next_scheduled_time(reminder_time, preferences.get('timezone', 'UTC'))

    async def _schedule_notification(self, notification: PushNotification) -> None:
        """Schedule a notification for delivery."""
        # In production, this would add to a job queue (Redis, Celery, etc.)
        logger.info(f"Scheduled notification {notification['notification_id']} for {notification['scheduled_for']}")

    async def _send_notification(self, notification: PushNotification) -> None:
        """Send a notification immediately."""
        # In production, this would use Firebase, APNs, or similar
        logger.info(f"Sent notification {notification['notification_id']} to user {notification['user_id']}")

# =============================================================================
# Singleton Instance
# =============================================================================

notification_service = NotificationService()
