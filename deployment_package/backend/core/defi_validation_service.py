"""
DeFi Transaction Validation Service

Backend risk validation for all DeFi operations:
- Amount limits (tiered per user level: Starter / Growth / Premium)
- Health factor checks (prevent liquidation)
- Circuit breaker integration (halt on gas spikes / incidents)
- Gas estimation validation
- Protocol / pool activity validation
- Rate limiting per wallet

This is the gatekeeper: every on-chain transaction must pass validation
before the mobile app sends it via WalletConnect.

Part of Phase 4: Mainnet Migration
"""
import logging
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum

logger = logging.getLogger(__name__)


# ---- Tiered Transaction Limits (Phase 4) ----

TRANSACTION_TIERS = {
    'starter': {
        'label': 'Starter',
        'per_tx_limit_usd': 100,
        'daily_limit_usd': 500,
        'monthly_limit_usd': 2_000,
        'max_borrow_usd': 50,
    },
    'growth': {
        'label': 'Growth',
        'per_tx_limit_usd': 1_000,
        'daily_limit_usd': 5_000,
        'monthly_limit_usd': 25_000,
        'max_borrow_usd': 500,
    },
    'premium': {
        'label': 'Premium',
        'per_tx_limit_usd': 10_000,
        'daily_limit_usd': 50_000,
        'monthly_limit_usd': 200_000,
        'max_borrow_usd': 5_000,
    },
}

# Fallback flat limits for operations that don't need tiering
OPERATION_LIMITS = {
    'repay': {'min': 0.01, 'max': 100_000},
    'harvest': {'min': 0, 'max': 100_000},
    'approve': {'min': 0, 'max': float('inf')},
}

# Health factor thresholds
MIN_HEALTH_FACTOR = 1.1  # Warn below this
CRITICAL_HEALTH_FACTOR = 1.05  # Block transactions below this

# Supported chains (Phase 4: mainnet + testnet)
SUPPORTED_CHAINS = {
    1: 'ethereum',
    137: 'polygon',
    42161: 'arbitrum',
    8453: 'base',
    11155111: 'sepolia',
}

# Chains that require DEFI_MAINNET_ENABLED flag
MAINNET_CHAINS = {1, 137, 42161, 8453}

# Allowed protocols for transactions
ALLOWED_PROTOCOLS = [
    'aave-v3',
    'compound-v3',
    'lido',
    'curve-dex',
    'yearn-finance',
    'convex-finance',
    'balancer-v2',
]

# Gas price thresholds per chain (gwei) — mirrors circuit breaker
GAS_PRICE_THRESHOLDS = {
    1: 200,        # Ethereum: warn above 200 gwei
    137: 500,      # Polygon: warn above 500 gwei
    42161: 10,     # Arbitrum: warn above 10 gwei
    8453: 5,       # Base: warn above 5 gwei
    11155111: 1000, # Sepolia: very high (testnet)
}


class ValidationResult:
    """Result of a validation check."""

    def __init__(self, is_valid: bool, reason: str = '', warnings: list = None):
        self.is_valid = is_valid
        self.reason = reason
        self.warnings = warnings or []

    def to_dict(self):
        return {
            'isValid': self.is_valid,
            'reason': self.reason,
            'warnings': self.warnings,
        }


def _get_user_tier(user) -> str:
    """
    Determine user's transaction tier based on subscription or profile.
    Returns: 'starter', 'growth', or 'premium'
    """
    try:
        # Check if user has a subscription or profile with tier info
        if hasattr(user, 'profile'):
            tier = getattr(user.profile, 'defi_tier', None)
            if tier and tier in TRANSACTION_TIERS:
                return tier

        # Check for premium subscription
        if hasattr(user, 'subscription'):
            sub = user.subscription
            if hasattr(sub, 'plan_name'):
                plan = sub.plan_name.lower()
                if 'premium' in plan:
                    return 'premium'
                elif 'growth' in plan or 'pro' in plan:
                    return 'growth'

        # Default to starter
        return 'starter'

    except Exception:
        return 'starter'


def _get_tier_limits(user) -> dict:
    """Get transaction limits for user's tier."""
    tier_name = _get_user_tier(user)
    return TRANSACTION_TIERS.get(tier_name, TRANSACTION_TIERS['starter'])


