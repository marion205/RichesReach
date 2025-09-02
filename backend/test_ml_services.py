#!/usr/bin/env python3
"""
Test script for ML services
Run this to verify the ML-enhanced AI system is working
"""

import os
import sys
import django
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

def test_ml_services():
    """Test the ML services"""
    print("🧪 Testing ML Services...")
    print("=" * 50)
    
    try:
        # Test ML Service
        print("\n1. Testing ML Service...")
        from core.ml_service import MLService
        
        ml_service = MLService()
        print(f"✅ ML Service initialized: {ml_service.is_available()}")
        
        if ml_service.is_available():
            # Test market regime prediction
            print("\n2. Testing Market Regime Prediction...")
            market_data = {
                'sp500_return': 0.05,
                'volatility': 0.15,
                'interest_rate': 0.05,
                'sector_performance': {
                    'technology': 'outperforming',
                    'healthcare': 'neutral',
                    'financials': 'underperforming'
                }
            }
            
            regime_prediction = ml_service.predict_market_regime(market_data)
            print(f"✅ Market Regime: {regime_prediction['regime']}")
            print(f"   Confidence: {regime_prediction['confidence']:.2f}")
            print(f"   Method: {regime_prediction['method']}")
            
            # Test portfolio optimization
            print("\n3. Testing Portfolio Optimization...")
            user_profile = {
                'age': 30,
                'income_bracket': '$50,000 - $75,000',
                'risk_tolerance': 'Moderate',
                'investment_horizon': '5-10 years'
            }
            
            market_conditions = {
                'sp500_return': 0.03,
                'volatility': 0.12,
                'interest_rate': 0.04
            }
            
            available_stocks = [
                {'beginner_friendly_score': 8.0},
                {'beginner_friendly_score': 7.5},
                {'beginner_friendly_score': 6.8}
            ]
            
            portfolio_opt = ml_service.optimize_portfolio_allocation(
                user_profile, market_conditions, available_stocks
            )
            print(f"✅ Portfolio Optimization: {portfolio_opt['method']}")
            print(f"   Expected Return: {portfolio_opt['expected_return']}")
            print(f"   Risk Score: {portfolio_opt['risk_score']:.2f}")
            
            # Test stock scoring
            print("\n4. Testing Stock Scoring...")
            stocks = [
                {'beginner_friendly_score': 8.5, 'symbol': 'AAPL'},
                {'beginner_friendly_score': 7.2, 'symbol': 'MSFT'},
                {'beginner_friendly_score': 6.8, 'symbol': 'GOOGL'}
            ]
            
            scored_stocks = ml_service.score_stocks_ml(stocks, market_conditions, user_profile)
            print(f"✅ Stock Scoring: {len(scored_stocks)} stocks scored")
            for stock in scored_stocks[:3]:
                print(f"   {stock.get('symbol', 'Unknown')}: ML Score {stock['ml_score']:.2f}")
        
    except Exception as e:
        print(f"❌ Error testing ML Service: {e}")
    
    try:
        # Test Market Data Service
        print("\n5. Testing Market Data Service...")
        from core.market_data_service import MarketDataService
        
        market_service = MarketDataService()
        
        # Test market overview
        market_overview = market_service.get_market_overview()
        print(f"✅ Market Overview: {market_overview['method']}")
        print(f"   S&P 500 Return: {market_overview['sp500_return']:.2%}")
        print(f"   Volatility: {market_overview['volatility']:.2%}")
        
        # Test sector performance
        sector_performance = market_service.get_sector_performance()
        print(f"✅ Sector Performance: {len(sector_performance)} sectors analyzed")
        
        # Test economic indicators
        economic_indicators = market_service.get_economic_indicators()
        print(f"✅ Economic Indicators: {economic_indicators['method']}")
        print(f"   Interest Rate: {economic_indicators['interest_rate']:.2%}")
        print(f"   GDP Growth: {economic_indicators['gdp_growth']:.2%}")
        
        # Test regime indicators
        regime_indicators = market_service.get_market_regime_indicators()
        print(f"✅ Regime Indicators: {regime_indicators['market_regime']}")
        print(f"   Volatility Regime: {regime_indicators['volatility_regime']}")
        print(f"   Economic Cycle: {regime_indicators['economic_cycle']}")
        
    except Exception as e:
        print(f"❌ Error testing Market Data Service: {e}")
    
    try:
        # Test AI Service Integration
        print("\n6. Testing AI Service Integration...")
        from core.ai_service import AIService
        
        ai_service = AIService()
        
        # Test service status
        status = ai_service.get_service_status()
        print(f"✅ AI Service Status:")
        print(f"   OpenAI: {status['openai_available']}")
        print(f"   ML: {status['ml_available']}")
        print(f"   Market Data: {status['market_data_available']}")
        
        if status['ml_available']:
            # Test ML market analysis
            print("\n7. Testing ML Market Analysis...")
            market_analysis = ai_service.get_enhanced_market_analysis()
            print(f"✅ Enhanced Market Analysis: {market_analysis['ai_service']}")
            
            # Test ML portfolio optimization
            print("\n8. Testing ML Portfolio Optimization...")
            user_profile = {
                'age': 35,
                'income_bracket': '$75,000 - $100,000',
                'risk_tolerance': 'Aggressive',
                'investment_horizon': '10+ years'
            }
            
            portfolio_opt = ai_service.optimize_portfolio_ml(user_profile)
            print(f"✅ ML Portfolio Optimization: {portfolio_opt['method']}")
            print(f"   Expected Return: {portfolio_opt['expected_return']}")
            print(f"   Risk Score: {portfolio_opt['risk_score']:.2f}")
        
    except Exception as e:
        print(f"❌ Error testing AI Service Integration: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 ML Services Test Complete!")
    print("\nNext steps:")
    print("1. Install ML dependencies: pip install -r requirements.txt")
    print("2. Set up API keys for real market data")
    print("3. Test with real user data")
    print("4. Customize ML algorithms based on your preferences")

if __name__ == "__main__":
    test_ml_services()
