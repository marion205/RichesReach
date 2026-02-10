"""
Tests for DeFi relayer circuit breaker (gas spike pause) and audit/push:
- is_relayer_paused, set_relayer_paused, relayer_submission_allowed, check_relayer_gas_spike
- ReportRepairExecutedOnChain mutation (audit + notify_funds_moved)
- SubmitRepairViaRelayer with repair_id (tx_hash update + push)
- notify_funds_moved (push payload and deep link data)

Run: python manage.py test core.tests.test_defi_circuit_breaker_and_audit -v 2
"""
from decimal import Decimal
from unittest.mock import Mock, patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from graphene import ResolveInfo

from core.defi_circuit_breaker import (
    is_relayer_paused,
    set_relayer_paused,
    relayer_submission_allowed,
    check_relayer_gas_spike,
    record_gas_for_relayer,
    _get_relayer_baseline_gwei,
    RELAYER_REDIS_PREFIX,
    RELAYER_BASELINE_MIN_AGE_SECONDS,
)
from core.defi_mutations import SubmitRepairViaRelayer, ReportRepairExecutedOnChain
from core.defi_models import (
    DeFiRepairDecision,
    DeFiPool,
    DeFiProtocol,
    UserDeFiPosition,
    DeFiNotificationPreferences,
)

User = get_user_model()


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


class FakeCache:
    """In-memory cache for testing Redis-backed relayer circuit breaker."""

    def __init__(self):
        self.data = {}
        self.list_data = {}

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value, timeout=None):
        self.data[key] = value

    def lpush(self, key, *values):
        self.list_data.setdefault(key, [])
        for v in reversed(values):
            self.list_data[key].insert(0, v)

    def lrange(self, key, start, end):
        lst = self.list_data.get(key, [])
        if end == -1:
            end = len(lst)
        return lst[start : end + 1]

    def ltrim(self, key, start, end):
        if key not in self.list_data:
            return
        lst = self.list_data[key]
        if end == -1:
            end = len(lst) - 1
        self.list_data[key] = lst[start : end + 1]


class RelayerCircuitBreakerTests(TestCase):
    """Test relayer pause and gas spike detection with mocked cache."""

    def setUp(self):
        self.cache = FakeCache()

    @patch('core.defi_circuit_breaker._get_redis')
    def test_is_relayer_paused_false_when_not_set(self, mock_get_redis):
        mock_get_redis.return_value = self.cache
        self.assertFalse(is_relayer_paused(8453))

    @patch('core.defi_circuit_breaker._get_redis')
    def test_set_relayer_paused_and_is_relayer_paused(self, mock_get_redis):
        mock_get_redis.return_value = self.cache
        set_relayer_paused(8453, ttl_seconds=60)
        self.assertTrue(is_relayer_paused(8453))
        self.assertEqual(self.cache.get(f'{RELAYER_REDIS_PREFIX}:paused:8453'), '1')

    @patch('core.defi_circuit_breaker._get_redis')
    def test_relayer_submission_allowed_when_paused_returns_false(self, mock_get_redis):
        mock_get_redis.return_value = self.cache
        set_relayer_paused(42161, ttl_seconds=60)
        out = relayer_submission_allowed(42161, 5.0)
        self.assertFalse(out['allowed'])
        self.assertIn('paused', out['reason'].lower())

    @patch('core.defi_circuit_breaker._get_redis')
    @patch('core.defi_circuit_breaker.is_halted')
    def test_relayer_submission_allowed_when_not_paused_no_baseline(self, mock_halted, mock_get_redis):
        mock_get_redis.return_value = self.cache
        mock_halted.return_value = False
        out = relayer_submission_allowed(8453, 10.0)
        self.assertTrue(out['allowed'])
        self.assertEqual(out['reason'], '')

    @patch('core.defi_circuit_breaker._get_redis')
    def test_get_baseline_empty_returns_none(self, mock_get_redis):
        mock_get_redis.return_value = self.cache
        gwei, age = _get_relayer_baseline_gwei(1)
        self.assertIsNone(gwei)
        self.assertIsNone(age)

    @patch('core.defi_circuit_breaker._get_redis')
    def test_record_gas_and_baseline_age(self, mock_get_redis):
        mock_get_redis.return_value = self.cache
        import json
        from django.utils import timezone as tz
        now = tz.now().timestamp()
        old_ts = now - (RELAYER_BASELINE_MIN_AGE_SECONDS + 60)  # > 4 min ago
        self.cache.lpush(
            f'{RELAYER_REDIS_PREFIX}:gas_history:8453',
            json.dumps({'ts': old_ts, 'gwei': 2.0}),
        )
        gwei, age = _get_relayer_baseline_gwei(8453)
        self.assertIsNotNone(gwei)
        self.assertEqual(gwei, 2.0)
        self.assertGreaterEqual(age, RELAYER_BASELINE_MIN_AGE_SECONDS)

    @patch('core.defi_circuit_breaker._get_redis')
    @patch('core.defi_circuit_breaker.is_halted')
    def test_check_relayer_gas_spike_true_when_current_3x_baseline(self, mock_halted, mock_get_redis):
        mock_get_redis.return_value = self.cache
        mock_halted.return_value = False
        import json
        from django.utils import timezone as tz
        now = tz.now().timestamp()
        old_ts = now - (RELAYER_BASELINE_MIN_AGE_SECONDS + 120)
        self.cache.lpush(
            f'{RELAYER_REDIS_PREFIX}:gas_history:8453',
            json.dumps({'ts': old_ts, 'gwei': 3.0}),
        )
        # current 10 gwei >= 3 * 3 = 9
        self.assertTrue(check_relayer_gas_spike(8453, 10.0))

    @patch('core.defi_circuit_breaker._get_redis')
    @patch('core.defi_circuit_breaker.is_halted')
    def test_relayer_submission_allowed_false_on_gas_spike(self, mock_halted, mock_get_redis):
        mock_get_redis.return_value = self.cache
        mock_halted.return_value = False
        import json
        from django.utils import timezone as tz
        now = tz.now().timestamp()
        old_ts = now - (RELAYER_BASELINE_MIN_AGE_SECONDS + 120)
        self.cache.lpush(
            f'{RELAYER_REDIS_PREFIX}:gas_history:8453',
            json.dumps({'ts': old_ts, 'gwei': 2.0}),
        )
        out = relayer_submission_allowed(8453, 10.0)  # 10 >= 3*2
        self.assertFalse(out['allowed'])
        self.assertIn('spiked', out['reason'].lower())
        self.assertTrue(is_relayer_paused(8453))


