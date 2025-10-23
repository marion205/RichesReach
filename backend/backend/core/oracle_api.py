"""
Oracle API - RESTful endpoints for the Predictive Wealth Oracle
==============================================================

Provides API endpoints for accessing oracle insights, events, and recommendations.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from pydantic import BaseModel, Field, validator

from .predictive_wealth_oracle import (
    oracle_service,
    OracleEvent,
    OracleEventType,
    OraclePriority,
    OracleConfidence
)

logger = logging.getLogger(__name__)

# =============================================================================
# Request/Response Models
# =============================================================================

class OracleEventResponse(BaseModel):
    """Response model for oracle events."""
    id: str
    event_type: str
    priority: str
    confidence: str
    title: str
    description: str
    recommendation: str
    expected_impact: str
    time_sensitivity: str
    created_at: str
    expires_at: Optional[str] = None
    acknowledged: bool = False
    acted_upon: bool = False

class OracleInsightRequest(BaseModel):
    """Request model for generating AI insights."""
    insight_type: str = Field(..., description="Type of insight to generate")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")

class OracleInsightResponse(BaseModel):
    """Response model for AI insights."""
    insight: OracleEventResponse
    confidence: float
    reasoning: str

class OracleStatusResponse(BaseModel):
    """Response model for oracle status."""
    is_active: bool
    active_events_count: int
    last_updated: str
    market_context: Optional[Dict[str, Any]] = None

# =============================================================================
# API Views
# =============================================================================

@csrf_exempt
@require_http_methods(["GET"])
def get_oracle_events(request):
    """Get oracle events for the current user."""
    try:
        user_id = request.user.id if request.user.is_authenticated else None
        if not user_id:
            return JsonResponse({"error": "Authentication required"}, status=401)
        
        limit = int(request.GET.get('limit', 10))
        event_type = request.GET.get('type')
        priority = request.GET.get('priority')
        
        # Get events from oracle service
        events = await oracle_service.get_user_oracle_events(user_id, limit)
        
        # Filter by type and priority if specified
        if event_type:
            events = [e for e in events if e.event_type.value == event_type]
        
        if priority:
            events = [e for e in events if e.priority.value == priority]
        
        # Convert to response format
        response_events = []
        for event in events:
            response_events.append(OracleEventResponse(
                id=event.id,
                event_type=event.event_type.value,
                priority=event.priority.value,
                confidence=event.confidence.value,
                title=event.title,
                description=event.description,
                recommendation=event.recommendation,
                expected_impact=event.expected_impact,
                time_sensitivity=event.time_sensitivity,
                created_at=event.created_at.isoformat(),
                expires_at=event.expires_at.isoformat() if event.expires_at else None,
                acknowledged=event.acknowledged,
                acted_upon=event.acted_upon
            ))
        
        return JsonResponse({
            "success": True,
            "events": [event.dict() for event in response_events],
            "count": len(response_events)
        })
        
    except Exception as e:
        logger.error(f"Error getting oracle events: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def acknowledge_oracle_event(request):
    """Acknowledge an oracle event."""
    try:
        user_id = request.user.id if request.user.is_authenticated else None
        if not user_id:
            return JsonResponse({"error": "Authentication required"}, status=401)
        
        data = json.loads(request.body)
        event_id = data.get('event_id')
        
        if not event_id:
            return JsonResponse({"error": "event_id is required"}, status=400)
        
        # Acknowledge the event
        await oracle_service.acknowledge_oracle_event(event_id, user_id)
        
        return JsonResponse({
            "success": True,
            "message": "Event acknowledged successfully"
        })
        
    except Exception as e:
        logger.error(f"Error acknowledging oracle event: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def generate_ai_insight(request):
    """Generate AI-powered insight for the user."""
    try:
        user_id = request.user.id if request.user.is_authenticated else None
        if not user_id:
            return JsonResponse({"error": "Authentication required"}, status=401)
        
        data = json.loads(request.body)
        insight_request = OracleInsightRequest(**data)
        
        # Generate insight
        insight_event = await oracle_service.generate_ai_insight(
            user_id, 
            insight_request.insight_type
        )
        
        if not insight_event:
            return JsonResponse({
                "success": False,
                "message": "Unable to generate insight at this time"
            }, status=400)
        
        # Convert to response format
        response_insight = OracleEventResponse(
            id=insight_event.id,
            event_type=insight_event.event_type.value,
            priority=insight_event.priority.value,
            confidence=insight_event.confidence.value,
            title=insight_event.title,
            description=insight_event.description,
            recommendation=insight_event.recommendation,
            expected_impact=insight_event.expected_impact,
            time_sensitivity=insight_event.time_sensitivity,
            created_at=insight_event.created_at.isoformat(),
            expires_at=insight_event.expires_at.isoformat() if insight_event.expires_at else None,
            acknowledged=insight_event.acknowledged,
            acted_upon=insight_event.acted_upon
        )
        
        return JsonResponse({
            "success": True,
            "insight": response_insight.dict(),
            "confidence": 0.8,  # This would come from the AI model
            "reasoning": "Generated based on your portfolio, behavior, and market conditions"
        })
        
    except Exception as e:
        logger.error(f"Error generating AI insight: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_proactive_recommendations(request):
    """Get proactive portfolio recommendations."""
    try:
        user_id = request.user.id if request.user.is_authenticated else None
        if not user_id:
            return JsonResponse({"error": "Authentication required"}, status=401)
        
        # Get proactive recommendations
        recommendations = await oracle_service.get_proactive_portfolio_recommendations(user_id)
        
        # Convert to response format
        response_recommendations = []
        for rec in recommendations:
            response_recommendations.append(OracleEventResponse(
                id=rec.id,
                event_type=rec.event_type.value,
                priority=rec.priority.value,
                confidence=rec.confidence.value,
                title=rec.title,
                description=rec.description,
                recommendation=rec.recommendation,
                expected_impact=rec.expected_impact,
                time_sensitivity=rec.time_sensitivity,
                created_at=rec.created_at.isoformat(),
                expires_at=rec.expires_at.isoformat() if rec.expires_at else None,
                acknowledged=rec.acknowledged,
                acted_upon=rec.acted_upon
            ))
        
        return JsonResponse({
            "success": True,
            "recommendations": [rec.dict() for rec in response_recommendations],
            "count": len(response_recommendations)
        })
        
    except Exception as e:
        logger.error(f"Error getting proactive recommendations: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_oracle_status(request):
    """Get oracle system status."""
    try:
        # Get oracle status
        status = {
            "is_active": True,
            "active_events_count": len(oracle_service.active_events),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "market_context": None
        }
        
        # Add market context if available
        if oracle_service.market_context:
            status["market_context"] = {
                "regime": oracle_service.market_context.regime,
                "volatility": oracle_service.market_context.volatility,
                "trend": oracle_service.market_context.trend,
                "sentiment": oracle_service.market_context.sentiment,
                "timestamp": oracle_service.market_context.timestamp.isoformat()
            }
        
        return JsonResponse({
            "success": True,
            "status": status
        })
        
    except Exception as e:
        logger.error(f"Error getting oracle status: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_oracle_insights_summary(request):
    """Get summary of oracle insights for dashboard."""
    try:
        user_id = request.user.id if request.user.is_authenticated else None
        if not user_id:
            return JsonResponse({"error": "Authentication required"}, status=401)
        
        # Get recent events
        events = await oracle_service.get_user_oracle_events(user_id, 5)
        
        # Categorize events
        summary = {
            "total_events": len(events),
            "critical_events": len([e for e in events if e.priority == OraclePriority.CRITICAL]),
            "high_priority_events": len([e for e in events if e.priority == OraclePriority.HIGH]),
            "unacknowledged_events": len([e for e in events if not e.acknowledged]),
            "recent_insights": [],
            "market_alerts": [],
            "portfolio_recommendations": []
        }
        
        # Categorize recent events
        for event in events:
            event_summary = {
                "id": event.id,
                "title": event.title,
                "priority": event.priority.value,
                "created_at": event.created_at.isoformat()
            }
            
            if event.event_type == OracleEventType.MARKET_REGIME_CHANGE:
                summary["market_alerts"].append(event_summary)
            elif event.event_type == OracleEventType.PORTFOLIO_OPTIMIZATION:
                summary["portfolio_recommendations"].append(event_summary)
            else:
                summary["recent_insights"].append(event_summary)
        
        return JsonResponse({
            "success": True,
            "summary": summary
        })
        
    except Exception as e:
        logger.error(f"Error getting oracle insights summary: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)

# =============================================================================
# WebSocket Events (for real-time updates)
# =============================================================================

@csrf_exempt
@require_http_methods(["GET"])
def get_oracle_websocket_url(request):
    """Get WebSocket URL for real-time oracle updates."""
    try:
        user_id = request.user.id if request.user.is_authenticated else None
        if not user_id:
            return JsonResponse({"error": "Authentication required"}, status=401)
        
        # Generate WebSocket URL with user token
        ws_url = f"wss://app.richesreach.net/ws/oracle/{user_id}/"
        
        return JsonResponse({
            "success": True,
            "websocket_url": ws_url,
            "message": "Connect to this URL for real-time oracle updates"
        })
        
    except Exception as e:
        logger.error(f"Error getting WebSocket URL: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)

# =============================================================================
# Admin Endpoints
# =============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def trigger_oracle_analysis(request):
    """Trigger manual oracle analysis (admin only)."""
    try:
        # Check if user is admin
        if not request.user.is_authenticated or not request.user.is_staff:
            return JsonResponse({"error": "Admin access required"}, status=403)
        
        data = json.loads(request.body)
        analysis_type = data.get('analysis_type', 'full')
        user_id = data.get('user_id')
        
        if analysis_type == 'full':
            # Trigger full oracle analysis
            await oracle_service._market_monitoring_loop()
            await oracle_service._opportunity_detection_loop()
            
            if user_id:
                await oracle_service._analyze_user_behavior(user_id)
        
        return JsonResponse({
            "success": True,
            "message": f"Oracle analysis triggered: {analysis_type}"
        })
        
    except Exception as e:
        logger.error(f"Error triggering oracle analysis: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_oracle_metrics(request):
    """Get oracle system metrics (admin only)."""
    try:
        # Check if user is admin
        if not request.user.is_authenticated or not request.user.is_staff:
            return JsonResponse({"error": "Admin access required"}, status=403)
        
        metrics = {
            "active_events": len(oracle_service.active_events),
            "user_profiles": len(oracle_service.user_profiles),
            "market_context_available": oracle_service.market_context is not None,
            "models_loaded": {
                "portfolio_optimizer": oracle_service.portfolio_optimizer is not None,
                "risk_predictor": oracle_service.risk_predictor is not None,
                "opportunity_detector": oracle_service.opportunity_detector is not None
            },
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        
        return JsonResponse({
            "success": True,
            "metrics": metrics
        })
        
    except Exception as e:
        logger.error(f"Error getting oracle metrics: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)
