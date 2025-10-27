#!/usr/bin/env python3
"""
RichesReach Adaptive Mastery Engine
Beats Fidelity with IRT + Spaced Repetition + Voice-First Learning

This implements Item Response Theory (IRT) for adaptive difficulty
and spaced repetition (SM-2 variant) for long-term retention.
"""

import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import redis
from enum import Enum

class BloomLevel(Enum):
    """Bloom's Taxonomy levels for learning objectives"""
    REMEMBER = "Remember"
    UNDERSTAND = "Understand"
    APPLY = "Apply"
    ANALYZE = "Analyze"
    EVALUATE = "Evaluate"
    CREATE = "Create"

@dataclass
class IRTParameters:
    """Item Response Theory parameters for adaptive difficulty"""
    a: float  # discrimination (how well item distinguishes ability)
    b: float  # difficulty (ability level where 50% success)
    c: float  # guessing parameter (probability of correct guess)

@dataclass
class ContentItem:
    """Educational content item with IRT parameters"""
    id: str
    prompt: str
    options: List[str]
    correct: int
    taxonomy: BloomLevel
    skills: List[str]  # e.g., ["options:spreads", "risk:greeks:delta"]
    irt: IRTParameters
    sources: List[str]
    regime_tags: List[str]  # e.g., ["BULL", "BEAR", "SIDEWAYS"]
    voice_hint: str  # Suggested voice for narration
    difficulty_estimate: float = 0.0
    times_shown: int = 0
    times_correct: int = 0

@dataclass
class UserProgress:
    """User's learning progress with IRT ability estimate"""
    user_id: str
    xp: int = 0
    level: int = 1
    streak_days: int = 0
    badges: List[str] = None
    last_login: datetime = None
    theta: float = 0.0  # IRT ability estimate (-3 to +3)
    next_review_at: datetime = None
    skill_mastery: Dict[str, float] = None  # skill -> mastery level
    review_queue: List[str] = None  # item IDs for spaced repetition
    
    def __post_init__(self):
        if self.badges is None:
            self.badges = []
        if self.skill_mastery is None:
            self.skill_mastery = {}
        if self.review_queue is None:
            self.review_queue = []

