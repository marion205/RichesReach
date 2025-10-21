"""
Trade Simulator Challenges Service
==================================

Implements social betting and trading competitions to gamify learning and create
community engagement through friendly competition. This creates the "social gaming"
element that drives daily engagement.

Key Features:
- Virtual trading competitions with real market data
- Social betting and prediction challenges
- Leaderboards and rankings
- Team challenges and group competitions
- Educational trading scenarios
- Risk-free learning environment

Dependencies:
- market_data_service: For real-time market data
- peer_progress_service: For social features and leaderboards
- notification_service: For challenge updates and results
"""

from __future__ import annotations

import asyncio
import json
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, TypedDict
from enum import Enum

from .peer_progress_service import PeerProgressService
from .notification_service import NotificationService

logger = logging.getLogger(__name__)

# =============================================================================
# Enums and Types
# =============================================================================

class ChallengeType(str, Enum):
    """Types of trading challenges."""
    DAILY_PREDICTION = "daily_prediction"
    WEEKLY_COMPETITION = "weekly_competition"
    MONTHLY_TOURNAMENT = "monthly_tournament"
    TEAM_CHALLENGE = "team_challenge"
    EDUCATIONAL_SCENARIO = "educational_scenario"
    RISK_MANAGEMENT = "risk_management"

class ChallengeStatus(str, Enum):
    """Challenge status."""
    UPCOMING = "upcoming"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PredictionType(str, Enum):
    """Types of predictions."""
    STOCK_PRICE = "stock_price"
    MARKET_DIRECTION = "market_direction"
    VOLATILITY = "volatility"
    SECTOR_PERFORMANCE = "sector_performance"
    CRYPTO_MOVEMENT = "crypto_movement"

# =============================================================================
# Typed Payloads
# =============================================================================

class TradingChallenge(TypedDict, total=False):
    """Trading challenge."""
    challenge_id: str
    title: str
    description: str
    challenge_type: str
    status: str
    start_date: str
    end_date: str
    entry_fee: float
    prize_pool: float
    max_participants: int
    current_participants: int
    rules: List[str]
    created_by: str
    created_at: str

class Prediction(TypedDict, total=False):
    """User prediction."""
    prediction_id: str
    challenge_id: str
    user_id: str
    prediction_type: str
    asset: str
    predicted_value: float
    confidence: float
    reasoning: str
    created_at: str
    result: Optional[Dict[str, Any]]

class LeaderboardEntry(TypedDict, total=False):
    """Leaderboard entry."""
    user_id: str
    username: str
    score: float
    rank: int
    total_predictions: int
    correct_predictions: int
    accuracy: float
    total_winnings: float
    is_anonymous: bool

class TeamChallenge(TypedDict, total=False):
    """Team-based challenge."""
    team_id: str
    challenge_id: str
    team_name: str
    members: List[str]
    captain: str
    total_score: float
    rank: int
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

