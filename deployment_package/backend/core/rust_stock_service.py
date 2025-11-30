# core/rust_stock_service.py
import requests
import json
import os
from typing import Dict, Any, Optional
from django.conf import settings
import logging
logger = logging.getLogger(__name__)

class RustStockService:
    """
    Service to communicate with the Rust Stock Analysis Engine
    """
    def __init__(self):
        # Get Rust service URL from environment or settings, default to localhost:3001
        self.base_url = getattr(settings, 'RUST_SERVICE_URL', None) or os.getenv('RUST_SERVICE_URL', 'http://localhost:3001')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'RichesReach-Django/1.0'
        })
    
    def _make_request(self, endpoint: str, method: str = 'GET', data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make HTTP request to Rust service
        """
        url = f"{self.base_url}{endpoint}"
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, timeout=10)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.warning(f"Rust service unavailable at {url}: {e}")
            # Return empty response instead of raising exception
            return {}
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response from Rust service: {e}")
            # Return empty response instead of raising exception
            return {}
        except Exception as e:
            logger.warning(f"Unexpected error communicating with Rust service: {e}")
            # Return empty response instead of raising exception
            return {}
    def analyze_stock(self, symbol: str, include_technical: bool = True, include_fundamental: bool = True) -> Dict[str, Any]:
        """
        Analyze a stock using the Rust engine
        """
        data = {
            "symbol": symbol.upper(),
        }
        # Rust service endpoint is /v1/analyze
        return self._make_request("/v1/analyze", method="POST", data=data)
    
    def get_recommendations(self) -> Dict[str, Any]:
        """
        Get beginner-friendly stock recommendations
        """
        return self._make_request("/recommendations", method="GET")
    
    def calculate_indicators(self, symbol: str) -> Dict[str, Any]:
        """
        Calculate technical indicators for a stock
        """
        data = {
            "symbol": symbol.upper()
        }
        return self._make_request("/indicators", method="POST", data=data)
    def health_check(self) -> Dict[str, Any]:
        """
        Check if Rust service is healthy
        """
        # Try /health/live endpoint first, fallback to /health
        try:
            return self._make_request("/health/live", method="GET")
        except:
            return self._make_request("/health", method="GET")
    
    def is_available(self) -> bool:
        """
        Check if Rust service is available
        """
        try:
            health = self.health_check()
            return health.get('status') == 'healthy' or health.get('status') == 'live'
        except Exception:
            return False
    
    def analyze_options(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze options for a stock symbol using the Rust engine
        """
        data = {
            "symbol": symbol.upper(),
        }
        return self._make_request("/v1/options/analyze", method="POST", data=data)
    
    def analyze_forex(self, pair: str) -> Dict[str, Any]:
        """
        Analyze a forex pair using the Rust engine
        """
        data = {
            "pair": pair.upper(),
        }
        return self._make_request("/v1/forex/analyze", method="POST", data=data)
    
    def analyze_sentiment(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze sentiment for a symbol using the Rust engine
        """
        data = {
            "symbol": symbol.upper(),
        }
        return self._make_request("/v1/sentiment/analyze", method="POST", data=data)
    
    def analyze_correlation(self, primary: str, secondary: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze correlation between two symbols using the Rust engine
        """
        data = {
            "primary": primary.upper(),
        }
        if secondary:
            data["secondary"] = secondary.upper()
        return self._make_request("/v1/correlation/analyze", method="POST", data=data)
    
    def predict_edge(self, symbol: str) -> Dict[str, Any]:
        """
        Predict edge (mispricing) for options chain using the Rust ML engine
        """
        data = {
            "symbol": symbol.upper(),
        }
        return self._make_request("/v1/options/edge-predict", method="POST", data=data)
    
    def get_one_tap_trades(
        self,
        symbol: str,
        account_size: float = 10000.0,
        risk_tolerance: float = 0.1
    ) -> Dict[str, Any]:
        """
        Get one-tap trade recommendations (ML-optimized strategies with brackets)
        """
        data = {
            "symbol": symbol.upper(),
            "account_size": account_size,
            "risk_tolerance": risk_tolerance,
        }
        return self._make_request("/v1/options/one-tap-trades", method="POST", data=data)
    
    def forecast_iv_surface(self, symbol: str) -> Dict[str, Any]:
        """
        Forecast IV surface 1-24 hours forward using sentiment and macro signals
        """
        data = {
            "symbol": symbol.upper(),
        }
        return self._make_request("/v1/options/iv-forecast", method="POST", data=data)

# Global instance
rust_stock_service = RustStockService()
