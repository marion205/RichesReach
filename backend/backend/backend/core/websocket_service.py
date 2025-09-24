import asyncio
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Stock, Watchlist
from .market_data_service import MarketDataService
import time

logger = logging.getLogger(__name__)

class WebSocketService:
    """Service for managing WebSocket communications"""
    
    def __init__(self):
        try:
            self.channel_layer = get_channel_layer()
        except Exception as e:
            logger.warning(f"Could not initialize channel layer: {e}")
            self.channel_layer = None
        self.market_service = MarketDataService()
    
    def broadcast_stock_price_update(self, symbol, price_data):
        """Broadcast stock price update to all connected clients"""
        if not self.channel_layer:
            logger.warning("Channel layer not available, skipping broadcast")
            return
            
        try:
            # Send to all users who might be watching this stock
            async_to_sync(self.channel_layer.group_send)(
                "stock_prices_all",
                {
                    'type': 'stock_price_update',
                    'symbol': symbol,
                    'price': price_data.get('price', 0),
                    'change': price_data.get('change', 0),
                    'change_percent': price_data.get('change_percent', 0),
                    'volume': price_data.get('volume', 0),
                    'timestamp': time.time()
                }
            )
            
            # Send to specific user groups who have this stock in their watchlist
            watchlist_users = Watchlist.objects.filter(
                stock__symbol=symbol
            ).values_list('user_id', flat=True)
            
            for user_id in watchlist_users:
                async_to_sync(self.channel_layer.group_send)(
                    f"stock_prices_{user_id}",
                    {
                        'type': 'stock_price_update',
                        'symbol': symbol,
                        'price': price_data.get('price', 0),
                        'change': price_data.get('change', 0),
                        'change_percent': price_data.get('change_percent', 0),
                        'volume': price_data.get('volume', 0),
                        'timestamp': time.time()
                    }
                )
                
        except Exception as e:
            logger.error(f"Error broadcasting stock price update: {e}")
    
    def broadcast_price_alert(self, user_id, symbol, price, alert_type, message):
        """Broadcast price alert to specific user"""
        try:
            async_to_sync(self.channel_layer.group_send)(
                f"stock_prices_{user_id}",
                {
                    'type': 'price_alert',
                    'symbol': symbol,
                    'price': price,
                    'alert_type': alert_type,
                    'message': message,
                    'timestamp': time.time()
                }
            )
        except Exception as e:
            logger.error(f"Error broadcasting price alert: {e}")
    
    def broadcast_new_discussion(self, discussion_data):
        """Broadcast new discussion to all connected clients"""
        if not self.channel_layer:
            logger.warning("Channel layer not available, skipping broadcast")
            return
            
        try:
            async_to_sync(self.channel_layer.group_send)(
                "discussions",
                {
                    'type': 'new_discussion',
                    'discussion': discussion_data,
                    'timestamp': time.time()
                }
            )
        except Exception as e:
            logger.error(f"Error broadcasting new discussion: {e}")
    
    def broadcast_new_comment(self, comment_data, discussion_id):
        """Broadcast new comment to all connected clients"""
        if not self.channel_layer:
            logger.warning("Channel layer not available, skipping broadcast")
            return
            
        try:
            async_to_sync(self.channel_layer.group_send)(
                "discussions",
                {
                    'type': 'new_comment',
                    'comment': comment_data,
                    'discussion_id': discussion_id,
                    'timestamp': time.time()
                }
            )
        except Exception as e:
            logger.error(f"Error broadcasting new comment: {e}")
    
    def broadcast_discussion_update(self, discussion_id, updates):
        """Broadcast discussion update (votes, etc.) to all connected clients"""
        try:
            async_to_sync(self.channel_layer.group_send)(
                "discussions",
                {
                    'type': 'discussion_update',
                    'discussion_id': discussion_id,
                    'updates': updates,
                    'timestamp': time.time()
                }
            )
        except Exception as e:
            logger.error(f"Error broadcasting discussion update: {e}")


class StockPriceUpdater:
    """Background service for updating stock prices and broadcasting via WebSocket"""
    
    def __init__(self):
        self.websocket_service = WebSocketService()
        self.market_service = MarketDataService()
        self.running = False
    
    def start(self):
        """Start the stock price updater service"""
        self.running = True
        logger.info("Starting stock price updater service")
        
        # Run in background
        import threading
        thread = threading.Thread(target=self._update_loop, daemon=True)
        thread.start()
    
    def stop(self):
        """Stop the stock price updater service"""
        self.running = False
        logger.info("Stopping stock price updater service")
    
    def _update_loop(self):
        """Main update loop for stock prices"""
        while self.running:
            try:
                # Get all stocks that users are watching
                watched_stocks = Stock.objects.filter(
                    watchlist__isnull=False
                ).distinct()
                
                for stock in watched_stocks:
                    try:
                        # Get latest price from API
                        price_data = self.market_service.get_stock_quote(stock.symbol)
                        
                        if price_data:
                            # Update database
                            stock.current_price = price_data.get('price', stock.current_price)
                            stock.save(update_fields=['current_price'])
                            
                            # Broadcast update via WebSocket
                            self.websocket_service.broadcast_stock_price_update(
                                stock.symbol, price_data
                            )
                            
                            logger.info(f"Updated price for {stock.symbol}: ${price_data.get('price', 0)}")
                        
                    except Exception as e:
                        logger.error(f"Error updating price for {stock.symbol}: {e}")
                
                # Wait before next update (5 minutes)
                time.sleep(300)
                
            except Exception as e:
                logger.error(f"Error in stock price update loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying


# Global instance
websocket_service = WebSocketService()
stock_price_updater = StockPriceUpdater()