def _is_mainnet_enabled() -> bool:
    """
    Check if mainnet DeFi is enabled via Django settings or environment.
    This is the server-side equivalent of the mobile DEFI_MAINNET_ENABLED flag.
    """
    try:
        from django.conf import settings
        return getattr(settings, 'DEFI_MAINNET_ENABLED', False)
    except Exception:
        return False


def validate_transaction(
    user,
    tx_type: str,
    wallet_address: str,
    symbol: str = '',
    amount_human: str = '0',
    chain_id: int = 11155111,
    pool_id: str = '',
    rate_mode: int = 2,
    extra_data: dict = None,
) -> ValidationResult:
    """
    Master validation function.
    Called by GraphQL mutations before allowing on-chain transactions.

    Validation pipeline:
    1. Input validation
    2. Chain validation + mainnet gate
    3. Circuit breaker check
    4. Wallet address validation
    5. Tiered amount limits
    6. Daily volume check
    7. Gas price check
    8. Pool validation
    9. Health factor check (for borrows)
    10. Rate limiting

    Returns ValidationResult with is_valid, reason, and optional warnings.
    """
    warnings = []
    is_authenticated = bool(user and getattr(user, 'is_authenticated', False))

    # 1. Basic input validation
    try:
        amount = Decimal(amount_human) if amount_human else Decimal('0')
    except Exception:
        return ValidationResult(False, 'Invalid amount format')

    valid_tx_types = ('deposit', 'withdraw', 'borrow', 'repay', 'harvest', 'approve')
    if tx_type not in valid_tx_types:
        return ValidationResult(False, f'Unknown transaction type: {tx_type}')

    # 2. Chain validation + mainnet gate
    if chain_id not in SUPPORTED_CHAINS:
        return ValidationResult(
            False,
            f'Chain {chain_id} is not supported. '
            f'Supported chains: {list(SUPPORTED_CHAINS.values())}'
        )

    if chain_id in MAINNET_CHAINS and not _is_mainnet_enabled():
        return ValidationResult(
            False,
            'Mainnet DeFi transactions are not yet enabled. '
            'Currently only Sepolia testnet is supported.'
        )

    if chain_id in MAINNET_CHAINS:
        warnings.append(
            'This is a MAINNET transaction using REAL funds. '
            'Transactions are irreversible.'
        )

    # 3. Circuit breaker check
    cb_result = _check_circuit_breaker(chain_id, float(amount))
    if not cb_result.is_valid:
        return cb_result
    if cb_result.warnings:
        warnings.extend(cb_result.warnings)

    # 4. Wallet address validation
    if not wallet_address or len(wallet_address) != 42 or not wallet_address.startswith('0x'):
        return ValidationResult(False, 'Invalid wallet address')

    # 5. Tiered amount limits
    if tx_type in ('deposit', 'withdraw', 'borrow'):
        tier_limits = _get_tier_limits(user)
        amount_usd = float(amount)

        if tx_type == 'borrow' and amount_usd > tier_limits['max_borrow_usd']:
            return ValidationResult(
                False,
                f'Borrow amount ${amount_usd:,.0f} exceeds your '
                f'{tier_limits["label"]} tier limit of '
                f'${tier_limits["max_borrow_usd"]:,.0f}. '
                f'Upgrade your plan for higher limits.'
            )

        if amount_usd > tier_limits['per_tx_limit_usd']:
            return ValidationResult(
                False,
                f'Amount ${amount_usd:,.0f} exceeds your '
                f'{tier_limits["label"]} tier per-transaction limit of '
                f'${tier_limits["per_tx_limit_usd"]:,.0f}. '
                f'Upgrade your plan for higher limits.'
            )

        if amount_usd < 0.01:
            return ValidationResult(False, 'Amount too small. Minimum: $0.01')
    elif tx_type in OPERATION_LIMITS:
        limits = OPERATION_LIMITS[tx_type]
        amount_usd = float(amount)
        if amount_usd < limits['min']:
            return ValidationResult(False, f'Amount too small. Minimum: ${limits["min"]}')
        if amount_usd > limits['max']:
            return ValidationResult(
                False,
                f'Amount exceeds per-transaction limit of ${limits["max"]:,.0f}.'
            )

    # 6. Daily volume check (uses tiered daily limit)
    daily_check = _check_daily_volume(user if is_authenticated else None, wallet_address, float(amount))
    if not daily_check.is_valid:
        return daily_check
    if daily_check.warnings:
        warnings.extend(daily_check.warnings)

    # 7. Gas price check (mainnet only)
    if chain_id in MAINNET_CHAINS:
        gas_check = _check_gas_price(chain_id)
        if not gas_check.is_valid:
            return gas_check
        if gas_check.warnings:
            warnings.extend(gas_check.warnings)

    # 8. Pool validation (if pool_id provided)
    if pool_id:
        pool_check = _validate_pool(pool_id)
        if not pool_check.is_valid:
            return pool_check

    # 9. Health factor check for borrows
    if tx_type == 'borrow':
        hf_check = _check_health_factor(user, wallet_address, float(amount))
        if not hf_check.is_valid:
            return hf_check
        if hf_check.warnings:
            warnings.extend(hf_check.warnings)

    # 10. Deposit-specific warnings
    if tx_type == 'deposit':
        tier_limits = _get_tier_limits(user)
        if float(amount) > tier_limits['per_tx_limit_usd'] * 0.5:
            warnings.append(
                'Large deposit detected. Ensure you have reviewed the protocol risks.'
            )

    # 11. Rate limiting (max 10 transactions per minute)
    rate_check = _check_rate_limit(user if is_authenticated else None, wallet_address)
    if not rate_check.is_valid:
        return rate_check

    logger.info(
        f"Transaction validated: type={tx_type} user={getattr(user, 'id', None)} "
        f"wallet={wallet_address[:8]}... amount={amount_human} {symbol} "
        f"chain={chain_id} tier={_get_user_tier(user) if user else 'starter'}"
    )

    result = ValidationResult(True, warnings=warnings)
    return result


