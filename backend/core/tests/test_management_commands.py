"""
Tests for management commands
"""
from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from io import StringIO
import sys

from core.models import OHLCV, Signal, User
from django.utils import timezone
from decimal import Decimal
import datetime


class ManagementCommandsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com', 
            username='testuser', 
            password='password'
        )
        
        # Create some test OHLCV data
        base_time = timezone.now() - datetime.timedelta(days=30)
        for i in range(50):
            OHLCV.objects.create(
                symbol='AAPL',
                timeframe='1d',
                timestamp=base_time + datetime.timedelta(days=i),
                open_price=Decimal('150.00'),
                high_price=Decimal('155.00'),
                low_price=Decimal('145.00'),
                close_price=Decimal('152.00'),
                volume=1000000
            )

    def test_backfill_command_dry_run(self):
        """Test the backfill command in dry run mode"""
        
        # Capture output
        out = StringIO()
        err = StringIO()
        
        # Run command in dry run mode
        call_command(
            'backfill_swing_trading_data',
            '--symbols', 'AAPL',
            '--timeframes', '1d',
            '--days-back', '30',
            '--dry-run',
            stdout=out,
            stderr=err
        )
        
        output = out.getvalue()
        
        # Check that dry run mode was indicated
        self.assertIn('DRY RUN MODE', output)
        self.assertIn('Would process', output)
        
        # Verify no actual changes were made
        ohlcv = OHLCV.objects.filter(symbol='AAPL').first()
        self.assertIsNone(ohlcv.ema_12)  # Should still be None

    def test_backfill_command_help(self):
        """Test that the command help is displayed correctly"""
        
        out = StringIO()
        err = StringIO()
        
        try:
            call_command(
                'backfill_swing_trading_data',
                '--help',
                stdout=out,
                stderr=err
            )
        except SystemExit:
            pass  # --help causes SystemExit
        
        output = out.getvalue()
        
        # Check that help text contains expected options
        self.assertIn('--symbols', output)
        self.assertIn('--timeframes', output)
        self.assertIn('--days-back', output)
        self.assertIn('--warm-indexes', output)
        self.assertIn('--generate-signals', output)
        self.assertIn('--dry-run', output)

    def test_backfill_command_invalid_symbols(self):
        """Test the command with invalid symbols"""
        
        out = StringIO()
        err = StringIO()
        
        # This should not raise an error, just process empty results
        call_command(
            'backfill_swing_trading_data',
            '--symbols', 'INVALID_SYMBOL',
            '--timeframes', '1d',
            '--days-back', '30',
            '--dry-run',
            stdout=out,
            stderr=err
        )
        
        output = out.getvalue()
        self.assertIn('No data found', output)

    def test_backfill_command_invalid_timeframes(self):
        """Test the command with invalid timeframes"""
        
        out = StringIO()
        err = StringIO()
        
        # This should not raise an error, just process empty results
        call_command(
            'backfill_swing_trading_data',
            '--symbols', 'AAPL',
            '--timeframes', 'invalid_timeframe',
            '--days-back', '30',
            '--dry-run',
            stdout=out,
            stderr=err
        )
        
        output = out.getvalue()
        self.assertIn('No data found', output)

    def test_backfill_command_insufficient_data(self):
        """Test the command with insufficient data"""
        
        # Create only a few records
        OHLCV.objects.filter(symbol='AAPL').delete()
        for i in range(5):  # Less than 50 records
            OHLCV.objects.create(
                symbol='AAPL',
                timeframe='1d',
                timestamp=timezone.now() - datetime.timedelta(days=i),
                open_price=Decimal('150.00'),
                high_price=Decimal('155.00'),
                low_price=Decimal('145.00'),
                close_price=Decimal('152.00'),
                volume=1000000
            )
        
        out = StringIO()
        err = StringIO()
        
        call_command(
            'backfill_swing_trading_data',
            '--symbols', 'AAPL',
            '--timeframes', '1d',
            '--days-back', '30',
            '--dry-run',
            stdout=out,
            stderr=err
        )
        
        output = out.getvalue()
        self.assertIn('Insufficient data', output)
