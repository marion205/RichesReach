"""
E2E Sanity Check Script
Walks through the moment generation and consumption paths to verify everything works.
"""

import os
import sys
import django
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "richesreach.settings")
django.setup()

from core.models import StockMoment, MomentCategory
from core.queries import Query
from core.stock_moment_worker import (
    RawMomentJob,
    PriceContext,
    Event as WorkerEvent,
    create_stock_moment_from_job,
    fetch_events_for_moment,
)
import asyncio


def check_moment_generation(symbol: str = "TSLA") -> Dict[str, Any]:
    """
    Check 1: Moment generation path
    - Backend worker pulls data → calls LLM → inserts StockMoment
    """
    print(f"\n{'='*60}")
    print(f"1️⃣  MOMENT GENERATION PATH CHECK: {symbol}")
    print(f"{'='*60}\n")

    results = {
        "symbol": symbol,
        "moments_created": 0,
        "moments_skipped": 0,
        "errors": [],
        "sample_moment": None,
    }

    # Create a test moment job
    timestamp = datetime.now() - timedelta(days=7)
    price_ctx = PriceContext(
        start_price=150.0,
        end_price=165.0,
        pct_change=10.0,
        volume_vs_average="150%",
    )

    # Create test events
    events = [
        WorkerEvent(
            type="NEWS",
            time=timestamp,
            headline=f"{symbol} Announces New Product",
            summary="Company announced major product launch",
            url="https://example.com/news",
        ),
        WorkerEvent(
            type="EARNINGS",
            time=timestamp,
            headline=f"{symbol} Q4 Earnings Beat Expectations",
            summary="Earnings exceeded analyst estimates",
        ),
    ]

    job = RawMomentJob(
        symbol=symbol,
        timestamp=timestamp,
        price_context=price_ctx,
        events=events,
    )

    try:
        print(f"📝 Creating moment for {symbol} @ {timestamp.isoformat()}")
        moment = create_stock_moment_from_job(job)

        if moment:
            results["moments_created"] = 1
            results["sample_moment"] = {
                "id": str(moment.id),
                "symbol": moment.symbol,
                "timestamp": moment.timestamp.isoformat(),
                "category": moment.category,
                "importance_score": moment.importance_score,
                "title": moment.title,
                "has_source_links": len(moment.source_links) > 0,
            }

            print(f"✅ Moment created: {moment.id}")
            print(f"   - Symbol: {moment.symbol}")
            print(f"   - Category: {moment.category}")
            print(f"   - Importance: {moment.importance_score:.2f}")
            print(f"   - Title: {moment.title[:50]}...")
            print(f"   - Source links: {len(moment.source_links)}")
        else:
            results["moments_skipped"] = 1
            print(f"⚠️  Moment skipped (low importance score)")

    except Exception as e:
        results["errors"].append(str(e))
        print(f"❌ Error creating moment: {e}")

    return results


def check_graphql_query(symbol: str = "TSLA", range: str = "ONE_MONTH") -> Dict[str, Any]:
    """
    Check 2: GraphQL query returns moments correctly
    """
    print(f"\n{'='*60}")
    print(f"2️⃣  GRAPHQL QUERY CHECK: {symbol} ({range})")
    print(f"{'='*60}\n")

    results = {
        "symbol": symbol,
        "range": range,
        "moments_returned": 0,
        "moments": [],
        "errors": [],
    }

    try:
        query = Query()
        moments = query.resolve_stock_moments(None, symbol=symbol, range=range)

        results["moments_returned"] = len(moments)
        results["moments"] = [
            {
                "id": str(m.id),
                "symbol": m.symbol,
                "timestamp": m.timestamp.isoformat(),
                "category": m.category,
                "title": m.title,
            }
            for m in moments[:5]  # First 5
        ]

        print(f"✅ GraphQL query returned {len(moments)} moments")
        for i, moment in enumerate(moments[:3], 1):
            print(f"   {i}. {moment.category}: {moment.title[:40]}...")

    except Exception as e:
        results["errors"].append(str(e))
        print(f"❌ GraphQL query error: {e}")

    return results