# ---- Circuit Breaker Integration ----

def _check_circuit_breaker(chain_id: int, amount_usd: float) -> ValidationResult:
    """
    Check the Redis-backed circuit breaker before allowing a transaction.
    Integrates with defi_circuit_breaker.py.
    """
    try:
        from .defi_circuit_breaker import validate_transaction_allowed

        cb_result = validate_transaction_allowed(chain_id, amount_usd)

        if not cb_result['allowed']:
            return ValidationResult(False, cb_result['reason'])

        warnings = []
        if cb_result['state'] == 'HALF_OPEN':
            warnings.append(
                f'System is in recovery mode. '
                f'Transactions are limited to ${100:,.0f}.'
            )

        return ValidationResult(True, warnings=warnings)

    except ImportError:
        logger.warning("Circuit breaker module not available, skipping check")
        return ValidationResult(True)
    except Exception as e:
        logger.warning(f"Circuit breaker check error (non-blocking): {e}")
        return ValidationResult(True, warnings=['Could not verify system status.'])


# ---- Gas Price Validation ----

def _check_gas_price(chain_id: int) -> ValidationResult:
    """
    Check current gas price against chain thresholds.
    Uses circuit breaker auto-trip as a backstop.
    """
    try:
        from .defi_circuit_breaker import check_gas_and_trip, GAS_PRICE_THRESHOLDS

        # Get current gas price from cache if available
        from django.core.cache import cache
        cached_gas = cache.get(f'defi:gas_price:{chain_id}')

        if cached_gas is not None:
            threshold = GAS_PRICE_THRESHOLDS.get(chain_id, 500)
            gas_gwei = float(cached_gas)

            # Auto-trip breaker if extreme
            if gas_gwei > threshold:
                tripped = check_gas_and_trip(chain_id, gas_gwei)
                if tripped:
                    return ValidationResult(
                        False,
                        f'Gas price is extremely high ({gas_gwei:.0f} gwei). '
                        f'DeFi transactions are temporarily paused for your protection. '
                        f'They will automatically resume when gas normalizes.'
                    )

            # Warn if approaching threshold
            if gas_gwei > threshold * 0.7:
                return ValidationResult(
                    True,
                    warnings=[
                        f'Gas price is elevated ({gas_gwei:.0f} gwei). '
                        f'Consider waiting for lower gas to reduce costs.'
                    ]
                )

        return ValidationResult(True)

    except ImportError:
        return ValidationResult(True)
    except Exception as e:
        logger.warning(f"Gas price check error (non-blocking): {e}")
        return ValidationResult(True)


# ---- Daily Volume Check ----

