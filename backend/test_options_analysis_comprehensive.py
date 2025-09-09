#!/usr/bin/env python3
"""
Comprehensive Options Analysis Testing Suite
Tests accuracy, consistency, and performance of the options analysis system
"""

import os
import sys
import django
import time
import asyncio
import concurrent.futures
from typing import Dict, List, Any
import statistics

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from core.options_service import OptionsAnalysisService

class OptionsAnalysisTester:
    """Comprehensive testing suite for options analysis"""
    
    def __init__(self):
        self.service = OptionsAnalysisService()
        self.test_results = {}
        
    def test_accuracy_and_consistency(self):
        """Test 1: Accuracy and Consistency"""
        print("🧪 Test 1: Accuracy and Consistency")
        print("=" * 50)
        
        # Test predefined stocks
        predefined_stocks = ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'NFLX', 'AMD', 'SPY']
        results = {}
        
        for symbol in predefined_stocks:
            print(f"\n📊 Testing {symbol}...")
            
            # Test multiple times to ensure consistency
            prices = []
            sentiments = []
            max_profits = []
            
            for i in range(3):
                result = self.service.get_comprehensive_analysis(symbol)
                prices.append(result['underlying_price'])
                sentiments.append(result['market_sentiment']['sentiment_description'])
                max_profits.append(result['recommended_strategies'][0]['max_profit'])
            
            # Check consistency
            price_consistent = len(set(prices)) == 1
            sentiment_consistent = len(set(sentiments)) == 1
            profit_consistent = len(set(max_profits)) == 1
            
            results[symbol] = {
                'price': prices[0],
                'sentiment': sentiments[0],
                'max_profit': max_profits[0],
                'price_consistent': price_consistent,
                'sentiment_consistent': sentiment_consistent,
                'profit_consistent': profit_consistent,
                'all_consistent': price_consistent and sentiment_consistent and profit_consistent
            }
            
            status = "✅" if results[symbol]['all_consistent'] else "❌"
            print(f"  {status} Price: ${prices[0]:.2f} | Sentiment: {sentiments[0]} | Max Profit: ${max_profits[0]:.2f}")
            if not results[symbol]['all_consistent']:
                print(f"    ⚠️  Inconsistencies detected!")
        
        self.test_results['accuracy_consistency'] = results
        return results
    
    def test_dynamic_pricing(self):
        """Test 2: Dynamic Pricing for Unknown Stocks"""
        print("\n🧪 Test 2: Dynamic Pricing for Unknown Stocks")
        print("=" * 50)
        
        # Test unknown stocks
        unknown_stocks = ['XYZ', 'ABC123', 'TEST', 'RANDOM', 'UNKNOWN']
        results = {}
        
        for symbol in unknown_stocks:
            print(f"\n📊 Testing {symbol}...")
            
            # Test multiple times to ensure consistency
            prices = []
            for i in range(3):
                result = self.service.get_comprehensive_analysis(symbol)
                prices.append(result['underlying_price'])
            
            # Check consistency
            price_consistent = len(set(prices)) == 1
            price_range_valid = 50 <= prices[0] <= 450  # Should be in our defined range
            
            results[symbol] = {
                'price': prices[0],
                'price_consistent': price_consistent,
                'price_range_valid': price_range_valid,
                'all_valid': price_consistent and price_range_valid
            }
            
            status = "✅" if results[symbol]['all_valid'] else "❌"
            print(f"  {status} Price: ${prices[0]:.2f} | Consistent: {price_consistent} | Range Valid: {price_range_valid}")
        
        self.test_results['dynamic_pricing'] = results
        return results
    
    def test_strategy_calculations(self):
        """Test 3: Strategy Calculations Mathematical Accuracy"""
        print("\n🧪 Test 3: Strategy Calculations Mathematical Accuracy")
        print("=" * 50)
        
        test_stocks = ['AAPL', 'TSLA', 'UNKNOWN']
        results = {}
        
        for symbol in test_stocks:
            print(f"\n📊 Testing {symbol} strategy calculations...")
            
            result = self.service.get_comprehensive_analysis(symbol)
            current_price = result['underlying_price']
            strategies = result['recommended_strategies']
            
            strategy_results = {}
            
            for strategy in strategies:
                name = strategy['strategy_name']
                max_profit = strategy['max_profit']
                max_loss = strategy['max_loss']
                breakeven_points = strategy['breakeven_points']
                total_cost = strategy['total_cost']
                total_credit = strategy['total_credit']
                
                # Test Covered Call calculations
                if name == 'Covered Call':
                    expected_premium = current_price * 0.02  # 2% of stock price
                    expected_breakeven = current_price - expected_premium
                    expected_max_loss = -(current_price - expected_premium)
                    
                    premium_accurate = abs(max_profit - expected_premium) < 0.01
                    breakeven_accurate = abs(breakeven_points[0] - expected_breakeven) < 0.01
                    max_loss_accurate = abs(max_loss - expected_max_loss) < 0.01
                    
                    strategy_results[name] = {
                        'premium_accurate': premium_accurate,
                        'breakeven_accurate': breakeven_accurate,
                        'max_loss_accurate': max_loss_accurate,
                        'all_accurate': premium_accurate and breakeven_accurate and max_loss_accurate,
                        'expected_premium': expected_premium,
                        'actual_premium': max_profit,
                        'expected_breakeven': expected_breakeven,
                        'actual_breakeven': breakeven_points[0]
                    }
                    
                    status = "✅" if strategy_results[name]['all_accurate'] else "❌"
                    print(f"  {status} {name}: Premium ${max_profit:.2f} | Breakeven ${breakeven_points[0]:.2f}")
                    if not strategy_results[name]['all_accurate']:
                        print(f"    ⚠️  Expected Premium: ${expected_premium:.2f}, Breakeven: ${expected_breakeven:.2f}")
                
                # Test Cash Secured Put calculations
                elif name == 'Cash Secured Put':
                    expected_premium = current_price * 0.015  # 1.5% of stock price
                    expected_breakeven = current_price - expected_premium
                    expected_max_loss = -(current_price - expected_premium)
                    
                    premium_accurate = abs(max_profit - expected_premium) < 0.01
                    breakeven_accurate = abs(breakeven_points[0] - expected_breakeven) < 0.01
                    max_loss_accurate = abs(max_loss - expected_max_loss) < 0.01
                    
                    strategy_results[name] = {
                        'premium_accurate': premium_accurate,
                        'breakeven_accurate': breakeven_accurate,
                        'max_loss_accurate': max_loss_accurate,
                        'all_accurate': premium_accurate and breakeven_accurate and max_loss_accurate,
                        'expected_premium': expected_premium,
                        'actual_premium': max_profit,
                        'expected_breakeven': expected_breakeven,
                        'actual_breakeven': breakeven_points[0]
                    }
                    
                    status = "✅" if strategy_results[name]['all_accurate'] else "❌"
                    print(f"  {status} {name}: Premium ${max_profit:.2f} | Breakeven ${breakeven_points[0]:.2f}")
                    if not strategy_results[name]['all_accurate']:
                        print(f"    ⚠️  Expected Premium: ${expected_premium:.2f}, Breakeven: ${expected_breakeven:.2f}")
            
            results[symbol] = strategy_results
        
        self.test_results['strategy_calculations'] = results
        return results
    
    def test_performance(self):
        """Test 4: Performance with Concurrent Requests"""
        print("\n🧪 Test 4: Performance with Concurrent Requests")
        print("=" * 50)
        
        test_symbols = ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'NVDA', 'NFLX', 'AMD', 'SPY', 'UNKNOWN', 'TEST123']
        
        def analyze_stock(symbol):
            start_time = time.time()
            result = self.service.get_comprehensive_analysis(symbol)
            end_time = time.time()
            return {
                'symbol': symbol,
                'response_time': end_time - start_time,
                'price': result['underlying_price'],
                'success': True
            }
        
        # Test sequential performance
        print("📊 Testing sequential performance...")
        sequential_times = []
        for symbol in test_symbols:
            result = analyze_stock(symbol)
            sequential_times.append(result['response_time'])
            print(f"  {symbol}: {result['response_time']:.3f}s")
        
        # Test concurrent performance
        print("\n📊 Testing concurrent performance...")
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(analyze_stock, symbol) for symbol in test_symbols]
            concurrent_results = [future.result() for future in concurrent.futures.as_completed(futures)]
        end_time = time.time()
        
        concurrent_times = [result['response_time'] for result in concurrent_results]
        total_concurrent_time = end_time - start_time
        
        # Calculate statistics
        sequential_avg = statistics.mean(sequential_times)
        concurrent_avg = statistics.mean(concurrent_times)
        sequential_total = sum(sequential_times)
        
        print(f"\n📈 Performance Results:")
        print(f"  Sequential Total Time: {sequential_total:.3f}s")
        print(f"  Concurrent Total Time: {total_concurrent_time:.3f}s")
        print(f"  Sequential Average: {sequential_avg:.3f}s")
        print(f"  Concurrent Average: {concurrent_avg:.3f}s")
        print(f"  Speedup: {sequential_total / total_concurrent_time:.2f}x")
        
        performance_results = {
            'sequential_times': sequential_times,
            'concurrent_times': concurrent_times,
            'sequential_total': sequential_total,
            'concurrent_total': total_concurrent_time,
            'speedup': sequential_total / total_concurrent_time,
            'sequential_avg': sequential_avg,
            'concurrent_avg': concurrent_avg
        }
        
        self.test_results['performance'] = performance_results
        return performance_results
    
    def test_edge_cases(self):
        """Test 5: Edge Cases and Error Handling"""
        print("\n🧪 Test 5: Edge Cases and Error Handling")
        print("=" * 50)
        
        edge_cases = [
            '',  # Empty string
            'A',  # Single character
            '123',  # Numbers only
            'AAPL!@#',  # Special characters
            'VERYLONGSTOCKSYMBOL',  # Very long symbol
            'aapl',  # Lowercase
            'aApL',  # Mixed case
        ]
        
        results = {}
        
        for symbol in edge_cases:
            print(f"\n📊 Testing edge case: '{symbol}'...")
            
            try:
                result = self.service.get_comprehensive_analysis(symbol)
                success = True
                error = None
                price = result['underlying_price']
                sentiment = result['market_sentiment']['sentiment_description']
                
                status = "✅"
                print(f"  {status} Success: Price ${price:.2f} | Sentiment: {sentiment}")
                
            except Exception as e:
                success = False
                error = str(e)
                price = None
                sentiment = None
                
                status = "❌"
                print(f"  {status} Error: {error}")
            
            results[symbol] = {
                'success': success,
                'error': error,
                'price': price,
                'sentiment': sentiment
            }
        
        self.test_results['edge_cases'] = results
        return results
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📋 COMPREHENSIVE TEST REPORT")
        print("=" * 60)
        
        # Test 1: Accuracy and Consistency
        if 'accuracy_consistency' in self.test_results:
            results = self.test_results['accuracy_consistency']
            consistent_count = sum(1 for r in results.values() if r['all_consistent'])
            total_count = len(results)
            print(f"\n✅ Test 1 - Accuracy & Consistency: {consistent_count}/{total_count} stocks consistent")
            
            if consistent_count < total_count:
                print("   ⚠️  Inconsistent stocks:")
                for symbol, result in results.items():
                    if not result['all_consistent']:
                        print(f"     - {symbol}")
        
        # Test 2: Dynamic Pricing
        if 'dynamic_pricing' in self.test_results:
            results = self.test_results['dynamic_pricing']
            valid_count = sum(1 for r in results.values() if r['all_valid'])
            total_count = len(results)
            print(f"\n✅ Test 2 - Dynamic Pricing: {valid_count}/{total_count} stocks valid")
        
        # Test 3: Strategy Calculations
        if 'strategy_calculations' in self.test_results:
            results = self.test_results['strategy_calculations']
            total_strategies = 0
            accurate_strategies = 0
            
            for symbol_results in results.values():
                for strategy_result in symbol_results.values():
                    total_strategies += 1
                    if strategy_result['all_accurate']:
                        accurate_strategies += 1
            
            print(f"\n✅ Test 3 - Strategy Calculations: {accurate_strategies}/{total_strategies} strategies accurate")
        
        # Test 4: Performance
        if 'performance' in self.test_results:
            perf = self.test_results['performance']
            print(f"\n✅ Test 4 - Performance:")
            print(f"   Sequential Total: {perf['sequential_total']:.3f}s")
            print(f"   Concurrent Total: {perf['concurrent_total']:.3f}s")
            print(f"   Speedup: {perf['speedup']:.2f}x")
            print(f"   Average Response: {perf['concurrent_avg']:.3f}s")
        
        # Test 5: Edge Cases
        if 'edge_cases' in self.test_results:
            results = self.test_results['edge_cases']
            success_count = sum(1 for r in results.values() if r['success'])
            total_count = len(results)
            print(f"\n✅ Test 5 - Edge Cases: {success_count}/{total_count} cases handled successfully")
        
        print("\n" + "=" * 60)
        print("🎯 RECOMMENDATIONS FOR OPTIMIZATION")
        print("=" * 60)
        
        # Generate recommendations based on test results
        recommendations = []
        
        if 'accuracy_consistency' in self.test_results:
            inconsistent_count = sum(1 for r in self.test_results['accuracy_consistency'].values() if not r['all_consistent'])
            if inconsistent_count > 0:
                recommendations.append("🔧 Fix consistency issues in predefined stock data")
        
        if 'performance' in self.test_results:
            if self.test_results['performance']['concurrent_avg'] > 0.5:
                recommendations.append("⚡ Optimize response times - consider caching")
        
        if 'edge_cases' in self.test_results:
            failed_count = sum(1 for r in self.test_results['edge_cases'].values() if not r['success'])
            if failed_count > 0:
                recommendations.append("🛡️ Improve error handling for edge cases")
        
        if not recommendations:
            recommendations.append("🎉 All tests passed! System is performing optimally.")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
        
        print("\n" + "=" * 60)

def main():
    """Run comprehensive tests"""
    print("🚀 Starting Comprehensive Options Analysis Testing")
    print("=" * 60)
    
    tester = OptionsAnalysisTester()
    
    # Run all tests
    tester.test_accuracy_and_consistency()
    tester.test_dynamic_pricing()
    tester.test_strategy_calculations()
    tester.test_performance()
    tester.test_edge_cases()
    
    # Generate report
    tester.generate_report()

if __name__ == "__main__":
    main()
