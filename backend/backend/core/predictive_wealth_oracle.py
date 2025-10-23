"""
Predictive Wealth Oracle - AI Co-Pilot System
============================================

This is the crown jewel of RichesReach Version 2 - an AI system that doesn't just
react to user requests, but proactively anticipates their needs and provides
intelligent recommendations before they even ask.

Key Features:
- Proactive market regime detection and alerts
- Predictive portfolio optimization
- Anticipatory tax optimization
- Risk prediction and mitigation
- Personalized learning path recommendations
- Behavioral pattern analysis and intervention
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import redis
from django.conf import settings

from .advanced_ai_router import AdvancedAIRouter, get_advanced_ai_router
from .ml_service import MLService
from .regime_monitor_service import RegimeMonitorService
from .notification_service import NotificationService

logger = logging.getLogger(__name__)

# =============================================================================
# Data Models
# =============================================================================

class OracleEventType(str, Enum):
    """Types of oracle events."""
    MARKET_REGIME_CHANGE = "market_regime_change"
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"
    TAX_OPPORTUNITY = "tax_opportunity"
    RISK_ALERT = "risk_alert"
    LEARNING_RECOMMENDATION = "learning_recommendation"
    BEHAVIORAL_INTERVENTION = "behavioral_intervention"
    OPPORTUNITY_ALERT = "opportunity_alert"

class OraclePriority(str, Enum):
    """Priority levels for oracle events."""
    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"         # Action within 24 hours
    MEDIUM = "medium"     # Action within week
    LOW = "low"          # Informational

class OracleConfidence(str, Enum):
    """Confidence levels for predictions."""
    VERY_HIGH = "very_high"  # 90%+ confidence
    HIGH = "high"           # 80-90% confidence
    MEDIUM = "medium"       # 70-80% confidence
    LOW = "low"            # 60-70% confidence
    VERY_LOW = "very_low"   # <60% confidence

@dataclass
class OracleEvent:
    """An oracle event - a proactive insight or recommendation."""
    id: str
    user_id: str
    event_type: OracleEventType
    priority: OraclePriority
    confidence: OracleConfidence
    title: str
    description: str
    recommendation: str
    expected_impact: str
    time_sensitivity: str
    data: Dict[str, Any]
    created_at: datetime
    expires_at: Optional[datetime] = None
    acknowledged: bool = False
    acted_upon: bool = False

@dataclass
class UserBehaviorProfile:
    """User behavior analysis for personalized recommendations."""
    user_id: str
    risk_tolerance: float
    trading_frequency: str
    learning_preference: str
    decision_style: str
    time_horizon: str
    churn_risk: float
    engagement_score: float
    last_updated: datetime

@dataclass
class MarketContext:
    """Current market context for predictions."""
    regime: str
    volatility: float
    trend: str
    sentiment: float
    economic_indicators: Dict[str, float]
    sector_rotation: Dict[str, float]
    timestamp: datetime

# =============================================================================
# Main Oracle Service
# =============================================================================

class PredictiveWealthOracle:
    """
    The Predictive Wealth Oracle - AI Co-Pilot System.
    
    This system continuously monitors market conditions, user behavior,
    and portfolio performance to provide proactive insights and recommendations.
    """
    
    def __init__(self):
        self.ai_router = get_advanced_ai_router()
        self.ml_service = MLService()
        self.regime_monitor = RegimeMonitorService()
        self.notification_service = NotificationService()
        self.redis_client = redis.Redis.from_url(settings.REDIS_URL)
        
        # Oracle state
        self.active_events: Dict[str, OracleEvent] = {}
        self.user_profiles: Dict[str, UserBehaviorProfile] = {}
        self.market_context: Optional[MarketContext] = None
        
        # Prediction models
        self.portfolio_optimizer = None
        self.risk_predictor = None
        self.opportunity_detector = None
        
        # Initialize models
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize ML models for predictions."""
        try:
            # Load or train portfolio optimization model
            self.portfolio_optimizer = self._load_or_train_model(
                'portfolio_optimizer',
                self._train_portfolio_optimizer
            )
            
            # Load or train risk prediction model
            self.risk_predictor = self._load_or_train_model(
                'risk_predictor',
                self._train_risk_predictor
            )
            
            # Load or train opportunity detection model
            self.opportunity_detector = self._load_or_train_model(
                'opportunity_detector',
                self._train_opportunity_detector
            )
            
            logger.info("Oracle models initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing oracle models: {e}")
    
    def _load_or_train_model(self, model_name: str, trainer_func):
        """Load existing model or train new one."""
        try:
            model_path = f"models/{model_name}.joblib"
            return joblib.load(model_path)
        except FileNotFoundError:
            logger.info(f"Training new {model_name} model")
            return trainer_func()
    
    async def start_oracle_monitoring(self):
        """Start the oracle monitoring loop."""
        logger.info("🔮 Starting Predictive Wealth Oracle monitoring")
        
        # Start background monitoring tasks
        asyncio.create_task(self._market_monitoring_loop())
        asyncio.create_task(self._user_behavior_analysis_loop())
        asyncio.create_task(self._opportunity_detection_loop())
        asyncio.create_task(self._event_cleanup_loop())
    
    # =========================================================================
    # Market Monitoring
    # =========================================================================
    
    async def _market_monitoring_loop(self):
        """Continuously monitor market conditions."""
        while True:
            try:
                await self._update_market_context()
                await self._detect_regime_changes()
                await self._analyze_market_opportunities()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Error in market monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _update_market_context(self):
        """Update current market context."""
        try:
            # Get current market regime
            regime_data = await self.regime_monitor.get_current_regime()
            
            # Get market indicators
            indicators = await self._get_market_indicators()
            
            # Calculate market sentiment
            sentiment = await self._calculate_market_sentiment()
            
            self.market_context = MarketContext(
                regime=regime_data.get('regime', 'unknown'),
                volatility=regime_data.get('volatility', 0.0),
                trend=regime_data.get('trend', 'neutral'),
                sentiment=sentiment,
                economic_indicators=indicators,
                sector_rotation=await self._get_sector_rotation(),
                timestamp=datetime.now(timezone.utc)
            )
            
            # Cache market context
            await self._cache_market_context()
            
        except Exception as e:
            logger.error(f"Error updating market context: {e}")
    
    async def _detect_regime_changes(self):
        """Detect and alert on market regime changes."""
        if not self.market_context:
            return
        
        # Check for regime changes
        regime_change = await self.regime_monitor.detect_regime_change()
        
        if regime_change and regime_change.get('confidence', 0) > 0.8:
            # Create oracle event for regime change
            event = OracleEvent(
                id=str(uuid.uuid4()),
                user_id="system",  # System-wide event
                event_type=OracleEventType.MARKET_REGIME_CHANGE,
                priority=OraclePriority.HIGH,
                confidence=OracleConfidence.HIGH,
                title=f"Market Regime Change Detected",
                description=f"Market has shifted from {regime_change.get('previous_regime')} to {regime_change.get('current_regime')}",
                recommendation=self._get_regime_change_recommendation(regime_change),
                expected_impact="Portfolio rebalancing may be beneficial",
                time_sensitivity="Action recommended within 24-48 hours",
                data=regime_change,
                created_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=48)
            )
            
            await self._create_oracle_event(event)
    
    # =========================================================================
    # User Behavior Analysis
    # =========================================================================
    
    async def _user_behavior_analysis_loop(self):
        """Continuously analyze user behavior patterns."""
        while True:
            try:
                # Get all active users
                user_ids = await self._get_active_user_ids()
                
                for user_id in user_ids:
                    await self._analyze_user_behavior(user_id)
                
                await asyncio.sleep(3600)  # Check every hour
            except Exception as e:
                logger.error(f"Error in user behavior analysis loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _analyze_user_behavior(self, user_id: str):
        """Analyze individual user behavior."""
        try:
            # Get user activity data
            activity_data = await self._get_user_activity_data(user_id)
            
            # Calculate behavior metrics
            behavior_profile = await self._calculate_behavior_profile(user_id, activity_data)
            
            # Update user profile
            self.user_profiles[user_id] = behavior_profile
            
            # Check for behavioral interventions
            await self._check_behavioral_interventions(user_id, behavior_profile)
            
        except Exception as e:
            logger.error(f"Error analyzing user behavior for {user_id}: {e}")
    
    async def _check_behavioral_interventions(self, user_id: str, profile: UserBehaviorProfile):
        """Check if behavioral interventions are needed."""
        interventions = []
        
        # High churn risk
        if profile.churn_risk > 0.7:
            interventions.append({
                'type': 'churn_prevention',
                'priority': OraclePriority.HIGH,
                'title': 'We\'ve noticed you haven\'t been active lately',
                'description': 'Your engagement has decreased. Let\'s get you back on track!',
                'recommendation': 'Try our new AI Trading Coach or explore Wealth Circles',
                'expected_impact': 'Increased engagement and retention'
            })
        
        # Low engagement
        if profile.engagement_score < 0.3:
            interventions.append({
                'type': 'engagement_boost',
                'priority': OraclePriority.MEDIUM,
                'title': 'Boost your investment knowledge',
                'description': 'We have personalized learning content just for you',
                'recommendation': 'Complete your personalized learning path',
                'expected_impact': 'Improved knowledge and confidence'
            })
        
        # Risk tolerance mismatch
        if profile.risk_tolerance > 0.8 and self.market_context and self.market_context.volatility > 0.3:
            interventions.append({
                'type': 'risk_adjustment',
                'priority': OraclePriority.MEDIUM,
                'title': 'Market volatility detected',
                'description': 'High volatility may not align with your risk tolerance',
                'recommendation': 'Consider reducing position sizes or adding hedges',
                'expected_impact': 'Better risk-adjusted returns'
            })
        
        # Create oracle events for interventions
        for intervention in interventions:
            event = OracleEvent(
                id=str(uuid.uuid4()),
                user_id=user_id,
                event_type=OracleEventType.BEHAVIORAL_INTERVENTION,
                priority=intervention['priority'],
                confidence=OracleConfidence.HIGH,
                title=intervention['title'],
                description=intervention['description'],
                recommendation=intervention['recommendation'],
                expected_impact=intervention['expected_impact'],
                time_sensitivity="Action recommended within 1 week",
                data=intervention,
                created_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=7)
            )
            
            await self._create_oracle_event(event)
    
    # =========================================================================
    # Opportunity Detection
    # =========================================================================
    
    async def _opportunity_detection_loop(self):
        """Continuously scan for investment opportunities."""
        while True:
            try:
                await self._scan_tax_opportunities()
                await self._scan_rebalancing_opportunities()
                await self._scan_learning_opportunities()
                await asyncio.sleep(1800)  # Check every 30 minutes
            except Exception as e:
                logger.error(f"Error in opportunity detection loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _scan_tax_opportunities(self):
        """Scan for tax optimization opportunities."""
        try:
            # Get users with portfolios
            user_ids = await self._get_users_with_portfolios()
            
            for user_id in user_ids:
                portfolio = await self._get_user_portfolio(user_id)
                
                if not portfolio:
                    continue
                
                # Check for tax loss harvesting opportunities
                tax_opportunities = await self._analyze_tax_opportunities(user_id, portfolio)
                
                for opportunity in tax_opportunities:
                    event = OracleEvent(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        event_type=OracleEventType.TAX_OPPORTUNITY,
                        priority=OraclePriority.MEDIUM,
                        confidence=OracleConfidence.HIGH,
                        title=opportunity['title'],
                        description=opportunity['description'],
                        recommendation=opportunity['recommendation'],
                        expected_impact=opportunity['expected_impact'],
                        time_sensitivity="Action recommended before year-end",
                        data=opportunity,
                        created_at=datetime.now(timezone.utc),
                        expires_at=datetime.now(timezone.utc) + timedelta(days=30)
                    )
                    
                    await self._create_oracle_event(event)
                    
        except Exception as e:
            logger.error(f"Error scanning tax opportunities: {e}")
    
    # =========================================================================
    # Portfolio Optimization
    # =========================================================================
    
    async def get_proactive_portfolio_recommendations(self, user_id: str) -> List[OracleEvent]:
        """Get proactive portfolio optimization recommendations."""
        try:
            portfolio = await self._get_user_portfolio(user_id)
            if not portfolio:
                return []
            
            recommendations = []
            
            # Analyze current allocation
            allocation_analysis = await self._analyze_portfolio_allocation(portfolio)
            
            if allocation_analysis['needs_rebalancing']:
                event = OracleEvent(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    event_type=OracleEventType.PORTFOLIO_OPTIMIZATION,
                    priority=OraclePriority.MEDIUM,
                    confidence=OracleConfidence.HIGH,
                    title="Portfolio Rebalancing Opportunity",
                    description=f"Your portfolio has drifted {allocation_analysis['drift_percentage']:.1f}% from target allocation",
                    recommendation=allocation_analysis['rebalancing_recommendation'],
                    expected_impact=f"Expected improvement: {allocation_analysis['expected_improvement']:.1f}% risk-adjusted returns",
                    time_sensitivity="Action recommended within 1 week",
                    data=allocation_analysis,
                    created_at=datetime.now(timezone.utc),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=14)
                )
                recommendations.append(event)
            
            # Risk analysis
            risk_analysis = await self._analyze_portfolio_risk(portfolio)
            
            if risk_analysis['risk_level'] == 'high':
                event = OracleEvent(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    event_type=OracleEventType.RISK_ALERT,
                    priority=OraclePriority.HIGH,
                    confidence=OracleConfidence.MEDIUM,
                    title="Portfolio Risk Alert",
                    description=f"Your portfolio risk score is {risk_analysis['risk_score']:.1f}/10",
                    recommendation=risk_analysis['risk_reduction_recommendation'],
                    expected_impact="Reduced portfolio volatility and drawdown risk",
                    time_sensitivity="Action recommended within 48 hours",
                    data=risk_analysis,
                    created_at=datetime.now(timezone.utc),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=7)
                )
                recommendations.append(event)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting proactive portfolio recommendations: {e}")
            return []
    
    # =========================================================================
    # AI-Powered Insights
    # =========================================================================
    
    async def generate_ai_insight(self, user_id: str, insight_type: str) -> Optional[OracleEvent]:
        """Generate AI-powered insight using advanced models."""
        try:
            # Get user context
            user_profile = self.user_profiles.get(user_id)
            portfolio = await self._get_user_portfolio(user_id)
            
            if not user_profile or not portfolio:
                return None
            
            # Generate insight using AI
            insight_prompt = self._build_insight_prompt(user_profile, portfolio, insight_type)
            
            response = await self.ai_router.process_request(
                request_type="financial_analysis",
                prompt=insight_prompt,
                context={
                    'user_profile': asdict(user_profile),
                    'portfolio': portfolio,
                    'market_context': asdict(self.market_context) if self.market_context else None
                }
            )
            
            if response and response.get('success'):
                insight_data = response.get('data', {})
                
                event = OracleEvent(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    event_type=OracleEventType.OPPORTUNITY_ALERT,
                    priority=OraclePriority.MEDIUM,
                    confidence=OracleConfidence.MEDIUM,
                    title=insight_data.get('title', 'AI Insight'),
                    description=insight_data.get('description', ''),
                    recommendation=insight_data.get('recommendation', ''),
                    expected_impact=insight_data.get('expected_impact', ''),
                    time_sensitivity=insight_data.get('time_sensitivity', ''),
                    data=insight_data,
                    created_at=datetime.now(timezone.utc),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=7)
                )
                
                return event
            
        except Exception as e:
            logger.error(f"Error generating AI insight: {e}")
        
        return None
    
    # =========================================================================
    # Event Management
    # =========================================================================
    
    async def _create_oracle_event(self, event: OracleEvent):
        """Create and store an oracle event."""
        try:
            # Store event
            self.active_events[event.id] = event
            
            # Cache in Redis
            await self._cache_oracle_event(event)
            
            # Send notification if high priority
            if event.priority in [OraclePriority.CRITICAL, OraclePriority.HIGH]:
                await self._send_oracle_notification(event)
            
            logger.info(f"Created oracle event: {event.id} for user {event.user_id}")
            
        except Exception as e:
            logger.error(f"Error creating oracle event: {e}")
    
    async def get_user_oracle_events(self, user_id: str, limit: int = 10) -> List[OracleEvent]:
        """Get oracle events for a specific user."""
        try:
            # Get events from cache
            events = await self._get_cached_oracle_events(user_id)
            
            # Filter and sort events
            user_events = [
                event for event in events
                if event.user_id == user_id and not event.acknowledged
            ]
            
            # Sort by priority and creation time
            user_events.sort(key=lambda x: (
                x.priority.value,
                x.created_at
            ), reverse=True)
            
            return user_events[:limit]
            
        except Exception as e:
            logger.error(f"Error getting user oracle events: {e}")
            return []
    
    async def acknowledge_oracle_event(self, event_id: str, user_id: str):
        """Acknowledge an oracle event."""
        try:
            if event_id in self.active_events:
                event = self.active_events[event_id]
                if event.user_id == user_id:
                    event.acknowledged = True
                    await self._cache_oracle_event(event)
                    
        except Exception as e:
            logger.error(f"Error acknowledging oracle event: {e}")
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _build_insight_prompt(self, user_profile: UserBehaviorProfile, portfolio: dict, insight_type: str) -> str:
        """Build AI prompt for insight generation."""
        return f"""
        As a financial AI oracle, analyze this user's situation and provide a personalized insight.
        
        User Profile:
        - Risk Tolerance: {user_profile.risk_tolerance}
        - Trading Frequency: {user_profile.trading_frequency}
        - Learning Preference: {user_profile.learning_preference}
        - Decision Style: {user_profile.decision_style}
        - Time Horizon: {user_profile.time_horizon}
        
        Portfolio:
        - Total Value: ${portfolio.get('total_value', 0):,.2f}
        - Allocation: {portfolio.get('allocation', {})}
        - Performance: {portfolio.get('performance', {})}
        
        Market Context:
        - Regime: {self.market_context.regime if self.market_context else 'Unknown'}
        - Volatility: {self.market_context.volatility if self.market_context else 0}
        - Trend: {self.market_context.trend if self.market_context else 'Neutral'}
        
        Insight Type: {insight_type}
        
        Provide a personalized, actionable insight that considers the user's profile, portfolio, and current market conditions.
        """
    
    async def _get_market_indicators(self) -> Dict[str, float]:
        """Get current market indicators."""
        # This would integrate with your market data APIs
        return {
            'vix': 20.5,
            'dxy': 103.2,
            'yield_10y': 4.2,
            'unemployment': 3.8,
            'inflation': 3.2
        }
    
    async def _calculate_market_sentiment(self) -> float:
        """Calculate overall market sentiment."""
        # This would use news sentiment analysis, social media, etc.
        return 0.6  # Neutral to slightly positive
    
    async def _get_sector_rotation(self) -> Dict[str, float]:
        """Get sector rotation data."""
        return {
            'technology': 0.3,
            'healthcare': 0.2,
            'financials': 0.15,
            'energy': 0.1,
            'consumer': 0.25
        }
    
    # =========================================================================
    # Model Training Methods
    # =========================================================================
    
    def _train_portfolio_optimizer(self):
        """Train portfolio optimization model."""
        # This would train a model to predict optimal portfolio allocations
        # For now, return a simple model
        return RandomForestRegressor(n_estimators=100, random_state=42)
    
    def _train_risk_predictor(self):
        """Train risk prediction model."""
        # This would train a model to predict portfolio risk
        return GradientBoostingRegressor(n_estimators=100, random_state=42)
    
    def _train_opportunity_detector(self):
        """Train opportunity detection model."""
        # This would train a model to detect investment opportunities
        return RandomForestRegressor(n_estimators=100, random_state=42)
    
    # =========================================================================
    # Cache Methods
    # =========================================================================
    
    async def _cache_market_context(self):
        """Cache market context in Redis."""
        if self.market_context:
            await self.redis_client.setex(
                'oracle:market_context',
                300,  # 5 minutes
                json.dumps(asdict(self.market_context), default=str)
            )
    
    async def _cache_oracle_event(self, event: OracleEvent):
        """Cache oracle event in Redis."""
        await self.redis_client.setex(
            f'oracle:event:{event.id}',
            86400,  # 24 hours
            json.dumps(asdict(event), default=str)
        )
    
    async def _get_cached_oracle_events(self, user_id: str) -> List[OracleEvent]:
        """Get cached oracle events for user."""
        try:
            keys = await self.redis_client.keys(f'oracle:event:*')
            events = []
            
            for key in keys:
                event_data = await self.redis_client.get(key)
                if event_data:
                    event_dict = json.loads(event_data)
                    event = OracleEvent(**event_dict)
                    events.append(event)
            
            return events
        except Exception as e:
            logger.error(f"Error getting cached oracle events: {e}")
            return []
    
    # =========================================================================
    # Placeholder Methods (to be implemented)
    # =========================================================================
    
    async def _get_active_user_ids(self) -> List[str]:
        """Get list of active user IDs."""
        # This would query your user database
        return []
    
    async def _get_user_activity_data(self, user_id: str) -> Dict[str, Any]:
        """Get user activity data."""
        # This would query your user activity database
        return {}
    
    async def _calculate_behavior_profile(self, user_id: str, activity_data: Dict[str, Any]) -> UserBehaviorProfile:
        """Calculate user behavior profile."""
        # This would analyze user activity and calculate behavior metrics
        return UserBehaviorProfile(
            user_id=user_id,
            risk_tolerance=0.5,
            trading_frequency='moderate',
            learning_preference='visual',
            decision_style='analytical',
            time_horizon='long_term',
            churn_risk=0.3,
            engagement_score=0.7,
            last_updated=datetime.now(timezone.utc)
        )
    
    async def _get_users_with_portfolios(self) -> List[str]:
        """Get users who have portfolios."""
        # This would query your portfolio database
        return []
    
    async def _get_user_portfolio(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user portfolio data."""
        # This would query your portfolio database
        return None
    
    async def _analyze_tax_opportunities(self, user_id: str, portfolio: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze tax optimization opportunities."""
        # This would analyze the portfolio for tax opportunities
        return []
    
    async def _analyze_portfolio_allocation(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze portfolio allocation."""
        # This would analyze the portfolio allocation
        return {
            'needs_rebalancing': False,
            'drift_percentage': 0.0,
            'rebalancing_recommendation': '',
            'expected_improvement': 0.0
        }
    
    async def _analyze_portfolio_risk(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze portfolio risk."""
        # This would analyze the portfolio risk
        return {
            'risk_level': 'medium',
            'risk_score': 5.0,
            'risk_reduction_recommendation': ''
        }
    
    async def _send_oracle_notification(self, event: OracleEvent):
        """Send notification for oracle event."""
        # This would send push notification
        pass
    
    async def _event_cleanup_loop(self):
        """Clean up expired events."""
        while True:
            try:
                current_time = datetime.now(timezone.utc)
                expired_events = [
                    event_id for event_id, event in self.active_events.items()
                    if event.expires_at and event.expires_at < current_time
                ]
                
                for event_id in expired_events:
                    del self.active_events[event_id]
                
                await asyncio.sleep(3600)  # Clean up every hour
            except Exception as e:
                logger.error(f"Error in event cleanup loop: {e}")
                await asyncio.sleep(300)

# =============================================================================
# Global Instance
# =============================================================================

oracle_service = PredictiveWealthOracle()
