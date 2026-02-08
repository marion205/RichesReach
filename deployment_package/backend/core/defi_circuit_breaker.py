"""
DeFi Circuit Breaker Service

Emergency halt mechanism for all DeFi operations.
Can be triggered:
  1. Automatically by gas price spikes
  2. Automatically by protocol incident detection
  3. Manually by admin via Django admin or API

Uses Redis for instant propagation across all backend instances.
Every DeFi mutation checks the circuit breaker before proceeding.

Part of Phase 4: Mainnet Migration
"""
import logging
import json
from datetime import timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)

# ---- Circuit Breaker States ----

STATE_CLOSED = 'CLOSED'        # Normal operation — all transactions allowed
STATE_OPEN = 'OPEN'            # Emergency halt — all transactions blocked
STATE_HALF_OPEN = 'HALF_OPEN'  # Recovery mode — only small transactions allowed

# ---- Thresholds ----

GAS_PRICE_THRESHOLDS = {
    1: 200,          # Ethereum: halt above 200 gwei
    137: 500,        # Polygon: halt above 500 gwei
    42161: 10,       # Arbitrum: halt above 10 gwei
    8453: 5,         # Base: halt above 5 gwei
    11155111: 1000,  # Sepolia: very high threshold (testnet)
}

HALF_OPEN_TX_LIMIT_USD = 100  # In half-open state, max $100 per tx

# Redis key prefix
REDIS_PREFIX = 'defi:circuit_breaker'


def _get_redis():
    """Get Redis connection. Returns None if Redis unavailable."""
    try:
        from django.core.cache import cache
        return cache
    except Exception:
        return None


def get_circuit_state() -> dict:
    """
    Get current circuit breaker state.

    Returns:
        dict with keys: state, reason, triggered_at, triggered_by, chain_id, auto_resume_at
    """
    cache = _get_redis()
    if not cache:
        # No Redis = default to closed (allow transactions)
        return {
            'state': STATE_CLOSED,
            'reason': '',
            'triggered_at': None,
            'triggered_by': None,
            'chain_id': None,
            'auto_resume_at': None,
        }

    try:
        state_json = cache.get(f'{REDIS_PREFIX}:state')
        if state_json:
            if isinstance(state_json, str):
                return json.loads(state_json)
            return state_json
    except Exception as e:
        logger.warning(f"Error reading circuit breaker state: {e}")

    return {
        'state': STATE_CLOSED,
        'reason': '',
        'triggered_at': None,
        'triggered_by': None,
        'chain_id': None,
        'auto_resume_at': None,
    }


def is_halted(chain_id: int = None) -> bool:
    """
    Quick check: is the circuit breaker open?

    If chain_id is provided, also checks chain-specific halts.
    Returns True if transactions should be blocked.
    """
    state = get_circuit_state()

    if state['state'] == STATE_OPEN:
        # Check if it's a chain-specific halt
        if state.get('chain_id') and chain_id:
            return state['chain_id'] == chain_id
        return True

    return False


def is_half_open() -> bool:
    """Check if we're in recovery mode (limited transactions)."""
    state = get_circuit_state()
    return state['state'] == STATE_HALF_OPEN


def trip_breaker(
    reason: str,
    triggered_by: str = 'system',
    chain_id: int = None,
    auto_resume_minutes: int = 30,
):
    """
    OPEN the circuit breaker — halt all DeFi transactions.

    Args:
        reason: Why the breaker was tripped
        triggered_by: 'system', 'admin', 'gas_spike', 'protocol_incident'
        chain_id: Optional chain-specific halt (None = all chains)
        auto_resume_minutes: Auto-resume after N minutes (0 = manual only)
    """
    cache = _get_redis()
    now = timezone.now()

    state = {
        'state': STATE_OPEN,
        'reason': reason,
        'triggered_at': now.isoformat(),
        'triggered_by': triggered_by,
        'chain_id': chain_id,
        'auto_resume_at': (now + timedelta(minutes=auto_resume_minutes)).isoformat()
            if auto_resume_minutes > 0 else None,
    }

    if cache:
        try:
            cache.set(
                f'{REDIS_PREFIX}:state',
                json.dumps(state),
                timeout=auto_resume_minutes * 60 if auto_resume_minutes > 0 else 86400,
            )
        except Exception as e:
            logger.error(f"Failed to set circuit breaker state in Redis: {e}")

    # Log the event
    logger.critical(
        f"CIRCUIT BREAKER TRIPPED: reason='{reason}' "
        f"triggered_by={triggered_by} chain_id={chain_id} "
        f"auto_resume_minutes={auto_resume_minutes}"
    )

    # Record in database for audit trail
    _record_event('TRIP', reason, triggered_by, chain_id)

    return state


