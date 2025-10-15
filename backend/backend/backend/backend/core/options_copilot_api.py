"""
Options Copilot API
FastAPI endpoints for AI-powered options strategy recommendations
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import asyncio
import logging

from .options_copilot_engine import OptionsCopilotEngine
from .monitoring import logger

router = APIRouter(prefix="/api/options/copilot", tags=["Options Copilot"])

# Initialize Options Copilot Engine
options_copilot_engine = OptionsCopilotEngine()

# Pydantic Models
class OptionsCopilotRequest(BaseModel):
    symbol: str
    current_price: float
    risk_tolerance: str  # 'low', 'medium', 'high'
    time_horizon: str    # 'short', 'medium', 'long'
    max_risk: float
    account_value: float
    market_outlook: str  # 'bullish', 'bearish', 'neutral'

class ExpectedPayoff(BaseModel):
    max_profit: float
    max_loss: float
    breakeven_points: List[float]
    profit_probability: float
    expected_value: float
    time_decay: float

class Greeks(BaseModel):
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float

class SlippageEstimate(BaseModel):
    bid_ask_spread: float
    market_impact: float
    total_slippage: float
    liquidity_score: float

class RiskExplanation(BaseModel):
    plain_english: str
    risk_factors: List[str]
    mitigation_strategies: List[str]
    worst_case_scenario: str
    probability_of_loss: float

class StrategyLeg(BaseModel):
    action: str  # 'buy', 'sell'
    option_type: str  # 'call', 'put'
    quantity: int
    strike_price: float
    expiration_date: str
    premium: float
    greeks: Greeks

class StrategySetup(BaseModel):
    legs: List[StrategyLeg]
    total_cost: float
    margin_requirement: float
    expiration_date: str
    strike_prices: List[float]

class RiskRails(BaseModel):
    max_position_size: float
    stop_loss: float
    take_profit: float
    time_stop: int
    volatility_stop: float
    max_drawdown: float

class StrategyRecommendation(BaseModel):
    id: str
    name: str
    type: str
    description: str
    expected_payoff: ExpectedPayoff
    greeks: Greeks
    slippage_estimate: SlippageEstimate
    risk_explanation: RiskExplanation
    setup: StrategySetup
    risk_rails: RiskRails
    confidence: float
    reasoning: str

class RiskFactor(BaseModel):
    factor: str
    impact: str  # 'low', 'medium', 'high'
    description: str
    mitigation: str

class RiskAssessment(BaseModel):
    overall_risk: str  # 'low', 'medium', 'high'
    risk_score: float
    risk_factors: List[RiskFactor]
    recommendations: List[str]

class VolatilityAnalysis(BaseModel):
    current_iv: float
    historical_iv: float
    iv_percentile: float
    iv_rank: float
    trend: str  # 'increasing', 'decreasing', 'stable'

class SentimentSource(BaseModel):
    source: str
    sentiment: str  # 'bullish', 'bearish', 'neutral'
    confidence: float

class SentimentAnalysis(BaseModel):
    overall: str  # 'bullish', 'bearish', 'neutral'
    score: float
    sources: List[SentimentSource]

class TechnicalIndicator(BaseModel):
    name: str
    value: float
    signal: str  # 'bullish', 'bearish', 'neutral'
    strength: float

class TechnicalAnalysis(BaseModel):
    trend: str  # 'bullish', 'bearish', 'neutral'
    support: float
    resistance: float
    key_levels: List[float]
    indicators: List[TechnicalIndicator]

class FundamentalMetric(BaseModel):
    metric: str
    value: float
    benchmark: float
    signal: str  # 'positive', 'negative', 'neutral'

class FundamentalAnalysis(BaseModel):
    rating: str  # 'strong_buy', 'buy', 'hold', 'sell', 'strong_sell'
    price_target: float
    upside: float
    key_metrics: List[FundamentalMetric]

class MarketAnalysis(BaseModel):
    volatility: VolatilityAnalysis
    sentiment: SentimentAnalysis
    technical: TechnicalAnalysis
    fundamental: FundamentalAnalysis

class OptionsCopilotResponse(BaseModel):
    symbol: str
    current_price: float
    market_outlook: str
    recommended_strategies: List[StrategyRecommendation]
    risk_assessment: RiskAssessment
    market_analysis: MarketAnalysis

class OptionsChainRequest(BaseModel):
    symbol: str
    expiration_date: Optional[str] = None

class PnLCalculationRequest(BaseModel):
    strategy: StrategyRecommendation
    price_scenarios: List[float]

@router.post("/recommendations", response_model=OptionsCopilotResponse)
async def get_recommendations(request: OptionsCopilotRequest):
    """Get AI-powered options strategy recommendations"""
    try:
        copilot_request = CopilotRequest(
            symbol=request.symbol,
            current_price=request.current_price,
            risk_tolerance=request.risk_tolerance,
            time_horizon=request.time_horizon,
            max_risk=request.max_risk,
            account_value=request.account_value,
            market_outlook=request.market_outlook
        )
        
        response = await options_copilot_engine.get_recommendations(copilot_request)
        logger.info(f"Generated {len(response.recommended_strategies)} recommendations for {request.symbol}")
        return response
        
    except Exception as e:
        logger.error(f"Error getting recommendations for {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chain")
async def get_options_chain(
    symbol: str = Query(..., description="Stock symbol"),
    expiration: Optional[str] = Query(None, description="Expiration date (YYYY-MM-DD)")
):
    """Get options chain data for a symbol"""
    try:
        chain = await options_copilot_engine.get_options_chain(symbol, expiration)
        logger.info(f"Retrieved options chain for {symbol}")
        return chain
        
    except Exception as e:
        logger.error(f"Error getting options chain for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculate-pnl")
async def calculate_strategy_pnl(request: PnLCalculationRequest):
    """Calculate strategy P&L for different price scenarios"""
    try:
        pnl_results = await options_copilot_engine.calculate_strategy_pnl(
            request.strategy, 
            request.price_scenarios
        )
        logger.info(f"Calculated P&L for {len(request.price_scenarios)} scenarios")
        return pnl_results
        
    except Exception as e:
        logger.error(f"Error calculating strategy P&L: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/risk-analysis")
async def get_risk_analysis(strategy: StrategyRecommendation):
    """Get detailed risk analysis for a strategy"""
    try:
        risk_analysis = await options_copilot_engine.get_risk_analysis(strategy)
        logger.info(f"Generated risk analysis for strategy {strategy.id}")
        return risk_analysis
        
    except Exception as e:
        logger.error(f"Error getting risk analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/strategies")
async def get_available_strategies():
    """Get list of available options strategies"""
    try:
        strategies = await options_copilot_engine.get_available_strategies()
        logger.info(f"Retrieved {len(strategies)} available strategies")
        return strategies
        
    except Exception as e:
        logger.error(f"Error getting available strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market-data/{symbol}")
async def get_market_data(symbol: str):
    """Get comprehensive market data for options analysis"""
    try:
        market_data = await options_copilot_engine.get_market_data(symbol)
        logger.info(f"Retrieved market data for {symbol}")
        return market_data
        
    except Exception as e:
        logger.error(f"Error getting market data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backtest")
async def backtest_strategy(
    strategy: StrategyRecommendation,
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    symbol: str = Query(..., description="Stock symbol")
):
    """Backtest a strategy against historical data"""
    try:
        backtest_results = await options_copilot_engine.backtest_strategy(
            strategy, symbol, start_date, end_date
        )
        logger.info(f"Backtested strategy {strategy.id} for {symbol}")
        return backtest_results
        
    except Exception as e:
        logger.error(f"Error backtesting strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/greeks-calculator")
async def calculate_greeks(
    symbol: str = Query(..., description="Stock symbol"),
    strike: float = Query(..., description="Strike price"),
    expiration: str = Query(..., description="Expiration date (YYYY-MM-DD)"),
    option_type: str = Query(..., description="'call' or 'put'"),
    current_price: float = Query(..., description="Current stock price"),
    volatility: float = Query(..., description="Implied volatility"),
    risk_free_rate: float = Query(0.05, description="Risk-free rate")
):
    """Calculate Greeks for a specific option"""
    try:
        greeks = await options_copilot_engine.calculate_greeks(
            symbol, strike, expiration, option_type, 
            current_price, volatility, risk_free_rate
        )
        logger.info(f"Calculated Greeks for {symbol} {option_type} {strike}")
        return greeks
        
    except Exception as e:
        logger.error(f"Error calculating Greeks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/volatility-analysis/{symbol}")
async def get_volatility_analysis(symbol: str):
    """Get comprehensive volatility analysis for a symbol"""
    try:
        vol_analysis = await options_copilot_engine.get_volatility_analysis(symbol)
        logger.info(f"Retrieved volatility analysis for {symbol}")
        return vol_analysis
        
    except Exception as e:
        logger.error(f"Error getting volatility analysis for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for Options Copilot service"""
    try:
        status = await options_copilot_engine.get_health_status()
        return {
            "status": "healthy",
            "service": "options_copilot",
            "details": status
        }
    except Exception as e:
        logger.error(f"Options Copilot health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")
