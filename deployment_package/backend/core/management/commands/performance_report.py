"""
Django management command to generate performance reports
Usage: python manage.py performance_report
"""
from django.core.management.base import BaseCommand
from core.performance_monitoring import get_performance_monitor
import json
from datetime import datetime


class Command(BaseCommand):
    help = 'Generate performance report for RAHA queries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--export',
            type=str,
            help='Export report to JSON file',
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset metrics after generating report',
        )

    def handle(self, *args, **options):
        monitor = get_performance_monitor()
        summary = monitor.get_summary()
        
        self.stdout.write(self.style.SUCCESS('\n📊 RAHA Performance Report'))
        self.stdout.write('=' * 80)
        self.stdout.write('')
        
        # Summary
        self.stdout.write(self.style.SUCCESS('Summary:'))
        self.stdout.write(f"  Total Queries: {summary['total_queries']}")
        self.stdout.write(f"  Overall Cache Hit Rate: {summary['overall_cache_hit_rate']}%")
        self.stdout.write(f"  Avg Query Time: {summary['avg_query_time_ms']}ms")
        self.stdout.write(f"  Query Types: {summary['query_types']}")
        self.stdout.write('')
        
        # Detailed metrics
        if summary['metrics']:
            self.stdout.write(self.style.SUCCESS('Query Performance:'))
            self.stdout.write('-' * 80)
            
            # Sort by average time (slowest first)
            sorted_queries = sorted(
                summary['metrics'].items(),
                key=lambda x: x[1]['avg_time_ms'],
                reverse=True
            )
            
            for query_name, metric in sorted_queries:
                self.stdout.write(f"\n{query_name}:")
                self.stdout.write(f"  Queries: {metric['query_count']}")
                self.stdout.write(f"  Avg Time: {metric['avg_time_ms']}ms")
                self.stdout.write(f"  Min Time: {metric['min_time_ms']}ms")
                self.stdout.write(f"  Max Time: {metric['max_time_ms']}ms")
                self.stdout.write(f"  Cache Hit Rate: {metric['cache_hit_rate']}%")
                self.stdout.write(f"  Avg DB Queries: {metric['avg_db_queries']}")
        
        # Export if requested
        if options['export']:
            json_data = monitor.export_metrics(options['export'])
            self.stdout.write(self.style.SUCCESS(f'\n✅ Report exported to {options["export"]}'))
        
        # Reset if requested
        if options['reset']:
            monitor.reset()
            self.stdout.write(self.style.SUCCESS('\n✅ Metrics reset'))
        
        self.stdout.write('')

