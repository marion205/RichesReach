#!/usr/bin/env python3
"""
Adjusted Nightly Scan - Lower Thresholds for Initial Testing

Uses more lenient gating rules for initial testing:
- MIN_ROBUSTNESS: 0.60 (lowered from 0.70)
- MIN_SSR: 0.40 (lowered from 0.50)

Usage:
    python3 run_nightly_scan_adjusted.py
    python3 run_nightly_scan_adjusted.py --min-robustness 0.6 --min-ssr 0.4
"""

import sys
import os

# Import the main scan function
sys.path.insert(0, os.path.dirname(__file__))

# Modify the gating rules in the imported module
import run_nightly_scan as scan_module

# Override gating rules for testing
scan_module.GATING_RULES = {
    'MIN_ROBUSTNESS': 0.60,  # Lowered from 0.70
    'MIN_SSR': 0.40,         # Lowered from 0.50
    'MIN_HISTORY': 252,
    'FORBIDDEN_REGIMES': ['Crash', 'Bear Volatile', 'Crisis', 'Deflation']
}

# Use different log/order files to avoid overwriting production
scan_module.LOG_FILE = "trading_log_adjusted.jsonl"
scan_module.ORDERS_FILE = "morning_orders_adjusted.csv"

if __name__ == "__main__":
    print("⚠️  Running with ADJUSTED (lower) thresholds for initial testing")
    print(f"   Min Robustness: {scan_module.GATING_RULES['MIN_ROBUSTNESS']}")
    print(f"   Min SSR: {scan_module.GATING_RULES['MIN_SSR']}")
    print()
    
    scan_module.run_nightly_scan()

