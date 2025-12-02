#!/bin/bash

# RichesReach - Disk Space Cleanup Script
# Safely removes unnecessary files to free up disk space

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🧹 RichesReach Disk Space Cleanup${NC}"
echo "=========================================="
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Calculate space before
echo -e "${YELLOW}📊 Calculating disk usage before cleanup...${NC}"
SPACE_BEFORE=$(du -sh . 2>/dev/null | cut -f1)
echo "Current size: $SPACE_BEFORE"
echo ""

# 1. Remove Python cache files
echo -e "${BLUE}1️⃣  Removing Python cache files...${NC}"
PYCACHE_COUNT=$(find . -type d -name "__pycache__" ! -path "*/venv/*" ! -path "*/node_modules/*" 2>/dev/null | wc -l | tr -d ' ')
if [ "$PYCACHE_COUNT" -gt 0 ]; then
    find . -type d -name "__pycache__" ! -path "*/venv/*" ! -path "*/node_modules/*" -exec rm -rf {} + 2>/dev/null
    echo -e "${GREEN}✅ Removed $PYCACHE_COUNT __pycache__ directories${NC}"
else
    echo -e "${YELLOW}⚠️  No __pycache__ directories found${NC}"
fi

PYC_COUNT=$(find . -type f -name "*.pyc" ! -path "*/venv/*" ! -path "*/node_modules/*" 2>/dev/null | wc -l | tr -d ' ')
if [ "$PYC_COUNT" -gt 0 ]; then
    find . -type f -name "*.pyc" ! -path "*/venv/*" ! -path "*/node_modules/*" -delete 2>/dev/null
    echo -e "${GREEN}✅ Removed $PYC_COUNT .pyc files${NC}"
else
    echo -e "${YELLOW}⚠️  No .pyc files found${NC}"
fi

# 2. Remove test cache and coverage files
echo ""
echo -e "${BLUE}2️⃣  Removing test cache and coverage files...${NC}"
if [ -d ".pytest_cache" ]; then
    rm -rf .pytest_cache
    echo -e "${GREEN}✅ Removed .pytest_cache${NC}"
fi
if [ -d "deployment_package/backend/.pytest_cache" ]; then
    rm -rf deployment_package/backend/.pytest_cache
    echo -e "${GREEN}✅ Removed deployment_package/backend/.pytest_cache${NC}"
fi
if [ -d "backend/.pytest_cache" ]; then
    rm -rf backend/.pytest_cache
    echo -e "${GREEN}✅ Removed backend/.pytest_cache${NC}"
fi
if [ -f "deployment_package/backend/.coverage" ]; then
    rm -f deployment_package/backend/.coverage
    echo -e "${GREEN}✅ Removed .coverage file${NC}"
fi
if [ -d "deployment_package/backend/htmlcov" ]; then
    rm -rf deployment_package/backend/htmlcov
    echo -e "${GREEN}✅ Removed htmlcov directory${NC}"
fi

# 3. Remove OS-specific files
echo ""
echo -e "${BLUE}3️⃣  Removing OS-specific files...${NC}"
DS_STORE_COUNT=$(find . -type f -name ".DS_Store" ! -path "*/venv/*" ! -path "*/node_modules/*" 2>/dev/null | wc -l | tr -d ' ')
if [ "$DS_STORE_COUNT" -gt 0 ]; then
    find . -type f -name ".DS_Store" ! -path "*/venv/*" ! -path "*/node_modules/*" -delete 2>/dev/null
    echo -e "${GREEN}✅ Removed $DS_STORE_COUNT .DS_Store files${NC}"
else
    echo -e "${YELLOW}⚠️  No .DS_Store files found${NC}"
fi

# 4. Remove editor swap files
echo ""
echo -e "${BLUE}4️⃣  Removing editor swap files...${NC}"
SWAP_COUNT=$(find . -type f \( -name "*.swp" -o -name "*.swo" -o -name "*~" \) ! -path "*/venv/*" ! -path "*/node_modules/*" ! -path "*/.git/*" 2>/dev/null | wc -l | tr -d ' ')
if [ "$SWAP_COUNT" -gt 0 ]; then
    find . -type f \( -name "*.swp" -o -name "*.swo" -o -name "*~" \) ! -path "*/venv/*" ! -path "*/node_modules/*" ! -path "*/.git/*" -delete 2>/dev/null
    echo -e "${GREEN}✅ Removed $SWAP_COUNT swap files${NC}"