class TradeSimulatorService:
    """
    Trade Simulator Challenges Service for gamified learning.
    
    Core Functionality:
        - Virtual trading competitions with real market data
        - Social betting and prediction challenges
        - Leaderboards and rankings
        - Team challenges and group competitions
        - Educational trading scenarios
        - Risk-free learning environment
    
    Design Notes:
        - All timestamps in UTC (ISO8601)
        - Virtual currency for risk-free learning
        - Social features for community engagement
        - Educational focus with real market data
    """

    def __init__(
        self,
        peer_progress_service: Optional[PeerProgressService] = None,
        notification_service: Optional[NotificationService] = None,
    ) -> None:
        self.peer_progress_service = peer_progress_service or PeerProgressService()
        self.notification_service = notification_service or NotificationService()

    # -------------------------------------------------------------------------
    # Public API Methods
    # -------------------------------------------------------------------------

    async def create_challenge(
        self,
        title: str,
        description: str,
        challenge_type: str,
        start_date: str,
        end_date: str,
        creator_id: str,
        *,
        entry_fee: float = 0.0,
        max_participants: int = 100,
    ) -> TradingChallenge:
        """
        Create a new trading challenge.
        
        Args:
            title: Challenge title
            description: Challenge description
            challenge_type: Type of challenge
            start_date: Challenge start date (ISO8601)
            end_date: Challenge end date (ISO8601)
            creator_id: ID of the challenge creator
            entry_fee: Entry fee in virtual currency
            max_participants: Maximum number of participants
            
        Returns:
            TradingChallenge object
        """
        try:
            challenge_id = str(uuid.uuid4())
            
            # Calculate prize pool (entry fees + bonus)
            prize_pool = entry_fee * max_participants * 0.8  # 80% of entry fees as prize pool
            
            # Generate challenge rules
            rules = self._generate_challenge_rules(challenge_type)
            
            challenge: TradingChallenge = {
                "challenge_id": challenge_id,
                "title": title,
                "description": description,
                "challenge_type": challenge_type,
                "status": ChallengeStatus.UPCOMING.value,
                "start_date": start_date,
                "end_date": end_date,
                "entry_fee": entry_fee,
                "prize_pool": prize_pool,
                "max_participants": max_participants,
                "current_participants": 0,
                "rules": rules,
                "created_by": creator_id,
                "created_at": _now_iso_utc()
            }
            
            logger.info(f"Created trading challenge: {title} (ID: {challenge_id})")
            return challenge
            
        except Exception as e:
            logger.error(f"Error creating challenge: {e}")
            raise

    async def join_challenge(
        self,
        challenge_id: str,
        user_id: str,
        *,
        team_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Join a trading challenge.
        
        Args:
            challenge_id: ID of the challenge
            user_id: ID of the user joining
            team_id: Optional team ID for team challenges
            
        Returns:
            Join result with confirmation
        """
        try:
            # In a real system, this would check challenge availability, entry fees, etc.
            
            join_result = {
                "challenge_id": challenge_id,
                "user_id": user_id,
                "team_id": team_id,
                "joined_at": _now_iso_utc(),
                "status": "confirmed",
                "message": "Successfully joined the challenge!"
            }
            
            logger.info(f"User {user_id} joined challenge {challenge_id}")
            return join_result
            
        except Exception as e:
            logger.error(f"Error joining challenge: {e}")
            raise

    async def make_prediction(
        self,
        challenge_id: str,
        user_id: str,
        prediction_type: str,
        asset: str,
        predicted_value: float,
        confidence: float,
        reasoning: str,
    ) -> Prediction:
        """
        Make a prediction in a trading challenge.
        
        Args:
            challenge_id: ID of the challenge
            user_id: ID of the user making prediction
            prediction_type: Type of prediction
            asset: Asset being predicted (stock symbol, etc.)
            predicted_value: Predicted value
            confidence: Confidence level (0.0-1.0)
            reasoning: Reasoning for the prediction
            
        Returns:
            Prediction object
        """
        try:
            prediction_id = str(uuid.uuid4())
            
            prediction: Prediction = {
                "prediction_id": prediction_id,
                "challenge_id": challenge_id,
                "user_id": user_id,
                "prediction_type": prediction_type,
                "asset": asset,
                "predicted_value": predicted_value,
                "confidence": confidence,
                "reasoning": reasoning,
                "created_at": _now_iso_utc(),
                "result": None
            }
            
            logger.info(f"Prediction made: {asset} by user {user_id}")
            return prediction
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            raise

    async def get_leaderboard(
        self,
        challenge_id: str,
        *,
        limit: int = 50,
    ) -> List[LeaderboardEntry]:
        """
        Get challenge leaderboard.
        
        Args:
            challenge_id: ID of the challenge
            limit: Maximum number of entries to return
            
        Returns:
            List of leaderboard entries
        """
        try:
            # Simulate leaderboard data
            # In a real system, this would calculate actual scores and rankings
            
            leaderboard = []
            
            for i in range(min(limit, 25)):  # Simulate 25 participants
                accuracy = 0.6 + (i * 0.015)  # Simulate decreasing accuracy
                total_predictions = 10 + (i * 2)
                correct_predictions = int(total_predictions * accuracy)
                score = (correct_predictions * 100) + (accuracy * 50)  # Scoring formula
                
                entry: LeaderboardEntry = {
                    "user_id": f"user_{i+1:03d}",
                    "username": f"Trader{i+1:03d}" if i < 10 else "Anonymous",
                    "score": round(score, 2),
                    "rank": i + 1,
                    "total_predictions": total_predictions,
                    "correct_predictions": correct_predictions,
                    "accuracy": round(accuracy, 3),
                    "total_winnings": round(score * 0.1, 2),  # Simulate winnings
                    "is_anonymous": i >= 10
                }
                leaderboard.append(entry)
            
            logger.info(f"Generated leaderboard for challenge {challenge_id}")
            return leaderboard
            
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            raise

    async def create_team_challenge(
        self,
        challenge_id: str,
        team_name: str,
        captain_id: str,
        member_ids: List[str],
    ) -> TeamChallenge:
        """
        Create a team for a team challenge.
        
        Args:
            challenge_id: ID of the challenge
            team_name: Name of the team
            captain_id: ID of the team captain
            member_ids: List of team member IDs
            
        Returns:
            TeamChallenge object
        """
        try:
            team_id = str(uuid.uuid4())
            
            team: TeamChallenge = {
                "team_id": team_id,
                "challenge_id": challenge_id,
                "team_name": team_name,
                "members": member_ids,
                "captain": captain_id,
                "total_score": 0.0,
                "rank": 0,
                "created_at": _now_iso_utc()
            }
            
            logger.info(f"Created team: {team_name} for challenge {challenge_id}")
            return team
            
        except Exception as e:
            logger.error(f"Error creating team challenge: {e}")
            raise

    async def get_active_challenges(
        self,
        *,
        challenge_type: Optional[str] = None,
        limit: int = 20,
    ) -> List[TradingChallenge]:
        """
        Get active trading challenges.
        
        Args:
            challenge_type: Optional filter by challenge type
            limit: Maximum number of challenges to return
            
        Returns:
            List of active challenges
        """
        try:
            # Simulate active challenges
            challenges = [
                {
                    "challenge_id": "challenge_001",
                    "title": "Daily AAPL Prediction",
                    "description": "Predict Apple's closing price today!",
                    "challenge_type": "daily_prediction",
                    "status": "active",
                    "start_date": "2024-01-15T09:30:00Z",
                    "end_date": "2024-01-15T16:00:00Z",
                    "entry_fee": 10.0,
                    "prize_pool": 800.0,
                    "max_participants": 100,
                    "current_participants": 67,
                    "rules": [
                        "Predict AAPL closing price within $0.50",
                        "One prediction per user",
                        "Winner takes 50% of prize pool"
                    ],
                    "created_by": "system",
                    "created_at": "2024-01-15T09:00:00Z"
                },
                {
                    "challenge_id": "challenge_002",
                    "title": "Weekly Market Direction",
                    "description": "Predict if S&P 500 will be up or down this week!",
                    "challenge_type": "weekly_competition",
                    "status": "active",
                    "start_date": "2024-01-15T09:30:00Z",
                    "end_date": "2024-01-19T16:00:00Z",
                    "entry_fee": 25.0,
                    "prize_pool": 2000.0,
                    "max_participants": 100,
                    "current_participants": 43,
                    "rules": [
                        "Predict weekly market direction",
                        "Include confidence level",
                        "Top 10% share prize pool"
                    ],
                    "created_by": "system",
                    "created_at": "2024-01-15T08:00:00Z"
                },
                {
                    "challenge_id": "challenge_003",
                    "title": "Risk Management Master",
                    "description": "Educational challenge focusing on risk management!",
                    "challenge_type": "educational_scenario",
                    "status": "active",
                    "start_date": "2024-01-15T10:00:00Z",
                    "end_date": "2024-01-22T10:00:00Z",
                    "entry_fee": 0.0,
                    "prize_pool": 500.0,
                    "max_participants": 50,
                    "current_participants": 28,
                    "rules": [
                        "Complete risk management scenarios",
                        "Learn proper position sizing",
                        "All participants get educational materials"
                    ],
                    "created_by": "system",
                    "created_at": "2024-01-15T09:30:00Z"
                }
            ]
            
            # Filter by challenge type if specified
            if challenge_type:
                challenges = [c for c in challenges if c["challenge_type"] == challenge_type]
            
            return challenges[:limit]
            
        except Exception as e:
            logger.error(f"Error getting active challenges: {e}")
            raise

    async def evaluate_predictions(
        self,
        challenge_id: str,
    ) -> Dict[str, Any]:
        """
        Evaluate predictions and determine winners.
        
        Args:
            challenge_id: ID of the challenge to evaluate
            
        Returns:
            Evaluation results with winners and scores
        """
        try:
            # In a real system, this would:
            # 1. Get actual market data for the challenge period
            # 2. Compare predictions to actual results
            # 3. Calculate scores based on accuracy and confidence
            # 4. Determine winners and distribute prizes
            
            evaluation_result = {
                "challenge_id": challenge_id,
                "evaluated_at": _now_iso_utc(),
                "total_predictions": 67,
                "winners": [
                    {
                        "user_id": "user_001",
                        "rank": 1,
                        "score": 95.5,
                        "prize": 400.0,
                        "prediction_accuracy": 0.98
                    },
                    {
                        "user_id": "user_015",
                        "rank": 2,
                        "score": 92.3,
                        "prize": 200.0,
                        "prediction_accuracy": 0.95
                    },
                    {
                        "user_id": "user_042",
                        "rank": 3,
                        "score": 89.7,
                        "prize": 100.0,
                        "prediction_accuracy": 0.92
                    }
                ],
                "community_stats": {
                    "average_accuracy": 0.73,
                    "total_participants": 67,
                    "prize_distributed": 700.0
                }
            }
            
            logger.info(f"Evaluated predictions for challenge {challenge_id}")
            return evaluation_result
            
        except Exception as e:
            logger.error(f"Error evaluating predictions: {e}")
            raise

    # -------------------------------------------------------------------------
    # Private Helper Methods
    # -------------------------------------------------------------------------

    def _generate_challenge_rules(
        self,
        challenge_type: str
    ) -> List[str]:
        """Generate challenge rules based on type."""
        rules_templates = {
            "daily_prediction": [
                "One prediction per user per day",
                "Predictions must be made before market open",
                "Winner determined by closest to actual price",
                "Tie-breaker: earliest prediction wins"
            ],
            "weekly_competition": [
                "Predictions must include reasoning",
                "Confidence level affects scoring",
                "Multiple predictions allowed with different assets",
                "Top performers share prize pool"
            ],
            "educational_scenario": [
                "Focus on learning, not just winning",
                "Complete all educational modules",
                "Apply concepts in simulated scenarios",
                "All participants receive educational materials"
            ],
            "team_challenge": [
                "Teams of 3-5 members",
                "Collaborative predictions allowed",
                "Team score is average of member scores",
                "Team captain manages submissions"
            ]
        }
        
        return rules_templates.get(challenge_type, [
            "Follow community guidelines",
            "Respect other participants",
            "Have fun and learn!"
        ])

# =============================================================================
# Singleton Instance
# =============================================================================

trade_simulator_service = TradeSimulatorService()
