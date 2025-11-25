#!/usr/bin/env python3
"""
Analyze Why Algorithm Missed Top Gainers
Checks each top gainer against the algorithm's filtering criteria
"""
import requests
import json
from typing import Dict, List, Optional

# Top gainers from today
TOP_GAINERS = [
    {"symbol": "RJET", "change_pct": 1487.79},
    {"symbol": "CETY", "change_pct": 128.04},
    {"symbol": "LIXTW", "change_pct": 63.00},
    {"symbol": "MPTI.WS", "change_pct": 56.22},
    {"symbol": "RUBI", "change_pct": 54.29},
    {"symbol": "KZIA", "change_pct": 49.35},
    {"symbol": "OPENZ", "change_pct": 44.41},
    {"symbol": "KSS", "change_pct": 42.22},
    {"symbol": "PAVS", "change_pct": 41.87},
    {"symbol": "SYM", "change_pct": 39.24},
]

# Algorithm filter criteria
FILTERS = {
    "SAFE": {
        "min_price": 5.0,
        "max_price": 500.0,
        "min_volume": 5_000_000,
        "min_market_cap": 50_000_000_000,  # $50B
        "max_change_pct": 0.15,  # 15%
        "max_volatility": 0.03,  # 3%
    },
    "AGGRESSIVE": {
        "min_price": 2.0,
        "max_price": 500.0,
        "min_volume": 1_000_000,
        "min_market_cap": 1_000_000_000,  # $1B
        "max_change_pct": 0.30,  # 30%
        "max_volatility": 0.08,  # 8%
    }
}

def check_symbol_filters(symbol: str) -> Dict:
    """Check basic symbol filters"""
    issues = []
    
    # Check symbol length
    if len(symbol) > 5:
        issues.append(f"Symbol too long ({len(symbol)} chars, max 5)")
    
    # Check for dots (warrants, etc.)
    if '.' in symbol:
        issues.append(f"Contains '.' (warrants/units filtered out)")
    
    # Check for X suffix (ETFs)
    if symbol.endswith('X'):
        issues.append(f"Ends with 'X' (ETFs filtered out)")
    
    return {
        "symbol": symbol,
        "basic_filters_passed": len(issues) == 0,
        "basic_filter_issues": issues
    }


def analyze_gainer(gainer: Dict, mode: str = "AGGRESSIVE") -> Dict:
    """Analyze why a top gainer was filtered out"""
    symbol = gainer["symbol"]
    change_pct = gainer["change_pct"] / 100  # Convert to decimal
    
    filters = FILTERS[mode]
    reasons = []
    
    # 1. Check symbol format
    symbol_check = check_symbol_filters(symbol)
    if not symbol_check["basic_filters_passed"]:
        reasons.extend(symbol_check["basic_filter_issues"])
    
    # 2. Check change percentage (MOST LIKELY REASON)
    if change_pct > filters["max_change_pct"]:
        reasons.append(
            f"Change {change_pct:.1%} > max {filters['max_change_pct']:.1%} "
            f"(filtered: too volatile, already moved too much)"
        )
    
    # 3. Check if it would pass volatility filter
    # These massive moves indicate extreme volatility
    estimated_volatility = min(change_pct * 0.5, 1.0)  # Rough estimate
    if estimated_volatility > filters["max_volatility"]:
        reasons.append(
            f"Estimated volatility {estimated_volatility:.1%} > max {filters['max_volatility']:.1%} "
            f"(too risky for day trading)"
        )
    
    return {
        "symbol": symbol,
        "change_pct": f"{change_pct:.1%}",
        "mode": mode,
        "filtered_out": True,
        "reasons": reasons,
        "would_pass": len(reasons) == 0
    }


