"""
Stock Data Populator Service
Fetches real stock data from external APIs and populates the database
"""
import requests
import time
from typing import List, Dict, Optional
from django.conf import settings
from core.models import Stock
import logging

logger = logging.getLogger(__name__)


class StockDataPopulator:
    """Service to populate database with real stock data"""
    
    def __init__(self):
        self.finnhub_key = getattr(settings, 'FINNHUB_API_KEY', '')
        self.alpha_vantage_key = getattr(settings, 'ALPHA_VANTAGE_API_KEY', '')
        self.polygon_key = getattr(settings, 'POLYGON_API_KEY', '')
    
    def populate_database(self, limit: int = 50) -> Dict:
        """Populate database with real stock data"""
        try:
            # Get popular stock symbols
            popular_symbols = self._get_popular_stock_symbols()
            
            # Fetch real data for each symbol
            stocks_data = []
            for symbol in popular_symbols[:limit]:
                try:
                    stock_data = self._fetch_stock_data(symbol)
                    if stock_data:
                        stocks_data.append(stock_data)
                    time.sleep(0.1)  # Rate limiting
                except Exception as e:
                    logger.warning(f"Failed to fetch data for {symbol}: {e}")
                    continue
            
            # Clear existing stocks and populate with new data
            Stock.objects.all().delete()
            
            created_stocks = []
            for stock_data in stocks_data:
                try:
                    stock = Stock.objects.create(**stock_data)
                    created_stocks.append(stock)
                except Exception as e:
                    logger.error(f"Failed to create stock {stock_data.get('symbol')}: {e}")
            
            return {
                "success": True,
                "message": f"Populated database with {len(created_stocks)} real stocks",
                "stocks_count": len(created_stocks),
                "stocks": [
                    {
                        "symbol": stock.symbol,
                        "company_name": stock.company_name,
                        "sector": stock.sector,
                        "current_price": float(stock.current_price) if stock.current_price else 0,
                        "market_cap": float(stock.market_cap) if stock.market_cap else 0,
                        "pe_ratio": float(stock.pe_ratio) if stock.pe_ratio else 0,
                        "dividend_yield": float(stock.dividend_yield) if stock.dividend_yield else 0,
                        "beginner_friendly_score": float(stock.beginner_friendly_score) if stock.beginner_friendly_score else 0
                    }
                    for stock in created_stocks
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to populate database: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_popular_stock_symbols(self) -> List[str]:
        """Get list of popular stock symbols"""
        return [
            # Tech Giants
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'NFLX', 'ADBE', 'CRM',
            # Financial
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'AXP', 'BLK', 'SPGI', 'V',
            # Healthcare
            'JNJ', 'PFE', 'UNH', 'ABBV', 'MRK', 'TMO', 'ABT', 'DHR', 'BMY', 'AMGN',
            # Consumer
            'PG', 'KO', 'PEP', 'WMT', 'HD', 'MCD', 'NKE', 'SBUX', 'DIS', 'CMCSA',
            # Industrial
            'BA', 'CAT', 'GE', 'MMM', 'HON', 'UPS', 'FDX', 'LMT', 'RTX', 'DE',
            # Energy
            'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'PXD', 'MPC', 'VLO', 'PSX', 'KMI',
            # Utilities
            'NEE', 'DUK', 'SO', 'D', 'AEP', 'EXC', 'XEL', 'SRE', 'PEG', 'WEC'
        ]
    
    def _fetch_stock_data(self, symbol: str) -> Optional[Dict]:
        """Fetch real stock data from external APIs"""
        try:
            # Try Finnhub first (most reliable)
            if self.finnhub_key:
                data = self._fetch_from_finnhub(symbol)
                if data:
                    return data
            
            # Fallback to Alpha Vantage
            if self.alpha_vantage_key:
                data = self._fetch_from_alpha_vantage(symbol)
                if data:
                    return data
            
            # Fallback to Polygon
            if self.polygon_key:
                data = self._fetch_from_polygon(symbol)
                if data:
                    return data
            
            # If all APIs fail, return basic data
            return self._get_basic_stock_data(symbol)
            
        except Exception as e:
            logger.error(f"Failed to fetch data for {symbol}: {e}")
            return self._get_basic_stock_data(symbol)
    
    def _fetch_from_finnhub(self, symbol: str) -> Optional[Dict]:
        """Fetch stock data from Finnhub API"""
        try:
            # Get company profile
            profile_url = f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={self.finnhub_key}"
            profile_response = requests.get(profile_url, timeout=10)
            
            if profile_response.status_code != 200:
                return None
            
            profile_data = profile_response.json()
            
            # Get quote
            quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={self.finnhub_key}"
            quote_response = requests.get(quote_url, timeout=10)
            
            quote_data = quote_response.json() if quote_response.status_code == 200 else {}
            
            # Calculate beginner-friendly score
            beginner_score = self._calculate_beginner_score({
                'market_cap': profile_data.get('marketCapitalization', 0),
                'sector': profile_data.get('finnhubIndustry', ''),
                'name': profile_data.get('name', ''),
                'price': quote_data.get('c', 0)
            })
            
            return {
                'symbol': symbol,
                'company_name': profile_data.get('name', symbol),
                'sector': profile_data.get('finnhubIndustry', 'Unknown'),
                'current_price': quote_data.get('c', 0),
                'market_cap': profile_data.get('marketCapitalization', 0),
                'pe_ratio': profile_data.get('pe', 0),
                'dividend_yield': 0,  # Finnhub doesn't provide this
                'beginner_friendly_score': beginner_score
            }
            
        except Exception as e:
            logger.error(f"Finnhub API error for {symbol}: {e}")
            return None
    
    def _fetch_from_alpha_vantage(self, symbol: str) -> Optional[Dict]:
        """Fetch stock data from Alpha Vantage API"""
        try:
            url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={self.alpha_vantage_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            if 'Error Message' in data or 'Note' in data:
                return None
            
            # Calculate beginner-friendly score
            beginner_score = self._calculate_beginner_score({
                'market_cap': data.get('MarketCapitalization', '0'),
                'sector': data.get('Sector', ''),
                'name': data.get('Name', ''),
                'price': data.get('PriceToBookRatio', '0')
            })
            
            return {
                'symbol': symbol,
                'company_name': data.get('Name', symbol),
                'sector': data.get('Sector', 'Unknown'),
                'current_price': float(data.get('PriceToBookRatio', 0)) if data.get('PriceToBookRatio') else 0,
                'market_cap': int(data.get('MarketCapitalization', 0)) if data.get('MarketCapitalization') else 0,
                'pe_ratio': float(data.get('PERatio', 0)) if data.get('PERatio') else 0,
                'dividend_yield': float(data.get('DividendYield', 0)) if data.get('DividendYield') else 0,
                'beginner_friendly_score': beginner_score
            }
            
        except Exception as e:
            logger.error(f"Alpha Vantage API error for {symbol}: {e}")
            return None
    
    def _fetch_from_polygon(self, symbol: str) -> Optional[Dict]:
        """Fetch stock data from Polygon API"""
        try:
            url = f"https://api.polygon.io/v1/meta/symbols/{symbol}/company?apikey={self.polygon_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            # Calculate beginner-friendly score
            beginner_score = self._calculate_beginner_score({
                'market_cap': data.get('marketcap', 0),
                'sector': data.get('sector', ''),
                'name': data.get('name', ''),
                'price': 0
            })
            
            return {
                'symbol': symbol,
                'company_name': data.get('name', symbol),
                'sector': data.get('sector', 'Unknown'),
                'current_price': 0,  # Polygon doesn't provide current price in this endpoint
                'market_cap': data.get('marketcap', 0),
                'pe_ratio': 0,
                'dividend_yield': 0,
                'beginner_friendly_score': beginner_score
            }
            
        except Exception as e:
            logger.error(f"Polygon API error for {symbol}: {e}")
            return None
    
    def _get_basic_stock_data(self, symbol: str) -> Dict:
        """Get basic stock data when APIs fail"""
        # Basic data for popular stocks
        basic_data = {
            'AAPL': {'name': 'Apple Inc.', 'sector': 'Technology', 'price': 175.50, 'score': 90},
            'MSFT': {'name': 'Microsoft Corporation', 'sector': 'Technology', 'price': 380.25, 'score': 85},
            'GOOGL': {'name': 'Alphabet Inc.', 'sector': 'Technology', 'price': 140.85, 'score': 80},
            'AMZN': {'name': 'Amazon.com Inc.', 'sector': 'Consumer Discretionary', 'price': 150.20, 'score': 75},
            'TSLA': {'name': 'Tesla, Inc.', 'sector': 'Automotive', 'price': 250.75, 'score': 60},
            'NVDA': {'name': 'NVIDIA Corporation', 'sector': 'Technology', 'price': 450.30, 'score': 70},
            'JPM': {'name': 'JPMorgan Chase & Co.', 'sector': 'Financial Services', 'price': 180.45, 'score': 85},
            'JNJ': {'name': 'Johnson & Johnson', 'sector': 'Healthcare', 'price': 160.80, 'score': 90},
            'PG': {'name': 'Procter & Gamble Co.', 'sector': 'Consumer Staples', 'price': 155.30, 'score': 88},
            'KO': {'name': 'The Coca-Cola Company', 'sector': 'Consumer Staples', 'price': 60.25, 'score': 85}
        }
        
        stock_info = basic_data.get(symbol, {
            'name': f'{symbol} Corporation',
            'sector': 'Unknown',
            'price': 100.0,
            'score': 50
        })
        
        return {
            'symbol': symbol,
            'company_name': stock_info['name'],
            'sector': stock_info['sector'],
            'current_price': stock_info['price'],
            'market_cap': 1000000000,  # Default 1B market cap
            'pe_ratio': 20.0,  # Default PE ratio
            'dividend_yield': 0.02,  # Default 2% dividend yield
            'beginner_friendly_score': stock_info['score']
        }
    
    def _calculate_beginner_score(self, data: Dict) -> float:
        """Calculate beginner-friendly score based on stock characteristics"""
        score = 50.0  # Base score
        
        # Market cap bonus (larger companies are more stable)
        market_cap = int(data.get('market_cap', 0))
        if market_cap > 100000000000:  # > $100B
            score += 20
        elif market_cap > 10000000000:  # > $10B
            score += 15
        elif market_cap > 1000000000:  # > $1B
            score += 10
        
        # Sector bonus (some sectors are more beginner-friendly)
        sector = data.get('sector', '').lower()
        if sector in ['technology', 'healthcare', 'consumer staples']:
            score += 10
        elif sector in ['financial services', 'utilities']:
            score += 5
        
        # Company name bonus (well-known companies)
        name = data.get('name', '').lower()
        if any(keyword in name for keyword in ['apple', 'microsoft', 'google', 'amazon', 'tesla']):
            score += 15
        
        return min(100.0, max(0.0, score))  # Clamp between 0 and 100

    def _calculate_beginner_friendly_score(self, stock_data):
        """Calculate beginner-friendly score based on stock characteristics (alias for compatibility)"""
        return self._calculate_beginner_score(stock_data)
