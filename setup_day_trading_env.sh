#!/bin/bash
# Environment setup script for Day Trading features
# Sets all required API keys as environment variables

export POLYGON_API_KEY="uuKmy9dPAjaSVXVEtCumQPga1dqEPDS2"
export ALPACA_API_KEY="CKVL76T6J6F5BNDADQ322V2BJK"
export ALPACA_SECRET_KEY="6CGQRytfGBWauNSFdVA75jvisv1ctPuMHXU1mwovDXQz"

# Optional: Other API keys (if needed)
export ALPHA_VANTAGE_API_KEY="OHYSFF1AE446O7CR"
export FINNHUB_API_KEY="d2rnitpr01qv11lfegugd2rnitpr01qv11lfegv0"
export NEWS_API_KEY="94a335c7316145f79840edd62f77e11e"

echo "✅ Environment variables set for Day Trading"
echo "   - Polygon.io: Configured"
echo "   - Alpaca: Configured"
echo ""
echo "To use these in your current shell, run:"
echo "  source setup_day_trading_env.sh"
echo ""
echo "Or add to your .env file for Django"

