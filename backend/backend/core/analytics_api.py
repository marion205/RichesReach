"""
Advanced Analytics API - Phase 3
FastAPI endpoints for real-time analytics, business intelligence, and predictive analytics
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import uuid
import logging
from datetime import datetime, timedelta
import json

from .analytics_engine import (
    analytics_engine, predictive_analytics, 
    Metric, AnalyticsEvent, MarketData, UserBehavior,
    AnalyticsType, MetricType
)

logger = logging.getLogger("richesreach")

# Create router
router = APIRouter(prefix="/analytics", tags=["Advanced Analytics"])

# Pydantic models for API
class MetricModel(BaseModel):
    """Metric model for API"""
    name: str = Field(..., description="Metric name")
    value: float = Field(..., description="Metric value")
    labels: Dict[str, str] = Field(default_factory=dict, description="Metric labels")
    metric_type: str = Field("gauge", description="Metric type")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class EventModel(BaseModel):
    """Event model for API"""
    event_type: str = Field(..., description="Event type")
    user_id: Optional[str] = Field(None, description="User ID")
    session_id: Optional[str] = Field(None, description="Session ID")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Event properties")
    context: Dict[str, Any] = Field(default_factory=dict, description="Event context")

class MarketDataModel(BaseModel):
    """Market data model for API"""
    symbol: str = Field(..., description="Symbol")
    price: float = Field(..., description="Price")
    volume: int = Field(..., description="Volume")
    change: float = Field(..., description="Price change")
    change_percent: float = Field(..., description="Price change percentage")
    high: float = Field(..., description="High price")
    low: float = Field(..., description="Low price")
    open_price: float = Field(..., description="Open price")
    close_price: float = Field(..., description="Close price")

class UserBehaviorModel(BaseModel):
    """User behavior model for API"""
    user_id: str = Field(..., description="User ID")
    session_id: str = Field(..., description="Session ID")
    event_type: str = Field(..., description="Event type")
    page: str = Field(..., description="Page")
    action: str = Field(..., description="Action")
    duration: float = Field(..., description="Duration in seconds")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties")

class PredictionRequestModel(BaseModel):
    """Prediction request model"""
    symbol: str = Field(..., description="Symbol to predict")
    horizon_hours: int = Field(24, ge=1, le=168, description="Prediction horizon in hours")

class AnomalyDetectionRequestModel(BaseModel):
    """Anomaly detection request model"""
    symbol: str = Field(..., description="Symbol to analyze")
    threshold: float = Field(0.1, ge=0.01, le=0.5, description="Anomaly threshold")

class UserClusteringRequestModel(BaseModel):
    """User clustering request model"""
    n_clusters: int = Field(5, ge=2, le=20, description="Number of clusters")

# Real-time Analytics Endpoints
@router.post("/metrics")
async def record_metric(metric: MetricModel):
    """Record a metric"""
    try:
        metric_obj = Metric(
            name=metric.name,
            value=metric.value,
            timestamp=datetime.now(),
            labels=metric.labels,
            metric_type=MetricType(metric.metric_type),
            metadata=metric.metadata
        )
        
        await analytics_engine.record_metric(metric_obj)
        
        return {
            "status": "success",
            "message": "Metric recorded successfully",
            "metric_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error recording metric: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/events")
async def record_event(event: EventModel):
    """Record an analytics event"""
    try:
        event_obj = AnalyticsEvent(
            event_id=str(uuid.uuid4()),
            event_type=event.event_type,
            user_id=event.user_id,
            session_id=event.session_id,
            timestamp=datetime.now(),
            properties=event.properties,
            context=event.context
        )
        
        await analytics_engine.record_event(event_obj)
        
        return {
            "status": "success",
            "message": "Event recorded successfully",
            "event_id": event_obj.event_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error recording event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/market-data")
async def record_market_data(market_data: MarketDataModel):
    """Record market data"""
    try:
        market_data_obj = MarketData(
            symbol=market_data.symbol,
            price=market_data.price,
            volume=market_data.volume,
            timestamp=datetime.now(),
            change=market_data.change,
            change_percent=market_data.change_percent,
            high=market_data.high,
            low=market_data.low,
            open_price=market_data.open_price,
            close_price=market_data.close_price
        )
        
        await analytics_engine.record_market_data(market_data_obj)
        
        return {
            "status": "success",
            "message": "Market data recorded successfully",
            "symbol": market_data.symbol,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error recording market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/user-behavior")
async def record_user_behavior(behavior: UserBehaviorModel):
    """Record user behavior"""
    try:
        behavior_obj = UserBehavior(
            user_id=behavior.user_id,
            session_id=behavior.session_id,
            event_type=behavior.event_type,
            timestamp=datetime.now(),
            page=behavior.page,
            action=behavior.action,
            duration=behavior.duration,
            properties=behavior.properties
        )
        
        await analytics_engine.record_user_behavior(behavior_obj)
        
        return {
            "status": "success",
            "message": "User behavior recorded successfully",
            "user_id": behavior.user_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error recording user behavior: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Dashboard Endpoints
@router.get("/dashboards/{dashboard_type}")
async def get_dashboard(dashboard_type: str):
    """Get dashboard data"""
    try:
        if dashboard_type not in ["business_intelligence", "market_analytics", "user_analytics", "performance"]:
            raise HTTPException(status_code=400, detail="Invalid dashboard type")
        
        dashboard_data = await analytics_engine.get_dashboard_data(dashboard_type)
        
        return {
            "status": "success",
            "dashboard_type": dashboard_type,
            "data": dashboard_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard {dashboard_type}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboards")
async def list_dashboards():
    """List available dashboards"""
    try:
        dashboards = list(analytics_engine.dashboards.keys())
        
        return {
            "status": "success",
            "dashboards": dashboards,
            "count": len(dashboards),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error listing dashboards: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Real-time Metrics Endpoints
@router.get("/metrics/realtime")
async def get_real_time_metrics(
    metrics: List[str] = Query(..., description="List of metric names to retrieve")
):
    """Get real-time metrics"""
    try:
        metrics_data = await analytics_engine.get_real_time_metrics(metrics)
        
        return {
            "status": "success",
            "metrics": metrics_data,
            "count": len(metrics_data),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting real-time metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/summary")
async def get_metrics_summary():
    """Get metrics summary"""
    try:
        summary = await analytics_engine.get_analytics_summary()
        
        return {
            "status": "success",
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Predictive Analytics Endpoints
@router.post("/predictions/price")
async def predict_price(request: PredictionRequestModel):
    """Predict price for a symbol"""
    try:
        prediction = await predictive_analytics.predict_price(
            request.symbol, 
            request.horizon_hours
        )
        
        return {
            "status": "success",
            "prediction": prediction,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error predicting price for {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predictions/anomalies")
async def detect_anomalies(request: AnomalyDetectionRequestModel):
    """Detect anomalies in market data"""
    try:
        anomalies = await predictive_analytics.detect_anomalies(
            request.symbol,
            request.threshold
        )
        
        return {
            "status": "success",
            "anomalies": anomalies,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error detecting anomalies for {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predictions/user-clusters")
async def cluster_users(request: UserClusteringRequestModel):
    """Cluster users based on behavior"""
    try:
        clusters = await predictive_analytics.cluster_users(request.n_clusters)
        
        return {
            "status": "success",
            "clusters": clusters,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error clustering users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Business Intelligence Endpoints
@router.get("/bi/revenue")
async def get_revenue_analytics(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get revenue analytics"""
    try:
        # Default to last 30 days if no dates provided
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Get revenue metrics from dashboard
        bi_data = await analytics_engine.get_dashboard_data("business_intelligence")
        revenue_metrics = bi_data.get("revenue_metrics", {})
        
        return {
            "status": "success",
            "revenue_analytics": revenue_metrics,
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting revenue analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bi/users")
async def get_user_analytics(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get user analytics"""
    try:
        # Default to last 30 days if no dates provided
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Get user metrics from dashboard
        bi_data = await analytics_engine.get_dashboard_data("business_intelligence")
        user_metrics = bi_data.get("user_metrics", {})
        
        return {
            "status": "success",
            "user_analytics": user_metrics,
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting user analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Market Analytics Endpoints
@router.get("/market/overview")
async def get_market_overview():
    """Get market overview"""
    try:
        market_data = await analytics_engine.get_dashboard_data("market_analytics")
        market_overview = market_data.get("market_overview", {})
        
        return {
            "status": "success",
            "market_overview": market_overview,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting market overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market/trends")
async def get_market_trends(
    symbol: Optional[str] = Query(None, description="Symbol to analyze"),
    timeframe: str = Query("1d", description="Timeframe (1h, 1d, 1w, 1m)")
):
    """Get market trends"""
    try:
        market_data = await analytics_engine.get_dashboard_data("market_analytics")
        stock_analytics = market_data.get("stock_analytics", {})
        
        if symbol:
            # Filter for specific symbol
            trends = {
                "symbol": symbol,
                "trend_data": stock_analytics.get(symbol, {})
            }
        else:
            # Return general trends
            trends = {
                "top_gainers": stock_analytics.get("top_gainers", []),
                "top_losers": stock_analytics.get("top_losers", []),
                "most_active": stock_analytics.get("most_active", [])
            }
        
        return {
            "status": "success",
            "market_trends": trends,
            "timeframe": timeframe,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting market trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Performance Analytics Endpoints
@router.get("/performance/system")
async def get_system_performance():
    """Get system performance metrics"""
    try:
        performance_data = await analytics_engine.get_dashboard_data("performance")
        system_metrics = performance_data.get("system_metrics", {})
        
        return {
            "status": "success",
            "system_performance": system_metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting system performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance/api")
async def get_api_performance():
    """Get API performance metrics"""
    try:
        performance_data = await analytics_engine.get_dashboard_data("performance")
        api_metrics = performance_data.get("api_metrics", {})
        
        return {
            "status": "success",
            "api_performance": api_metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting API performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health Check
@router.get("/health")
async def analytics_health():
    """Health check for analytics system"""
    try:
        summary = await analytics_engine.get_analytics_summary()
        
        return {
            "status": "healthy",
            "analytics_summary": summary,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Analytics health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
