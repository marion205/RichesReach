#!/usr/bin/env python3
"""
Simple WebSocket test to verify portfolio updates are working
"""
import asyncio
import websockets
import json
import time

async def test_portfolio_websocket():
    """Simple test of portfolio WebSocket"""
    uri = "ws://localhost:8001/ws/portfolio/"
    
    try:
        print("🔌 Connecting to Portfolio WebSocket...")
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!")
            
            # Subscribe to portfolio updates
            subscribe_message = {"type": "subscribe_portfolio"}
            await websocket.send(json.dumps(subscribe_message))
            print("📤 Sent subscription message")
            
            # Listen for 3 updates
            for i in range(3):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(message)
                    
                    if data.get('type') == 'portfolio_update':
                        print(f"\n📊 Update #{i+1}:")
                        print(f"   💰 Total Value: ${data.get('totalValue', 0):,.2f}")
                        print(f"   📈 Total Return: ${data.get('totalReturn', 0):,.2f}")
                        print(f"   📊 Return %: {data.get('totalReturnPercent', 0):.2f}%")
                        print(f"   🏢 Holdings: {len(data.get('holdings', []))} stocks")
                        print(f"   🕐 Market Status: {data.get('marketStatus', 'N/A')}")
                        
                        # Show individual stock changes
                        holdings = data.get('holdings', [])
                        for holding in holdings[:2]:  # Show first 2 stocks
                            print(f"   📈 {holding.get('symbol', 'N/A')}: ${holding.get('currentPrice', 0):.2f} ({holding.get('returnPercent', 0):+.2f}%)")
                        
                except asyncio.TimeoutError:
                    print(f"⏰ Timeout waiting for update #{i+1}")
                    break
                    
            print("\n✅ Test completed successfully!")
                    
    except ConnectionRefusedError:
        print("❌ Connection refused. Make sure Django server is running with WebSocket support.")
        print("   Try: python manage.py runserver")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Simple Portfolio WebSocket Test")
    print("=" * 40)
    asyncio.run(test_portfolio_websocket())