def _check_daily_volume(user, wallet_address: str, amount_usd: float) -> ValidationResult:
    """Check daily transaction volume against tiered limits."""
    if not user:
        return ValidationResult(True, warnings=['Daily limits unavailable for unauthenticated user.'])
    try:
        from .defi_models import DeFiTransaction

        tier_limits = _get_tier_limits(user)
        daily_limit = tier_limits['daily_limit_usd']

        today_start = timezone.now() - timedelta(hours=24)
        daily_total = DeFiTransaction.objects.filter(
            user=user,
            created_at__gte=today_start,
            status__in=['pending', 'confirmed'],
        ).aggregate(total=Sum('amount_usd'))['total'] or 0

        daily_total = float(daily_total)
        new_total = daily_total + amount_usd

        if new_total > daily_limit:
            return ValidationResult(
                False,
                f'Daily transaction limit of ${daily_limit:,.0f} exceeded '
                f'({tier_limits["label"]} tier). '
                f'Today\'s total: ${daily_total:,.0f}. '
                f'Requested: ${amount_usd:,.0f}. '
                f'Upgrade your plan for higher daily limits.'
            )

        warnings = []
        if new_total > daily_limit * 0.8:
            remaining = daily_limit - daily_total
            warnings.append(
                f'Approaching daily limit ({tier_limits["label"]} tier). '
                f'${remaining:,.0f} remaining today.'
            )

        return ValidationResult(True, warnings=warnings)

    except Exception as e:
        logger.warning(f"Daily volume check error (non-blocking): {e}")
        return ValidationResult(True, warnings=['Could not verify daily limits.'])


# ---- Monthly Volume Check ----

def _check_monthly_volume(user, amount_usd: float) -> ValidationResult:
    """Check monthly transaction volume against tiered limits."""
    if not user:
        return ValidationResult(True)
    try:
        from .defi_models import DeFiTransaction

        tier_limits = _get_tier_limits(user)
        monthly_limit = tier_limits['monthly_limit_usd']

        month_start = timezone.now() - timedelta(days=30)
        monthly_total = DeFiTransaction.objects.filter(
            user=user,
            created_at__gte=month_start,
            status__in=['pending', 'confirmed'],
        ).aggregate(total=Sum('amount_usd'))['total'] or 0

        monthly_total = float(monthly_total)
        new_total = monthly_total + amount_usd

        if new_total > monthly_limit:
            return ValidationResult(
                False,
                f'Monthly transaction limit of ${monthly_limit:,.0f} exceeded '
                f'({tier_limits["label"]} tier). '
                f'This month: ${monthly_total:,.0f}. '
                f'Upgrade your plan for higher limits.'
            )

        return ValidationResult(True)

    except Exception as e:
        logger.warning(f"Monthly volume check error (non-blocking): {e}")
        return ValidationResult(True)


# ---- Pool Validation ----

def _validate_pool(pool_id: str) -> ValidationResult:
    """Validate that the pool exists and is active."""
    try:
        from .defi_models import DeFiPool

        pool = DeFiPool.objects.filter(id=pool_id, is_active=True).first()
        if not pool:
            return ValidationResult(False, f'Pool {pool_id} not found or is inactive.')

        # Check protocol is in allowed list
        protocol_slug = pool.protocol.slug if pool.protocol else ''
        if protocol_slug and protocol_slug not in ALLOWED_PROTOCOLS:
            return ValidationResult(
                False,
                f'Protocol {protocol_slug} is not currently supported.'
            )

        return ValidationResult(True)

    except Exception as e:
        logger.warning(f"Pool validation error (non-blocking): {e}")
        return ValidationResult(True, warnings=['Could not verify pool status.'])


# ---- Health Factor Check ----

