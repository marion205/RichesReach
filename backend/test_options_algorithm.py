#!/usr/bin/env python3
"""
Options Algorithm Industry Standards Test
Tests our options calculations against industry benchmarks and real market data
"""

import os
import sys
import django
import asyncio
import aiohttp
import json
from decimal import Decimal
import math

# Setup Django
sys.path.append('/Users/marioncollins/RichesReach/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from core.options_service import OptionsAnalysisService
from core.real_options_service import RealOptionsService
from core.market_data_api_service import MarketDataAPIService

class OptionsAlgorithmTester:
    def __init__(self):
        self.options_service = OptionsAnalysisService()
        self.real_options_service = RealOptionsService()
        self.market_data_service = MarketDataAPIService()
        
    async def test_black_scholes_accuracy(self):
        """Test Black-Scholes calculations against known values"""
        print("🧮 Testing Black-Scholes Calculations...")
        
        # Test case 1: Standard parameters
        S = 100  # Stock price
        K = 100  # Strike price
        T = 0.25  # Time to expiration (3 months)
        r = 0.05  # Risk-free rate
        sigma = 0.2  # Volatility
        
        # Expected values (calculated with industry standard formulas)
        expected_call_price = 4.33  # Approximate
        expected_put_price = 2.13   # Approximate
        
        # Test our calculations
        try:
            # This would test our Black-Scholes implementation
            print(f"✅ Black-Scholes test case: S={S}, K={K}, T={T}, r={r}, σ={sigma}")
            print(f"   Expected Call: ~${expected_call_price:.2f}")
            print(f"   Expected Put: ~${expected_put_price:.2f}")
            print("   Note: Implement Black-Scholes in options service for full validation")
        except Exception as e:
            print(f"❌ Black-Scholes test failed: {e}")
    
    async def test_greeks_calculations(self):
        """Test Greeks calculations for accuracy"""
        print("\n📊 Testing Greeks Calculations...")
        
        # Test case: AAPL options
        symbol = "AAPL"
        current_price = 155.0
        strike = 160.0
        days_to_exp = 30
        volatility = 0.25
        
        print(f"📈 Testing Greeks for {symbol}:")
        print(f"   Current Price: ${current_price}")
        print(f"   Strike Price: ${strike}")
        print(f"   Days to Expiration: {days_to_exp}")
        print(f"   Volatility: {volatility*100}%")
        
        # Expected ranges for Greeks (industry standards)
        expected_delta_range = (0.1, 0.9)  # Call delta range
        expected_gamma_range = (0.01, 0.05)  # Gamma range
        expected_theta_range = (-0.2, -0.05)  # Theta range (negative)
        expected_vega_range = (0.1, 0.5)  # Vega range
        
        print(f"   Expected Delta Range: {expected_delta_range}")
        print(f"   Expected Gamma Range: {expected_gamma_range}")
        print(f"   Expected Theta Range: {expected_theta_range}")
        print(f"   Expected Vega Range: {expected_vega_range}")
        
        # Test our Greeks calculations
        try:
            # Get options data from our service
            options_data = self.options_service.get_comprehensive_analysis(symbol)
            
            if options_data and 'options_chain' in options_data:
                options_chain = options_data['options_chain']
                
                # Test call options Greeks
                if 'calls' in options_chain and options_chain['calls']:
                    call_option = options_chain['calls'][0]  # First call option
                    
                    delta = call_option.get('delta', 0)
                    gamma = call_option.get('gamma', 0)
                    theta = call_option.get('theta', 0)
                    vega = call_option.get('vega', 0)
                    
                    print(f"\n   📞 Call Option Greeks:")
                    print(f"      Delta: {delta:.4f} {'✅' if expected_delta_range[0] <= delta <= expected_delta_range[1] else '❌'}")
                    print(f"      Gamma: {gamma:.4f} {'✅' if expected_gamma_range[0] <= gamma <= expected_gamma_range[1] else '❌'}")
                    print(f"      Theta: {theta:.4f} {'✅' if expected_theta_range[0] <= theta <= expected_theta_range[1] else '❌'}")
                    print(f"      Vega: {vega:.4f} {'✅' if expected_vega_range[0] <= vega <= expected_vega_range[1] else '❌'}")
                
                # Test put options Greeks
                if 'puts' in options_chain and options_chain['puts']:
                    put_option = options_chain['puts'][0]  # First put option
                    
                    delta = put_option.get('delta', 0)
                    gamma = put_option.get('gamma', 0)
                    theta = put_option.get('theta', 0)
                    vega = put_option.get('vega', 0)
                    
                    print(f"\n   📉 Put Option Greeks:")
                    print(f"      Delta: {delta:.4f} {'✅' if -expected_delta_range[1] <= delta <= -expected_delta_range[0] else '❌'}")
                    print(f"      Gamma: {gamma:.4f} {'✅' if expected_gamma_range[0] <= gamma <= expected_gamma_range[1] else '❌'}")
                    print(f"      Theta: {theta:.4f} {'✅' if expected_theta_range[0] <= theta <= expected_theta_range[1] else '❌'}")
                    print(f"      Vega: {vega:.4f} {'✅' if expected_vega_range[0] <= vega <= expected_vega_range[1] else '❌'}")
            
        except Exception as e:
            print(f"❌ Greeks test failed: {e}")
    
    async def test_strategy_pricing(self):
        """Test options strategy pricing accuracy"""
        print("\n💰 Testing Strategy Pricing...")
        
        symbol = "AAPL"
        
        try:
            # Get comprehensive analysis which includes strategies
            analysis = self.options_service.get_comprehensive_analysis(symbol)
            
            if analysis and 'recommended_strategies' in analysis:
                strategies = analysis['recommended_strategies']
                current_price = analysis.get('underlying_price', 155.0)
                
                print(f"📊 Testing {len(strategies)} strategies for {symbol}:")
                
                for i, strategy in enumerate(strategies, 1):
                    name = strategy.get('strategy_name', 'Unknown')
                    max_profit = strategy.get('max_profit', 0)
                    max_loss = strategy.get('max_loss', 0)
                    risk_reward = strategy.get('risk_reward_ratio', 0)
                    win_rate = strategy.get('probability_of_profit', 0)
                    
                    print(f"\n   {i}. {name}:")
                    print(f"      Max Profit: ${max_profit:.2f}")
                    print(f"      Max Loss: ${max_loss:.2f}")
                    print(f"      Risk/Reward: {risk_reward:.2f}")
                    print(f"      Win Rate: {win_rate*100:.0f}%")
                    
                    # Validate strategy metrics
                    issues = []
                    
                    # Check for unrealistic values
                    if max_profit > current_price * 2:
                        issues.append("Max profit too high")
                    if max_loss > current_price:
                        issues.append("Max loss too high")
                    if risk_reward > 10:
                        issues.append("Risk/reward ratio too high")
                    if win_rate > 0.9:
                        issues.append("Win rate too optimistic")
                    
                    if issues:
                        print(f"      ⚠️  Issues: {', '.join(issues)}")
                    else:
                        print(f"      ✅ Metrics look reasonable")
            else:
                print(f"❌ No strategies found in analysis")
        
        except Exception as e:
            print(f"❌ Strategy pricing test failed: {e}")
    
    async def test_implied_volatility(self):
        """Test implied volatility calculations"""
        print("\n📈 Testing Implied Volatility...")
        
        symbol = "AAPL"
        
        try:
            # Get comprehensive analysis
            analysis = self.options_service.get_comprehensive_analysis(symbol)
            
            if analysis and 'market_sentiment' in analysis:
                sentiment = analysis['market_sentiment']
                iv_rank = sentiment.get('implied_volatility_rank', 0)
                put_call_ratio = sentiment.get('put_call_ratio', 0)
                sentiment_score = sentiment.get('sentiment_score', 0)
                
                print(f"📊 Market Sentiment for {symbol}:")
                print(f"   IV Rank: {iv_rank}% {'✅' if 0 <= iv_rank <= 100 else '❌'}")
                print(f"   Put/Call Ratio: {put_call_ratio:.2f} {'✅' if 0.3 <= put_call_ratio <= 2.0 else '❌'}")
                print(f"   Sentiment Score: {sentiment_score} {'✅' if 0 <= sentiment_score <= 100 else '❌'}")
                
                # Validate IV rank interpretation
                if iv_rank < 20:
                    print("   📉 Low IV - Good for selling options")
                elif iv_rank > 80:
                    print("   📈 High IV - Good for buying options")
                else:
                    print("   📊 Moderate IV - Neutral strategy")
        
        except Exception as e:
            print(f"❌ Implied volatility test failed: {e}")
    
    async def test_real_market_data(self):
        """Test against real market data"""
        print("\n🌐 Testing Real Market Data Integration...")
        
        symbols = ["AAPL", "MSFT", "GOOGL", "TSLA"]
        
        for symbol in symbols:
            try:
                print(f"\n📊 Testing {symbol}:")
                
                # Get real stock quote
                quote = await self.market_data_service.get_stock_quote(symbol)
                
                if quote:
                    price = quote.get('price', 0)
                    change = quote.get('change', 0)
                    change_percent = quote.get('change_percent', 0)
                    
                    print(f"   Current Price: ${price:.2f}")
                    print(f"   Change: ${change:.2f} ({change_percent:.2f}%)")
                    
                    # Validate price is reasonable
                    if 1 <= price <= 10000:
                        print("   ✅ Price within reasonable range")
                    else:
                        print("   ❌ Price outside reasonable range")
                    
                    # Get options analysis
                    analysis = self.options_service.get_comprehensive_analysis(symbol)
                    
                    if analysis:
                        print("   ✅ Options data retrieved successfully")
                        
                        # Check if we have realistic options chain
                        if 'options_chain' in analysis:
                            chain = analysis['options_chain']
                            calls = chain.get('calls', [])
                            puts = chain.get('puts', [])
                            
                            print(f"   📞 Call options: {len(calls)}")
                            print(f"   📉 Put options: {len(puts)}")
                            
                            if len(calls) > 0 and len(puts) > 0:
                                print("   ✅ Options chain populated")
                            else:
                                print("   ⚠️  Options chain may be empty")
                    else:
                        print("   ❌ No options data available")
                else:
                    print(f"   ❌ No market data for {symbol}")
            
            except Exception as e:
                print(f"   ❌ Error testing {symbol}: {e}")
    
    async def run_comprehensive_test(self):
        """Run all tests"""
        print("🚀 Starting Options Algorithm Industry Standards Test")
        print("=" * 60)
        
        await self.test_black_scholes_accuracy()
        await self.test_greeks_calculations()
        await self.test_strategy_pricing()
        await self.test_implied_volatility()
        await self.test_real_market_data()
        
        print("\n" + "=" * 60)
        print("✅ Options Algorithm Test Complete!")
        print("\n📋 Summary:")
        print("   • Black-Scholes: Needs implementation for full validation")
        print("   • Greeks: Check individual calculations above")
        print("   • Strategy Pricing: Validate metrics are realistic")
        print("   • Implied Volatility: Check IV rank and sentiment")
        print("   • Real Market Data: Verify data accuracy and completeness")

async def main():
    tester = OptionsAlgorithmTester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())
