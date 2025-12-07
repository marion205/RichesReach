#!/bin/bash
# Staging Deployment Script for RichesReach RAHA Backend
# This script deploys the backend to staging environment

set -e  # Exit on error

echo "🚀 Starting Staging Deployment..."
echo "=================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
ENV="staging"
BACKEND_DIR="deployment_package/backend"
VENV_PATH="$BACKEND_DIR/venv"

# Step 1: Pre-deployment checks
echo -e "\n${YELLOW}Step 1: Pre-deployment checks...${NC}"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}❌ Virtual environment not found at $VENV_PATH${NC}"
    exit 1
fi

# Activate virtual environment
source "$VENV_PATH/bin/activate"

# Check Python version
PYTHON_VERSION=$(python --version)
echo "✅ Python: $PYTHON_VERSION"

# Check Django installation
if ! python -c "import django" 2>/dev/null; then
    echo -e "${RED}❌ Django not installed${NC}"
    exit 1
fi
echo "✅ Django installed"

# Step 2: Run tests
echo -e "\n${YELLOW}Step 2: Running tests...${NC}"
cd "$BACKEND_DIR"
python manage.py test core.tests.test_raha_performance --verbosity=1
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Tests failed. Aborting deployment.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ All tests passed${NC}"

# Step 3: Check for uncommitted changes
echo -e "\n${YELLOW}Step 3: Checking for uncommitted changes...${NC}"
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️  Warning: Uncommitted changes detected${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 4: Database migrations
echo -e "\n${YELLOW}Step 4: Running database migrations...${NC}"
python manage.py migrate --noinput
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Migrations failed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Migrations applied${NC}"

# Step 5: Collect static files
echo -e "\n${YELLOW}Step 5: Collecting static files...${NC}"
python manage.py collectstatic --noinput
echo -e "${GREEN}✅ Static files collected${NC}"

# Step 6: Generate baseline performance report
echo -e "\n${YELLOW}Step 6: Generating baseline performance report...${NC}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
python manage.py performance_report --export "baseline_staging_${TIMESTAMP}.json"
echo -e "${GREEN}✅ Baseline report generated: baseline_staging_${TIMESTAMP}.json${NC}"

# Step 7: Check environment variables
echo -e "\n${YELLOW}Step 7: Checking environment variables...${NC}"
REQUIRED_VARS=("SECRET_KEY" "DATABASE_URL")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Warning: Missing environment variables:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 8: Health check
echo -e "\n${YELLOW}Step 8: Running health check...${NC}"
python manage.py check --deploy
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Health check warnings (non-critical)${NC}"
fi

# Step 9: Deployment summary
echo -e "\n${GREEN}==================================${NC}"
echo -e "${GREEN}✅ Staging Deployment Complete!${NC}"
echo -e "${GREEN}==================================${NC}"
echo ""
echo "Next steps:"
echo "1. Start the server: python manage.py runserver 0.0.0.0:8000"
echo "2. Monitor logs for errors"
echo "3. Run smoke tests"
echo "4. Monitor performance metrics"
echo ""
echo "Baseline report: baseline_staging_${TIMESTAMP}.json"
echo ""
echo "To monitor performance:"
echo "  python manage.py performance_report"

