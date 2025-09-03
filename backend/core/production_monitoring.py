"""
Production Monitoring Service for Live Market Intelligence
Continuous performance tracking, alerting, and optimization
"""

import os
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str]
    metadata: Dict[str, Any]

@dataclass
class Alert:
    """Alert data structure"""
    name: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    timestamp: datetime
    metric_name: str
    threshold: float
    current_value: float
    status: str  # 'active', 'resolved'

class ProductionMonitoringService:
    """
    Production monitoring service for continuous performance tracking
    """
    
    def __init__(self):
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.namespace = os.getenv('CLOUDWATCH_NAMESPACE', 'RichesReach/AIService')
        
        # Initialize AWS clients
        try:
            self.cloudwatch = boto3.client('cloudwatch', region_name=self.aws_region)
            self.sns = boto3.client('sns', region_name=self.aws_region)
            logger.info("AWS monitoring clients initialized")
        except Exception as e:
            logger.warning(f"AWS monitoring clients not available: {e}")
            self.cloudwatch = None
            self.sns = None
        
        # Initialize metrics storage
        self.metrics_buffer = []
        self.alerts = []
        self.alert_history = []
        
        # Load configuration
        self.load_config()
        
        logger.info("Production Monitoring Service initialized")
    
    def _load_alert_thresholds(self) -> Dict[str, Dict[str, Any]]:
        """Load alert thresholds from configuration"""
        return {
            'APIRequests': {
                'high_latency': {'threshold': 1000, 'unit': 'ms', 'severity': 'medium'},
                'low_throughput': {'threshold': 10, 'unit': 'requests/min', 'severity': 'high'}
            },
            'ModelAccuracy': {
                'low_accuracy': {'threshold': 0.8, 'unit': 'percent', 'severity': 'critical'},
                'accuracy_drop': {'threshold': 0.05, 'unit': 'percent', 'severity': 'high'}
            },
            'DataQuality': {
                'low_quality': {'threshold': 0.7, 'unit': 'score', 'severity': 'high'},
                'data_freshness': {'threshold': 300, 'unit': 'seconds', 'severity': 'medium'}
            },
            'SystemHealth': {
                'high_cpu': {'threshold': 80, 'unit': 'percent', 'severity': 'medium'},
                'high_memory': {'threshold': 85, 'unit': 'percent', 'severity': 'medium'},
                'disk_usage': {'threshold': 90, 'unit': 'percent', 'severity': 'high'}
            }
        }
    
    def record_metric(self, name: str, value: float, unit: str, 
                     tags: Dict[str, str] = None, metadata: Dict[str, Any] = None):
        """Record a performance metric"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            tags=tags or {},
            metadata=metadata or {}
        )
        
        # Add to buffer
        self.metrics_buffer.append(metric)
        
        # Store in history
        if name not in self.performance_history:
            self.performance_history[name] = []
        self.performance_history[name].append(metric)
        
        # Keep only recent history
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.performance_history[name] = [
            m for m in self.performance_history[name] 
            if m.timestamp > cutoff_time
        ]
        
        # Check for alerts
        self._check_alerts(metric)
        
        # Flush buffer if full
        if len(self.metrics_buffer) >= self.buffer_size:
            self._flush_metrics()
    
    def _check_alerts(self, metric: PerformanceMetric):
        """Check if metric triggers any alerts"""
        if metric.name not in self.alert_thresholds:
            return
        
        thresholds = self.alert_thresholds[metric.name]
        
        for alert_name, config in thresholds.items():
            threshold = config['threshold']
            severity = config['severity']
            
            # Check if threshold is exceeded
            if self._is_threshold_exceeded(metric, threshold, alert_name):
                alert = Alert(
                    name=f"{metric.name}_{alert_name}",
                    severity=severity,
                    message=f"{metric.name} exceeded {alert_name} threshold: {metric.value} {metric.unit} > {threshold}",
                    timestamp=datetime.now(),
                    metric_name=metric.name,
                    threshold=threshold,
                    current_value=metric.value,
                    status='active'
                )
                
                self.alerts_buffer.append(alert)
                logger.warning(f"ALERT: {alert.message}")
                
                # Send alert if AWS is available
                if self.sns:
                    self._send_sns_alert(alert)
    
    def _is_threshold_exceeded(self, metric: PerformanceMetric, threshold: float, alert_type: str) -> bool:
        """Check if metric exceeds threshold based on alert type"""
        if alert_type in ['high_latency', 'high_cpu', 'high_memory', 'disk_usage']:
            return metric.value > threshold
        elif alert_type in ['low_accuracy', 'low_quality']:
            return metric.value < threshold
        elif alert_type == 'accuracy_drop':
            # Check if accuracy dropped by threshold amount
            if len(self.performance_history[metric.name]) < 2:
                return False
            previous = self.performance_history[metric.name][-2].value
            return (previous - metric.value) > threshold
        else:
            return False
    
    def _send_sns_alert(self, alert: Alert):
        """Send alert via SNS"""
        try:
            topic_arn = os.getenv('SNS_TOPIC_ARN')
            if not topic_arn:
                logger.warning("SNS_TOPIC_ARN not configured")
                return
            
            message = {
                'alert_name': alert.name,
                'severity': alert.severity,
                'message': alert.message,
                'timestamp': alert.timestamp.isoformat(),
                'metric_name': alert.metric_name,
                'threshold': alert.threshold,
                'current_value': alert.current_value
            }
            
            self.sns.publish(
                TopicArn=topic_arn,
                Message=json.dumps(message),
                Subject=f"Alert: {alert.severity.upper()} Alert: {alert.name}"
            )
            
            logger.info(f"SNS alert sent: {alert.name}")
            
        except Exception as e:
            logger.error(f"Failed to send SNS alert: {e}")
    
    def _flush_metrics(self):
        """Flush metrics buffer to CloudWatch"""
        if not self.cloudwatch or not self.metrics_buffer:
            return
        
        try:
            # Prepare CloudWatch metrics
            cloudwatch_metrics = []
            
            for metric in self.metrics_buffer:
                cloudwatch_metric = {
                    'MetricName': metric.name,
                    'Value': metric.value,
                    'Unit': metric.unit,
                    'Timestamp': metric.timestamp,
                    'Dimensions': [
                        {'Name': 'Service', 'Value': 'AI-Market-Intelligence'},
                        {'Name': 'Environment', 'Value': 'production'}
                    ]
                }
                
                # Add custom tags as dimensions
                for key, value in metric.tags.items():
                    cloudwatch_metric['Dimensions'].append({
                        'Name': key,
                        'Value': str(value)
                    })
                
                cloudwatch_metrics.append(cloudwatch_metric)
            
            # Send to CloudWatch
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=cloudwatch_metrics
            )
            
            logger.info(f"Flushed {len(cloudwatch_metrics)} metrics to CloudWatch")
            
            # Clear buffer
            self.metrics_buffer.clear()
            
        except Exception as e:
            logger.error(f"Failed to flush metrics to CloudWatch: {e}")
    
    def record_api_performance(self, endpoint: str, response_time: float, 
                             status_code: int, user_id: str = None):
        """Record API performance metrics"""
        # Response time metric
        self.record_metric(
            name='APIResponseTime',
            value=response_time,
            unit='Milliseconds',
            tags={
                'endpoint': endpoint,
                'status_code': str(status_code)
            },
            metadata={'user_id': user_id}
        )
        
        # Request count metric
        self.record_metric(
            name='APIRequestCount',
            value=1,
            unit='Count',
            tags={
                'endpoint': endpoint,
                'status_code': str(status_code)
            }
        )
        
        # Throughput metric (requests per minute)
        self._calculate_throughput(endpoint)
    
    def _calculate_throughput(self, endpoint: str):
        """Calculate requests per minute for endpoint"""
        now = datetime.now()
        cutoff = now - timedelta(minutes=1)
        
        # Count requests in last minute
        recent_requests = [
            m for m in self.performance_history.get('APIRequestCount', [])
            if m.timestamp > cutoff and m.tags.get('endpoint') == endpoint
        ]
        
        throughput = len(recent_requests)
        
        self.record_metric(
            name='APIThroughput',
            value=throughput,
            unit='Count',
            tags={'endpoint': endpoint}
        )
    
    def record_model_performance(self, model_name: str, accuracy: float, 
                               prediction_time: float, data_quality: float):
        """Record ML model performance metrics"""
        # Model accuracy
        self.record_metric(
            name='ModelAccuracy',
            value=accuracy,
            unit='Percent',
            tags={'model_name': model_name}
        )
        
        # Prediction latency
        self.record_metric(
            name='ModelPredictionTime',
            value=prediction_time,
            unit='Milliseconds',
            tags={'model_name': model_name}
        )
        
        # Data quality score
        self.record_metric(
            name='DataQualityScore',
            value=data_quality,
            unit='None',
            tags={'model_name': model_name}
        )
        
        # Check for model drift
        self._check_model_drift(model_name, accuracy)
    
    def _check_model_drift(self, model_name: str, current_accuracy: float):
        """Check for model accuracy drift"""
        if model_name not in self.performance_history.get('ModelAccuracy', []):
            return
        
        # Get historical accuracy for this model
        model_metrics = [
            m for m in self.performance_history['ModelAccuracy']
            if m.tags.get('model_name') == model_name
        ]
        
        if len(model_metrics) < 10:  # Need enough data
            return
        
        # Calculate average accuracy over last 24 hours
        recent_metrics = model_metrics[-10:]
        avg_accuracy = sum(m.value for m in recent_metrics) / len(recent_metrics)
        
        # Check if current accuracy dropped significantly
        accuracy_drop = avg_accuracy - current_accuracy
        
        if accuracy_drop > 0.05:  # 5% drop
            self.record_metric(
                name='ModelDrift',
                value=accuracy_drop,
                unit='Percent',
                tags={'model_name': model_name},
                metadata={'avg_accuracy': avg_accuracy, 'current_accuracy': current_accuracy}
            )
    
    def record_market_data_quality(self, data_source: str, freshness: float, 
                                 completeness: float, accuracy: float):
        """Record market data quality metrics"""
        # Data freshness (seconds since last update)
        self.record_metric(
            name='DataFreshness',
            value=freshness,
            unit='Seconds',
            tags={'data_source': data_source}
        )
        
        # Data completeness
        self.record_metric(
            name='DataCompleteness',
            value=completeness,
            unit='Percent',
            tags={'data_source': data_source}
        )
        
        # Data accuracy
        self.record_metric(
            name='DataAccuracy',
            value=accuracy,
            unit='None',
            tags={'data_source': data_source}
        )
        
        # Overall data quality score
        overall_quality = (freshness + completeness + accuracy) / 3
        self.record_metric(
            name='OverallDataQuality',
            value=overall_quality,
            unit='None',
            tags={'data_source': data_source}
        )
    
    def record_system_health(self, cpu_usage: float, memory_usage: float, 
                           disk_usage: float, active_connections: int):
        """Record system health metrics"""
        # CPU usage
        self.record_metric(
            name='CPUUsage',
            value=cpu_usage,
            unit='Percent'
        )
        
        # Memory usage
        self.record_metric(
            name='MemoryUsage',
            value=memory_usage,
            unit='Percent'
        )
        
        # Disk usage
        self.record_metric(
            name='DiskUsage',
            value=disk_usage,
            unit='Percent'
        )
        
        # Active connections
        self.record_metric(
            name='ActiveConnections',
            value=active_connections,
            unit='Count'
        )
    
    def get_performance_summary(self, metric_name: str = None, 
                              hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for metrics"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        if metric_name:
            metrics = self.performance_history.get(metric_name, [])
        else:
            # Get all metrics
            all_metrics = []
            for metric_list in self.performance_history.values():
                all_metrics.extend(metric_list)
            metrics = all_metrics
        
        # Filter by time
        recent_metrics = [m for m in metrics if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return {"error": "No metrics found for specified time period"}
        
        # Calculate statistics
        values = [m.value for m in recent_metrics]
        
        summary = {
            "metric_name": metric_name or "all",
            "time_period_hours": hours,
            "total_metrics": len(recent_metrics),
            "statistics": {
                "min": min(values),
                "max": max(values),
                "average": sum(values) / len(values),
                "latest": recent_metrics[-1].value
            },
            "alerts": len([a for a in self.alerts_buffer if a.status == 'active']),
            "last_updated": recent_metrics[-1].timestamp.isoformat()
        }
        
        return summary
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return [alert for alert in self.alerts_buffer if alert.status == 'active']
    
    def resolve_alert(self, alert_name: str):
        """Mark an alert as resolved"""
        for alert in self.alerts_buffer:
            if alert.name == alert_name:
                alert.status = 'resolved'
                alert.timestamp = datetime.now()
                logger.info(f"Alert resolved: {alert_name}")
                break
    
    def create_cloudwatch_dashboard(self):
        """Create CloudWatch dashboard for monitoring"""
        if not self.cloudwatch:
            logger.warning("CloudWatch not available")
            return None
        
        try:
            dashboard_body = {
                "widgets": [
                    {
                        "type": "metric",
                        "x": 0,
                        "y": 0,
                        "width": 12,
                        "height": 6,
                        "properties": {
                            "metrics": [
                                [self.namespace, "APIResponseTime"],
                                [self.namespace, "APIRequestCount"]
                            ],
                            "period": 300,
                            "stat": "Average",
                            "region": self.aws_region,
                            "title": "API Performance"
                        }
                    },
                    {
                        "type": "metric",
                        "x": 12,
                        "y": 0,
                        "width": 12,
                        "height": 6,
                        "properties": {
                            "metrics": [
                                [self.namespace, "ModelAccuracy"],
                                [self.namespace, "ModelPredictionTime"]
                            ],
                            "period": 300,
                            "stat": "Average",
                            "region": self.aws_region,
                            "title": "ML Model Performance"
                        }
                    },
                    {
                        "type": "metric",
                        "x": 0,
                        "y": 6,
                        "width": 12,
                        "height": 6,
                        "properties": {
                            "metrics": [
                                [self.namespace, "DataQualityScore"],
                                [self.namespace, "DataFreshness"]
                            ],
                            "period": 300,
                            "stat": "Average",
                            "region": self.aws_region,
                            "title": "Data Quality"
                        }
                    },
                    {
                        "type": "metric",
                        "x": 12,
                        "y": 6,
                        "width": 12,
                        "height": 6,
                        "properties": {
                            "metrics": [
                                [self.namespace, "CPUUsage"],
                                [self.namespace, "MemoryUsage"]
                            ],
                            "period": 300,
                            "stat": "Average",
                            "region": self.aws_region,
                            "title": "System Health"
                        }
                    }
                ]
            }
            
            dashboard_name = f"{self.namespace.replace('/', '-')}-Dashboard"
            
            self.cloudwatch.put_dashboard(
                DashboardName=dashboard_name,
                DashboardBody=json.dumps(dashboard_body)
            )
            
            logger.info(f"CloudWatch dashboard created: {dashboard_name}")
            return dashboard_name
            
        except Exception as e:
            logger.error(f"Failed to create CloudWatch dashboard: {e}")
            return None
    
    def start_monitoring(self):
        """Start continuous monitoring"""
        logger.info("Starting continuous monitoring...")
        
        # Create CloudWatch dashboard
        self.create_cloudwatch_dashboard()
        
        # Start periodic metric flushing
        import threading
        import time
        
        def flush_loop():
            while True:
                time.sleep(self.metrics_interval)
                self._flush_metrics()
        
        flush_thread = threading.Thread(target=flush_loop, daemon=True)
        flush_thread.start()
        
        logger.info(f"Continuous monitoring started (flush interval: {self.metrics_interval}s)")
    
    def stop_monitoring(self):
        """Stop monitoring and flush remaining metrics"""
        logger.info("Stopping monitoring service...")
        
        # Flush remaining metrics
        self._flush_metrics()
        
        logger.info("Monitoring service stopped")

# Global monitoring instance
monitoring_service = ProductionMonitoringService()
