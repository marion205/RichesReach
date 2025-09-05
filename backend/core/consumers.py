import json
import asyncio
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import Stock, Watchlist
from .services import MarketDataService
import jwt
from django.conf import settings

logger = logging.getLogger(__name__)

class StockPriceConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time stock price updates"""
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope["user"]
        self.room_group_name = f"stock_prices_{self.user.id if not isinstance(self.user, AnonymousUser) else 'anonymous'}"
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        logger.info(f"WebSocket connected for user: {self.user}")
        
        # Start sending initial stock prices
        await self.send_initial_prices()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        logger.info(f"WebSocket disconnected for user: {self.user}")
    
    async def receive(self, text_data):
        """Handle messages from WebSocket client"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'subscribe_stocks':
                # Client wants to subscribe to specific stocks
                stock_symbols = data.get('symbols', [])
                await self.subscribe_to_stocks(stock_symbols)
            elif message_type == 'get_watchlist_prices':
                # Client wants prices for their watchlist
                await self.send_watchlist_prices()
            elif message_type == 'ping':
                # Heartbeat ping
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': asyncio.get_event_loop().time()
                }))
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received from WebSocket")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
    
    async def send_initial_prices(self):
        """Send initial stock prices when client connects"""
        try:
            if isinstance(self.user, AnonymousUser):
                # Send some popular stocks for anonymous users
                popular_symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
                prices = await self.get_stock_prices(popular_symbols)
            else:
                # Send user's watchlist prices
                prices = await self.get_watchlist_prices()
            
            await self.send(text_data=json.dumps({
                'type': 'initial_prices',
                'prices': prices,
                'timestamp': asyncio.get_event_loop().time()
            }))
            
        except Exception as e:
            logger.error(f"Error sending initial prices: {e}")
    
    async def subscribe_to_stocks(self, symbols):
        """Subscribe to specific stock symbols"""
        try:
            prices = await self.get_stock_prices(symbols)
            await self.send(text_data=json.dumps({
                'type': 'stock_prices',
                'prices': prices,
                'timestamp': asyncio.get_event_loop().time()
            }))
        except Exception as e:
            logger.error(f"Error subscribing to stocks: {e}")
    
    async def send_watchlist_prices(self):
        """Send prices for user's watchlist"""
        try:
            prices = await self.get_watchlist_prices()
            await self.send(text_data=json.dumps({
                'type': 'watchlist_prices',
                'prices': prices,
                'timestamp': asyncio.get_event_loop().time()
            }))
        except Exception as e:
            logger.error(f"Error sending watchlist prices: {e}")
    
    @database_sync_to_async
    def get_watchlist_prices(self):
        """Get stock prices for user's watchlist"""
        if isinstance(self.user, AnonymousUser):
            return []
        
        try:
            watchlist_items = Watchlist.objects.filter(user=self.user).select_related('stock')
            symbols = [item.stock.symbol for item in watchlist_items]
            return self.get_stock_prices_sync(symbols)
        except Exception as e:
            logger.error(f"Error getting watchlist prices: {e}")
            return []
    
    def get_stock_prices_sync(self, symbols):
        """Synchronous method to get stock prices"""
        try:
            market_service = MarketDataService()
            prices = []
            
            for symbol in symbols:
                try:
                    # Get current price from Alpha Vantage
                    price_data = market_service.get_stock_quote(symbol)
                    if price_data:
                        prices.append({
                            'symbol': symbol,
                            'price': price_data.get('price', 0),
                            'change': price_data.get('change', 0),
                            'change_percent': price_data.get('change_percent', 0),
                            'volume': price_data.get('volume', 0),
                            'timestamp': asyncio.get_event_loop().time()
                        })
                except Exception as e:
                    logger.error(f"Error getting price for {symbol}: {e}")
                    # Fallback to database price
                    try:
                        stock = Stock.objects.get(symbol=symbol)
                        prices.append({
                            'symbol': symbol,
                            'price': stock.current_price,
                            'change': 0,
                            'change_percent': 0,
                            'volume': 0,
                            'timestamp': asyncio.get_event_loop().time()
                        })
                    except Stock.DoesNotExist:
                        continue
            
            return prices
            
        except Exception as e:
            logger.error(f"Error in get_stock_prices_sync: {e}")
            return []
    
    async def get_stock_prices(self, symbols):
        """Async wrapper for getting stock prices"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_stock_prices_sync, symbols)
    
    async def stock_price_update(self, event):
        """Handle stock price update from group"""
        await self.send(text_data=json.dumps({
            'type': 'price_update',
            'symbol': event['symbol'],
            'price': event['price'],
            'change': event['change'],
            'change_percent': event['change_percent'],
            'volume': event['volume'],
            'timestamp': event['timestamp']
        }))
    
    async def price_alert(self, event):
        """Handle price alert from group"""
        await self.send(text_data=json.dumps({
            'type': 'price_alert',
            'symbol': event['symbol'],
            'price': event['price'],
            'alert_type': event['alert_type'],
            'message': event['message'],
            'timestamp': event['timestamp']
        }))


class DiscussionConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time discussion updates"""
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope["user"]
        self.room_group_name = "discussions"
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        logger.info(f"Discussion WebSocket connected for user: {self.user}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        logger.info(f"Discussion WebSocket disconnected for user: {self.user}")
    
    async def receive(self, text_data):
        """Handle messages from WebSocket client"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                # Heartbeat ping
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': asyncio.get_event_loop().time()
                }))
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received from Discussion WebSocket")
        except Exception as e:
            logger.error(f"Error processing Discussion WebSocket message: {e}")
    
    async def new_discussion(self, event):
        """Handle new discussion post"""
        await self.send(text_data=json.dumps({
            'type': 'new_discussion',
            'discussion': event['discussion'],
            'timestamp': event['timestamp']
        }))
    
    async def new_comment(self, event):
        """Handle new comment on discussion"""
        await self.send(text_data=json.dumps({
            'type': 'new_comment',
            'comment': event['comment'],
            'discussion_id': event['discussion_id'],
            'timestamp': event['timestamp']
        }))
    
    async def discussion_update(self, event):
        """Handle discussion update (votes, etc.)"""
        await self.send(text_data=json.dumps({
            'type': 'discussion_update',
            'discussion_id': event['discussion_id'],
            'updates': event['updates'],
            'timestamp': event['timestamp']
        }))
