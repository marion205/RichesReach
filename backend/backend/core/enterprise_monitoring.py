"""
Enterprise Monitoring System
Comprehensive monitoring and metrics collection for enterprise-level observability
"""
import time
import psutil
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
from django.core.cache import cache
from django.db import connection
from django.conf import settings
import logging
import json

from .enterprise_config import config
from .enterprise_logging import get_enterprise_logger


class MetricType(Enum):
    """Metric types"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertLevel(Enum):
    """Alert levels"""
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
    tags: Dict[str, str]
    unit: Optional[str] = None


@dataclass
class Alert:
    """Alert data structure"""
    name: str
    level: AlertLevel
    message: str
    timestamp: datetime
    metric_name: str
    threshold: float
    current_value: float
    resolved: bool = False


class PerformanceMonitor:
    """Performance monitoring system"""
    
    def __init__(self):
        self.logger = get_enterprise_logger('performance_monitor')
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.alerts: List[Alert] = []
        self.alert_thresholds = self._load_alert_thresholds()
        self.monitoring_thread = None
        self.is_monitoring = False
    
    def _load_alert_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Load alert thresholds from configuration"""
        return {
            'cpu_usage': {'warning': 70.0, 'critical': 90.0},
            'memory_usage': {'warning': 80.0, 'critical': 95.0},
            'disk_usage': {'warning': 85.0, 'critical': 95.0},
            'response_time': {'warning': 1000.0, 'critical': 5000.0},
            'error_rate': {'warning': 5.0, 'critical': 10.0},
            'database_connections': {'warning': 15, 'critical': 18}
        }
    
    def start_monitoring(self):
        """Start background monitoring"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            self.logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        self.logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.is_monitoring:
            try:
                self._collect_system_metrics()
                self._collect_application_metrics()
                self._check_alerts()
                time.sleep(30)  # Monitor every 30 seconds
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _collect_system_metrics(self):
        """Collect system-level metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_metric('cpu_usage', cpu_percent, MetricType.GAUGE, unit='percent')
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.record_metric('memory_usage', memory.percent, MetricType.GAUGE, unit='percent')
            self.record_metric('memory_available', memory.available, MetricType.GAUGE, unit='bytes')
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.record_metric('disk_usage', disk_percent, MetricType.GAUGE, unit='percent')
            self.record_metric('disk_free', disk.free, MetricType.GAUGE, unit='bytes')
            
            # Network I/O
            net_io = psutil.net_io_counters()
            self.record_metric('network_bytes_sent', net_io.bytes_sent, MetricType.COUNTER, unit='bytes')
            self.record_metric('network_bytes_recv', net_io.bytes_recv, MetricType.COUNTER, unit='bytes')
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
    
    def _collect_application_metrics(self):
        """Collect application-level metrics"""
        try:
            # Database connections
            db_connections = len(connection.queries)
            self.record_metric('database_connections', db_connections, MetricType.GAUGE)
            
            # Cache hit rate
            cache_stats = cache.get('cache_stats', {'hits': 0, 'misses': 0})
            total_requests = cache_stats['hits'] + cache_stats['misses']
            if total_requests > 0:
                hit_rate = (cache_stats['hits'] / total_requests) * 100
                self.record_metric('cache_hit_rate', hit_rate, MetricType.GAUGE, unit='percent')
            
            # Active users (if available)
            active_users = cache.get('active_users', 0)
            self.record_metric('active_users', active_users, MetricType.GAUGE)
            
        except Exception as e:
            self.logger.error(f"Error collecting application metrics: {e}")
    
    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType,
        tags: Optional[Dict[str, str]] = None,
        unit: Optional[str] = None
    ):
        """Record a metric"""
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            timestamp=datetime.utcnow(),
            tags=tags or {},
            unit=unit
        )
        
        self.metrics[name].append(metric)
        
        # Store in cache for real-time access
        self._store_metric_in_cache(metric)
    
    def _store_metric_in_cache(self, metric: Metric):
        """Store metric in cache"""
        try:
            cache_key = f"metric:{metric.name}"
            recent_metrics = cache.get(cache_key, [])
            recent_metrics.append(asdict(metric))
            
            # Keep only last 100 metrics
            if len(recent_metrics) > 100:
                recent_metrics = recent_metrics[-100:]
            
            cache.set(cache_key, recent_metrics, timeout=3600)  # 1 hour
        except Exception as e:
            self.logger.error(f"Failed to store metric in cache: {e}")
    
    def get_metric_history(self, name: str, hours: int = 1) -> List[Metric]:
        """Get metric history"""
        if name not in self.metrics:
            return []
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [metric for metric in self.metrics[name] if metric.timestamp >= cutoff_time]
    
    def get_metric_summary(self, name: str, hours: int = 1) -> Dict[str, Any]:
        """Get metric summary statistics"""
        history = self.get_metric_history(name, hours)
        
        if not history:
            return {}
        
        values = [metric.value for metric in history]
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'latest': values[-1] if values else None,
            'unit': history[0].unit if history else None
        }
    
    def _check_alerts(self):
        """Check for alert conditions"""
        for metric_name, thresholds in self.alert_thresholds.items():
            try:
                latest_metrics = self.get_metric_history(metric_name, hours=0.1)  # Last 6 minutes
                if not latest_metrics:
                    continue
                
                current_value = latest_metrics[-1].value
                
                # Check warning threshold
                if current_value >= thresholds.get('warning', float('inf')):
                    self._create_alert(
                        metric_name,
                        AlertLevel.WARNING,
                        f"{metric_name} is {current_value:.2f}, above warning threshold {thresholds['warning']}",
                        current_value,
                        thresholds['warning']
                    )
                
                # Check critical threshold
                if current_value >= thresholds.get('critical', float('inf')):
                    self._create_alert(
                        metric_name,
                        AlertLevel.CRITICAL,
                        f"{metric_name} is {current_value:.2f}, above critical threshold {thresholds['critical']}",
                        current_value,
                        thresholds['critical']
                    )
            
            except Exception as e:
                self.logger.error(f"Error checking alerts for {metric_name}: {e}")
    
    def _create_alert(
        self,
        metric_name: str,
        level: AlertLevel,
        message: str,
        current_value: float,
        threshold: float
    ):
        """Create an alert"""
        # Check if alert already exists and is not resolved
        existing_alert = None
        for alert in self.alerts:
            if (alert.metric_name == metric_name and 
                alert.level == level and 
                not alert.resolved):
                existing_alert = alert
                break
        
        if existing_alert:
            return  # Alert already exists
        
        alert = Alert(
            name=f"{metric_name}_{level.value}",
            level=level,
            message=message,
            timestamp=datetime.utcnow(),
            metric_name=metric_name,
            threshold=threshold,
            current_value=current_value
        )
        
        self.alerts.append(alert)
        
        # Log alert
        self.logger.error(
            f"Alert: {message}",
            extra_data={
                'alert_name': alert.name,
                'level': level.value,
                'metric_name': metric_name,
                'current_value': current_value,
                'threshold': threshold
            }
        )
        
        # Store in cache
        self._store_alert_in_cache(alert)
    
    def _store_alert_in_cache(self, alert: Alert):
        """Store alert in cache"""
        try:
            cache_key = "recent_alerts"
            recent_alerts = cache.get(cache_key, [])
            recent_alerts.append(asdict(alert))
            
            # Keep only last 50 alerts
            if len(recent_alerts) > 50:
                recent_alerts = recent_alerts[-50:]
            
            cache.set(cache_key, recent_alerts, timeout=3600)  # 1 hour
        except Exception as e:
            self.logger.error(f"Failed to store alert in cache: {e}")
    
    def resolve_alert(self, alert_name: str):
        """Resolve an alert"""
        for alert in self.alerts:
            if alert.name == alert_name and not alert.resolved:
                alert.resolved = True
                self.logger.info(f"Alert resolved: {alert_name}")
                break
    
    def get_active_alerts(self) -> List[Alert]:
        """Get active (unresolved) alerts"""
        return [alert for alert in self.alerts if not alert.resolved]
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary"""
        active_alerts = self.get_active_alerts()
        
        summary = {
            'total_alerts': len(active_alerts),
            'by_level': defaultdict(int),
            'by_metric': defaultdict(int)
        }
        
        for alert in active_alerts:
            summary['by_level'][alert.level.value] += 1
            summary['by_metric'][alert.metric_name] += 1
        
        return dict(summary)


class DatabaseMonitor:
    """Database performance monitoring"""
    
    def __init__(self):
        self.logger = get_enterprise_logger('database_monitor')
    
    def get_query_stats(self) -> Dict[str, Any]:
        """Get database query statistics"""
        try:
            queries = connection.queries
            total_queries = len(queries)
            
            if total_queries == 0:
                return {'total_queries': 0, 'total_time': 0, 'avg_time': 0}
            
            total_time = sum(float(query['time']) for query in queries)
            avg_time = total_time / total_queries
            
            # Find slow queries
            slow_queries = [q for q in queries if float(q['time']) > 1.0]  # > 1 second
            
            return {
                'total_queries': total_queries,
                'total_time': total_time,
                'avg_time': avg_time,
                'slow_queries': len(slow_queries),
                'slowest_query': max(queries, key=lambda q: float(q['time'])) if queries else None
            }
        
        except Exception as e:
            self.logger.error(f"Error getting query stats: {e}")
            return {}
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get database connection statistics"""
        try:
            # This would need to be implemented based on your database setup
            return {
                'active_connections': 1,  # Placeholder
                'max_connections': 20,   # From config
                'connection_usage': 5.0  # Placeholder
            }
        except Exception as e:
            self.logger.error(f"Error getting connection stats: {e}")
            return {}


