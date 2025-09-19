"""
GraphQL Types for Monitoring and Health Checks
"""
import graphene
from graphene_django import DjangoObjectType
from .models import AuditLog, MLModelVersion
from .monitoring_service import monitoring_service

class HealthStatusType(graphene.ObjectType):
    """Health status information"""
    overall_status = graphene.String()
    timestamp = graphene.String()
    components = graphene.JSONString()
    error = graphene.String()

class MetricsType(graphene.ObjectType):
    """System metrics information"""
    system = graphene.JSONString()
    application = graphene.JSONString()
    business = graphene.JSONString()
    timestamp = graphene.String()

class AlertType(graphene.ObjectType):
    """Alert information"""
    type = graphene.String()
    severity = graphene.String()
    message = graphene.String()
    timestamp = graphene.String()

class AuditLogType(DjangoObjectType):
    """Audit log type"""
    class Meta:
        model = AuditLog
        fields = '__all__'

class MLModelVersionType(DjangoObjectType):
    """ML model version type"""
    class Meta:
        model = MLModelVersion
        fields = '__all__'

class MonitoringDashboardType(graphene.ObjectType):
    """Monitoring dashboard data"""
    timestamp = graphene.String()
    metrics = graphene.Field(MetricsType)
    health = graphene.Field(HealthStatusType)
    alerts = graphene.List(AlertType)
    config = graphene.JSONString()

class GetSystemHealth(graphene.Mutation):
    """Get system health status"""
    success = graphene.Boolean()
    message = graphene.String()
    health = graphene.Field(HealthStatusType)

    def mutate(self, info):
        try:
            health_data = monitoring_service.perform_health_check()
            
            return GetSystemHealth(
                success=True,
                message="Health check completed",
                health=HealthStatusType(
                    overall_status=health_data.get('overall_status', 'unknown'),
                    timestamp=health_data.get('timestamp', ''),
                    components=health_data.get('components', {}),
                    error=health_data.get('error')
                )
            )
        except Exception as e:
            return GetSystemHealth(
                success=False,
                message=f"Health check failed: {str(e)}",
                health=None
            )

class GetSystemMetrics(graphene.Mutation):
    """Get system metrics"""
    success = graphene.Boolean()
    message = graphene.String()
    metrics = graphene.Field(MetricsType)

    def mutate(self, info):
        try:
            metrics_data = monitoring_service.collect_all_metrics()
            
            return GetSystemMetrics(
                success=True,
                message="Metrics collected successfully",
                metrics=MetricsType(
                    system=metrics_data.get('system', {}),
                    application=metrics_data.get('application', {}),
                    business=metrics_data.get('business', {}),
                    timestamp=timezone.now().isoformat()
                )
            )
        except Exception as e:
            return GetSystemMetrics(
                success=False,
                message=f"Metrics collection failed: {str(e)}",
                metrics=None
            )

class GetMonitoringDashboard(graphene.Mutation):
    """Get comprehensive monitoring dashboard data"""
    success = graphene.Boolean()
    message = graphene.String()
    dashboard = graphene.Field(MonitoringDashboardType)

    def mutate(self, info):
        try:
            dashboard_data = monitoring_service.get_monitoring_dashboard_data()
            
            return GetMonitoringDashboard(
                success=True,
                message="Dashboard data retrieved successfully",
                dashboard=MonitoringDashboardType(
                    timestamp=dashboard_data.get('timestamp', ''),
                    metrics=MetricsType(
                        system=dashboard_data.get('metrics', {}).get('system', {}),
                        application=dashboard_data.get('metrics', {}).get('application', {}),
                        business=dashboard_data.get('metrics', {}).get('business', {}),
                        timestamp=dashboard_data.get('timestamp', '')
                    ),
                    health=HealthStatusType(
                        overall_status=dashboard_data.get('health', {}).get('overall_status', 'unknown'),
                        timestamp=dashboard_data.get('health', {}).get('timestamp', ''),
                        components=dashboard_data.get('health', {}).get('components', {}),
                        error=dashboard_data.get('health', {}).get('error')
                    ),
                    alerts=[AlertType(
                        type=alert.get('type', ''),
                        severity=alert.get('severity', ''),
                        message=alert.get('message', ''),
                        timestamp=alert.get('timestamp', '')
                    ) for alert in dashboard_data.get('alerts', [])],
                    config=dashboard_data.get('config', {})
                )
            )
        except Exception as e:
            return GetMonitoringDashboard(
                success=False,
                message=f"Dashboard data retrieval failed: {str(e)}",
                dashboard=None
            )

class GetAuditLogs(graphene.Mutation):
    """Get audit logs with optional filtering"""
    success = graphene.Boolean()
    message = graphene.String()
    logs = graphene.List(AuditLogType)
    total_count = graphene.Int()

    class Arguments:
        user_id = graphene.Int(required=False)
        action_type = graphene.String(required=False)
        start_date = graphene.Date(required=False)
        end_date = graphene.Date(required=False)
        limit = graphene.Int(default_value=100)

    def mutate(self, info, **kwargs):
        try:
            from .pit_data_service import audit_service
            
            logs = audit_service.get_audit_logs(
                user_id=kwargs.get('user_id'),
                action_type=kwargs.get('action_type'),
                start_date=kwargs.get('start_date'),
                end_date=kwargs.get('end_date'),
                limit=kwargs.get('limit', 100)
            )
            
            return GetAuditLogs(
                success=True,
                message=f"Retrieved {len(logs)} audit logs",
                logs=logs,
                total_count=len(logs)
            )
        except Exception as e:
            return GetAuditLogs(
                success=False,
                message=f"Audit logs retrieval failed: {str(e)}",
                logs=[],
                total_count=0
            )

class GetMLModelVersions(graphene.Mutation):
    """Get ML model versions"""
    success = graphene.Boolean()
    message = graphene.String()
    models = graphene.List(MLModelVersionType)

    def mutate(self, info):
        try:
            models = MLModelVersion.objects.all().order_by('-created_at')
            
            return GetMLModelVersions(
                success=True,
                message=f"Retrieved {len(models)} model versions",
                models=models
            )
        except Exception as e:
            return GetMLModelVersions(
                success=False,
                message=f"Model versions retrieval failed: {str(e)}",
                models=[]
            )

# Add to existing mutations
class MonitoringMutations(graphene.ObjectType):
    """Monitoring-related mutations"""
    get_system_health = GetSystemHealth.Field()
    get_system_metrics = GetSystemMetrics.Field()
    get_monitoring_dashboard = GetMonitoringDashboard.Field()
    get_audit_logs = GetAuditLogs.Field()
    get_ml_model_versions = GetMLModelVersions.Field()
