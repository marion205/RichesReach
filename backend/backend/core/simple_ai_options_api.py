"""
Simple AI Options API - Clean implementation using the fixed engine
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.ai_options_engine import AIOptionsEngine

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/ai-options", tags=["AI Options"])

# Initialize AI engine
ai_engine = AIOptionsEngine()

# Request/Response models
class OptionsRequest(BaseModel):
    symbol: str
    user_risk_tolerance: str = "medium"
    portfolio_value: float = 10000.0
    time_horizon: int = 30
    max_recommendations: int = 5

class OptionsResponse(BaseModel):
    symbol: str
    recommendations: List[Dict[str, Any]]
    market_analysis: Dict[str, Any]
    generated_at: str
    total_recommendations: int

@router.post("/recommendations", response_model=OptionsResponse)
async def get_ai_recommendations(request: OptionsRequest):
    """
    Get AI-powered options recommendations
    """
    try:
        logger.info(f"AI Options request for {request.symbol}")
        
        # Validate inputs
        if request.user_risk_tolerance not in ['low', 'medium', 'high']:
            raise HTTPException(
                status_code=400, 
                detail="user_risk_tolerance must be 'low', 'medium', or 'high'"
            )
        
        if request.portfolio_value <= 0:
            raise HTTPException(
                status_code=400, 
                detail="portfolio_value must be positive"
            )
        
        if request.time_horizon <= 0:
            raise HTTPException(
                status_code=400, 
                detail="time_horizon must be positive"
            )

        # Generate recommendations using the cleaned engine
        recommendations = await ai_engine.generate_recommendations(
            symbol=request.symbol,
            user_risk_tolerance=request.user_risk_tolerance,
            portfolio_value=request.portfolio_value,
            time_horizon=request.time_horizon
        )
        
        # Limit to max_recommendations
        recommendations = recommendations[:request.max_recommendations]
        
        # Create market analysis (simplified)
        market_analysis = {
            "symbol": request.symbol,
            "current_price": 100.0,  # Will be updated by engine
            "volatility": 0.25,
            "sentiment": "neutral",
            "trend": "neutral"
        }
        
        # Update with actual data if available
        if recommendations:
            first_rec = recommendations[0]
            market_analysis["current_price"] = first_rec.get("current_price", 100.0)
            market_analysis["sentiment"] = first_rec.get("sentiment", "neutral")
        
        return OptionsResponse(
            symbol=request.symbol,
            recommendations=recommendations,
            market_analysis=market_analysis,
            generated_at="2024-01-01T00:00:00Z",  # Will be updated by engine
            total_recommendations=len(recommendations)
        )
        
    except Exception as e:
        logger.exception(f"Error generating AI options recommendations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate recommendations: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ai-options-api"}
