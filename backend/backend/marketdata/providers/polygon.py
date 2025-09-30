# marketdata/providers/polygon.py
import httpx
import os
import time
from typing import Dict, Any, List
from .base import BaseProvider

class PolygonProvider(BaseProvider):
    """Polygon.io provider for real-time market data and options"""
    
    @property
    def name(self) -> str:
        return "polygon"
    
    @property
    def base_url(self) -> str:
        return "https://api.polygon.io"
    
    def __init__(self, api_key: str = None, timeout: int = 5):
        super().__init__(api_key or os.getenv("POLYGON_API_KEY"), timeout)
        self._client = httpx.Client(timeout=self.timeout, base_url=self.base_url)
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time quote from Polygon"""
        symbol = self._normalize_symbol(symbol)
        
        try:
            # Try last trade first (most accurate)
            response = self._client.get(
                f"/v2/last/trade/{symbol}",
                params={"apikey": self.api_key}
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "OK" and data.get("results"):
                result = data["results"]
                return {
                    "symbol": symbol,
                    "price": float(result.get("p", 0)),
                    "timestamp": result.get("t", int(time.time() * 1000)),
                    "volume": result.get("s", 0),
                    "provider": self.name
                }
            
            # Fallback to NBBO if last trade fails
            return self._get_nbbo_quote(symbol)
            
        except Exception as e:
            self._handle_error(e, "get_quote")
    
    def _get_nbbo_quote(self, symbol: str) -> Dict[str, Any]:
        """Get NBBO quote as fallback"""
        response = self._client.get(
            f"/v2/last/nbbo/{symbol}",
            params={"apikey": self.api_key}
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "OK" and data.get("results"):
            result = data["results"]
            bid = result.get("bid", {})
            ask = result.get("ask", {})
            
            # Use mid-price if available, otherwise bid or ask
            bid_price = bid.get("price", 0) if bid else 0
            ask_price = ask.get("price", 0) if ask else 0
            price = (bid_price + ask_price) / 2 if bid_price and ask_price else (bid_price or ask_price)
            
            return {
                "symbol": symbol,
                "price": float(price),
                "bid": float(bid_price) if bid_price else None,
                "ask": float(ask_price) if ask_price else None,
                "timestamp": result.get("t", int(time.time() * 1000)),
                "provider": self.name
            }
        
        raise Exception(f"No quote data available for {symbol}")
    
    def get_profile(self, symbol: str) -> Dict[str, Any]:
        """Get company profile from Polygon"""
        symbol = self._normalize_symbol(symbol)
        
        try:
            response = self._client.get(
                f"/v3/reference/tickers/{symbol}",
                params={"apikey": self.api_key}
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "OK" and data.get("results"):
                result = data["results"]
                return {
                    "symbol": symbol,
                    "name": result.get("name"),
                    "exchange": result.get("primary_exchange"),
                    "sector": result.get("sic_description"),
                    "market_cap": result.get("market_cap"),
                    "provider": self.name
                }
            
            raise Exception(f"No profile data available for {symbol}")
            
        except Exception as e:
            self._handle_error(e, "get_profile")
    
    def get_options_chain(self, symbol: str, limit: int = 50) -> Dict[str, Any]:
        """Get options chain from Polygon"""
        symbol = self._normalize_symbol(symbol)
        
        try:
            # Get options contracts
            response = self._client.get(
                "/v3/reference/options/contracts",
                params={
                    "underlying_ticker": symbol,
                    "limit": limit,
                    "apikey": self.api_key
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "OK":
                contracts = data.get("results", [])
                
                # Get quotes for each contract
                contract_data = []
                for contract in contracts[:limit]:
                    contract_symbol = contract.get("ticker")
                    if contract_symbol:
                        try:
                            quote = self._get_option_quote(contract_symbol)
                            contract_data.append({
                                "symbol": contract_symbol,
                                "type": contract.get("contract_type", "").upper(),
                                "strike": float(contract.get("strike_price", 0)),
                                "expiration": contract.get("expiration_date"),
                                "bid": quote.get("bid"),
                                "ask": quote.get("ask"),
                                "last_price": quote.get("last_price"),
                                "volume": quote.get("volume"),
                                "open_interest": quote.get("open_interest"),
                                "implied_volatility": quote.get("implied_volatility")
                            })
                        except:
                            # If quote fails, still include basic contract info
                            contract_data.append({
                                "symbol": contract_symbol,
                                "type": contract.get("contract_type", "").upper(),
                                "strike": float(contract.get("strike_price", 0)),
                                "expiration": contract.get("expiration_date")
                            })
                
                return {
                    "symbol": symbol,
                    "contracts": contract_data,
                    "provider": self.name
                }
            
            raise Exception(f"No options data available for {symbol}")
            
        except Exception as e:
            self._handle_error(e, "get_options_chain")
    
    def _get_option_quote(self, contract_symbol: str) -> Dict[str, Any]:
        """Get quote for a specific option contract"""
        try:
            response = self._client.get(
                f"/v2/last/trade/{contract_symbol}",
                params={"apikey": self.api_key}
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "OK" and data.get("results"):
                result = data["results"]
                return {
                    "last_price": float(result.get("p", 0)),
                    "volume": result.get("s", 0)
                }
        except:
            pass
        
        # Fallback to NBBO
        try:
            response = self._client.get(
                f"/v2/last/nbbo/{contract_symbol}",
                params={"apikey": self.api_key}
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "OK" and data.get("results"):
                result = data["results"]
                bid = result.get("bid", {})
                ask = result.get("ask", {})
                
                return {
                    "bid": float(bid.get("price", 0)) if bid.get("price") else None,
                    "ask": float(ask.get("price", 0)) if ask.get("price") else None
                }
        except:
            pass
        
        return {}
    
    def __del__(self):
        """Clean up HTTP client"""
        if hasattr(self, '_client') and self._client:
            self._client.close()
