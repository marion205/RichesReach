"""
Setup Cloud Locality Optimization
Configure inference endpoints for multi-region deployment.
"""
from django.core.management.base import BaseCommand
from core.cloud_locality_service import get_cloud_locality_service
import os


class Command(BaseCommand):
    help = 'Setup cloud locality optimization for inference endpoints'

    def add_arguments(self, parser):
        parser.add_argument(
            '--add-endpoint',
            type=str,
            nargs=2,
            metavar=('REGION', 'URL'),
            help='Add inference endpoint: --add-endpoint us-east-1 http://inference-us-east.example.com'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List configured endpoints'
        )
        parser.add_argument(
            '--test',
            action='store_true',
            help='Test endpoint latency'
        )
        parser.add_argument(
            '--set-default',
            type=str,
            help='Set default inference endpoint URL'
        )

    def handle(self, *args, **options):
        service = get_cloud_locality_service()
        
        if options['add_endpoint']:
            region, url = options['add_endpoint']
            service.add_inference_endpoint(region, url)
            self.stdout.write(self.style.SUCCESS(f"✅ Added endpoint: {region} -> {url}"))
            self.stdout.write(f"   Set environment variable: INFERENCE_ENDPOINTS={region}:{url}")
        
        if options['set_default']:
            default_url = options['set_default']
            service.default_endpoint = default_url
            self.stdout.write(self.style.SUCCESS(f"✅ Set default endpoint: {default_url}"))
            self.stdout.write(f"   Set environment variable: DEFAULT_INFERENCE_ENDPOINT={default_url}")
        
        if options['list']:
            self.stdout.write("\n📊 Cloud Locality Configuration")
            self.stdout.write("=" * 60)
            
            status = service.get_status()
            
            self.stdout.write(f"\n🌍 Broker Regions:")
            for broker, region in status['broker_regions'].items():
                self.stdout.write(f"   {broker}: {region}")
            
            self.stdout.write(f"\n🔗 Inference Endpoints:")
            if status['endpoints']:
                for region, endpoints in status['endpoints'].items():
                    self.stdout.write(f"\n   {region}:")
                    for ep in endpoints:
                        status_icon = "✅" if ep['is_active'] else "❌"
                        self.stdout.write(f"      {status_icon} {ep['url']}")
                        self.stdout.write(f"         Priority: {ep['priority']}, Latency: {ep['latency_ms']:.1f}ms")
            else:
                self.stdout.write("   ⚠️  No endpoints configured")
                self.stdout.write("\n   💡 Add endpoints with:")
                self.stdout.write("      python manage.py setup_cloud_locality --add-endpoint us-east-1 http://inference.example.com")
            
            self.stdout.write(f"\n🔧 Default Endpoint: {status['default_endpoint']}")
            
            if status['enabled']:
                self.stdout.write(self.style.SUCCESS("\n✅ Cloud locality optimization is ENABLED"))
            else:
                self.stdout.write(self.style.WARNING("\n⚠️  Cloud locality optimization is DISABLED"))
                self.stdout.write("   Add at least one endpoint to enable")
        
        if options['test']:
            self.stdout.write("\n🧪 Testing Endpoint Latency")
            self.stdout.write("=" * 60)
            
            status = service.get_status()
            
            for region, endpoints in status['endpoints'].items():
                self.stdout.write(f"\n{region}:")
                for ep in endpoints:
                    latency = service.measure_latency(ep['url'])
                    if latency < float('inf'):
                        self.stdout.write(self.style.SUCCESS(f"   ✅ {ep['url']}: {latency:.1f}ms"))
                    else:
                        self.stdout.write(self.style.ERROR(f"   ❌ {ep['url']}: Unreachable"))
            
            # Test optimal endpoint
            self.stdout.write("\n🎯 Optimal Endpoint:")
            optimal_url, optimal_latency = service.get_optimal_endpoint('alpaca')
            if optimal_latency < float('inf'):
                self.stdout.write(self.style.SUCCESS(f"   ✅ {optimal_url}: {optimal_latency:.1f}ms"))
            else:
                self.stdout.write(self.style.WARNING(f"   ⚠️  {optimal_url}: Using default (latency unknown)"))

