#!/usr/bin/env python3
"""
Test script for concurrent portfolio WebSocket updates
This script simulates multiple clients and real-time data changes
"""
import asyncio
import websockets
import json
import time
import random
from datetime import datetime

class PortfolioDataSimulator:
    """Simulates realistic portfolio data changes"""
    
    def __init__(self):
        self.base_portfolio = {
            'totalValue': 14303.52,
            'totalCost': 12157.99,
            'totalReturn': 2145.53,
            'totalReturnPercent': 17.65,
            'holdings': [
                {
                    'symbol': 'AAPL',
                    'companyName': 'Apple Inc.',
                    'shares': 10,
                    'currentPrice': 175.43,
                    'totalValue': 1754.30,
                    'costBasis': 1500.00,
                    'returnAmount': 254.30,
                    'returnPercent': 16.95,
                    'sector': 'Technology'
                },
                {
                    'symbol': 'MSFT',
                    'companyName': 'Microsoft Corporation',
                    'shares': 5,
                    'currentPrice': 378.85,
                    'totalValue': 1894.25,
                    'costBasis': 1800.00,
                    'returnAmount': 94.25,
                    'returnPercent': 5.24,
                    'sector': 'Technology'
                },
                {
                    'symbol': 'GOOGL',
                    'companyName': 'Alphabet Inc.',
                    'shares': 3,
                    'currentPrice': 142.56,
                    'totalValue': 427.68,
                    'costBasis': 400.00,
                    'returnAmount': 27.68,
                    'returnPercent': 6.92,
                    'sector': 'Technology'
                },
                {
                    'symbol': 'NFLX',
                    'companyName': 'Netflix Inc.',
                    'shares': 8,
                    'currentPrice': 485.20,
                    'totalValue': 3881.60,
                    'costBasis': 3500.00,
                    'returnAmount': 381.60,
                    'returnPercent': 10.90,
                    'sector': 'Communication Services'
                }
            ],
            'marketStatus': 'open'
        }
    
    def generate_realistic_update(self):
        """Generate a realistic portfolio update with small price changes"""
        portfolio = self.base_portfolio.copy()
        
        # Simulate small price changes (±0.5% to ±2%)
        for holding in portfolio['holdings']:
            change_percent = random.uniform(-2.0, 2.0)
            old_price = holding['currentPrice']
            new_price = old_price * (1 + change_percent / 100)
            
            holding['currentPrice'] = round(new_price, 2)
            holding['totalValue'] = round(holding['shares'] * new_price, 2)
            holding['returnAmount'] = round(holding['totalValue'] - holding['costBasis'], 2)
            holding['returnPercent'] = round((holding['returnAmount'] / holding['costBasis']) * 100, 2)
        
        # Recalculate totals
        portfolio['totalValue'] = round(sum(h['totalValue'] for h in portfolio['holdings']), 2)
        portfolio['totalReturn'] = round(portfolio['totalValue'] - portfolio['totalCost'], 2)
        portfolio['totalReturnPercent'] = round((portfolio['totalReturn'] / portfolio['totalCost']) * 100, 2)
        
        return portfolio

async def test_single_client():
    """Test a single WebSocket client"""
    uri = "ws://localhost:8001/ws/portfolio/"
    
    try:
        print(f"🔌 [{datetime.now().strftime('%H:%M:%S')}] Connecting to Portfolio WebSocket...")
        async with websockets.connect(uri) as websocket:
            print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] Connected successfully")
            
            # Subscribe to portfolio updates
            subscribe_message = {"type": "subscribe_portfolio"}
            await websocket.send(json.dumps(subscribe_message))
            print(f"📤 [{datetime.now().strftime('%H:%M:%S')}] Subscribed to portfolio updates")
            
            # Listen for updates
            update_count = 0
            start_time = time.time()
            
            while update_count < 10:  # Listen for 10 updates
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                    data = json.loads(message)
                    
                    if data.get('type') == 'portfolio_update':
                        update_count += 1
                        elapsed = time.time() - start_time
                        
                        print(f"📊 [{datetime.now().strftime('%H:%M:%S')}] Update #{update_count} (after {elapsed:.1f}s):")
                        print(f"   💰 Total Value: ${data.get('totalValue', 'N/A'):,.2f}")
                        print(f"   📈 Total Return: ${data.get('totalReturn', 'N/A'):,.2f}")
                        print(f"   📊 Return %: {data.get('totalReturnPercent', 'N/A'):.2f}%")
                        print(f"   🏢 Holdings: {len(data.get('holdings', []))} stocks")
                        print(f"   🕐 Market Status: {data.get('marketStatus', 'N/A')}")
                        print()
                        
                except asyncio.TimeoutError:
                    print(f"⏰ [{datetime.now().strftime('%H:%M:%S')}] Timeout waiting for update #{update_count + 1}")
                    break
                    
    except websockets.exceptions.ConnectionRefused:
        print(f"❌ [{datetime.now().strftime('%H:%M:%S')}] Connection refused. Make sure Django server is running.")
    except Exception as e:
        print(f"❌ [{datetime.now().strftime('%H:%M:%S')}] Error: {e}")