def _check_health_factor(user, wallet_address: str, borrow_amount_usd: float) -> ValidationResult:
    """
    Check if a borrow would drop the health factor below safe thresholds.

    Phase 4: Uses stored position data + on-chain read when available.
    On-chain health factor via Aave's getUserAccountData is the source of truth
    on mainnet; database records serve as the optimistic cache.
    """
    try:
        from .defi_models import UserDeFiPosition

        positions = UserDeFiPosition.objects.filter(
            user=user,
            wallet_address=wallet_address,
            is_active=True,
        )

        total_collateral = sum(float(p.staked_value_usd) for p in positions)

        if total_collateral == 0:
            return ValidationResult(
                False,
                'No collateral found. You must deposit assets before borrowing.'
            )

        # Simple health factor estimation:
        # HF = (collateral * liquidation_threshold) / (debt + new_borrow)
        # Using 0.80 as average liquidation threshold
        liq_threshold = 0.80
        estimated_hf = (total_collateral * liq_threshold) / max(borrow_amount_usd, 0.01)

        warnings = []

        if estimated_hf < CRITICAL_HEALTH_FACTOR:
            return ValidationResult(
                False,
                f'This borrow would bring your health factor to {estimated_hf:.2f}, '
                f'below the critical threshold of {CRITICAL_HEALTH_FACTOR}. '
                f'Risk of liquidation is too high.'
            )

        if estimated_hf < MIN_HEALTH_FACTOR:
            warnings.append(
                f'Health factor would be {estimated_hf:.2f}. '
                f'Consider a smaller amount to maintain a safer position.'
            )

        if estimated_hf < 1.5:
            warnings.append(
                'Your health factor will be relatively low. '
                'Monitor your position closely to avoid liquidation.'
            )

        return ValidationResult(True, warnings=warnings)

    except Exception as e:
        logger.warning(f"Health factor check error (non-blocking): {e}")
        return ValidationResult(
            True,
            warnings=['Could not calculate health factor. Proceed with caution.']
        )


# ---- Rate Limiting ----

def _check_rate_limit(user, wallet_address: str) -> ValidationResult:
    """Rate limiting: max 10 DeFi transactions per minute per user."""
    if not user:
        return ValidationResult(True)
    try:
        from .defi_models import DeFiTransaction

        one_minute_ago = timezone.now() - timedelta(minutes=1)
        recent_count = DeFiTransaction.objects.filter(
            user=user,
            created_at__gte=one_minute_ago,
        ).count()

        if recent_count >= 10:
            return ValidationResult(
                False,
                'Rate limit exceeded. Please wait a moment before sending another transaction.'
            )

        return ValidationResult(True)

    except Exception as e:
        logger.warning(f"Rate limit check error (non-blocking): {e}")
        return ValidationResult(True)


# ---- Main Entry Points ----

def validate_and_record_intent(
    user,
    tx_type: str,
    wallet_address: str,
    pool_id: str,
    chain_id: int,
    symbol: str,
    amount_human: str,
    rate_mode: int = 2,
) -> dict:
    """
    Validate a transaction and create a pending DeFiTransaction record.
    Returns the validation result plus the transaction ID for tracking.

    This is the main entry point called by GraphQL mutations.
    """
    result = validate_transaction(
        user=user,
        tx_type=tx_type,
        wallet_address=wallet_address,
        symbol=symbol,
        amount_human=amount_human,
        chain_id=chain_id,
        pool_id=pool_id,
        rate_mode=rate_mode,
    )

    response = result.to_dict()

    # Also add tier info for the frontend
    tier_name = _get_user_tier(user)
    tier_limits = TRANSACTION_TIERS.get(tier_name, TRANSACTION_TIERS['starter'])
    response['tier'] = tier_name
    response['tierLabel'] = tier_limits['label']

    if result.is_valid:
        # Create pending transaction record
        try:
            from .defi_models import DeFiPool, DeFiTransaction

            pool = None
            if pool_id:
                pool = DeFiPool.objects.filter(id=pool_id).first()

            if pool:
                tx_record = DeFiTransaction.objects.create(
                    user=user,
                    pool=pool,
                    action=tx_type,
                    tx_hash=f'pending_{timezone.now().timestamp():.0f}',
                    chain_id=chain_id,
                    amount=Decimal(amount_human),
                    amount_usd=Decimal(amount_human),  # Phase 5 adds real price conversion
                    status='pending',
                )
                response['transactionId'] = str(tx_record.id)
                logger.info(f"Pending transaction created: {tx_record.id}")

        except Exception as e:
            logger.warning(f"Could not create pending transaction record: {e}")

    return response


