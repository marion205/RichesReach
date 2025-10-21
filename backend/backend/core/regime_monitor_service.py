"""
Real-time Regime Monitoring Service
===================================

Continuously monitors market conditions and detects regime changes in real-time.
This is a key Phase 1 enhancement that provides immediate regime alerts and
adaptive content updates.

Key Features:
- Real-time market data monitoring
- Regime change detection with confidence scoring
- Automatic notification triggering
- Historical regime tracking
- Performance analytics and backtesting

Dependencies:
- ml_service: For regime prediction models
- notification_service: For alert delivery
- market_data_service: For real-time data feeds
"""

from __future__ import annotations

import asyncio
import json
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, TypedDict
from enum import Enum

from .ml_service import MLService
from .notification_service import NotificationService

logger = logging.getLogger(__name__)

# =============================================================================
# Enums and Types
# =============================================================================

class RegimeChangeSeverity(str, Enum):
    """Severity levels for regime changes."""
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CRITICAL = "critical"

class MonitoringStatus(str, Enum):
    """Monitoring service status."""
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    MAINTENANCE = "maintenance"

# =============================================================================
# Typed Payloads
# =============================================================================

class RegimeChangeEvent(TypedDict, total=False):
    """Regime change event payload."""
    event_id: str
    timestamp: str  # ISO8601 (UTC)
    old_regime: str
    new_regime: str
    confidence: float
    severity: str
    market_data: Dict[str, Any]
    change_factors: List[str]
    impact_assessment: Dict[str, Any]
    recommended_actions: List[str]

class MonitoringMetrics(TypedDict, total=False):
    """Monitoring service metrics."""
    service_id: str
    status: str
    uptime_seconds: int
    total_events_detected: int
    events_last_hour: int
    average_confidence: float
    false_positive_rate: float
    last_regime_change: Optional[str]  # ISO8601 (UTC)
    active_monitors: int
    error_count: int
    last_error: Optional[str]

# =============================================================================
# Utility Functions
# =============================================================================

def _now_iso_utc() -> str:
    """Get current UTC timestamp in ISO8601 format."""
    return datetime.now(timezone.utc).isoformat()

def _safe_json_loads(s: str) -> Optional[Dict[str, Any]]:
    """Safely parse JSON string, returning None on failure."""
    try:
        return json.loads(s)
    except Exception:
        return None

# =============================================================================
# Main Service Class
# =============================================================================

