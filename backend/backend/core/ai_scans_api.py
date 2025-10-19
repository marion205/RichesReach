"""
AI Scans API
FastAPI endpoints for AI-powered market scanning and playbooks
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import asyncio
import logging

from .ai_scans_engine import AIScansEngine
from .real_data_service import get_real_data_service
from .monitoring import logger

router = APIRouter(prefix="/api/ai-scans", tags=["AI Scans"])

# Initialize AI Scans Engine
ai_scans_engine = AIScansEngine(get_real_data_service())

# Pydantic Models
class AIScanFilters(BaseModel):
    category: Optional[str] = None
    risk_level: Optional[str] = None
    time_horizon: Optional[str] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None

class CreateScanRequest(BaseModel):
    name: str
    description: str
    category: str
    parameters: Dict[str, Any]
    playbook_id: Optional[str] = None

class RunScanRequest(BaseModel):
    scan_id: str
    parameters: Optional[Dict[str, Any]] = None

class ClonePlaybookRequest(BaseModel):
    playbook_id: str
    name: str
    description: str
    parameters: Optional[Dict[str, Any]] = None

class ScanResult(BaseModel):
    id: str
    symbol: str
    name: str
    current_price: float
    change: float
    change_percent: float
    volume: int
    market_cap: float
    score: float
    confidence: float
    reasoning: str
    risk_factors: List[str]
    opportunity_factors: List[str]
    technical_signals: List[Dict[str, Any]]
    fundamental_metrics: List[Dict[str, Any]]
    alt_data_signals: List[Dict[str, Any]]

class AIScanResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    risk_level: str
    time_horizon: str
    is_active: bool
    last_run: Optional[str] = None
    results: Optional[List[ScanResult]] = None
    parameters: Dict[str, Any]
    playbook: Optional[Dict[str, Any]] = None

class PlaybookResponse(BaseModel):
    id: str
    name: str
    description: str
    author: str
    category: str
    risk_level: str
    is_public: bool
    is_clonable: bool
    parameters: Dict[str, Any]
    explanation: Dict[str, Any]
    performance: Dict[str, Any]
    tags: List[str]

@router.get("/", response_model=List[AIScanResponse])
async def get_scans(
    category: Optional[str] = Query(None, description="Filter by category"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    time_horizon: Optional[str] = Query(None, description="Filter by time horizon"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    user_id: str = Query(..., description="User ID")
):
    """Get all AI scans for a user with optional filters"""
    try:
        filters = AIScanFilters(
            category=category,
            risk_level=risk_level,
            time_horizon=time_horizon,
            is_active=is_active,
            tags=tags.split(',') if tags else None
        )
        
        scans = await ai_scans_engine.get_user_scans(user_id, filters)
        logger.info(f"Retrieved {len(scans)} scans for user {user_id}")
        return scans
        
    except Exception as e:
        logger.error(f"Error getting scans: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{scan_id}", response_model=AIScanResponse)
async def get_scan(scan_id: str, user_id: str = Query(..., description="User ID")):
    """Get a specific scan by ID"""
    try:
        scan = await ai_scans_engine.get_scan(scan_id, user_id)
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        logger.info(f"Retrieved scan {scan_id} for user {user_id}")
        return scan
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting scan {scan_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=AIScanResponse)
async def create_scan(request: CreateScanRequest, user_id: str = Query(..., description="User ID")):
    """Create a new AI scan"""
    try:
        scan = await ai_scans_engine.create_scan(user_id, request)
        logger.info(f"Created scan {scan.id} for user {user_id}")
        return scan
        
    except Exception as e:
        logger.error(f"Error creating scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{scan_id}/run", response_model=List[ScanResult])
async def run_scan(scan_id: str, request: RunScanRequest, user_id: str = Query(..., description="User ID")):
    """Run a scan and get results"""
    try:
        results = await ai_scans_engine.run_scan(scan_id, user_id, request.parameters)
        logger.info(f"Ran scan {scan_id} for user {user_id}, found {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"Error running scan {scan_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{scan_id}", response_model=AIScanResponse)
async def update_scan(
    scan_id: str, 
    updates: Dict[str, Any], 
    user_id: str = Query(..., description="User ID")
):
    """Update a scan"""
    try:
        scan = await ai_scans_engine.update_scan(scan_id, user_id, updates)
        logger.info(f"Updated scan {scan_id} for user {user_id}")
        return scan
        
    except Exception as e:
        logger.error(f"Error updating scan {scan_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{scan_id}")
async def delete_scan(scan_id: str, user_id: str = Query(..., description="User ID")):
    """Delete a scan"""
    try:
        await ai_scans_engine.delete_scan(scan_id, user_id)
        logger.info(f"Deleted scan {scan_id} for user {user_id}")
        return {"message": "Scan deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting scan {scan_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{scan_id}/history", response_model=List[List[ScanResult]])
async def get_scan_history(
    scan_id: str, 
    limit: int = Query(10, description="Number of historical runs to return"),
    user_id: str = Query(..., description="User ID")
):
    """Get scan results history"""
    try:
        history = await ai_scans_engine.get_scan_history(scan_id, user_id, limit)
        logger.info(f"Retrieved {len(history)} historical runs for scan {scan_id}")
        return history
        
    except Exception as e:
        logger.error(f"Error getting scan history for {scan_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Playbook endpoints
@router.get("/playbooks/", response_model=List[PlaybookResponse])
async def get_playbooks(
    category: Optional[str] = Query(None, description="Filter by category"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    is_public: Optional[bool] = Query(True, description="Filter by public status")
):
    """Get all available playbooks"""
    try:
        playbooks = await ai_scans_engine.get_playbooks(category, risk_level, is_public)
        logger.info(f"Retrieved {len(playbooks)} playbooks")
        return playbooks
        
    except Exception as e:
        logger.error(f"Error getting playbooks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/playbooks/{playbook_id}", response_model=PlaybookResponse)
async def get_playbook(playbook_id: str):
    """Get a specific playbook by ID"""
    try:
        playbook = await ai_scans_engine.get_playbook(playbook_id)
        if not playbook:
            raise HTTPException(status_code=404, detail="Playbook not found")
        
        logger.info(f"Retrieved playbook {playbook_id}")
        return playbook
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting playbook {playbook_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/playbooks/{playbook_id}/clone", response_model=AIScanResponse)
async def clone_playbook(
    playbook_id: str, 
    request: ClonePlaybookRequest, 
    user_id: str = Query(..., description="User ID")
):
    """Clone a playbook to create a new scan"""
    try:
        scan = await ai_scans_engine.clone_playbook(playbook_id, user_id, request)
        logger.info(f"Cloned playbook {playbook_id} to scan {scan.id} for user {user_id}")
        return scan
        
    except Exception as e:
        logger.error(f"Error cloning playbook {playbook_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for AI Scans service"""
    try:
        status = await ai_scans_engine.get_health_status()
        return {
            "status": "healthy",
            "service": "ai_scans",
            "details": status
        }
    except Exception as e:
        logger.error(f"AI Scans health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")
