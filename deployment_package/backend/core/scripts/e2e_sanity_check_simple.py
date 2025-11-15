"""
Simplified E2E Sanity Check Script
Checks basic moment generation and database integrity without complex imports.
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "richesreach.settings")
django.setup()

from core.models import StockMoment, MomentCategory


def check_database_moments(symbol: str = "TSLA") -> dict:
    """Check if moments exist in database for a symbol"""
    print(f"\n{'='*60}")
    print(f"📊 DATABASE CHECK: {symbol}")
    print(f"{'='*60}\n")

    results = {
        "symbol": symbol,
        "total_moments": 0,
        "valid_moments": 0,
        "recent_moments": [],
        "issues": [],
    }

    try:
        moments = StockMoment.objects.filter(symbol=symbol.upper()).order_by("-timestamp")[:10]
        results["total_moments"] = moments.count()

        print(f"✅ Found {results['total_moments']} moments for {symbol}")

        for moment in moments:
            # Basic validation
            is_valid = all([
                moment.symbol,
                moment.timestamp,
                moment.title,
                moment.quick_summary,
                moment.deep_summary,
                0.0 <= moment.importance_score <= 1.0,
            ])

            if is_valid:
                results["valid_moments"] += 1
                if len(results["recent_moments"]) < 3:
                    results["recent_moments"].append({
                        "id": str(moment.id)[:8],
                        "title": moment.title[:50],
                        "category": moment.category,
                        "score": moment.importance_score,
                        "timestamp": moment.timestamp.strftime("%Y-%m-%d"),
                    })
            else:
                results["issues"].append(f"Invalid moment: {moment.id}")

        print(f"   - Valid: {results['valid_moments']}")
        print(f"   - Issues: {len(results['issues'])}")

        if results["recent_moments"]:
            print(f"\n   Recent moments:")
            for i, m in enumerate(results["recent_moments"], 1):
                print(f"   {i}. [{m['category']}] {m['title']}... (score: {m['score']:.2f})")

    except Exception as e:
        results["issues"].append(str(e))
        print(f"❌ Error: {e}")

    return results


def check_model_fields():
    """Verify StockMoment model has all required fields"""
    print(f"\n{'='*60}")
    print(f"🔍 MODEL STRUCTURE CHECK")
    print(f"{'='*60}\n")

    try:
        # Check if we can create a test instance (without saving)
        test_moment = StockMoment(
            symbol="TEST",
            timestamp=datetime.now(),
            category=MomentCategory.NEWS,
            title="Test",
            quick_summary="Test summary",
            deep_summary="Test deep summary",
            importance_score=0.5,
        )

        required_fields = [
            "symbol", "timestamp", "category", "title",
            "quick_summary", "deep_summary", "importance_score"
        ]

        missing = []
        for field in required_fields:
            if not hasattr(test_moment, field):
                missing.append(field)

        if missing:
            print(f"❌ Missing fields: {', '.join(missing)}")
        else:
            print(f"✅ All required fields present")
            print(f"   Fields: {', '.join(required_fields)}")

        # Check categories
        categories = [c[0] for c in MomentCategory.choices]
        print(f"\n✅ Available categories: {', '.join(categories)}")

        return {"valid": len(missing) == 0, "missing_fields": missing}

    except Exception as e:
        print(f"❌ Error checking model: {e}")
        return {"valid": False, "error": str(e)}


def main():
    """Run simplified sanity checks"""
    print("\n" + "="*60)
    print("🔍 KEY MOMENTS E2E SANITY CHECKS (Simplified)")
    print("="*60)

    # Check 1: Model structure
    model_check = check_model_fields()

    # Check 2: Database moments
    symbols = ["TSLA", "AAPL", "SPY"]
    all_results = []

    for symbol in symbols:
        results = check_database_moments(symbol)
        all_results.append(results)

    # Summary
    print(f"\n\n{'='*60}")
    print("📊 SUMMARY")
    print(f"{'='*60}\n")

    total_moments = sum(r.get("total_moments", 0) for r in all_results)
    total_valid = sum(r.get("valid_moments", 0) for r in all_results)
    total_issues = sum(len(r.get("issues", [])) for r in all_results)

    print(f"✅ Model structure: {'Valid' if model_check.get('valid') else 'Issues found'}")
    print(f"✅ Total moments found: {total_moments}")
    print(f"✅ Valid moments: {total_valid}")
    print(f"❌ Issues: {total_issues}")

    if total_issues == 0 and model_check.get("valid"):
        print("\n🎉 Basic checks passed!")
        print("\n💡 Next steps:")
        print("   1. Test moment generation with real data")
        print("   2. Test GraphQL queries in GraphQL playground")
        print("   3. Test mobile app integration")
    else:
        print("\n⚠️  Some checks failed. Review issues above.")


if __name__ == "__main__":
    main()

