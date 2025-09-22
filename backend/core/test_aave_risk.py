"""
Unit tests for AAVE-style risk engine
Tests HF calculations, stress testing, and tier determination
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from .aave_risk import (
    total_collateral_usd, total_debt_usd, available_borrow_usd, health_factor,
    weighted_ltv, hf_tier, stress_test_hf, repay_to_target_hf, add_collateral_to_target_hf,
    risk_color, risk_message, calculate_lending_account_data
)
from .crypto_models import Cryptocurrency, LendingReserve, SupplyPosition, BorrowPosition

User = get_user_model()


class MockReserve:
    """Mock reserve object for testing"""
    def __init__(self, symbol, ltv=0.7, liquidation_threshold=0.75, can_be_collateral=True):
        self.cryptocurrency = MockCryptocurrency(symbol)
        self.ltv = Decimal(str(ltv))
        self.liquidation_threshold = Decimal(str(liquidation_threshold))
        self.can_be_collateral = can_be_collateral


class MockCryptocurrency:
    """Mock cryptocurrency object for testing"""
    def __init__(self, symbol):
        self.symbol = symbol


class AAVERiskEngineTest(TestCase):
    """Test AAVE-style risk engine calculations"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test cryptocurrencies
        self.btc = Cryptocurrency.objects.create(
            symbol='BTC',
            name='Bitcoin',
            is_active=True,
            volatility_tier='HIGH'
        )
        self.eth = Cryptocurrency.objects.create(
            symbol='ETH', 
            name='Ethereum',
            is_active=True,
            volatility_tier='MEDIUM'
        )
        self.usdc = Cryptocurrency.objects.create(
            symbol='USDC',
            name='USD Coin',
            is_active=True,
            volatility_tier='LOW'
        )
        
        # Create lending reserves
        self.btc_reserve = LendingReserve.objects.create(
            cryptocurrency=self.btc,
            ltv=Decimal('0.70'),
            liquidation_threshold=Decimal('0.75'),
            can_be_collateral=True,
            can_borrow=False
        )
        self.eth_reserve = LendingReserve.objects.create(
            cryptocurrency=self.eth,
            ltv=Decimal('0.80'),
            liquidation_threshold=Decimal('0.82'),
            can_be_collateral=True,
            can_borrow=False
        )
        self.usdc_reserve = LendingReserve.objects.create(
            cryptocurrency=self.usdc,
            ltv=Decimal('0.90'),
            liquidation_threshold=Decimal('0.92'),
            can_be_collateral=True,
            can_borrow=True
        )
        
        # Test prices
        self.prices = {
            'BTC': Decimal('50000.00'),
            'ETH': Decimal('3000.00'),
            'USDC': Decimal('1.00')
        }
    
    def test_total_collateral_usd(self):
        """Test collateral calculation with weighted liquidation threshold"""
        supplies = [
            (self.btc_reserve, Decimal('1.0'), True),  # $50,000 collateral
            (self.eth_reserve, Decimal('10.0'), True), # $30,000 collateral
            (self.usdc_reserve, Decimal('1000.0'), False) # Not used as collateral
        ]
        
        coll_usd, w_liq_th = total_collateral_usd(supplies, self.prices)
        
        # Total collateral: $50,000 + $30,000 = $80,000
        self.assertEqual(coll_usd, Decimal('80000.00'))
        
        # Weighted liquidation threshold:
        # BTC: $50,000 * 0.75 = $37,500
        # ETH: $30,000 * 0.82 = $24,600
        # Total: $62,100 / $80,000 = 0.77625
        expected_w_liq = (Decimal('50000') * Decimal('0.75') + Decimal('30000') * Decimal('0.82')) / Decimal('80000')
        self.assertAlmostEqual(w_liq_th, expected_w_liq, places=4)
    
    def test_weighted_ltv(self):
        """Test weighted LTV calculation"""
        supplies = [
            (self.btc_reserve, Decimal('1.0'), True),  # $50,000
            (self.eth_reserve, Decimal('10.0'), True), # $30,000
        ]
        
        w_ltv = weighted_ltv(supplies, self.prices)
        
        # Weighted LTV:
        # BTC: $50,000 * 0.70 = $35,000
        # ETH: $30,000 * 0.80 = $24,000
        # Total: $59,000 / $80,000 = 0.7375
        expected_w_ltv = (Decimal('50000') * Decimal('0.70') + Decimal('30000') * Decimal('0.80')) / Decimal('80000')
        self.assertAlmostEqual(w_ltv, expected_w_ltv, places=4)
    
    def test_total_debt_usd(self):
        """Test total debt calculation"""
        borrows = [
            (self.usdc_reserve, Decimal('10000.0')),  # $10,000 USDC
        ]
        
        debt_usd = total_debt_usd(borrows, self.prices)
        self.assertEqual(debt_usd, Decimal('10000.00'))
    
    def test_available_borrow_usd(self):
        """Test available borrow calculation"""
        collateral_usd = Decimal('80000.00')
        w_ltv = Decimal('0.7375')
        debt_usd = Decimal('10000.00')
        
        avail = available_borrow_usd(collateral_usd, w_ltv, debt_usd)
        
        # Available = (collateral * LTV) - debt = (80000 * 0.7375) - 10000 = 49000
        expected = Decimal('80000') * Decimal('0.7375') - Decimal('10000')
        self.assertEqual(avail, expected)
    
    def test_health_factor(self):
        """Test health factor calculation"""
        collateral_usd = Decimal('80000.00')
        w_liq_th = Decimal('0.77625')
        debt_usd = Decimal('10000.00')
        
        hf = health_factor(collateral_usd, w_liq_th, debt_usd)
        
        # HF = (collateral * liq_threshold) / debt = (80000 * 0.77625) / 10000 = 6.21
        expected = (Decimal('80000') * Decimal('0.77625')) / Decimal('10000')
        self.assertEqual(hf, expected)
    
    def test_health_factor_no_debt(self):
        """Test health factor with no debt (should be infinite)"""
        collateral_usd = Decimal('80000.00')
        w_liq_th = Decimal('0.77625')
        debt_usd = Decimal('0.00')
        
        hf = health_factor(collateral_usd, w_liq_th, debt_usd)
        self.assertEqual(hf, Decimal('999999999'))
    
    def test_hf_tier_determination(self):
        """Test health factor tier determination"""
        # Test different HF values
        self.assertEqual(hf_tier(Decimal('3.0')), 'SAFE')
        self.assertEqual(hf_tier(Decimal('1.5')), 'WARN')
        self.assertEqual(hf_tier(Decimal('1.1')), 'TOP_UP')
        self.assertEqual(hf_tier(Decimal('1.02')), 'AT_RISK')
        self.assertEqual(hf_tier(Decimal('0.8')), 'LIQUIDATE')
    
    def test_hf_tier_hysteresis(self):
        """Test tier hysteresis to prevent flickering"""
        # Test hysteresis around WARN/TOP_UP boundary
        self.assertEqual(hf_tier(Decimal('1.20'), 'SAFE'), 'SAFE')  # Should stay in SAFE
        self.assertEqual(hf_tier(Decimal('1.20'), 'WARN'), 'WARN')  # Should stay in WARN
        self.assertEqual(hf_tier(Decimal('1.20'), 'TOP_UP'), 'TOP_UP')  # Should stay in TOP_UP
    
    def test_stress_testing(self):
        """Test stress testing with price shocks"""
        supplies = [
            (self.btc_reserve, Decimal('1.0'), True),
            (self.eth_reserve, Decimal('10.0'), True),
        ]
        borrows = [
            (self.usdc_reserve, Decimal('10000.0')),
        ]
        
        results = stress_test_hf(supplies, borrows, self.prices, shocks=[-0.2, -0.3, -0.5])
        
        self.assertEqual(len(results), 3)
        
        # Test that shocks reduce health factor
        base_hf = health_factor(Decimal('80000'), Decimal('0.77625'), Decimal('10000'))
        for result in results:
            self.assertLess(result.health_factor, float(base_hf))
            self.assertIn(result.tier, ['SAFE', 'WARN', 'TOP_UP', 'AT_RISK', 'LIQUIDATE'])
    
    def test_repay_to_target_hf(self):
        """Test repay amount calculation to reach target HF"""
        collateral_usd = Decimal('80000.00')
        w_liq_th = Decimal('0.77625')
        debt_usd = Decimal('10000.00')
        target_hf = Decimal('2.0')
        
        repay_amount = repay_to_target_hf(collateral_usd, w_liq_th, debt_usd, target_hf)
        
        # Should calculate correct repay amount
        self.assertGreater(repay_amount, Decimal('0'))
        self.assertLessEqual(repay_amount, debt_usd)
    
    def test_add_collateral_to_target_hf(self):
        """Test additional collateral needed to reach target HF"""
        collateral_usd = Decimal('80000.00')
        w_liq_th = Decimal('0.77625')
        debt_usd = Decimal('10000.00')
        target_hf = Decimal('2.0')
        
        additional_collateral = add_collateral_to_target_hf(collateral_usd, w_liq_th, debt_usd, target_hf)
        
        # Should calculate additional collateral needed
        self.assertGreaterEqual(additional_collateral, Decimal('0'))
    
    def test_risk_color_and_message(self):
        """Test risk color and message functions"""
        # Test colors
        self.assertEqual(risk_color('SAFE'), '#10B981')
        self.assertEqual(risk_color('WARN'), '#F59E0B')
        self.assertEqual(risk_color('TOP_UP'), '#EF4444')
        self.assertEqual(risk_color('AT_RISK'), '#DC2626')
        self.assertEqual(risk_color('LIQUIDATE'), '#7C2D12')
        
        # Test messages
        self.assertIn('Healthy', risk_message('SAFE', 2.5))
        self.assertIn('Monitor closely', risk_message('WARN', 1.5))
        self.assertIn('Consider adding', risk_message('TOP_UP', 1.1))
        self.assertIn('Immediate action', risk_message('AT_RISK', 1.02))
        self.assertIn('Liquidation risk', risk_message('LIQUIDATE', 0.8))
    
    def test_calculate_lending_account_data(self):
        """Test the legacy compatibility function"""
        # Create supply positions
        btc_supply = SupplyPosition.objects.create(
            user=self.user,
            reserve=self.btc_reserve,
            quantity=Decimal('1.0'),
            use_as_collateral=True
        )
        eth_supply = SupplyPosition.objects.create(
            user=self.user,
            reserve=self.eth_reserve,
            quantity=Decimal('10.0'),
            use_as_collateral=True
        )
        
        # Create borrow position
        usdc_borrow = BorrowPosition.objects.create(
            user=self.user,
            reserve=self.usdc_reserve,
            amount=Decimal('10000.0'),
            rate_mode='VARIABLE',
            is_active=True
        )
        
        supplies = [btc_supply, eth_supply]
        borrows = [usdc_borrow]
        
        account_data = calculate_lending_account_data(supplies, borrows, self.prices)
        
        # Verify calculated values
        self.assertEqual(account_data.total_collateral_usd, Decimal('80000.00'))
        self.assertEqual(account_data.total_debt_usd, Decimal('10000.00'))
        self.assertGreater(account_data.health_factor, Decimal('1.0'))
        self.assertIn(account_data.health_factor_tier, ['SAFE', 'WARN', 'TOP_UP', 'AT_RISK', 'LIQUIDATE'])
        self.assertGreater(account_data.available_borrow_usd, Decimal('0'))
    
    def test_edge_cases(self):
        """Test edge cases and error conditions"""
        # Test with zero collateral
        supplies = []
        coll_usd, w_liq_th = total_collateral_usd(supplies, self.prices)
        self.assertEqual(coll_usd, Decimal('0'))
        self.assertEqual(w_liq_th, Decimal('0'))
        
        # Test with zero debt
        borrows = []
        debt_usd = total_debt_usd(borrows, self.prices)
        self.assertEqual(debt_usd, Decimal('0'))
        
        # Test with missing prices
        supplies = [(self.btc_reserve, Decimal('1.0'), True)]
        empty_prices = {}
        coll_usd, w_liq_th = total_collateral_usd(supplies, empty_prices)
        self.assertEqual(coll_usd, Decimal('0'))
        
        # Test with non-collateral reserves
        non_collateral_reserve = MockReserve('TEST', can_be_collateral=False)
        supplies = [(non_collateral_reserve, Decimal('1000.0'), True)]
        coll_usd, w_liq_th = total_collateral_usd(supplies, {'TEST': Decimal('1.0')})
        self.assertEqual(coll_usd, Decimal('0'))
