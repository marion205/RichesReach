"""
Real Data Service - Mock implementation for testing
"""

import asyncio
import random
from typing import Dict, Any, Optional
from datetime import datetime

class RealDataService:
    """Mock real data service for testing purposes"""
    
    def __init__(self):
        self.mock_data = {
            "AAPL": {
                "name": "Apple Inc.",
                "price": 175.50,
                "change": 2.30,
                "change_percent": 1.33,
                "volume": 45000000,
                "market_cap": 2800000000000,
                "pe_ratio": 28.5
            },
            "GOOGL": {
                "name": "Alphabet Inc.",
                "price": 142.80,
                "change": -1.20,
                "change_percent": -0.83,
                "volume": 25000000,
                "market_cap": 1800000000000,
                "pe_ratio": 25.2
            },
            "MSFT": {
                "name": "Microsoft Corporation",
                "price": 378.90,
                "change": 5.40,
                "change_percent": 1.45,
                "volume": 30000000,
                "market_cap": 2800000000000,
                "pe_ratio": 32.1
            }
        }
    
    async def get_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get mock stock data for testing"""
        await asyncio.sleep(0.1)  # Simulate network delay
        return self.mock_data.get(symbol.upper())
    
    async def get_options_chain(self, symbol: str) -> Dict[str, Any]:
        """Get mock options chain data"""
        await asyncio.sleep(0.1)
        return {
            "calls": [
                {"strike": 175, "bid": 2.50, "ask": 2.60, "volume": 1000},
                {"strike": 180, "bid": 1.20, "ask": 1.30, "volume": 800}
            ],
            "puts": [
                {"strike": 170, "bid": 1.80, "ask": 1.90, "volume": 1200},
                {"strike": 165, "bid": 0.90, "ask": 1.00, "volume": 600}
            ]
        }

# Global instance
_real_data_service = None

def get_real_data_service() -> RealDataService:
    """Get the global real data service instance"""
    global _real_data_service
    if _real_data_service is None:
        _real_data_service = RealDataService()
    return _real_data_service