async def test_multiple_clients():
    """Test multiple concurrent WebSocket clients"""
    print("🚀 Testing multiple concurrent WebSocket clients...")
    
    # Create multiple client tasks
    tasks = []
    for i in range(3):  # 3 concurrent clients
        task = asyncio.create_task(test_single_client_with_id(i + 1))
        tasks.append(task)
    
    # Wait for all clients to complete
    await asyncio.gather(*tasks, return_exceptions=True)
    print("✅ All concurrent client tests completed")

async def test_single_client_with_id(client_id):
    """Test a single client with ID for concurrent testing"""
    uri = "ws://localhost:8001/ws/portfolio/"
    
    try:
        print(f"🔌 [Client {client_id}] Connecting...")
        async with websockets.connect(uri) as websocket:
            print(f"✅ [Client {client_id}] Connected")
            
            # Subscribe
            await websocket.send(json.dumps({"type": "subscribe_portfolio"}))
            
            # Listen for 5 updates
            for i in range(5):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(message)
                    
                    if data.get('type') == 'portfolio_update':
                        print(f"📊 [Client {client_id}] Update #{i+1}: ${data.get('totalValue', 0):,.2f}")
                        
                except asyncio.TimeoutError:
                    print(f"⏰ [Client {client_id}] Timeout on update #{i+1}")
                    break
                    
    except Exception as e:
        print(f"❌ [Client {client_id}] Error: {e}")

async def test_data_consistency():
    """Test that all clients receive the same data"""
    print("🔍 Testing data consistency across multiple clients...")
    
    uri = "ws://localhost:8001/ws/portfolio/"
    clients_data = []
    
    try:
        # Connect multiple clients
        clients = []
        for i in range(3):
            client = await websockets.connect(uri)
            await client.send(json.dumps({"type": "subscribe_portfolio"}))
            clients.append(client)
        
        # Collect one update from each client
        for i, client in enumerate(clients):
            try:
                message = await asyncio.wait_for(client.recv(), timeout=10.0)
                data = json.loads(message)
                if data.get('type') == 'portfolio_update':
                    clients_data.append({
                        'client_id': i + 1,
                        'totalValue': data.get('totalValue'),
                        'timestamp': data.get('timestamp')
                    })
            except asyncio.TimeoutError:
                print(f"⏰ Client {i+1} timeout")
        
        # Close all clients
        for client in clients:
            await client.close()
        
        # Check consistency
        if len(clients_data) >= 2:
            values = [d['totalValue'] for d in clients_data]
            if len(set(values)) == 1:
                print(f"✅ Data consistency: All clients received same value ${values[0]:,.2f}")
            else:
                print(f"❌ Data inconsistency: Values {values}")
        else:
            print("❌ Not enough data to test consistency")
            
    except Exception as e:
        print(f"❌ Consistency test error: {e}")

async def main():
    """Run all tests"""
    print("🧪 Portfolio WebSocket Concurrent Testing Suite")
    print("=" * 50)
    
    # Test 1: Single client
    print("\n1️⃣ Testing single client...")
    await test_single_client()
    
    # Test 2: Multiple concurrent clients
    print("\n2️⃣ Testing multiple concurrent clients...")
    await test_multiple_clients()
    
    # Test 3: Data consistency
    print("\n3️⃣ Testing data consistency...")
    await test_data_consistency()
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
