"""
Daily Brief Models
Database models for daily brief, streaks, progress tracking, and user engagement
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import json
import uuid

User = get_user_model()


class DailyBrief(models.Model):
    """Daily brief generated for each user"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_briefs')
    date = models.DateField(default=timezone.now, db_index=True)
    
    # Content sections
    market_summary = models.TextField(help_text="Plain English market update (30 sec)")
    personalized_action = models.TextField(help_text="One personalized action (30 sec)")
    action_type = models.CharField(
        max_length=50,
        choices=[
            ('review_portfolio', 'Review Portfolio'),
            ('learn_lesson', 'Learn Lesson'),
            ('check_tax', 'Check Tax Opportunities'),
            ('rebalance', 'Rebalance Portfolio'),
            ('set_goal', 'Set Goal'),
        ],
        default='learn_lesson'
    )
    lesson_id = models.CharField(max_length=100, blank=True, null=True, help_text="ID of the 2-min lesson")
    lesson_title = models.CharField(max_length=200, blank=True, null=True)
    lesson_content = models.TextField(blank=True, null=True, help_text="2-minute lesson content")
    
    # Personalization
    experience_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ],
        default='beginner'
    )
    goals_referenced = models.JSONField(default=list, help_text="List of user goals referenced")
    
    # Status
    is_completed = models.BooleanField(default=False, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent_seconds = models.IntegerField(null=True, blank=True, help_text="Time spent reading brief")
    
    # Generated metadata
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'daily_briefs'
        unique_together = ['user', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['user', 'is_completed']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.date} ({'Completed' if self.is_completed else 'Pending'})"


class UserStreak(models.Model):
    """Tracks user's daily brief completion streak"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='streak')
    current_streak = models.IntegerField(default=0, help_text="Current consecutive days")
    longest_streak = models.IntegerField(default=0, help_text="Longest streak ever achieved")
    last_completed_date = models.DateField(null=True, blank=True, help_text="Last date brief was completed")
    streak_started_at = models.DateField(null=True, blank=True, help_text="When current streak started")
    
    # Milestones
    last_milestone_reached = models.IntegerField(default=0, help_text="Last milestone (3, 7, 30, etc.)")
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_streaks'
    
    def __str__(self):
        return f"{self.user.email} - {self.current_streak} day streak"
    
    def update_streak(self, completed_date=None):
        """Update streak when brief is completed"""
        from datetime import timedelta
        
        if completed_date is None:
            completed_date = timezone.now().date()
        
        # If no last completed date, start new streak
        if not self.last_completed_date:
            self.current_streak = 1
            self.streak_started_at = completed_date
            self.last_completed_date = completed_date
            if self.current_streak > self.longest_streak:
                self.longest_streak = self.current_streak
            self.save()
            return
        
        # Check if consecutive day
        days_diff = (completed_date - self.last_completed_date).days
        
        if days_diff == 1:
            # Consecutive day - increment streak
            self.current_streak += 1
            self.last_completed_date = completed_date
        elif days_diff == 0:
            # Same day - don't change streak
            pass
        else:
            # Streak broken - start new streak
            self.current_streak = 1
            self.streak_started_at = completed_date
            self.last_completed_date = completed_date
        
        # Update longest streak
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        
        self.save()


class UserProgress(models.Model):
    """Tracks user's learning and engagement progress"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='progress')
    
    # Learning progress
    concepts_learned = models.IntegerField(default=0, help_text="Total concepts learned")
    lessons_completed = models.IntegerField(default=0, help_text="Total lessons completed")
    completed_lesson_ids = models.JSONField(
        default=list,
        help_text="List of lesson IDs the user has completed (prevents double-counting)"
    )
    current_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ],
        default='beginner'
    )
    
    # Weekly progress (resets weekly)
    weekly_briefs_completed = models.IntegerField(default=0, help_text="Briefs completed this week")
    weekly_lessons_completed = models.IntegerField(default=0, help_text="Lessons completed this week")
    weekly_goal = models.IntegerField(default=5, help_text="Weekly goal (default: 5 briefs)")
    week_start_date = models.DateField(default=timezone.now, help_text="Start of current week")
    
    # Monthly progress (resets monthly)
    monthly_lessons_completed = models.IntegerField(default=0, help_text="Lessons completed this month")
    monthly_goal = models.IntegerField(default=20, help_text="Monthly goal (default: 20 lessons)")
    month_start_date = models.DateField(default=timezone.now, help_text="Start of current month")
    
    # Confidence score (1-10)
    confidence_score = models.IntegerField(default=5, help_text="User confidence score (1-10)")
    confidence_history = models.JSONField(
        default=list,
        help_text="Array of {date, score} objects for tracking confidence over time"
    )
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_progress'
    
    def __str__(self):
        return f"{self.user.email} - Level: {self.current_level}, Confidence: {self.confidence_score}/10"
    
    def update_confidence(self, score: int, date=None):
        """Update confidence score and history"""
        if date is None:
            date = timezone.now().date()
        
        self.confidence_score = max(1, min(10, score))  # Clamp between 1-10
        
        # Add to history (keep last 30 entries)
        history = self.confidence_history or []
        history.append({
            'date': date.isoformat(),
            'score': self.confidence_score
        })
        self.confidence_history = history[-30:]  # Keep last 30 entries
        
        self.save()
    
    def reset_weekly_progress(self):
        """Reset weekly progress (call on Monday)"""
        self.weekly_briefs_completed = 0
        self.weekly_lessons_completed = 0
        self.week_start_date = timezone.now().date()
        self.save()
    
    def reset_monthly_progress(self):
        """Reset monthly progress (call on 1st of month)"""
        self.monthly_lessons_completed = 0
        self.month_start_date = timezone.now().date()
        self.save()


class UserAchievement(models.Model):
    """User achievements/badges"""
    
    ACHIEVEMENT_TYPES = [
        ('early_bird', 'Early Bird'),
        ('consistent_learner', 'Consistent Learner'),
        ('first_investment', 'First Investment'),
        ('first_lesson', 'First Lesson'),
        ('goal_setter', 'Goal Setter'),
        ('streak_3', '3 Day Streak'),
        ('streak_7', '7 Day Streak'),
        ('streak_30', '30 Day Streak'),
        ('lessons_10', '10 Lessons Learned'),
        ('lessons_50', '50 Lessons Learned'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement_type = models.CharField(max_length=50, choices=ACHIEVEMENT_TYPES)
    unlocked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_achievements'
        unique_together = ['user', 'achievement_type']
        ordering = ['-unlocked_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.get_achievement_type_display()}"


class DailyBriefCompletion(models.Model):
    """Tracks when user completes daily brief (for analytics)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brief = models.ForeignKey(DailyBrief, on_delete=models.CASCADE, related_name='completions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='brief_completions')
    
    # Completion metrics
    time_spent_seconds = models.IntegerField(help_text="Time spent reading brief")
    sections_viewed = models.JSONField(
        default=list,
        help_text="Which sections user viewed: ['market_summary', 'action', 'lesson']"
    )
    lesson_completed = models.BooleanField(default=False)
    action_completed = models.BooleanField(default=False)
    
    completed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'daily_brief_completions'
        ordering = ['-completed_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.brief.date} ({self.time_spent_seconds}s)"

