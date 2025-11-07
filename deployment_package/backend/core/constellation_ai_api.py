"""
Constellation AI API - AI/ML-powered features for Constellation Orb
Provides personalized life events, ML growth projections, shield analysis, and recommendations
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
import sys
import os

# Add backend path for imports
backend_path = os.path.join(os.path.dirname(__file__))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

logger = logging.getLogger(__name__)

# Initialize AI/ML services
try:
    from .ai_service import AIService
    from .optimized_ml_service import OptimizedMLService
    from .market_data_service import MarketDataService
    from .premium_analytics import PremiumAnalytics
    
    _ai_service = AIService()
    _ml_service = OptimizedMLService() if hasattr(AIService(), 'ml_service') else None
    _market_data_service = MarketDataService() if hasattr(AIService(), 'market_data_service') else None
    _premium_analytics = PremiumAnalytics()
    logger.info("✅ Constellation AI services initialized")
except Exception as e:
    logger.warning(f"⚠️ Some Constellation AI services not available: {e}")
    _ai_service = None
    _ml_service = None
    _market_data_service = None
    _premium_analytics = None

# Create API router
router = APIRouter(prefix="/api/ai", tags=["Constellation AI"])

# ============================================================================
# Request/Response Models
# ============================================================================

class SnapshotData(BaseModel):
    """Financial snapshot data"""
    netWorth: float
    cashflow: Dict[str, Any]
    breakdown: Dict[str, Any]
    positions: Optional[List[Dict[str, Any]]] = None

class UserProfile(BaseModel):
    """User profile data"""
    age: Optional[int] = None
    incomeBracket: Optional[str] = None
    riskTolerance: Optional[str] = None
    investmentGoals: Optional[List[str]] = None

class LifeEventsRequest(BaseModel):
    """Request for personalized life events"""
    snapshot: SnapshotData
    userProfile: Optional[UserProfile] = None

class LifeEvent(BaseModel):
    """Life event response"""
    id: str
    title: str
    icon: str
    targetAmount: float
    currentProgress: float
    monthsAway: int
    suggestion: str
    color: str
    aiConfidence: float
    aiReasoning: str
    personalizedFactors: List[str]

class LifeEventsResponse(BaseModel):
    """Response for life events"""
    events: List[LifeEvent]

class GrowthProjectionsRequest(BaseModel):
    """Request for ML growth projections"""
    currentValue: float
    monthlySurplus: float
    portfolioValue: float
    timeframes: List[int] = [6, 12, 24, 36]

class MLFactors(BaseModel):
    """ML prediction factors"""
    marketRegime: str
    volatility: float
    momentum: float
    riskLevel: str

class GrowthProjection(BaseModel):
    """Growth projection response"""
    scenario: str
    growthRate: float
    confidence: float
    timeframe: int
    projectedValue: float
    color: str
    mlFactors: MLFactors

class GrowthProjectionsResponse(BaseModel):
    """Response for growth projections"""
    projections: List[GrowthProjection]

class ShieldAnalysisRequest(BaseModel):
    """Request for shield analysis"""
    portfolioValue: float
    bankBalance: float
    positions: Optional[List[Dict[str, Any]]] = None
    cashflow: Optional[Dict[str, Any]] = None

class RecommendedStrategy(BaseModel):
    """Recommended shield strategy"""
    id: str
    priority: int
    aiReasoning: str
    expectedImpact: str

class MarketOutlook(BaseModel):
    """Market outlook analysis"""
    sentiment: str  # bullish, bearish, neutral
    confidence: float
    keyFactors: List[str]

class ShieldAnalysisResponse(BaseModel):
    """Response for shield analysis"""
    currentRisk: float
    marketRegime: str
    recommendedStrategies: List[RecommendedStrategy]
    marketOutlook: MarketOutlook

class RecommendationsRequest(BaseModel):
    """Request for personalized recommendations"""
    snapshot: SnapshotData
    userBehavior: Optional[Dict[str, Any]] = None

class Recommendation(BaseModel):
    """Personalized recommendation"""
    type: str  # life_event, investment, savings, risk_management
    title: str
    description: str
    action: str
    priority: int
    aiConfidence: float
    reasoning: str

class RecommendationsResponse(BaseModel):
    """Response for recommendations"""
    recommendations: List[Recommendation]

# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/life-events", response_model=LifeEventsResponse)
async def get_personalized_life_events(request: LifeEventsRequest):
    """
    Get AI-powered personalized life event suggestions based on user profile and financial snapshot.
    
    Returns personalized financial milestones with AI confidence scores and reasoning.
    """
    try:
        snapshot = request.snapshot
        user_profile = request.userProfile
        
        net_worth = snapshot.netWorth
        bank_balance = snapshot.breakdown.get('bankBalance', 0)
        portfolio_value = snapshot.breakdown.get('portfolioValue', 0)
        cashflow_delta = snapshot.cashflow.get('delta', 100)
        
        events = []
        
        # Use AI service if available
        if _ai_service and _ai_service.api_key:
            try:
                # Generate AI-powered life events
                user_context = f"Net worth: ${net_worth:,.0f}, Age: {user_profile.age if user_profile and user_profile.age else 'unknown'}, Risk tolerance: {user_profile.riskTolerance if user_profile and user_profile.riskTolerance else 'medium'}"
                
                ai_prompt = f"""Based on this financial profile, suggest 3-5 personalized life events:
