#!/bin/bash

# RichesReach - Archive More Outdated Documentation
# Archives additional status/completion/test reports

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}📚 Archiving Additional Outdated Documentation${NC}"
echo "=========================================="
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

ARCHIVE_DIR="docs/archive/outdated"
mkdir -p "$ARCHIVE_DIR"

# Additional files to archive - status/completion/test reports
ADDITIONAL_FILES=(
    # Status Reports
    "AWS_DEPLOYMENT_STATUS.md"
    "BACKEND_CONNECTION_VERIFIED.md"
    "BACKEND_RESTART_SUCCESS.md"
    "FUTURES_IMPLEMENTATION_STATUS.md"
    "MIGRATION_STATUS.md"
    "ML_LEARNING_STATUS.md"
    "MOBILE_TESTING_SUMMARY.md"
    "OPTIONS_FEATURES_STATUS.md"
    "POSTGRES_SETUP_COMPLETE.md"
    "SERVER_STATUS.md"
    "SENTRY_SETUP_COMPLETE.md"
    "SENTRY_COMPLETE_SUMMARY.md"
    "UNIFIED_MARKET_ENGINE_COMPLETE.md"
    "YODLEE_CREDENTIALS_CONFIGURED.md"
    
    # Test/Verification Reports
    "INTEGRATION_TEST_RESULTS.md"
    "MOBILE_NAVIGATION_TEST_GUIDE.md"
    "MOBILE_TEST_CHECKLIST.md"
    "OPTIONS_FEATURES_TEST_SUITE.md"
    "OPTIONS_FEATURES_VERIFICATION.md"
    "PRE_MARKET_TESTS_SUMMARY.md"
    "PRIVACY_SETTINGS_TEST_RESULTS.md"
    "PUSH_VERIFICATION.md"
    "SBLOC_VERIFICATION_RESULT.md"
    "TAX_OPTIMIZATION_TESTS_SUMMARY.md"
    "VERIFICATION_CHECKLIST.md"
    "VERIFY_LIVE_STREAM.md"
    
    # Completion/Implementation Summaries
    "FUTURES_PHASES_COMPLETE.md"
    "FUTURES_IMPLEMENTATION.md"
    "FUTURES_HARDENING_SUMMARY.md"
    "MEMEQUEST_IMPLEMENTATION_COMPLETE.md"
    "OPTIONS_GAPS_IMPLEMENTATION_SUMMARY.md"
    "SECURITY_AND_IMPROVEMENTS_SUMMARY.md"
    
    # Analysis Reports (historical)
    "COMPONENT_REACHABILITY_REPORT.md"
    "COMPREHENSIVE_IMPROVEMENTS_REPORT.md"
    "COVERAGE_ANALYSIS.md"
    "ENV_REVIEW_REPORT.md"
    "FEATURE_ACCESSIBILITY_REPORT.md"
    "FINAL_REACHABILITY_VERIFICATION.md"
    "PERFORMANCE_OPTIMIZATION_REPORT.md"
    "PRODUCTION_READINESS_REPORT.md"
    "SECURITY_AUDIT_REPORT.md"
    "SECURITIES_TRADING_ANALYSIS.md"
    "YODLEE_BUDGETING_ANALYSIS.md"
    "YODLEE_WIRED_SUMMARY.md"
    
    # Duplicate Competitive Analysis (keep only FINAL version)
    "OPTIONS_COMPETITIVE_ANALYSIS_2025.md"
    "OPTIONS_COMPETITIVE_COMPARISON.md"
    "OPTIONS_COMPETITIVE_GAP_ANALYSIS.md"
    
    # Old Setup/Implementation Guides (if superseded)
    "BACKEND_SERVER_SETUP.md"
    "BROKER_API_SETUP.md"
    "DAWN_RITUAL_TESTING_GUIDE.md"
    "DEPLOYMENT_CHECK.md"
    "DJANGO_SETTINGS_LOCATION.md"
    "HEY_RICHES_SETUP.md"
    "LIVE_STREAMING_SETUP.md"
    "MONITORING_SETUP.md"
    "MOBILE_APP_POSTGRES_CONNECTION.md"
    "POSTGRES_GRAPHQL_SETUP.md"
    "PRE_MARKET_ML_ALERTS_SETUP.md"
    "SELF_HOSTED_SETUP.md"
    "SENTRY_ALERTS_SETUP.md"
    "SENTRY_QUICK_ALERT_SETUP.md"
    "SERVER_START_INSTRUCTIONS.md"
    "YODLEE_SETUP_INSTRUCTIONS.md"
    
    # Old Roadmaps/Plans (if superseded)
    "IMPROVEMENTS_ROADMAP.md"
    "ML_DAY_TRADING_IMPROVEMENTS_PLAN.md"
    "OPTIONS_ML_IMPLEMENTATION_PLAN.md"
    "RICHESREACH_MARKET_DOMINATION_ROADMAP.md"
    "TOP_1_PERCENT_ROADMAP.md"
    "WEEK_3_AND_4_ROADMAP.md"
    
    # Checklists (if completed/outdated)
    "CES_2026_BOOTH_CHECKLIST.md"
    "COMPLIANCE_CHECKLIST.md"
    "IMPLEMENTATION_CHECKLIST.md"
    "LEGAL_REVIEW_CHECKLIST.md"
    "MERGE_CHECKLIST.md"
    "MOBILE_TEST_CHECKLIST.md"
    
    # Other status/summary files
    "ADDITIONAL_IMPROVEMENTS.md"
    "COMPLETE_PRE_MARKET_SYSTEM.md"
    "CONSTELLATION_PLACEMENT_RECOMMENDATION.md"
    "DAY_TRADING_COMPETITOR_COMPARISON.md"
    "DAY_TRADING_ML_LEARNING.md"
    "EDUCATIONAL_IMPROVEMENT_OPPORTUNITIES.md"
    "GRAPHQL_HARDENING.md"
    "KEY_FILTER_SNIPPETS.md"
    "LEVEL_UP_FEATURES.md"
    "LIVE_STREAMING_ENHANCEMENTS.md"
    "models_fix_guide.md"
    "models_fix_summary.md"
    "NETWORKING_DECK_10_SLIDES.md"
    "ONE_PAGER_OUTLINE.md"
    "PERFORMANCE_IMPROVEMENTS.md"
    "PRE_MARKET_SCANNER_SUMMARY.md"
    "QUICK_TEST_START.md"
    "REACT_HOOKS_HARDENING.md"
    "RELOAD_APP_INSTRUCTIONS.md"
    "RUST_STOCK_ANALYSIS_IMPLEMENTATION.md"
    "SCRIPTS.md"
    "STOCK_CHART_DATA_REFACTOR.md"
    "TAX_OPTIMIZATION_NEXT_STEPS.md"
    "TEMPLATE_RECOMMENDATIONS.md"
    "TROUBLESHOOT_DATA_ISSUE.md"
    "UPDATE_REDIS_AND_EMAIL.md"
    "WHAT_NEXT.md"
)

