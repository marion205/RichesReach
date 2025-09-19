#!/usr/bin/env python3
"""
Production Setup Script for RichesReach
This script sets up the production environment with real APIs, ML, and database
"""
import os
import sys
import django
from pathlib import Path
import subprocess
import time

# Add the backend directory to Python path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings_production')

# Setup Django
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection
from core.models import User, Stock, IncomeProfile
import requests
import json

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return None

def setup_database():
    """Set up the production database"""
    print("🗄️ Setting up production database...")
    
    # Run migrations
    run_command("python manage.py makemigrations", "Creating migrations")
    run_command("python manage.py migrate", "Running migrations")
    
    # Create superuser if it doesn't exist
    if not User.objects.filter(is_superuser=True).exists():
        print("👤 Creating superuser...")
        User.objects.create_superuser(
            email="admin@richesreach.com",
            name="Admin User",
            password="admin123"  # Change this in production!
        )
        print("✅ Superuser created: admin@richesreach.com / admin123")
    
    print("✅ Database setup completed")

def setup_sample_data():
    """Set up sample data for production"""
    print("📊 Setting up sample data...")
    
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
            print(f"✅ Created stock: {stock.symbol}")
    
    print("✅ Sample data setup completed")

def test_api_connections():
    """Test API connections"""
    print("🔌 Testing API connections...")
    
    # Test Finnhub API
    finnhub_key = os.getenv('FINNHUB_API_KEY')
    if finnhub_key:
        try:
            response = requests.get(f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={finnhub_key}", timeout=10)
            if response.status_code == 200:
                print("✅ Finnhub API connection successful")
            else:
                print(f"⚠️ Finnhub API returned status {response.status_code}")
        except Exception as e:
            print(f"❌ Finnhub API connection failed: {e}")
    else:
        print("⚠️ FINNHUB_API_KEY not set")
    
    # Test Alpha Vantage API
    alpha_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if alpha_key:
        try:
            response = requests.get(f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey={alpha_key}", timeout=10)
            if response.status_code == 200:
                print("✅ Alpha Vantage API connection successful")
            else:
                print(f"⚠️ Alpha Vantage API returned status {response.status_code}")
        except Exception as e:
            print(f"❌ Alpha Vantage API connection failed: {e}")
    else:
        print("⚠️ ALPHA_VANTAGE_API_KEY not set")

def setup_ml_models():
    """Set up ML models"""
    print("🤖 Setting up ML models...")
    
    # Create models directory
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    # This would typically download or train models
    print("✅ ML models setup completed (placeholder)")

def setup_monitoring():
    """Set up monitoring and logging"""
    print("📊 Setting up monitoring...")
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create log files
    (logs_dir / "django.log").touch()
    (logs_dir / "celery.log").touch()
    (logs_dir / "ml_service.log").touch()
    
    print("✅ Monitoring setup completed")

def main():
    """Main setup function"""
    print("🚀 Starting RichesReach Production Setup...")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("manage.py").exists():
        print("❌ Please run this script from the backend directory")
        sys.exit(1)
    
    # Check environment variables
    required_vars = ['SECRET_KEY', 'DB_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set up your .env file with production values")
        sys.exit(1)
    
    try:
        # Setup steps
        setup_database()
        setup_sample_data()
        test_api_connections()
        setup_ml_models()
        setup_monitoring()
        
        print("=" * 50)
        print("🎉 Production setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Configure your API keys in the environment")
        print("2. Set up AWS services (RDS, ElastiCache, S3)")
        print("3. Deploy using Docker or AWS ECS")
        print("4. Configure your domain and SSL certificates")
        print("\n🔧 To start the production server:")
        print("   python production_server.py")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

