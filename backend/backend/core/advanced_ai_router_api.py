"""
Advanced AI Router API - Phase 3 Enhanced AI Integration
FastAPI endpoints for GPT-5, Claude, and multi-model AI with advanced capabilities
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import uuid
import logging
from datetime import datetime

from .advanced_ai_router import advanced_ai_router, AIRequest, AIResponse, RequestType, AIModel

logger = logging.getLogger("richesreach")

# Create router
router = APIRouter(prefix="/advanced-ai", tags=["Advanced AI Router"])

# Enhanced Pydantic models for API
class AdvancedAIRequestModel(BaseModel):
    """Enhanced AI request model for API"""
    request_type: str = Field(..., description="Type of AI request")
    prompt: str = Field(..., description="The prompt to send to AI")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Temperature for generation")
    model_preference: Optional[str] = Field(None, description="Preferred AI model")
    budget_limit: Optional[float] = Field(None, description="Maximum cost for this request")
    timeout_seconds: int = Field(30, ge=5, le=120, description="Request timeout in seconds")
    priority: str = Field("normal", description="Request priority (low, normal, high, critical)")
    requires_reasoning: bool = Field(False, description="Requires advanced reasoning")
    requires_math: bool = Field(False, description="Requires mathematical accuracy")
    requires_financial_knowledge: bool = Field(False, description="Requires financial expertise")
    multi_step: bool = Field(False, description="Multi-step reasoning required")
    confidence_threshold: float = Field(0.8, ge=0.0, le=1.0, description="Minimum confidence threshold")

class AdvancedAIResponseModel(BaseModel):
    """Enhanced AI response model for API"""
    request_id: str
    model_used: str
    response: str
    tokens_used: int
    cost: float
    latency_ms: int
    timestamp: str
    confidence_score: float
    reasoning_steps: Optional[List[str]] = None
    mathematical_verification: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class EnsembleRequestModel(BaseModel):
    """Ensemble prediction request model"""
    request_type: str = Field(..., description="Type of AI request")
    prompt: str = Field(..., description="The prompt to send to AI")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Temperature for generation")
    budget_limit: Optional[float] = Field(None, description="Maximum cost for this request")
    timeout_seconds: int = Field(60, ge=10, le=180, description="Request timeout in seconds")
    priority: str = Field("high", description="Request priority for ensemble")
    requires_reasoning: bool = Field(True, description="Requires advanced reasoning")
    requires_math: bool = Field(False, description="Requires mathematical accuracy")
    requires_financial_knowledge: bool = Field(False, description="Requires financial expertise")
    confidence_threshold: float = Field(0.9, ge=0.0, le=1.0, description="Minimum confidence threshold")

class ModelComparisonRequestModel(BaseModel):
    """Model comparison request model"""
    request_type: str = Field(..., description="Type of AI request")
    prompt: str = Field(..., description="The prompt to send to AI")
    models_to_compare: List[str] = Field(..., description="List of models to compare")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Temperature for generation")

class FinancialAnalysisRequestModel(BaseModel):
    """Financial analysis request model"""
    analysis_type: str = Field(..., description="Type of financial analysis")
    symbol: Optional[str] = Field(None, description="Stock symbol")
    portfolio_data: Optional[Dict[str, Any]] = Field(None, description="Portfolio data")
    market_data: Optional[Dict[str, Any]] = Field(None, description="Market data")
    risk_tolerance: str = Field("moderate", description="Risk tolerance level")
    time_horizon: str = Field("medium", description="Investment time horizon")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")

class TradingSignalRequestModel(BaseModel):
    """Trading signal request model"""
    symbol: str = Field(..., description="Stock symbol")
    timeframe: str = Field("1d", description="Analysis timeframe")
    signal_type: str = Field("comprehensive", description="Type of signal analysis")
    market_context: Optional[Dict[str, Any]] = Field(None, description="Market context")
    risk_parameters: Optional[Dict[str, Any]] = Field(None, description="Risk parameters")

# Enhanced API Endpoints
@router.post("/route", response_model=AdvancedAIResponseModel)
async def route_advanced_ai_request(request: AdvancedAIRequestModel):
    """Route a single AI request to the optimal model with advanced features"""
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
            timeout_seconds=request.timeout_seconds,
            priority=request.priority,
            requires_reasoning=request.requires_reasoning,
            requires_math=request.requires_math,
            requires_financial_knowledge=request.requires_financial_knowledge,
            multi_step=request.multi_step,
            confidence_threshold=request.confidence_threshold
        )
        
        # Route request
        response = await advanced_ai_router.route_request(ai_request)
        
        # Convert to API response
        return AdvancedAIResponseModel(
            request_id=response.request_id,
            model_used=response.model_used.value,
            response=response.response,
            tokens_used=response.tokens_used,
            cost=response.cost,
            latency_ms=response.latency_ms,
            timestamp=response.timestamp.isoformat(),
            confidence_score=response.confidence_score,
            reasoning_steps=response.reasoning_steps,
            mathematical_verification=response.mathematical_verification,
            metadata=response.metadata
        )
        
    except Exception as e:
        logger.error(f"Error routing advanced AI request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ensemble")
async def get_ensemble_prediction(request: EnsembleRequestModel):
    """Get ensemble prediction from multiple models"""
    try:
        # Validate request type
        try:
            request_type = RequestType(request.request_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid request type. Valid types: {[rt.value for rt in RequestType]}"
            )
        
        # Create AI request
        ai_request = AIRequest(
            request_id=str(uuid.uuid4()),
            request_type=request_type,
            prompt=request.prompt,
            context=request.context,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            budget_limit=request.budget_limit,
            timeout_seconds=request.timeout_seconds,
            priority=request.priority,
            requires_reasoning=request.requires_reasoning,
            requires_math=request.requires_math,
            requires_financial_knowledge=request.requires_financial_knowledge,
            confidence_threshold=request.confidence_threshold
        )
        
        # Get ensemble prediction
        ensemble_result = await advanced_ai_router.get_ensemble_prediction(ai_request)
        
        return {
            "status": "success",
            "ensemble_result": ensemble_result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting ensemble prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compare-models")
async def compare_models(request: ModelComparisonRequestModel):
    """Compare responses from multiple models"""
    try:
        # Validate request type
        try:
            request_type = RequestType(request.request_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid request type. Valid types: {[rt.value for rt in RequestType]}"
            )
        
        # Validate models
        models_to_compare = []
        for model_name in request.models_to_compare:
            try:
                model = AIModel(model_name)
                models_to_compare.append(model)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid model: {model_name}"
                )
        
        # Get responses from each model
        responses = []
        for model in models_to_compare:
            try:
                ai_request = AIRequest(
                    request_id=str(uuid.uuid4()),
                    request_type=request_type,
                    prompt=request.prompt,
                    context=request.context,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    model_preference=model
                )
                
                response = await advanced_ai_router.route_request(ai_request)
                responses.append({
                    "model": model.value,
                    "response": response.response,
                    "confidence_score": response.confidence_score,
                    "latency_ms": response.latency_ms,
                    "cost": response.cost,
                    "tokens_used": response.tokens_used
                })
            except Exception as e:
                logger.warning(f"Model {model.value} failed: {e}")
                responses.append({
                    "model": model.value,
                    "error": str(e)
                })
        
        return {
            "status": "success",
            "comparison_results": responses,
            "models_compared": len(models_to_compare),
            "successful_responses": len([r for r in responses if "error" not in r]),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error comparing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/financial-analysis")
async def perform_financial_analysis(request: FinancialAnalysisRequestModel):
    """Perform advanced financial analysis using specialized models"""
    try:
        # Create specialized prompt based on analysis type
        if request.analysis_type == "portfolio_optimization":
            prompt = f"""
            Perform comprehensive portfolio optimization analysis:
            
            Portfolio Data: {request.portfolio_data}
            Market Data: {request.market_data}
            Risk Tolerance: {request.risk_tolerance}
            Time Horizon: {request.time_horizon}
            
            Please provide:
            1. Current portfolio analysis and risk assessment
            2. Optimization recommendations using modern portfolio theory
            3. Risk-adjusted return projections
            4. Rebalancing suggestions with specific allocations
            5. Scenario analysis for different market conditions
            
            Use advanced mathematical models and provide detailed reasoning for all recommendations.
            """
            request_type = RequestType.PORTFOLIO_OPTIMIZATION
            requires_reasoning = True
            requires_math = True
            requires_financial_knowledge = True
            
        elif request.analysis_type == "risk_assessment":
            prompt = f"""
            Perform comprehensive risk assessment:
            
            Symbol: {request.symbol}
            Market Data: {request.market_data}
            Risk Tolerance: {request.risk_tolerance}
            
            Please provide:
            1. Quantitative risk metrics (VaR, CVaR, Sharpe ratio, etc.)
            2. Qualitative risk factors and market analysis
            3. Stress testing scenarios
            4. Risk mitigation strategies
            5. Risk-adjusted performance projections
            
            Use advanced statistical models and provide detailed mathematical analysis.
            """
            request_type = RequestType.RISK_ASSESSMENT
            requires_reasoning = True
            requires_math = True
            requires_financial_knowledge = True
            
        elif request.analysis_type == "market_analysis":
            prompt = f"""
            Perform comprehensive market analysis:
            
            Symbol: {request.symbol}
            Market Data: {request.market_data}
            Context: {request.context}
            
            Please provide:
            1. Technical analysis with multiple indicators
            2. Fundamental analysis and valuation metrics
            3. Market sentiment and news analysis
            4. Competitive landscape analysis
            5. Price target and investment recommendation
            
            Use advanced analytical frameworks and provide detailed reasoning.
            """
            request_type = RequestType.MARKET_ANALYSIS
            requires_reasoning = True
            requires_math = False
            requires_financial_knowledge = True
            
        else:
            raise HTTPException(status_code=400, detail="Invalid analysis type")
        
        # Create AI request
        ai_request = AIRequest(
            request_id=str(uuid.uuid4()),
            request_type=request_type,
            prompt=prompt,
            context=request.context,
            max_tokens=4000,
            temperature=0.2,  # Low temperature for financial analysis
            priority="high",
            requires_reasoning=requires_reasoning,
            requires_math=requires_math,
            requires_financial_knowledge=requires_financial_knowledge,
            confidence_threshold=0.9
        )
        
        # Route request
        response = await advanced_ai_router.route_request(ai_request)
        
        return {
            "status": "success",
            "analysis_type": request.analysis_type,
            "analysis": response.response,
            "model_used": response.model_used.value,
            "confidence_score": response.confidence_score,
            "reasoning_steps": response.reasoning_steps,
            "mathematical_verification": response.mathematical_verification,
            "timestamp": response.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error performing financial analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trading-signals")
async def generate_trading_signals(request: TradingSignalRequestModel):
    """Generate advanced trading signals using AI"""
    try:
        # Create specialized prompt for trading signals
        prompt = f"""
        Generate comprehensive trading signals for {request.symbol}:
        
        Timeframe: {request.timeframe}
        Signal Type: {request.signal_type}
        Market Context: {request.market_context}
        Risk Parameters: {request.risk_parameters}
        
        Please provide:
        1. Technical analysis with multiple indicators (RSI, MACD, Bollinger Bands, etc.)
        2. Entry and exit signals with specific price levels
        3. Risk management recommendations (stop-loss, take-profit)
        4. Position sizing recommendations
        5. Market sentiment analysis
        6. Risk-reward ratio analysis
        7. Alternative scenarios and contingency plans
        
        Use advanced technical analysis and provide detailed mathematical reasoning for all signals.
        """
        
        # Create AI request
        ai_request = AIRequest(
            request_id=str(uuid.uuid4()),
            request_type=RequestType.TRADING_SIGNALS,
            prompt=prompt,
            context={
                "symbol": request.symbol,
                "timeframe": request.timeframe,
                "market_context": request.market_context,
                "risk_parameters": request.risk_parameters
            },
            max_tokens=3000,
            temperature=0.1,  # Very low temperature for trading signals
            priority="critical",
            requires_reasoning=True,
            requires_math=True,
            requires_financial_knowledge=True,
            confidence_threshold=0.95
        )
        
        # Route request
        response = await advanced_ai_router.route_request(ai_request)
        
        return {
            "status": "success",
            "symbol": request.symbol,
            "timeframe": request.timeframe,
            "trading_signals": response.response,
            "model_used": response.model_used.value,
            "confidence_score": response.confidence_score,
            "reasoning_steps": response.reasoning_steps,
            "mathematical_verification": response.mathematical_verification,
            "timestamp": response.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating trading signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models", response_model=Dict[str, Any])
async def get_available_models():
    """Get available AI models and their enhanced capabilities"""
    try:
        return {
            "models": advanced_ai_router.get_model_capabilities(),
            "request_types": [rt.value for rt in RequestType],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance", response_model=Dict[str, Any])
async def get_model_performance():
    """Get enhanced model performance statistics"""
    try:
        stats = advanced_ai_router.get_performance_stats()
        return {
            "status": "success",
            "performance_stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting model performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def advanced_ai_health():
    """Health check for Advanced AI Router"""
    try:
        # Test with a simple request
        test_request = AIRequest(
            request_id=str(uuid.uuid4()),
            request_type=RequestType.GENERAL_CHAT,
            prompt="Hello, this is a health check for the advanced AI router.",
            max_tokens=10,
            temperature=0.1
        )
        
        response = await advanced_ai_router.route_request(test_request)
        
        return {
            "status": "healthy",
            "test_response": response.response,
            "model_used": response.model_used.value,
            "latency_ms": response.latency_ms,
            "confidence_score": response.confidence_score,
            "models_available": len(advanced_ai_router.models),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Advanced AI Router health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Specialized endpoints for different AI capabilities
@router.post("/reasoning")
async def advanced_reasoning(request: AdvancedAIRequestModel):
    """Advanced reasoning endpoint with enhanced capabilities"""
    request.requires_reasoning = True
    request.priority = "high"
    request.confidence_threshold = 0.9
    return await route_advanced_ai_request(request)

@router.post("/mathematical")
async def mathematical_analysis(request: AdvancedAIRequestModel):
    """Mathematical analysis endpoint with verification"""
    request.requires_math = True
    request.requires_reasoning = True
    request.priority = "high"
    request.confidence_threshold = 0.95
    return await route_advanced_ai_request(request)

@router.post("/financial")
async def financial_analysis(request: AdvancedAIRequestModel):
    """Financial analysis endpoint with specialized knowledge"""
    request.requires_financial_knowledge = True
    request.requires_reasoning = True
    request.priority = "high"
    request.confidence_threshold = 0.9
    return await route_advanced_ai_request(request)

@router.post("/research")
async def research_analysis(request: AdvancedAIRequestModel):
    """Research analysis endpoint with multi-step reasoning"""
    request.multi_step = True
    request.requires_reasoning = True
    request.priority = "high"
    request.confidence_threshold = 0.9
    return await route_advanced_ai_request(request)
