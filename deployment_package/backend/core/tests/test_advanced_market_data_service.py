"""
Unit tests for Advanced Market Data Service
"""
import os
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
from django.test import TestCase

from core.advanced_market_data_service import (
    AdvancedMarketDataService,
    MarketIndicator,
    EconomicIndicator,
    AlternativeData,
    DataSource
)


class AdvancedMarketDataServiceTestCase(TestCase):
    """Tests for Advanced Market Data Service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.service = AdvancedMarketDataService()
    
    def test_initialization(self):
        """Test service initialization"""
        self.assertIsNotNone(self.service.api_keys)
        self.assertIsNone(self.service.session)
        self.assertEqual(self.service.cache, {})
        self.assertEqual(self.service.cache_duration, 300)
        self.assertIn(DataSource.ALPHA_VANTAGE, self.service.rate_limits)
    
    def test_load_api_keys(self):
        """Test API key loading from environment"""
        with patch.dict(os.environ, {
            'ALPHA_VANTAGE_API_KEY': 'test_av_key',
            'FINNHUB_API_KEY': 'test_fh_key',
            'NEWS_API_KEY': 'test_news_key'
        }):
            service = AdvancedMarketDataService()
            self.assertEqual(service.api_keys['alpha_vantage'], 'test_av_key')
            self.assertEqual(service.api_keys['finnhub'], 'test_fh_key')
            self.assertEqual(service.api_keys['news_api'], 'test_news_key')
    
    def test_check_rate_limit(self):
        """Test rate limiting"""
        # First call should pass
        result = self.service._check_rate_limit(DataSource.ALPHA_VANTAGE)
        self.assertTrue(result)
        
        # Should still pass (rate limit resets after 60 seconds)
        result = self.service._check_rate_limit(DataSource.ALPHA_VANTAGE)
        self.assertTrue(result)
    
    def test_is_cache_valid(self):
        """Test cache validation"""
        # Empty cache should be invalid
        self.assertFalse(self.service._is_cache_valid('test_key'))
        
        # Add to cache
        self.service._cache_data('test_key', 'test_value')
        self.assertTrue(self.service._is_cache_valid('test_key'))
        
        # Expire cache
        self.service.cache_expiry['test_key'] = datetime.now() - timedelta(seconds=1)
        self.assertFalse(self.service._is_cache_valid('test_key'))
    
    def test_cache_data(self):
        """Test data caching"""
        test_data = {'test': 'data'}
        self.service._cache_data('test_key', test_data)
        
        self.assertIn('test_key', self.service.cache)
        self.assertEqual(self.service.cache['test_key'], test_data)
        self.assertIn('test_key', self.service.cache_expiry)
    
    def test_analyze_vix_trend(self):
        """Test VIX trend analysis"""
        # Low VIX (bullish)
        trend = self.service._analyze_vix_trend(12.0)
        self.assertEqual(trend, 'bullish')
        
        # Medium VIX (neutral)
        trend = self.service._analyze_vix_trend(20.0)
        self.assertEqual(trend, 'neutral')
        
        # High VIX (bearish)
        trend = self.service._analyze_vix_trend(30.0)
        self.assertEqual(trend, 'bearish')
    
    def test_analyze_yield_trend(self):
        """Test bond yield trend analysis"""
        # Low yield (bullish)
        trend = self.service._analyze_yield_trend(1.5)
        self.assertEqual(trend, 'bullish')
        
        # Medium yield (neutral)
        trend = self.service._analyze_yield_trend(2.5)
        self.assertEqual(trend, 'neutral')
        
        # High yield (bearish)
        trend = self.service._analyze_yield_trend(4.0)
        self.assertEqual(trend, 'bearish')
    
    def test_analyze_sector_trend(self):
        """Test sector trend analysis"""
        # Positive change (bullish)
        trend = self.service._analyze_sector_trend(1.0)
        self.assertEqual(trend, 'bullish')
        
        # Negative change (bearish)
        trend = self.service._analyze_sector_trend(-0.5)
        self.assertEqual(trend, 'bearish')
        
        # Small change (neutral)
        trend = self.service._analyze_sector_trend(0.1)
        self.assertEqual(trend, 'neutral')
    
    def test_get_synthetic_vix(self):
        """Test synthetic VIX data generation"""
        vix = self.service._get_synthetic_vix()
        self.assertIsInstance(vix, MarketIndicator)
        self.assertEqual(vix.name, "VIX Volatility Index")
        self.assertEqual(vix.source, 'synthetic')
        self.assertGreater(vix.value, 0)
    
    def test_get_synthetic_bond_yields(self):
        """Test synthetic bond yield data generation"""
        yields = self.service._get_synthetic_bond_yields()
        self.assertIsInstance(yields, list)
        self.assertGreater(len(yields), 0)
        self.assertIsInstance(yields[0], MarketIndicator)
        self.assertIn('Treasury', yields[0].name)
    
    def test_get_synthetic_currency_data(self):
        """Test synthetic currency data generation"""
        currencies = self.service._get_synthetic_currency_data()
        self.assertIsInstance(currencies, list)
        self.assertGreater(len(currencies), 0)
        self.assertIsInstance(currencies[0], MarketIndicator)
        self.assertIn('Exchange Rate', currencies[0].name)
    
    def test_get_synthetic_economic_indicators(self):
        """Test synthetic economic indicators generation"""
        indicators = self.service._get_synthetic_economic_indicators()
        self.assertIsInstance(indicators, list)
        self.assertGreater(len(indicators), 0)
        self.assertIsInstance(indicators[0], EconomicIndicator)
    
    def test_get_synthetic_sector_data(self):
        """Test synthetic sector data generation"""
        sectors = self.service._get_synthetic_sector_data()
        self.assertIsInstance(sectors, dict)
        self.assertGreater(len(sectors), 0)
        self.assertIn('Technology', sectors)
        self.assertIsInstance(sectors['Technology'], MarketIndicator)
    
    def test_get_synthetic_alternative_data(self):
        """Test synthetic alternative data generation"""
        alt_data = self.service._get_synthetic_alternative_data()
        self.assertIsInstance(alt_data, list)
        self.assertGreater(len(alt_data), 0)
        self.assertIsInstance(alt_data[0], AlternativeData)
    
    def test_analyze_market_regime(self):
        """Test market regime analysis"""
        results = [None, None, None, None, None, None]
        regime = self.service._analyze_market_regime(results)
        self.assertIsInstance(regime, dict)
        self.assertIn('regime', regime)
        self.assertIn('confidence', regime)
        self.assertIn('trend', regime)
    
    def test_assess_market_risk(self):
        """Test market risk assessment"""
        results = [None, None, None, None, None, None]
        risk = self.service._assess_market_risk(results)
        self.assertIsInstance(risk, dict)
        self.assertIn('risk_level', risk)
        self.assertIn('risk_score', risk)
        self.assertIn('key_risks', risk)
    
    def test_analyze_market_opportunities(self):
        """Test market opportunity analysis"""
        results = [None, None, None, None, None, None]
        opportunities = self.service._analyze_market_opportunities(results)
        self.assertIsInstance(opportunities, dict)
        self.assertIn('opportunity_score', opportunities)
        self.assertIn('top_opportunities', opportunities)
    
    def test_get_session(self):
        """Test session creation"""
        async def run_test():
            session = await self.service._get_session()
            self.assertIsNotNone(session)
            self.assertFalse(session.closed)
            
            # Should reuse same session
            session2 = await self.service._get_session()
            self.assertEqual(session, session2)
        
        asyncio.run(run_test())
    
    def test_make_api_call_success(self):
        """Test successful API call"""
        async def run_test():
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={'test': 'data'})
            
            with patch('aiohttp.ClientSession.get') as mock_get:
                mock_get.return_value.__aenter__.return_value = mock_response
                
                result = await self.service._make_api_call('https://test.com')
                self.assertEqual(result, {'test': 'data'})
        
        asyncio.run(run_test())
    
    def test_make_api_call_failure(self):
        """Test failed API call"""
        async def run_test():
            mock_response = MagicMock()
            mock_response.status = 404
            
            with patch('aiohttp.ClientSession.get') as mock_get:
                mock_get.return_value.__aenter__.return_value = mock_response
                
                result = await self.service._make_api_call('https://test.com')
                self.assertEqual(result, {})
        
        asyncio.run(run_test())
    
    def test_get_real_time_vix_with_cache(self):
        """Test VIX retrieval with cache"""
        async def run_test():
            # Cache some data
            cached_vix = MarketIndicator(
                name="VIX",
                value=20.0,
                change=0.5,
                change_percent=2.5,
                timestamp=datetime.now(),
                source='test',
                confidence=0.9,
                trend='neutral'
            )
            self.service._cache_data('vix_real_time', cached_vix)
            
            result = await self.service.get_real_time_vix()
            self.assertEqual(result, cached_vix)
        
        asyncio.run(run_test())
    
    def test_get_real_time_vix_synthetic_fallback(self):
        """Test VIX retrieval with synthetic fallback"""
        async def run_test():
            # No API keys, should use synthetic
            service = AdvancedMarketDataService()
            result = await service.get_real_time_vix()
            self.assertIsInstance(result, MarketIndicator)
            self.assertEqual(result.name, "VIX Volatility Index")
        
        asyncio.run(run_test())
    
    def test_get_real_time_bond_yields_synthetic(self):
        """Test bond yields retrieval"""
        async def run_test():
            service = AdvancedMarketDataService()
            yields = await service.get_real_time_bond_yields()
            self.assertIsInstance(yields, list)
            self.assertGreater(len(yields), 0)
            self.assertIsInstance(yields[0], MarketIndicator)
        
        asyncio.run(run_test())
    
    def test_get_real_time_currency_strength_synthetic(self):
        """Test currency strength retrieval"""
        async def run_test():
            service = AdvancedMarketDataService()
            currencies = await service.get_real_time_currency_strength()
            self.assertIsInstance(currencies, list)
            self.assertGreater(len(currencies), 0)
        
        asyncio.run(run_test())
    
    def test_get_economic_indicators_synthetic(self):
        """Test economic indicators retrieval"""
        async def run_test():
            service = AdvancedMarketDataService()
            indicators = await service.get_economic_indicators()
            self.assertIsInstance(indicators, list)
            self.assertGreater(len(indicators), 0)
            self.assertIsInstance(indicators[0], EconomicIndicator)
        
        asyncio.run(run_test())
    
    def test_get_sector_performance_synthetic(self):
        """Test sector performance retrieval"""
        async def run_test():
            service = AdvancedMarketDataService()
            sectors = await service.get_sector_performance()
            self.assertIsInstance(sectors, dict)
            self.assertGreater(len(sectors), 0)
        
        asyncio.run(run_test())
    
    def test_get_alternative_data_synthetic(self):
        """Test alternative data retrieval"""
        async def run_test():
            service = AdvancedMarketDataService()
            alt_data = await service.get_alternative_data()
            self.assertIsInstance(alt_data, list)
            self.assertGreater(len(alt_data), 0)
            self.assertIsInstance(alt_data[0], AlternativeData)
        
        asyncio.run(run_test())
    
    def test_get_comprehensive_market_overview(self):
        """Test comprehensive market overview"""
        async def run_test():
            service = AdvancedMarketDataService()
            overview = await service.get_comprehensive_market_overview()
            
            self.assertIsInstance(overview, dict)
            self.assertIn('timestamp', overview)
            self.assertIn('vix', overview)
            self.assertIn('bond_yields', overview)
            self.assertIn('currencies', overview)
            self.assertIn('economic_indicators', overview)
            self.assertIn('sector_performance', overview)
            self.assertIn('alternative_data', overview)
            self.assertIn('market_regime', overview)
            self.assertIn('risk_assessment', overview)
            self.assertIn('opportunity_analysis', overview)
        
        asyncio.run(run_test())
    
    def test_close(self):
        """Test service cleanup"""
        async def run_test():
            await self.service._get_session()  # Create session
            await self.service.close()
            self.assertTrue(self.service.session.closed)
        
        asyncio.run(run_test())