class AdaptiveMasteryEngine:
    """
    Core adaptive learning engine that beats Fidelity's static approach
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.r = redis_client
        self.xp_per_lesson = 10
        self.streak_bonus = 0.1  # 10% XP boost per streak day
        self.learning_rate = 0.07  # IRT learning rate
        self.min_theta = -3.0
        self.max_theta = 3.0
        
    def prob_correct(self, theta: float, irt: IRTParameters) -> float:
        """
        3-Parameter Logistic (3PL) model for probability of correct response
        P(θ) = c + (1-c) / (1 + exp(-a*(θ - b)))
        """
        if irt.a == 0:  # Avoid division by zero
            return 0.5
        
        exponent = -irt.a * (theta - irt.b)
        return irt.c + (1 - irt.c) / (1 + math.exp(exponent))
    
    def update_theta(self, theta: float, irt: IRTParameters, correct: bool) -> float:
        """
        Update ability estimate using gradient descent on IRT model
        """
        p = self.prob_correct(theta, irt)
        grad = (1 if correct else 0) - p
        new_theta = theta + self.learning_rate * grad * irt.a
        
        # Clamp to reasonable range
        return max(self.min_theta, min(self.max_theta, new_theta))
    
    def schedule_next_interval(self, easiness: float, repetitions: int) -> int:
        """
        SM-2 spaced repetition scheduling
        Returns days until next review
        """
        if repetitions == 0:
            return 1
        elif repetitions == 1:
            return 6
        else:
            return max(1, int((repetitions - 1) * easiness * 2))
    
    def get_progress(self, user_id: str) -> UserProgress:
        """Get user's learning progress"""
        data = self.r.get(f"tutor_progress:{user_id}")
        if data:
            progress_data = json.loads(data)
            # Convert datetime strings back to datetime objects
            if progress_data.get('last_login'):
                progress_data['last_login'] = datetime.fromisoformat(progress_data['last_login'])
            if progress_data.get('next_review_at'):
                progress_data['next_review_at'] = datetime.fromisoformat(progress_data['next_review_at'])
            return UserProgress(**progress_data)
        return UserProgress(user_id=user_id)
    
    def save_progress(self, user_id: str, progress: UserProgress):
        """Save user's learning progress"""
        progress_data = asdict(progress)
        # Convert datetime objects to strings for JSON serialization
        if progress_data.get('last_login'):
            progress_data['last_login'] = progress_data['last_login'].isoformat()
        if progress_data.get('next_review_at'):
            progress_data['next_review_at'] = progress_data['next_review_at'].isoformat()
        
        self.r.set(f"tutor_progress:{user_id}", json.dumps(progress_data))
    
    def check_streak(self, user_id: str) -> int:
        """Check and update user's learning streak"""
        progress = self.get_progress(user_id)
        today = datetime.now().date()
        
        if progress.last_login:
            last_date = progress.last_login.date()
            if (today - last_date).days == 1:
                progress.streak_days += 1
            elif (today - last_date).days > 1:
                progress.streak_days = 1  # Reset streak
        else:
            progress.streak_days = 1
        
        progress.last_login = datetime.now()
        self.save_progress(user_id, progress)
        return progress.streak_days
    
    def award_xp(self, user_id: str, amount: int, skill: str = None) -> UserProgress:
        """Award XP and update skill mastery"""
        progress = self.get_progress(user_id)
        
        # Apply streak bonus
        streak_multiplier = 1 + (progress.streak_days * self.streak_bonus)
        total_xp = int(amount * streak_multiplier)
        
        progress.xp += total_xp
        
        # Level up check
        xp_needed = progress.level * 100
        if progress.xp >= xp_needed:
            progress.level += 1
            progress.badges.append(f"Level {progress.level} Achiever")
        
        # Update skill mastery
        if skill:
            current_mastery = progress.skill_mastery.get(skill, 0.0)
            # Skill mastery increases with XP earned
            progress.skill_mastery[skill] = min(1.0, current_mastery + (total_xp / 1000))
        
        self.save_progress(user_id, progress)
        return progress
    
    def select_next_item(self, user_id: str, target_skills: List[str] = None) -> Optional[ContentItem]:
        """
        Select next item based on IRT ability estimate and spaced repetition
        """
        progress = self.get_progress(user_id)
        
        # Check if there are items due for review
        if progress.review_queue:
            # Get items from review queue first
            for item_id in progress.review_queue[:5]:  # Check next 5 items
                item_data = self.r.get(f"content_item:{item_id}")
                if item_data:
                    item = ContentItem(**json.loads(item_data))
                    # Check if item matches target skills
                    if not target_skills or any(skill in item.skills for skill in target_skills):
                        return item
        
        # If no review items, select new item near user's ability level
        theta_range = 0.3  # Select items within ±0.3 of user's ability
        min_difficulty = progress.theta - theta_range
        max_difficulty = progress.theta + theta_range
        
        # Get all available items (in production, this would be filtered by skills)
        all_items = self._get_available_items()
        
        # Filter by difficulty range and target skills
        suitable_items = []
        for item in all_items:
            if min_difficulty <= item.irt.b <= max_difficulty:
                if not target_skills or any(skill in item.skills for skill in target_skills):
                    suitable_items.append(item)
        
        if suitable_items:
            # Select item with highest discrimination (a parameter) for better measurement
            return max(suitable_items, key=lambda x: x.irt.a)
        
        return None
    
    def record_response(self, user_id: str, item_id: str, correct: bool, response_time: float = None):
        """
        Record user response and update ability estimate
        """
        progress = self.get_progress(user_id)
        
        # Get item data
        item_data = self.r.get(f"content_item:{item_id}")
        if not item_data:
            return
        
        item = ContentItem(**json.loads(item_data))
        
        # Update IRT ability estimate
        old_theta = progress.theta
        progress.theta = self.update_theta(progress.theta, item.irt, correct)
        
        # Update item statistics
        item.times_shown += 1
        if correct:
            item.times_correct += 1
        
        # Calculate easiness factor for spaced repetition
        easiness = 2.5  # Default easiness
        if correct:
            easiness = min(2.5, easiness + 0.1)
        else:
            easiness = max(1.3, easiness - 0.2)
        
        # Schedule next review
        repetitions = item.times_shown
        interval_days = self.schedule_next_interval(easiness, repetitions)
        
        # Add to review queue
        review_date = datetime.now() + timedelta(days=interval_days)
        if item_id not in progress.review_queue:
            progress.review_queue.append(item_id)
        
        # Award XP based on difficulty and correctness
        base_xp = 10
        if correct:
            # Bonus XP for difficult items
            difficulty_bonus = int((item.irt.b - old_theta) * 5)
            xp_earned = base_xp + max(0, difficulty_bonus)
        else:
            xp_earned = base_xp // 2  # Half XP for incorrect answers
        
        # Award XP for each skill
        for skill in item.skills:
            self.award_xp(user_id, xp_earned, skill)
        
        # Update progress
        self.save_progress(user_id, progress)
        
        # Save updated item
        self.r.set(f"content_item:{item_id}", json.dumps(asdict(item)))
        
        return {
            "theta_change": progress.theta - old_theta,
            "xp_earned": xp_earned,
            "next_review_days": interval_days,
            "easiness": easiness
        }
    
    def _get_available_items(self) -> List[ContentItem]:
        """Get all available content items (mock implementation)"""
        # In production, this would query a database
        # For now, return some sample items
        return [
            ContentItem(
                id="opt_bull_call_001",
                prompt="In a bull regime, which leg tightens risk in a bull call spread?",
                options=["Buy lower strike call", "Sell higher strike call", "Buy put", "Sell put"],
                correct=1,
                taxonomy=BloomLevel.APPLY,
                skills=["options:spreads", "risk:greeks:delta"],
                irt=IRTParameters(a=1.25, b=-0.15, c=0.18),
                sources=["CBOE handbook §2.3"],
                regime_tags=["BULL"],
                voice_hint="Shimmer"
            ),
            ContentItem(
                id="vol_hedge_001",
                prompt="What's the primary purpose of a volatility hedge in sideways markets?",
                options=["Profit from price movement", "Protect against volatility", "Generate income", "Reduce margin"],
                correct=1,
                taxonomy=BloomLevel.UNDERSTAND,
                skills=["volatility:hedging", "risk:management"],
                irt=IRTParameters(a=1.0, b=0.5, c=0.25),
                sources=["Options Volatility & Pricing by Natenberg"],
                regime_tags=["SIDEWAYS"],
                voice_hint="Nova"
            ),
            ContentItem(
                id="hft_scalping_001",
                prompt="In HFT scalping, what's the typical profit target in basis points?",
                options=["0.1-0.5 bps", "1-2 bps", "5-10 bps", "20+ bps"],
                correct=1,
                taxonomy=BloomLevel.REMEMBER,
                skills=["hft:scalping", "microstructure"],
                irt=IRTParameters(a=0.8, b=1.2, c=0.2),
                sources=["High-Frequency Trading by Aldridge"],
                regime_tags=["BULL", "BEAR"],
                voice_hint="Echo"
            )
        ]
    
    def get_learning_analytics(self, user_id: str) -> Dict:
        """Get comprehensive learning analytics"""
        progress = self.get_progress(user_id)
        
        # Calculate mastery percentages
        skill_mastery = {}
        for skill, mastery in progress.skill_mastery.items():
            skill_mastery[skill] = {
                "mastery_level": mastery,
                "mastery_percentage": int(mastery * 100),
                "status": "Master" if mastery >= 0.8 else "Learning" if mastery >= 0.5 else "Beginner"
            }
        
        return {
            "user_id": user_id,
            "current_level": progress.level,
            "total_xp": progress.xp,
            "streak_days": progress.streak_days,
            "ability_estimate": progress.theta,
            "skill_mastery": skill_mastery,
            "badges_earned": progress.badges,
            "items_in_review": len(progress.review_queue),
            "next_level_xp": (progress.level + 1) * 100 - progress.xp,
            "learning_streak_status": "On Fire" if progress.streak_days >= 7 else "Building" if progress.streak_days >= 3 else "Starting"
        }

# Global instance
def get_adaptive_engine() -> AdaptiveMasteryEngine:
    """Get the global adaptive mastery engine instance"""
    import redis
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    return AdaptiveMasteryEngine(redis_client)