class APIMonitor:
    """API performance monitoring"""
    
    def __init__(self):
        self.logger = get_enterprise_logger('api_monitor')
        self.request_times = deque(maxlen=1000)
        self.error_counts = defaultdict(int)
    
    def record_request(self, endpoint: str, method: str, status_code: int, response_time: float):
        """Record API request"""
        self.request_times.append({
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'response_time': response_time,
            'timestamp': datetime.utcnow()
        })
        
        if status_code >= 400:
            self.error_counts[f"{method} {endpoint}"] += 1
    
    def get_api_stats(self) -> Dict[str, Any]:
        """Get API statistics"""
        if not self.request_times:
            return {}
        
        response_times = [req['response_time'] for req in self.request_times]
        
        return {
            'total_requests': len(self.request_times),
            'avg_response_time': sum(response_times) / len(response_times),
            'max_response_time': max(response_times),
            'min_response_time': min(response_times),
            'error_count': sum(self.error_counts.values()),
            'error_rate': sum(self.error_counts.values()) / len(self.request_times) * 100
        }
    
    def get_endpoint_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics by endpoint"""
        endpoint_stats = defaultdict(lambda: {'count': 0, 'total_time': 0, 'errors': 0})
        
        for req in self.request_times:
            key = f"{req['method']} {req['endpoint']}"
            endpoint_stats[key]['count'] += 1
            endpoint_stats[key]['total_time'] += req['response_time']
            if req['status_code'] >= 400:
                endpoint_stats[key]['errors'] += 1
        
        # Calculate averages
        for stats in endpoint_stats.values():
            if stats['count'] > 0:
                stats['avg_time'] = stats['total_time'] / stats['count']
                stats['error_rate'] = stats['errors'] / stats['count'] * 100
        
        return dict(endpoint_stats)


class HealthChecker:
    """System health checker"""
    
    def __init__(self):
        self.logger = get_enterprise_logger('health_checker')
        self.performance_monitor = PerformanceMonitor()
        self.database_monitor = DatabaseMonitor()
        self.api_monitor = APIMonitor()
    
    def check_system_health(self) -> Dict[str, Any]:
        """Check overall system health"""
        health_status = {
            'overall_status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {}
        }
        
        # Check system resources
        health_status['checks']['system'] = self._check_system_resources()
        
        # Check database
        health_status['checks']['database'] = self._check_database()
        
        # Check cache
        health_status['checks']['cache'] = self._check_cache()
        
        # Check API performance
        health_status['checks']['api'] = self._check_api_performance()
        
        # Determine overall status
        failed_checks = [name for name, check in health_status['checks'].items() if not check['healthy']]
        if failed_checks:
            health_status['overall_status'] = 'unhealthy'
            health_status['failed_checks'] = failed_checks
        
        return health_status
    
    def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            healthy = (
                cpu_percent < 90 and
                memory.percent < 95 and
                (disk.used / disk.total) < 0.95
            )
            
            return {
                'healthy': healthy,
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'disk_usage': (disk.used / disk.total) * 100
            }
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            # Get query stats
            query_stats = self.database_monitor.get_query_stats()
            
            healthy = query_stats.get('avg_time', 0) < 1.0  # Average query time < 1 second
            
            return {
                'healthy': healthy,
                'query_stats': query_stats
            }
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    def _check_cache(self) -> Dict[str, Any]:
        """Check cache functionality"""
        try:
            test_key = 'health_check_test'
            test_value = 'test_value'
            
            # Test cache write
            cache.set(test_key, test_value, timeout=60)
            
            # Test cache read
            retrieved_value = cache.get(test_key)
            
            # Clean up
            cache.delete(test_key)
            
            healthy = retrieved_value == test_value
            
            return {
                'healthy': healthy,
                'test_passed': retrieved_value == test_value
            }
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    def _check_api_performance(self) -> Dict[str, Any]:
        """Check API performance"""
        try:
            api_stats = self.api_monitor.get_api_stats()
            
            if not api_stats:
                return {'healthy': True, 'message': 'No API requests recorded'}
            
            healthy = (
                api_stats.get('avg_response_time', 0) < 2.0 and  # Average response time < 2 seconds
                api_stats.get('error_rate', 0) < 5.0  # Error rate < 5%
            )
            
            return {
                'healthy': healthy,
                'stats': api_stats
            }
        except Exception as e:
            return {'healthy': False, 'error': str(e)}


# Global monitoring instances
performance_monitor = PerformanceMonitor()
database_monitor = DatabaseMonitor()
api_monitor = APIMonitor()
health_checker = HealthChecker()
