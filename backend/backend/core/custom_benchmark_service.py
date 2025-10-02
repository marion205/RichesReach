import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from django.contrib.auth.models import User
from .models_custom_benchmark import CustomBenchmark, CustomBenchmarkHolding
from .real_market_data_service import real_market_data_service

logger = logging.getLogger(__name__)

class CustomBenchmarkService:
    """Service for managing custom benchmark portfolios"""
    
    def __init__(self):
        self.real_market_service = real_market_data_service
    
    def create_custom_benchmark(self, user: User, name: str, description: str, holdings: List[Dict[str, Any]]) -> Optional[CustomBenchmark]:
        """Create a new custom benchmark portfolio"""
        try:
            # Validate holdings
            if not self._validate_holdings(holdings):
                logger.error("Invalid holdings for custom benchmark")
                return None
            
            # Create custom benchmark
            custom_benchmark = CustomBenchmark.objects.create(
                user=user,
                name=name,
                description=description,
                is_active=True
            )
            
            # Create holdings
            for holding in holdings:
                CustomBenchmarkHolding.objects.create(
                    benchmark=custom_benchmark,
                    symbol=holding['symbol'],
                    weight=holding['weight'],
                    name=holding.get('name', ''),
                    sector=holding.get('sector', ''),
                    description=holding.get('description', '')
                )
            
            logger.info(f"Created custom benchmark '{name}' for user {user.id}")
            return custom_benchmark
            
        except Exception as e:
            logger.error(f"Error creating custom benchmark: {e}")
            return None
    
    def update_custom_benchmark(self, benchmark_id: int, user: User, name: str = None, description: str = None, holdings: List[Dict[str, Any]] = None) -> Optional[CustomBenchmark]:
        """Update an existing custom benchmark"""
        try:
            benchmark = CustomBenchmark.objects.get(id=benchmark_id, user=user)
            
            if name is not None:
                benchmark.name = name
            if description is not None:
                benchmark.description = description
            
            if holdings is not None:
                # Validate holdings
                if not self._validate_holdings(holdings):
                    logger.error("Invalid holdings for custom benchmark update")
                    return None
                
                # Clear existing holdings
                CustomBenchmarkHolding.objects.filter(benchmark=benchmark).delete()
                
                # Create new holdings
                for holding in holdings:
                    CustomBenchmarkHolding.objects.create(
                        benchmark=benchmark,
                        symbol=holding['symbol'],
                        weight=holding['weight'],
                        name=holding.get('name', ''),
                        sector=holding.get('sector', ''),
                        description=holding.get('description', '')
                    )
            
            benchmark.save()
            logger.info(f"Updated custom benchmark {benchmark_id}")
            return benchmark
            
        except CustomBenchmark.DoesNotExist:
            logger.error(f"Custom benchmark {benchmark_id} not found for user {user.id}")
            return None
        except Exception as e:
            logger.error(f"Error updating custom benchmark: {e}")
            return None
    
    def delete_custom_benchmark(self, benchmark_id: int, user: User) -> bool:
        """Delete a custom benchmark"""
        try:
            benchmark = CustomBenchmark.objects.get(id=benchmark_id, user=user)
            benchmark.delete()
            logger.info(f"Deleted custom benchmark {benchmark_id}")
            return True
            
        except CustomBenchmark.DoesNotExist:
            logger.error(f"Custom benchmark {benchmark_id} not found for user {user.id}")
            return False
        except Exception as e:
            logger.error(f"Error deleting custom benchmark: {e}")
            return False
    
    def get_user_custom_benchmarks(self, user: User) -> List[CustomBenchmark]:
        """Get all custom benchmarks for a user"""
        try:
            return CustomBenchmark.objects.filter(user=user, is_active=True).order_by('-created_at')
        except Exception as e:
            logger.error(f"Error fetching custom benchmarks for user {user.id}: {e}")
            return []
    
    def get_custom_benchmark_data(self, benchmark_id: int, user: User, timeframe: str) -> Optional[Dict[str, Any]]:
        """Get performance data for a custom benchmark"""
        try:
            benchmark = CustomBenchmark.objects.get(id=benchmark_id, user=user)
            holdings = CustomBenchmarkHolding.objects.filter(benchmark=benchmark)
            
            if not holdings.exists():
                logger.error(f"No holdings found for custom benchmark {benchmark_id}")
                return None
            
            # Get data for all holdings
            symbols = [holding.symbol for holding in holdings]
            holdings_data = self.real_market_service.get_multiple_benchmarks(symbols, timeframe)
            
            if not holdings_data:
                logger.error(f"No market data found for custom benchmark {benchmark_id}")
                return None
            
            # Calculate weighted portfolio performance
            portfolio_data = self._calculate_weighted_portfolio(holdings, holdings_data, timeframe)
            
            return {
                'id': benchmark.id,
                'name': benchmark.name,
                'description': benchmark.description,
                'symbol': f"CUSTOM_{benchmark.id}",
                'timeframe': timeframe,
                'dataPoints': portfolio_data['dataPoints'],
                'startValue': portfolio_data['startValue'],
                'endValue': portfolio_data['endValue'],
                'totalReturn': portfolio_data['totalReturn'],
                'totalReturnPercent': portfolio_data['totalReturnPercent'],
                'volatility': portfolio_data['volatility'],
                'sharpeRatio': portfolio_data['sharpeRatio'],
                'maxDrawdown': portfolio_data['maxDrawdown'],
                'holdings': [
                    {
                        'symbol': holding.symbol,
                        'weight': holding.weight,
                        'name': holding.name,
                        'sector': holding.sector,
                        'description': holding.description
                    }
                    for holding in holdings
                ],
                'source': 'custom_benchmark'
            }
            
        except CustomBenchmark.DoesNotExist:
            logger.error(f"Custom benchmark {benchmark_id} not found for user {user.id}")
            return None
        except Exception as e:
            logger.error(f"Error getting custom benchmark data: {e}")
            return None
    
    def _validate_holdings(self, holdings: List[Dict[str, Any]]) -> bool:
        """Validate holdings data"""
        if not holdings:
            return False
        
        total_weight = sum(holding.get('weight', 0) for holding in holdings)
        if abs(total_weight - 1.0) > 0.01:  # Allow small rounding errors
            logger.error(f"Holdings weights must sum to 1.0, got {total_weight}")
            return False
        
        for holding in holdings:
            if not holding.get('symbol'):
                logger.error("All holdings must have a symbol")
                return False
            
            weight = holding.get('weight', 0)
            if weight <= 0 or weight > 1:
                logger.error(f"Invalid weight {weight} for symbol {holding['symbol']}")
                return False
        
        return True
    
    def _calculate_weighted_portfolio(self, holdings: List[CustomBenchmarkHolding], holdings_data: Dict[str, Dict[str, Any]], timeframe: str) -> Dict[str, Any]:
        """Calculate weighted portfolio performance"""
        try:
            # Get the minimum length of all data series
            min_length = float('inf')
            aligned_data = {}
            
            for holding in holdings:
                symbol = holding.symbol
                if symbol not in holdings_data:
                    logger.warning(f"No data found for {symbol}")
                    continue
                
                data_points = holdings_data[symbol]['dataPoints']
                min_length = min(min_length, len(data_points))
                aligned_data[symbol] = data_points
            
            if min_length == float('inf') or min_length == 0:
                logger.error("No valid data found for portfolio calculation")
                return self._get_default_portfolio_data()
            
            # Align all data to the same length
            for symbol in aligned_data:
                aligned_data[symbol] = aligned_data[symbol][-min_length:]
            
            # Calculate weighted portfolio values
            portfolio_values = []
            portfolio_data_points = []
            
            for i in range(min_length):
                weighted_value = 0
                timestamp = None
                
                for holding in holdings:
                    symbol = holding.symbol
                    if symbol in aligned_data:
                        data_point = aligned_data[symbol][i]
                        weighted_value += data_point['value'] * holding.weight
                        if timestamp is None:
                            timestamp = data_point['timestamp']
                
                portfolio_values.append(weighted_value)
                portfolio_data_points.append({
                    'timestamp': timestamp,
                    'value': weighted_value,
                    'open': weighted_value,  # Simplified
                    'high': weighted_value,
                    'low': weighted_value,
                    'volume': 0  # Not applicable for portfolio
                })
            
            # Calculate metrics
            returns = np.diff(portfolio_values) / portfolio_values[:-1]
            
            return {
                'dataPoints': portfolio_data_points,
                'startValue': portfolio_values[0],
                'endValue': portfolio_values[-1],
                'totalReturn': portfolio_values[-1] - portfolio_values[0],
                'totalReturnPercent': ((portfolio_values[-1] - portfolio_values[0]) / portfolio_values[0]) * 100,
                'volatility': np.std(returns) * np.sqrt(252) if len(returns) > 1 else 0,
                'sharpeRatio': self._calculate_sharpe_ratio(returns),
                'maxDrawdown': self._calculate_max_drawdown(portfolio_values)
            }
            
        except Exception as e:
            logger.error(f"Error calculating weighted portfolio: {e}")
            return self._get_default_portfolio_data()
    
    def _calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) == 0:
            return 0.0
        
        excess_returns = np.array(returns) - (risk_free_rate / 252)  # Daily risk-free rate
        if np.std(excess_returns) == 0:
            return 0.0
        
        return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
    
    def _calculate_max_drawdown(self, prices: List[float]) -> float:
        """Calculate maximum drawdown"""
        if len(prices) == 0:
            return 0.0
        
        peak = prices[0]
        max_dd = 0.0
        
        for price in prices:
            if price > peak:
                peak = price
            drawdown = (peak - price) / peak
            if drawdown > max_dd:
                max_dd = drawdown
        
        return max_dd * 100  # Return as percentage
    
    def _get_default_portfolio_data(self) -> Dict[str, Any]:
        """Return default portfolio data when calculation fails"""
        return {
            'dataPoints': [],
            'startValue': 100.0,
            'endValue': 100.0,
            'totalReturn': 0.0,
            'totalReturnPercent': 0.0,
            'volatility': 0.0,
            'sharpeRatio': 0.0,
            'maxDrawdown': 0.0
        }
    
    def get_predefined_benchmarks(self) -> List[Dict[str, Any]]:
        """Get list of predefined benchmark portfolios"""
        return [
            {
                'name': 'S&P 500 Equal Weight',
                'description': 'Equal-weighted S&P 500 portfolio',
                'symbols': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'AMD', 'INTC'],
                'weights': [0.1] * 10
            },
            {
                'name': 'Tech Heavy',
                'description': 'Technology-focused portfolio',
                'symbols': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'AMD', 'CRM'],
                'weights': [0.15, 0.15, 0.15, 0.15, 0.1, 0.1, 0.1, 0.05, 0.03, 0.02]
            },
            {
                'name': 'Dividend Focused',
                'description': 'High dividend yield portfolio',
                'symbols': ['JNJ', 'PG', 'KO', 'PEP', 'WMT', 'T', 'VZ', 'XOM', 'CVX', 'JPM'],
                'weights': [0.12, 0.12, 0.12, 0.12, 0.1, 0.1, 0.1, 0.1, 0.1, 0.02]
            },
            {
                'name': 'Growth Stocks',
                'description': 'High growth potential portfolio',
                'symbols': ['TSLA', 'NVDA', 'AMD', 'NFLX', 'CRM', 'ADBE', 'PYPL', 'UBER', 'LYFT', 'ZM'],
                'weights': [0.2, 0.2, 0.15, 0.1, 0.1, 0.1, 0.05, 0.03, 0.03, 0.04]
            },
            {
                'name': 'Value Stocks',
                'description': 'Undervalued stocks portfolio',
                'symbols': ['BRK.B', 'JPM', 'BAC', 'WFC', 'XOM', 'CVX', 'JNJ', 'PG', 'KO', 'WMT'],
                'weights': [0.15, 0.15, 0.15, 0.1, 0.1, 0.1, 0.1, 0.05, 0.05, 0.05]
            }
        ]
    
    def create_predefined_benchmark(self, user: User, benchmark_name: str) -> Optional[CustomBenchmark]:
        """Create a predefined benchmark for a user"""
        try:
            predefined = next((b for b in self.get_predefined_benchmarks() if b['name'] == benchmark_name), None)
            if not predefined:
                logger.error(f"Predefined benchmark '{benchmark_name}' not found")
                return None
            
            holdings = []
            for symbol, weight in zip(predefined['symbols'], predefined['weights']):
                holdings.append({
                    'symbol': symbol,
                    'weight': weight,
                    'name': symbol,
                    'sector': 'Mixed',
                    'description': f'Component of {benchmark_name}'
                })
            
            return self.create_custom_benchmark(
                user=user,
                name=predefined['name'],
                description=predefined['description'],
                holdings=holdings
            )
            
        except Exception as e:
            logger.error(f"Error creating predefined benchmark: {e}")
            return None

# Global instance
custom_benchmark_service = CustomBenchmarkService()
