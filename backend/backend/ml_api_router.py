"""
FastAPI Router for ML Learning System
Provides REST endpoints for ML status, outcome logging, and training
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from ml_learning_system import ml_system

logger = logging.getLogger(__name__)

# Create router
ml_router = APIRouter(prefix="/ml", tags=["ml"])

# ==== PYDANTIC MODELS ====
class TradingOutcomeRequest(BaseModel):
    symbol: str
    side: str  # LONG | SHORT
    entry_price: float
    exit_price: float
    entry_time: str  # ISO8601
    exit_time: str   # ISO8601
    mode: str        # SAFE | AGGRESSIVE
    outcome: str     # +1R | -1R | time_stop | ...
    features: Dict[str, float]
    score: float
    timestamp: Optional[str] = None  # defaults to now

class TrainingRequest(BaseModel):
    modes: Optional[list] = None  # defaults to ["SAFE", "AGGRESSIVE"]
    force: bool = False  # force training even if not needed

class BanditUpdateRequest(BaseModel):
    strategy: str
    reward: float

class ContextRequest(BaseModel):
    vix_level: float = 20.0
    market_trend: float = 0.1
    volatility_regime: float = 0.5
    time_of_day: float = 0.4

# ==== ENDPOINTS ====
@ml_router.get("/status")
async def get_ml_status():
    """Get ML system status and metrics"""
    try:
        status = ml_system.status()
        return {"success": True, "data": status}
    except Exception as e:
        logger.exception("Error getting ML status")
        raise HTTPException(status_code=500, detail=str(e))

@ml_router.post("/outcome")
async def log_trading_outcome(outcome: TradingOutcomeRequest):
    """Log a trading outcome for ML learning"""
    try:
        # Set timestamp if not provided
        if outcome.timestamp is None:
            outcome.timestamp = datetime.utcnow().isoformat()
        
        # Convert to dict for the ML system
        outcome_dict = outcome.dict()
        
        success = ml_system.log_trading_outcome(outcome_dict)
        
        if success:
            return {
                "success": True, 
                "message": "Outcome logged successfully",
                "outcome": outcome_dict
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to log outcome")
            
    except Exception as e:
        logger.exception("Error logging trading outcome")
        raise HTTPException(status_code=500, detail=str(e))

@ml_router.post("/train")
async def train_models(request: TrainingRequest):
    """Train ML models for specified modes"""
    try:
        modes = request.modes or ["SAFE", "AGGRESSIVE"]
        
        if request.force:
            # Force training by temporarily clearing last_train
            for mode in modes:
                ml_system.last_train[mode] = None
        
        results = ml_system.train_if_needed()
        
        # Filter to requested modes
        filtered_results = {mode: results.get(mode) for mode in modes}
        
        return {
            "success": True,
            "message": "Training completed",
            "results": filtered_results
        }
        
    except Exception as e:
        logger.exception("Error training models")
        raise HTTPException(status_code=500, detail=str(e))

@ml_router.post("/bandit/select")
async def select_bandit_strategy(context: ContextRequest):
    """Select strategy using contextual bandit"""
    try:
        context_dict = context.dict()
        strategy = ml_system.bandit.select(context_dict)
        
        return {
            "success": True,
            "selected_strategy": strategy,
            "context": context_dict
        }
        
    except Exception as e:
        logger.exception("Error selecting bandit strategy")
        raise HTTPException(status_code=500, detail=str(e))

@ml_router.post("/bandit/update")
async def update_bandit_reward(request: BanditUpdateRequest):
    """Update bandit with reward for strategy"""
    try:
        ml_system.bandit.update(request.strategy, request.reward)
        
        return {
            "success": True,
            "message": f"Updated {request.strategy} with reward {request.reward}",
            "bandit_state": ml_system.bandit.snapshot()
        }
        
    except Exception as e:
        logger.exception("Error updating bandit reward")
        raise HTTPException(status_code=500, detail=str(e))

@ml_router.get("/bandit/state")
async def get_bandit_state():
    """Get current bandit state"""
    try:
        state = ml_system.bandit.snapshot()
        return {"success": True, "bandit_state": state}
        
    except Exception as e:
        logger.exception("Error getting bandit state")
        raise HTTPException(status_code=500, detail=str(e))

@ml_router.get("/models/{mode}")
async def get_best_model(mode: str):
    """Get best model ID for a mode"""
    try:
        if mode.upper() not in ["SAFE", "AGGRESSIVE"]:
            raise HTTPException(status_code=400, detail="Mode must be SAFE or AGGRESSIVE")
        
        model_id = ml_system.best_model_id(mode.upper())
        
        return {
            "success": True,
            "mode": mode.upper(),
            "model_id": model_id,
            "has_model": model_id is not None
        }
        
    except Exception as e:
        logger.exception("Error getting best model")
        raise HTTPException(status_code=500, detail=str(e))

@ml_router.post("/drift/detect")
async def detect_drift(features: Dict[str, Any]):
    """Detect feature drift using PSI"""
    try:
        # Convert features to numpy array
        import numpy as np
        feature_values = np.array(list(features.values())).reshape(1, -1)
        
        drift_result = ml_system.drift.detect(feature_values)
        
        return {
            "success": True,
            "drift_detected": drift_result["drift_detected"],
            "max_psi": drift_result["max_psi"],
            "psi_scores": drift_result["psi_scores"]
        }
        
    except Exception as e:
        logger.exception("Error detecting drift")
        raise HTTPException(status_code=500, detail=str(e))

@ml_router.post("/drift/update-reference")
async def update_drift_reference(features: Dict[str, Any]):
    """Update drift detection reference data"""
    try:
        import numpy as np
        feature_values = np.array(list(features.values())).reshape(1, -1)
        
        ml_system.drift.update_reference(feature_values)
        
        return {
            "success": True,
            "message": "Reference data updated for drift detection"
        }
        
    except Exception as e:
        logger.exception("Error updating drift reference")
        raise HTTPException(status_code=500, detail=str(e))