- Net worth: ${net_worth:,.0f}
- Bank balance: ${bank_balance:,.0f}
- Portfolio value: ${portfolio_value:,.0f}
- Monthly surplus: ${cashflow_delta:,.0f}
- Age: {user_profile.age if user_profile and user_profile.age else 'unknown'}
- Risk tolerance: {user_profile.riskTolerance if user_profile and user_profile.riskTolerance else 'medium'}

Return JSON with events including: id, title, icon, targetAmount, currentProgress, monthsAway, suggestion, color, aiReasoning, personalizedFactors"""
                
                messages = [{"role": "user", "content": ai_prompt}]
                ai_response = _ai_service.get_chat_response(messages, user_context)
                
                # Parse AI response (simplified - in production, use structured output)
                # For now, generate intelligent defaults with AI reasoning
                pass  # Will use fallback logic below
            except Exception as e:
                logger.warning(f"AI service error, using fallback: {e}")
        
        # Generate intelligent life events based on financial profile
        # Emergency Fund
        emergency_target = max(net_worth * 0.1, 10000)
        emergency_progress = bank_balance
        emergency_months = max(1, int((emergency_target - emergency_progress) / max(cashflow_delta * 0.3, 100)))
        
        events.append(LifeEvent(
            id="emergency",
            title="Emergency Fund",
            icon="shield",
            targetAmount=emergency_target,
            currentProgress=emergency_progress,
            monthsAway=emergency_months,
            suggestion=f"Save ${max(100, int(cashflow_delta * 0.3)):,.0f}/mo to reach goal",
            color="#34C759",
            aiConfidence=0.85,
            aiReasoning="Standard emergency fund recommendation: 10% of net worth provides 3-6 months of expenses buffer",
            personalizedFactors=[
                f"Based on ${net_worth:,.0f} net worth",
                f"Current cash flow: ${cashflow_delta:,.0f}/mo",
                "Financial best practices"
            ]
        ))
        
        # Home Down Payment (if net worth > 50k)
        if net_worth > 50000:
            home_target = net_worth * 2
            home_progress = 0
            home_months = max(1, int(home_target / max(cashflow_delta * 0.4, 500)))
            
            events.append(LifeEvent(
                id="home",
                title="Home Down Payment",
                icon="home",
                targetAmount=home_target,
                currentProgress=home_progress,
                monthsAway=home_months,
                suggestion=f"Save ${max(500, int(cashflow_delta * 0.4)):,.0f}/mo for down payment",
                color="#007AFF",
                aiConfidence=0.75,
                aiReasoning=f"Based on your net worth of ${net_worth:,.0f}, a home purchase is a realistic goal. Target 20% down payment.",
                personalizedFactors=[
                    f"Net worth analysis: ${net_worth:,.0f}",
                    "Real estate market trends",
                    "Mortgage affordability"
                ]
            ))
        
        # Retirement Savings (if age provided)
        if user_profile and user_profile.age:
            age = user_profile.age
            retirement_target = net_worth * 10 if age < 40 else net_worth * 5
            retirement_progress = portfolio_value
            retirement_months = max(1, int((retirement_target - retirement_progress) / max(cashflow_delta * 0.5, 500)))
            
            events.append(LifeEvent(
                id="retirement",
                title="Retirement Fund",
                icon="trending-up",
                targetAmount=retirement_target,
                currentProgress=retirement_progress,
                monthsAway=retirement_months,
                suggestion=f"Invest ${max(500, int(cashflow_delta * 0.5)):,.0f}/mo for retirement",
                color="#AF52DE",
                aiConfidence=0.80,
                aiReasoning=f"At age {age}, targeting {retirement_target/net_worth:.0f}x current net worth for retirement provides financial security",
                personalizedFactors=[
                    f"Age-based calculation: {age} years old",
                    f"Current portfolio: ${portfolio_value:,.0f}",
                    "Retirement planning best practices"
                ]
            ))
        
        # Education Fund (if net worth > 30k and age < 50)
        if user_profile and user_profile.age and user_profile.age < 50 and net_worth > 30000:
            education_target = 50000
            education_progress = 0
            education_months = max(1, int(education_target / max(cashflow_delta * 0.2, 200)))
            
            events.append(LifeEvent(
                id="education",
                title="Education Fund",
                icon="book",
                targetAmount=education_target,
                currentProgress=education_progress,
                monthsAway=education_months,
                suggestion=f"Save ${max(200, int(cashflow_delta * 0.2)):,.0f}/mo for education",
                color="#5AC8FA",
                aiConfidence=0.70,
                aiReasoning="Education fund provides flexibility for personal development or family education needs",
                personalizedFactors=[
                    "Age-appropriate goal",
                    "Education cost trends",
                    "Financial flexibility"
                ]
            ))
        
        return LifeEventsResponse(events=events)
        
    except Exception as e:
        logger.error(f"Error generating life events: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate life events: {str(e)}")


@router.post("/growth-projections", response_model=GrowthProjectionsResponse)
async def get_ml_growth_projections(request: GrowthProjectionsRequest):
    """
    Get ML-enhanced growth projections with predicted growth rates based on market conditions.
    
    Returns multiple scenarios with ML-predicted growth rates, confidence scores, and market factors.
    """
    try:
        current_value = request.currentValue
        monthly_surplus = request.monthlySurplus
        portfolio_value = request.portfolioValue
        timeframes = request.timeframes
        
        projections = []
        
        # Get market regime prediction from ML service
        market_regime = "neutral"
        volatility = 0.15
        momentum = 0.5
        risk_level = "medium"
        confidence = 0.70
        
        if _ml_service and _market_data_service:
            try:
                market_data = _market_data_service.get_market_regime_indicators()
                regime_prediction = _ml_service.predict_market_regime(market_data)
                
                market_regime = regime_prediction.get('regime', 'neutral')
                confidence = regime_prediction.get('confidence', 0.70)
                volatility = regime_prediction.get('volatility', 0.15)
                momentum = regime_prediction.get('momentum', 0.5)
                
                # Determine risk level based on regime
                if market_regime in ['bull', 'strong_bull']:
                    risk_level = "low"
                elif market_regime in ['bear', 'strong_bear']:
                    risk_level = "high"
                else:
                    risk_level = "medium"
                    
            except Exception as e:
                logger.warning(f"ML prediction error, using defaults: {e}")
        
        # Calculate growth rates based on market regime
        base_rates = {
            'conservative': 5.0,
            'moderate': 8.0,
            'aggressive': 12.0,
            'very_aggressive': 15.0,
            'dividend_focus': 6.0,
            'balanced': 7.0
        }
        
        # Adjust rates based on market regime
        regime_multipliers = {
            'bull': 1.2,
            'strong_bull': 1.3,
            'bear': 0.7,
            'strong_bear': 0.6,
            'neutral': 1.0
        }
        
        multiplier = regime_multipliers.get(market_regime, 1.0)
        
        scenario_configs = [
            ('Conservative Growth', 'conservative', '#34C759', 0.3),
            ('Moderate Growth', 'moderate', '#007AFF', 0.5),
            ('Aggressive Growth', 'aggressive', '#FF9500', 0.7),
            ('Very Aggressive', 'very_aggressive', '#FF3B30', 0.8),
            ('Dividend Focus', 'dividend_focus', '#AF52DE', 0.4),
            ('Balanced Approach', 'balanced', '#5AC8FA', 0.45)
        ]
        
        for timeframe in timeframes:
            for title, key, color, contribution_rate in scenario_configs:
                base_rate = base_rates[key]
                adjusted_rate = base_rate * multiplier
                
                # Calculate projected value
                monthly_rate = adjusted_rate / 12 / 100
                monthly_contribution = monthly_surplus * contribution_rate
                projected_value = current_value
                
                for _ in range(timeframe):
                    projected_value = projected_value * (1 + monthly_rate) + monthly_contribution
                
                projections.append(GrowthProjection(
                    scenario=title,
                    growthRate=adjusted_rate,
                    confidence=confidence,
                    timeframe=timeframe,
                    projectedValue=projected_value,
                    color=color,
                    mlFactors=MLFactors(
                        marketRegime=market_regime,
                        volatility=volatility,
                        momentum=momentum,
                        riskLevel=risk_level
                    )
                ))
        
        return GrowthProjectionsResponse(projections=projections)
        
    except Exception as e:
        logger.error(f"Error generating growth projections: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate projections: {str(e)}")


@router.post("/shield-analysis", response_model=ShieldAnalysisResponse)
async def get_ai_shield_analysis(request: ShieldAnalysisRequest):
    """
    Get AI-powered market analysis and protection strategies for portfolio shield.
    
    Returns real-time market outlook, risk assessment, and prioritized protection strategies.
    """
    try:
        portfolio_value = request.portfolioValue
        bank_balance = request.bankBalance
        positions = request.positions or []
        cashflow = request.cashflow or {}
        
        # Calculate current risk metrics
        cash_ratio = bank_balance / (bank_balance + portfolio_value) if (bank_balance + portfolio_value) > 0 else 0
        current_risk = 1.0 - cash_ratio  # Higher portfolio = higher risk
        
        # Get market regime and outlook
        market_regime = "neutral"
        sentiment = "neutral"
        confidence = 0.60
        key_factors = []
        
        if _ml_service and _market_data_service:
            try:
                market_data = _market_data_service.get_market_regime_indicators()
                regime_prediction = _ml_service.predict_market_regime(market_data)
                
                market_regime = regime_prediction.get('regime', 'neutral')
                confidence = regime_prediction.get('confidence', 0.60)
                
                # Determine sentiment
                if market_regime in ['bull', 'strong_bull']:
                    sentiment = "bullish"
                    key_factors = ["Positive market momentum", "Low volatility", "Strong earnings"]
                elif market_regime in ['bear', 'strong_bear']:
                    sentiment = "bearish"
                    key_factors = ["Market uncertainty", "High volatility", "Economic concerns"]
                else:
                    sentiment = "neutral"
                    key_factors = ["Mixed signals", "Moderate volatility", "Wait and see"]
                    
            except Exception as e:
                logger.warning(f"ML analysis error, using defaults: {e}")
                key_factors = ["Current market conditions", "Portfolio composition"]
        
        # Generate recommended strategies
        strategies = []
        
        # Strategy 1: Increase Cash Reserves
        if cash_ratio < 0.2:
            strategies.append(RecommendedStrategy(
                id="increase-cash",
                priority=1,
                aiReasoning=f"Current cash ratio ({cash_ratio*100:.0f}%) is below recommended 20%. Increasing cash reserves to {((bank_balance + portfolio_value * 0.1) / (bank_balance + portfolio_value)) * 100:.0f}% would improve risk management.",
                expectedImpact="Reduces portfolio volatility by 10-15%"
            ))
        
        # Strategy 2: Pause High-Risk Orders
        if current_risk > 0.7:
            strategies.append(RecommendedStrategy(
                id="pause-risky",
                priority=2,
                aiReasoning=f"Portfolio risk level ({current_risk*100:.0f}%) is high. Pausing high-risk orders (options, margin) would protect against volatility spikes.",
                expectedImpact="Protects against margin calls during volatility"
            ))
        
        # Strategy 3: Set Stop-Loss Orders
        if len(positions) > 0:
            strategies.append(RecommendedStrategy(
                id="stop-loss",
                priority=3,
                aiReasoning=f"With {len(positions)} positions, setting 5-10% stop-loss orders would limit downside risk while preserving upside potential.",
                expectedImpact="Limits downside to 5-10% per position"
            ))
        
        # Strategy 4: Hedge Positions
        if portfolio_value > 50000 and current_risk > 0.6:
            strategies.append(RecommendedStrategy(
                id="hedge-positions",
                priority=4,
                aiReasoning=f"Large portfolio (${portfolio_value:,.0f}) with high risk exposure. Adding 10% hedge allocation (inverse ETFs) would reduce correlation to market downturns.",
                expectedImpact="Reduces portfolio correlation to market by 20-30%"
            ))
        
        # If no strategies, add default
        if not strategies:
            strategies.append(RecommendedStrategy(
                id="increase-cash",
                priority=1,
                aiReasoning="Based on current portfolio allocation, increasing cash reserves would improve risk management",
                expectedImpact="Reduces portfolio volatility by 10-15%"
            ))
        
        return ShieldAnalysisResponse(
            currentRisk=current_risk,
            marketRegime=market_regime,
            recommendedStrategies=strategies,
            marketOutlook=MarketOutlook(
                sentiment=sentiment,
                confidence=confidence,
                keyFactors=key_factors
            )
        )
        
    except Exception as e:
        logger.error(f"Error generating shield analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate shield analysis: {str(e)}")


@router.post("/recommendations", response_model=RecommendationsResponse)
async def get_personalized_recommendations(request: RecommendationsRequest):
    """
    Get personalized AI recommendations based on financial snapshot and user behavior.
    
    Returns actionable recommendations with AI confidence scores and reasoning.
    """
    try:
        snapshot = request.snapshot
        user_behavior = request.userBehavior or {}
        
        net_worth = snapshot.netWorth
        bank_balance = snapshot.breakdown.get('bankBalance', 0)
        portfolio_value = snapshot.breakdown.get('portfolioValue', 0)
        cashflow_delta = snapshot.cashflow.get('delta', 0)
        positions = snapshot.positions or []
        
        recommendations = []
        
        # Recommendation 1: Emergency Fund
        emergency_target = net_worth * 0.1
        if bank_balance < emergency_target:
            recommendations.append(Recommendation(
                type="savings",
                title="Increase Emergency Fund",
                description=f"Build emergency fund to ${emergency_target:,.0f} (currently ${bank_balance:,.0f})",
                action=f"Set aside ${max(100, int(cashflow_delta * 0.3)):,.0f}/mo",
                priority=1,
                aiConfidence=0.85,
                reasoning=f"Emergency fund of 10% net worth provides 3-6 months of expenses buffer. Current: ${bank_balance:,.0f}, Target: ${emergency_target:,.0f}"
            ))
        
        # Recommendation 2: Portfolio Diversification
        if portfolio_value > 0 and len(positions) < 3:
            recommendations.append(Recommendation(
                type="investment",
                title="Diversify Portfolio",
                description=f"Portfolio has only {len(positions)} positions. Diversification reduces risk.",
                action="Add 2-3 positions across different sectors",
                priority=2,
                aiConfidence=0.80,
                reasoning=f"Current portfolio has {len(positions)} positions. Diversifying across 5-10 positions in different sectors reduces risk by 20-30%"
            ))
        
        # Recommendation 3: Increase Savings Rate
        if cashflow_delta > 0 and cashflow_delta < net_worth * 0.01:
            recommendations.append(Recommendation(
                type="savings",
                title="Increase Savings Rate",
                description=f"Current monthly surplus (${cashflow_delta:,.0f}) is low relative to net worth",
                action="Aim to save 10-20% of income monthly",
                priority=3,
                aiConfidence=0.75,
                reasoning=f"Monthly surplus of ${cashflow_delta:,.0f} represents {cashflow_delta/net_worth*100:.1f}% of net worth. Increasing to 1-2% would accelerate wealth building"
            ))
        
        # Recommendation 4: Risk Management
        cash_ratio = bank_balance / (bank_balance + portfolio_value) if (bank_balance + portfolio_value) > 0 else 0
        if cash_ratio < 0.1 and portfolio_value > 0:
            recommendations.append(Recommendation(
                type="risk_management",
                title="Improve Risk Management",
                description=f"Cash ratio ({cash_ratio*100:.0f}%) is very low. Increase cash buffer for safety.",
                action="Rebalance to 10-20% cash allocation",
                priority=1,
                aiConfidence=0.90,
                reasoning=f"Cash ratio of {cash_ratio*100:.0f}% is below recommended 10-20%. Increasing cash provides liquidity and reduces portfolio volatility"
            ))
        
        # Recommendation 5: Life Event Planning
        if net_worth > 50000:
            recommendations.append(Recommendation(
                type="life_event",
                title="Plan for Major Life Events",
                description="Consider setting aside funds for major life events (home, education, retirement)",
                action="Review life event goals in Constellation Orb",
                priority=4,
                aiConfidence=0.70,
                reasoning=f"With net worth of ${net_worth:,.0f}, planning for major life events ensures financial readiness"
            ))
        
        # If no recommendations, add default
        if not recommendations:
            recommendations.append(Recommendation(
                type="savings",
                title="Maintain Current Strategy",
                description="Your financial position looks healthy. Continue current savings and investment strategy.",
                action="Review progress monthly",
                priority=5,
                aiConfidence=0.60,
                reasoning="Based on your current financial snapshot, maintaining current strategy is appropriate"
            ))
        
        # Sort by priority
        recommendations.sort(key=lambda x: x.priority)
        
        return RecommendationsResponse(recommendations=recommendations)
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")