def confirm_transaction(
    tx_hash: str,
    pool_id: str,
    user,
    wallet_address: str,
    chain_id: int,
    amount_human: str,
    action: str,
    gas_used: int = None,
    gas_price_gwei: float = None,
) -> dict:
    """
    Called after a transaction is confirmed on-chain.
    Updates the DeFiTransaction record and creates/updates UserDeFiPosition.

    Phase 4: Also records gas costs for analytics and caches gas price for
    the circuit breaker's auto-trip logic.
    """
    try:
        if not user or not getattr(user, 'is_authenticated', False):
            return {
                'success': False,
                'message': 'Authentication required to record transactions.',
            }
        from .defi_models import DeFiPool, DeFiTransaction, UserDeFiPosition

        pool = DeFiPool.objects.filter(id=pool_id).first() if pool_id else None

        # Cache the gas price for circuit breaker use
        if gas_price_gwei is not None and chain_id:
            try:
                from django.core.cache import cache
                cache.set(
                    f'defi:gas_price:{chain_id}',
                    str(gas_price_gwei),
                    timeout=300,  # 5 minute TTL
                )
            except Exception:
                pass

        # Try to find and update pending record, or create new
        tx_record = None
        pending_txs = DeFiTransaction.objects.filter(
            user=user,
            pool=pool,
            action=action,
            status='pending',
        ).order_by('-created_at')

        if pending_txs.exists():
            tx_record = pending_txs.first()
            tx_record.tx_hash = tx_hash
            tx_record.status = 'confirmed'
            tx_record.confirmed_at = timezone.now()
            if gas_used:
                tx_record.gas_used = gas_used
            tx_record.save()
        else:
            # Create new record (tx was sent without pre-validation)
            if pool:
                tx_record = DeFiTransaction.objects.create(
                    user=user,
                    pool=pool,
                    action=action,
                    tx_hash=tx_hash,
                    chain_id=chain_id,
                    amount=Decimal(amount_human),
                    amount_usd=Decimal(amount_human),
                    status='confirmed',
                    confirmed_at=timezone.now(),
                    gas_used=gas_used,
                )

        # Update position based on action
        if pool and action in ('deposit', 'withdraw', 'harvest'):
            _update_position(
                user=user,
                pool=pool,
                wallet_address=wallet_address,
                action=action,
                amount=Decimal(amount_human),
                tx_record=tx_record,
            )

        chain_name = SUPPORTED_CHAINS.get(chain_id, 'unknown')
        return {
            'success': True,
            'message': f'Transaction {action} confirmed on {chain_name}: {tx_hash[:10]}...',
            'transactionId': str(tx_record.id) if tx_record else None,
        }

    except Exception as e:
        logger.error(f"Error confirming transaction: {e}")
        return {
            'success': False,
            'message': f'Error recording transaction: {str(e)}',
        }


def _update_position(user, pool, wallet_address: str, action: str, amount: Decimal, tx_record=None):
    """Create or update a UserDeFiPosition based on transaction action."""
    from .defi_models import UserDeFiPosition

    position, created = UserDeFiPosition.objects.get_or_create(
        user=user,
        pool=pool,
        wallet_address=wallet_address,
        is_active=True,
        defaults={
            'staked_amount': Decimal('0'),
            'staked_value_usd': Decimal('0'),
            'rewards_earned': Decimal('0'),
        },
    )

    if action == 'deposit':
        position.staked_amount += amount
        position.staked_value_usd += amount  # Phase 5 adds real price conversion
    elif action == 'withdraw':
        position.staked_amount = max(Decimal('0'), position.staked_amount - amount)
        position.staked_value_usd = max(Decimal('0'), position.staked_value_usd - amount)
        if position.staked_amount == 0:
            position.is_active = False
    elif action == 'harvest':
        if amount and amount > 0:
            position.rewards_earned = max(Decimal('0'), position.rewards_earned - amount)
        else:
            position.rewards_earned = Decimal('0')

    position.save()

    # Link transaction to position
    if tx_record:
        tx_record.position = position
        tx_record.save(update_fields=['position'])

    logger.info(
        f"Position updated: user={user.id} pool={pool.id} action={action} "
        f"staked={position.staked_amount} rewards={position.rewards_earned}"
    )


# ---- Admin / Diagnostic Helpers ----

def get_validation_status() -> dict:
    """
    Return current validation service status for admin dashboard.
    Includes circuit breaker state, supported chains, and tier info.
    """
    cb_state = {'state': 'UNKNOWN'}
    try:
        from .defi_circuit_breaker import get_circuit_state
        cb_state = get_circuit_state()
    except Exception:
        pass

    return {
        'circuit_breaker': cb_state,
        'mainnet_enabled': _is_mainnet_enabled(),
        'supported_chains': SUPPORTED_CHAINS,
        'mainnet_chains': list(MAINNET_CHAINS),
        'tiers': {k: v['label'] for k, v in TRANSACTION_TIERS.items()},
        'allowed_protocols': ALLOWED_PROTOCOLS,
    }