def main():
    """Main analysis"""
    print("\n" + "="*100)
    print("WHY ALGORITHM MISSED TOP GAINERS - ANALYSIS")
    print("="*100)
    print()
    print("Top Gainers Today:")
    for i, gainer in enumerate(TOP_GAINERS, 1):
        print(f"  {i}. {gainer['symbol']}: +{gainer['change_pct']:.2f}%")
    print()
    
    print("="*100)
    print("ALGORITHM FILTER CRITERIA")
    print("="*100)
    print("\nAGGRESSIVE Mode (most permissive):")
    filters = FILTERS["AGGRESSIVE"]
    print(f"  • Min Price: ${filters['min_price']:.2f}")
    print(f"  • Max Price: ${filters['max_price']:.2f}")
    print(f"  • Min Volume: {filters['min_volume']:,} shares")
    print(f"  • Min Market Cap: ${filters['min_market_cap']:,}")
    print(f"  • Max Change %: {filters['max_change_pct']:.1%}")
    print(f"  • Max Volatility: {filters['max_volatility']:.1%}")
    print()
    
    print("="*100)
    print("ANALYSIS: WHY EACH GAINER WAS FILTERED")
    print("="*100)
    
    for gainer in TOP_GAINERS:
        analysis = analyze_gainer(gainer, "AGGRESSIVE")
        
        print(f"\n{'='*100}")
        print(f"Symbol: {analysis['symbol']} (+{analysis['change_pct']})")
        print(f"{'='*100}")
        
        if analysis['would_pass']:
            print("✅ Would pass basic filters (but may fail on volume/market cap)")
        else:
            print("❌ FILTERED OUT - Reasons:")
            for i, reason in enumerate(analysis['reasons'], 1):
                print(f"   {i}. {reason}")
    
    print("\n" + "="*100)
    print("KEY FINDINGS")
    print("="*100)
    print()
    print("🎯 PRIMARY REASON: Change Percentage Too High")
    print("   • AGGRESSIVE mode allows max 30% moves")
    print("   • All top gainers moved 39-1487% (WAY over limit)")
    print("   • Algorithm is designed to AVOID chasing massive moves")
    print()
    print("🎯 SECONDARY REASONS:")
    print("   • Symbol format issues (dots, length, etc.)")
    print("   • Likely low market cap (penny stocks)")
    print("   • Likely low volume (illiquid)")
    print("   • Extreme volatility (gambling, not trading)")
    print()
    print("="*100)
    print("WHY THE ALGORITHM IS DESIGNED THIS WAY")
    print("="*100)
    print()
    print("✅ PROTECTS AGAINST:")
    print("   • Chasing massive moves (usually too late)")
    print("   • Penny stock manipulation")
    print("   • Low liquidity (can't exit positions)")
    print("   • Extreme volatility (gambling vs. trading)")
    print("   • Pump & dump schemes")
    print()
    print("✅ FOCUSES ON:")
    print("   • Quality setups with room to run")
    print("   • Liquid stocks (easy entry/exit)")
    print("   • Manageable risk (stop losses work)")
    print("   • Repeatable patterns (not lottery tickets)")
    print()
    print("💡 THESE TOP GAINERS ARE:")
    print("   • Already moved (chasing = bad entry)")
    print("   • Too volatile (stop losses won't work)")
    print("   • Likely low liquidity (slippage risk)")
    print("   • High manipulation risk (pump & dump)")
    print()
    print("="*100)
    print("RECOMMENDATION")
    print("="*100)
    print()
    print("Your algorithm is working CORRECTLY by filtering these out.")
    print("These are NOT quality day trading opportunities - they're lottery tickets.")
    print()
    print("If you want to catch these, you'd need:")
    print("  1. Pre-market scanner (catch them BEFORE they move)")
    print("  2. Much looser filters (but higher risk)")
    print("  3. Different strategy (momentum chasing vs. quality setups)")
    print()
    print("But beware: catching 1487% moves is luck, not skill.")
    print("Your algorithm focuses on repeatable, quality trades.")
    print()


if __name__ == "__main__":
    main()

