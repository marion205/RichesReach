"""
Tests for DeFi EIP-712 spend permission, execution payload decimals, and repair auto-approval.
"""
from decimal import Decimal
from unittest.mock import Mock, patch
from django.test import TestCase
from graphene import ResolveInfo
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.autopilot_service import (
    _symbol_to_decimals,
    _has_valid_eip712_spend_permission,
    execute_repair,
    get_pending_repairs,
    set_autopilot_enabled,
    _policy_key,
)
from core.eip712_spend_permission import get_spend_permission_typed_data, verify_signature
from core.defi_models import DeFiSpendPermission, DeFiPool, DeFiProtocol, UserDeFiPosition
from core.defi_mutations import SubmitSpendPermission

User = get_user_model()


class SymbolToDecimalsTests(TestCase):
    """Test _symbol_to_decimals mapping."""

    def test_usdc_returns_6(self):
        self.assertEqual(_symbol_to_decimals('USDC'), 6)
        self.assertEqual(_symbol_to_decimals('usdc'), 6)

    def test_usdt_dai_return_6(self):
        self.assertEqual(_symbol_to_decimals('USDT'), 6)
        self.assertEqual(_symbol_to_decimals('DAI'), 6)

    def test_wbtc_weth_return_18(self):
        self.assertEqual(_symbol_to_decimals('WBTC'), 18)
        self.assertEqual(_symbol_to_decimals('WETH'), 18)

    def test_unknown_returns_18(self):
        self.assertEqual(_symbol_to_decimals('ETH'), 18)
        self.assertEqual(_symbol_to_decimals(''), 18)
        self.assertEqual(_symbol_to_decimals(None), 18)


class EIP712TypedDataTests(TestCase):
    """Test get_spend_permission_typed_data structure."""

    def test_returns_typed_data_structure(self):
        data = get_spend_permission_typed_data(
            chain_id=137,
            max_amount_wei='500000000',
            token_address='0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
            valid_until_seconds=2000000000,
            nonce='123',
        )
        self.assertIn('domain', data)
        self.assertIn('message', data)
        self.assertIn('types', data)
        self.assertEqual(data['domain'].get('name'), 'RichesReach')
        self.assertEqual(data['message']['chainId'], 137)
        self.assertEqual(data['message']['maxAmountWei'], '500000000')
        self.assertEqual(data['message']['validUntil'], 2000000000)


class HasValidEIP712SpendPermissionTests(TestCase):
    """Test _has_valid_eip712_spend_permission with DB."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='spendperm@test.com',
            password='testpass123',
            name='Spend Perm User',
        )
        self.wallet = '0x1234567890123456789012345678901234567890'
        self.chain_id = 137

    def test_no_permission_returns_false(self):
        self.assertFalse(
            _has_valid_eip712_spend_permission(
                self.user, self.wallet, self.chain_id, 100_000_000
            )
        )

    def test_valid_permission_within_limit_returns_true(self):
        DeFiSpendPermission.objects.create(
            user=self.user,
            wallet_address=self.wallet,
            chain_id=self.chain_id,
            max_amount_wei='500000000',
            token_address='0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
            valid_until=timezone.now() + timezone.timedelta(days=30),
            nonce='1',
            signature='0x',
        )
        self.assertTrue(
            _has_valid_eip712_spend_permission(
                self.user, self.wallet, self.chain_id, 100_000_000
            )
        )

    def test_valid_permission_over_limit_returns_false(self):
        DeFiSpendPermission.objects.create(
            user=self.user,
            wallet_address=self.wallet,
            chain_id=self.chain_id,
            max_amount_wei='100',
            token_address='0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
            valid_until=timezone.now() + timezone.timedelta(days=30),
            nonce='2',
            signature='0x',
        )
        self.assertFalse(
            _has_valid_eip712_spend_permission(
                self.user, self.wallet, self.chain_id, 100_000_000
            )
        )

    def test_expired_permission_returns_false(self):
        DeFiSpendPermission.objects.create(
            user=self.user,
            wallet_address=self.wallet,
            chain_id=self.chain_id,
            max_amount_wei='500000000',
            token_address='0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
            valid_until=timezone.now() - timezone.timedelta(days=1),
            nonce='3',
            signature='0x',
        )
        self.assertFalse(
            _has_valid_eip712_spend_permission(
                self.user, self.wallet, self.chain_id, 100_000_000
            )
        )


class _FakeCache:
    """In-memory cache so tests don't require Redis."""

    def __init__(self):
        self._data = {}

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value, timeout=None):
        self._data[key] = value


