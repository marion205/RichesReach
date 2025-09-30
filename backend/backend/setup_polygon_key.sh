#!/bin/bash

echo "🚀 Polygon API Key Setup"
echo "========================"

# Check if API key is provided as argument
if [ -z "$1" ]; then
    echo "❌ Please provide your Polygon API key as an argument"
    echo "Usage: ./setup_polygon_key.sh YOUR_API_KEY_HERE"
    echo ""
    echo "📝 To get an API key:"
    echo "1. Go to https://polygon.io/pricing"
    echo "2. Sign up for free"
    echo "3. Get your API key from the dashboard"
    exit 1
fi

API_KEY="$1"

echo "🔑 Setting up API key: ${API_KEY:0:8}..."

# Test the API key
echo "🧪 Testing API key..."
response=$(curl -s "https://api.polygon.io/v2/last/trade/AAPL?apikey=$API_KEY")

if echo "$response" | grep -q '"status":"OK"'; then
    echo "✅ API key is valid!"
    
    # Test options endpoint
    echo "🎯 Testing options access..."
    options_response=$(curl -s "https://api.polygon.io/v3/reference/options/contracts?underlying_ticker=AAPL&limit=5&apikey=$API_KEY")
    
    if echo "$options_response" | grep -q '"status":"OK"'; then
        echo "✅ Options endpoint accessible!"
        echo "🎉 Your API key has full access!"
    else
        echo "⚠️  Options endpoint not accessible (may need paid plan)"
        echo "💡 Free tier works for basic quotes, paid tier needed for options"
    fi
    
    # Set environment variable
    echo "🔧 Setting environment variable..."
    export POLYGON_API_KEY="$API_KEY"
    echo "export POLYGON_API_KEY='$API_KEY'" >> ~/.bashrc
    echo "export POLYGON_API_KEY='$API_KEY'" >> ~/.zshrc
    
    echo ""
    echo "✅ Setup complete!"
    echo "🔄 Restart your terminal or run: source ~/.bashrc"
    echo "🧪 Test with: python test_polygon_api.py"
    
else
    echo "❌ API key is invalid"
    echo "Response: $response"
    exit 1
fi
