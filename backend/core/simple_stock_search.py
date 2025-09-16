"""
Simple stock search service that uses Alpha Vantage API to search for stocks
and populate the database with real data.
"""
import os
import requests
import logging
from typing import List, Optional, Dict, Any
from django.conf import settings
from .models import Stock

logger = logging.getLogger(__name__)

class SimpleStockSearchService:
    """Simple service for searching stocks using Alpha Vantage API with Finnhub fallback"""
    
    def __init__(self):
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_KEY')
        self.finnhub_key = os.getenv('FINNHUB_KEY')
        self.alpha_vantage_url = 'https://www.alphavantage.co/query'
        self.finnhub_url = 'https://finnhub.io/api/v1'
        self.session = requests.Session()
        
        if not self.alpha_vantage_key:
            logger.warning("ALPHA_VANTAGE_KEY not set in environment variables.")
        if not self.finnhub_key:
            logger.warning("FINNHUB_KEY not set in environment variables.")
    
    def search_and_sync_stocks(self, search_query: str) -> List[Stock]:
        """Search for stocks and sync them to the database using Alpha Vantage with Finnhub fallback"""
        # Try Alpha Vantage first
        stocks = self._search_alpha_vantage(search_query)
        if stocks:
            return stocks
        
        # Fallback to Finnhub if Alpha Vantage fails
        logger.info("Alpha Vantage failed, trying Finnhub fallback")
        stocks = self._search_finnhub(search_query)
        if stocks:
            return stocks
        
        # Final fallback to database search
        logger.info("Both APIs failed, falling back to database search")
        return self._search_database(search_query)
    
    def _search_alpha_vantage(self, search_query: str) -> List[Stock]:
        """Search using Alpha Vantage API"""
        if not self.alpha_vantage_key:
            return []
        
        try:
            params = {
                'function': 'SYMBOL_SEARCH',
                'keywords': search_query,
                'apikey': self.alpha_vantage_key
            }
            
            response = self.session.get(self.alpha_vantage_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                return []
            
            if 'Note' in data:
                logger.warning(f"Alpha Vantage rate limit: {data['Note']}")
                return []
            
            if 'Information' in data:
                logger.warning(f"Alpha Vantage info: {data['Information']}")
                return []
            
            if 'bestMatches' not in data:
                logger.warning("No matches found in Alpha Vantage response")
                return []
            
            stocks = []
            for match in data['bestMatches'][:10]:  # Limit to 10 results
                try:
                    stock = self._create_or_update_stock_from_alpha_vantage(match)
                    if stock:
                        stocks.append(stock)
                except Exception as e:
                    import traceback
                    logger.error(f"Error processing Alpha Vantage stock {match.get('1. symbol', 'Unknown')}: {e}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    continue
            
            return stocks
            
        except Exception as e:
            logger.error(f"Error searching Alpha Vantage: {e}")
            return []
    
    def _search_finnhub(self, search_query: str) -> List[Stock]:
        """Search using Finnhub API"""
        if not self.finnhub_key:
            return []
        
        try:
            params = {
                'q': search_query,
                'token': self.finnhub_key
            }
            
            response = self.session.get(f"{self.finnhub_url}/search", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                logger.error(f"Finnhub API error: {data['error']}")
                return []
            
            if 'result' not in data or not data['result']:
                logger.warning("No matches found in Finnhub response")
                return []
            
            stocks = []
            for match in data['result'][:10]:  # Limit to 10 results
                try:
                    stock = self._create_or_update_stock_from_finnhub(match)
                    if stock:
                        stocks.append(stock)
                except Exception as e:
                    import traceback
                    logger.error(f"Error processing Finnhub stock {match.get('symbol', 'Unknown')}: {e}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    continue
            
            return stocks
            
        except Exception as e:
            logger.error(f"Error searching Finnhub: {e}")
            return []
    
    def _search_database(self, search_query: str) -> List[Stock]:
        """Fallback to database search"""
        try:
            from django.db.models import Q
            stocks = Stock.objects.filter(
                Q(symbol__icontains=search_query.upper()) |
                Q(company_name__icontains=search_query)
            ).order_by('symbol')[:10]
            return list(stocks)
        except Exception as e:
            logger.error(f"Error searching database: {e}")
            return []
    
    def _create_or_update_stock_from_alpha_vantage(self, match: Dict[str, Any]) -> Optional[Stock]:
        """Create or update stock from Alpha Vantage data"""
        from decimal import Decimal
        symbol = match['1. symbol']
        company_name = match['2. name']
        region = match['4. region']
        
        stock, created = Stock.objects.get_or_create(
            symbol=symbol,
            defaults={
                'company_name': company_name,
                'sector': region,
                'market_cap': None,
                'pe_ratio': Decimal('0.00'),
                'dividend_yield': Decimal('0.00'),
                'debt_ratio': Decimal('0.00'),
                'volatility': Decimal('0.00'),
                'current_price': Decimal('0.00'),
                'beginner_friendly_score': 50
            }
        )
        
        if created:
            logger.info(f"Created new stock from Alpha Vantage: {stock.symbol}")
            self._update_stock_overview_alpha_vantage(stock)
        
        return stock
    
    def _create_or_update_stock_from_finnhub(self, match: Dict[str, Any]) -> Optional[Stock]:
        """Create or update stock from Finnhub data"""
        from decimal import Decimal
        symbol = match.get('symbol', '')
        description = match.get('description', '')
        display_symbol = match.get('displaySymbol', symbol)
        stock_type = match.get('type', '')
        
        if not symbol:
            return None
        
        # Only try to get detailed profile for main US stocks (no dots in symbol)
        # International stocks often don't have profile data
        is_main_stock = '.' not in symbol and stock_type == 'Common Stock'
        
        stock, created = Stock.objects.get_or_create(
            symbol=symbol,
            defaults={
                'company_name': description or display_symbol,
                'sector': 'Unknown',
                'market_cap': None,
                'pe_ratio': Decimal('0.00'),
                'dividend_yield': Decimal('0.00'),
                'debt_ratio': Decimal('0.00'),
                'volatility': Decimal('0.00'),
                'current_price': Decimal('0.00'),
                'beginner_friendly_score': 50
            }
        )
        
        if created:
            logger.info(f"Created new stock from Finnhub: {stock.symbol}")
            # Only try to get detailed profile for main stocks
            if is_main_stock:
                self._update_stock_overview_finnhub(stock)
            else:
                # For international stocks, just set a basic score
                stock.beginner_friendly_score = 60 if 'APPLE' in description.upper() else 50
                stock.save()
        
        return stock
    
    def _update_stock_overview_alpha_vantage(self, stock: Stock) -> bool:
        """Update stock with Alpha Vantage company overview data"""
        if not self.alpha_vantage_key:
            return False
        
        try:
            params = {
                'function': 'OVERVIEW',
                'symbol': stock.symbol,
                'apikey': self.alpha_vantage_key
            }
            
            response = self.session.get(self.alpha_vantage_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage overview error for {stock.symbol}: {data['Error Message']}")
                return False
            
            # Update stock with overview data
            if 'MarketCapitalization' in data and data['MarketCapitalization'] != 'None':
                try:
                    stock.market_cap = int(data['MarketCapitalization'])
                except (ValueError, TypeError):
                    pass
            
            if 'PERatio' in data and data['PERatio'] != 'None':
                try:
                    from decimal import Decimal
                    stock.pe_ratio = Decimal(str(data['PERatio']))
                except (ValueError, TypeError):
                    pass
            
            if 'DividendYield' in data and data['DividendYield'] != 'None':
                try:
                    from decimal import Decimal
                    # Convert percentage to decimal
                    dividend_yield = float(data['DividendYield'].rstrip('%'))
                    stock.dividend_yield = Decimal(str(dividend_yield / 100))
                except (ValueError, TypeError):
                    pass
            
            if 'Sector' in data:
                stock.sector = data['Sector']
            
            # Calculate beginner-friendly score
            stock.beginner_friendly_score = self._calculate_beginner_score(data)
            
            stock.save()
            logger.info(f"Updated stock overview from Alpha Vantage for {stock.symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating stock overview from Alpha Vantage for {stock.symbol}: {e}")
            return False
    
    def _update_stock_overview_finnhub(self, stock: Stock) -> bool:
        """Update stock with Finnhub company profile data"""
        if not self.finnhub_key:
            return False
        
        try:
            params = {
                'symbol': stock.symbol,
                'token': self.finnhub_key
            }
            
            response = self.session.get(f"{self.finnhub_url}/stock/profile2", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                logger.error(f"Finnhub profile error for {stock.symbol}: {data['error']}")
                return False
            
            # Update stock with profile data
            if 'marketCapitalization' in data and data['marketCapitalization']:
                try:
                    # Finnhub returns market cap in millions, convert to full value
                    market_cap_millions = float(data['marketCapitalization'])
                    stock.market_cap = int(market_cap_millions * 1_000_000)
                except (ValueError, TypeError):
                    pass
            
            if 'sector' in data:
                stock.sector = data['sector']
            
            if 'name' in data:
                stock.company_name = data['name']
            
            # Get additional financial data
            self._update_finnhub_financials(stock)
            
            # Calculate beginner-friendly score
            stock.beginner_friendly_score = self._calculate_beginner_score_finnhub(data)
            
            stock.save()
            logger.info(f"Updated stock overview from Finnhub for {stock.symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating stock overview from Finnhub for {stock.symbol}: {e}")
            return False
    
    def _update_finnhub_financials(self, stock: Stock) -> bool:
        """Update stock with Finnhub financial metrics"""
        if not self.finnhub_key:
            return False
        
        try:
            params = {
                'symbol': stock.symbol,
                'token': self.finnhub_key
            }
            
            response = self.session.get(f"{self.finnhub_url}/stock/metric", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                logger.warning(f"Finnhub metrics error for {stock.symbol}: {data['error']}")
                return False
            
            # Update financial metrics
            if 'peTTM' in data and data['peTTM']:
                try:
                    from decimal import Decimal
                    # Get the most recent P/E ratio
                    pe_data = data['peTTM']
                    if isinstance(pe_data, list) and len(pe_data) > 0:
                        latest_pe = pe_data[0]['v']  # Most recent value
                        stock.pe_ratio = Decimal(str(latest_pe))
                    elif isinstance(pe_data, (int, float)):
                        stock.pe_ratio = Decimal(str(pe_data))
                except (ValueError, TypeError, KeyError, IndexError):
                    pass
            
            if 'payoutRatioTTM' in data and data['payoutRatioTTM']:
                try:
                    from decimal import Decimal
                    # Get the most recent payout ratio and convert to dividend yield
                    payout_data = data['payoutRatioTTM']
                    if isinstance(payout_data, list) and len(payout_data) > 0:
                        latest_payout = payout_data[0]['v']  # Most recent value
                        # Convert payout ratio to dividend yield (approximate)
                        # This is a rough calculation - actual dividend yield would need current price
                        stock.dividend_yield = Decimal(str(latest_payout / 100))  # Convert to decimal
                    elif isinstance(payout_data, (int, float)):
                        stock.dividend_yield = Decimal(str(payout_data / 100))
                except (ValueError, TypeError, KeyError, IndexError):
                    pass
            
            return True
            
        except Exception as e:
            logger.warning(f"Error updating Finnhub financials for {stock.symbol}: {e}")
            return False
    
    def _calculate_beginner_score(self, overview_data: Dict[str, Any]) -> int:
        """Calculate beginner-friendly score based on company data"""
        score = 60  # Base score
        
        try:
            # Market cap scoring
            if 'MarketCapitalization' in overview_data and overview_data['MarketCapitalization'] != 'None':
                market_cap = int(overview_data['MarketCapitalization'])
                if market_cap >= 100_000_000_000:  # $100B+
                    score += 20
                elif market_cap >= 10_000_000_000:  # $10B+
                    score += 15
                elif market_cap >= 1_000_000_000:  # $1B+
                    score += 10
            
            # P/E ratio scoring
            if 'PERatio' in overview_data and overview_data['PERatio'] != 'None':
                pe_ratio = float(overview_data['PERatio'])
                if 5 <= pe_ratio <= 25:
                    score += 15
                elif 5 <= pe_ratio <= 35:
                    score += 10
                elif pe_ratio < 50:
                    score += 5
            
            # Dividend yield scoring
            if 'DividendYield' in overview_data and overview_data['DividendYield'] != 'None':
                dividend_yield = float(overview_data['DividendYield'].rstrip('%'))
                if 2 <= dividend_yield <= 6:
                    score += 15
                elif dividend_yield > 0:
                    score += 10
            
            # Sector scoring
            if 'Sector' in overview_data:
                stable_sectors = ['Technology', 'Healthcare', 'Consumer Defensive', 'Utilities', 'Financial Services']
                if overview_data['Sector'] in stable_sectors:
                    score += 10
            
            # Company name recognition bonus
            if 'Name' in overview_data:
                well_known = ['Apple', 'Microsoft', 'Amazon', 'Google', 'Tesla', 'Johnson & Johnson', 'Procter & Gamble']
                if any(name in overview_data['Name'] for name in well_known):
                    score += 10
                    
        except Exception as e:
            logger.error(f"Error calculating beginner score: {e}")
        
        return min(100, max(0, score))  # Ensure score is between 0-100
    
    def _calculate_beginner_score_finnhub(self, profile_data: Dict[str, Any]) -> int:
        """Calculate beginner-friendly score based on Finnhub profile data"""
        score = 60  # Base score
        
        try:
            # Market cap scoring
            if 'marketCapitalization' in profile_data and profile_data['marketCapitalization']:
                market_cap = int(profile_data['marketCapitalization'])
                if market_cap >= 100_000_000_000:  # $100B+
                    score += 20
                elif market_cap >= 10_000_000_000:  # $10B+
                    score += 15
                elif market_cap >= 1_000_000_000:  # $1B+
                    score += 10
            
            # Sector scoring
            if 'sector' in profile_data:
                stable_sectors = ['Technology', 'Healthcare', 'Consumer Defensive', 'Utilities', 'Financial Services']
                if profile_data['sector'] in stable_sectors:
                    score += 10
            
            # Company name recognition bonus
            if 'name' in profile_data:
                well_known = ['Apple', 'Microsoft', 'Amazon', 'Google', 'Tesla', 'Johnson & Johnson', 'Procter & Gamble']
                if any(name in profile_data['name'] for name in well_known):
                    score += 10
                    
        except Exception as e:
            logger.error(f"Error calculating Finnhub beginner score: {e}")
        
        return min(100, max(0, score))  # Ensure score is between 0-100
