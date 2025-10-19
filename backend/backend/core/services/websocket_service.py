"""
WebSocket Service for Real-time Notifications
Handles live updates for trading, KYC, and account activities
"""
import json
import logging
import asyncio
from typing import Dict, List, Set, Any, Optional
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
import redis

User = get_user_model()
logger = logging.getLogger(__name__)

class WebSocketService:
    """Service for managing WebSocket connections and real-time notifications"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=getattr(settings, 'REDIS_HOST', 'localhost'),
            port=getattr(settings, 'REDIS_PORT', 6379),
            db=getattr(settings, 'REDIS_DB', 0),
            decode_responses=True
        )
        self.connection_groups = {}  # user_id -> set of channel_names
        self.user_connections = {}   # channel_name -> user_id
    
    async def connect_user(self, user_id: str, channel_name: str):
        """Connect a user to WebSocket service"""
        try:
            if user_id not in self.connection_groups:
                self.connection_groups[user_id] = set()
            
            self.connection_groups[user_id].add(channel_name)
            self.user_connections[channel_name] = user_id
            
            # Subscribe to user-specific channels
            await self._subscribe_to_user_channels(user_id, channel_name)
            
            logger.info(f"User {user_id} connected via {channel_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect user {user_id}: {e}")
            return False
    
    async def disconnect_user(self, channel_name: str):
        """Disconnect a user from WebSocket service"""
        try:
            if channel_name in self.user_connections:
                user_id = self.user_connections[channel_name]
                
                if user_id in self.connection_groups:
                    self.connection_groups[user_id].discard(channel_name)
                    if not self.connection_groups[user_id]:
                        del self.connection_groups[user_id]
                
                del self.user_connections[channel_name]
                
                logger.info(f"User {user_id} disconnected from {channel_name}")
                return True
            
        except Exception as e:
            logger.error(f"Failed to disconnect user from {channel_name}: {e}")
            return False
    
    async def send_to_user(self, user_id: str, message_type: str, data: Dict[str, Any]):
        """Send message to all connections of a specific user"""
        try:
            if user_id not in self.connection_groups:
                logger.warning(f"No active connections for user {user_id}")
                return False
            
            message = {
                'type': message_type,
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id
            }
            
            # Send to all user's connections
            for channel_name in self.connection_groups[user_id]:
                await self._send_to_channel(channel_name, message)
            
            logger.info(f"Sent {message_type} to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message to user {user_id}: {e}")
            return False
    
    async def send_to_all(self, message_type: str, data: Dict[str, Any]):
        """Send message to all connected users"""
        try:
            message = {
                'type': message_type,
                'data': data,
                'timestamp': datetime.now().isoformat()
            }
            
            # Send to all active connections
            for user_id, connections in self.connection_groups.items():
                for channel_name in connections:
                    await self._send_to_channel(channel_name, message)
            
            logger.info(f"Sent {message_type} to all users")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message to all users: {e}")
            return False
    
    async def _send_to_channel(self, channel_name: str, message: Dict[str, Any]):
        """Send message to a specific channel"""
        try:
            # This would integrate with Django Channels
            # For now, we'll use Redis pub/sub as a fallback
            await sync_to_async(self.redis_client.publish)(
                f"websocket_{channel_name}",
                json.dumps(message)
            )
        except Exception as e:
            logger.error(f"Failed to send message to channel {channel_name}: {e}")
    
    async def _subscribe_to_user_channels(self, user_id: str, channel_name: str):
        """Subscribe to user-specific notification channels"""
        try:
            # Subscribe to various user-specific channels
            channels = [
                f"user_{user_id}_trading",
                f"user_{user_id}_kyc",
                f"user_{user_id}_account",
                f"user_{user_id}_notifications"
            ]
            
            for channel in channels:
                await sync_to_async(self.redis_client.sadd)(
                    f"channel_{channel_name}_subscriptions",
                    channel
                )
            
        except Exception as e:
            logger.error(f"Failed to subscribe user {user_id} to channels: {e}")
    
    # =============================================================================
    # NOTIFICATION METHODS
    # =============================================================================
    
    async def notify_order_update(self, user_id: str, order_data: Dict[str, Any]):
        """Send order update notification"""
        await self.send_to_user(user_id, 'order_update', {
            'order_id': order_data.get('id'),
            'symbol': order_data.get('symbol'),
            'side': order_data.get('side'),
            'status': order_data.get('status'),
            'filled_qty': order_data.get('filled_qty'),
            'filled_price': order_data.get('filled_avg_price'),
            'message': f"Order {order_data.get('status', 'updated')} for {order_data.get('symbol', 'Unknown')}"
        })
    
    async def notify_kyc_update(self, user_id: str, kyc_data: Dict[str, Any]):
        """Send KYC status update notification"""
        await self.send_to_user(user_id, 'kyc_update', {
            'workflow_type': kyc_data.get('workflow_type'),
            'step': kyc_data.get('step'),
            'status': kyc_data.get('status'),
            'message': f"KYC {kyc_data.get('status', 'updated')} - Step {kyc_data.get('step', 'Unknown')}"
        })
    
    async def notify_account_update(self, user_id: str, account_data: Dict[str, Any]):
        """Send account update notification"""
        await self.send_to_user(user_id, 'account_update', {
            'account_type': account_data.get('account_type'),
            'status': account_data.get('status'),
            'buying_power': account_data.get('buying_power'),
            'portfolio_value': account_data.get('portfolio_value'),
            'message': f"Account {account_data.get('status', 'updated')}"
        })
    
    async def notify_market_update(self, symbol: str, price_data: Dict[str, Any]):
        """Send market data update to all users watching this symbol"""
        await self.send_to_all('market_update', {
            'symbol': symbol,
            'price': price_data.get('price'),
            'change': price_data.get('change'),
            'change_percent': price_data.get('change_percent'),
            'volume': price_data.get('volume'),
            'timestamp': price_data.get('timestamp')
        })
    
    async def notify_ai_recommendation(self, user_id: str, recommendation_data: Dict[str, Any]):
        """Send AI recommendation notification"""
        await self.send_to_user(user_id, 'ai_recommendation', {
            'symbol': recommendation_data.get('symbol'),
            'recommendation': recommendation_data.get('recommendation'),
            'confidence': recommendation_data.get('confidence'),
            'reasoning': recommendation_data.get('reasoning'),
            'message': f"New AI recommendation for {recommendation_data.get('symbol', 'Unknown')}"
        })
    
    async def notify_system_alert(self, user_id: str, alert_data: Dict[str, Any]):
        """Send system alert notification"""
        await self.send_to_user(user_id, 'system_alert', {
            'alert_type': alert_data.get('alert_type'),
            'severity': alert_data.get('severity'),
            'title': alert_data.get('title'),
            'message': alert_data.get('message'),
            'action_required': alert_data.get('action_required', False)
        })


class TradingWebSocketConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for trading-related real-time updates"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.websocket_service = WebSocketService()
        self.user_id = None
        self.channel_name = None
    
    async def connect(self):
        """Handle WebSocket connection"""
        try:
            # Get user from scope (assuming authentication middleware)
            user = self.scope.get('user')
            if not user or user.is_anonymous:
                await self.close()
                return
            
            self.user_id = str(user.id)
            self.channel_name = self.channel_name
            
            # Accept connection
            await self.accept()
            
            # Connect to WebSocket service
            await self.websocket_service.connect_user(self.user_id, self.channel_name)
            
            # Send welcome message
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'data': {
                    'user_id': self.user_id,
                    'timestamp': datetime.now().isoformat(),
                    'message': 'Connected to real-time trading updates'
                }
            }))
            
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            await self.close()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        try:
            if self.channel_name:
                await self.websocket_service.disconnect_user(self.channel_name)
        except Exception as e:
            logger.error(f"WebSocket disconnection failed: {e}")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                }))
            elif message_type == 'subscribe':
                # Handle subscription requests
                await self._handle_subscription(data.get('data', {}))
            elif message_type == 'unsubscribe':
                # Handle unsubscription requests
                await self._handle_unsubscription(data.get('data', {}))
            
        except Exception as e:
            logger.error(f"WebSocket message handling failed: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'data': {'message': 'Invalid message format'}
            }))
    
    async def _handle_subscription(self, data: Dict[str, Any]):
        """Handle subscription to specific data streams"""
        try:
            stream_type = data.get('stream_type')
            
            if stream_type == 'market_data':
                symbols = data.get('symbols', [])
                # Subscribe to market data for specific symbols
                await self._subscribe_to_market_data(symbols)
            elif stream_type == 'orders':
                # Subscribe to order updates
                await self._subscribe_to_orders()
            elif stream_type == 'account':
                # Subscribe to account updates
                await self._subscribe_to_account()
            
            await self.send(text_data=json.dumps({
                'type': 'subscription_confirmed',
                'data': {
                    'stream_type': stream_type,
                    'timestamp': datetime.now().isoformat()
                }
            }))
            
        except Exception as e:
            logger.error(f"Subscription handling failed: {e}")
    
    async def _handle_unsubscription(self, data: Dict[str, Any]):
        """Handle unsubscription from data streams"""
        try:
            stream_type = data.get('stream_type')
            # Handle unsubscription logic here
            
            await self.send(text_data=json.dumps({
                'type': 'unsubscription_confirmed',
                'data': {
                    'stream_type': stream_type,
                    'timestamp': datetime.now().isoformat()
                }
            }))
            
        except Exception as e:
            logger.error(f"Unsubscription handling failed: {e}")
    
    async def _subscribe_to_market_data(self, symbols: List[str]):
        """Subscribe to market data for specific symbols"""
        # Implementation would depend on your market data provider
        pass
    
    async def _subscribe_to_orders(self):
        """Subscribe to order updates"""
        # Implementation would monitor order status changes
        pass
    
    async def _subscribe_to_account(self):
        """Subscribe to account updates"""
        # Implementation would monitor account changes
        pass


class KYCWebSocketConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for KYC workflow updates"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.websocket_service = WebSocketService()
        self.user_id = None
        self.channel_name = None
    
    async def connect(self):
        """Handle WebSocket connection for KYC updates"""
        try:
            user = self.scope.get('user')
            if not user or user.is_anonymous:
                await self.close()
                return
            
            self.user_id = str(user.id)
            self.channel_name = self.channel_name
            
            await self.accept()
            await self.websocket_service.connect_user(self.user_id, self.channel_name)
            
            await self.send(text_data=json.dumps({
                'type': 'kyc_connection_established',
                'data': {
                    'user_id': self.user_id,
                    'timestamp': datetime.now().isoformat(),
                    'message': 'Connected to KYC workflow updates'
                }
            }))
            
        except Exception as e:
            logger.error(f"KYC WebSocket connection failed: {e}")
            await self.close()
    
    async def disconnect(self, close_code):
        """Handle KYC WebSocket disconnection"""
        try:
            if self.channel_name:
                await self.websocket_service.disconnect_user(self.channel_name)
        except Exception as e:
            logger.error(f"KYC WebSocket disconnection failed: {e}")


# Global WebSocket service instance
websocket_service = WebSocketService()
