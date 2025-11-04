"""
Holding Insight API - AI insights for individual portfolio holdings
Phase 3: Fast, cached, human-readable insights
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/coach", tags=["Holding Insights"])


class HoldingInsight(BaseModel):
    """AI insight response for a holding"""
    headline: str  # One-line "Why now" insight
    drivers: list[str]  # Up to 3 key drivers


@router.get("/holding-insight", response_model=HoldingInsight)
async def get_holding_insight(ticker: str = Query(..., description="Stock ticker symbol")):
    """
    Get AI-powered insight for a specific holding.
    
    Returns a quick, actionable insight about why this holding might be
    interesting right now. Cached for 5-15 minutes.
    
    Example:
        GET /api/coach/holding-insight?ticker=AAPL
        {
            "headline": "Strong earnings beat expected",
            "drivers": ["Revenue growth", "iPhone sales", "Services expansion"]
        }
    """
    try:
        ticker = ticker.upper().strip()
        
        # TODO: Replace with actual AI/ML model or LLM call
        # For now, return mock insights based on ticker
        mock_insights = {
            "AAPL": {
                "headline": "Strong iPhone 15 sales driving momentum",
                "drivers": ["Revenue growth", "Services expansion", "China recovery"]
            },
            "MSFT": {
                "headline": "AI integration driving Azure growth",
                "drivers": ["Cloud adoption", "Office 365", "Copilot demand"]
            },
            "GOOGL": {
                "headline": "Search revenue stable, YouTube growing",
                "drivers": ["Ad recovery", "YouTube Premium", "Cloud expansion"]
            },
        }
        
        insight = mock_insights.get(ticker, {
            "headline": "Market sentiment positive",
            "drivers": ["Recent earnings", "Sector momentum"]
        })
        
        logger.info(f"Generated insight for {ticker}: {insight['headline']}")
        
        return HoldingInsight(**insight)
        
    except Exception as e:
        logger.error(f"Error generating insight for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate insight: {str(e)}")

