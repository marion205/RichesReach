"""
Market Regime Oracle - Price Feed Integration
Automatically ingests price data into the Rust correlation engine
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from decimal import Decimal
from django.utils import timezone
from .rust_stock_service import rust_stock_service

logger = logging.getLogger(__name__)


class RegimePriceFeed:
    """
    Bridge service that feeds price data to the Rust correlation engine.
    Hooks into existing price feed services to automatically ingest prices.
    """
    
    def __init__(self):
        self.rust_service = rust_stock_service
        self.enabled = True  # Can be toggled via feature flag
    
    def ingest_stock_price(
        self,
        symbol: str,
        price: float,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Ingest a stock price into the correlation engine.
        Synchronous version for use in existing code paths.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            price: Current price
            timestamp: Price timestamp (defaults to now)
        
        Returns:
            True if ingested successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            timestamp = timestamp or timezone.now()
            
            # Call Rust service to ingest price (synchronous)
            response = self.rust_service.ingest_price(
                symbol.upper(),
                float(price),
                timestamp.isoformat()
            )
            
            if response and response.get('success'):
                logger.debug(f"Ingested price for {symbol}: ${price:.2f}")
                return True
            else:
                logger.debug(f"Failed to ingest price for {symbol} (non-blocking)")
                return False
                
        except Exception as e:
            logger.debug(f"Error ingesting price for {symbol}: {e} (non-blocking)")
            return False
    
    def ingest_crypto_price(
        self,
        symbol: str,
        price: float,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Ingest a crypto price into the correlation engine.
        """
        return self.ingest_stock_price(symbol, price, timestamp)


# Global instance
regime_price_feed = RegimePriceFeed()