def check_database_integrity(symbol: str = "TSLA") -> Dict[str, Any]:
    """
    Check 3: Database integrity
    - Verify moments have sane data
    """
    print(f"\n{'='*60}")
    print(f"3️⃣  DATABASE INTEGRITY CHECK: {symbol}")
    print(f"{'='*60}\n")

    results = {
        "symbol": symbol,
        "total_moments": 0,
        "valid_moments": 0,
        "invalid_moments": [],
        "issues": [],
    }

    try:
        moments = StockMoment.objects.filter(symbol=symbol.upper()).order_by("-timestamp")[:20]

        results["total_moments"] = moments.count()

        for moment in moments:
            issues = []

            # Check required fields
            if not moment.symbol:
                issues.append("Missing symbol")
            if not moment.timestamp:
                issues.append("Missing timestamp")
            if not moment.title:
                issues.append("Missing title")
            if not moment.quick_summary:
                issues.append("Missing quick_summary")
            if not moment.deep_summary:
                issues.append("Missing deep_summary")

            # Check importance score range
            if not (0.0 <= moment.importance_score <= 1.0):
                issues.append(f"Invalid importance_score: {moment.importance_score}")

            # Check category
            valid_categories = [c[0] for c in MomentCategory.choices]
            if moment.category not in valid_categories:
                issues.append(f"Invalid category: {moment.category}")

            if issues:
                results["invalid_moments"].append({
                    "id": str(moment.id),
                    "issues": issues,
                })
            else:
                results["valid_moments"] += 1

        print(f"✅ Found {results['total_moments']} moments")
        print(f"   - Valid: {results['valid_moments']}")
        print(f"   - Invalid: {len(results['invalid_moments'])}")

        if results["invalid_moments"]:
            print(f"\n⚠️  Issues found:")
            for invalid in results["invalid_moments"][:3]:
                print(f"   - {invalid['id']}: {', '.join(invalid['issues'])}")

    except Exception as e:
        results["issues"].append(str(e))
        print(f"❌ Database check error: {e}")

    return results


async def check_event_fetching(symbol: str = "TSLA") -> Dict[str, Any]:
    """
    Check 4: Event fetching from unified data service
    """
    print(f"\n{'='*60}")
    print(f"4️⃣  EVENT FETCHING CHECK: {symbol}")
    print(f"{'='*60}\n")

    results = {
        "symbol": symbol,
        "events_fetched": 0,
        "event_types": {},
        "errors": [],
    }

    try:
        timestamp = datetime.now() - timedelta(days=7)
        events = await fetch_events_for_moment(symbol, timestamp, window_hours=48)

        results["events_fetched"] = len(events)
        for event in events:
            event_type = event.type
            results["event_types"][event_type] = results["event_types"].get(event_type, 0) + 1

        print(f"✅ Fetched {len(events)} events")
        for event_type, count in results["event_types"].items():
            print(f"   - {event_type}: {count}")

    except Exception as e:
        results["errors"].append(str(e))
        print(f"❌ Event fetching error: {e}")

    return results


def main():
    """Run all sanity checks"""
    print("\n" + "="*60)
    print("🔍 KEY MOMENTS E2E SANITY CHECKS")
    print("="*60)

    symbols = ["TSLA", "AAPL", "SPY"]
    all_results = []

    for symbol in symbols:
        print(f"\n\n{'#'*60}")
        print(f"Testing: {symbol}")
        print(f"{'#'*60}")

        # Check 1: Moment generation
        gen_results = check_moment_generation(symbol)
        all_results.append(gen_results)

        # Check 2: GraphQL query
        graphql_results = check_graphql_query(symbol, "ONE_MONTH")
        all_results.append(graphql_results)

        # Check 3: Database integrity
        db_results = check_database_integrity(symbol)
        all_results.append(db_results)

        # Check 4: Event fetching (async)
        event_results = asyncio.run(check_event_fetching(symbol))
        all_results.append(event_results)

    # Summary
    print(f"\n\n{'='*60}")
    print("📊 SUMMARY")
    print(f"{'='*60}\n")

    total_moments = sum(r.get("moments_created", 0) for r in all_results)
    total_errors = sum(len(r.get("errors", [])) for r in all_results)

    print(f"✅ Moments created: {total_moments}")
    print(f"❌ Total errors: {total_errors}")

    if total_errors == 0:
        print("\n🎉 All checks passed!")
    else:
        print("\n⚠️  Some checks failed. Review errors above.")


if __name__ == "__main__":
    main()

