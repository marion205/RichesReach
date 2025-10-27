#!/usr/bin/env python3
"""
RichesReach Gamified Tutor
Duolingo-Style Learning with Voice Integration

Beats Fidelity by making learning addictive, adaptive, and voice-first.
Implements streaks, leagues, badges, and live-market simulations.
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import redis
from enum import Enum

from .adaptive_engine import AdaptiveMasteryEngine, ContentItem, UserProgress, BloomLevel

class QuestType(Enum):
    """Types of learning quests"""
    DAILY_TRADE_QUEST = "daily_trade_quest"
    REGIME_MASTERY = "regime_mastery"
    VOLATILITY_DUEL = "volatility_duel"
    BIPOC_WEALTH_CHALLENGE = "bipoc_wealth_challenge"
    HFT_SCALPING_SIM = "hft_scalping_sim"

class BadgeType(Enum):
    """Types of achievement badges"""
    STREAK_MASTER = "streak_master"
    REGIME_GURU = "regime_guru"
    VOLATILITY_WIZARD = "volatility_wizard"
    OPTIONS_NINJA = "options_ninja"
    HFT_SCALPER = "hft_scalper"
    BIPOC_WEALTH_BUILDER = "bipoc_wealth_builder"
    VOICE_COMMANDER = "voice_commander"
    COMMUNITY_CHAMPION = "community_champion"

@dataclass
class Quest:
    """Learning quest with gamification elements"""
    id: str
    title: str
    description: str
    quest_type: QuestType
    difficulty: int  # 1-5
    xp_reward: int
    time_limit_minutes: int
    required_skills: List[str]
    regime_context: str
    voice_narration: str
    completion_criteria: Dict
    is_active: bool = True
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class LeagueEntry:
    """League ranking entry"""
    user_id: str
    username: str
    xp_week: int
    rank: int
    circle: str
    avatar_url: str = None
    streak_days: int = 0
    badges_count: int = 0

@dataclass
class LiveSimSession:
    """Live market simulation session"""
    id: str
    user_id: str
    symbol: str
    mode: str  # "paper", "demo", "practice"
    start_time: datetime
    end_time: datetime = None
    initial_balance: float
    current_balance: float
    trades_executed: List[Dict]
    learning_objectives: List[str]
    voice_feedback_enabled: bool = True
    regime_context: str = None

class GamifiedTutor:
    """
    Main gamified tutor that beats Fidelity's static approach
    """
    
    def __init__(self, adaptive_engine: AdaptiveMasteryEngine, redis_client: redis.Redis):
        self.engine = adaptive_engine
        self.r = redis_client
        
        # Gamification parameters
        self.xp_per_lesson = 10
        self.streak_freeze_cost = 100  # XP cost to freeze streak
        self.league_reset_days = 7
        self.max_hearts = 5
        self.heart_regen_minutes = 30
        
    def generate_lesson(self, user_id: str, topic: str, regime: str = None) -> Dict:
        """
        Generate adaptive lesson with gamification
        """
        progress = self.engine.get_progress(user_id)
        
        # Check streak
        streak = self.engine.check_streak(user_id)
        
        # Select next item based on user's ability
        target_skills = self._extract_skills_from_topic(topic)
        item = self.engine.select_next_item(user_id, target_skills)
        
        if not item:
            return {
                "error": "No suitable content found",
                "suggestion": "Try a different topic or complete prerequisite lessons"
            }
        
        # Generate lesson content with AI (mock for now)
        lesson_content = self._generate_lesson_content(item, regime)
        
        # Create quiz questions
        quiz_questions = self._create_quiz_questions(item, lesson_content)
        
        # Calculate XP rewards
        base_xp = self.xp_per_lesson
        streak_bonus = int(base_xp * streak * 0.1)  # 10% bonus per streak day
        difficulty_bonus = int(base_xp * abs(item.irt.b) * 0.2)  # Bonus for difficult items
        
        total_xp = base_xp + streak_bonus + difficulty_bonus
        
        return {
            "lesson_id": f"lesson_{item.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "title": lesson_content["title"],
            "text": lesson_content["text"],
            "voice_narration": item.voice_hint,
            "quiz": quiz_questions,
            "xp_earned": total_xp,
            "streak": streak,
            "next_unlock": f"Level {progress.level + 1} at {(progress.level + 1) * 100} XP",
            "difficulty": self._get_difficulty_label(item.irt.b),
            "sources": item.sources,
            "regime_context": regime or "GENERAL",
            "estimated_time_minutes": len(quiz_questions) * 2 + 3,  # 2 min per Q + 3 min reading
            "skills_targeted": item.skills,
            "bloom_level": item.taxonomy.value
        }
    
    def submit_quiz(self, user_id: str, lesson_id: str, answers: List[int]) -> Dict:
        """
        Grade quiz and update progress
        """
        # Get lesson data (in production, this would be stored)
        # For now, we'll use the adaptive engine to record responses
        
        progress = self.engine.get_progress(user_id)
        correct_count = 0
        total_questions = len(answers)
        
        # Mock grading (in production, this would check against correct answers)
        for i, answer in enumerate(answers):
            # Simulate 80% accuracy for demo
            is_correct = random.random() < 0.8
            if is_correct:
                correct_count += 1
            
            # Record response in adaptive engine
            item_id = f"item_{i}"  # Mock item ID
            self.engine.record_response(user_id, item_id, is_correct)
        
        score = (correct_count / total_questions) * 100
        
        # Calculate XP bonus based on score
        score_bonus = int(score / 10)  # 1 XP per 10% score
        total_xp = self.xp_per_lesson + score_bonus
        
        # Award XP
        progress = self.engine.award_xp(user_id, total_xp)
        
        # Check for badges
        new_badges = self._check_badge_earnings(user_id, score, progress)
        
        # Generate feedback
        feedback = self._generate_feedback(score, progress)
        
        return {
            "score": score,
            "xp_bonus": score_bonus,
            "total_xp": total_xp,
            "feedback": feedback,
            "badges_earned": new_badges,
            "next_recommendation": self._get_next_recommendation(score, progress),
            "streak_status": f"{progress.streak_days} day streak!",
            "level_progress": {
                "current_level": progress.level,
                "current_xp": progress.xp,
                "next_level_xp": (progress.level + 1) * 100,
                "progress_percentage": int((progress.xp % 100) / 100 * 100)
            }
        }
    
    def start_live_sim(self, user_id: str, symbol: str, mode: str = "paper") -> LiveSimSession:
        """
        Start live market simulation for hands-on learning
        """
        session_id = f"sim_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Get current market regime
        regime = self._get_current_regime()
        
        # Create simulation session
        session = LiveSimSession(
            id=session_id,
            user_id=user_id,
            symbol=symbol,
            mode=mode,
            start_time=datetime.now(),
            initial_balance=10000.0,  # $10k paper trading
            current_balance=10000.0,
            trades_executed=[],
            learning_objectives=self._get_sim_objectives(symbol, regime),
            regime_context=regime
        )
        
        # Store session
        self.r.set(f"sim_session:{session_id}", json.dumps(asdict(session), default=str))
        
        return session
    
    def execute_sim_trade(self, session_id: str, trade_data: Dict) -> Dict:
        """
        Execute trade in simulation and provide learning feedback
        """
        # Get session
        session_data = self.r.get(f"sim_session:{session_id}")
        if not session_data:
            return {"error": "Session not found"}
        
        session_dict = json.loads(session_data)
        session = LiveSimSession(**session_dict)
        
        # Mock trade execution (in production, this would use real market data)
        trade_result = self._simulate_trade_execution(trade_data, session.symbol)
        
        # Update session
        session.trades_executed.append({
            "timestamp": datetime.now().isoformat(),
            "trade_data": trade_data,
            "result": trade_result
        })
        
        session.current_balance += trade_result["pnl"]
        
        # Generate learning feedback
        feedback = self._generate_trade_feedback(trade_result, session.learning_objectives)
        
        # Award XP for successful trades
        if trade_result["pnl"] > 0:
            xp_earned = int(trade_result["pnl"] * 10)  # 1 XP per $0.10 profit
            self.engine.award_xp(session.user_id, xp_earned, "trading:simulation")
        
        # Update session
        self.r.set(f"sim_session:{session_id}", json.dumps(asdict(session), default=str))
        
        return {
            "trade_result": trade_result,
            "feedback": feedback,
            "xp_earned": xp_earned if trade_result["pnl"] > 0 else 0,
            "new_balance": session.current_balance,
            "learning_objectives_progress": self._update_objectives_progress(session)
        }
    
    def get_league_rankings(self, circle: str = "general", period: str = "week") -> List[LeagueEntry]:
        """
        Get league rankings for gamified competition
        """
        # Mock league data (in production, this would query user progress)
        mock_entries = [
            LeagueEntry(
                user_id="user_001",
                username="TradingPro2025",
                xp_week=1250,
                rank=1,
                circle=circle,
                streak_days=15,
                badges_count=8
            ),
            LeagueEntry(
                user_id="user_002",
                username="BIPOCWealthBuilder",
                xp_week=1100,
                rank=2,
                circle=circle,
                streak_days=12,
                badges_count=6
            ),
            LeagueEntry(
                user_id="user_003",
                username="OptionsNinja",
                xp_week=950,
                rank=3,
                circle=circle,
                streak_days=8,
                badges_count=5
            )
        ]
        
        return mock_entries
    
    def create_daily_quest(self, user_id: str) -> Quest:
        """
        Create personalized daily quest based on user's learning progress
        """
        progress = self.engine.get_progress(user_id)
        regime = self._get_current_regime()
        
        # Select quest type based on user's skill gaps
        quest_type = self._select_quest_type(progress)
        
        quest = Quest(
            id=f"daily_{user_id}_{datetime.now().strftime('%Y%m%d')}",
            title=self._get_quest_title(quest_type, regime),
            description=self._get_quest_description(quest_type, regime),
            quest_type=quest_type,
            difficulty=self._calculate_quest_difficulty(progress),
            xp_reward=self._calculate_quest_xp_reward(progress),
            time_limit_minutes=15,
            required_skills=self._get_quest_skills(quest_type),
            regime_context=regime,
            voice_narration="Nova",
            completion_criteria=self._get_completion_criteria(quest_type)
        )
        
        # Store quest
        self.r.set(f"daily_quest:{user_id}:{datetime.now().strftime('%Y%m%d')}", 
                  json.dumps(asdict(quest), default=str))
        
        return quest
    
    def claim_streak_freeze(self, user_id: str) -> Dict:
        """
        Allow user to freeze their streak using XP
        """
        progress = self.engine.get_progress(user_id)
        
        if progress.xp < self.streak_freeze_cost:
            return {
                "success": False,
                "message": f"Need {self.streak_freeze_cost} XP to freeze streak. You have {progress.xp} XP.",
                "xp_needed": self.streak_freeze_cost - progress.xp
            }
        
        # Deduct XP and freeze streak
        progress.xp -= self.streak_freeze_cost
        progress.badges.append("Streak Protector")
        
        self.engine.save_progress(user_id, progress)
        
        return {
            "success": True,
            "message": "Streak frozen! You won't lose it if you miss a day.",
            "xp_remaining": progress.xp,
            "streak_days": progress.streak_days
        }
    
    def _extract_skills_from_topic(self, topic: str) -> List[str]:
        """Extract skills from topic string"""
        skill_mapping = {
            "options": ["options:basics", "options:spreads"],
            "volatility": ["volatility:hedging", "volatility:trading"],
            "hft": ["hft:scalping", "hft:market_making"],
            "risk": ["risk:management", "risk:greeks"],
            "regime": ["regime:detection", "regime:adaptation"]
        }
        
        topic_lower = topic.lower()
        skills = []
        for key, skill_list in skill_mapping.items():
            if key in topic_lower:
                skills.extend(skill_list)
        
        return skills if skills else ["general:basics"]
    
    def _generate_lesson_content(self, item: ContentItem, regime: str) -> Dict:
        """Generate lesson content with AI (mock implementation)"""
        return {
            "title": f"Mastering {item.skills[0].split(':')[1].title()} in {regime or 'Any'} Markets",
            "text": f"""
            Welcome to your personalized lesson on {item.prompt.lower()}.
            
            In today's {regime or 'current'} market regime, understanding this concept is crucial for successful trading.
            
            Key Learning Points:
            • This concept applies directly to real market conditions
            • You'll practice with interactive examples
            • Voice feedback will guide your understanding
            
            Ready to test your knowledge? Let's begin!
            """,
            "voice_script": f"Welcome to your lesson on {item.skills[0].split(':')[1]}. I'm {item.voice_hint}, and I'll guide you through this important concept."
        }
    
    def _create_quiz_questions(self, item: ContentItem, lesson_content: Dict) -> List[Dict]:
        """Create quiz questions from content item"""
        return [
            {
                "id": f"q1_{item.id}",
                "question": item.prompt,
                "options": item.options,
                "correct": item.correct,
                "explanation": f"This is the correct answer because...",
                "voice_hint": item.voice_hint
            }
        ]
    
    def _get_difficulty_label(self, difficulty: float) -> str:
        """Get human-readable difficulty label"""
        if difficulty < -1:
            return "Beginner"
        elif difficulty < 0:
            return "Easy"
        elif difficulty < 1:
            return "Intermediate"
        elif difficulty < 2:
            return "Advanced"
        else:
            return "Expert"
    
    def _check_badge_earnings(self, user_id: str, score: float, progress: UserProgress) -> List[str]:
        """Check for new badge earnings"""
        new_badges = []
        
        if score >= 90 and "Quiz Ace" not in progress.badges:
            new_badges.append("Quiz Ace")
            progress.badges.append("Quiz Ace")
        
        if progress.streak_days >= 7 and "Streak Master" not in progress.badges:
            new_badges.append("Streak Master")
            progress.badges.append("Streak Master")
        
        if progress.level >= 5 and "Level 5 Achiever" not in progress.badges:
            new_badges.append("Level 5 Achiever")
            progress.badges.append("Level 5 Achiever")
        
        if new_badges:
            self.engine.save_progress(user_id, progress)
        
        return new_badges
    
    def _generate_feedback(self, score: float, progress: UserProgress) -> str:
        """Generate personalized feedback based on performance"""
        if score >= 90:
            return f"Outstanding! You're mastering this material. Your {progress.streak_days}-day streak shows real dedication!"
        elif score >= 70:
            return f"Great job! You're making solid progress. Keep up the momentum!"
        elif score >= 50:
            return f"Good effort! Review the material and try again. Every expert was once a beginner."
        else:
            return f"Don't give up! Learning takes time. Try the lesson again or ask for help in your Circles."
    
    def _get_next_recommendation(self, score: float, progress: UserProgress) -> str:
        """Get next learning recommendation"""
        if score >= 80:
            return "Ready for advanced concepts? Try our HFT simulation!"
        elif score >= 60:
            return "Practice more with similar questions to build confidence."
        else:
            return "Review the lesson material and try the quiz again."
    
    def _get_current_regime(self) -> str:
        """Get current market regime (mock implementation)"""
        regimes = ["BULL", "BEAR", "SIDEWAYS", "HIGH_VOL"]
        return random.choice(regimes)
    
    def _get_sim_objectives(self, symbol: str, regime: str) -> List[str]:
        """Get learning objectives for simulation"""
        return [
            f"Understand {symbol} price action in {regime} markets",
            "Practice risk management techniques",
            "Learn to read market microstructure",
            "Develop trading discipline"
        ]
    
    def _simulate_trade_execution(self, trade_data: Dict, symbol: str) -> Dict:
        """Simulate trade execution (mock implementation)"""
        # Mock trade result
        pnl = random.uniform(-50, 100)  # Random P&L between -$50 and +$100
        
        return {
            "executed": True,
            "pnl": pnl,
            "execution_price": 150.0 + random.uniform(-5, 5),
            "slippage": random.uniform(0, 0.1),
            "commission": 1.0,
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_trade_feedback(self, trade_result: Dict, objectives: List[str]) -> str:
        """Generate learning feedback for trade"""
        if trade_result["pnl"] > 0:
            return f"Excellent trade! You made ${trade_result['pnl']:.2f}. This demonstrates good risk management and market timing."
        else:
            return f"Trade resulted in ${trade_result['pnl']:.2f} loss. This is a learning opportunity - analyze what went wrong and adjust your strategy."
    
    def _update_objectives_progress(self, session: LiveSimSession) -> Dict:
        """Update learning objectives progress"""
        return {
            "objectives": session.learning_objectives,
            "progress": [random.uniform(0.3, 0.9) for _ in session.learning_objectives],
            "completed": len([p for p in [random.uniform(0.3, 0.9) for _ in session.learning_objectives] if p >= 0.8])
        }
    
    def _select_quest_type(self, progress: UserProgress) -> QuestType:
        """Select quest type based on user progress"""
        if progress.streak_days >= 7:
            return QuestType.HFT_SCALPING_SIM
        elif progress.level >= 3:
            return QuestType.VOLATILITY_DUEL
        else:
            return QuestType.DAILY_TRADE_QUEST
    
    def _get_quest_title(self, quest_type: QuestType, regime: str) -> str:
        """Get quest title"""
        titles = {
            QuestType.DAILY_TRADE_QUEST: f"Daily Trading Quest - {regime} Market",
            QuestType.REGIME_MASTERY: f"Master {regime} Market Dynamics",
            QuestType.VOLATILITY_DUEL: "Volatility Duel Challenge",
            QuestType.BIPOC_WEALTH_CHALLENGE: "BIPOC Wealth Building Challenge",
            QuestType.HFT_SCALPING_SIM: "HFT Scalping Simulation"
        }
        return titles.get(quest_type, "Learning Quest")
    
    def _get_quest_description(self, quest_type: QuestType, regime: str) -> str:
        """Get quest description"""
        descriptions = {
            QuestType.DAILY_TRADE_QUEST: f"Complete 5 trading scenarios in {regime} market conditions",
            QuestType.REGIME_MASTERY: f"Demonstrate mastery of {regime} market strategies",
            QuestType.VOLATILITY_DUEL: "Compete in volatility trading challenges",
            QuestType.BIPOC_WEALTH_CHALLENGE: "Build wealth through culturally relevant strategies",
            QuestType.HFT_SCALPING_SIM: "Master high-frequency trading techniques"
        }
        return descriptions.get(quest_type, "Complete the learning objectives")
    
    def _calculate_quest_difficulty(self, progress: UserProgress) -> int:
        """Calculate quest difficulty based on user progress"""
        base_difficulty = min(5, max(1, progress.level // 2))
        return base_difficulty
    
    def _calculate_quest_xp_reward(self, progress: UserProgress) -> int:
        """Calculate quest XP reward"""
        base_xp = 50
        level_bonus = progress.level * 10
        streak_bonus = progress.streak_days * 5
        return base_xp + level_bonus + streak_bonus
    
    def _get_quest_skills(self, quest_type: QuestType) -> List[str]:
        """Get skills targeted by quest"""
        skill_mapping = {
            QuestType.DAILY_TRADE_QUEST: ["trading:basics", "risk:management"],
            QuestType.REGIME_MASTERY: ["regime:detection", "regime:adaptation"],
            QuestType.VOLATILITY_DUEL: ["volatility:trading", "options:strategies"],
            QuestType.BIPOC_WEALTH_CHALLENGE: ["wealth:building", "community:investing"],
            QuestType.HFT_SCALPING_SIM: ["hft:scalping", "microstructure:trading"]
        }
        return skill_mapping.get(quest_type, ["general:learning"])
    
    def _get_completion_criteria(self, quest_type: QuestType) -> Dict:
        """Get quest completion criteria"""
        criteria = {
            QuestType.DAILY_TRADE_QUEST: {"scenarios_completed": 5, "success_rate": 0.6},
            QuestType.REGIME_MASTERY: {"quizzes_passed": 3, "score_threshold": 80},
            QuestType.VOLATILITY_DUEL: {"duels_won": 2, "accuracy": 0.7},
            QuestType.BIPOC_WEALTH_CHALLENGE: {"strategies_learned": 3, "community_engagement": 1},
            QuestType.HFT_SCALPING_SIM: {"simulations_completed": 5, "profit_target": 100}
        }
        return criteria.get(quest_type, {"lessons_completed": 1})

# Global instance
def get_gamified_tutor() -> GamifiedTutor:
    """Get the global gamified tutor instance"""
    from .adaptive_engine import get_adaptive_engine
    import redis
    
    adaptive_engine = get_adaptive_engine()
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    return GamifiedTutor(adaptive_engine, redis_client)
