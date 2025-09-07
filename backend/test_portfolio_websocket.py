#!/usr/bin/env python3
"""
Test script for Portfolio WebSocket functionality
"""
import asyncio
import websockets
import json
import time

async def test_portfolio_websocket():
    """Test the portfolio WebSocket connection"""
    uri = "ws://localhost:8001/ws/portfolio/"
    
    try:
        print("🔌 Connecting to Portfolio WebSocket...")
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to Portfolio WebSocket")
            
            # Send authentication (optional for testing)
            auth_message = {
                "type": "authenticate",
                "token": "test_token"
            }
            await websocket.send(json.dumps(auth_message))
            print("📤 Sent authentication message")
            
            # Subscribe to portfolio updates
            subscribe_message = {
                "type": "subscribe_portfolio"
            }
            await websocket.send(json.dumps(subscribe_message))
            print("📤 Sent subscription message")
            
            # Listen for messages
            print("👂 Listening for portfolio updates...")
            for i in range(5):  # Listen for 5 messages
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(message)
                    print(f"📊 Received portfolio update #{i+1}:")
                    print(f"   Total Value: ${data.get('totalValue', 'N/A')}")
                    print(f"   Total Return: ${data.get('totalReturn', 'N/A')}")
                    print(f"   Return %: {data.get('totalReturnPercent', 'N/A')}%")
                    print(f"   Holdings: {len(data.get('holdings', []))} stocks")
                    print(f"   Market Status: {data.get('marketStatus', 'N/A')}")
                    print()
                except asyncio.TimeoutError:
                    print(f"⏰ Timeout waiting for message #{i+1}")
                    break
                    
    except websockets.exceptions.ConnectionRefused:
        print("❌ Connection refused. Make sure the Django server is running with WebSocket support.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Testing Portfolio WebSocket...")
    asyncio.run(test_portfolio_websocket())
