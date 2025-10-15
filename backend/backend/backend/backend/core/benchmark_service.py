import logging
import requests
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

class BenchmarkService:
    """Service for fetching and processing benchmark data"""
    
    def __init__(self):
        self.benchmark_info = {
            'SPY': {'name': 'SPDR S&P 500 ETF', 'description': 'S&P 500 Index'},
            'QQQ': {'name': 'Invesco QQQ Trust', 'description': 'NASDAQ-100 Index'},
            'DIA': {'name': 'SPDR Dow Jones Industrial Average ETF', 'description': 'Dow Jones Industrial Average'},
            'IWM': {'name': 'iShares Russell 2000 ETF', 'description': 'Russell 2000 Index'},
            'VTI': {'name': 'Vanguard Total Stock Market ETF', 'description': 'Total Stock Market'},
            'VEA': {'name': 'Vanguard FTSE Developed Markets ETF', 'description': 'Developed Markets'},
            'VWO': {'name': 'Vanguard FTSE Emerging Markets ETF', 'description': 'Emerging Markets'},
            'AGG': {'name': 'iShares Core U.S. Aggregate Bond ETF', 'description': 'Total Bond Market'},
            'TLT': {'name': 'iShares 20+ Year Treasury Bond ETF', 'description': 'Long-term Treasury'},
            'GLD': {'name': 'SPDR Gold Shares', 'description': 'Gold'},
            'SLV': {'name': 'iShares Silver Trust', 'description': 'Silver'},
        }
    
    def get_benchmark_series(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """Get benchmark series data for a symbol and timeframe"""
        try:
            # For now, we'll use mock data that's more realistic
            # In production, this would integrate with real APIs like Alpha Vantage, Yahoo Finance, etc.
            
            if not self._is_valid_symbol(symbol):
                logger.warning(f"Invalid benchmark symbol: {symbol}")
                return None
            
            # Generate realistic mock data based on the symbol and timeframe
            data_points = self._generate_mock_benchmark_data(symbol, timeframe)
            
            if not data_points:
                return None
            
            # Calculate metrics
            start_value = data_points[0]['value']
            end_value = data_points[-1]['value']
            total_return = end_value - start_value
            total_return_percent = (total_return / start_value) * 100
            
            # Calculate volatility
            returns = [point['changePercent'] for point in data_points[1:]]
            volatility = np.std(returns) if len(returns) > 1 else 0
            
            return {
                'symbol': symbol,
                'name': self.benchmark_info[symbol]['name'],
                'timeframe': timeframe,
                'dataPoints': data_points,
                'startValue': start_value,
                'endValue': end_value,
                'totalReturn': total_return,
                'totalReturnPercent': total_return_percent,
                'volatility': volatility
            }
            
        except Exception as e:
            logger.error(f"Error getting benchmark series for {symbol} {timeframe}: {e}")
            return None
    
    def _is_valid_symbol(self, symbol: str) -> bool:
        """Check if symbol is valid"""
        return symbol.upper() in self.benchmark_info
    
    def _generate_mock_benchmark_data(self, symbol: str, timeframe: str) -> List[Dict[str, Any]]:
        """Generate realistic mock benchmark data"""
        try:
            # Get timeframe parameters
            timeframe_config = self._get_timeframe_config(timeframe)
            if not timeframe_config:
                return []
            
            points, interval_minutes, base_value = timeframe_config
            
            # Symbol-specific characteristics
            symbol_config = self._get_symbol_config(symbol)
            
            # Generate time series
            data_points = []
            current_time = datetime.now() - timedelta(minutes=interval_minutes * points)
            current_value = base_value
            
            for i in range(points):
                # Add some realistic market behavior
                volatility = symbol_config['volatility']
                drift = symbol_config['drift']
                
                # Add some correlation with market cycles
                cycle_factor = np.sin(i * 0.1) * 0.3
                
                # Random walk with drift
                change_percent = (np.random.normal(drift, volatility) + cycle_factor) / 100
                new_value = current_value * (1 + change_percent)
                
                # Ensure positive values
                new_value = max(new_value, current_value * 0.95)
                
                change = new_value - current_value
                change_percent_actual = (change / current_value) * 100
                
                data_points.append({
                    'timestamp': current_time.isoformat(),
                    'value': round(new_value, 2),
                    'change': round(change, 2),
                    'changePercent': round(change_percent_actual, 2)
                })
                
                current_value = new_value
                current_time += timedelta(minutes=interval_minutes)
            
            return data_points
            
        except Exception as e:
            logger.error(f"Error generating mock benchmark data: {e}")
            return []
    
    def _get_timeframe_config(self, timeframe: str) -> Optional[tuple]:
        """Get configuration for timeframe"""
        configs = {
            '1D': (24, 60, 450.0),      # 24 hours, hourly data, start at $450
            '1W': (7, 1440, 450.0),     # 7 days, daily data, start at $450
            '1M': (30, 1440, 450.0),    # 30 days, daily data, start at $450
            '3M': (13, 10080, 450.0),   # 13 weeks, weekly data, start at $450
            '6M': (26, 10080, 450.0),   # 26 weeks, weekly data, start at $450
            '1Y': (12, 43200, 450.0),   # 12 months, monthly data, start at $450
            'All': (60, 43200, 400.0),  # 60 months, monthly data, start at $400
        }
        return configs.get(timeframe)
    
    def _get_symbol_config(self, symbol: str) -> Dict[str, float]:
        """Get symbol-specific configuration for realistic data generation"""
        configs = {
            'SPY': {'volatility': 1.2, 'drift': 0.05},      # S&P 500 - moderate volatility, slight upward drift
            'QQQ': {'volatility': 1.8, 'drift': 0.08},      # NASDAQ - higher volatility, tech growth
            'DIA': {'volatility': 1.1, 'drift': 0.04},      # Dow Jones - lower volatility, blue chip stability
            'IWM': {'volatility': 2.1, 'drift': 0.06},      # Small caps - high volatility
            'VTI': {'volatility': 1.3, 'drift': 0.05},      # Total market - similar to SPY
            'VEA': {'volatility': 1.4, 'drift': 0.03},      # Developed markets - moderate
            'VWO': {'volatility': 2.5, 'drift': 0.07},      # Emerging markets - high volatility
            'AGG': {'volatility': 0.4, 'drift': 0.01},      # Bonds - low volatility
            'TLT': {'volatility': 1.0, 'drift': 0.02},      # Long-term bonds - moderate
            'GLD': {'volatility': 1.6, 'drift': 0.04},      # Gold - moderate volatility
            'SLV': {'volatility': 2.8, 'drift': 0.05},      # Silver - high volatility
        }
        return configs.get(symbol, {'volatility': 1.5, 'drift': 0.05})
    
    def get_real_benchmark_data(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """Get real benchmark data from external APIs (placeholder for production)"""
        # This would integrate with real APIs in production
        # For now, we'll use the mock data
        logger.info(f"Would fetch real data for {symbol} {timeframe} from external API")
        return self.get_benchmark_series(symbol, timeframe)
    
    def get_benchmark_performance_summary(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """Get summary performance metrics for a benchmark"""
        series_data = self.get_benchmark_series(symbol, timeframe)
        if not series_data:
            return None
        
        return {
            'symbol': symbol,
            'name': series_data['name'],
            'timeframe': timeframe,
            'totalReturn': series_data['totalReturn'],
            'totalReturnPercent': series_data['totalReturnPercent'],
            'volatility': series_data['volatility'],
            'startValue': series_data['startValue'],
            'endValue': series_data['endValue']
        }
