# core/rust_stock_service.py
import requests
import json
from typing import Dict, Any, Optional
from django.conf import settings
import logging
logger = logging.getLogger(__name__)
class RustStockService:
"""
Service to communicate with the Rust Stock Analysis Engine
"""
def __init__(self):
self.base_url = "http://localhost:3001"
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
logger.error(f"Failed to communicate with Rust service: {e}")
raise Exception(f"Rust service communication failed: {str(e)}")
except json.JSONDecodeError as e:
logger.error(f"Failed to parse JSON response from Rust service: {e}")
raise Exception(f"Invalid JSON response from Rust service: {str(e)}")
def analyze_stock(self, symbol: str, include_technical: bool = True, include_fundamental: bool = True) -> Dict[str, Any]:
"""
Analyze a stock using the Rust engine
"""
data = {
"symbol": symbol.upper(),
"include_technical": include_technical,
"include_fundamental": include_fundamental
}
return self._make_request("/analyze", method="POST", data=data)
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
return self._make_request("/health", method="GET")
def is_available(self) -> bool:
"""
Check if Rust service is available
"""
try:
health = self.health_check()
return health.get('status') == 'healthy'
except Exception:
return False
# Global instance
rust_stock_service = RustStockService()
