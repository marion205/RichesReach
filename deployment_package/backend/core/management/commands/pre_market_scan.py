"""
Django management command to run pre-market scanner
Usage: python manage.py pre_market_scan
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.pre_market_scanner import PreMarketScanner
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Scan pre-market movers and flag quality setups before market open'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mode',
            type=str,
            default='AGGRESSIVE',
            choices=['SAFE', 'AGGRESSIVE'],
            help='Trading mode (SAFE or AGGRESSIVE)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Maximum number of setups to return'
        )
        parser.add_argument(
            '--alert',
            action='store_true',
            help='Generate and print alert message'
        )

    def handle(self, *args, **options):
        mode = options['mode']
        limit = options['limit']
        alert = options.get('alert', False)
        
        scanner = PreMarketScanner()
        
        # Check if we're in pre-market hours
        if not scanner.is_pre_market_hours():
            et_hour = scanner._get_et_hour()
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  Not in pre-market hours (current ET hour: {et_hour})"
                )
            )
            self.stdout.write("Pre-market hours: 4:00 AM - 9:30 AM ET")
            return
        
        self.stdout.write(self.style.SUCCESS(f"🔍 Starting pre-market scan (mode: {mode})"))
        self.stdout.write(f"Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write(f"Minutes until open: {scanner._minutes_until_open()}")
        self.stdout.write("")
        
        # Run scan
        setups = scanner.scan_pre_market_sync(mode=mode, limit=limit)
        
        if not setups:
            self.stdout.write(
                self.style.WARNING("⚠️  No quality pre-market setups found")
            )
            return
        
        # Display results
        self.stdout.write(self.style.SUCCESS(f"✅ Found {len(setups)} quality setups"))
        self.stdout.write("")
        self.stdout.write("=" * 80)
        self.stdout.write("PRE-MARKET QUALITY SETUPS")
        self.stdout.write("=" * 80)
        self.stdout.write("")
        
        for i, setup in enumerate(setups, 1):
            symbol = setup['symbol']
            side = setup['side']
            change = setup['pre_market_change_pct']
            price = setup['pre_market_price']
            score = setup['score']
            volume = setup['volume']
            
            self.stdout.write(f"{i}. {symbol} - {side}")
            self.stdout.write(f"   Pre-market move: {change:+.2%}")
            self.stdout.write(f"   Current price: ${price:.2f}")
            self.stdout.write(f"   Volume: {volume:,} shares")
            self.stdout.write(f"   Quality score: {score:.2f}")
            self.stdout.write(f"   Notes: {setup['notes']}")
            self.stdout.write("")
        
        # Generate alert if requested
        if alert:
            alert_message = scanner.generate_alert(setups)
            self.stdout.write("=" * 80)
            self.stdout.write("ALERT MESSAGE")
            self.stdout.write("=" * 80)
            self.stdout.write(alert_message)
        
        self.stdout.write(self.style.SUCCESS("✅ Pre-market scan complete"))

