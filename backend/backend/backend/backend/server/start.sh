#!/bin/bash

# RichesReach Production Server Startup Script

echo "🚀 Starting RichesReach Production Server..."

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not running. Please start Redis first:"
    echo "   brew install redis && brew services start redis"
    echo "   or: redis-server"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cat > .env << EOF
ENV=prod
ALPHA_VANTAGE_KEY=OHYSFF1AE446O7CR
FINNHUB_KEY=d2rnitpr01qv11lfegugd2rnitpr01qv11lfegv0
NEWS_API_KEY=94a335c7316145f79840edd62f77e11e
SECRET_KEY=change-this-in-production
REDIS_URL=redis://localhost:6379/0
EOF
    echo "✅ Created .env file with default values"
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo "🔧 Starting server on http://localhost:8000"
echo "📊 GraphQL Playground: http://localhost:8000/graphql"
echo "❤️  Health Check: http://localhost:8000/health"
echo "📈 Metrics: http://localhost:8000/metrics"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
