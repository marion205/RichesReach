import threading

import logging

import time



from asgiref.sync import async_to_sync

from channels.layers import get_channel_layer



from .models import Stock, Watchlist

from .market_data_service import MarketDataService



logger = logging.getLogger(__name__)





class WebSocketService:

    """Service for managing WebSocket communications."""



    def __init__(self):

        try:

            self.channel_layer = get_channel_layer()

        except Exception as e:

            logger.warning(f"Could not initialize channel layer: {e}")

            self.channel_layer = None



        self.market_service = MarketDataService()



    def _ensure_channel_layer(self) -> bool:

        if not self.channel_layer:

            logger.warning("Channel layer not available, skipping WebSocket broadcast")

            return False

        return True



    def broadcast_stock_price_update(self, symbol, price_data: dict):

        """Broadcast stock price update to all connected clients."""

        if not self._ensure_channel_layer():

            return



        try:

            # Broadcast to a general group for all users

            async_to_sync(self.channel_layer.group_send)(

                "stock_prices_all",

                {

                    "type": "stock_price_update",

                    "symbol": symbol,

                    "price": price_data.get("price", 0),

                    "change": price_data.get("change", 0),

                    "change_percent": price_data.get("change_percent", 0),

                    "volume": price_data.get("volume", 0),

                    "timestamp": time.time(),

                },

            )



            # Broadcast to specific user groups who have this stock in their watchlist

            watchlist_users = (

                Watchlist.objects.filter(stock__symbol=symbol)

                .values_list("user_id", flat=True)

                .distinct()

            )



            for user_id in watchlist_users:

                async_to_sync(self.channel_layer.group_send)(

                    f"stock_prices_{user_id}",

                    {

                        "type": "stock_price_update",

                        "symbol": symbol,

                        "price": price_data.get("price", 0),

                        "change": price_data.get("change", 0),

                        "change_percent": price_data.get("change_percent", 0),

                        "volume": price_data.get("volume", 0),

                        "timestamp": time.time(),

                    },

                )

        except Exception as e:

            logger.error(f"Error broadcasting stock price update for {symbol}: {e}")



    def broadcast_price_alert(self, user_id, symbol, price, alert_type, message):

        """Broadcast a price alert to a specific user."""

        if not self._ensure_channel_layer():

            return



        try:

            async_to_sync(self.channel_layer.group_send)(

                f"stock_prices_{user_id}",

                {

                    "type": "price_alert",

                    "symbol": symbol,

                    "price": price,

                    "alert_type": alert_type,

                    "message": message,

                    "timestamp": time.time(),

                },

            )

        except Exception as e:

            logger.error(f"Error broadcasting price alert for {symbol} to {user_id}: {e}")



    def broadcast_new_discussion(self, discussion_data: dict):

        """Broadcast new discussion to all connected clients."""

        if not self._ensure_channel_layer():

            return



        try:

            async_to_sync(self.channel_layer.group_send)(

                "discussions",

                {

                    "type": "new_discussion",

                    "discussion": discussion_data,

                    "timestamp": time.time(),

                },

            )

        except Exception as e:

            logger.error(f"Error broadcasting new discussion: {e}")



    def broadcast_new_comment(self, comment_data: dict, discussion_id):

        """Broadcast new comment to all connected clients."""

        if not self._ensure_channel_layer():

            return



        try:

            async_to_sync(self.channel_layer.group_send)(

                "discussions",

                {

                    "type": "new_comment",

                    "comment": comment_data,

                    "discussion_id": discussion_id,

                    "timestamp": time.time(),

                },

            )

        except Exception as e:

            logger.error(f"Error broadcasting new comment on discussion {discussion_id}: {e}")



    def broadcast_discussion_update(self, discussion_id, updates: dict):

        """Broadcast discussion update (votes, etc.) to all connected clients."""

        if not self._ensure_channel_layer():

            return



        try:

            async_to_sync(self.channel_layer.group_send)(

                "discussions",

                {

                    "type": "discussion_update",

                    "discussion_id": discussion_id,

                    "updates": updates,

                    "timestamp": time.time(),

                },

            )

        except Exception as e:

            logger.error(f"Error broadcasting discussion update for {discussion_id}: {e}")





class StockPriceUpdater:

    """Background service for updating stock prices and broadcasting via WebSocket."""



    def __init__(self):

        self.websocket_service = WebSocketService()

        self.market_service = MarketDataService()

        self.running = False



    def start(self):

        """Start the stock price updater service in a background thread."""

        if self.running:

            return



        self.running = True

        logger.info("Starting stock price updater service")

        thread = threading.Thread(target=self._update_loop, daemon=True)

        thread.start()



    def stop(self):

        """Stop the stock price updater service."""

        self.running = False

        logger.info("Stopping stock price updater service")



    def _update_loop(self):

        """Main update loop for stock prices."""

        while self.running:

            try:

                watched_stocks = (

                    Stock.objects.filter(watchlist__isnull=False).distinct()

                )



                for stock in watched_stocks:

                    try:

                        price_data = self.market_service.get_stock_quote(stock.symbol)

                        if not price_data:

                            continue



                        # Update DB

                        stock.current_price = price_data.get(

                            "price", stock.current_price

                        )

                        stock.save(update_fields=["current_price"])



                        # Broadcast via WebSocket

                        self.websocket_service.broadcast_stock_price_update(

                            stock.symbol, price_data

                        )



                        logger.info(

                            f"Updated price for {stock.symbol}: "

                            f"${price_data.get('price', 0)}"

                        )

                    except Exception as e:

                        logger.error(

                            f"Error updating price for {stock.symbol}: {e}"

                        )



                # Wait 5 minutes before next refresh

                time.sleep(300)

            except Exception as e:

                logger.error(f"Error in stock price update loop: {e}")

                # Back off 1 minute before retry

                time.sleep(60)





# Global instances

websocket_service = WebSocketService()

stock_price_updater = StockPriceUpdater()
