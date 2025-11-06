#!/bin/bash
# Build Check Script for Backend and Frontend

set -e

echo "🔨 Building Backend and Frontend - Comprehensive Check"
echo "======================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0

# 1. Backend Python Syntax Check
echo "📊 1. Backend Python Syntax Check..."
echo "-----------------------------------"
cd deployment_package/backend
source venv/bin/activate 2>/dev/null || echo "⚠️  Virtual environment not found"

if python -m py_compile core/*.py 2>&1 | grep -i error; then
    echo -e "${RED}❌ Python syntax errors found${NC}"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✅ All Python files compile successfully${NC}"
fi

# 2. Django System Check
echo ""
echo "📊 2. Django System Check..."
echo "---------------------------"
if python manage.py check 2>&1 | grep -i "error\|exception"; then
    echo -e "${RED}❌ Django check found issues${NC}"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✅ Django system check passed${NC}"
fi

# 3. Django Migrations Check
echo ""
echo "📊 3. Django Migrations Check..."
echo "-------------------------------"
if python manage.py makemigrations --dry-run 2>&1 | grep -i "no changes"; then
    echo -e "${GREEN}✅ No pending migrations${NC}"
else
    echo -e "${YELLOW}⚠️  Pending migrations detected${NC}"
fi

# 4. Frontend TypeScript Check
echo ""
echo "📱 4. Frontend TypeScript Check..."
echo "--------------------------------"
cd ../../mobile

if command -v npx &> /dev/null; then
    if npx tsc --noEmit --skipLibCheck 2>&1 | grep -i "error\|warning" | head -10; then
        echo -e "${YELLOW}⚠️  TypeScript errors/warnings found${NC}"
        ERRORS=$((ERRORS + 1))
    else
        echo -e "${GREEN}✅ TypeScript check passed${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  npx not found, skipping TypeScript check${NC}"
fi

# 5. Frontend Dependencies Check
echo ""
echo "📱 5. Frontend Dependencies Check..."
echo "-----------------------------------"
if [ -f "package.json" ]; then
    if npm list --depth=0 2>&1 | grep -i "missing\|unmet"; then
        echo -e "${RED}❌ Missing dependencies${NC}"
        ERRORS=$((ERRORS + 1))
    else
        echo -e "${GREEN}✅ All dependencies installed${NC}"
    fi
else
    echo -e "${RED}❌ package.json not found${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 6. Summary
echo ""
echo "📋 BUILD CHECK SUMMARY"
echo "======================"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    echo ""
    echo "✅ Backend: Python syntax valid"
    echo "✅ Backend: Django system check passed"
    echo "✅ Frontend: TypeScript check passed"
    echo "✅ Frontend: Dependencies installed"
    exit 0
else
    echo -e "${RED}❌ Found $ERRORS issue(s)${NC}"
    echo ""
    echo "Please review the errors above"
    exit 1
fi

