"""
Comprehensive Monitoring and Alerting Service
Handles metrics collection, health checks, and alerting
"""
import logging
import time
import json
import psutil
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from .ml_settings import get_monitoring_config, is_monitoring_enabled
from .pit_data_service import pit_service, audit_service

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Collects system and application metrics"""
    
    def __init__(self):
        self.config = get_monitoring_config()
        self.enabled = is_monitoring_enabled()
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-level metrics"""
        try:
            return {
                'timestamp': timezone.now().isoformat(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None,
                'process_count': len(psutil.pids()),
                'uptime_seconds': time.time() - psutil.boot_time(),
            }
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}
    
    def get_application_metrics(self) -> Dict[str, Any]:
        """Get application-level metrics"""
        try:
            # Database metrics
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM django_migrations")
                migration_count = cursor.fetchone()[0]
            
            # Cache metrics
            cache_stats = cache.get('monitoring:cache_stats', {})
            
            # ML service metrics
            ml_metrics = self._get_ml_metrics()
            
            # Point-in-time data metrics
            pit_metrics = pit_service.get_data_quality_metrics()
            
            return {
                'timestamp': timezone.now().isoformat(),
                'database': {
                    'migration_count': migration_count,
                    'connection_count': len(connection.queries) if hasattr(connection, 'queries') else 0,
                },
                'cache': cache_stats,
                'ml_service': ml_metrics,
                'point_in_time_data': pit_metrics,
            }
        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")
            return {}
    
    def _get_ml_metrics(self) -> Dict[str, Any]:
        """Get ML service specific metrics"""
        try:
            # Count recent ML mutations
            recent_mutations = audit_service.get_audit_logs(
                action_type='ML_RECOMMENDATION',
                start_date=timezone.now().date() - timedelta(days=1),
                limit=1000
            )
            
            # Count institutional mutations
            institutional_mutations = audit_service.get_audit_logs(
                action_type='INSTITUTIONAL_RECOMMENDATION',
                start_date=timezone.now().date() - timedelta(days=1),
                limit=1000
            )
            
            # Calculate success rates
            ml_success_rate = sum(1 for log in recent_mutations if log.success) / len(recent_mutations) if recent_mutations else 0
            inst_success_rate = sum(1 for log in institutional_mutations if log.success) / len(institutional_mutations) if institutional_mutations else 0
            
            # Calculate average execution times
            ml_avg_time = sum(log.execution_time_ms for log in recent_mutations if log.execution_time_ms) / len([log for log in recent_mutations if log.execution_time_ms]) if recent_mutations else 0
            inst_avg_time = sum(log.execution_time_ms for log in institutional_mutations if log.execution_time_ms) / len([log for log in institutional_mutations if log.execution_time_ms]) if institutional_mutations else 0
            
            return {
                'ml_mutations_24h': len(recent_mutations),
                'institutional_mutations_24h': len(institutional_mutations),
                'ml_success_rate': ml_success_rate,
                'institutional_success_rate': inst_success_rate,
                'ml_avg_execution_time_ms': ml_avg_time,
                'institutional_avg_execution_time_ms': inst_avg_time,
            }
        except Exception as e:
            logger.error(f"Error collecting ML metrics: {e}")
            return {}
    
    def get_business_metrics(self) -> Dict[str, Any]:
        """Get business-level metrics"""
        try:
            # User activity metrics
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            total_users = User.objects.count()
            active_users_24h = User.objects.filter(
                last_login__gte=timezone.now() - timedelta(days=1)
            ).count()
            
            # Portfolio metrics
            from .models import AIPortfolioRecommendation
            total_recommendations = AIPortfolioRecommendation.objects.count()
            recommendations_24h = AIPortfolioRecommendation.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=1)
            ).count()
            
            return {
                'timestamp': timezone.now().isoformat(),
                'users': {
                    'total': total_users,
                    'active_24h': active_users_24h,
                },
                'recommendations': {
                    'total': total_recommendations,
                    'generated_24h': recommendations_24h,
                },
            }
        except Exception as e:
            logger.error(f"Error collecting business metrics: {e}")
            return {}