class ReportRepairExecutedOnChainTests(TestCase):
    """Test ReportRepairExecutedOnChain mutation: updates tx_hash and sends notify_funds_moved."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='audit@test.com',
            password='testpass123',
            name='Audit User',
        )
        self.protocol = DeFiProtocol.objects.create(
            name='Test Protocol',
            slug='test-protocol',
            risk_score=0.2,
        )
        self.pool_from = DeFiPool.objects.create(
            protocol=self.protocol,
            chain='polygon',
            chain_id=137,
            symbol='USDC',
            pool_address='0xFromVault1111111111111111111111111111111111',
            pool_type='vault',
        )
        self.pool_to = DeFiPool.objects.create(
            protocol=self.protocol,
            chain='polygon',
            chain_id=137,
            symbol='USDC',
            pool_address='0xToVault2222222222222222222222222222222222',
            pool_type='vault',
        )
        self.position = UserDeFiPosition.objects.create(
            user=self.user,
            pool=self.pool_from,
            wallet_address='0x1234567890123456789012345678901234567890',
            staked_amount=Decimal('100'),
            staked_value_usd=Decimal('100'),
            realized_apy=0.05,
        )
        self.repair_id = f'{self.position.id}:{self.pool_to.id}'
        self.decision = DeFiRepairDecision.objects.create(
            user=self.user,
            position=self.position,
            from_pool=self.pool_from,
            to_pool=self.pool_to,
            repair_id=self.repair_id,
            decision_type='executed',
            tx_hash='',
            executed_at=timezone.now(),
        )
        self.info = _make_resolve_info(self.user)

    @patch('core.autopilot_service.cache', new_callable=FakeCache)
    @patch('core.autopilot_notification_service.get_autopilot_notification_service')
    def test_report_updates_tx_hash_and_calls_notify(self, mock_get_service, _mock_cache):
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        mock_service.notify_funds_moved = Mock(return_value=True)

        result = ReportRepairExecutedOnChain.mutate(
            None, self.info, repair_id=self.repair_id, tx_hash='0xabc123'
        )

        self.assertTrue(result.ok)
        self.decision.refresh_from_db()
        self.assertEqual(self.decision.tx_hash, '0xabc123')
        mock_service.notify_funds_moved.assert_called_once()
        call_kw = mock_service.notify_funds_moved.call_args[1]
        self.assertEqual(call_kw['repair_id'], self.repair_id)
        self.assertEqual(call_kw['tx_hash'], '0xabc123')

    def test_report_repair_not_found_returns_ok_false(self):
        result = ReportRepairExecutedOnChain.mutate(
            None, self.info, repair_id='nonexistent:id', tx_hash='0xabc'
        )
        self.assertFalse(result.ok)
        self.assertIn('not found', result.message.lower())


class SubmitRepairViaRelayerAuditTests(TestCase):
    """Test that SubmitRepairViaRelayer with repair_id updates audit and sends push on success."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='relayer@test.com',
            password='testpass123',
            name='Relayer User',
        )
        self.protocol = DeFiProtocol.objects.create(
            name='Test Protocol',
            slug='test-protocol',
            risk_score=0.2,
        )
        self.pool_from = DeFiPool.objects.create(
            protocol=self.protocol,
            chain='base',
            chain_id=8453,
            symbol='USDC',
            pool_address='0xFromVault1111111111111111111111111111111111',
            pool_type='vault',
        )
        self.pool_to = DeFiPool.objects.create(
            protocol=self.protocol,
            chain='base',
            chain_id=8453,
            symbol='USDC',
            pool_address='0xToVault2222222222222222222222222222222222',
            pool_type='vault',
        )
        self.position = UserDeFiPosition.objects.create(
            user=self.user,
            pool=self.pool_from,
            wallet_address='0x1234567890123456789012345678901234567890',
            staked_amount=Decimal('50'),
            staked_value_usd=Decimal('50'),
            realized_apy=0.05,
        )
        self.repair_id = f'{self.position.id}:{self.pool_to.id}'
        self.decision = DeFiRepairDecision.objects.create(
            user=self.user,
            position=self.position,
            from_pool=self.pool_from,
            to_pool=self.pool_to,
            repair_id=self.repair_id,
            decision_type='executed',
            tx_hash='',
            executed_at=timezone.now(),
        )
        self.info = _make_resolve_info(self.user)

    @patch('core.repair_relayer.submit_repair_via_relayer')
    @patch('core.autopilot_service.get_last_move')
    @patch('core.autopilot_notification_service.get_autopilot_notification_service')
    def test_submit_with_repair_id_updates_tx_hash_and_sends_push(
        self, mock_get_notif, mock_get_last_move, mock_submit
    ):
        mock_submit.return_value = {'success': True, 'tx_hash': '0xrelayerhash'}
        mock_get_last_move.return_value = {
            'id': self.repair_id,
            'from_vault': 'FromVault',
            'to_vault': 'ToVault',
        }
        mock_service = Mock()
        mock_get_notif.return_value = mock_service
        mock_service.notify_funds_moved = Mock(return_value=True)

        result = SubmitRepairViaRelayer.mutate(
            None,
            self.info,
            user_address=self.position.wallet_address,
            chain_id=8453,
            from_vault=self.pool_from.pool_address,
            to_vault=self.pool_to.pool_address,
            amount_wei='50000000',
            deadline=0,
            nonce=0,
            signature='0xdeadbeef',
            repair_id=self.repair_id,
        )

        self.assertTrue(result.success)
        self.assertEqual(result.tx_hash, '0xrelayerhash')
        self.decision.refresh_from_db()
        self.assertEqual(self.decision.tx_hash, '0xrelayerhash')
        mock_service.notify_funds_moved.assert_called_once()
        call_kw = mock_service.notify_funds_moved.call_args[1]
        self.assertEqual(call_kw['repair_id'], self.repair_id)
        self.assertEqual(call_kw['tx_hash'], '0xrelayerhash')


