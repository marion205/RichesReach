"""
IBKR Adapter - Phase 2 (Hardened)
Interactive Brokers API Integration with Auto-Reconnect

Simple adapter pattern: Order router → IBKR adapter → TWS API
"""

import logging
from typing import Optional, Dict, List, Any
from enum import Enum
import asyncio
import time

logger = logging.getLogger(__name__)


class IBKRConnectionStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class IBKROrderStatus(Enum):
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class IBKRAdapter:
    """
    Interactive Brokers adapter for futures trading.
    
    Phase 2: Handles connection, authentication, order routing
    """
    
    def __init__(self):
        self.connection_status = IBKRConnectionStatus.DISCONNECTED
        self.client_id = None
        self.tws_host = "127.0.0.1"  # TWS/Gateway host
        self.tws_port = 7497  # Paper trading port (7496 for live)
        self.client = None  # IB API client
        self.last_heartbeat = None
        self.heartbeat_interval = 30  # seconds
        self.reconnect_delay = 2  # seconds
        self.max_reconnect_attempts = 10
    
    async def connect(self, client_id: int = 1) -> bool:
        """
        Connect to TWS/Gateway with auto-retry.
        
        Args:
            client_id: Unique client ID for this connection
            
        Returns:
            True if connected successfully
        """
        attempts = 0
        initial_delay = self.reconnect_delay
        
        while attempts < self.max_reconnect_attempts:
            try:
                self.connection_status = IBKRConnectionStatus.CONNECTING
                logger.info(f"Connecting to IBKR TWS at {self.tws_host}:{self.tws_port} (attempt {attempts + 1})")
                
                # TODO: Implement actual IB API connection
                # from ib_insync import IB, util
                # self.client = IB()
                # await self.client.connectAsync(self.tws_host, self.tws_port, clientId=client_id, timeout=5)
                
                # For now, simulate connection
                await asyncio.sleep(0.1)
                
                self.connection_status = IBKRConnectionStatus.CONNECTED
                self.client_id = client_id
                self.last_heartbeat = time.time()
                self.reconnect_delay = initial_delay  # Reset on success
                logger.info("✅ Connected to IBKR TWS")
                return True
                
            except Exception as e:
                attempts += 1
                logger.warning(f"IBKR connect failed (attempt {attempts}): {e}")
                
                if attempts < self.max_reconnect_attempts:
                    await asyncio.sleep(self.reconnect_delay)
                    self.reconnect_delay = min(self.reconnect_delay * 1.5, 30)  # Exponential backoff
                else:
                    self.connection_status = IBKRConnectionStatus.ERROR
                    self.reconnect_delay = initial_delay  # Reset on final failure
                    logger.error(f"❌ Failed to connect to IBKR after {attempts} attempts")
        
        return False
    
    async def disconnect(self):
        """Disconnect from TWS/Gateway"""
        try:
            if self.client:
                # await self.client.disconnect()
                pass
            self.connection_status = IBKRConnectionStatus.DISCONNECTED
            logger.info("Disconnected from IBKR TWS")
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
    
    async def ensure_connected(self):
        """Ensure connection is active, reconnect if needed"""
        if self.connection_status != IBKRConnectionStatus.CONNECTED:
            logger.warning("IBKR not connected, attempting reconnect...")
            await self.connect(self.client_id or 1)
        
        # Heartbeat check
        if self.last_heartbeat:
            elapsed = time.time() - self.last_heartbeat
            if elapsed > self.heartbeat_interval * 2:
                logger.warning("IBKR heartbeat stale, reconnecting...")
                await self.disconnect()
                await self.connect(self.client_id or 1)
    
    async def place_order(
        self,
        symbol: str,
        side: str,
        quantity: int,
        order_type: str = "MKT",
        limit_price: Optional[float] = None,
        client_order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Place a futures order via IBKR with idempotency.
        
        Args:
            symbol: Futures symbol (e.g., "MESZ5")
            side: "BUY" or "SELL"
            quantity: Number of contracts
            order_type: "MKT" or "LMT"
            limit_price: Limit price if order_type is "LMT"
            client_order_id: Idempotent client order ID
            
        Returns:
            Order response with order_id and status
        """
        try:
            await self.ensure_connected()
            
            if self.connection_status != IBKRConnectionStatus.CONNECTED:
                raise Exception("Not connected to IBKR TWS")
            
            logger.info(f"Placing IBKR order: {side} {quantity} {symbol} (client_order_id={client_order_id})")
            
            # TODO: Implement actual IB API order placement with idempotency
            # contract = Future(symbol=symbol, exchange='CME')
            # if order_type == "MKT":
            #     order = MarketOrder(side, quantity)
            # else:
            #     order = LimitOrder(side, quantity, limit_price)
            # order.clientId = self.client_id
            # order.orderRef = client_order_id  # Use for idempotency
            
            # # Check if order already exists
            # existing = self._find_order_by_ref(client_order_id)
            # if existing:
            #     return {"order_id": existing.orderId, "status": existing.orderStatus.status, "duplicate": True}
            
            # trade = self.client.placeOrder(contract, order)
            # return {"order_id": trade.order.orderId, "status": trade.orderStatus.status}
            
            # For now, simulate order placement
            await asyncio.sleep(0.1)
            
            order_id = f"IBKR_{symbol}_{side}_{quantity}_{int(asyncio.get_event_loop().time())}"
            self.last_heartbeat = time.time()
            
            return {
                "order_id": order_id,
                "status": "submitted",
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "fill_price": None,  # Will be updated when filled
                "client_order_id": client_order_id,
            }
            
        except Exception as e:
            logger.error(f"Error placing IBKR order: {e}")
            # Attempt reconnect on error
            if "Not connected" in str(e):
                await self.connect(self.client_id or 1)
            raise
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get current futures positions from IBKR.
        
        Returns:
            List of position dictionaries
        """
        try:
            if self.connection_status != IBKRConnectionStatus.CONNECTED:
                return []
            
            # TODO: Implement actual IB API positions
            # positions = self.client.positions()
            # return [{"symbol": p.contract.symbol, "quantity": p.position, ...} for p in positions]
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting IBKR positions: {e}")
            return []
    
    async def get_market_data(self, symbol: str) -> Dict[str, float]:
        """
        Get current market data for a futures contract.
        
        Returns:
            Dictionary with bid, ask, last, volume, etc.
        """
        try:
            if self.connection_status != IBKRConnectionStatus.CONNECTED:
                return {}
            
            # TODO: Implement actual IB API market data
            # contract = Future(symbol=symbol, exchange='CME')
            # ticker = self.client.reqMktData(contract, '', False, False)
            # await asyncio.sleep(1)  # Wait for data
            # return {"bid": ticker.bid, "ask": ticker.ask, "last": ticker.last, ...}
            
            # For now, return mock data
            return {
                "bid": 5000.0,
                "ask": 5000.25,
                "last": 5000.15,
                "volume": 1000,
            }
            
        except Exception as e:
            logger.error(f"Error getting IBKR market data: {e}")
            return {}
    
    def is_connected(self) -> bool:
        """Check if connected to IBKR"""
        return self.connection_status == IBKRConnectionStatus.CONNECTED


# Global adapter instance
_ibkr_adapter: Optional[IBKRAdapter] = None


def get_ibkr_adapter() -> IBKRAdapter:
    """Get global IBKR adapter instance"""
    global _ibkr_adapter
    if _ibkr_adapter is None:
        _ibkr_adapter = IBKRAdapter()
    return _ibkr_adapter

