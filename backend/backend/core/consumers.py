# core/consumers.py
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .stock_data_provider import stock_provider

class StockPriceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = 'stock_prices'
        self.room_group_name = f'stock_{self.room_name}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        
        # Start sending stock price updates
        await self.send_stock_updates()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def send_stock_updates(self):
        """Send stock price updates every 5 seconds"""
        symbols = ['AAPL', 'MSFT', 'TSLA', 'NVDA', 'GOOGL', 'AMZN', 'META', 'NFLX']
        
        while True:
            try:
                # Get stock data for all symbols
                stock_data = {}
                for symbol in symbols:
                    data = await database_sync_to_async(stock_provider.get_stock_data)(symbol)
                    if data:
                        stock_data[symbol] = data
                
                # Send to WebSocket
                await self.send(text_data=json.dumps({
                    'type': 'stock_update',
                    'data': stock_data,
                    'timestamp': asyncio.get_event_loop().time()
                }))
                
                # Wait 5 seconds before next update
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"Error in stock price updates: {e}")
                await asyncio.sleep(5)

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = 'notifications'
        self.room_group_name = f'notifications_{self.room_name}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Handle incoming messages"""
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json['message']

            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'notification_message',
                    'message': message
                }
            )
        except Exception as e:
            print(f"Error processing notification: {e}")

    async def notification_message(self, event):
        """Handle notification messages"""
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'message': message
        }))