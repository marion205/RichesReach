"""
Real Data Service - Production implementation with real API calls
"""

import asyncio
import httpx
import os
from typing import Dict, Any, Optional
from datetime import datetime

class RealDataService:
    """Real data service using actual market data APIs"""
    
    def __init__(self):
        self.polygon_api_key = os.getenv('POLYGON_API_KEY')
        self.finnhub_api_key = os.getenv('FINNHUB_API_KEY')
        self.alpha_vantage_api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    
    async def get_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get real stock data from market data providers"""
        try:
            # Try Polygon first
            if self.polygon_api_key:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev",
                        params={"apikey": self.polygon_api_key}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('results'):
                            result = data['results'][0]
                            return {
                                "name": symbol,
                                "price": result.get('c', 0),
                                "change": result.get('c', 0) - result.get('o', 0),
                                "change_percent": ((result.get('c', 0) - result.get('o', 0)) / result.get('o', 1)) * 100,
                                "volume": result.get('v', 0),
                                "market_cap": 0,  # Would need additional API call
                                "pe_ratio": 0  # Would need additional API call
                            }
        except Exception as e:
            print(f"Error fetching stock data from Polygon: {e}")
        
        # Fallback to Finnhub
        try:
            if self.finnhub_api_key:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"https://finnhub.io/api/v1/quote",
                        params={"symbol": symbol, "token": self.finnhub_api_key}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return {
                            "name": symbol,
                            "price": data.get('c', 0),
                            "change": data.get('d', 0),
                            "change_percent": data.get('dp', 0),
                            "volume": 0,  # Not available in quote endpoint
                            "market_cap": 0,
                            "pe_ratio": 0
                        }
        except Exception as e:
            print(f"Error fetching stock data from Finnhub: {e}")
        
        return None
    
    async def get_options_chain(self, symbol: str) -> Dict[str, Any]:
        """Get real options chain data from market data providers"""
        try:
            # Try Polygon for options data
            if self.polygon_api_key:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"https://api.polygon.io/v3/reference/options/contracts",
                        params={"underlying_ticker": symbol, "apikey": self.polygon_api_key}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        # Process real options data
                        calls = []
                        puts = []
                        for contract in data.get('results', [])[:10]:  # Limit to 10 contracts
                            if contract.get('contract_type') == 'call':
                                calls.append({
                                    "strike": contract.get('strike_price', 0),
                                    "bid": 0,  # Would need additional API call for quotes
                                    "ask": 0,
                                    "volume": 0
                                })
                            else:
                                puts.append({
                                    "strike": contract.get('strike_price', 0),
                                    "bid": 0,
                                    "ask": 0,
                                    "volume": 0
                                })
                        return {"calls": calls, "puts": puts}
        except Exception as e:
            print(f"Error fetching options data: {e}")
        
        return {"calls": [], "puts": []}

# Global instance
_real_data_service = None

def get_real_data_service() -> RealDataService:
    """Get the global real data service instance"""
    global _real_data_service
    if _real_data_service is None:
        _real_data_service = RealDataService()
    return _real_data_service
