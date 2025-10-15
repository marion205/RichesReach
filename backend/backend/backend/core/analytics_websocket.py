"""
Real-time Analytics WebSocket - Phase 3
WebSocket endpoints for real-time analytics streaming
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Set
from fastapi import WebSocket, WebSocketDisconnect
import websockets

from .analytics_engine import analytics_engine, predictive_analytics

logger = logging.getLogger("richesreach")

class AnalyticsWebSocketManager:
    """Manages WebSocket connections for real-time analytics"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "dashboard": set(),
            "metrics": set(),
            "predictions": set(),
            "alerts": set()
        }
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        
        # Start background tasks
        asyncio.create_task(self._broadcast_dashboard_updates())
        asyncio.create_task(self._broadcast_metrics_updates())
        asyncio.create_task(self._broadcast_predictions_updates())
        asyncio.create_task(self._broadcast_alerts())
    
    async def connect(self, websocket: WebSocket, connection_type: str, metadata: Dict[str, Any] = None):
        """Connect a WebSocket client"""
        await websocket.accept()
        
        if connection_type in self.active_connections:
            self.active_connections[connection_type].add(websocket)
            self.connection_metadata[websocket] = {
                "type": connection_type,
                "connected_at": datetime.now(),
                "metadata": metadata or {}
            }
            
            logger.info(f"WebSocket connected: {connection_type}")
            
            # Send initial data
            await self._send_initial_data(websocket, connection_type)
        else:
            await websocket.close(code=1008, reason="Invalid connection type")
    
    async def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client"""
        connection_type = None
        
        # Find and remove from all connection types
        for conn_type, connections in self.active_connections.items():
            if websocket in connections:
                connections.remove(websocket)
                connection_type = conn_type
                break
        
        # Remove metadata
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]
        
        logger.info(f"WebSocket disconnected: {connection_type}")
    
    async def _send_initial_data(self, websocket: WebSocket, connection_type: str):
        """Send initial data to newly connected client"""
        try:
            if connection_type == "dashboard":
                # Send current dashboard data
                for dashboard_type in ["business_intelligence", "market_analytics", "user_analytics", "performance"]:
                    data = await analytics_engine.get_dashboard_data(dashboard_type)
                    await websocket.send_text(json.dumps({
                        "type": "dashboard_update",
                        "dashboard_type": dashboard_type,
                        "data": data,
                        "timestamp": datetime.now().isoformat()
                    }))
            
            elif connection_type == "metrics":
                # Send current metrics summary
                summary = await analytics_engine.get_analytics_summary()
                await websocket.send_text(json.dumps({
                    "type": "metrics_summary",
                    "data": summary,
                    "timestamp": datetime.now().isoformat()
                }))
            
            elif connection_type == "predictions":
                # Send available prediction models
                models = list(predictive_analytics.models.keys())
                await websocket.send_text(json.dumps({
                    "type": "available_models",
                    "models": models,
                    "timestamp": datetime.now().isoformat()
                }))
            
            elif connection_type == "alerts":
                # Send recent alerts
                await websocket.send_text(json.dumps({
                    "type": "alerts_summary",
                    "data": {"active_alerts": 0, "recent_alerts": []},
                    "timestamp": datetime.now().isoformat()
                }))
                
        except Exception as e:
            logger.error(f"Error sending initial data: {e}")
    
    async def _broadcast_dashboard_updates(self):
        """Broadcast dashboard updates to connected clients"""
        while True:
            try:
                if self.active_connections["dashboard"]:
                    # Get updated dashboard data
                    for dashboard_type in ["business_intelligence", "market_analytics", "user_analytics", "performance"]:
                        data = await analytics_engine.get_dashboard_data(dashboard_type)
                        
                        message = json.dumps({
                            "type": "dashboard_update",
                            "dashboard_type": dashboard_type,
                            "data": data,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        # Send to all dashboard connections
                        disconnected = set()
                        for websocket in self.active_connections["dashboard"]:
                            try:
                                await websocket.send_text(message)
                            except Exception as e:
                                logger.warning(f"Error sending to dashboard WebSocket: {e}")
                                disconnected.add(websocket)
                        
                        # Remove disconnected clients
                        for websocket in disconnected:
                            await self.disconnect(websocket)
                
                await asyncio.sleep(10)  # Update every 10 seconds
                
            except Exception as e:
                logger.error(f"Error broadcasting dashboard updates: {e}")
                await asyncio.sleep(30)
    
    async def _broadcast_metrics_updates(self):
        """Broadcast metrics updates to connected clients"""
        while True:
            try:
                if self.active_connections["metrics"]:
                    # Get metrics summary
                    summary = await analytics_engine.get_analytics_summary()
                    
                    message = json.dumps({
                        "type": "metrics_update",
                        "data": summary,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Send to all metrics connections
                    disconnected = set()
                    for websocket in self.active_connections["metrics"]:
                        try:
                            await websocket.send_text(message)
                        except Exception as e:
                            logger.warning(f"Error sending to metrics WebSocket: {e}")
                            disconnected.add(websocket)
                    
                    # Remove disconnected clients
                    for websocket in disconnected:
                        await self.disconnect(websocket)
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"Error broadcasting metrics updates: {e}")
                await asyncio.sleep(30)
    
    async def _broadcast_predictions_updates(self):
        """Broadcast prediction updates to connected clients"""
        while True:
            try:
                if self.active_connections["predictions"]:
                    # Get predictions for active models
                    predictions = {}
                    for symbol in predictive_analytics.models.keys():
                        try:
                            prediction = await predictive_analytics.predict_price(symbol, 24)
                            if "error" not in prediction:
                                predictions[symbol] = prediction
                        except Exception as e:
                            logger.warning(f"Error getting prediction for {symbol}: {e}")
                    
                    if predictions:
                        message = json.dumps({
                            "type": "predictions_update",
                            "data": predictions,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        # Send to all predictions connections
                        disconnected = set()
                        for websocket in self.active_connections["predictions"]:
                            try:
                                await websocket.send_text(message)
                            except Exception as e:
                                logger.warning(f"Error sending to predictions WebSocket: {e}")
                                disconnected.add(websocket)
                        
                        # Remove disconnected clients
                        for websocket in disconnected:
                            await self.disconnect(websocket)
                
                await asyncio.sleep(60)  # Update every minute
                
            except Exception as e:
                logger.error(f"Error broadcasting predictions updates: {e}")
                await asyncio.sleep(120)
    
    async def _broadcast_alerts(self):
        """Broadcast alerts to connected clients"""
        while True:
            try:
                if self.active_connections["alerts"]:
                    # Check for anomalies and generate alerts
                    alerts = []
                    
                    # Check for system performance alerts
                    performance_data = await analytics_engine.get_dashboard_data("performance")
                    system_metrics = performance_data.get("system_metrics", {})
                    
                    if system_metrics.get("cpu_usage", 0) > 80:
                        alerts.append({
                            "type": "system_alert",
                            "severity": "warning",
                            "message": "High CPU usage detected",
                            "value": system_metrics["cpu_usage"],
                            "threshold": 80
                        })
                    
                    if system_metrics.get("memory_usage", 0) > 85:
                        alerts.append({
                            "type": "system_alert",
                            "severity": "critical",
                            "message": "High memory usage detected",
                            "value": system_metrics["memory_usage"],
                            "threshold": 85
                        })
                    
                    # Check for market alerts
                    market_data = await analytics_engine.get_dashboard_data("market_analytics")
                    stock_analytics = market_data.get("stock_analytics", {})
                    
                    # Check for significant price movements
                    for gainer in stock_analytics.get("top_gainers", []):
                        if gainer.get("change_percent", 0) > 10:
                            alerts.append({
                                "type": "market_alert",
                                "severity": "info",
                                "message": f"Significant price increase: {gainer.get('symbol', 'Unknown')}",
                                "value": gainer.get("change_percent", 0),
                                "threshold": 10
                            })
                    
                    for loser in stock_analytics.get("top_losers", []):
                        if loser.get("change_percent", 0) < -10:
                            alerts.append({
                                "type": "market_alert",
                                "severity": "warning",
                                "message": f"Significant price decrease: {loser.get('symbol', 'Unknown')}",
                                "value": loser.get("change_percent", 0),
                                "threshold": -10
                            })
                    
                    if alerts:
                        message = json.dumps({
                            "type": "alerts_update",
                            "data": {
                                "active_alerts": len(alerts),
                                "alerts": alerts
                            },
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        # Send to all alerts connections
                        disconnected = set()
                        for websocket in self.active_connections["alerts"]:
                            try:
                                await websocket.send_text(message)
                            except Exception as e:
                                logger.warning(f"Error sending to alerts WebSocket: {e}")
                                disconnected.add(websocket)
                        
                        # Remove disconnected clients
                        for websocket in disconnected:
                            await self.disconnect(websocket)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error broadcasting alerts: {e}")
                await asyncio.sleep(60)
    
    async def send_custom_message(self, connection_type: str, message: Dict[str, Any]):
        """Send custom message to specific connection type"""
        if connection_type in self.active_connections:
            message_json = json.dumps({
                "type": "custom_message",
                "data": message,
                "timestamp": datetime.now().isoformat()
            })
            
            disconnected = set()
            for websocket in self.active_connections[connection_type]:
                try:
                    await websocket.send_text(message_json)
                except Exception as e:
                    logger.warning(f"Error sending custom message: {e}")
                    disconnected.add(websocket)
            
            # Remove disconnected clients
            for websocket in disconnected:
                await self.disconnect(websocket)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "total_connections": sum(len(connections) for connections in self.active_connections.values()),
            "connections_by_type": {
                conn_type: len(connections) 
                for conn_type, connections in self.active_connections.items()
            },
            "connection_metadata": {
                str(websocket): metadata 
                for websocket, metadata in self.connection_metadata.items()
            }
        }

# Global WebSocket manager instance
websocket_manager = AnalyticsWebSocketManager()

# WebSocket endpoint handlers
async def handle_dashboard_websocket(websocket: WebSocket, metadata: Dict[str, Any] = None):
    """Handle dashboard WebSocket connection"""
    await websocket_manager.connect(websocket, "dashboard", metadata)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle client requests
            if message.get("type") == "request_dashboard":
                dashboard_type = message.get("dashboard_type", "business_intelligence")
                data = await analytics_engine.get_dashboard_data(dashboard_type)
                
                await websocket.send_text(json.dumps({
                    "type": "dashboard_response",
                    "dashboard_type": dashboard_type,
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                }))
            
            elif message.get("type") == "request_metrics":
                metrics = message.get("metrics", [])
                metrics_data = await analytics_engine.get_real_time_metrics(metrics)
                
                await websocket.send_text(json.dumps({
                    "type": "metrics_response",
                    "data": metrics_data,
                    "timestamp": datetime.now().isoformat()
                }))
                
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error in dashboard WebSocket: {e}")
        await websocket_manager.disconnect(websocket)

async def handle_metrics_websocket(websocket: WebSocket, metadata: Dict[str, Any] = None):
    """Handle metrics WebSocket connection"""
    await websocket_manager.connect(websocket, "metrics", metadata)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle client requests
            if message.get("type") == "request_metrics":
                metrics = message.get("metrics", [])
                metrics_data = await analytics_engine.get_real_time_metrics(metrics)
                
                await websocket.send_text(json.dumps({
                    "type": "metrics_response",
                    "data": metrics_data,
                    "timestamp": datetime.now().isoformat()
                }))
            
            elif message.get("type") == "request_summary":
                summary = await analytics_engine.get_analytics_summary()
                
                await websocket.send_text(json.dumps({
                    "type": "summary_response",
                    "data": summary,
                    "timestamp": datetime.now().isoformat()
                }))
                
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error in metrics WebSocket: {e}")
        await websocket_manager.disconnect(websocket)

async def handle_predictions_websocket(websocket: WebSocket, metadata: Dict[str, Any] = None):
    """Handle predictions WebSocket connection"""
    await websocket_manager.connect(websocket, "predictions", metadata)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle client requests
            if message.get("type") == "request_prediction":
                symbol = message.get("symbol")
                horizon_hours = message.get("horizon_hours", 24)
                
                if symbol:
                    prediction = await predictive_analytics.predict_price(symbol, horizon_hours)
                    
                    await websocket.send_text(json.dumps({
                        "type": "prediction_response",
                        "symbol": symbol,
                        "data": prediction,
                        "timestamp": datetime.now().isoformat()
                    }))
            
            elif message.get("type") == "request_anomalies":
                symbol = message.get("symbol")
                threshold = message.get("threshold", 0.1)
                
                if symbol:
                    anomalies = await predictive_analytics.detect_anomalies(symbol, threshold)
                    
                    await websocket.send_text(json.dumps({
                        "type": "anomalies_response",
                        "symbol": symbol,
                        "data": anomalies,
                        "timestamp": datetime.now().isoformat()
                    }))
                
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error in predictions WebSocket: {e}")
        await websocket_manager.disconnect(websocket)

async def handle_alerts_websocket(websocket: WebSocket, metadata: Dict[str, Any] = None):
    """Handle alerts WebSocket connection"""
    await websocket_manager.connect(websocket, "alerts", metadata)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle client requests
            if message.get("type") == "request_alerts":
                # Send current alerts
                await websocket.send_text(json.dumps({
                    "type": "alerts_response",
                    "data": {"active_alerts": 0, "recent_alerts": []},
                    "timestamp": datetime.now().isoformat()
                }))
            
            elif message.get("type") == "acknowledge_alert":
                alert_id = message.get("alert_id")
                # Handle alert acknowledgment
                await websocket.send_text(json.dumps({
                    "type": "alert_acknowledged",
                    "alert_id": alert_id,
                    "timestamp": datetime.now().isoformat()
                }))
                
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error in alerts WebSocket: {e}")
        await websocket_manager.disconnect(websocket)
