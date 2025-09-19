"""
Django management command for system monitoring
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.monitoring_service import monitoring_service
from core.pit_data_service import pit_service
import json

class Command(BaseCommand):
    help = 'Monitor system health and collect metrics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['health', 'metrics', 'alerts', 'dashboard', 'cleanup'],
            default='dashboard',
            help='Monitoring action to perform'
        )
        parser.add_argument(
            '--output',
            type=str,
            choices=['json', 'text'],
            default='text',
            help='Output format'
        )
        parser.add_argument(
            '--retention-days',
            type=int,
            default=90,
            help='Days to retain point-in-time data (for cleanup action)'
        )

    def handle(self, *args, **options):
        action = options['action']
        output_format = options['output']
        
        try:
            if action == 'health':
                self.handle_health_check(output_format)
            elif action == 'metrics':
                self.handle_metrics_collection(output_format)
            elif action == 'alerts':
                self.handle_alerts_check(output_format)
            elif action == 'dashboard':
                self.handle_dashboard(output_format)
            elif action == 'cleanup':
                self.handle_cleanup(options['retention_days'])
            else:
                self.stdout.write(self.style.ERROR(f'Unknown action: {action}'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))

    def handle_health_check(self, output_format):
        """Handle health check action"""
        self.stdout.write('Performing system health check...')
        
        health_data = monitoring_service.perform_health_check()
        
        if output_format == 'json':
            self.stdout.write(json.dumps(health_data, indent=2))
        else:
            self.stdout.write(f"Overall Status: {health_data.get('overall_status', 'unknown')}")
            self.stdout.write(f"Timestamp: {health_data.get('timestamp', 'unknown')}")
            
            components = health_data.get('components', {})
            for component, status in components.items():
                self.stdout.write(f"  {component}: {status.get('status', 'unknown')}")

    def handle_metrics_collection(self, output_format):
        """Handle metrics collection action"""
        self.stdout.write('Collecting system metrics...')
        
        metrics_data = monitoring_service.collect_all_metrics()
        
        if output_format == 'json':
            self.stdout.write(json.dumps(metrics_data, indent=2))
        else:
            self.stdout.write(f"Timestamp: {metrics_data.get('timestamp', 'unknown')}")
            
            # System metrics
            system = metrics_data.get('system', {})
            if system:
                self.stdout.write(f"CPU: {system.get('cpu_percent', 0)}%")
                self.stdout.write(f"Memory: {system.get('memory_percent', 0)}%")
                self.stdout.write(f"Disk: {system.get('disk_percent', 0)}%")
            
            # Application metrics
            app = metrics_data.get('application', {})
            if app:
                ml_service = app.get('ml_service', {})
                if ml_service:
                    self.stdout.write(f"ML Mutations (24h): {ml_service.get('ml_mutations_24h', 0)}")
                    self.stdout.write(f"ML Success Rate: {ml_service.get('ml_success_rate', 0):.2%}")

    def handle_alerts_check(self, output_format):
        """Handle alerts check action"""
        self.stdout.write('Checking for alerts...')
        
        alerts = monitoring_service.check_and_send_alerts()
        
        if output_format == 'json':
            self.stdout.write(json.dumps(alerts, indent=2))
        else:
            if alerts:
                self.stdout.write(f"Found {len(alerts)} alerts:")
                for alert in alerts:
                    self.stdout.write(f"  [{alert['severity'].upper()}] {alert['type']}: {alert['message']}")
            else:
                self.stdout.write("No alerts found")

    def handle_dashboard(self, output_format):
        """Handle dashboard action"""
        self.stdout.write('Generating monitoring dashboard...')
        
        dashboard_data = monitoring_service.get_monitoring_dashboard_data()
        
        if output_format == 'json':
            self.stdout.write(json.dumps(dashboard_data, indent=2))
        else:
            self.stdout.write("=== MONITORING DASHBOARD ===")
            self.stdout.write(f"Timestamp: {dashboard_data.get('timestamp', 'unknown')}")
            
            # Health status
            health = dashboard_data.get('health', {})
            self.stdout.write(f"\nHealth Status: {health.get('overall_status', 'unknown')}")
            
            # Metrics summary
            metrics = dashboard_data.get('metrics', {})
            system = metrics.get('system', {})
            if system:
                self.stdout.write(f"\nSystem Resources:")
                self.stdout.write(f"  CPU: {system.get('cpu_percent', 0)}%")
                self.stdout.write(f"  Memory: {system.get('memory_percent', 0)}%")
                self.stdout.write(f"  Disk: {system.get('disk_percent', 0)}%")
            
            # Alerts
            alerts = dashboard_data.get('alerts', [])
            if alerts:
                self.stdout.write(f"\nActive Alerts ({len(alerts)}):")
                for alert in alerts:
                    self.stdout.write(f"  [{alert['severity'].upper()}] {alert['type']}: {alert['message']}")
            else:
                self.stdout.write("\nNo active alerts")

    def handle_cleanup(self, retention_days):
        """Handle cleanup action"""
        self.stdout.write(f'Cleaning up data older than {retention_days} days...')
        
        pit_service.cleanup_old_data(retention_days)
        
        self.stdout.write('Cleanup completed successfully')
