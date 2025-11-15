#!/bin/bash
# Cleanup unused files

echo "🧹 Cleaning up unused files..."

# Test result files
rm -f benchmark_stock_results.json e2e_test_results.json

# Temporary scripts
rm -f create_test_moments_sqlite.py missing_endpoints.py remove_all_hardcoded_values.py
rm -f run_sql_commands.py fix_sbloc_health.py production_health_check.py

# Unused GraphQL query file
rm -f mobile/src/graphql/queries_comprehensive.ts

# Old status reports
rm -f BACKEND_ISSUE_FOUND.md FIXES_APPLIED.md INDENTATION_FIX_STATUS.md
rm -f INSTANT_STORY_FIX.md POLISH_AND_GUARDRAILS_COMPLETE.md SQLITE_SETUP_COMPLETE.md
rm -f USE_REAL_DATA.md WHAT_LEFT_TO_DO.md IMPLEMENTATION_SUMMARY.md

echo "✅ Cleanup complete!"
