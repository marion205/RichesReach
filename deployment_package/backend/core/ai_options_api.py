"""
AI Options API Endpoints
REST API for AI-Powered Options Recommendations
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import json  # used for serialization test
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from .ai_options_engine import AIOptionsEngine, OptionsRecommendation
from .options_ml_models import OptionsMLModels


logger = logging.getLogger(__name__)


def make_json_safe(obj: Any) -> Any:
    """Recursively convert inf / -inf / NaN values to safe numbers."""
    if isinstance(obj, float):
        if obj == float("inf"):
            return 999_999.0
        elif obj == float("-inf"):
            return -999_999.0
        elif obj != obj:  # NaN check
            return 0.0
        return obj
    elif isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_safe(item) for item in obj]
    return obj


# Initialize AI services
ai_engine = AIOptionsEngine()
ml_models = OptionsMLModels()

# Create API router
router = APIRouter(prefix="/api/ai-options", tags=["AI Options"])


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class OptionsRequest(BaseModel):
    symbol: str
    user_risk_tolerance: str = "medium"  # low, medium, high
    portfolio_value: float = 10_000
    time_horizon: int = 30  # days
    max_recommendations: int = 5


class OptionsResponse(BaseModel):
    symbol: str
    current_price: float
    recommendations: List[Dict[str, Any]]
    market_analysis: Dict[str, Any]
    generated_at: datetime
    total_recommendations: int


class StrategyOptimizationRequest(BaseModel):
    symbol: str
    strategy_type: str  # covered_call, protective_put, iron_condor, etc.
    current_price: float
    user_preferences: Optional[Dict[str, Any]] = None


class StrategyOptimizationResponse(BaseModel):
    symbol: str
    strategy_type: str
    optimal_parameters: Dict[str, Any]
    optimization_score: float
    predicted_outcomes: Dict[str, Any]
    generated_at: datetime


class MarketAnalysisRequest(BaseModel):
    symbol: str
    analysis_type: str = "comprehensive"  # comprehensive, quick, detailed


class MarketAnalysisResponse(BaseModel):
    symbol: str
    analysis: Dict[str, Any]
    predictions: Dict[str, Any]
    confidence_scores: Dict[str, float]
    generated_at: datetime


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post("/recommendations")
async def get_ai_recommendations(request: OptionsRequest):
    """
    Get AI-powered options recommendations.

    This endpoint provides hedge fund-level options strategy recommendations
    based on advanced ML models and market analysis.
    """
    try:
        logger.info("=" * 50)
        logger.info(" NEW REQUEST: AI Options Recommendations")
        logger.info(" Symbol: %s", request.symbol)
        logger.info(" Risk Tolerance: %s", request.user_risk_tolerance)
        logger.info(" Portfolio Value: $%s", f"{request.portfolio_value:,.2f}")
        logger.info(" Time Horizon: %s days", request.time_horizon)
        logger.info(" Max Recommendations: %s", request.max_recommendations)
        logger.info("=" * 50)

        # ------------------------------------------------------------------
        # Validate inputs
        # ------------------------------------------------------------------
        logger.info(" Validating request parameters...")

        if request.user_risk_tolerance not in ["low", "medium", "high"]:
            logger.error(" Invalid risk tolerance: %s", request.user_risk_tolerance)
            raise HTTPException(
                status_code=400,
                detail="user_risk_tolerance must be 'low', 'medium', or 'high'",
            )

        if request.portfolio_value <= 0:
            logger.error(" Invalid portfolio value: %s", request.portfolio_value)
            raise HTTPException(status_code=400, detail="portfolio_value must be positive")

        if request.time_horizon <= 0:
            logger.error(" Invalid time horizon: %s", request.time_horizon)
            raise HTTPException(status_code=400, detail="time_horizon must be positive")

        logger.info(" Request validation passed")

        # ------------------------------------------------------------------
        # Generate recommendations (legacy compatibility method)
        # ------------------------------------------------------------------
        logger.info(" Starting AI recommendation generation...")

        # NOTE: This assumes AIOptionsEngine has an async method
        # `generate_recommendations_legacy(...)`.
        recommendations = await ai_engine.generate_recommendations_legacy(
            symbol=request.symbol,
            user_risk_tolerance=request.user_risk_tolerance,
            portfolio_value=request.portfolio_value,
            time_horizon=request.time_horizon,
        )

        logger.info(" Generated %d raw recommendations", len(recommendations))

        for i, rec in enumerate(recommendations):
            logger.info(
                " Recommendation %d: %s (%s)",
                i + 1,
                rec.get("strategy_name", "Unknown"),
                rec.get("strategy_type", "unknown"),
            )
            logger.info("  Confidence: %s%%", rec.get("confidence_score", 0))
            logger.info("  Risk Score: %s", rec.get("risk_score", 0))
            logger.info(
                "  Expected Return: %.2f%%",
                float(rec.get("expected_return", 0)) * 100,
            )
            logger.info("  Max Profit: $%s", rec.get("max_profit", 0))
            logger.info("  Max Loss: $%s", rec.get("max_loss", 0))

        # ------------------------------------------------------------------
        # Limit recommendations
        # ------------------------------------------------------------------
        original_count = len(recommendations)
        recommendations = recommendations[: request.max_recommendations]
        logger.info(
            " Limited recommendations from %d to %d",
            original_count,
            len(recommendations),
        )

        # ------------------------------------------------------------------
        # Convert to JSON-safe API format
        # ------------------------------------------------------------------
        logger.info(" Converting recommendations to JSON-safe format...")
        recommendations_dict: List[Dict[str, Any]] = []

        for i, rec in enumerate(recommendations):
            logger.info(
                " Processing recommendation %d: %s",
                i + 1,
                rec.get("strategy_name", "Unknown"),
            )

            # rec is already a dict from legacy method
            analytics = rec.get("analytics", {}) or {}

            rec_dict: Dict[str, Any] = {
                "strategy_name": rec.get("strategy_name", "Unknown Strategy"),
                "strategy_type": rec.get("strategy_type", "speculation"),
                "confidence_score": make_json_safe(rec.get("confidence_score", 50.0)),
                "symbol": rec.get("symbol", request.symbol),
                "current_price": make_json_safe(rec.get("current_price", 100.0)),
                "options": rec.get("options", []),
                "analytics": {k: make_json_safe(v) for k, v in analytics.items()},
                "reasoning": rec.get("reasoning", {}),
                "risk_score": make_json_safe(rec.get("risk_score", 50.0)),
                "expected_return": make_json_safe(rec.get("expected_return", 0.1)),
                "max_profit": make_json_safe(rec.get("max_profit", 0)),
                "max_loss": make_json_safe(rec.get("max_loss", 0)),
                "probability_of_profit": make_json_safe(rec.get("probability_of_profit", 0.5)),
                "days_to_expiration": int(rec.get("days_to_expiration", 30)),
                "market_outlook": rec.get("market_outlook", "neutral"),
                "created_at": (
                    rec.get("created_at", datetime.now()).isoformat()
                    if isinstance(rec.get("created_at"), datetime)
                    else datetime.now().isoformat()
                ),
            }

            recommendations_dict.append(rec_dict)
            logger.info(" Recommendation %d converted successfully", i + 1)

        logger.info(" Successfully converted %d recommendations", len(recommendations_dict))

        # ------------------------------------------------------------------
        # Market analysis placeholder (since new engine may not expose it)
        # ------------------------------------------------------------------
        logger.info(" Building placeholder market analysis...")
        market_analysis_dict: Dict[str, Any] = {
            "symbol": request.symbol,
            "current_price": 100.0,  # TODO: replace with real price
            "volatility": 0.2,
            "implied_volatility": 0.25,
            "volume": 1_000_000,
            "market_cap": 1_000_000_000,
            "sector": "Technology",
            "sentiment_score": 0.0,
            "trend_direction": "neutral",
            "support_levels": [],
            "resistance_levels": [],
            "earnings_date": None,
            "dividend_yield": 0.0,
            "beta": 1.0,
        }

        logger.info(" Market Analysis Results:")
        logger.info("  Symbol: %s", market_analysis_dict["symbol"])
        logger.info("  Current Price: %s", market_analysis_dict["current_price"])
        logger.info("  Volatility: %s", market_analysis_dict["volatility"])
        logger.info("  Volume: %s", market_analysis_dict["volume"])
        logger.info("  Sector: %s", market_analysis_dict["sector"])
        logger.info("  Trend: %s", market_analysis_dict["trend_direction"])

        # ------------------------------------------------------------------
        # Final response
        # ------------------------------------------------------------------
        logger.info(" Building final response...")

        response_data: Dict[str, Any] = {
            "symbol": request.symbol,
            "current_price": market_analysis_dict["current_price"],
            "recommendations": recommendations_dict,
            "market_analysis": market_analysis_dict,
            "generated_at": datetime.now().isoformat(),
            "total_recommendations": len(recommendations_dict),
        }

        logger.info(" Final Response Summary:")
        logger.info("  Symbol: %s", response_data["symbol"])
        logger.info("  Current Price: %s", response_data["current_price"])
        logger.info("  Total Recommendations: %s", response_data["total_recommendations"])
        logger.info("  Generated At: %s", response_data["generated_at"])

        # Test JSON serialization
        logger.info(" Testing JSON serialization...")
        try:
            json_str = json.dumps(response_data)
            logger.info(
                " JSON serialization successful! Length: %d characters",
                len(json_str),
            )
        except Exception as json_error:
            logger.error(" JSON serialization failed: %s", json_error)
            raise

        logger.info(" SUCCESS: Returning response to client")
        logger.info("=" * 50)

        return response_data

    except Exception as e:
        logger.error("=" * 50)
        logger.error(" ERROR in AI recommendations endpoint: %s", e)
        logger.error(" Error type: %s", type(e).__name__)
        import traceback

        logger.error(" Traceback: %s", traceback.format_exc())
        logger.error("=" * 50)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize-strategy", response_model=StrategyOptimizationResponse)
async def optimize_strategy(request: StrategyOptimizationRequest):
    """
    Optimize specific options strategy parameters using ML.

    This endpoint uses machine learning to find the optimal parameters
    for a specific options strategy.
    """
    try:
        logger.info("Optimizing %s strategy for %s", request.strategy_type, request.symbol)

        # Get options data (new engine doesn't have _get_options_data, so create mock)
        options_data = None
        try:
            import yfinance as yf
            stock = yf.Ticker(request.symbol)
            if stock.options:
                expirations = stock.options[:3]
                options_data = {}
                for exp in expirations:
                    opt_chain = stock.option_chain(exp)
                    options_data[exp] = {
                        'calls': opt_chain.calls.head(5).to_dict('records'),
                        'puts': opt_chain.puts.head(5).to_dict('records')
                    }
        except Exception as e:
            logger.warning("Could not fetch options data: %s", e)
            options_data = None

        # If no real options data, create mock data for optimization
        if not options_data:
            logger.warning("No real options data for %s, using mock data", request.symbol)
            options_data = {
                "2024-10-18": {
                    "calls": [
                        {
                            "strike": request.current_price * 1.05,
                            "bid": 2.50,
                            "ask": 2.75,
                        },
                        {
                            "strike": request.current_price * 1.10,
                            "bid": 1.25,
                            "ask": 1.50,
                        },
                        {
                            "strike": request.current_price * 1.15,
                            "bid": 0.50,
                            "ask": 0.75,
                        },
                    ],
                    "puts": [
                        {
                            "strike": request.current_price * 0.95,
                            "bid": 2.25,
                            "ask": 2.50,
                        },
                        {
                            "strike": request.current_price * 0.90,
                            "bid": 1.00,
                            "ask": 1.25,
                        },
                        {
                            "strike": request.current_price * 0.85,
                            "bid": 0.40,
                            "ask": 0.65,
                        },
                    ],
                }
            }

        # Optimize strategy parameters (via ML models)
        optimization_result = await ml_models.optimize_strategy_parameters(
            strategy_type=request.strategy_type,
            symbol=request.symbol,
            current_price=request.current_price,
            options_data=options_data,
        )

        # If optimization fails, return basic optimization
        if not optimization_result:
            logger.warning(
                "ML optimization failed for %s, using basic optimization",
                request.strategy_type,
            )
            optimization_result = {
                "optimal_strike": (
                    request.current_price * 1.05
                    if "call" in request.strategy_type.lower()
                    else request.current_price * 0.95
                ),
                "optimal_expiration": "2024-10-18",
                "optimization_score": 75.0,
                "predicted_price": request.current_price * 1.02,
                "predicted_volatility": 0.25,
                "confidence": 70.0,
            }

        # Get predictions for context
        price_prediction = await ml_models.predict_price_movement(request.symbol, request.current_price)
        volatility_prediction = await ml_models.predict_volatility(request.symbol)

        predicted_outcomes = {
            "price_prediction": price_prediction,
            "volatility_prediction": volatility_prediction,
            "optimization_confidence": optimization_result.get("optimization_score", 0),
        }

        return StrategyOptimizationResponse(
            symbol=request.symbol,
            strategy_type=request.strategy_type,
            optimal_parameters=optimization_result,
            optimization_score=optimization_result.get("optimization_score", 75.0),
            predicted_outcomes=predicted_outcomes,
            generated_at=datetime.now(),
        )

    except Exception as e:
        logger.error("Error optimizing strategy: %s", e)

        # Return a basic optimization result instead of failing
        basic_result = {
            "optimal_strike": (
                request.current_price * 1.05
                if "call" in request.strategy_type.lower()
                else request.current_price * 0.95
            ),
            "optimal_expiration": "2024-10-18",
            "optimization_score": 70.0,
            "predicted_price": request.current_price * 1.02,
            "predicted_volatility": 0.25,
            "confidence": 65.0,
            "error": str(e),
        }

        return StrategyOptimizationResponse(
            symbol=request.symbol,
            strategy_type=request.strategy_type,
            optimal_parameters=basic_result,
            optimization_score=70.0,
            predicted_outcomes=basic_result,
            generated_at=datetime.now(),
        )


@router.post("/market-analysis", response_model=MarketAnalysisResponse)
async def get_market_analysis(request: MarketAnalysisRequest):
    """
    Get comprehensive market analysis for options trading.

    This endpoint provides detailed market analysis including price predictions,
    volatility forecasts, and sentiment analysis.
    """
    try:
        logger.info("Generating market analysis for %s", request.symbol)

        # The new engine's _analyze_market requires different parameters
        # Fetch market data and build indicators
        import yfinance as yf
        
        try:
            stock = yf.Ticker(request.symbol)
            hist = stock.history(period="1mo")
            info = stock.info
            
            if not hist.empty:
                spot_price = float(hist['Close'].iloc[-1])
                iv = info.get('impliedVolatility', 0.3) or 0.3
                
                # Build basic indicators
                indicators = {
                    'rsi': 50.0,
                    'macd': 0.0,
                    'implied_volatility': iv,
                    'support': float(hist['Low'].min()),
                    'resistance': float(hist['High'].max()),
                }
                
                # Use the new engine's _analyze_market (not async)
                market_analysis = ai_engine._analyze_market(
                    symbol=request.symbol,
                    spot_price=spot_price,
                    indicators=indicators,
                    news_sentiment=None,
                )
            else:
                # Fallback to placeholder
                market_analysis = None
                spot_price = 100.0
        except Exception as e:
            logger.warning("Could not fetch market data: %s", e)
            market_analysis = None
            spot_price = 100.0

        # Get ML predictions (if available)
        try:
            price_prediction = await ml_models.predict_price_movement(
                request.symbol, spot_price
            )
            volatility_prediction = await ml_models.predict_volatility(request.symbol)
        except Exception as e:
            logger.warning("ML predictions not available: %s", e)
            price_prediction = {"price": spot_price, "confidence": 0.5}
            volatility_prediction = {"volatility": 0.25, "confidence": 0.5}

        # Build analysis dict
        if market_analysis:
            analysis = {
                "current_price": spot_price,
                "volatility": market_analysis.volatility,
                "implied_volatility": market_analysis.volatility,
                "volume": 1_000_000,  # Placeholder
                "market_cap": 1_000_000_000,  # Placeholder
                "sector": "Technology",  # Placeholder
                "sentiment_score": 0.0 if market_analysis.sentiment == "neutral" else (0.5 if market_analysis.sentiment == "bullish" else -0.5),
                "trend_direction": market_analysis.sentiment,
                "support_levels": [market_analysis.support_level] if market_analysis.support_level else [],
                "resistance_levels": [market_analysis.resistance_level] if market_analysis.resistance_level else [],
                "earnings_date": None,
                "dividend_yield": 0.0,
                "beta": 1.0,
            }
        else:
            # Fallback placeholder
            analysis = {
                "current_price": spot_price,
                "volatility": 0.2,
                "implied_volatility": 0.25,
                "volume": 1_000_000,
                "market_cap": 1_000_000_000,
                "sector": "Technology",
                "sentiment_score": 0.0,
                "trend_direction": "neutral",
                "support_levels": [],
                "resistance_levels": [],
                "earnings_date": None,
                "dividend_yield": 0.0,
                "beta": 1.0,
            }

        predictions = {
            "price_prediction": price_prediction,
            "volatility_prediction": volatility_prediction,
        }

        confidence_scores = {
            "price_prediction": price_prediction.get("confidence", 0),
            "volatility_prediction": volatility_prediction.get("confidence", 0),
            "market_analysis": 85.0,  # baseline confidence
        }

        return MarketAnalysisResponse(
            symbol=request.symbol,
            analysis=analysis,
            predictions=predictions,
            confidence_scores=confidence_scores,
            generated_at=datetime.now(),
        )

    except Exception as e:
        logger.error("Error generating market analysis: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train-models")
async def train_ml_models(symbol: str, background_tasks: BackgroundTasks):
    """
    Train ML models for a specific symbol.

    This endpoint triggers the training of price prediction and volatility
    models for the specified symbol.
    """
    try:
        logger.info("Training ML models for %s", symbol)

        background_tasks.add_task(ml_models.train_price_prediction_model, symbol)
        background_tasks.add_task(ml_models.train_volatility_prediction_model, symbol)

        return {
            "message": f"ML model training started for {symbol}",
            "status": "training",
            "symbol": symbol,
            "started_at": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error("Error starting model training: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model-status/{symbol}")
async def get_model_status(symbol: str):
    """
    Get the status of ML models for a symbol.
    """
    try:
        price_model_key = f"{symbol}_price_prediction"
        vol_model_key = f"{symbol}_volatility_prediction"

        status = {
            "symbol": symbol,
            "price_prediction_model": {
                "trained": price_model_key in ml_models.models,
                "performance": ml_models.model_performance.get(price_model_key, {}),
            },
            "volatility_prediction_model": {
                "trained": vol_model_key in ml_models.models,
                "performance": ml_models.model_performance.get(vol_model_key, {}),
            },
        }

        return status

    except Exception as e:
        logger.error("Error getting model status: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Health check for AI Options API.
    """
    return {
        "status": "healthy",
        "service": "AI Options API",
        "timestamp": datetime.now().isoformat(),
        "models_loaded": len(ml_models.models),
        "scalers_loaded": len(ml_models.scalers),
    }


__all__ = ["router"]
