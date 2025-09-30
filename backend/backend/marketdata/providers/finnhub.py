# marketdata/providers/finnhub.py
import httpx
import os
import time
from typing import Dict, Any, List
from .base import BaseProvider

class FinnhubProvider(BaseProvider):
    """Finnhub provider for market data and fundamentals"""
    
    @property
    def name(self) -> str:
        return "finnhub"
    
    @property
    def base_url(self) -> str:
        return "https://finnhub.io/api/v1"
    
    def __init__(self, api_key: str = None, timeout: int = 5):
        super().__init__(api_key or os.getenv("FINNHUB_API_KEY"), timeout)
        self._client = httpx.Client(timeout=self.timeout, base_url=self.base_url)
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time quote from Finnhub"""
        symbol = self._normalize_symbol(symbol)
        
        try:
            response = self._client.get(
                "/quote",
                params={"symbol": symbol, "token": self.api_key}
            )
            response.raise_for_status()
            data = response.json()
            
            # Check for error response
            if data.get("error"):
                raise Exception(f"Finnhub error: {data['error']}")
            
            return {
                "symbol": symbol,
                "price": float(data.get("c", 0)),  # current price
                "change": float(data.get("d", 0)),  # change
                "change_percent": float(data.get("dp", 0)),  # change percent
                "high": float(data.get("h", 0)),  # high
                "low": float(data.get("l", 0)),  # low
                "open": float(data.get("o", 0)),  # open
                "previous_close": float(data.get("pc", 0)),  # previous close
                "timestamp": int(time.time() * 1000),
                "provider": self.name
            }
            
        except Exception as e:
            self._handle_error(e, "get_quote")
    
    def get_profile(self, symbol: str) -> Dict[str, Any]:
        """Get company profile from Finnhub"""
        symbol = self._normalize_symbol(symbol)
        
        try:
            response = self._client.get(
                "/stock/profile2",
                params={"symbol": symbol, "token": self.api_key}
            )
            response.raise_for_status()
            data = response.json()
            
            # Check for error response
            if data.get("error"):
                raise Exception(f"Finnhub error: {data['error']}")
            
            return {
                "symbol": symbol,
                "name": data.get("name"),
                "exchange": data.get("exchange"),
                "sector": data.get("finnhubIndustry"),
                "industry": data.get("finnhubIndustry"),
                "market_cap": data.get("marketCapitalization"),
                "country": data.get("country"),
                "currency": data.get("currency"),
                "provider": self.name
            }
            
        except Exception as e:
            self._handle_error(e, "get_profile")
    
    def get_options_chain(self, symbol: str, limit: int = 50) -> Dict[str, Any]:
        """Get options chain from Finnhub (limited support)"""
        symbol = self._normalize_symbol(symbol)
        
        try:
            # Finnhub has limited options support, so we'll return basic structure
            # In a real implementation, you might want to use a different provider for options
            response = self._client.get(
                "/stock/option-chain",
                params={"symbol": symbol, "token": self.api_key}
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("error"):
                raise Exception(f"Finnhub error: {data['error']}")
            
            # Finnhub options data is limited, so we'll return what we can
            contracts = []
            if data.get("data"):
                for item in data["data"][:limit]:
                    contracts.append({
                        "symbol": item.get("contractSymbol"),
                        "type": item.get("type", "").upper(),
                        "strike": float(item.get("strike", 0)),
                        "expiration": item.get("expirationDate"),
                        "bid": float(item.get("bid", 0)) if item.get("bid") else None,
                        "ask": float(item.get("ask", 0)) if item.get("ask") else None,
                        "last_price": float(item.get("lastPrice", 0)) if item.get("lastPrice") else None,
                        "volume": item.get("volume"),
                        "open_interest": item.get("openInterest"),
                        "implied_volatility": float(item.get("impliedVolatility", 0)) if item.get("impliedVolatility") else None
                    })
            
            return {
                "symbol": symbol,
                "contracts": contracts,
                "provider": self.name
            }
            
        except Exception as e:
            # Finnhub options support is limited, so we'll return empty chain
            # rather than failing completely
            return {
                "symbol": symbol,
                "contracts": [],
                "provider": self.name,
                "note": "Limited options support from Finnhub"
            }
    
    def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """Get fundamental data from Finnhub"""
        symbol = self._normalize_symbol(symbol)
        
        try:
            # Get basic metrics
            response = self._client.get(
                "/stock/metric",
                params={
                    "symbol": symbol,
                    "metric": "all",
                    "token": self.api_key
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("error"):
                raise Exception(f"Finnhub error: {data['error']}")
            
            metric = data.get("metric", {})
            return {
                "symbol": symbol,
                "pe_ratio": metric.get("peBasicExclExtraTTM"),
                "pb_ratio": metric.get("pbQuarterly"),
                "ps_ratio": metric.get("psTTM"),
                "dividend_yield": metric.get("dividendYieldIndicatedAnnual"),
                "market_cap": metric.get("marketCapitalization"),
                "provider": self.name
            }
            
        except Exception as e:
            self._handle_error(e, "get_fundamentals")
    
    def __del__(self):
        """Clean up HTTP client"""
        if hasattr(self, '_client') and self._client:
            self._client.close()
