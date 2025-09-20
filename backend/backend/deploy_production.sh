#!/bin/bash

# Production Deployment Script for RichesReach
# Uses existing production services and ML models

set -e

echo "🚀 Starting RichesReach Production Deployment..."

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Please run this script from the backend directory"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install it first."
    exit 1
fi

# Check if required services exist
echo "🔍 Checking production services..."

if [ ! -f "core/optimized_ml_service.py" ]; then
    echo "❌ OptimizedMLService not found"
    exit 1
fi

if [ ! -f "core/advanced_market_data_service.py" ]; then
    echo "❌ AdvancedMarketDataService not found"
    exit 1
fi

if [ ! -f "core/advanced_ml_algorithms.py" ]; then
    echo "❌ AdvancedMLAlgorithms not found"
    exit 1
fi

echo "✅ All production services found"

# Set up environment
echo "🔧 Setting up production environment..."

# Create production environment file if it doesn't exist
if [ ! -f ".env.production" ]; then
    echo "📝 Creating production environment file..."
    cat > .env.production << EOF
# Production Environment Variables
SECRET_KEY=your-super-secret-production-key-$(date +%s)
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database Configuration
DB_NAME=richesreach_prod
DB_USER=postgres
DB_PASSWORD=your-secure-database-password
DB_HOST=localhost
DB_PORT=5432

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# API Keys (set these with your actual keys)
FINNHUB_API_KEY=your-finnhub-api-key
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-api-key
POLYGON_API_KEY=your-polygon-api-key

# AWS Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-s3-bucket-name
AWS_S3_REGION_NAME=us-east-1

# Frontend URL
FRONTEND_URL=http://localhost:3000
EOF
    echo "⚠️  Please update .env.production with your actual API keys and configuration"
fi

# Install production dependencies
echo "📦 Installing production dependencies..."
pip install -r requirements_production.txt

# Set up database
echo "🗄️ Setting up production database..."
python3 manage.py makemigrations
python3 manage.py migrate

# Create superuser if it doesn't exist
echo "👤 Creating superuser..."
python3 manage.py shell << EOF
from core.models import User
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        email="admin@richesreach.com",
        name="Admin User",
        password="admin123"
    )
    print("Superuser created: admin@richesreach.com / admin123")
else:
    print("Superuser already exists")
EOF

# Set up sample data
echo "📊 Setting up sample data..."
python3 manage.py shell << EOF
from core.models import Stock
import random

# Create sample stocks if they don't exist
sample_stocks = [
    {
        "symbol": "AAPL",
        "company_name": "Apple Inc.",
        "sector": "Technology",
        "market_cap": 3000000000000,
        "pe_ratio": 25.5,
        "dividend_yield": 0.5,
        "beginner_friendly_score": 85,
        "current_price": 175.50
    },
    {
        "symbol": "MSFT",
        "company_name": "Microsoft Corporation",
        "sector": "Technology",
        "market_cap": 2800000000000,
        "pe_ratio": 28.0,
        "dividend_yield": 0.7,
        "beginner_friendly_score": 88,
        "current_price": 380.25
    },
    {
        "symbol": "GOOGL",
        "company_name": "Alphabet Inc.",
        "sector": "Technology",
        "market_cap": 1800000000000,
        "pe_ratio": 22.5,
        "dividend_yield": 0.0,
        "beginner_friendly_score": 75,
        "current_price": 140.80
    },
    {
        "symbol": "SPY",
        "company_name": "SPDR S&P 500 ETF Trust",
        "sector": "ETF",
        "market_cap": 400000000000,
        "pe_ratio": 20.0,
        "dividend_yield": 1.5,
        "beginner_friendly_score": 95,
        "current_price": 450.00
    },
    {
        "symbol": "VTI",
        "company_name": "Vanguard Total Stock Market ETF",
        "sector": "ETF",
        "market_cap": 300000000000,
        "pe_ratio": 19.5,
        "dividend_yield": 1.8,
        "beginner_friendly_score": 92,
        "current_price": 240.00
    }
]

for stock_data in sample_stocks:
    stock, created = Stock.objects.get_or_create(
        symbol=stock_data["symbol"],
        defaults=stock_data
    )
    if created:
        print(f"Created stock: {stock.symbol}")

print("Sample data setup completed")
EOF

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p media
mkdir -p staticfiles
mkdir -p ml_models

# Set up logging
echo "📊 Setting up logging..."
touch logs/django.log
touch logs/celery.log
touch logs/ml_service.log

# Test the production server
echo "🧪 Testing production server..."
python3 -c "
import sys
sys.path.append('.')
try:
    from unified_production_server import app
    print('✅ Production server imports successfully')
except Exception as e:
    print(f'❌ Production server import failed: {e}')
    sys.exit(1)
"

echo "✅ Production setup completed successfully!"
echo ""
echo "🎉 RichesReach is ready for production!"
echo ""
echo "📋 Next steps:"
echo "1. Update .env.production with your actual API keys"
echo "2. Configure your database (PostgreSQL recommended)"
echo "3. Set up Redis for caching and Celery"
echo "4. Configure your domain and SSL certificates"
echo ""
echo "🚀 To start the production server:"
echo "   python3 unified_production_server.py"
echo ""
echo "🔧 To start with specific settings:"
echo "   DJANGO_SETTINGS_MODULE=richesreach.settings_production python3 unified_production_server.py"
echo ""
echo "📊 To monitor the application:"
echo "   curl http://localhost:8000/health"
echo ""
echo "🎯 Your production API will be available at:"
echo "   http://localhost:8000"
echo "   http://localhost:8000/graphql/"
echo "   http://localhost:8000/docs (API documentation)"

