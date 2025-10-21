"""
AI Router API - Phase 3 Advanced AI Integration
FastAPI endpoints for the AI Router microservice
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import uuid
import logging
from datetime import datetime

from .ai_router import ai_router, AIRequest, AIResponse, RequestType, AIModel

logger = logging.getLogger("richesreach")

# Create router
router = APIRouter(prefix="/ai", tags=["AI Router"])

# Pydantic models for API
class AIRequestModel(BaseModel):
    """AI request model for API"""
    request_type: str = Field(..., description="Type of AI request")
    prompt: str = Field(..., description="The prompt to send to AI")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    temperature: float = Field(1.0, ge=0.0, le=2.0, description="Temperature for generation (1.0 for GPT-5 compatibility)")
    model_preference: Optional[str] = Field(None, description="Preferred AI model")
    budget_limit: Optional[float] = Field(None, description="Maximum cost for this request")
    timeout_seconds: int = Field(30, ge=5, le=120, description="Request timeout in seconds")

class AIResponseModel(BaseModel):
    """AI response model for API"""
    request_id: str
    model_used: str
    response: str
    tokens_used: int
    cost: float
    latency_ms: int
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None

class BatchAIRequestModel(BaseModel):
    """Batch AI request model"""
    requests: List[AIRequestModel] = Field(..., description="List of AI requests")
    max_concurrent: int = Field(5, ge=1, le=10, description="Maximum concurrent requests")

class ModelPerformanceModel(BaseModel):
    """Model performance model"""
    model: str
    total_requests: int
    successful_requests: int
    success_rate: float
    average_latency_ms: float
    average_cost: float
    last_updated: str

@router.post("/route", response_model=AIResponseModel)
async def route_ai_request(request: AIRequestModel):
    """Route a single AI request to the optimal model"""
    try:
        # Validate request type
        try:
            request_type = RequestType(request.request_type)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid request type. Valid types: {[rt.value for rt in RequestType]}"
            )
        
        # Validate model preference if provided
        model_preference = None
        if request.model_preference:
            try:
                model_preference = AIModel(request.model_preference)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid model preference. Valid models: {[m.value for m in AIModel]}"
                )
        
        # Create AI request
        ai_request = AIRequest(
            request_id=str(uuid.uuid4()),
            request_type=request_type,
            prompt=request.prompt,
            context=request.context,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            model_preference=model_preference,
            budget_limit=request.budget_limit,
            timeout_seconds=request.timeout_seconds
        )
        
        # Route request
        response = await ai_router.route_request(ai_request)
        
        # Convert to API response
        return AIResponseModel(
            request_id=response.request_id,
            model_used=response.model_used.value,
            response=response.response,
            tokens_used=response.tokens_used,
            cost=response.cost,
            latency_ms=response.latency_ms,
            timestamp=response.timestamp.isoformat(),
            metadata=response.metadata
        )
        
    except Exception as e:
        logger.error(f"Error routing AI request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/route/batch", response_model=List[AIResponseModel])
async def route_batch_ai_requests(batch_request: BatchAIRequestModel):
    """Route multiple AI requests concurrently"""
    try:
        import asyncio
        
        # Create AI requests
        ai_requests = []
        for req in batch_request.requests:
            try:
                request_type = RequestType(req.request_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid request type: {req.request_type}"
                )
            
            model_preference = None
            if req.model_preference:
                try:
                    model_preference = AIModel(req.model_preference)
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid model preference: {req.model_preference}"
                    )
            
            ai_request = AIRequest(
                request_id=str(uuid.uuid4()),
                request_type=request_type,
                prompt=req.prompt,
                context=req.context,
                max_tokens=req.max_tokens,
                temperature=req.temperature,
                model_preference=model_preference,
                budget_limit=req.budget_limit,
                timeout_seconds=req.timeout_seconds
            )
            ai_requests.append(ai_request)
        
        # Process requests with concurrency limit
        semaphore = asyncio.Semaphore(batch_request.max_concurrent)
        
        async def process_request(request):
            async with semaphore:
                return await ai_router.route_request(request)
        
        # Execute batch requests
        responses = await asyncio.gather(*[process_request(req) for req in ai_requests])
        
        # Convert to API responses
        api_responses = []
        for response in responses:
            api_responses.append(AIResponseModel(
                request_id=response.request_id,
                model_used=response.model_used.value,
                response=response.response,
                tokens_used=response.tokens_used,
                cost=response.cost,
                latency_ms=response.latency_ms,
                timestamp=response.timestamp.isoformat(),
                metadata=response.metadata
            ))
        
        return api_responses
        
    except Exception as e:
        logger.error(f"Error routing batch AI requests: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models", response_model=Dict[str, Any])
async def get_available_models():
    """Get available AI models and their capabilities"""
    try:
        return {
            "models": ai_router.get_model_capabilities(),
            "request_types": [rt.value for rt in RequestType],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance", response_model=Dict[str, ModelPerformanceModel])
async def get_model_performance():
    """Get performance statistics for all models"""
    try:
        stats = ai_router.get_performance_stats()
        performance_models = {}
        
        for model_name, stats_data in stats.items():
            performance_models[model_name] = ModelPerformanceModel(**stats_data)
        
        return performance_models
        
    except Exception as e:
        logger.error(f"Error getting model performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/market")
async def analyze_market_data(symbol: str, timeframe: str = "1d", analysis_type: str = "technical"):
    """Specialized endpoint for market analysis"""
    try:
        # Create market analysis prompt
        prompt = f"""
        Analyze the market data for {symbol} with {timeframe} timeframe.
        Analysis type: {analysis_type}
        
        Please provide:
        1. Technical analysis summary
        2. Key support and resistance levels
        3. Trend analysis
        4. Risk assessment
        5. Trading recommendations
        
        Be concise but comprehensive.
        """
        
        # Create AI request
        ai_request = AIRequest(
            request_id=str(uuid.uuid4()),
            request_type=RequestType.MARKET_ANALYSIS,
            prompt=prompt,
            context={
                "symbol": symbol,
                "timeframe": timeframe,
                "analysis_type": analysis_type
            },
            temperature=1.0,  # Temperature for financial analysis (GPT-5 compatible)
            max_tokens=2000
        )
        
        # Route request
        response = await ai_router.route_request(ai_request)
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "analysis_type": analysis_type,
            "analysis": response.response,
            "model_used": response.model_used.value,
            "confidence": "high" if response.model_used in [AIModel.GPT_4O, AIModel.CLAUDE_3_5_SONNET] else "medium",
            "timestamp": response.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize/portfolio")
async def optimize_portfolio(portfolio_data: Dict[str, Any]):
    """Specialized endpoint for portfolio optimization"""
    try:
        # Create portfolio optimization prompt
        prompt = f"""
        Optimize the following portfolio based on modern portfolio theory and risk management:
        
        Portfolio Data: {portfolio_data}
        
        Please provide:
        1. Current portfolio analysis
        2. Risk assessment
        3. Optimization recommendations
        4. Rebalancing suggestions
        5. Risk-adjusted return projections
        
        Focus on practical, actionable advice.
        """
        
        # Create AI request
        ai_request = AIRequest(
            request_id=str(uuid.uuid4()),
            request_type=RequestType.PORTFOLIO_OPTIMIZATION,
            prompt=prompt,
            context={"portfolio_data": portfolio_data},
            temperature=1.0,  # Temperature for financial calculations (GPT-5 compatible)
            max_tokens=3000
        )
        
        # Route request
        response = await ai_router.route_request(ai_request)
        
        return {
            "portfolio_analysis": response.response,
            "model_used": response.model_used.value,
            "optimization_timestamp": response.timestamp.isoformat(),
            "confidence": "high"
        }
        
    except Exception as e:
        logger.error(f"Error optimizing portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sentiment/news")
async def analyze_news_sentiment(news_data: List[Dict[str, Any]]):
    """Specialized endpoint for news sentiment analysis"""
    try:
        # Create sentiment analysis prompt
        news_text = "\n".join([f"- {item.get('title', '')}: {item.get('content', '')}" for item in news_data])
        
        prompt = f"""
        Analyze the sentiment of the following financial news articles:
        
        {news_text}
        
        Please provide:
        1. Overall market sentiment (bullish/bearish/neutral)
        2. Key themes and topics
        3. Sentiment score (-1 to +1)
        4. Confidence level
        5. Potential market impact
        
        Be objective and data-driven in your analysis.
        """
        
        # Create AI request
        ai_request = AIRequest(
            request_id=str(uuid.uuid4()),
            request_type=RequestType.NEWS_SENTIMENT,
            prompt=prompt,
            context={"news_count": len(news_data)},
            temperature=1.0,  # Temperature for sentiment analysis (GPT-5 compatible)
            max_tokens=1500
        )
        
        # Route request
        response = await ai_router.route_request(ai_request)
        
        return {
            "sentiment_analysis": response.response,
            "model_used": response.model_used.value,
            "news_count": len(news_data),
            "analysis_timestamp": response.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing news sentiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def ai_router_health():
    """Health check for AI Router"""
    try:
        # Test with a simple request
        test_request = AIRequest(
            request_id=str(uuid.uuid4()),
            request_type=RequestType.GENERAL_CHAT,
            prompt="Hello, this is a health check.",
            max_tokens=10,
            temperature=1.0
        )
        
        response = await ai_router.route_request(test_request)
        
        return {
            "status": "healthy",
            "test_response": response.response,
            "model_used": response.model_used.value,
            "latency_ms": response.latency_ms,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"AI Router health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
