# core/stock_data_provider.py
import os
import requests
import time
from typing import Dict, List, Optional

class StockDataProvider:
    """Unified stock data provider that can use multiple APIs"""
    
    def __init__(self):
        self.polygon_api_key = os.getenv('POLYGON_API_KEY')
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.finnhub_key = os.getenv('FINNHUB_API_KEY')
        
    def get_stock_data(self, symbol: str) -> Optional[Dict]:
        """Get stock data from the best available provider"""
        
        # Try Polygon.io first (best free tier)
        if self.polygon_api_key:
            data = self._get_polygon_data(symbol)
            if data:
                return data
        
        # Try FinnHub as backup
        if self.finnhub_key:
            data = self._get_finnhub_data(symbol)
            if data:
                return data
                
        # Fallback to mock data
        return self._get_mock_data(symbol)
    
    def _get_polygon_data(self, symbol: str) -> Optional[Dict]:
        """Get data from Polygon.io (free tier: 5 calls/minute, 1000 calls/day)"""
        try:
            url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev"
            params = {
                'adjusted': 'true',
                'apikey': self.polygon_api_key
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'OK' and data.get('results'):
                    result = data['results'][0]
                    return {
                        'symbol': symbol,
                        'price': result.get('c', 0),  # Close price
                        'change': result.get('c', 0) - result.get('o', 0),  # Close - Open
                        'change_percent': ((result.get('c', 0) - result.get('o', 0)) / result.get('o', 1)) * 100,
                        'volume': result.get('v', 0),
                        'high': result.get('h', 0),
                        'low': result.get('l', 0),
                        'provider': 'polygon'
                    }
        except Exception as e:
            print(f"Polygon.io error for {symbol}: {e}")
        
        return None
    
    def _get_finnhub_data(self, symbol: str) -> Optional[Dict]:
        """Get data from FinnHub (free tier: 60 calls/minute)"""
        try:
            url = f"https://finnhub.io/api/v1/quote"
            params = {
                'symbol': symbol,
                'token': self.finnhub_key
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('c'):  # Current price exists
                    return {
                        'symbol': symbol,
                        'price': data.get('c', 0),
                        'change': data.get('d', 0),  # Change
                        'change_percent': data.get('dp', 0),  # Change percent
                        'high': data.get('h', 0),
                        'low': data.get('l', 0),
                        'provider': 'finnhub'
                    }
        except Exception as e:
            print(f"FinnHub error for {symbol}: {e}")
        
        return None
    
    def _get_mock_data(self, symbol: str) -> Dict:
        """Return mock data when APIs are unavailable"""
        mock_prices = {
            'AAPL': {'price': 175.50, 'change': 2.30, 'change_percent': 1.33},
            'MSFT': {'price': 380.25, 'change': -1.75, 'change_percent': -0.46},
            'TSLA': {'price': 250.75, 'change': 5.20, 'change_percent': 2.12},
            'NVDA': {'price': 450.30, 'change': 12.80, 'change_percent': 2.93},
            'GOOGL': {'price': 140.85, 'change': 0.95, 'change_percent': 0.68},
            'AMZN': {'price': 155.20, 'change': -0.80, 'change_percent': -0.51},
            'META': {'price': 485.60, 'change': 8.40, 'change_percent': 1.76},
            'NFLX': {'price': 620.15, 'change': 3.25, 'change_percent': 0.53},
        }
        
        data = mock_prices.get(symbol.upper(), {
            'price': 100.00,
            'change': 0.50,
            'change_percent': 0.50
        })
        
        return {
            'symbol': symbol.upper(),
            'price': data['price'],
            'change': data['change'],
            'change_percent': data['change_percent'],
            'volume': 1000000,
            'high': data['price'] + 2.0,
            'low': data['price'] - 2.0,
            'provider': 'mock'
        }

# Global instance
stock_provider = StockDataProvider()