else
    echo -e "${YELLOW}⚠️  No swap files found${NC}"
fi

# 5. Remove old log files (keep recent ones)
echo ""
echo -e "${BLUE}5️⃣  Removing old log files...${NC}"
LOG_COUNT=$(find . -type f \( -name "*.log" -o -name "*.tmp" \) ! -path "*/venv/*" ! -path "*/node_modules/*" ! -path "*/mobile/.expo/*" ! -name "package-lock.json" 2>/dev/null | wc -l | tr -d ' ')
if [ "$LOG_COUNT" -gt 0 ]; then
    # Keep logs in mobile/.expo and recent logs in /tmp
    find . -type f \( -name "*.log" -o -name "*.tmp" \) ! -path "*/venv/*" ! -path "*/node_modules/*" ! -path "*/mobile/.expo/*" ! -path "*/mobile/artifacts/*" -mtime +7 -delete 2>/dev/null
    echo -e "${GREEN}✅ Removed old log files (kept recent ones)${NC}"
else
    echo -e "${YELLOW}⚠️  No log files found${NC}"
fi

# 6. Remove build artifacts (but keep important ones)
echo ""
echo -e "${BLUE}6️⃣  Cleaning build artifacts...${NC}"
if [ -d "mobile/build" ] && [ -f "mobile/build/full.log" ]; then
    rm -f mobile/build/*.log 2>/dev/null
    echo -e "${GREEN}✅ Removed mobile build logs${NC}"
fi
if [ -d "mobile/bundle-analysis" ]; then
    rm -f mobile/bundle-analysis/*.log 2>/dev/null
    echo -e "${GREEN}✅ Removed bundle analysis logs${NC}"
fi
if [ -f "rust_crypto_engine/rust_engine.log" ]; then
    rm -f rust_crypto_engine/rust_engine.log
    echo -e "${GREEN}✅ Removed rust engine log${NC}"
fi

# 7. Remove Python __pycache__ in venv (safe, will regenerate)
echo ""
echo -e "${BLUE}7️⃣  Cleaning venv cache (safe to remove)...${NC}"
if [ -d "venv" ]; then
    VENV_PYCACHE=$(find venv -type d -name "__pycache__" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$VENV_PYCACHE" -gt 0 ]; then
        find venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
        find venv -type f -name "*.pyc" -delete 2>/dev/null
        echo -e "${GREEN}✅ Cleaned venv cache (will regenerate on next use)${NC}"
    fi
fi
if [ -d "deployment_package/backend/venv" ]; then
    VENV_PYCACHE=$(find deployment_package/backend/venv -type d -name "__pycache__" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$VENV_PYCACHE" -gt 0 ]; then
        find deployment_package/backend/venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
        find deployment_package/backend/venv -type f -name "*.pyc" -delete 2>/dev/null
        echo -e "${GREEN}✅ Cleaned deployment_package/backend/venv cache${NC}"
    fi
fi

# Calculate space after
echo ""
echo -e "${YELLOW}📊 Calculating disk usage after cleanup...${NC}"
SPACE_AFTER=$(du -sh . 2>/dev/null | cut -f1)
echo "New size: $SPACE_AFTER"
echo ""

# Summary
echo -e "${GREEN}=========================================="
echo "✅ Cleanup Complete!"
echo "==========================================${NC}"
echo ""
echo -e "${BLUE}Summary:${NC}"
echo "  • Python cache files removed"
echo "  • Test cache files removed"
echo "  • OS-specific files removed"
echo "  • Editor swap files removed"
echo "  • Old log files removed"
echo "  • Build artifacts cleaned"
echo ""
echo -e "${YELLOW}Note:${NC}"
echo "  • node_modules (1.2GB) kept - required for app"
echo "  • venv kept - required for Python"
echo "  • Recent logs kept - only old ones removed"
echo "  • Source code and configs preserved"
echo ""
echo -e "${GREEN}All unnecessary files removed! 🎉${NC}"
echo ""

