#!/bin/bash

# RichesReach - Archive Outdated Documentation
# Moves outdated status/completion reports to docs/archive/outdated/ for review

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}📚 Archiving Outdated Documentation${NC}"
echo "=========================================="
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Create archive directory
ARCHIVE_DIR="docs/archive/outdated"
mkdir -p "$ARCHIVE_DIR"
echo -e "${GREEN}✅ Created archive directory: $ARCHIVE_DIR${NC}"
echo ""

# List of outdated status/completion reports to archive
# These are historical status reports, not active documentation
OUTDATED_FILES=(
    # Status Reports
    "AI_INSIGHTS_FIX.md"
    "AUTHENTICATION_FIX.md"
    "AUTHENTICATION_FIXED.md"
    "BACKEND_ALL_ERRORS_SUMMARY.md"
    "BACKEND_BUILD_ERRORS.md"
    "BACKEND_BUILD_STATUS.md"
    "BACKEND_ERRORS_SUMMARY.md"
    "BACKEND_STATUS.md"
    "BANK_INTEGRATIONS_STATUS.md"
    "BRANCH_COMPLETION_STATUS.md"
    "BUILD_ISSUES_REPORT.md"
    "BUILD_STATUS_FINAL.md"
    "CURRENT_STATUS.md"
    "DAILY_VOICE_DIGEST_FIX.md"
    "DEV_TOKEN_AUTH_FIX.md"
    "DJANGO_SETTINGS_FIX.md"
    "ELASTICACHE_STATUS.md"
    "EXPO_START_FIX.md"
    "FIXES_COMPLETE.md"
    "FIX_MARKET_DATA_NETWORK_ERROR.md"
    "FIX_NETWORK_ERRORS.md"
    "FIX_PDF_404_ERROR.md"
    "IP_ADDRESS_VERIFICATION.md"
    "LOGIN_FIX.md"
    "MOBILE_CONNECTION_FIX.md"
    "NAVIGATION_FIX.md"
    "NETWORK_TIMEOUT_FIX.md"
    "PAPER_TRADING_LOADING_FIX.md"
    "PAPER_TRADING_TIMEOUT_FIX.md"
    "PHYSICAL_DEVICE_CONNECTION_FIX.md"
    "SERVER_CONNECTION_FIX.md"
    "SERVER_RESTART_COMPLETE.md"
    
    # Test/Analysis Reports
    "AI_RECOMMENDATIONS_PERFORMANCE_ANALYSIS.md"
    "AI_RECOMMENDATIONS_TEST_RESULTS.md"
    "AI_RECOMMENDATIONS_TEST_SUMMARY.md"
    "ALGORITHM_ANALYSIS_SUMMARY.md"
    "COVERAGE_ANALYSIS.md"
    "TEST_RESULTS_FINAL.md"
    "TEST_RESULTS_SUMMARY.md"
    "TEST_RESULTS.md"
    "SYSTEM_TEST_REPORT.md"
    "SERVER_LOG_ANALYSIS.md"
    
    # Completion Reports
    "ALL_LEVEL_UP_FEATURES_COMPLETE.md"
    "CONSTELLATION_IMPLEMENTATION_COMPLETE.md"
    "FINAL_BUILD_STATUS.md"
    "FINAL_IMPLEMENTATION_SUMMARY.md"
    "FINAL_INTEGRATION_SUMMARY.md"
    "FINAL_STATUS.md"
    "FINAL_TASK_SUMMARY.md"
    "IMPLEMENTATION_COMPLETE.md"
    "MIGRATIONS_COMPLETE.md"
    "NEXT_STEPS_COMPLETE.md"
    "OPTIONS_FEATURES_IMPLEMENTATION_COMPLETE.md"
    "PERFORMANCE_OPTIMIZATION_COMPLETE.md"
    "PERFORMANCE_OPTIMIZATIONS_COMPLETE.md"
    "PERFORMANCE_SETUP_COMPLETE.md"
    "PHASE2_GESTURE_ACTIONS_COMPLETE.md"
    "SETUP_DAY_TRADING_COMPLETE.md"
    "TAX_OPTIMIZATION_COMPLETE.md"
    "WEBSOCKET_AND_PERFORMANCE_COMPLETE.md"
    "YODLEE_ENHANCEMENTS_COMPLETE.md"
    "YODLEE_IMPLEMENTATION_COMPLETE.md"
    "YODLEE_FINAL_STATUS.md"
    
    # Old Guides (superseded by newer versions)
    "DEMO_PITCH_GUIDE.md"
    "LOCAL_DEMO_READY.md"
    "LOCAL_DEMO_SETUP.md"
    "DEMO_VOICE_READY.md"
    
    # Old summaries
    "AI_ML_COMPLIANCE_SUMMARY.md"
    "BROKER_API_IMPLEMENTATION_SUMMARY.md"
    "EXECUTIVE_TECHNICAL_SUMMARY.md"
    "FEATURES_SUMMARY.md"
    "PROGRESS_SUMMARY.md"
    "REVIEW_SUMMARY.md"
    "TASK_COMPLETION_SUMMARY.md"
    
    # Old roadmaps (if superseded)
    "REMAINING_IMPROVEMENTS.md"
    "REMAINING_TASKS.md"
    "NEXT_STEPS_ROADMAP.md"
    "NEXT_STEPS_SUMMARY.md"
)

echo -e "${BLUE}📦 Archiving outdated files...${NC}"
echo ""

ARCHIVED_COUNT=0
NOT_FOUND_COUNT=0

for file in "${OUTDATED_FILES[@]}"; do
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
echo -e "${YELLOW}Note:${NC}"
echo "  • Files moved to archive (not deleted)"
echo "  • Review archive before permanent deletion"
echo "  • Active documentation preserved"
echo ""
echo -e "${GREEN}Outdated documentation archived! 📚${NC}"
echo ""

