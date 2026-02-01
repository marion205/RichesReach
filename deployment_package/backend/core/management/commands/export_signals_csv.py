"""
Export Signals to CSV
Generate downloadable CSV of signals for independent verification.
"""
import csv
import os
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import SignalRecord


class Command(BaseCommand):
    help = 'Export signals to CSV for transparency and verification'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Number of signals to export (default: 100)'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='signals_export.csv',
            help='Output CSV filename (default: signals_export.csv)'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=None,
            help='Export signals from last N days (optional)'
        )
        parser.add_argument(
            '--status',
            type=str,
            choices=['OPEN', 'CLOSED', 'ABSTAINED', 'ALL'],
            default='ALL',
            help='Filter by status (default: ALL)'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        output_file = options['output']
        days = options.get('days')
        status_filter = options['status']

        self.stdout.write("📊 Exporting signals to CSV...")
        self.stdout.write(f"   Limit: {limit}")
        self.stdout.write(f"   Status: {status_filter}")
        if days:
            self.stdout.write(f"   Days: {days}")

        # Build query
        queryset = SignalRecord.objects.all()

        if days:
            cutoff_date = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(entry_timestamp__gte=cutoff_date)

        if status_filter != 'ALL':
            queryset = queryset.filter(status=status_filter)

        # Order by most recent first
        queryset = queryset.order_by('-entry_timestamp')[:limit]

        signals = list(queryset)

        if not signals:
            self.stdout.write(self.style.WARNING("   ⚠️ No signals found matching criteria"))
            return

        # Write CSV
        output_path = os.path.join(os.getcwd(), output_file)
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'signal_id',
                'symbol',
                'action',
                'confidence',
                'entry_price',
                'entry_timestamp',
                'exit_price',
                'exit_timestamp',
                'pnl',
                'pnl_percent',
                'status',
                'reasoning',
                'user_id',
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for signal in signals:
                writer.writerow({
                    'signal_id': signal.id,
                    'symbol': signal.symbol,
                    'action': signal.action,
                    'confidence': signal.confidence,
                    'entry_price': signal.entry_price or '',
                    'entry_timestamp': signal.entry_timestamp.isoformat() if signal.entry_timestamp else '',
                    'exit_price': signal.exit_price or '',
                    'exit_timestamp': signal.exit_timestamp.isoformat() if signal.exit_timestamp else '',
                    'pnl': signal.pnl or '',
                    'pnl_percent': signal.pnl_percent or '',
                    'status': signal.status,
                    'reasoning': signal.reasoning or '',
                    'user_id': signal.user_id or '',
                })

        self.stdout.write(self.style.SUCCESS(f"\n   ✅ Exported {len(signals)} signals to {output_path}"))
        self.stdout.write(f"\n   📋 Fields included:")
        for field in fieldnames:
            self.stdout.write(f"      - {field}")

