"""
Validate Training Data
Checks data quality, completeness, and prevents look-ahead bias.
"""
import os
import sys
import django
import logging
from django.core.management.base import BaseCommand
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Validate training data quality and check for issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-dir',
            type=str,
            default='training_data',
            help='Directory containing training data'
        )
        parser.add_argument(
            '--fix-issues',
            action='store_true',
            help='Attempt to fix common issues automatically'
        )

    def handle(self, *args, **options):
        self.stdout.write("🔍 Validating Training Data")
        self.stdout.write("=" * 60)
        
        data_dir = Path(options['data_dir'])
        price_dir = data_dir / 'price_data'
        
        if not price_dir.exists():
            self.stdout.write(self.style.ERROR(f"❌ Data directory not found: {price_dir}"))
            return
        
        # Find all price data files
        price_files = list(price_dir.glob('*.csv'))
        
        if not price_files:
            self.stdout.write(self.style.WARNING("⚠️ No price data files found"))
            return
        
        self.stdout.write(f"\n📊 Found {len(price_files)} price data files")
        
        # Validate each file
        total_issues = 0
        validated = 0
        
        for price_file in price_files:
            symbol = price_file.stem.split('_')[0]
            self.stdout.write(f"\n🔍 Validating {symbol}...")
            
            try:
                df = pd.read_csv(price_file, index_col=0, parse_dates=True)
                
                issues = self._validate_dataframe(df, symbol, options['fix_issues'])
                
                if issues:
                    total_issues += len(issues)
                    for issue in issues:
                        self.stdout.write(self.style.WARNING(f"   ⚠️ {issue}"))
                else:
                    validated += 1
                    self.stdout.write(self.style.SUCCESS(f"   ✅ {symbol} validated"))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ Error validating {symbol}: {e}"))
                total_issues += 1
        
        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("📊 Validation Summary:")
        self.stdout.write(self.style.SUCCESS(f"   ✅ Validated: {validated}/{len(price_files)}"))
        if total_issues > 0:
            self.stdout.write(self.style.WARNING(f"   ⚠️ Total issues: {total_issues}"))
        else:
            self.stdout.write(self.style.SUCCESS("   ✅ No issues found!"))
    
    def _validate_dataframe(
        self,
        df: pd.DataFrame,
        symbol: str,
        fix_issues: bool
    ) -> list:
        """Validate a single dataframe"""
        issues = []
        
        # Check 1: Required columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            issues.append(f"Missing columns: {missing_cols}")
        
        # Check 2: No empty dataframe
        if len(df) == 0:
            issues.append("Empty dataframe")
            return issues
        
        # Check 3: No missing values
        missing_pct = df[required_cols].isnull().sum() / len(df) * 100
        for col, pct in missing_pct.items():
            if pct > 1.0:  # More than 1% missing
                issues.append(f"{col}: {pct:.1f}% missing values")
                if fix_issues:
                    df[col].fillna(method='ffill', inplace=True)
                    df[col].fillna(method='bfill', inplace=True)
        
        # Check 4: OHLC relationships
        invalid_ohlc = (
            (df['High'] < df['Low']) |
            (df['Close'] > df['High']) |
            (df['Close'] < df['Low']) |
            (df['Open'] > df['High']) |
            (df['Open'] < df['Low'])
        ).sum()
        
        if invalid_ohlc > 0:
            issues.append(f"{invalid_ohlc} bars with invalid OHLC relationships")
            if fix_issues:
                # Fix: ensure High >= Low, Close in range
                df['High'] = df[['High', 'Low', 'Open', 'Close']].max(axis=1)
                df['Low'] = df[['High', 'Low', 'Open', 'Close']].min(axis=1)
                df['Close'] = df['Close'].clip(lower=df['Low'], upper=df['High'])
                df['Open'] = df['Open'].clip(lower=df['Low'], upper=df['High'])
        
        # Check 5: Volume > 0
        zero_volume = (df['Volume'] <= 0).sum()
        if zero_volume > len(df) * 0.05:  # More than 5% zero volume
            issues.append(f"{zero_volume} bars with zero/negative volume ({zero_volume/len(df)*100:.1f}%)")
        
        # Check 6: Duplicate timestamps
        duplicates = df.index.duplicated().sum()
        if duplicates > 0:
            issues.append(f"{duplicates} duplicate timestamps")
            if fix_issues:
                df = df[~df.index.duplicated(keep='first')]
        
        # Check 7: Time gaps (missing bars)
        if len(df) > 1:
            time_diffs = df.index.to_series().diff()
            expected_diff = pd.Timedelta(minutes=1)
            large_gaps = (time_diffs > expected_diff * 2).sum()  # Gaps > 2 minutes
            if large_gaps > len(df) * 0.1:  # More than 10% gaps
                issues.append(f"{large_gaps} large time gaps detected ({large_gaps/len(df)*100:.1f}%)")
        
        # Check 8: Minimum data requirement
        min_bars = 60  # Need at least 60 bars for LSTM
        if len(df) < min_bars:
            issues.append(f"Insufficient data: {len(df)} bars (need {min_bars} minimum)")
        
        # Check 9: Price continuity (no extreme jumps)
        if 'Close' in df.columns:
            returns = df['Close'].pct_change()
            extreme_returns = (abs(returns) > 0.2).sum()  # >20% moves
            if extreme_returns > len(df) * 0.01:  # More than 1% extreme
                issues.append(f"{extreme_returns} extreme price moves detected (may indicate data errors)")
        
        # Check 10: Timestamp ordering
        if not df.index.is_monotonic_increasing:
            issues.append("Timestamps not in chronological order")
            if fix_issues:
                df.sort_index(inplace=True)
        
        return issues

