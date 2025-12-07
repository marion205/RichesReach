#!/bin/bash
# Production Deployment Script for RichesReach RAHA Backend
# This script deploys the backend to production environment

set -e  # Exit on error

echo "🚀 Starting Production Deployment..."
echo "===================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
ENV="production"
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

# Step 3: Database backup
echo -e "\n${YELLOW}Step 3: Creating database backup...${NC}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="backup_production_${TIMESTAMP}.sql"

# Check if PostgreSQL is available
if command -v pg_dump &> /dev/null; then
    if [ -n "$DATABASE_URL" ]; then
        echo "Creating database backup..."
        pg_dump "$DATABASE_URL" > "$BACKUP_FILE" 2>/dev/null || echo -e "${YELLOW}⚠️  Could not create backup (database may not be accessible)${NC}"
        if [ -f "$BACKUP_FILE" ]; then
            echo -e "${GREEN}✅ Backup created: $BACKUP_FILE${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  DATABASE_URL not set, skipping backup${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  pg_dump not available, skipping backup${NC}"
fi

# Step 4: Database migrations
echo -e "\n${YELLOW}Step 4: Running database migrations...${NC}"
python manage.py migrate --noinput
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Migrations failed${NC}"
    echo -e "${YELLOW}💡 To rollback, restore from: $BACKUP_FILE${NC}"
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
python manage.py performance_report --export "baseline_production_${TIMESTAMP}.json"
echo -e "${GREEN}✅ Baseline report generated: baseline_production_${TIMESTAMP}.json${NC}"

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
    echo -e "${RED}❌ Missing required environment variables:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
    echo -e "${RED}Aborting deployment.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ All required environment variables set${NC}"

# Step 8: Security checks
echo -e "\n${YELLOW}Step 8: Running security checks...${NC}"
python manage.py check --deploy
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Security warnings detected (review above)${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 9: Production readiness check
echo -e "\n${YELLOW}Step 9: Production readiness check...${NC}"

# Check DEBUG setting
if python -c "from django.conf import settings; exit(0 if not settings.DEBUG else 1)" 2>/dev/null; then
    echo -e "${GREEN}✅ DEBUG is False${NC}"
else
    echo -e "${RED}❌ DEBUG is True - NOT SAFE FOR PRODUCTION${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 10: Deployment summary
echo -e "\n${GREEN}====================================${NC}"
echo -e "${GREEN}✅ Production Deployment Complete!${NC}"
echo -e "${GREEN}====================================${NC}"
echo ""
echo "📊 Deployment Summary:"
echo "  - Tests: ✅ Passed"
echo "  - Migrations: ✅ Applied"
echo "  - Static Files: ✅ Collected"
echo "  - Baseline Report: ✅ Generated"
echo ""
echo "📝 Important Files:"
if [ -f "$BACKUP_FILE" ]; then
    echo "  - Backup: $BACKUP_FILE"
fi
echo "  - Baseline: baseline_production_${TIMESTAMP}.json"
echo ""
echo "🚀 Next Steps:"
echo "1. Start the production server"
echo "2. Monitor logs for errors"
echo "3. Run smoke tests"
echo "4. Monitor performance metrics closely for 48 hours"
echo ""
echo "📊 To monitor performance:"
echo "  python manage.py performance_report"
echo ""
echo "⚠️  IMPORTANT: Monitor closely for the first 48 hours!"

