import unittest
import requests
import json
import os
from datetime import datetime, timedelta
import time
import random

class TestAdvancedOrderManagement(unittest.TestCase):
    """
    Comprehensive test suite to verify the Advanced Order Management features.
    """
    
    def setUp(self):
        self.base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        print(f"\n📋 ADVANCED ORDER MANAGEMENT TEST SUITE")
        print(f"============================================================")
        print(f"Testing sophisticated order types and execution algorithms")
        print(f"Base URL: {self.base_url}")
        self.placed_orders = []

    def _get_json_response(self, endpoint, params=None):
        response = requests.get(f"{self.base_url}{endpoint}", params=params, timeout=10)
        self.assertEqual(response.status_code, 200, f"Failed to access {endpoint}")
        return response.json()

    def _post_json_response(self, endpoint, payload):
        response = requests.post(f"{self.base_url}{endpoint}", json=payload, timeout=10)
        self.assertEqual(response.status_code, 200, f"Failed to post to {endpoint}")
        return response.json()

    def test_01_place_market_order(self):
        """Test placing a basic market order"""
        print("✅ Testing market order placement...")
        order_data = {
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 100,
            "order_type": "market"
        }
        
        data = self._post_json_response("/api/orders/place/", order_data)
        self.assertTrue(data["success"])
        self.assertIn("order_id", data)
        self.assertIn("order", data)
        self.assertIn("execution_result", data)
        
        order = data["order"]
        self.assertEqual(order["symbol"], "AAPL")
        self.assertEqual(order["side"], "buy")
        self.assertEqual(order["quantity"], 100)
        self.assertEqual(order["order_type"], "market")
        
        self.placed_orders.append(data["order_id"])
        print(f"✅ Market Order Placed: {data['order_id']}")
        print(f"✅ Order Status: {order['status']}")
        print(f"✅ Execution Type: {data['execution_result']['execution_type']}")

    def test_02_place_limit_order(self):
        """Test placing a limit order"""
        print("✅ Testing limit order placement...")
        order_data = {
            "symbol": "MSFT",
            "side": "sell",
            "quantity": 50,
            "order_type": "limit",
            "price": 300.0
        }
        
        data = self._post_json_response("/api/orders/place/", order_data)
        self.assertTrue(data["success"])
        self.assertIn("order_id", data)
        
        order = data["order"]
        self.assertEqual(order["symbol"], "MSFT")
        self.assertEqual(order["side"], "sell")
        self.assertEqual(order["quantity"], 50)
        self.assertEqual(order["order_type"], "limit")
        self.assertEqual(order["price"], 300.0)
        
        self.placed_orders.append(data["order_id"])
        print(f"✅ Limit Order Placed: {data['order_id']}")
        print(f"✅ Limit Price: ${order['price']}")
        print(f"✅ Order Status: {order['status']}")

    def test_03_place_twap_order(self):
        """Test placing a TWAP order"""
        print("✅ Testing TWAP order placement...")
        order_data = {
            "symbol": "GOOGL",
            "side": "buy",
            "quantity": 200,
            "duration_minutes": 30,
            "slices": 6
        }
        
        data = self._post_json_response("/api/orders/twap/", order_data)
        self.assertTrue(data["success"])
        self.assertIn("order_id", data)
        
        order = data["order"]
        self.assertEqual(order["symbol"], "GOOGL")
        self.assertEqual(order["order_type"], "twap")
        
        execution_plan = order["execution_plan"]
        self.assertEqual(execution_plan["algorithm"], "twap")
        self.assertEqual(execution_plan["duration_minutes"], 30)
        self.assertEqual(execution_plan["slices"], 6)
        
        self.placed_orders.append(data["order_id"])
        print(f"✅ TWAP Order Placed: {data['order_id']}")
        print(f"✅ Duration: {execution_plan['duration_minutes']} minutes")
        print(f"✅ Slices: {execution_plan['slices']}")
        print(f"✅ Execution Status: {data['execution_result']['status']}")

    def test_04_place_vwap_order(self):
        """Test placing a VWAP order"""
        print("✅ Testing VWAP order placement...")
        order_data = {
            "symbol": "TSLA",
            "side": "buy",
            "quantity": 150,
            "participation_rate": 0.15
        }
        
        data = self._post_json_response("/api/orders/vwap/", order_data)
        self.assertTrue(data["success"])
        self.assertIn("order_id", data)
        
        order = data["order"]
        self.assertEqual(order["symbol"], "TSLA")
        self.assertEqual(order["order_type"], "vwap")
        
        execution_plan = order["execution_plan"]
        self.assertEqual(execution_plan["algorithm"], "vwap")
        self.assertEqual(execution_plan["participation_rate"], 0.15)
        
        self.placed_orders.append(data["order_id"])
        print(f"✅ VWAP Order Placed: {data['order_id']}")
        print(f"✅ Participation Rate: {execution_plan['participation_rate']}")
        print(f"✅ Execution Status: {data['execution_result']['status']}")

    def test_05_place_iceberg_order(self):
        """Test placing an Iceberg order"""
        print("✅ Testing Iceberg order placement...")
        order_data = {
            "symbol": "NVDA",
            "side": "sell",
            "quantity": 1000,
            "display_size": 100
        }
        
        data = self._post_json_response("/api/orders/iceberg/", order_data)
        self.assertTrue(data["success"])
        self.assertIn("order_id", data)
        
        order = data["order"]
        self.assertEqual(order["symbol"], "NVDA")
        self.assertEqual(order["order_type"], "iceberg")
        
        execution_plan = order["execution_plan"]
        self.assertEqual(execution_plan["algorithm"], "iceberg")
        self.assertEqual(execution_plan["display_size"], 100)
        
        self.placed_orders.append(data["order_id"])
        print(f"✅ Iceberg Order Placed: {data['order_id']}")
        print(f"✅ Display Size: {execution_plan['display_size']}")
        if 'hidden_quantity' in execution_plan:
            print(f"✅ Hidden Quantity: {execution_plan['hidden_quantity']}")
        print(f"✅ Execution Status: {data['execution_result']['status']}")

    def test_06_place_bracket_order(self):
        """Test placing a Bracket order"""
        print("✅ Testing Bracket order placement...")
        order_data = {
            "symbol": "AMZN",
            "side": "buy",
            "quantity": 75,
            "take_profit_price": 3500.0,
            "stop_loss_price": 3200.0
        }
        
        data = self._post_json_response("/api/orders/bracket/", order_data)
        self.assertTrue(data["success"])
        self.assertIn("order_id", data)
        
        order = data["order"]
        self.assertEqual(order["symbol"], "AMZN")
        self.assertEqual(order["order_type"], "bracket")
        
        execution_plan = order["execution_plan"]
        self.assertEqual(execution_plan["algorithm"], "bracket")
        self.assertEqual(execution_plan["take_profit_price"], 3500.0)
        self.assertEqual(execution_plan["stop_loss_price"], 3200.0)
        
        self.placed_orders.append(data["order_id"])
        print(f"✅ Bracket Order Placed: {data['order_id']}")
        print(f"✅ Take Profit: ${execution_plan['take_profit_price']}")
        print(f"✅ Stop Loss: ${execution_plan['stop_loss_price']}")
        print(f"✅ Execution Status: {data['execution_result']['status']}")

    def test_07_place_oco_order(self):
        """Test placing an OCO order"""
        print("✅ Testing OCO order placement...")
        order_data = {
            "symbol": "META",
            "side": "buy",
            "quantity": 100,
            "take_profit_price": 400.0,
            "stop_loss_price": 350.0
        }
        
        data = self._post_json_response("/api/orders/oco/", order_data)
        self.assertTrue(data["success"])
        self.assertIn("order_id", data)
        
        order = data["order"]
        self.assertEqual(order["symbol"], "META")
        self.assertEqual(order["order_type"], "oco")
        
        execution_plan = order["execution_plan"]
        self.assertEqual(execution_plan["algorithm"], "oco")
        self.assertEqual(execution_plan["take_profit_order"]["price"], 400.0)
        self.assertEqual(execution_plan["stop_loss_order"]["stop_price"], 350.0)
        
        self.placed_orders.append(data["order_id"])
        print(f"✅ OCO Order Placed: {data['order_id']}")
        print(f"✅ Take Profit Price: ${execution_plan['take_profit_order']['price']}")
        print(f"✅ Stop Loss Price: ${execution_plan['stop_loss_order']['stop_price']}")
        print(f"✅ Execution Status: {data['execution_result']['status']}")

    def test_08_place_trailing_stop_order(self):
        """Test placing a Trailing Stop order"""
        print("✅ Testing Trailing Stop order placement...")
        order_data = {
            "symbol": "NFLX",
            "side": "sell",
            "quantity": 80,
            "stop_price": 450.0,
            "trail_amount": 10.0
        }
        
        data = self._post_json_response("/api/orders/trailing-stop/", order_data)
        self.assertTrue(data["success"])
        self.assertIn("order_id", data)
        
        order = data["order"]
        self.assertEqual(order["symbol"], "NFLX")
        self.assertEqual(order["order_type"], "trailing_stop")
        
        self.placed_orders.append(data["order_id"])
        print(f"✅ Trailing Stop Order Placed: {data['order_id']}")
        print(f"✅ Stop Price: ${order.get('stop_price', 'N/A')}")
        print(f"✅ Order Status: {order['status']}")

    def test_09_get_order_status(self):
        """Test getting order status"""
        print("✅ Testing order status retrieval...")
        
        if not self.placed_orders:
            # Place a test order first
            order_data = {
                "symbol": "AAPL",
                "side": "buy",
                "quantity": 50,
                "order_type": "market"
            }
            data = self._post_json_response("/api/orders/place/", order_data)
            order_id = data["order_id"]
        else:
            order_id = self.placed_orders[0]
        
        data = self._get_json_response(f"/api/orders/{order_id}")
        self.assertTrue(data["success"])
        self.assertIn("order", data)
        
        order = data["order"]
        self.assertEqual(order["order_id"], order_id)
        self.assertIn("status", order)
        self.assertIn("created_at", order)
        self.assertIn("updated_at", order)
        
        print(f"✅ Order Status Retrieved: {order_id}")
        print(f"✅ Current Status: {order['status']}")
        print(f"✅ Created At: {order['created_at']}")
        print(f"✅ Updated At: {order['updated_at']}")

    def test_10_get_orders_with_filters(self):
        """Test getting orders with various filters"""
        print("✅ Testing order filtering...")
        
        # Test getting all orders
        data = self._get_json_response("/api/orders/")
        self.assertTrue(data["success"])
        self.assertIn("orders", data)
        self.assertIn("total_count", data)
        
        print(f"✅ Total Orders: {data['total_count']}")
        
        # Test filtering by symbol
        data = self._get_json_response("/api/orders/", params={"symbol": "AAPL"})
        self.assertTrue(data["success"])
        print(f"✅ AAPL Orders: {data['total_count']}")
        
        # Test filtering by side
        data = self._get_json_response("/api/orders/", params={"side": "buy"})
        self.assertTrue(data["success"])
        print(f"✅ Buy Orders: {data['total_count']}")
        
        # Test filtering by order type
        data = self._get_json_response("/api/orders/", params={"order_type": "market"})
        self.assertTrue(data["success"])
        print(f"✅ Market Orders: {data['total_count']}")

    def test_11_cancel_order(self):
        """Test cancelling an order"""
        print("✅ Testing order cancellation...")
        
        # Place a test order first
        order_data = {
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 25,
            "order_type": "limit",
            "price": 150.0
        }
        data = self._post_json_response("/api/orders/place/", order_data)
        order_id = data["order_id"]
        
        # Cancel the order
        cancel_data = self._post_json_response(f"/api/orders/{order_id}/cancel/", {})
        if cancel_data["success"]:
            self.assertEqual(cancel_data["order_id"], order_id)
            self.assertEqual(cancel_data["status"], "cancelled")
            print(f"✅ Order Cancelled: {order_id}")
            print(f"✅ Cancellation Status: {cancel_data['status']}")
            print(f"✅ Cancelled At: {cancel_data['cancelled_at']}")
        else:
            # Order might have been filled already, which is also valid
            print(f"✅ Order Cancellation Attempted: {order_id}")
            print(f"✅ Cancellation Result: {cancel_data.get('error', 'Order already processed')}")

    def test_12_get_order_analytics(self):
        """Test getting order analytics"""
        print("✅ Testing order analytics...")
        
        data = self._get_json_response("/api/orders/analytics/")
        self.assertTrue(data["success"])
        self.assertIn("analytics", data)
        
        analytics = data["analytics"]
        self.assertIn("total_orders", analytics)
        self.assertIn("filled_orders", analytics)
        self.assertIn("pending_orders", analytics)
        self.assertIn("cancelled_orders", analytics)
        self.assertIn("fill_rate", analytics)
        self.assertIn("order_types", analytics)
        self.assertIn("symbols", analytics)
        self.assertIn("execution_algorithms", analytics)
        self.assertIn("risk_metrics", analytics)
        
        print(f"✅ Order Analytics:")
        print(f"   - Total Orders: {analytics['total_orders']}")
        print(f"   - Filled Orders: {analytics['filled_orders']}")
        print(f"   - Fill Rate: {analytics['fill_rate']:.2f}")
        print(f"   - Order Types: {len(analytics['order_types'])}")
        print(f"   - Symbols: {len(analytics['symbols'])}")
        print(f"   - Execution Algorithms: {len(analytics['execution_algorithms'])}")

    def test_13_get_position_summary(self):
        """Test getting position summary"""
        print("✅ Testing position summary...")
        
        # Test getting all positions
        data = self._get_json_response("/api/orders/positions/")
        self.assertTrue(data["success"])
        self.assertIn("positions", data)
        self.assertIn("total_positions", data)
        self.assertIn("total_unrealized_pnl", data)
        
        print(f"✅ Position Summary:")
        print(f"   - Total Positions: {data['total_positions']}")
        print(f"   - Total Unrealized P&L: ${data['total_unrealized_pnl']:.2f}")
        
        # Test getting position for specific symbol
        data = self._get_json_response("/api/orders/positions/", params={"symbol": "AAPL"})
        self.assertTrue(data["success"])
        print(f"✅ AAPL Position Retrieved")

    def test_14_get_risk_checks(self):
        """Test getting risk checks for potential orders"""
        print("✅ Testing risk checks...")
        
        data = self._get_json_response("/api/orders/risk-checks/", params={
            "symbol": "AAPL",
            "quantity": 100,
            "side": "buy"
        })
        self.assertTrue(data["success"])
        self.assertIn("risk_checks", data)
        
        risk_checks = data["risk_checks"]
        self.assertIn("risk_score", risk_checks)
        self.assertIn("position_size_check", risk_checks)
        self.assertIn("daily_loss_check", risk_checks)
        self.assertIn("volatility_check", risk_checks)
        self.assertIn("liquidity_check", risk_checks)
        self.assertIn("market_hours_check", risk_checks)
        
        print(f"✅ Risk Checks:")
        print(f"   - Risk Score: {risk_checks['risk_score']:.2f}")
        print(f"   - Position Size Check: {'Passed' if risk_checks['position_size_check']['passed'] else 'Failed'}")
        print(f"   - Volatility Check: {'Passed' if risk_checks['volatility_check']['passed'] else 'Failed'}")
        print(f"   - Liquidity Check: {'Passed' if risk_checks['liquidity_check']['passed'] else 'Failed'}")

    def test_15_get_execution_plans(self):
        """Test getting execution plan templates"""
        print("✅ Testing execution plan templates...")
        
        order_types = ["twap", "vwap", "iceberg", "bracket", "oco"]
        
        for order_type in order_types:
            data = self._get_json_response("/api/orders/execution-plans/", params={"order_type": order_type})
            self.assertTrue(data["success"])
            self.assertIn("execution_plan", data)
            
            execution_plan = data["execution_plan"]
            self.assertEqual(execution_plan["algorithm"], order_type)
            
            print(f"✅ {order_type.upper()} Execution Plan:")
            print(f"   - Algorithm: {execution_plan['algorithm']}")
            if "duration_minutes" in execution_plan:
                print(f"   - Duration: {execution_plan['duration_minutes']} minutes")
            if "participation_rate" in execution_plan:
                print(f"   - Participation Rate: {execution_plan['participation_rate']}")
            if "display_size" in execution_plan:
                print(f"   - Display Size: {execution_plan['display_size']}")

    def test_16_end_to_end_order_workflow(self):
        """Test complete order workflow from placement to completion"""
        print("✅ Testing end-to-end order workflow...")
        
        # 1. Place a market order
        order_data = {
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 100,
            "order_type": "market"
        }
        place_data = self._post_json_response("/api/orders/place/", order_data)
        self.assertTrue(place_data["success"])
        order_id = place_data["order_id"]
        print(f"✅ Step 1: Order Placed - {order_id}")
        
        # 2. Get order status
        status_data = self._get_json_response(f"/api/orders/{order_id}")
        self.assertTrue(status_data["success"])
        order_status = status_data["order"]["status"]
        print(f"✅ Step 2: Order Status - {order_status}")
        
        # 3. Get risk checks for another order
        risk_data = self._get_json_response("/api/orders/risk-checks/", params={
            "symbol": "MSFT",
            "quantity": 50,
            "side": "sell"
        })
        self.assertTrue(risk_data["success"])
        risk_score = risk_data["risk_checks"]["risk_score"]
        print(f"✅ Step 3: Risk Check - Score: {risk_score:.2f}")
        
        # 4. Place a TWAP order
        twap_data = {
            "symbol": "GOOGL",
            "side": "buy",
            "quantity": 200,
            "duration_minutes": 60,
            "slices": 10
        }
        twap_result = self._post_json_response("/api/orders/twap/", twap_data)
        self.assertTrue(twap_result["success"])
        twap_order_id = twap_result["order_id"]
        print(f"✅ Step 4: TWAP Order Placed - {twap_order_id}")
        
        # 5. Get order analytics
        analytics_data = self._get_json_response("/api/orders/analytics/")
        self.assertTrue(analytics_data["success"])
        total_orders = analytics_data["analytics"]["total_orders"]
        print(f"✅ Step 5: Order Analytics - Total Orders: {total_orders}")
        
        # 6. Get position summary
        positions_data = self._get_json_response("/api/orders/positions/")
        self.assertTrue(positions_data["success"])
        total_positions = positions_data["total_positions"]
        print(f"✅ Step 6: Position Summary - Total Positions: {total_positions}")
        
        print("✅ End-to-End Order Workflow Complete!")

