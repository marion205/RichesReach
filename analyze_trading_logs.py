#!/usr/bin/env python3
"""
Trading Log Analyzer

Analyzes trading_log.jsonl to track:
- Pass rate trends
- Rejection reasons
- Signal quality metrics
- When signals start passing gating rules

Usage:
    python3 analyze_trading_logs.py
    python3 analyze_trading_logs.py --last-days 7
    python3 analyze_trading_logs.py --summary
"""

import sys
import os
import json
import argparse
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

LOG_FILE = "trading_log.jsonl"


def load_logs(last_days: Optional[int] = None) -> List[Dict]:
    """Load log entries from JSONL file"""
    if not os.path.exists(LOG_FILE):
        print(f"❌ Log file not found: {LOG_FILE}")
        return []
    
    logs = []
    cutoff_date = None
    if last_days:
        cutoff_date = datetime.now() - timedelta(days=last_days)
    
    with open(LOG_FILE, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if cutoff_date:
                    entry_date = datetime.fromisoformat(entry.get('timestamp', '').replace('Z', '+00:00'))
                    if entry_date.replace(tzinfo=None) < cutoff_date:
                        continue
                logs.append(entry)
            except json.JSONDecodeError:
                continue
    
    return logs


def analyze_logs(logs: List[Dict]) -> Dict:
    """Analyze log entries"""
    if not logs:
        return {}
    
    analysis = {
        'total_entries': len(logs),
        'by_decision': Counter(),
        'by_reason': Counter(),
        'scan_statuses': Counter(),
        'metrics_summary': {},
        'recent_scans': []
    }
    
    # Track decisions
    decisions = []
    reasons = []
    metrics_list = []
    scan_dates = []
    
    for entry in logs:
        decision = entry.get('decision', 'UNKNOWN')
        analysis['by_decision'][decision] += 1
        decisions.append(decision)
        
        reason = entry.get('reason', '')
        if reason:
            reasons.append(reason)
            # Extract main reason (first part before semicolon)
            main_reason = reason.split(';')[0].split(',')[0]
            analysis['by_reason'][main_reason] += 1
        
        scan_status = entry.get('scan_status')
        if scan_status:
            analysis['scan_statuses'][scan_status] += 1
            timestamp = entry.get('timestamp', '')
            if timestamp:
                try:
                    scan_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    scan_dates.append(scan_date)
                except:
                    pass
        
        # Extract metrics
        metrics = entry.get('metrics', {})
        if metrics:
            metrics_list.append(metrics)
    
    # Metrics summary
    if metrics_list:
        metrics_df = pd.DataFrame(metrics_list)
        analysis['metrics_summary'] = {
            'fss_score': {
                'mean': float(metrics_df['fss_score'].mean()) if 'fss_score' in metrics_df.columns else None,
                'median': float(metrics_df['fss_score'].median()) if 'fss_score' in metrics_df.columns else None,
                'min': float(metrics_df['fss_score'].min()) if 'fss_score' in metrics_df.columns else None,
                'max': float(metrics_df['fss_score'].max()) if 'fss_score' in metrics_df.columns else None
            },
            'robustness': {
                'mean': float(metrics_df['regime_robustness'].mean()) if 'regime_robustness' in metrics_df.columns else None,
                'median': float(metrics_df['regime_robustness'].median()) if 'regime_robustness' in metrics_df.columns else None,
                'min': float(metrics_df['regime_robustness'].min()) if 'regime_robustness' in metrics_df.columns else None,
                'max': float(metrics_df['regime_robustness'].max()) if 'regime_robustness' in metrics_df.columns else None
            },
            'ssr': {
                'mean': float(metrics_df['ssr'].mean()) if 'ssr' in metrics_df.columns else None,
                'median': float(metrics_df['ssr'].median()) if 'ssr' in metrics_df.columns else None,
                'min': float(metrics_df['ssr'].min()) if 'ssr' in metrics_df.columns else None,
                'max': float(metrics_df['ssr'].max()) if 'ssr' in metrics_df.columns else None
            }
        }
    
    # Recent scans
    if scan_dates:
        scan_dates.sort(reverse=True)
        analysis['recent_scans'] = [d.strftime('%Y-%m-%d %H:%M:%S') for d in scan_dates[:10]]
    
    # Pass rate
    pass_count = analysis['by_decision'].get('PASS', 0)
    skip_count = analysis['by_decision'].get('SKIP', 0)
    buy_count = analysis['by_decision'].get('BUY', 0)
    total_decisions = pass_count + skip_count + buy_count
    
    if total_decisions > 0:
        analysis['pass_rate'] = (pass_count + buy_count) / total_decisions
        analysis['skip_rate'] = skip_count / total_decisions
    else:
        analysis['pass_rate'] = 0.0
        analysis['skip_rate'] = 0.0
    
    return analysis


def print_analysis(analysis: Dict, summary_only: bool = False):
    """Print analysis results"""
    if not analysis:
        print("No log entries found")
        return
    
    print("\n" + "="*80)
    print("TRADING LOG ANALYSIS")
    print("="*80)
    
    print(f"\n📊 Overview:")
    print(f"   Total Entries: {analysis['total_entries']}")
    print(f"   Pass Rate: {analysis['pass_rate']:.2%}")
    print(f"   Skip Rate: {analysis['skip_rate']:.2%}")
    
    print(f"\n📈 Decisions Breakdown:")
    for decision, count in analysis['by_decision'].most_common():
        print(f"   {decision}: {count}")
    
    if not summary_only:
        print(f"\n🚫 Top Rejection Reasons:")
        for reason, count in analysis['by_reason'].most_common(10):
            print(f"   {reason}: {count}")
        
        if analysis['metrics_summary']:
            print(f"\n📊 Metrics Summary:")
            
            if analysis['metrics_summary'].get('fss_score'):
                fss = analysis['metrics_summary']['fss_score']
                print(f"   FSS Score:")
                print(f"     Mean: {fss['mean']:.2f}" if fss['mean'] else "     Mean: N/A")
                print(f"     Median: {fss['median']:.2f}" if fss['median'] else "     Median: N/A")
                print(f"     Range: [{fss['min']:.2f}, {fss['max']:.2f}]" if fss['min'] and fss['max'] else "     Range: N/A")
            
            if analysis['metrics_summary'].get('robustness'):
                rob = analysis['metrics_summary']['robustness']
                print(f"   Robustness:")
                print(f"     Mean: {rob['mean']:.3f}" if rob['mean'] else "     Mean: N/A")
                print(f"     Median: {rob['median']:.3f}" if rob['median'] else "     Median: N/A")
                print(f"     Range: [{rob['min']:.3f}, {rob['max']:.3f}]" if rob['min'] and rob['max'] else "     Range: N/A")
            
            if analysis['metrics_summary'].get('ssr'):
                ssr = analysis['metrics_summary']['ssr']
                print(f"   SSR:")
                print(f"     Mean: {ssr['mean']:.3f}" if ssr['mean'] else "     Mean: N/A")
                print(f"     Median: {ssr['median']:.3f}" if ssr['median'] else "     Median: N/A")
                print(f"     Range: [{ssr['min']:.3f}, {ssr['max']:.3f}]" if ssr['min'] and ssr['max'] else "     Range: N/A")
        
        if analysis['scan_statuses']:
            print(f"\n🔄 Scan Statuses:")
            for status, count in analysis['scan_statuses'].most_common():
                print(f"   {status}: {count}")
        
        if analysis['recent_scans']:
            print(f"\n📅 Recent Scans:")
            for scan_date in analysis['recent_scans'][:5]:
                print(f"   {scan_date}")
    
    print("\n" + "="*80)


def main():
    parser = argparse.ArgumentParser(description="Analyze Trading Logs")
    parser.add_argument("--last-days", type=int, help="Analyze last N days only")
    parser.add_argument("--summary", action="store_true", help="Show summary only")
    parser.add_argument("--export", help="Export to CSV file")
    
    args = parser.parse_args()
    
    logs = load_logs(last_days=args.last_days)
    analysis = analyze_logs(logs)
    print_analysis(analysis, summary_only=args.summary)
    
    if args.export:
        # Export to CSV
        logs_df = pd.DataFrame(logs)
        logs_df.to_csv(args.export, index=False)
        print(f"\n📄 Exported to: {args.export}")


if __name__ == "__main__":
    main()

