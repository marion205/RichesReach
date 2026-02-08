"""
Performance Monitoring Service for ML Models
Tracks model accuracy, drift, and system health metrics
"""
import logging
import json
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import queue
import sqlite3
import threading

from .alert_notifications import send_email_alert, send_slack_alert

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics to monitor"""

    ACCURACY = "accuracy"
    PREDICTION_DRIFT = "prediction_drift"
    FEATURE_DRIFT = "feature_drift"
    MODEL_PERFORMANCE = "model_performance"
    SYSTEM_HEALTH = "system_health"
    API_PERFORMANCE = "api_performance"


class AlertLevel(Enum):
    """Alert levels for monitoring"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Metric:
    """Metric data structure"""

    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime
    model_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Alert:
    """Alert data structure"""

    level: AlertLevel
    message: str
    metric_name: str
    timestamp: datetime
    threshold: float
    current_value: float
    model_name: Optional[str] = None


@dataclass
class ModelPerformance:
    """Model performance tracking"""

    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    mse: float
    mae: float
    timestamp: datetime
    training_samples: int
    validation_samples: int


class PerformanceMonitoringService:
    """
    Service for monitoring ML model performance and system health
    """

    def __init__(self, db_path: str = "ml_monitoring.db"):
        self.db_path = db_path
        self.metrics_queue = queue.Queue()
        self.alerts_queue = queue.Queue()
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None

        # Thresholds for alerts
        self.thresholds = {
            "accuracy_drop": 0.05,  # 5% drop in accuracy
            "prediction_drift": 0.1,  # 10% drift in predictions
            "feature_drift": 0.15,  # 15% drift in features
            "response_time": 2.0,  # 2 seconds max response time
            "error_rate": 0.05,  # 5% error rate
            "memory_usage": 0.9,  # 90% memory usage
            "cpu_usage": 0.8,  # 80% CPU usage
        }

        # Initialize database
        self._init_database()

        # Start monitoring
        self.start_monitoring()

    def _init_database(self) -> None:
        """Initialize monitoring database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create metrics table
            cursor.execute(
                """
CREATE TABLE IF NOT EXISTS metrics (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT NOT NULL,
value REAL NOT NULL,
metric_type TEXT NOT NULL,
timestamp TEXT NOT NULL,
model_name TEXT,
metadata TEXT
)
"""
            )

            # Create alerts table
            cursor.execute(
                """
CREATE TABLE IF NOT EXISTS alerts (
id INTEGER PRIMARY KEY AUTOINCREMENT,
level TEXT NOT NULL,
message TEXT NOT NULL,
metric_name TEXT NOT NULL,
timestamp TEXT NOT NULL,
threshold REAL NOT NULL,
current_value REAL NOT NULL,
model_name TEXT
)
"""
            )

            # Create model_performance table
            cursor.execute(
                """