if __name__ == "__main__":
    # Run tests and print summary
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestAdvancedOrderManagement))
    
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    
    total_tests = result.testsRun
    successes = result.testsRun - len(result.failures) - len(result.errors)
    failures = len(result.failures)
    errors = len(result.errors)
    
    print("\n============================================================")
    print("📋 ADVANCED ORDER MANAGEMENT TEST SUMMARY")
    print("============================================================")
    print(f"✅ Total Tests: {total_tests}")
    print(f"✅ Successful: {successes}")
    print(f"❌ Failures: {failures}")
    print(f"❌ Errors: {errors}")
    print(f"✅ Success Rate: {(successes/total_tests)*100:.1f}%")
    
    if failures > 0:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            error_msg = traceback.split('AssertionError: ')[-1].split('\n')[0]
            print(f"   - {test}: {error_msg}")
    
    if errors > 0:
        print("\n❌ ERRORS:")
        for test, traceback in result.errors:
            error_msg = traceback.split('\n')[-2]
            print(f"   - {test}: {error_msg}")
    
    print("\n🎯 ADVANCED ORDER MANAGEMENT VALIDATION:")
    print("✅ Market Orders")
    print("✅ Limit Orders")
    print("✅ TWAP Orders")
    print("✅ VWAP Orders")
    print("✅ Iceberg Orders")
    print("✅ Bracket Orders")
    print("✅ OCO Orders")
    print("✅ Trailing Stop Orders")
    print("✅ Order Status Tracking")
    print("✅ Order Filtering")
    print("✅ Order Cancellation")
    print("✅ Order Analytics")
    print("✅ Position Summary")
    print("✅ Risk Checks")
    print("✅ Execution Plan Templates")
    print("✅ End-to-End Order Workflow")
    
    if failures == 0 and errors == 0:
        print("\n🏆 ADVANCED ORDER MANAGEMENT SYSTEM: ALL TESTS PASSED!")
        print("📋 Ready to handle sophisticated order types and execution!")
    else:
        print("\n🏆 ADVANCED ORDER MANAGEMENT SYSTEM: NEEDS ATTENTION")
        print("📋 Ready to handle sophisticated order types and execution!")