class ExecuteRepairPayloadTests(TestCase):
    """Test execute_repair returns execution_payload with decimals and withinSpendPermission."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='repair@test.com',
            password='testpass123',
            name='Repair User',
        )
        self.protocol = DeFiProtocol.objects.create(
            name='Test Protocol',
            slug='test-protocol',
            risk_score=0.2,
        )
        self.from_pool = DeFiPool.objects.create(
            protocol=self.protocol,
            chain='polygon',
            chain_id=137,
            symbol='USDC',
            pool_address='0xFromVault1111111111111111111111111111111111',
            pool_type='vault',
        )
        self.to_pool = DeFiPool.objects.create(
            protocol=self.protocol,
            chain='polygon',
            chain_id=137,
            symbol='USDC',
            pool_address='0xToVault2222222222222222222222222222222222',
            pool_type='vault',
        )
        self.wallet = '0x1234567890123456789012345678901234567890'
        self.position = UserDeFiPosition.objects.create(
            user=self.user,
            pool=self.from_pool,
            wallet_address=self.wallet,
            staked_amount=Decimal('100.5'),
            staked_value_usd=Decimal('100.5'),
            realized_apy=0.05,
        )
        # Do not call set_autopilot_enabled here: it would use Redis. We do it inside the test with a fake cache.

    def test_execution_payload_includes_decimals(self):
        # repair_id format: position_id:to_pool_id (target pool for the move)
        repair_id = f'{self.position.id}:{self.to_pool.id}'
        fake_repairs = [{
            'id': repair_id,
            'from_vault': 'From',
            'to_vault': 'To',
            'from_pool_id': self.from_pool.id,
            'to_pool_id': self.to_pool.id,
            'estimated_apy_delta': 0.5,
            'proof': {},
        }]
        fake_cache = _FakeCache()
        with patch('core.autopilot_service.cache', fake_cache):
            set_autopilot_enabled(self.user, True)
            with patch('core.autopilot_service.get_pending_repairs', return_value=fake_repairs):
                result = execute_repair(self.user, repair_id)

        self.assertTrue(result.get('success'))
        payload = result.get('execution_payload')
        self.assertIsNotNone(payload)
        self.assertIn('decimals', payload)
        self.assertEqual(payload['decimals'], 6)  # USDC
        self.assertIn('withinSpendPermission', payload)
        self.assertIn('amountHuman', payload)
        self.assertEqual(float(payload['amountHuman']), 100.5)


def _make_resolve_info(user):
    """Build a minimal ResolveInfo so @login_required finds it (no StopIteration)."""
    ctx = Mock()
    ctx.user = user
    return ResolveInfo(
        field_name='mutate',
        field_nodes=[],
        return_type=Mock(),
        parent_type=Mock(),
        path=Mock(),
        schema=Mock(),
        fragments={},
        root_value=None,
        operation=Mock(),
        variable_values={},
        context=ctx,
        is_awaitable=False,
    )


class SubmitSpendPermissionMutationTests(TestCase):
    """Test SubmitSpendPermission with snake_case and camelCase args."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='submitperm@test.com',
            password='testpass123',
            name='Submit Perm User',
        )
        self.info = _make_resolve_info(self.user)

    @patch('core.eip712_spend_permission.verify_signature')
    def test_submit_snake_case_success(self, mock_verify):
        mock_verify.return_value = True
        result = SubmitSpendPermission.mutate(
            None,
            self.info,
            wallet_address='0x1234567890123456789012345678901234567890',
            chain_id=137,
            max_amount_wei='500000000',
            token_address='0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
            valid_until_seconds=2000000000,
            nonce='42',
            signature='0xsignature',
            raw_typed_data=None,
            walletAddress=None,
            chainId=None,
            maxAmountWei=None,
            tokenAddress=None,
            validUntilSeconds=None,
            rawTypedData=None,
        )
        self.assertTrue(result.ok)
        self.assertIn('Spend permission stored', result.message)
        self.assertEqual(DeFiSpendPermission.objects.filter(user=self.user).count(), 1)

    @patch('core.eip712_spend_permission.verify_signature')
    def test_submit_camelCase_success(self, mock_verify):
        mock_verify.return_value = True
        result = SubmitSpendPermission.mutate(
            None,
            self.info,
            wallet_address=None,
            chain_id=None,
            max_amount_wei=None,
            token_address=None,
            valid_until_seconds=None,
            nonce='43',
            signature='0xsignature2',
            raw_typed_data=None,
            walletAddress='0x1234567890123456789012345678901234567890',
            chainId=42161,
            maxAmountWei='1000000000',
            tokenAddress='0xaf88d065e77c8cC2239327C5Bb45045926D470c77',
            validUntilSeconds=2000000000,
            rawTypedData=None,
        )
        self.assertTrue(result.ok)
        perm = DeFiSpendPermission.objects.get(user=self.user, nonce='43')
        self.assertEqual(perm.chain_id, 42161)
        self.assertEqual(perm.max_amount_wei, '1000000000')

    def test_submit_missing_args_returns_error(self):
        result = SubmitSpendPermission.mutate(
            None,
            self.info,
            wallet_address=None,
            chain_id=None,
            max_amount_wei=None,
            token_address=None,
            valid_until_seconds=None,
            nonce=None,
            signature=None,
            raw_typed_data=None,
            walletAddress=None,
            chainId=None,
            maxAmountWei=None,
            tokenAddress=None,
            validUntilSeconds=None,
            rawTypedData=None,
        )
        self.assertFalse(result.ok)
        self.assertIn('Missing required', result.message)
