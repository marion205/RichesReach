#!/bin/bash
# RichesReach API Keys Setup Script
# This script helps you configure your API keys
set -e
echo " RichesReach API Keys Setup"
echo "============================="
# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'
print_status() {
echo -e "${GREEN} $1${NC}"
}
print_warning() {
echo -e "${YELLOW} $1${NC}"
}
print_error() {
echo -e "${RED} $1${NC}"
}
# Check if we're in the right directory
if [ ! -f "backend/manage.py" ]; then
print_error "Please run this script from the RichesReach root directory"
exit 1
fi
# Create .env file if it doesn't exist
if [ ! -f "backend/.env" ]; then
print_status "Creating .env file from template..."
cp backend/env.example backend/.env
print_warning "Please edit backend/.env with your actual API keys"
else
print_status ".env file already exists"
fi
echo ""
echo " Next Steps:"
echo "1. Edit backend/.env with your API keys:"
echo " - NEWS_API_KEY=your-news-api-key"
echo " - ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key"
echo " - FINNHUB_API_KEY=your-finnhub-key"
echo ""
echo "2. Test your API keys:"
echo " python test_apis.py"
echo ""
echo "3. Start your backend:"
echo " cd backend && python manage.py runserver"
echo ""
echo "4. Start your mobile app:"
echo " cd mobile && npx expo start"
echo ""
print_status "Setup complete! Edit your .env file and test your APIs."