class HealthChecker:
    """Performs health checks on various components"""
    
    def __init__(self):
        self.config = get_monitoring_config()
        self.enabled = is_monitoring_enabled()
    
    def check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            from django.db import connection
            start_time = time.time()
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                'status': 'healthy' if result and response_time < 1000 else 'degraded',
                'response_time_ms': response_time,
                'error': None
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'response_time_ms': None,
                'error': str(e)
            }
    
    def check_redis_health(self) -> Dict[str, Any]:
        """Check Redis connectivity and performance"""
        try:
            start_time = time.time()
            cache.set('health_check', 'test', 10)
            result = cache.get('health_check')
            response_time = (time.time() - start_time) * 1000
            
            return {
                'status': 'healthy' if result == 'test' and response_time < 100 else 'degraded',
                'response_time_ms': response_time,
                'error': None
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'response_time_ms': None,
                'error': str(e)
            }
    
    def check_ml_service_health(self) -> Dict[str, Any]:
        """Check ML service health"""
        try:
            from .ml_settings import MLServiceStatus
            status = MLServiceStatus.get_health_check()
            
            return {
                'status': status['status'],
                'components': status['components'],
                'error': None
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'components': {},
                'error': str(e)
            }
    
    def check_external_apis_health(self) -> Dict[str, Any]:
        """Check external API health"""
        try:
            api_health = {}
            
            # Check Finnhub API
            try:
                response = requests.get(
                    'https://finnhub.io/api/v1/quote?symbol=AAPL&token=demo',
                    timeout=5
                )
                api_health['finnhub'] = {
                    'status': 'healthy' if response.status_code == 200 else 'degraded',
                    'response_time_ms': response.elapsed.total_seconds() * 1000
                }
            except Exception as e:
                api_health['finnhub'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
            
            # Check Alpha Vantage API
            try:
                response = requests.get(
                    'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey=demo',
                    timeout=5
                )
                api_health['alpha_vantage'] = {
                    'status': 'healthy' if response.status_code == 200 else 'degraded',
                    'response_time_ms': response.elapsed.total_seconds() * 1000
                }
            except Exception as e:
                api_health['alpha_vantage'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
            
            return api_health
        except Exception as e:
            return {'error': str(e)}
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        try:
            database_health = self.check_database_health()
            redis_health = self.check_redis_health()
            ml_health = self.check_ml_service_health()
            api_health = self.check_external_apis_health()
            
            # Determine overall status
            component_statuses = [
                database_health['status'],
                redis_health['status'],
                ml_health['status']
            ]
            
            if 'unhealthy' in component_statuses:
                overall_status = 'unhealthy'
            elif 'degraded' in component_statuses:
                overall_status = 'degraded'
            else:
                overall_status = 'healthy'
            
            return {
                'timestamp': timezone.now().isoformat(),
                'overall_status': overall_status,
                'components': {
                    'database': database_health,
                    'redis': redis_health,
                    'ml_service': ml_health,
                    'external_apis': api_health,
                }
            }
        except Exception as e:
            return {
                'timestamp': timezone.now().isoformat(),
                'overall_status': 'unhealthy',
                'error': str(e)
            }

class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self):
        self.config = get_monitoring_config()
        self.enabled = is_monitoring_enabled()
    
    def check_alerts(self, metrics: Dict[str, Any], health: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for alert conditions"""
        alerts = []
        
        if not self.enabled:
            return alerts
        
        try:
            # System resource alerts
            if 'system' in metrics:
                cpu_percent = metrics['system'].get('cpu_percent', 0)
                memory_percent = metrics['system'].get('memory_percent', 0)
                disk_percent = metrics['system'].get('disk_percent', 0)
                
                if cpu_percent > 90:
                    alerts.append({
                        'type': 'high_cpu',
                        'severity': 'warning',
                        'message': f'High CPU usage: {cpu_percent}%',
                        'timestamp': timezone.now().isoformat()
                    })
                
                if memory_percent > 90:
                    alerts.append({
                        'type': 'high_memory',
                        'severity': 'warning',
                        'message': f'High memory usage: {memory_percent}%',
                        'timestamp': timezone.now().isoformat()
                    })
                
                if disk_percent > 90:
                    alerts.append({
                        'type': 'high_disk',
                        'severity': 'critical',
                        'message': f'High disk usage: {disk_percent}%',
                        'timestamp': timezone.now().isoformat()
                    })
            
            # Health check alerts
            if health.get('overall_status') == 'unhealthy':
                alerts.append({
                    'type': 'system_unhealthy',
                    'severity': 'critical',
                    'message': 'System is unhealthy',
                    'timestamp': timezone.now().isoformat()
                })
            
            # ML service alerts
            if 'ml_service' in metrics:
                ml_success_rate = metrics['ml_service'].get('ml_success_rate', 1.0)
                if ml_success_rate < 0.8:
                    alerts.append({
                        'type': 'low_ml_success_rate',
                        'severity': 'warning',
                        'message': f'Low ML success rate: {ml_success_rate:.2%}',
                        'timestamp': timezone.now().isoformat()
                    })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
            return []
    
    def send_alert(self, alert: Dict[str, Any]) -> bool:
        """Send an alert notification"""
        try:
            # Email alert
            if self.config.get('ALERT_EMAIL'):
                self._send_email_alert(alert)
            
            # Slack alert
            if self.config.get('SLACK_WEBHOOK'):
                self._send_slack_alert(alert)
            
            # Log alert
            logger.warning(f"ALERT: {alert['type']} - {alert['message']}")
            
            return True
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
            return False
    
    def _send_email_alert(self, alert: Dict[str, Any]):
        """Send email alert"""
        try:
            from django.core.mail import send_mail
            
            subject = f"RichesReach Alert: {alert['type']}"
            message = f"""
            Alert Type: {alert['type']}
            Severity: {alert['severity']}
            Message: {alert['message']}
            Timestamp: {alert['timestamp']}
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [self.config['ALERT_EMAIL']],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
    
    def _send_slack_alert(self, alert: Dict[str, Any]):
        """Send Slack alert"""
        try:
            webhook_url = self.config['SLACK_WEBHOOK']
            
            payload = {
                'text': f"🚨 RichesReach Alert",
                'attachments': [{
                    'color': 'danger' if alert['severity'] == 'critical' else 'warning',
                    'fields': [
                        {'title': 'Type', 'value': alert['type'], 'short': True},
                        {'title': 'Severity', 'value': alert['severity'], 'short': True},
                        {'title': 'Message', 'value': alert['message'], 'short': False},
                        {'title': 'Timestamp', 'value': alert['timestamp'], 'short': True},
                    ]
                }]
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")

class MonitoringService:
    """Main monitoring service that orchestrates everything"""
    
    def __init__(self):
        self.config = get_monitoring_config()
        self.enabled = is_monitoring_enabled()
        self.metrics_collector = MetricsCollector()
        self.health_checker = HealthChecker()
        self.alert_manager = AlertManager()
    
    def collect_all_metrics(self) -> Dict[str, Any]:
        """Collect all metrics"""
        if not self.enabled:
            return {}
        
        try:
            return {
                'system': self.metrics_collector.get_system_metrics(),
                'application': self.metrics_collector.get_application_metrics(),
                'business': self.metrics_collector.get_business_metrics(),
            }
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return {}
    
    def perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        if not self.enabled:
            return {'status': 'disabled'}
        
        try:
            return self.health_checker.get_overall_health()
        except Exception as e:
            logger.error(f"Error performing health check: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def check_and_send_alerts(self) -> List[Dict[str, Any]]:
        """Check for alerts and send notifications"""
        if not self.enabled:
            return []
        
        try:
            metrics = self.collect_all_metrics()
            health = self.perform_health_check()
            
            alerts = self.alert_manager.check_alerts(metrics, health)
            
            for alert in alerts:
                self.alert_manager.send_alert(alert)
            
            return alerts
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
            return []
    
    def get_monitoring_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard"""
        try:
            metrics = self.collect_all_metrics()
            health = self.perform_health_check()
            alerts = self.check_and_send_alerts()
            
            return {
                'timestamp': timezone.now().isoformat(),
                'metrics': metrics,
                'health': health,
                'alerts': alerts,
                'config': {
                    'monitoring_enabled': self.enabled,
                    'alert_email': bool(self.config.get('ALERT_EMAIL')),
                    'slack_webhook': bool(self.config.get('SLACK_WEBHOOK')),
                }
            }
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {'error': str(e)}

# Global instances
monitoring_service = MonitoringService()