CREATE TABLE IF NOT EXISTS model_performance (
id INTEGER PRIMARY KEY AUTOINCREMENT,
model_name TEXT NOT NULL,
accuracy REAL NOT NULL,
precision REAL NOT NULL,
recall REAL NOT NULL,
f1_score REAL NOT NULL,
mse REAL NOT NULL,
mae REAL NOT NULL,
timestamp TEXT NOT NULL,
training_samples INTEGER NOT NULL,
validation_samples INTEGER NOT NULL
)
"""
            )

            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_model ON metrics(model_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)")
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_model_perf_timestamp ON model_performance(timestamp)"
            )

            conn.commit()
            conn.close()
            logger.info("Monitoring database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing monitoring database: {e}")

    def start_monitoring(self) -> None:
        """Start the monitoring thread"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            logger.info("Performance monitoring started")

    def stop_monitoring(self) -> None:
        """Stop the monitoring thread"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
            logger.info("Performance monitoring stopped")

    def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Process metrics
                while not self.metrics_queue.empty():
                    metric = self.metrics_queue.get_nowait()
                    self._store_metric(metric)
                    self._check_thresholds(metric)

                # Process alerts
                while not self.alerts_queue.empty():
                    alert = self.alerts_queue.get_nowait()
                    self._store_alert(alert)
                    self._send_alert(alert)

                # System health check
                self._check_system_health()

                # Sleep for monitoring interval
                time.sleep(10)  # Check every 10 seconds
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(30)  # Wait longer on error

    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType,
        model_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record a new metric
        """
        try:
            metric = Metric(
                name=name,
                value=value,
                metric_type=metric_type,
                timestamp=datetime.now(),
                model_name=model_name,
                metadata=metadata,
            )
            self.metrics_queue.put(metric)
        except Exception as e:
            logger.error(f"Error recording metric {name}: {e}")

    def record_model_performance(
        self,
        model_name: str,
        accuracy: float,
        precision: float,
        recall: float,
        f1_score: float,
        mse: float,
        mae: float,
        training_samples: int,
        validation_samples: int,
    ) -> None:
        """
        Record model performance metrics
        """
        try:
            performance = ModelPerformance(
                model_name=model_name,
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                f1_score=f1_score,
                mse=mse,
                mae=mae,
                timestamp=datetime.now(),
                training_samples=training_samples,
                validation_samples=validation_samples,
            )

            # Store in database
            self._store_model_performance(performance)

            # Record accuracy metric
            self.record_metric(
                name=f"{model_name}_accuracy",
                value=accuracy,
                metric_type=MetricType.ACCURACY,
                model_name=model_name,
            )
        except Exception as e:
            logger.error(f"Error recording model performance for {model_name}: {e}")

    def _store_metric(self, metric: Metric) -> None:
        """Store metric in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
INSERT INTO metrics (name, value, metric_type, timestamp, model_name, metadata)
VALUES (?, ?, ?, ?, ?, ?)
""",
                (
                    metric.name,
                    metric.value,
                    metric.metric_type.value,
                    metric.timestamp.isoformat(),
                    metric.model_name,
                    json.dumps(metric.metadata) if metric.metadata else None,
                ),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error storing metric: {e}")

    def _store_alert(self, alert: Alert) -> None:
        """Store alert in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
INSERT INTO alerts (level, message, metric_name, timestamp, threshold, current_value, model_name)
VALUES (?, ?, ?, ?, ?, ?, ?)
""",
                (
                    alert.level.value,
                    alert.message,
                    alert.metric_name,
                    alert.timestamp.isoformat(),
                    alert.threshold,
                    alert.current_value,
                    alert.model_name,
                ),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error storing alert: {e}")

    def _store_model_performance(self, performance: ModelPerformance) -> None:
        """Store model performance in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
INSERT INTO model_performance
(model_name, accuracy, precision, recall, f1_score, mse, mae, timestamp, training_samples, validation_samples)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""",
                (
                    performance.model_name,
                    performance.accuracy,
                    performance.precision,
                    performance.recall,
                    performance.f1_score,
                    performance.mse,
                    performance.mae,
                    performance.timestamp.isoformat(),
                    performance.training_samples,
                    performance.validation_samples,
                ),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error storing model performance: {e}")

    def _check_thresholds(self, metric: Metric) -> None:
        """Check if metric exceeds thresholds and generate alerts"""
        try:
            if metric.metric_type == MetricType.ACCURACY:
                self._check_accuracy_threshold(metric)
            elif metric.metric_type == MetricType.PREDICTION_DRIFT:
                self._check_drift_threshold(metric)
            elif metric.metric_type == MetricType.SYSTEM_HEALTH:
                self._check_system_threshold(metric)
        except Exception as e:
            logger.error(f"Error checking thresholds: {e}")

    def _check_accuracy_threshold(self, metric: Metric) -> None:
        """Check accuracy threshold"""
        if metric.value < self.thresholds["accuracy_drop"]:
            alert = Alert(
                level=AlertLevel.WARNING,
                message=f"Model accuracy dropped to {metric.value:.3f}",
                metric_name=metric.name,
                timestamp=datetime.now(),
                threshold=self.thresholds["accuracy_drop"],
                current_value=metric.value,
                model_name=metric.model_name,
            )
            self.alerts_queue.put(alert)

    def _check_drift_threshold(self, metric: Metric) -> None:
        """Check drift threshold"""
        if metric.value > self.thresholds["prediction_drift"]:
            alert = Alert(
                level=AlertLevel.WARNING,
                message=f"Prediction drift detected: {metric.value:.3f}",
                metric_name=metric.name,
                timestamp=datetime.now(),
                threshold=self.thresholds["prediction_drift"],
                current_value=metric.value,
                model_name=metric.model_name,
            )
            self.alerts_queue.put(alert)

    def _check_system_threshold(self, metric: Metric) -> None:
        """Check system health threshold"""
        if "memory" in metric.name and metric.value > self.thresholds["memory_usage"]:
            alert = Alert(
                level=AlertLevel.WARNING,
                message=f"High memory usage: {metric.value:.1%}",
                metric_name=metric.name,
                timestamp=datetime.now(),
                threshold=self.thresholds["memory_usage"],
                current_value=metric.value,
            )
            self.alerts_queue.put(alert)
        elif "cpu" in metric.name and metric.value > self.thresholds["cpu_usage"]:
            alert = Alert(
                level=AlertLevel.WARNING,
                message=f"High CPU usage: {metric.value:.1%}",
                metric_name=metric.name,
                timestamp=datetime.now(),
                threshold=self.thresholds["cpu_usage"],
                current_value=metric.value,
            )
            self.alerts_queue.put(alert)

    def _check_system_health(self) -> None:
        """Check system health metrics"""
        try:
            import psutil

            # Memory usage
            memory_percent = psutil.virtual_memory().percent / 100.0
            self.record_metric(
                name="system_memory_usage",
                value=memory_percent,
                metric_type=MetricType.SYSTEM_HEALTH,
            )

            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1) / 100.0
            self.record_metric(
                name="system_cpu_usage",
                value=cpu_percent,
                metric_type=MetricType.SYSTEM_HEALTH,
            )

            # Disk usage
            disk_percent = psutil.disk_usage("/").percent / 100.0
            self.record_metric(
                name="system_disk_usage",
                value=disk_percent,
                metric_type=MetricType.SYSTEM_HEALTH,
            )
        except ImportError:
            logger.warning("psutil not available for system health monitoring")
        except Exception as e:
            logger.error(f"Error checking system health: {e}")

    def _send_alert(self, alert: Alert) -> None:
        """Send alert notification"""
        try:
            # Log alert
            logger.warning(f"ALERT [{alert.level.value.upper()}]: {alert.message}")

            from .alert_notifications import send_push_notification

            alert_details = {
                "threshold": alert.threshold,
                "current_value": alert.current_value,
                "model_name": alert.model_name or "",
            }
            email_sent = send_email_alert(
                alert.level.value,
                alert.metric_name,
                alert.message,
                alert.timestamp,
                alert_details,
            )
            slack_sent = send_slack_alert(
                alert.level.value,
                alert.metric_name,
                alert.message,
                alert.timestamp,
                alert_details,
            )
            push_sent = send_push_notification(
                title=f"[{alert.level.value.upper()}] {alert.metric_name}",
                body=alert.message,
                priority="high" if alert.level == AlertLevel.CRITICAL else "normal",
                data={
                    "metric": alert.metric_name,
                    "level": alert.level.value,
                    "threshold": alert.threshold,
                    "current_value": alert.current_value,
                    "model_name": alert.model_name or "",
                },
            )

            logger.info(
                "Alert notifications sent (email=%s, slack=%s, push=%s)",
                email_sent,
                slack_sent,
                push_sent,
            )
        except Exception as e:
            logger.error(f"Error sending alert: {e}")

    def get_metrics(
        self,
        metric_type: Optional[MetricType] = None,
        model_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[Metric]:
        """
        Get metrics from database
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            query = "SELECT * FROM metrics WHERE 1=1"
            params: List[Any] = []

            if metric_type:
                query += " AND metric_type = ?"
                params.append(metric_type.value)
            if model_name:
                query += " AND model_name = ?"
                params.append(model_name)
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time.isoformat())
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time.isoformat())

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            metrics: List[Metric] = []
            for row in rows:
                metric = Metric(
                    name=row[1],
                    value=row[2],
                    metric_type=MetricType(row[3]),
                    timestamp=datetime.fromisoformat(row[4]),
                    model_name=row[5],
                    metadata=json.loads(row[6]) if row[6] else None,
                )
                metrics.append(metric)

            conn.close()
            return metrics
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return []

    def get_alerts(
        self,
        level: Optional[AlertLevel] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[Alert]:
        """
        Get alerts from database
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            query = "SELECT * FROM alerts WHERE 1=1"
            params: List[Any] = []

            if level:
                query += " AND level = ?"
                params.append(level.value)
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time.isoformat())
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time.isoformat())

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            alerts: List[Alert] = []
            for row in rows:
                alert = Alert(
                    level=AlertLevel(row[1]),
                    message=row[2],
                    metric_name=row[3],
                    timestamp=datetime.fromisoformat(row[4]),
                    threshold=row[5],
                    current_value=row[6],
                    model_name=row[7],
                )
                alerts.append(alert)

            conn.close()
            return alerts
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return []

    def get_model_performance(
        self,
        model_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[ModelPerformance]:
        """
        Get model performance history
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            query = "SELECT * FROM model_performance WHERE model_name = ?"
            params: List[Any] = [model_name]

            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time.isoformat())
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time.isoformat())

            query += " ORDER BY timestamp DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()

            performances: List[ModelPerformance] = []
            for row in rows:
                performance = ModelPerformance(
                    model_name=row[1],
                    accuracy=row[2],
                    precision=row[3],
                    recall=row[4],
                    f1_score=row[5],
                    mse=row[6],
                    mae=row[7],
                    timestamp=datetime.fromisoformat(row[8]),
                    training_samples=row[9],
                    validation_samples=row[10],
                )
                performances.append(performance)

            conn.close()
            return performances
        except Exception as e:
            logger.error(f"Error getting model performance: {e}")
            return []

    def get_performance_summary(self, model_name: str, days: int = 30) -> Dict[str, Any]:
        """
        Get performance summary for a model
        """
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            performances = self.get_model_performance(model_name, start_time, end_time)
            if not performances:
                return {}

            accuracies = [p.accuracy for p in performances]
            precisions = [p.precision for p in performances]
            recalls = [p.recall for p in performances]
            f1_scores = [p.f1_score for p in performances]
            mses = [p.mse for p in performances]
            maes = [p.mae for p in performances]

            summary = {
                "model_name": model_name,
                "period_days": days,
                "total_evaluations": len(performances),
                "latest_evaluation": performances[0].timestamp.isoformat(),
                "accuracy": {
                    "current": accuracies[0],
                    "average": np.mean(accuracies),
                    "min": np.min(accuracies),
                    "max": np.max(accuracies),
                    "trend": "improving" if accuracies[0] > np.mean(accuracies) else "declining",
                },
                "precision": {
                    "current": precisions[0],
                    "average": np.mean(precisions),
                    "min": np.min(precisions),
                    "max": np.max(precisions),
                },
                "recall": {
                    "current": recalls[0],
                    "average": np.mean(recalls),
                    "min": np.min(recalls),
                    "max": np.max(recalls),
                },
                "f1_score": {
                    "current": f1_scores[0],
                    "average": np.mean(f1_scores),
                    "min": np.min(f1_scores),
                    "max": np.max(f1_scores),
                },
                "mse": {
                    "current": mses[0],
                    "average": np.mean(mses),
                    "min": np.min(mses),
                    "max": np.max(mses),
                },
                "mae": {
                    "current": maes[0],
                    "average": np.mean(maes),
                    "min": np.min(maes),
                    "max": np.max(maes),
                },
            }
            return summary
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {}

    def set_threshold(self, metric_name: str, threshold: float) -> None:
        """Set threshold for a metric"""
        if metric_name in self.thresholds:
            self.thresholds[metric_name] = threshold
            logger.info(f"Threshold for {metric_name} set to {threshold}")
        else:
            logger.warning(f"Unknown threshold: {metric_name}")

    def get_thresholds(self) -> Dict[str, float]:
        """Get current thresholds"""
        return self.thresholds.copy()

    def export_metrics(
        self,
        filepath: str,
        metric_type: Optional[MetricType] = None,
        model_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> None:
        """
        Export metrics to CSV file
        """
        try:
            metrics = self.get_metrics(metric_type, model_name, start_time, end_time)
            if not metrics:
                logger.warning("No metrics to export")
                return

            data = []
            for metric in metrics:
                data.append(
                    {
                        "name": metric.name,
                        "value": metric.value,
                        "metric_type": metric.metric_type.value,
                        "timestamp": metric.timestamp,
                        "model_name": metric.model_name,
                        "metadata": json.dumps(metric.metadata) if metric.metadata else None,
                    }
                )
            df = pd.DataFrame(data)
            df.to_csv(filepath, index=False)
            logger.info(f"Exported {len(metrics)} metrics to {filepath}")
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")

    def cleanup_old_data(self, days_to_keep: int = 90) -> None:
        """
        Clean up old monitoring data
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=days_to_keep)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM metrics WHERE timestamp < ?", (cutoff_time.isoformat(),))
            metrics_deleted = cursor.rowcount

            cursor.execute("DELETE FROM alerts WHERE timestamp < ?", (cutoff_time.isoformat(),))
            alerts_deleted = cursor.rowcount

            cursor.execute(
                "DELETE FROM model_performance WHERE timestamp < ?",
                (cutoff_time.isoformat(),),
            )
            performance_deleted = cursor.rowcount

            conn.commit()
            conn.close()
            logger.info(
                "Cleaned up old data: %s metrics, %s alerts, %s performance records",
                metrics_deleted,
                alerts_deleted,
                performance_deleted,
            )
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        try:
            recent_metrics = self.get_metrics(limit=100)
            recent_alerts = self.get_alerts(limit=50)

            system_metrics = [m for m in recent_metrics if m.metric_type == MetricType.SYSTEM_HEALTH]
            status = {
                "monitoring_active": self.monitoring_active,
                "database_path": self.db_path,
                "total_metrics_stored": len(recent_metrics),
                "total_alerts_stored": len(recent_alerts),
                "system_health": {
                    "memory_usage": "unknown",
                    "cpu_usage": "unknown",
                    "disk_usage": "unknown",
                },
                "recent_alerts": len(
                    [a for a in recent_alerts if a.timestamp > datetime.now() - timedelta(hours=1)]
                ),
                "thresholds": self.thresholds,
            }

            for metric in system_metrics:
                if "memory" in metric.name:
                    status["system_health"]["memory_usage"] = f"{metric.value:.1%}"
                elif "cpu" in metric.name:
                    status["system_health"]["cpu_usage"] = f"{metric.value:.1%}"
                elif "disk" in metric.name:
                    status["system_health"]["disk_usage"] = f"{metric.value:.1%}"

            return status
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {"error": str(e)}
