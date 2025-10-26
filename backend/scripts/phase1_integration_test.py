"""
Phase 1: Live Data Integration Script
Complete setup and testing for live market data and brokerage integration
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Phase1LiveDataIntegration:
    """Complete Phase 1 implementation and testing"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.test_results = {}
        
    async def run_complete_integration_test(self):
        """Run complete Phase 1 integration test"""
        self.logger.info("🚀 Starting Phase 1: Live Data Integration Test")
        
        try:
            # Test 1: Market Data Provider
            await self._test_market_data_provider()
            
            # Test 2: Universe Generation
            await self._test_universe_generation()
            
            # Test 3: Feature Calculation
            await self._test_feature_calculation()
            
            # Test 4: Live Trading Engine
            await self._test_live_trading_engine()
            
            # Test 5: Voice Trading Integration
            await self._test_voice_trading_integration()
            
            # Test 6: End-to-End Workflow
            await self._test_end_to_end_workflow()
            
            # Generate report
            self._generate_test_report()
            
        except Exception as e:
            self.logger.error(f"❌ Integration test failed: {e}")
    
    async def _test_market_data_provider(self):
        """Test market data provider functionality"""
        self.logger.info("📡 Testing Market Data Provider...")
        
        try:
            from backend.market.providers.polygon import PolygonProvider
            from backend.market.providers.base import MockMarketDataProvider
            
            # Test with mock provider first
            mock_provider = MockMarketDataProvider()
            
            # Test quotes
            quotes = await mock_provider.get_quotes(["AAPL", "MSFT", "TSLA"])
            assert len(quotes) == 3
            assert "AAPL" in quotes
            
            # Test OHLCV data
            ohlcv = await mock_provider.get_ohlcv("AAPL", "5m", 50)
            assert len(ohlcv) == 50
            
            # Test market status
            status = await mock_provider.get_market_status()
            assert "is_open" in status
            
            self.test_results["market_data_provider"] = "✅ PASS"
            self.logger.info("✅ Market Data Provider test passed")
            
        except Exception as e:
            self.test_results["market_data_provider"] = f"❌ FAIL: {e}"
            self.logger.error(f"❌ Market Data Provider test failed: {e}")
    
    async def _test_universe_generation(self):
        """Test universe generation"""
        self.logger.info("🔍 Testing Universe Generation...")
        
        try:
            from backend.market.providers.base import MockMarketDataProvider
            from backend.algo.universe_generator import LiveUniverseGenerator
            
            # Create universe generator with mock provider
            mock_provider = MockMarketDataProvider()
            universe_gen = LiveUniverseGenerator(mock_provider)
            
            # Test SAFE universe
            safe_universe = await universe_gen.generate_universe("SAFE")
            assert len(safe_universe) > 0
            
            # Test AGGRESSIVE universe
            aggressive_universe = await universe_gen.generate_universe("AGGRESSIVE")
            assert len(aggressive_universe) > 0
            
            # Test top movers
            top_movers = await universe_gen.get_top_movers(5)
            assert len(top_movers) <= 5
            
            # Test volume leaders
            volume_leaders = await universe_gen.get_volume_leaders(5)
            assert len(volume_leaders) <= 5
            
            self.test_results["universe_generation"] = "✅ PASS"
            self.logger.info("✅ Universe Generation test passed")
            
        except Exception as e:
            self.test_results["universe_generation"] = f"❌ FAIL: {e}"
            self.logger.error(f"❌ Universe Generation test failed: {e}")
    
    async def _test_feature_calculation(self):
        """Test real-time feature calculation"""
        self.logger.info("🧮 Testing Feature Calculation...")
        
        try:
            from backend.market.providers.base import MockMarketDataProvider
            from backend.algo.feature_calculator import RealTimeFeatureCalculator
            
            # Create feature calculator with mock provider
            mock_provider = MockMarketDataProvider()
            feature_calc = RealTimeFeatureCalculator(mock_provider)
            
            # Test feature calculation for AAPL
            features = await feature_calc.calculate_features("AAPL")
            assert features is not None
            assert features.symbol == "AAPL"
            assert hasattr(features, 'momentum_15m')
            assert hasattr(features, 'rsi_14')
            assert hasattr(features, 'composite_score')
            
            self.test_results["feature_calculation"] = "✅ PASS"
            self.logger.info("✅ Feature Calculation test passed")
            
        except Exception as e:
            self.test_results["feature_calculation"] = f"❌ FAIL: {e}"
            self.logger.error(f"❌ Feature Calculation test failed: {e}")
    
    async def _test_live_trading_engine(self):
        """Test live trading engine"""
        self.logger.info("🎯 Testing Live Trading Engine...")
        
        try:
            from backend.market.providers.base import MockMarketDataProvider
            from backend.broker.adapters.base import MockBroker
            from backend.algo.universe_generator import LiveUniverseGenerator
            from backend.algo.feature_calculator import RealTimeFeatureCalculator
            from backend.algo.live_trading_engine import LiveDayTradingEngine
            
            # Create all components with mock providers
            mock_market = MockMarketDataProvider()
            mock_broker = MockBroker()
            universe_gen = LiveUniverseGenerator(mock_market)
            feature_calc = RealTimeFeatureCalculator(mock_market)
            
            # Create trading engine
            engine = LiveDayTradingEngine(
                universe_generator=universe_gen,
                feature_calculator=feature_calc,
                broker=mock_broker,
                market_data_provider=mock_market
            )
            
            # Test SAFE picks generation
            safe_picks = await engine.generate_picks("SAFE")
            assert len(safe_picks) > 0
            
            # Test AGGRESSIVE picks generation
            aggressive_picks = await engine.generate_picks("AGGRESSIVE")
            assert len(aggressive_picks) > 0
            
            # Test live picks retrieval
            live_picks = await engine.get_live_picks("SAFE")
            assert len(live_picks) > 0
            
            self.test_results["live_trading_engine"] = "✅ PASS"
            self.logger.info("✅ Live Trading Engine test passed")
            
        except Exception as e:
            self.test_results["live_trading_engine"] = f"❌ FAIL: {e}"
            self.logger.error(f"❌ Live Trading Engine test failed: {e}")
    
    async def _test_voice_trading_integration(self):
        """Test voice trading integration"""
        self.logger.info("🎤 Testing Voice Trading Integration...")
        
        try:
            from backend.voice.command_parser import VoiceCommandParser
            from backend.streaming.alpaca_websocket import AlpacaWebSocketStreamer
            
            # Test voice command parser
            parser = VoiceCommandParser()
            
            test_commands = [
                "Nova, buy 100 AAPL at limit $150",
                "Echo, sell 50 TSLA at market",
                "Long 25 MSFT at $300",
                "Short 10 NVDA stop at $200"
            ]
            
            for command in test_commands:
                parsed = parser.parse_command(command)
                assert parsed is not None
                assert parsed.symbol in ["AAPL", "TSLA", "MSFT", "NVDA"]
                assert parsed.side in ["buy", "sell"]
                assert parsed.quantity > 0
                assert parsed.confidence > 0
            
            # Test confirmation messages
            test_order = parser.parse_command("Nova, buy 100 AAPL at limit $150")
            confirmation = parser.get_confirmation_message(test_order, "Nova")
            assert "Nova confirming" in confirmation
            assert "AAPL" in confirmation
            
            self.test_results["voice_trading_integration"] = "✅ PASS"
            self.logger.info("✅ Voice Trading Integration test passed")
            
        except Exception as e:
            self.test_results["voice_trading_integration"] = f"❌ FAIL: {e}"
            self.logger.error(f"❌ Voice Trading Integration test failed: {e}")
    
    async def _test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        self.logger.info("🔄 Testing End-to-End Workflow...")
        
        try:
            # Simulate complete trading workflow
            from backend.market.providers.base import MockMarketDataProvider
            from backend.broker.adapters.base import MockBroker
            from backend.algo.universe_generator import LiveUniverseGenerator
            from backend.algo.feature_calculator import RealTimeFeatureCalculator
            from backend.algo.live_trading_engine import LiveDayTradingEngine
            from backend.voice.command_parser import VoiceCommandParser
            
            # Create all components
            mock_market = MockMarketDataProvider()
            mock_broker = MockBroker()
            universe_gen = LiveUniverseGenerator(mock_market)
            feature_calc = RealTimeFeatureCalculator(mock_market)
            engine = LiveDayTradingEngine(
                universe_generator=universe_gen,
                feature_calculator=feature_calc,
                broker=mock_broker,
                market_data_provider=mock_market
            )
            parser = VoiceCommandParser()
            
            # Step 1: Generate universe
            universe = await universe_gen.generate_universe("SAFE")
            assert len(universe) > 0
            
            # Step 2: Generate picks
            picks = await engine.generate_picks("SAFE")
            assert len(picks) > 0
            
            # Step 3: Parse voice command
            voice_command = "Nova, buy 100 AAPL at limit $150"
            parsed_order = parser.parse_command(voice_command)
            assert parsed_order is not None
            
            # Step 4: Place order (mock)
            order = await mock_broker.place_order(
                symbol=parsed_order.symbol,
                side=self._map_side(parsed_order.side),
                quantity=parsed_order.quantity,
                order_type=self._map_order_type(parsed_order.order_type),
                limit_price=parsed_order.price
            )
            assert order is not None
            assert order.status.value in ["new", "filled"]
            
            self.test_results["end_to_end_workflow"] = "✅ PASS"
            self.logger.info("✅ End-to-End Workflow test passed")
            
        except Exception as e:
            self.test_results["end_to_end_workflow"] = f"❌ FAIL: {e}"
            self.logger.error(f"❌ End-to-End Workflow test failed: {e}")
    
    def _map_side(self, side: str):
        """Map string side to OrderSide enum"""
        from backend.broker.adapters.base import OrderSide
        return OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
    
    def _map_order_type(self, order_type: str):
        """Map string order type to OrderType enum"""
        from backend.broker.adapters.base import OrderType
        return OrderType(order_type.lower())
    
    def _generate_test_report(self):
        """Generate comprehensive test report"""
        self.logger.info("📊 Generating Test Report...")
        
        report = f"""
# 🚀 Phase 1: Live Data Integration - Test Report
Generated: {datetime.now().isoformat()}

## Test Results Summary

"""
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result.startswith("✅"))
        
        for test_name, result in self.test_results.items():
            report += f"- **{test_name.replace('_', ' ').title()}**: {result}\n"
        
        report += f"""
## Overall Status
- **Total Tests**: {total_tests}
- **Passed**: {passed_tests}
- **Failed**: {total_tests - passed_tests}
- **Success Rate**: {(passed_tests/total_tests)*100:.1f}%

## Next Steps
"""
        
        if passed_tests == total_tests:
            report += """
✅ **Phase 1 Complete!** All tests passed successfully.

### Ready for Production:
1. Configure real API keys (Alpaca, Polygon)
2. Deploy to staging environment
3. Run load tests with 100+ concurrent users
4. Begin beta testing with select users

### Phase 2 Preparation:
- Advanced order types (bracket, OCO)
- Machine learning model integration
- Real-time risk management
- Performance analytics dashboard
"""
        else:
            report += """
⚠️ **Phase 1 Needs Attention** - Some tests failed.

### Action Required:
1. Review failed tests and fix issues
2. Re-run integration tests
3. Ensure all dependencies are installed
4. Check API key configurations

### Common Issues:
- Missing dependencies
- Incorrect API configurations
- Network connectivity problems
- Environment variable issues
"""
        
        # Save report
        with open("phase1_test_report.md", "w") as f:
            f.write(report)
        
        self.logger.info(f"📊 Test report saved to phase1_test_report.md")
        print(report)


async def main():
    """Main function to run Phase 1 integration test"""
    integration = Phase1LiveDataIntegration()
    await integration.run_complete_integration_test()


if __name__ == "__main__":
    asyncio.run(main())