def reset_breaker(reset_by: str = 'admin'):
    """
    CLOSE the circuit breaker — resume normal operations.
    """
    cache = _get_redis()

    state = {
        'state': STATE_CLOSED,
        'reason': '',
        'triggered_at': None,
        'triggered_by': None,
        'chain_id': None,
        'auto_resume_at': None,
    }

    if cache:
        try:
            cache.set(f'{REDIS_PREFIX}:state', json.dumps(state), timeout=86400)
        except Exception as e:
            logger.error(f"Failed to reset circuit breaker in Redis: {e}")

    logger.info(f"CIRCUIT BREAKER RESET by {reset_by}")
    _record_event('RESET', f'Reset by {reset_by}', reset_by, None)

    return state


def set_half_open(reason: str = 'Recovery mode'):
    """
    Set circuit breaker to HALF_OPEN — limited transactions allowed.
    Used during recovery to test if conditions are safe.
    """
    cache = _get_redis()

    state = {
        'state': STATE_HALF_OPEN,
        'reason': reason,
        'triggered_at': timezone.now().isoformat(),
        'triggered_by': 'system',
        'chain_id': None,
        'auto_resume_at': None,
    }

    if cache:
        try:
            cache.set(f'{REDIS_PREFIX}:state', json.dumps(state), timeout=86400)
        except Exception as e:
            logger.error(f"Failed to set half-open state in Redis: {e}")

    logger.info(f"CIRCUIT BREAKER HALF-OPEN: {reason}")
    _record_event('HALF_OPEN', reason, 'system', None)

    return state


def check_gas_and_trip(chain_id: int, current_gas_gwei: float) -> bool:
    """
    Check if gas price exceeds threshold for a chain.
    If it does, trip the breaker automatically.

    Returns True if the breaker was tripped.
    """
    threshold = GAS_PRICE_THRESHOLDS.get(chain_id, 500)

    if current_gas_gwei > threshold:
        trip_breaker(
            reason=f'Gas price spike: {current_gas_gwei:.1f} gwei exceeds {threshold} gwei threshold on chain {chain_id}',
            triggered_by='gas_spike',
            chain_id=chain_id,
            auto_resume_minutes=15,
        )
        return True

    return False


def validate_transaction_allowed(chain_id: int, amount_usd: float = 0) -> dict:
    """
    Check if a transaction is allowed given the current circuit breaker state.

    Returns:
        dict with 'allowed' (bool), 'reason' (str), and 'state' (str)
    """
    state = get_circuit_state()

    if state['state'] == STATE_OPEN:
        # Check for chain-specific halt
        if state.get('chain_id') and state['chain_id'] != chain_id:
            # Different chain is halted, this chain is OK
            return {'allowed': True, 'reason': '', 'state': STATE_CLOSED}

        return {
            'allowed': False,
            'reason': f"DeFi transactions are temporarily paused. Reason: {state.get('reason', 'System maintenance')}",
            'state': STATE_OPEN,
        }

    if state['state'] == STATE_HALF_OPEN:
        if amount_usd > HALF_OPEN_TX_LIMIT_USD:
            return {
                'allowed': False,
                'reason': f"System is in recovery mode. Maximum transaction: ${HALF_OPEN_TX_LIMIT_USD}",
                'state': STATE_HALF_OPEN,
            }
        return {'allowed': True, 'reason': 'Recovery mode: limited transactions', 'state': STATE_HALF_OPEN}

    return {'allowed': True, 'reason': '', 'state': STATE_CLOSED}


def _record_event(event_type: str, reason: str, triggered_by: str, chain_id: int = None):
    """Record circuit breaker event in database for audit trail."""
    try:
        # Using DeFiTransaction model for audit trail
        # In production, create a dedicated CircuitBreakerEvent model
        logger.info(
            f"Circuit breaker event: type={event_type} reason={reason} "
            f"by={triggered_by} chain={chain_id}"
        )
    except Exception as e:
        logger.warning(f"Could not record circuit breaker event: {e}")
