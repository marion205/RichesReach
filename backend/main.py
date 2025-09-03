#!/usr/bin/env python3
"""
RichesReach AI Service - Production Main Application
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import logging
from datetime import datetime
import asyncio

# Import our AI services
try:
    from core.optimized_ml_service import OptimizedMLService
    from core.market_data_service import MarketDataService
    from core.advanced_market_data_service import AdvancedMarketDataService
    from core.advanced_ml_algorithms import AdvancedMLAlgorithms
    from core.performance_monitoring_service import ProductionMonitoringService
    ML_SERVICES_AVAILABLE = True
except ImportError:
    ML_SERVICES_AVAILABLE = False
    logging.warning("ML services not available - running in basic mode")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="RichesReach AI Service",
    description="Production AI-powered investment portfolio analysis and market intelligence",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
if ML_SERVICES_AVAILABLE:
    try:
        ml_service = OptimizedMLService()
        market_data_service = AdvancedMarketDataService()
        advanced_ml = AdvancedMLAlgorithms()
        monitoring_service = ProductionMonitoringService()
        logger.info("All ML services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize ML services: {e}")
        ML_SERVICES_AVAILABLE = False

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "RichesReach AI Service",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "ml_services": ML_SERVICES_AVAILABLE
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "ml_services": ML_SERVICES_AVAILABLE,
            "market_data": ML_SERVICES_AVAILABLE,
            "monitoring": ML_SERVICES_AVAILABLE
        }
    }
    
    if ML_SERVICES_AVAILABLE:
        try:
            # Test ML service health
            ml_health = ml_service.check_health()
            health_status["services"]["ml_health"] = ml_health
            
            # Test market data service
            market_health = market_data_service.check_health()
            health_status["services"]["market_health"] = market_health
            
        except Exception as e:
            health_status["status"] = "degraded"
            health_status["error"] = str(e)
    
    return health_status

@app.post("/api/portfolio/analyze")
async def analyze_portfolio(background_tasks: BackgroundTasks):
    """Analyze investment portfolio using AI"""
    if not ML_SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="ML services not available")
    
    try:
        # Record metric
        if 'monitoring_service' in locals():
            monitoring_service.record_metric(
                "portfolio_analysis_requests", 1, "count"
            )
        
        # Run portfolio analysis in background
        background_tasks.add_task(run_portfolio_analysis)
        
        return {
            "message": "Portfolio analysis started",
            "status": "processing",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Portfolio analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/market/regime")
async def predict_market_regime(background_tasks: BackgroundTasks):
    """Predict current market regime using AI"""
    if not ML_SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="ML services not available")
    
    try:
        # Record metric
        if 'monitoring_service' in locals():
            monitoring_service.record_metric(
                "market_regime_requests", 1, "count"
            )
        
        # Run market regime prediction in background
        background_tasks.add_task(run_market_regime_prediction)
        
        return {
            "message": "Market regime prediction started",
            "status": "processing",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Market regime prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def get_service_status():
    """Get comprehensive service status"""
    status = {
        "service": "RichesReach AI",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "production"),
        "ml_services": ML_SERVICES_AVAILABLE
    }
    
    if ML_SERVICES_AVAILABLE:
        try:
            # Get ML model status
            ml_status = ml_service.get_status()
            status["ml_status"] = ml_status
            
            # Get market data status
            market_status = market_data_service.get_status()
            status["market_status"] = market_status
            
        except Exception as e:
            status["error"] = str(e)
    
    return status

async def run_portfolio_analysis():
    """Background task for portfolio analysis"""
    try:
        logger.info("Running portfolio analysis...")
        # This would call your actual portfolio analysis logic
        await asyncio.sleep(5)  # Simulate processing
        logger.info("Portfolio analysis completed")
        
    except Exception as e:
        logger.error(f"Portfolio analysis background task error: {e}")

async def run_market_regime_prediction():
    """Background task for market regime prediction"""
    try:
        logger.info("Running market regime prediction...")
        # This would call your actual market regime logic
        await asyncio.sleep(3)  # Simulate processing
        logger.info("Market regime prediction completed")
        
    except Exception as e:
        logger.error(f"Market regime prediction background task error: {e}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
