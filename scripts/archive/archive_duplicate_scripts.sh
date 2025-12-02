#!/bin/bash

# RichesReach - Archive Duplicate/Outdated Shell Scripts
# Archives scripts that are duplicates or superseded by newer versions

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}📦 Archiving Duplicate/Outdated Shell Scripts${NC}"
echo "=========================================="
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

ARCHIVE_DIR="docs/archive/outdated/scripts"
mkdir -p "$ARCHIVE_DIR"

# Based on .main_server_note.md, we should use:
# - main_server.py (not manage.py)
# - start_backend_now.sh (recommended startup script)

# Duplicate/outdated backend startup scripts
# KEEP: start_backend_now.sh (uses main_server.py, recommended)
# ARCHIVE: Others that use old methods or are duplicates
DUPLICATE_SCRIPTS=(
    # Old backend startup scripts (superseded by start_backend_now.sh)
    "start_backend.sh"              # Uses old backend.final_complete_server
    "start_backend_fixed.sh"         # Old fixed version
    "start_django_backend.sh"        # Uses manage.py (old method)
    "start_local.sh"                 # Likely duplicate
    "start_local_dev.sh"             # Likely duplicate
    
    # Deployment scripts (consolidate to one)
    "deploy.sh"                      # Generic deploy
    "deploy_backend.sh"              # Backend-specific deploy
    "deploy_setup_env.sh"            # Setup script
    "EXECUTE_DEPLOYMENT.sh"          # Duplicate deployment
    
    # Test scripts (consolidate)
    "run_all_tests.sh"               # Generic test runner
    "run_comprehensive_tests.sh"     # Comprehensive tests (might overlap)
    
    # One-time fix scripts (no longer needed)
    "fix_django_settings.sh"        # One-time fix
    "fix_richesreach_ssl.sh"        # One-time fix
    "DEBUG_DATA_ISSUE.sh"            # One-time debug script
    
    # Cleanup scripts (we have newer ones)
    "cleanup_unused_files.sh"       # Old cleanup (we have cleanup_disk_space.sh)
    
    # Other potentially outdated scripts
    "build_check.sh"                 # Build check (might be outdated)
    "free_mac_space.sh"              # Generic cleanup (we have better ones)
)

echo -e "${BLUE}📦 Archiving duplicate/outdated scripts...${NC}"
echo ""

ARCHIVED_COUNT=0
NOT_FOUND_COUNT=0

for script in "${DUPLICATE_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        mv "$script" "$ARCHIVE_DIR/"
        echo -e "${GREEN}✅ Archived: $script${NC}"
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
echo "  • Scripts archived: $ARCHIVED_COUNT"
echo "  • Scripts not found: $NOT_FOUND_COUNT"
echo "  • Archive location: $ARCHIVE_DIR"
echo ""
echo -e "${YELLOW}Active scripts preserved:${NC}"
echo "  ✅ start_backend_now.sh - Recommended backend startup (uses main_server.py)"
echo "  ✅ restart_backend.sh - Restart script"
echo "  ✅ start_all_features.sh - Start all services"
echo "  ✅ bootstrap_backend.sh - Backend bootstrap"
echo "  ✅ run_tests.sh - Test runner"
echo "  ✅ run_full_app.sh - Full app runner"
echo "  ✅ deploy_to_production.sh - Production deployment"
echo "  ✅ All setup_*.sh scripts - Feature setup scripts"
echo "  ✅ All test_*.sh scripts - Test scripts"
echo "  ✅ cleanup_disk_space.sh - Disk cleanup"
echo "  ✅ archive_*.sh scripts - Documentation archiving"
echo ""
echo -e "${GREEN}Duplicate scripts archived! 📦${NC}"
echo ""