echo -e "${BLUE}📦 Archiving additional outdated files...${NC}"
echo ""

ARCHIVED_COUNT=0
NOT_FOUND_COUNT=0

for file in "${ADDITIONAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" "$ARCHIVE_DIR/"
        echo -e "${GREEN}✅ Archived: $file${NC}"
        ARCHIVED_COUNT=$((ARCHIVED_COUNT + 1))
    else
        NOT_FOUND_COUNT=$((NOT_FOUND_COUNT + 1))
    fi
done

echo ""
echo -e "${GREEN}=========================================="
echo "✅ Archive Complete!"
echo "==========================================${NC}"
echo ""
echo -e "${BLUE}Summary:${NC}"
echo "  • Files archived: $ARCHIVED_COUNT"
echo "  • Files not found: $NOT_FOUND_COUNT"
echo "  • Archive location: $ARCHIVE_DIR"
echo ""
echo -e "${YELLOW}Active documentation preserved:${NC}"
echo "  • README.md"
echo "  • COMPLETE_APP_DEMO_GUIDE.md"
echo "  • OPTIONS_COMPETITIVE_ANALYSIS_2025_FINAL.md"
echo "  • Setup guides that are still active"
echo "  • Technical documentation"
echo ""
echo -e "${GREEN}Additional outdated documentation archived! 📚${NC}"
echo ""