class RegimeMonitorService:
    """
    Real-time Regime Monitoring Service.
    
    Core Functionality:
        - Continuous market data monitoring
        - Real-time regime change detection
        - Automatic notification triggering
        - Historical regime tracking
        - Performance analytics and alerting
    
    Design Notes:
        - All timestamps in UTC (ISO8601)
        - Configurable monitoring intervals
        - Confidence-based alerting
        - Historical regime persistence
    """

    # Configuration Defaults
    DEFAULT_MONITORING_INTERVAL = 300  # 5 minutes
    MIN_CONFIDENCE_THRESHOLD = 0.7
    REGIME_CHANGE_THRESHOLD = 0.8
    MAX_HISTORICAL_REGIMES = 1000

    def __init__(
        self,
        ml_service: Optional[MLService] = None,
        notification_service: Optional[NotificationService] = None,
        *,
        monitoring_interval: int = DEFAULT_MONITORING_INTERVAL,
    ) -> None:
        self.ml_service = ml_service or MLService()
        self.notification_service = notification_service or NotificationService()
        self.monitoring_interval = monitoring_interval
        self.is_monitoring = False
        self.current_regime = None
        self.regime_history = []
        self.metrics = self._initialize_metrics()

    # -------------------------------------------------------------------------
    # Public API Methods
    # -------------------------------------------------------------------------

    async def start_monitoring(self) -> None:
        """Start real-time regime monitoring."""
        try:
            if self.is_monitoring:
                logger.warning("Regime monitoring is already active")
                return
            
            self.is_monitoring = True
            self.metrics["status"] = MonitoringStatus.ACTIVE.value
            self.metrics["uptime_seconds"] = 0
            
            logger.info("Starting real-time regime monitoring")
            
            # Start monitoring loop
            asyncio.create_task(self._monitoring_loop())
            
        except Exception as e:
            logger.error(f"Error starting regime monitoring: {e}")
            self.metrics["status"] = MonitoringStatus.ERROR.value
            self.metrics["error_count"] += 1
            self.metrics["last_error"] = str(e)
            raise

    async def stop_monitoring(self) -> None:
        """Stop real-time regime monitoring."""
        try:
            self.is_monitoring = False
            self.metrics["status"] = MonitoringStatus.PAUSED.value
            
            logger.info("Stopped real-time regime monitoring")
            
        except Exception as e:
            logger.error(f"Error stopping regime monitoring: {e}")
            raise

    async def check_regime_change(self, market_data: Dict[str, Any]) -> Optional[RegimeChangeEvent]:
        """
        Check for regime change based on current market data.
        
        Args:
            market_data: Current market data for regime detection
            
        Returns:
            RegimeChangeEvent if regime change detected, None otherwise
        """
        try:
            # Get current regime prediction
            regime_prediction = self.ml_service.predict_market_regime(market_data)
            new_regime = regime_prediction.get('regime', 'sideways_consolidation')
            confidence = regime_prediction.get('confidence', 0.5)
            
            # Check if this is a significant regime change
            if self._is_significant_regime_change(new_regime, confidence):
                # Create regime change event
                event = await self._create_regime_change_event(
                    old_regime=self.current_regime,
                    new_regime=new_regime,
                    confidence=confidence,
                    market_data=market_data
                )
                
                # Update current regime
                self.current_regime = new_regime
                self._add_to_regime_history(event)
                
                # Trigger notifications
                await self._trigger_regime_change_notifications(event)
                
                # Update metrics
                self._update_metrics(event)
                
                logger.info(f"Regime change detected: {event['old_regime']} → {event['new_regime']} (confidence: {confidence:.2f})")
                return event
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking regime change: {e}")
            self.metrics["error_count"] += 1
            self.metrics["last_error"] = str(e)
            raise

    async def get_current_regime_status(self) -> Dict[str, Any]:
        """
        Get current regime status and monitoring metrics.
        
        Returns:
            Current regime status with monitoring metrics
        """
        try:
            return {
                "current_regime": self.current_regime,
                "monitoring_active": self.is_monitoring,
                "metrics": self.metrics.copy(),
                "regime_history_count": len(self.regime_history),
                "last_check": _now_iso_utc()
            }
            
        except Exception as e:
            logger.error(f"Error getting regime status: {e}")
            raise

    async def get_regime_history(
        self,
        *,
        limit: int = 50,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[RegimeChangeEvent]:
        """
        Get historical regime change events.
        
        Args:
            limit: Maximum number of events to return
            start_date: Start date filter (ISO8601)
            end_date: End date filter (ISO8601)
            
        Returns:
            List of historical regime change events
        """
        try:
            # Filter regime history
            filtered_history = self.regime_history.copy()
            
            if start_date:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                filtered_history = [event for event in filtered_history 
                                  if datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00')) >= start_dt]
            
            if end_date:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                filtered_history = [event for event in filtered_history 
                                  if datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00')) <= end_dt]
            
            # Sort by timestamp (newest first) and limit
            filtered_history.sort(key=lambda x: x['timestamp'], reverse=True)
            return filtered_history[:limit]
            
        except Exception as e:
            logger.error(f"Error getting regime history: {e}")
            raise

    # -------------------------------------------------------------------------
    # Private Helper Methods
    # -------------------------------------------------------------------------

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                # Get current market data (in production, from real data feeds)
                market_data = await self._get_current_market_data()
                
                # Check for regime change
                await self.check_regime_change(market_data)
                
                # Update uptime
                self.metrics["uptime_seconds"] += self.monitoring_interval
                
                # Wait for next monitoring cycle
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                self.metrics["error_count"] += 1
                self.metrics["last_error"] = str(e)
                await asyncio.sleep(self.monitoring_interval)

    async def _get_current_market_data(self) -> Dict[str, Any]:
        """Get current market data for regime detection."""
        # In production, this would fetch from real market data feeds
        # For now, return mock data
        import random
        
        return {
            "spy_price": 450.0 + random.uniform(-5, 5),
            "vix": 15.0 + random.uniform(-2, 2),
            "dxy": 103.0 + random.uniform(-1, 1),
            "yield_10y": 4.5 + random.uniform(-0.1, 0.1),
            "volume_spy": 50000000 + random.randint(-10000000, 10000000),
            "sector_rotation": {
                "technology": random.uniform(-0.02, 0.02),
                "healthcare": random.uniform(-0.02, 0.02),
                "financials": random.uniform(-0.02, 0.02),
                "energy": random.uniform(-0.02, 0.02)
            }
        }

    def _is_significant_regime_change(self, new_regime: str, confidence: float) -> bool:
        """Check if this represents a significant regime change."""
        # Must meet confidence threshold
        if confidence < self.MIN_CONFIDENCE_THRESHOLD:
            return False
        
        # Must be different from current regime
        if self.current_regime is None:
            return True
        
        if new_regime == self.current_regime:
            return False
        
        # Check if confidence is high enough for regime change
        return confidence >= self.REGIME_CHANGE_THRESHOLD

    async def _create_regime_change_event(
        self,
        old_regime: Optional[str],
        new_regime: str,
        confidence: float,
        market_data: Dict[str, Any]
    ) -> RegimeChangeEvent:
        """Create a regime change event."""
        event_id = str(uuid.uuid4())
        
        # Determine severity
        severity = self._determine_change_severity(old_regime, new_regime, confidence)
        
        # Analyze change factors
        change_factors = self._analyze_change_factors(market_data, old_regime, new_regime)
        
        # Assess impact
        impact_assessment = self._assess_regime_impact(new_regime, confidence)
        
        # Generate recommended actions
        recommended_actions = self._generate_recommended_actions(new_regime, severity)
        
        return {
            "event_id": event_id,
            "timestamp": _now_iso_utc(),
            "old_regime": old_regime or "unknown",
            "new_regime": new_regime,
            "confidence": confidence,
            "severity": severity.value,
            "market_data": market_data,
            "change_factors": change_factors,
            "impact_assessment": impact_assessment,
            "recommended_actions": recommended_actions
        }

    def _determine_change_severity(self, old_regime: Optional[str], new_regime: str, confidence: float) -> RegimeChangeSeverity:
        """Determine the severity of a regime change."""
        if confidence >= 0.95:
            return RegimeChangeSeverity.CRITICAL
        elif confidence >= 0.85:
            return RegimeChangeSeverity.MAJOR
        elif confidence >= 0.75:
            return RegimeChangeSeverity.MODERATE
        else:
            return RegimeChangeSeverity.MINOR

    def _analyze_change_factors(self, market_data: Dict[str, Any], old_regime: Optional[str], new_regime: str) -> List[str]:
        """Analyze factors contributing to regime change."""
        factors = []
        
        # Analyze VIX changes
        vix = market_data.get('vix', 15)
        if vix > 25:
            factors.append("High volatility (VIX > 25)")
        elif vix < 12:
            factors.append("Low volatility (VIX < 12)")
        
        # Analyze sector rotation
        sector_rotation = market_data.get('sector_rotation', {})
        if sector_rotation:
            strongest_sector = max(sector_rotation.items(), key=lambda x: x[1])
            weakest_sector = min(sector_rotation.items(), key=lambda x: x[1])
            factors.append(f"Strong {strongest_sector[0]} sector performance")
            factors.append(f"Weak {weakest_sector[0]} sector performance")
        
        # Analyze volume
        volume = market_data.get('volume_spy', 0)
        if volume > 60000000:
            factors.append("High trading volume")
        elif volume < 40000000:
            factors.append("Low trading volume")
        
        return factors

    def _assess_regime_impact(self, new_regime: str, confidence: float) -> Dict[str, Any]:
        """Assess the impact of the new regime."""
        impact_levels = {
            'early_bull_market': {'risk_level': 'low', 'opportunity_level': 'high'},
            'late_bull_market': {'risk_level': 'medium', 'opportunity_level': 'medium'},
            'bear_market': {'risk_level': 'high', 'opportunity_level': 'low'},
            'sideways_consolidation': {'risk_level': 'low', 'opportunity_level': 'low'},
            'high_volatility': {'risk_level': 'high', 'opportunity_level': 'medium'},
            'correction': {'risk_level': 'medium', 'opportunity_level': 'medium'},
            'recovery': {'risk_level': 'medium', 'opportunity_level': 'high'},
            'bubble_formation': {'risk_level': 'high', 'opportunity_level': 'high'}
        }
        
        base_impact = impact_levels.get(new_regime, {'risk_level': 'medium', 'opportunity_level': 'medium'})
        
        return {
            "regime": new_regime,
            "confidence": confidence,
            "risk_level": base_impact['risk_level'],
            "opportunity_level": base_impact['opportunity_level'],
            "expected_duration": "short-term" if confidence < 0.8 else "medium-term",
            "key_considerations": self._get_regime_considerations(new_regime)
        }

    def _get_regime_considerations(self, regime: str) -> List[str]:
        """Get key considerations for a regime."""
        considerations = {
            'early_bull_market': [
                "Focus on growth stocks and momentum strategies",
                "Consider increasing equity allocation",
                "Watch for early signs of overvaluation"
            ],
            'late_bull_market': [
                "Take profits on extended positions",
                "Increase defensive allocation",
                "Prepare for potential correction"
            ],
            'bear_market': [
                "Focus on capital preservation",
                "Consider defensive strategies",
                "Look for quality stocks at discounted prices"
            ],
            'sideways_consolidation': [
                "Use range-bound trading strategies",
                "Focus on dividend-paying stocks",
                "Be patient and wait for clear direction"
            ],
            'high_volatility': [
                "Reduce position sizes",
                "Use stop-losses religiously",
                "Consider volatility trading strategies"
            ]
        }
        
        return considerations.get(regime, ["Monitor market conditions closely", "Maintain diversified portfolio"])

    def _generate_recommended_actions(self, new_regime: str, severity: RegimeChangeSeverity) -> List[str]:
        """Generate recommended actions based on regime change."""
        actions = []
        
        if severity in [RegimeChangeSeverity.CRITICAL, RegimeChangeSeverity.MAJOR]:
            actions.append("Review and rebalance portfolio immediately")
            actions.append("Consider adjusting risk management parameters")
        
        if new_regime == 'bear_market':
            actions.append("Increase defensive allocation")
            actions.append("Consider hedging strategies")
        elif new_regime == 'early_bull_market':
            actions.append("Consider increasing growth exposure")
            actions.append("Look for momentum opportunities")
        elif new_regime == 'high_volatility':
            actions.append("Reduce position sizes")
            actions.append("Implement strict stop-losses")
        
        actions.append("Monitor market conditions closely")
        actions.append("Stay disciplined with your strategy")
        
        return actions

    def _add_to_regime_history(self, event: RegimeChangeEvent) -> None:
        """Add regime change event to history."""
        self.regime_history.append(event)
        
        # Limit history size
        if len(self.regime_history) > self.MAX_HISTORICAL_REGIMES:
            self.regime_history = self.regime_history[-self.MAX_HISTORICAL_REGIMES:]

    def _update_metrics(self, event: RegimeChangeEvent) -> None:
        """Update monitoring metrics."""
        self.metrics["total_events_detected"] += 1
        self.metrics["events_last_hour"] += 1
        self.metrics["last_regime_change"] = event["timestamp"]
        
        # Update average confidence
        total_events = self.metrics["total_events_detected"]
        current_avg = self.metrics["average_confidence"]
        new_avg = ((current_avg * (total_events - 1)) + event["confidence"]) / total_events
        self.metrics["average_confidence"] = new_avg

    def _initialize_metrics(self) -> MonitoringMetrics:
        """Initialize monitoring metrics."""
        return {
            "service_id": str(uuid.uuid4()),
            "status": MonitoringStatus.PAUSED.value,
            "uptime_seconds": 0,
            "total_events_detected": 0,
            "events_last_hour": 0,
            "average_confidence": 0.0,
            "false_positive_rate": 0.0,
            "last_regime_change": None,
            "active_monitors": 1,
            "error_count": 0,
            "last_error": None
        }

    async def _trigger_regime_change_notifications(self, event: RegimeChangeEvent) -> None:
        """Trigger notifications for regime change."""
        try:
            # Determine urgency based on severity
            urgency_map = {
                RegimeChangeSeverity.CRITICAL: "urgent",
                RegimeChangeSeverity.MAJOR: "high",
                RegimeChangeSeverity.MODERATE: "medium",
                RegimeChangeSeverity.MINOR: "low"
            }
            
            urgency = urgency_map.get(RegimeChangeSeverity(event["severity"]), "medium")
            
            # Create regime change data for notification
            regime_change = {
                "old_regime": event["old_regime"],
                "new_regime": event["new_regime"],
                "confidence": event["confidence"]
            }
            
            # In production, this would notify all subscribed users
            # For now, we'll just log the notification
            logger.info(f"Would trigger regime change notification: {urgency} priority")
            
        except Exception as e:
            logger.error(f"Error triggering regime change notifications: {e}")

# =============================================================================
# Singleton Instance
# =============================================================================

regime_monitor_service = RegimeMonitorService()
