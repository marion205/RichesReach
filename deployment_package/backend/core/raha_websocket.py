"""
RAHA WebSocket Service
Broadcasts real-time RAHA signals and price updates to connected clients
"""
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
from django.utils import timezone

logger = logging.getLogger(__name__)

# Global socket.io instance (will be set by main_server.py)
_sio = None

def set_socketio_instance(sio_instance):
    """Set the global socket.io instance"""
    global _sio
    _sio = sio_instance
    logger.info("✅ RAHA WebSocket service initialized")

def broadcast_raha_signal(signal_data: Dict[str, Any], user_id: Optional[str] = None):
    """
    Broadcast a RAHA signal to connected clients.
    
    Args:
        signal_data: Signal data dictionary
        user_id: Optional user ID to send only to specific user
    """
    if not _sio:
        logger.warning("⚠️  Socket.io not initialized - cannot broadcast signal")
        return
    
    try:
        event_data = {
            'type': 'raha_signal',
            'timestamp': timezone.now().isoformat(),
            'signal': signal_data,
        }
        
        if user_id:
            # Send to specific user room
            room = f"user_{user_id}"
            _sio.emit('raha_signal', event_data, room=room)
            logger.info(f"📡 Broadcasted RAHA signal to user {user_id}")
        else:
            # Broadcast to all connected clients
            _sio.emit('raha_signal', event_data)
            logger.info("📡 Broadcasted RAHA signal to all clients")
            
    except Exception as e:
        logger.error(f"❌ Error broadcasting RAHA signal: {e}", exc_info=True)

def broadcast_price_update(symbol: str, price_data: Dict[str, Any]):
    """
    Broadcast a price update for a symbol.
    
    Args:
        symbol: Stock symbol
        price_data: Price data dictionary (price, change, changePercent, etc.)
    """
    if not _sio:
        logger.warning("⚠️  Socket.io not initialized - cannot broadcast price update")
        return
    
    try:
        event_data = {
            'type': 'price_update',
            'timestamp': timezone.now().isoformat(),
            'symbol': symbol,
            'price': price_data,
        }
        
        # Broadcast to all clients subscribed to this symbol
        room = f"symbol_{symbol}"
        _sio.emit('price_update', event_data, room=room)
        
        # Also broadcast to all clients (for The Whisper screen)
        _sio.emit('price_update', event_data)
        logger.debug(f"📡 Broadcasted price update for {symbol}")
            
    except Exception as e:
        logger.error(f"❌ Error broadcasting price update: {e}", exc_info=True)

def broadcast_backtest_complete(backtest_id: str, user_id: str, backtest_data: Dict[str, Any]):
    """
    Broadcast backtest completion notification.
    
    Args:
        backtest_id: Backtest run ID
        user_id: User who ran the backtest
        backtest_data: Backtest results data
    """
    if not _sio:
        logger.warning("⚠️  Socket.io not initialized - cannot broadcast backtest")
        return
    
    try:
        event_data = {
            'type': 'backtest_complete',
            'timestamp': timezone.now().isoformat(),
            'backtest_id': backtest_id,
            'backtest': backtest_data,
        }
        
        # Send to specific user
        room = f"user_{user_id}"
        _sio.emit('backtest_complete', event_data, room=room)
        logger.info(f"📡 Broadcasted backtest completion to user {user_id}")
            
    except Exception as e:
        logger.error(f"❌ Error broadcasting backtest: {e}", exc_info=True)

def register_websocket_handlers(sio):
    """
    Register WebSocket event handlers for RAHA.
    Called from main_server.py during socket.io setup.
    
    Args:
        sio: Socket.io server instance
    """
    global _sio
    _sio = sio
    
    @sio.event
    async def connect(sid, environ, auth):
        """Handle client connection"""
        try:
            # Extract user info from auth if available
            user_id = None
            if auth and isinstance(auth, dict):
                user_id = auth.get('user_id')
            
            if user_id:
                # Join user-specific room
                await sio.enter_room(sid, f"user_{user_id}")
                logger.info(f"✅ Client {sid} connected (user: {user_id})")
            else:
                logger.info(f"✅ Client {sid} connected (anonymous)")
            
            # Send welcome message
            await sio.emit('connected', {
                'message': 'Connected to RAHA WebSocket',
                'timestamp': timezone.now().isoformat(),
            }, room=sid)
            
        except Exception as e:
            logger.error(f"❌ Error in connect handler: {e}", exc_info=True)
    
    @sio.event
    async def disconnect(sid):
        """Handle client disconnection"""
        try:
            logger.info(f"👋 Client {sid} disconnected")
        except Exception as e:
            logger.error(f"❌ Error in disconnect handler: {e}", exc_info=True)
    
    @sio.event
    async def subscribe_symbol(sid, data):
        """Subscribe to price updates for a symbol"""
        try:
            symbol = data.get('symbol', '').upper()
            if symbol:
                room = f"symbol_{symbol}"
                await sio.enter_room(sid, room)
                logger.info(f"📊 Client {sid} subscribed to {symbol}")
                await sio.emit('subscribed', {
                    'symbol': symbol,
                    'message': f'Subscribed to {symbol}',
                }, room=sid)
        except Exception as e:
            logger.error(f"❌ Error in subscribe_symbol: {e}", exc_info=True)
    
    @sio.event
    async def unsubscribe_symbol(sid, data):
        """Unsubscribe from price updates for a symbol"""
        try:
            symbol = data.get('symbol', '').upper()
            if symbol:
                room = f"symbol_{symbol}"
                await sio.leave_room(sid, room)
                logger.info(f"📊 Client {sid} unsubscribed from {symbol}")
        except Exception as e:
            logger.error(f"❌ Error in unsubscribe_symbol: {e}", exc_info=True)
    
    logger.info("✅ RAHA WebSocket handlers registered")

