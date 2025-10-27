"""
Analytics Dashboard for RichesReach Education System
Comprehensive learning metrics, progress tracking, and insights
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import statistics
import logging

class MetricType(Enum):
    """Types of learning metrics"""
    ENGAGEMENT = "engagement"
    PERFORMANCE = "performance"
    RETENTION = "retention"
    PROGRESSION = "progression"
    SOCIAL = "social"
    COMPLIANCE = "compliance"

class TimeRange(Enum):
    """Time ranges for analytics"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

@dataclass
class LearningMetric:
    """Individual learning metric"""
    metric_id: str
    metric_type: MetricType
    value: float
    timestamp: datetime
    user_id: Optional[str] = None
    content_id: Optional[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class UserLearningProfile:
    """User's learning analytics profile"""
    user_id: str
    total_xp: int
    level: int
    streak_days: int
    lessons_completed: int
    quizzes_taken: int
    average_score: float
    retention_rate: float
    learning_velocity: float  # XP per day
    preferred_content_types: List[str]
    peak_learning_hours: List[int]
    skill_mastery: Dict[str, float]
    last_active: datetime
    engagement_score: float

@dataclass
class ContentAnalytics:
    """Analytics for specific content"""
    content_id: str
    content_type: str
    total_views: int
    completion_rate: float
    average_score: float
    average_time_spent: float
    difficulty_rating: float
    user_satisfaction: float
    retention_impact: float
    engagement_metrics: Dict[str, float]

class LearningAnalyticsDashboard:
    """Main analytics dashboard for learning metrics"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics_store = {}
        self.user_profiles = {}
        self.content_analytics = {}
        self.aggregated_metrics = {}
        
    def track_metric(self, metric: LearningMetric) -> None:
        """Track a learning metric"""
        if metric.user_id not in self.metrics_store:
            self.metrics_store[metric.user_id] = []
        
        self.metrics_store[metric.user_id].append(metric)
        
        # Update aggregated metrics
        self._update_aggregated_metrics(metric)
        
        self.logger.info(f"Metric tracked: {metric.metric_type.value} = {metric.value}")
    
    def _update_aggregated_metrics(self, metric: LearningMetric) -> None:
        """Update aggregated metrics for real-time dashboard"""
        metric_type = metric.metric_type.value
        timestamp = metric.timestamp.date()
        
        if metric_type not in self.aggregated_metrics:
            self.aggregated_metrics[metric_type] = {}
        
        if timestamp not in self.aggregated_metrics[metric_type]:
            self.aggregated_metrics[metric_type][timestamp] = {
                "count": 0,
                "sum": 0,
                "avg": 0,
                "min": float('inf'),
                "max": float('-inf')
            }
        
        agg = self.aggregated_metrics[metric_type][timestamp]
        agg["count"] += 1
        agg["sum"] += metric.value
        agg["avg"] = agg["sum"] / agg["count"]
        agg["min"] = min(agg["min"], metric.value)
        agg["max"] = max(agg["max"], metric.value)
    
    def get_user_learning_profile(self, user_id: str) -> UserLearningProfile:
        """Get comprehensive learning profile for user"""
        if user_id not in self.metrics_store:
            return self._create_default_profile(user_id)
        
        user_metrics = self.metrics_store[user_id]
        
        # Calculate profile metrics
        total_xp = sum(m.value for m in user_metrics if m.metric_type == MetricType.PERFORMANCE and "xp" in str(m.metadata))
        lessons_completed = len([m for m in user_metrics if m.metric_type == MetricType.ENGAGEMENT and m.metadata.get("action") == "lesson_completed"])
        quizzes_taken = len([m for m in user_metrics if m.metric_type == MetricType.PERFORMANCE and m.metadata.get("action") == "quiz_completed"])
        
        # Calculate average score
        quiz_scores = [m.value for m in user_metrics if m.metric_type == MetricType.PERFORMANCE and m.metadata.get("action") == "quiz_score"]
        average_score = statistics.mean(quiz_scores) if quiz_scores else 0
        
        # Calculate retention rate
        retention_rate = self._calculate_retention_rate(user_id)
        
        # Calculate learning velocity
        learning_velocity = self._calculate_learning_velocity(user_id)
        
        # Determine preferred content types
        preferred_content_types = self._get_preferred_content_types(user_id)
        
        # Determine peak learning hours
        peak_learning_hours = self._get_peak_learning_hours(user_id)
        
        # Calculate skill mastery
        skill_mastery = self._calculate_skill_mastery(user_id)
        
        # Calculate engagement score
        engagement_score = self._calculate_engagement_score(user_id)
        
        profile = UserLearningProfile(
            user_id=user_id,
            total_xp=int(total_xp),
            level=self._calculate_level(total_xp),
            streak_days=self._calculate_streak_days(user_id),
            lessons_completed=lessons_completed,
            quizzes_taken=quizzes_taken,
            average_score=average_score,
            retention_rate=retention_rate,
            learning_velocity=learning_velocity,
            preferred_content_types=preferred_content_types,
            peak_learning_hours=peak_learning_hours,
            skill_mastery=skill_mastery,
            last_active=self._get_last_active(user_id),
            engagement_score=engagement_score
        )
        
        self.user_profiles[user_id] = profile
        return profile
    
    def _create_default_profile(self, user_id: str) -> UserLearningProfile:
        """Create default profile for new user"""
        return UserLearningProfile(
            user_id=user_id,
            total_xp=0,
            level=1,
            streak_days=0,
            lessons_completed=0,
            quizzes_taken=0,
            average_score=0,
            retention_rate=0,
            learning_velocity=0,
            preferred_content_types=[],
            peak_learning_hours=[],
            skill_mastery={},
            last_active=datetime.now(),
            engagement_score=0
        )
    
    def _calculate_retention_rate(self, user_id: str) -> float:
        """Calculate user retention rate"""
        user_metrics = self.metrics_store.get(user_id, [])
        if not user_metrics:
            return 0
        
        # Calculate retention based on daily activity
        activity_days = set()
        for metric in user_metrics:
            activity_days.add(metric.timestamp.date())
        
        # Calculate retention over last 30 days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        total_days = 30
        active_days = len([d for d in activity_days if start_date <= d <= end_date])
        
        return (active_days / total_days) * 100 if total_days > 0 else 0
    
    def _calculate_learning_velocity(self, user_id: str) -> float:
        """Calculate learning velocity (XP per day)"""
        user_metrics = self.metrics_store.get(user_id, [])
        if not user_metrics:
            return 0
        
        # Get XP metrics from last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        xp_metrics = [
            m for m in user_metrics 
            if m.metric_type == MetricType.PERFORMANCE 
            and "xp" in str(m.metadata)
            and start_date <= m.timestamp <= end_date
        ]
        
        if not xp_metrics:
            return 0
        
        total_xp = sum(m.value for m in xp_metrics)
        days_active = len(set(m.timestamp.date() for m in xp_metrics))
        
        return total_xp / days_active if days_active > 0 else 0
    
    def _get_preferred_content_types(self, user_id: str) -> List[str]:
        """Get user's preferred content types"""
        user_metrics = self.metrics_store.get(user_id, [])
        content_type_counts = {}
        
        for metric in user_metrics:
            if metric.metadata and "content_type" in metric.metadata:
                content_type = metric.metadata["content_type"]
                content_type_counts[content_type] = content_type_counts.get(content_type, 0) + 1
        
        # Return top 3 content types
        return sorted(content_type_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    
    def _get_peak_learning_hours(self, user_id: str) -> List[int]:
        """Get user's peak learning hours"""
        user_metrics = self.metrics_store.get(user_id, [])
        hour_counts = {}
        
        for metric in user_metrics:
            hour = metric.timestamp.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        # Return top 3 hours
        return sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    
    def _calculate_skill_mastery(self, user_id: str) -> Dict[str, float]:
        """Calculate skill mastery levels"""
        user_metrics = self.metrics_store.get(user_id, [])
        skill_metrics = {}
        
        for metric in user_metrics:
            if metric.metadata and "skill" in metric.metadata:
                skill = metric.metadata["skill"]
                if skill not in skill_metrics:
                    skill_metrics[skill] = []
                skill_metrics[skill].append(metric.value)
        
        # Calculate mastery percentage for each skill
        mastery = {}
        for skill, values in skill_metrics.items():
            mastery[skill] = statistics.mean(values) if values else 0
        
        return mastery
    
    def _calculate_engagement_score(self, user_id: str) -> float:
        """Calculate overall engagement score"""
        user_metrics = self.metrics_store.get(user_id, [])
        if not user_metrics:
            return 0
        
        # Calculate engagement based on various factors
        engagement_factors = {
            "lesson_completion": 0.3,
            "quiz_participation": 0.2,
            "daily_activity": 0.2,
            "social_interaction": 0.15,
            "content_creation": 0.15
        }
        
        score = 0
        for factor, weight in engagement_factors.items():
            factor_score = self._calculate_factor_score(user_id, factor)
            score += factor_score * weight
        
        return min(score, 100)  # Cap at 100
    
    def _calculate_factor_score(self, user_id: str, factor: str) -> float:
        """Calculate score for specific engagement factor"""
        user_metrics = self.metrics_store.get(user_id, [])
        
        if factor == "lesson_completion":
            completions = len([m for m in user_metrics if m.metadata.get("action") == "lesson_completed"])
            return min(completions * 10, 100)
        
        elif factor == "quiz_participation":
            quizzes = len([m for m in user_metrics if m.metadata.get("action") == "quiz_completed"])
            return min(quizzes * 15, 100)
        
        elif factor == "daily_activity":
            return self._calculate_retention_rate(user_id)
        
        elif factor == "social_interaction":
            social_actions = len([m for m in user_metrics if m.metadata.get("action") in ["share", "comment", "like"]])
            return min(social_actions * 20, 100)
        
        elif factor == "content_creation":
            creations = len([m for m in user_metrics if m.metadata.get("action") == "content_created"])
            return min(creations * 25, 100)
        
        return 0
    
    def _calculate_level(self, total_xp: int) -> int:
        """Calculate user level based on total XP"""
        return max(1, total_xp // 100)
    
    def _calculate_streak_days(self, user_id: str) -> int:
        """Calculate current streak days"""
        user_metrics = self.metrics_store.get(user_id, [])
        if not user_metrics:
            return 0
        
        # Get daily activity
        activity_days = sorted(set(m.timestamp.date() for m in user_metrics))
        if not activity_days:
            return 0
        
        # Calculate current streak
        streak = 0
        current_date = datetime.now().date()
        
        for i in range(len(activity_days)):
            if activity_days[-(i+1)] == current_date - timedelta(days=i):
                streak += 1
            else:
                break
        
        return streak
    
    def _get_last_active(self, user_id: str) -> datetime:
        """Get last active timestamp for user"""
        user_metrics = self.metrics_store.get(user_id, [])
        if not user_metrics:
            return datetime.now()
        
        return max(m.timestamp for m in user_metrics)
    
    def get_content_analytics(self, content_id: str) -> ContentAnalytics:
        """Get analytics for specific content"""
        # Find all metrics related to this content
        content_metrics = []
        for user_metrics in self.metrics_store.values():
            for metric in user_metrics:
                if metric.content_id == content_id:
                    content_metrics.append(metric)
        
        if not content_metrics:
            return self._create_default_content_analytics(content_id)
        
        # Calculate content analytics
        total_views = len([m for m in content_metrics if m.metadata.get("action") == "view"])
        completions = len([m for m in content_metrics if m.metadata.get("action") == "complete"])
        completion_rate = (completions / total_views * 100) if total_views > 0 else 0
        
        scores = [m.value for m in content_metrics if m.metric_type == MetricType.PERFORMANCE and m.metadata.get("action") == "score"]
        average_score = statistics.mean(scores) if scores else 0
        
        time_spent = [m.value for m in content_metrics if m.metadata.get("action") == "time_spent"]
        average_time_spent = statistics.mean(time_spent) if time_spent else 0
        
        return ContentAnalytics(
            content_id=content_id,
            content_type=content_metrics[0].metadata.get("content_type", "unknown"),
            total_views=total_views,
            completion_rate=completion_rate,
            average_score=average_score,
            average_time_spent=average_time_spent,
            difficulty_rating=self._calculate_difficulty_rating(content_metrics),
            user_satisfaction=self._calculate_user_satisfaction(content_metrics),
            retention_impact=self._calculate_retention_impact(content_metrics),
            engagement_metrics=self._calculate_engagement_metrics(content_metrics)
        )
    
    def _create_default_content_analytics(self, content_id: str) -> ContentAnalytics:
        """Create default analytics for content with no data"""
        return ContentAnalytics(
            content_id=content_id,
            content_type="unknown",
            total_views=0,
            completion_rate=0,
            average_score=0,
            average_time_spent=0,
            difficulty_rating=0,
            user_satisfaction=0,
            retention_impact=0,
            engagement_metrics={}
        )
    
    def _calculate_difficulty_rating(self, content_metrics: List[LearningMetric]) -> float:
        """Calculate difficulty rating based on completion rates and scores"""
        completions = [m for m in content_metrics if m.metadata.get("action") == "complete"]
        scores = [m.value for m in content_metrics if m.metric_type == MetricType.PERFORMANCE and m.metadata.get("action") == "score"]
        
        if not scores:
            return 0
        
        # Difficulty is inversely related to average score
        avg_score = statistics.mean(scores)
        return max(0, 100 - avg_score)
    
    def _calculate_user_satisfaction(self, content_metrics: List[LearningMetric]) -> float:
        """Calculate user satisfaction based on ratings and feedback"""
        ratings = [m.value for m in content_metrics if m.metadata.get("action") == "rate"]
        return statistics.mean(ratings) if ratings else 0
    
    def _calculate_retention_impact(self, content_metrics: List[LearningMetric]) -> float:
        """Calculate retention impact of content"""
        # This would be calculated based on user return rates after consuming content
        return 0  # Placeholder
    
    def _calculate_engagement_metrics(self, content_metrics: List[LearningMetric]) -> Dict[str, float]:
        """Calculate various engagement metrics"""
        return {
            "time_on_content": statistics.mean([m.value for m in content_metrics if m.metadata.get("action") == "time_spent"]) if content_metrics else 0,
            "interaction_rate": len([m for m in content_metrics if m.metadata.get("action") in ["click", "scroll", "pause"]]) / len(content_metrics) if content_metrics else 0,
            "completion_rate": len([m for m in content_metrics if m.metadata.get("action") == "complete"]) / len(content_metrics) if content_metrics else 0
        }
    
    def get_dashboard_metrics(self, time_range: TimeRange = TimeRange.WEEKLY) -> Dict[str, Any]:
        """Get comprehensive dashboard metrics"""
        end_date = datetime.now()
        
        if time_range == TimeRange.DAILY:
            start_date = end_date - timedelta(days=1)
        elif time_range == TimeRange.WEEKLY:
            start_date = end_date - timedelta(weeks=1)
        elif time_range == TimeRange.MONTHLY:
            start_date = end_date - timedelta(days=30)
        elif time_range == TimeRange.QUARTERLY:
            start_date = end_date - timedelta(days=90)
        else:  # YEARLY
            start_date = end_date - timedelta(days=365)
        
        # Filter metrics by time range
        filtered_metrics = []
        for user_metrics in self.metrics_store.values():
            for metric in user_metrics:
                if start_date <= metric.timestamp <= end_date:
                    filtered_metrics.append(metric)
        
        # Calculate dashboard metrics
        total_users = len(set(m.user_id for m in filtered_metrics if m.user_id))
        total_lessons = len([m for m in filtered_metrics if m.metadata.get("action") == "lesson_completed"])
        total_quizzes = len([m for m in filtered_metrics if m.metadata.get("action") == "quiz_completed"])
        
        # Calculate average scores
        quiz_scores = [m.value for m in filtered_metrics if m.metric_type == MetricType.PERFORMANCE and m.metadata.get("action") == "quiz_score"]
        average_score = statistics.mean(quiz_scores) if quiz_scores else 0
        
        # Calculate engagement metrics
        engagement_metrics = self._calculate_engagement_metrics(filtered_metrics)
        
        # Calculate retention metrics
        retention_metrics = self._calculate_retention_metrics(filtered_metrics, time_range)
        
        # Calculate progression metrics
        progression_metrics = self._calculate_progression_metrics(filtered_metrics)
        
        # Calculate social metrics
        social_metrics = self._calculate_social_metrics(filtered_metrics)
        
        return {
            "time_range": time_range.value,
            "total_users": total_users,
            "total_lessons": total_lessons,
            "total_quizzes": total_quizzes,
            "average_score": average_score,
            "engagement_metrics": engagement_metrics,
            "retention_metrics": retention_metrics,
            "progression_metrics": progression_metrics,
            "social_metrics": social_metrics,
            "top_performing_content": self._get_top_performing_content(filtered_metrics),
            "user_segments": self._get_user_segments(filtered_metrics),
            "learning_trends": self._get_learning_trends(filtered_metrics, time_range)
        }
    
    def _calculate_retention_metrics(self, metrics: List[LearningMetric], time_range: TimeRange) -> Dict[str, float]:
        """Calculate retention metrics"""
        # Calculate daily active users
        daily_users = {}
        for metric in metrics:
            date = metric.timestamp.date()
            if date not in daily_users:
                daily_users[date] = set()
            daily_users[date].add(metric.user_id)
        
        # Calculate retention rates
        if len(daily_users) < 2:
            return {"daily_active_users": 0, "retention_rate": 0}
        
        dates = sorted(daily_users.keys())
        retention_rate = 0
        
        for i in range(1, len(dates)):
            prev_users = daily_users[dates[i-1]]
            curr_users = daily_users[dates[i]]
            overlap = len(prev_users.intersection(curr_users))
            if len(prev_users) > 0:
                retention_rate += (overlap / len(prev_users)) * 100
        
        retention_rate /= (len(dates) - 1) if len(dates) > 1 else 1
        
        return {
            "daily_active_users": len(daily_users.get(dates[-1], set())) if dates else 0,
            "retention_rate": retention_rate,
            "average_session_duration": self._calculate_average_session_duration(metrics)
        }
    
    def _calculate_progression_metrics(self, metrics: List[LearningMetric]) -> Dict[str, float]:
        """Calculate progression metrics"""
        # Calculate level progression
        user_levels = {}
        for metric in metrics:
            if metric.metadata and "level" in metric.metadata:
                user_id = metric.user_id
                if user_id not in user_levels:
                    user_levels[user_id] = []
                user_levels[user_id].append(metric.metadata["level"])
        
        # Calculate average level progression
        level_progressions = []
        for user_levels_list in user_levels.values():
            if len(user_levels_list) > 1:
                progression = user_levels_list[-1] - user_levels_list[0]
                level_progressions.append(progression)
        
        return {
            "average_level_progression": statistics.mean(level_progressions) if level_progressions else 0,
            "users_leveled_up": len([p for p in level_progressions if p > 0]),
            "skill_mastery_rate": self._calculate_skill_mastery_rate(metrics)
        }
    
    def _calculate_social_metrics(self, metrics: List[LearningMetric]) -> Dict[str, float]:
        """Calculate social metrics"""
        social_actions = [m for m in metrics if m.metadata and m.metadata.get("action") in ["share", "comment", "like", "follow"]]
        
        return {
            "total_social_actions": len(social_actions),
            "shares": len([m for m in social_actions if m.metadata.get("action") == "share"]),
            "comments": len([m for m in social_actions if m.metadata.get("action") == "comment"]),
            "likes": len([m for m in social_actions if m.metadata.get("action") == "like"]),
            "social_engagement_rate": len(social_actions) / len(metrics) * 100 if metrics else 0
        }
    
    def _calculate_average_session_duration(self, metrics: List[LearningMetric]) -> float:
        """Calculate average session duration"""
        session_durations = [m.value for m in metrics if m.metadata and m.metadata.get("action") == "session_duration"]
        return statistics.mean(session_durations) if session_durations else 0
    
    def _calculate_skill_mastery_rate(self, metrics: List[LearningMetric]) -> float:
        """Calculate skill mastery rate"""
        skill_metrics = [m for m in metrics if m.metadata and "skill" in m.metadata]
        if not skill_metrics:
            return 0
        
        # Calculate mastery rate based on skill completion
        mastered_skills = len([m for m in skill_metrics if m.value >= 80])  # 80% threshold
        total_skills = len(skill_metrics)
        
        return (mastered_skills / total_skills * 100) if total_skills > 0 else 0
    
    def _get_top_performing_content(self, metrics: List[LearningMetric]) -> List[Dict[str, Any]]:
        """Get top performing content"""
        content_performance = {}
        
        for metric in metrics:
            if metric.content_id:
                if metric.content_id not in content_performance:
                    content_performance[metric.content_id] = {
                        "views": 0,
                        "completions": 0,
                        "total_score": 0,
                        "score_count": 0
                    }
                
                if metric.metadata and metric.metadata.get("action") == "view":
                    content_performance[metric.content_id]["views"] += 1
                elif metric.metadata and metric.metadata.get("action") == "complete":
                    content_performance[metric.content_id]["completions"] += 1
                elif metric.metric_type == MetricType.PERFORMANCE and metric.metadata.get("action") == "score":
                    content_performance[metric.content_id]["total_score"] += metric.value
                    content_performance[metric.content_id]["score_count"] += 1
        
        # Calculate performance scores
        performance_scores = []
        for content_id, data in content_performance.items():
            completion_rate = (data["completions"] / data["views"] * 100) if data["views"] > 0 else 0
            average_score = (data["total_score"] / data["score_count"]) if data["score_count"] > 0 else 0
            
            performance_score = (completion_rate * 0.6) + (average_score * 0.4)
            
            performance_scores.append({
                "content_id": content_id,
                "performance_score": performance_score,
                "completion_rate": completion_rate,
                "average_score": average_score,
                "views": data["views"]
            })
        
        return sorted(performance_scores, key=lambda x: x["performance_score"], reverse=True)[:10]
    
    def _get_user_segments(self, metrics: List[LearningMetric]) -> Dict[str, int]:
        """Get user segments based on engagement"""
        user_engagement = {}
        
        for metric in metrics:
            user_id = metric.user_id
            if user_id not in user_engagement:
                user_engagement[user_id] = 0
            user_engagement[user_id] += 1
        
        # Segment users based on engagement
        segments = {
            "high_engagement": 0,
            "medium_engagement": 0,
            "low_engagement": 0
        }
        
        for engagement_count in user_engagement.values():
            if engagement_count >= 20:
                segments["high_engagement"] += 1
            elif engagement_count >= 10:
                segments["medium_engagement"] += 1
            else:
                segments["low_engagement"] += 1
        
        return segments
    
    def _get_learning_trends(self, metrics: List[LearningMetric], time_range: TimeRange) -> Dict[str, List[float]]:
        """Get learning trends over time"""
        # Group metrics by time period
        time_periods = {}
        
        for metric in metrics:
            if time_range == TimeRange.DAILY:
                period = metric.timestamp.date()
            elif time_range == TimeRange.WEEKLY:
                period = metric.timestamp.isocalendar()[:2]  # (year, week)
            elif time_range == TimeRange.MONTHLY:
                period = (metric.timestamp.year, metric.timestamp.month)
            else:
                period = metric.timestamp.date()
            
            if period not in time_periods:
                time_periods[period] = []
            time_periods[period].append(metric)
        
        # Calculate trends
        trends = {
            "lessons_completed": [],
            "quizzes_taken": [],
            "average_scores": [],
            "user_engagement": []
        }
        
        for period_metrics in time_periods.values():
            lessons = len([m for m in period_metrics if m.metadata and m.metadata.get("action") == "lesson_completed"])
            quizzes = len([m for m in period_metrics if m.metadata and m.metadata.get("action") == "quiz_completed"])
            scores = [m.value for m in period_metrics if m.metric_type == MetricType.PERFORMANCE and m.metadata.get("action") == "quiz_score"]
            avg_score = statistics.mean(scores) if scores else 0
            engagement = len(period_metrics)
            
            trends["lessons_completed"].append(lessons)
            trends["quizzes_taken"].append(quizzes)
            trends["average_scores"].append(avg_score)
            trends["user_engagement"].append(engagement)
        
        return trends
