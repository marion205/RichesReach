# core/stock_service.py
import requests
import os
from typing import Dict, List, Optional
from decimal import Decimal
from .models import Stock, StockData
from django.conf import settings
from .rust_stock_service import rust_stock_service

class AlphaVantageService:
    """Service for interacting with Alpha Vantage API"""
    
    def __init__(self):
        self.api_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        self.base_url = 'https://www.alphavantage.co/query'
    
    def search_stocks(self, query: str) -> List[Dict]:
        """Search for stocks by company name or symbol"""
        params = {
            'function': 'SYMBOL_SEARCH',
            'keywords': query,
            'apikey': self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'bestMatches' in data:
                return data['bestMatches']
            return []
        except Exception as e:
            print(f"Error searching stocks: {e}")
            return []
    
    def get_stock_quote(self, symbol: str) -> Optional[Dict]:
        """Get real-time stock quote"""
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'Global Quote' in data:
                return data['Global Quote']
            return None
        except Exception as e:
            print(f"Error getting stock quote: {e}")
            return None
    
    def get_company_overview(self, symbol: str) -> Optional[Dict]:
        """Get company overview and fundamentals"""
        params = {
            'function': 'OVERVIEW',
            'symbol': symbol,
            'apikey': self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'Symbol' in data:
                return data
            return None
        except Exception as e:
            print(f"Error getting company overview: {e}")
            return None
    
    def calculate_beginner_friendly_score(self, company_data: Dict) -> int:
        """Calculate a score (0-100) for how beginner-friendly a stock is"""
        score = 50  # Start with neutral score
        
        try:
            # Market cap scoring (higher is better for beginners)
            if 'MarketCapitalization' in company_data:
                market_cap = float(company_data['MarketCapitalization'])
                if market_cap > 10000000000:  # >$10B
                    score += 20
                elif market_cap > 1000000000:  # >$1B
                    score += 10
            
            # P/E ratio scoring (lower is generally better for beginners)
            if 'PERatio' in company_data and company_data['PERatio'] != 'None':
                pe_ratio = float(company_data['PERatio'])
                if pe_ratio < 15:
                    score += 15
                elif pe_ratio < 25:
                    score += 10
            
            # Dividend yield scoring (higher is better for beginners)
            if 'DividendYield' in company_data and company_data['DividendYield'] != 'None':
                dividend_yield = float(company_data['DividendYield'])
                if dividend_yield > 2.0:
                    score += 15
            
            # Debt ratio scoring (lower is better for beginners)
            if 'TotalDebtToEquity' in company_data and company_data['TotalDebtToEquity'] != 'None':
                debt_ratio = float(company_data['TotalDebtToEquity'])
                if debt_ratio < 0.5:
                    score += 10
                elif debt_ratio < 1.0:
                    score += 5
            
            # Sector scoring (some sectors are more stable for beginners)
            stable_sectors = ['Consumer Defensive', 'Healthcare', 'Utilities', 'Consumer Cyclical']
            if 'Sector' in company_data and company_data['Sector'] in stable_sectors:
                score += 10
            
        except (ValueError, TypeError):
            pass  # If any conversion fails, just use the base score
        
        return min(100, max(0, score))  # Ensure score is between 0-100
    
    def sync_stock_data(self, symbol: str) -> Optional[Stock]:
        """Sync stock data from Alpha Vantage API to our database"""
        try:
            # Get company overview
            company_data = self.get_company_overview(symbol)
            if not company_data:
                return None
            
            # Get current quote
            quote_data = self.get_stock_quote(symbol)
            
            # Create or update stock
            stock, created = Stock.objects.get_or_create(
                symbol=symbol.upper(),
                defaults={
                    'company_name': company_data.get('Name', symbol),
                    'sector': company_data.get('Sector', ''),
                    'market_cap': int(float(company_data.get('MarketCapitalization', 0))) if company_data.get('MarketCapitalization') != 'None' else None,
                    'pe_ratio': Decimal(company_data.get('PERatio', 0)) if company_data.get('PERatio') != 'None' else None,
                    'dividend_yield': Decimal(company_data.get('DividendYield', 0)) if company_data.get('DividendYield') != 'None' else None,
                    'debt_ratio': Decimal(company_data.get('TotalDebtToEquity', 0)) if company_data.get('TotalDebtToEquity') != 'None' else None,
                    'volatility': Decimal(company_data.get('Beta', 0)) if company_data.get('Beta') != 'None' else None,
                }
            )
            
            if not created:
                # Update existing stock
                stock.company_name = company_data.get('Name', symbol)
                stock.sector = company_data.get('Sector', '')
                stock.market_cap = int(float(company_data.get('MarketCapitalization', 0))) if company_data.get('MarketCapitalization') != 'None' else None
                stock.pe_ratio = Decimal(company_data.get('PERatio', 0)) if company_data.get('PERatio') != 'None' else None
                stock.dividend_yield = Decimal(company_data.get('DividendYield', 0)) if company_data.get('DividendYield') != 'None' else None
                stock.debt_ratio = Decimal(company_data.get('TotalDebtToEquity', 0)) if company_data.get('TotalDebtToEquity') != 'None' else None
                stock.volatility = Decimal(company_data.get('Beta', 0)) if company_data.get('Beta') != 'None' else None
            
            # Calculate beginner-friendly score
            stock.beginner_friendly_score = self.calculate_beginner_friendly_score(company_data)
            stock.save()
            
            return stock
            
        except Exception as e:
            print(f"Error syncing stock data for {symbol}: {e}")
            return None
    
    def analyze_stock_with_rust(self, symbol: str, include_technical: bool = True, include_fundamental: bool = True) -> Optional[Dict]:
        """
        Analyze a stock using the high-performance Rust engine
        """
        try:
            if not rust_stock_service.is_available():
                print("Rust service not available, falling back to Python analysis")
                return None
            
            # Use Rust engine for analysis
            analysis = rust_stock_service.analyze_stock(symbol, include_technical, include_fundamental)
            
            if analysis.get('success') and analysis.get('analysis'):
                return analysis['analysis']
            else:
                print(f"Rust analysis failed for {symbol}: {analysis.get('error', 'Unknown error')}")
                return None
                
        except Exception as e:
            print(f"Error using Rust engine for {symbol}: {e}")
            return None
    
    def get_rust_recommendations(self) -> Optional[List[Dict]]:
        """
        Get beginner-friendly stock recommendations from Rust engine
        """
        try:
            if not rust_stock_service.is_available():
                print("Rust service not available")
                return None
            
            recommendations = rust_stock_service.get_recommendations()
            return recommendations.get('recommendations', [])
            
        except Exception as e:
            print(f"Error getting Rust recommendations: {e}")
            return None