class NotifyFundsMovedTests(TestCase):
    """Test autopilot_notification_service.notify_funds_moved."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='push@test.com',
            password='testpass123',
            name='Push User',
        )
        DeFiNotificationPreferences.objects.create(
            user=self.user,
            push_token='ExponentPushToken[test]',
            push_enabled=True,
            repair_alerts_enabled=True,
        )

    @patch('core.autopilot_notification_service.AutopilotNotificationService._send_push_notification')
    def test_notify_funds_moved_sends_with_amount(self, mock_send):
        from core.autopilot_notification_service import AutopilotNotificationService

        mock_send.return_value = True
        service = AutopilotNotificationService()

        result = service.notify_funds_moved(
            self.user,
            repair_id='1:2',
            from_vault='VaultA',
            to_vault='VaultB',
            amount_usd=100.5,
            tx_hash='0xabc',
        )

        self.assertTrue(result)
        mock_send.assert_called_once()
        kwargs = mock_send.call_args[1]
        self.assertEqual(kwargs['title'], 'Funds moved to safer vault')
        self.assertIn('100', kwargs['body'])
        self.assertIn('proof', kwargs['body'].lower())
        data = kwargs.get('data')
        self.assertIsNotNone(data)
        self.assertEqual(data.get('type'), 'autopilot_funds_moved')
        self.assertEqual(data.get('repair_id'), '1:2')
        self.assertEqual(data.get('screen'), 'DeFiAutopilot')
        self.assertEqual(data.get('tx_hash'), '0xabc')
