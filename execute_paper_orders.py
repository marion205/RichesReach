#!/usr/bin/env python3
"""
Execute Paper Trading Orders

Reads morning_orders.csv and executes orders in Alpaca paper trading account.
Tracks execution prices and logs fills.

Usage:
    python3 execute_paper_orders.py
    python3 execute_paper_orders.py --dry-run
    python3 execute_paper_orders.py --orders-file morning_orders.csv
"""

import sys
import os
import csv
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# Try to import Alpaca
try:
    import alpaca_trade_api as tradeapi
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False
    print("⚠️  alpaca-trade-api not available. Install with: pip install alpaca-trade-api")

ORDERS_FILE = "morning_orders.csv"
EXECUTION_LOG = "execution_log.jsonl"
DRY_RUN = False


def log_execution(execution_dict: Dict, log_file: str = EXECUTION_LOG):
    """Log order execution"""
    execution_dict['timestamp'] = datetime.utcnow().isoformat() + 'Z'
    with open(log_file, 'a') as f:
        f.write(json.dumps(execution_dict) + "\n")


def execute_orders(orders_file: str = ORDERS_FILE, dry_run: bool = False, log_file: str = EXECUTION_LOG):
    """Execute orders from CSV file"""
    
    if not os.path.exists(orders_file):
        print(f"❌ Orders file not found: {orders_file}")
        return
    
    print("\n" + "="*80)
    print("EXECUTE PAPER TRADING ORDERS")
    print("="*80)
    print(f"\n📄 Orders File: {orders_file}")
    print(f"🔧 Mode: {'DRY RUN' if dry_run else 'LIVE EXECUTION'}")
    
    # Load orders
    orders = []
    with open(orders_file, 'r') as f:
        reader = csv.DictReader(f)
        orders = list(reader)
    
    if not orders:
        print("\n❌ No orders in file")
        return
    
    print(f"\n📊 Found {len(orders)} orders to execute")
    
    # Connect to Alpaca (if not dry run)
    api = None
    if not dry_run and ALPACA_AVAILABLE:
        api_key = os.getenv('ALPACA_API_KEY')
        api_secret = os.getenv('ALPACA_SECRET_KEY')
        
        if not api_key or not api_secret:
            print("\n⚠️  Alpaca credentials not found in environment")
            print("   Set ALPACA_API_KEY and ALPACA_SECRET_KEY")
            print("   Falling back to dry run mode")
            dry_run = True
        else:
            try:
                api = tradeapi.REST(
                    api_key,
                    api_secret,
                    base_url='https://paper-api.alpaca.markets',
                    api_version='v2'
                )
                print("✅ Connected to Alpaca Paper Trading")
            except Exception as e:
                print(f"❌ Failed to connect to Alpaca: {e}")
                print("   Falling back to dry run mode")
                dry_run = True
    
    # Execute orders
    executed = []
    failed = []
    
    print(f"\n📝 Executing Orders...")
    print("-" * 80)
    
    for order in orders:
        symbol = order['Symbol']
        quantity = int(order['Quantity'])
        limit_price = float(order['Limit_Price'])
        weight_pct = float(order['Weight_Pct'])
        
        print(f"\n{symbol}:")
        print(f"   Quantity: {quantity} shares")
        print(f"   Limit Price: ${limit_price:.2f}")
        print(f"   Weight: {weight_pct:.2f}%")
        
        if dry_run:
            print(f"   [DRY RUN] Would submit: BUY {quantity} {symbol} @ ${limit_price:.2f} limit")
            executed.append({
                'symbol': symbol,
                'quantity': quantity,
                'limit_price': limit_price,
                'status': 'DRY_RUN',
                'execution_price': limit_price  # Assume fills at limit
            })
            log_execution({
                'symbol': symbol,
                'action': 'DRY_RUN',
                'quantity': quantity,
                'limit_price': limit_price,
                'expected_fill': limit_price
            }, log_file)
        else:
            if api:
                try:
                    # Submit order
                    submitted_order = api.submit_order(
                        symbol=symbol,
                        qty=quantity,
                        side='buy',
                        type='limit',
                        time_in_force='day',
                        limit_price=limit_price
                    )
                    
                    print(f"   ✅ Order submitted: {submitted_order.id}")
                    
                    executed.append({
                        'symbol': symbol,
                        'quantity': quantity,
                        'limit_price': limit_price,
                        'order_id': submitted_order.id,
                        'status': 'SUBMITTED'
                    })
                    
                    log_execution({
                        'symbol': symbol,
                        'action': 'SUBMIT',
                        'order_id': submitted_order.id,
                        'quantity': quantity,
                        'limit_price': limit_price,
                        'status': 'submitted'
                    }, log_file)
                except Exception as e:
                    print(f"   ❌ Failed: {e}")
                    failed.append({
                        'symbol': symbol,
                        'error': str(e)
                    })
                    log_execution({
                        'symbol': symbol,
                        'action': 'ERROR',
                        'error': str(e)
                    }, log_file)
            else:
                print(f"   ⚠️  Cannot execute (Alpaca not available)")
                failed.append({
                    'symbol': symbol,
                    'error': 'Alpaca not available'
                })
    
    # Summary
    print("\n" + "="*80)
    print("EXECUTION SUMMARY")
    print("="*80)
    print(f"\n✅ Executed: {len(executed)}")
    print(f"❌ Failed: {len(failed)}")
    
    if executed:
        total_value = sum(e['quantity'] * e.get('execution_price', e['limit_price']) for e in executed)
        print(f"💰 Total Value: ${total_value:,.2f}")
    
    if failed:
        print(f"\n❌ Failed Orders:")
        for f in failed:
            print(f"   {f['symbol']}: {f['error']}")
    
    print(f"\n📋 Execution log: {log_file}")
    print("="*80 + "\n")
    
    return {
        'executed': executed,
        'failed': failed
    }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Execute Paper Trading Orders")
    parser.add_argument("--orders-file", default=ORDERS_FILE, help="Orders CSV file")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (don't actually execute)")
    parser.add_argument("--log-file", default=EXECUTION_LOG, help="Execution log file")
    
    args = parser.parse_args()
    
    # Initialize log file
    Path(args.log_file).touch(exist_ok=True)
    
    result = execute_orders(args.orders_file, args.dry_run, args.log_file)
    
    if result:
        print("✅ Order execution complete!")
    else:
        print("❌ Order execution failed")
        sys.exit(1)


if __name__ == "__main__":
    main()

