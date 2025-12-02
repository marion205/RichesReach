#!/bin/bash
# Setup script for market data API keys
# Run this before starting the server to configure market data providers

echo "🔑 Setting up market data API keys..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    touch .env
fi

# Add market data keys to .env (commented out - user needs to add real keys)
echo "" >> .env
echo "# Market Data API Keys" >> .env
echo "# Uncomment and add your real API keys:" >> .env
echo "# export POLYGON_API_KEY=\"pk_...your_polygon_key...\"" >> .env
echo "# export FINNHUB_API_KEY=\"fh_...your_finnhub_key...\"" >> .env
echo "# export ALPHAVANTAGE_API_KEY=\"av_...your_alpha_vantage_key...\"" >> .env
echo "" >> .env
echo "# Optional: Enable mock data for testing" >> .env
echo "# export USE_MARKET_MOCK=\"true\"" >> .env

echo "✅ .env file updated with market data key placeholders"
echo ""
echo "📝 Next steps:"
echo "1. Get API keys from:"
echo "   - Polygon.io: https://polygon.io/dashboard"
echo "   - Finnhub: https://finnhub.io/register"
echo "   - Alpha Vantage: https://www.alphavantage.co/support/#api-key"
echo ""
echo "2. Edit .env file and uncomment/add your real keys"
echo ""
echo "3. Start the server:"
echo "   cd backend/backend && PORT=8000 python3 final_complete_server.py"
echo ""
echo "4. Test the endpoint:"
echo "   curl 'http://localhost:8000/api/market/quotes?symbols=AAPL,MSFT'"
