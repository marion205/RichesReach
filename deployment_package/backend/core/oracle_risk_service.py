"""
Oracle & Counterparty Risk Service

Monitors oracle health and stablecoin peg integrity:
1. Stablecoin depeg detection (USDC, USDT, DAI)
2. Oracle freshness checks (per-chain)
3. Pool-level oracle risk assessment

Integrates into the validation pipeline (defi_validation_service.py)
and the alert service (defi_alert_service.py).

Part of Trust-First Framework: Gap 3 — Oracle/Counterparty Risk
"""
import logging
from typing import Dict, Any, Optional, List
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

# Cache key formats
PRICE_KEY = 'defi:price:{symbol}'
ORACLE_UPDATE_KEY = 'defi:oracle_update:{chain_id}'
DEPEG_ALERT_KEY = 'defi:depeg_alert:{symbol}'

# Stablecoins to monitor
STABLECOINS = {
    'USDC': {'peg': 1.0, 'name': 'USD Coin'},
    'USDT': {'peg': 1.0, 'name': 'Tether'},
    'DAI': {'peg': 1.0, 'name': 'Dai'},
    'FRAX': {'peg': 1.0, 'name': 'Frax'},
}

# Default thresholds (overridden by autopilot_policy.yaml)
DEFAULT_DEPEG_WARNING = 0.005    # 0.5% deviation = warning
DEFAULT_DEPEG_CRITICAL = 0.02    # 2.0% deviation = block
DEFAULT_ORACLE_STALE_WARNING = 30   # 30 minutes = warning
DEFAULT_ORACLE_STALE_BLOCK = 120    # 2 hours = block


class OracleRiskService:
    """
    Monitors oracle and stablecoin health for all supported assets and chains.
    """

    def __init__(self):
        self._load_thresholds()

    def _load_thresholds(self):
        """Load thresholds from policy config."""
        try:
            from .policy_engine import get_policy
            policy = get_policy()
            thresholds = policy.get('risk_thresholds', {})
            self.depeg_warning = float(
                thresholds.get('max_stablecoin_depeg', DEFAULT_DEPEG_WARNING)
            )
            self.depeg_critical = DEFAULT_DEPEG_CRITICAL
            self.oracle_stale_warning = int(
                thresholds.get('max_oracle_staleness_minutes', DEFAULT_ORACLE_STALE_WARNING)
            )
            self.oracle_stale_block = DEFAULT_ORACLE_STALE_BLOCK
        except Exception:
            self.depeg_warning = DEFAULT_DEPEG_WARNING
            self.depeg_critical = DEFAULT_DEPEG_CRITICAL
            self.oracle_stale_warning = DEFAULT_ORACLE_STALE_WARNING
            self.oracle_stale_block = DEFAULT_ORACLE_STALE_BLOCK

    # ----- Stablecoin Peg Monitoring -----

    def check_stablecoin_peg(self, symbol: str) -> Dict[str, Any]:
        """
        Check if a stablecoin has depegged beyond thresholds.

        Args:
            symbol: Token symbol (e.g., 'USDC', 'DAI')

        Returns:
            dict with: symbol, price, peg, deviation, status ('ok'|'warning'|'critical')
        """
        symbol_upper = symbol.upper()
        stable_info = STABLECOINS.get(symbol_upper)

        if not stable_info:
            # Not a stablecoin — no peg risk
            return {
                'symbol': symbol_upper,
                'is_stablecoin': False,
                'status': 'ok',
            }

        # Get cached price
        price_key = PRICE_KEY.format(symbol=symbol_upper)
        cached_price = cache.get(price_key)

        if cached_price is None:
            # No price data available — can't assess
            return {
                'symbol': symbol_upper,
                'is_stablecoin': True,
                'price': None,
                'status': 'unknown',
                'message': 'Price data unavailable',
            }

        try:
            price = float(cached_price)
        except (ValueError, TypeError):
            return {
                'symbol': symbol_upper,
                'is_stablecoin': True,
                'price': None,
                'status': 'unknown',
                'message': 'Invalid price data',
            }

        peg = stable_info['peg']
        deviation = abs(price - peg)

        if deviation > self.depeg_critical:
            status = 'critical'
        elif deviation > self.depeg_warning:
            status = 'warning'
        else:
            status = 'ok'

        return {
            'symbol': symbol_upper,
            'is_stablecoin': True,
            'price': price,
            'peg': peg,
            'deviation': round(deviation, 6),
            'deviation_pct': round(deviation / peg, 6),
            'status': status,
        }

    def check_all_stablecoins(self) -> Dict[str, Dict[str, Any]]:
        """Check peg status for all monitored stablecoins."""
        results = {}
        for symbol in STABLECOINS:
            results[symbol] = self.check_stablecoin_peg(symbol)
        return results

    # ----- Oracle Freshness -----

    def check_oracle_freshness(self, chain_id: int) -> Dict[str, Any]:
        """
        Check if oracle data is fresh for a given chain.

        Uses cache key tracking when data was last updated.

        Returns:
            dict with: chain_id, last_update, stale_minutes, status
        """
        key = ORACLE_UPDATE_KEY.format(chain_id=chain_id)
        last_update_str = cache.get(key)

        if last_update_str is None:
            return {
                'chain_id': chain_id,
                'last_update': None,
                'stale_minutes': None,
                'status': 'unknown',
                'message': 'No oracle update timestamp available',
            }

        try:
            last_update = timezone.datetime.fromisoformat(str(last_update_str))
        except (ValueError, TypeError):
            return {
                'chain_id': chain_id,
                'last_update': None,
                'stale_minutes': None,
                'status': 'unknown',
                'message': 'Invalid oracle timestamp',
            }

        now = timezone.now()
        stale_minutes = (now - last_update).total_seconds() / 60

        if stale_minutes > self.oracle_stale_block:
            status = 'critical'
        elif stale_minutes > self.oracle_stale_warning:
            status = 'warning'
        else:
            status = 'ok'

        return {
            'chain_id': chain_id,
            'last_update': last_update.isoformat(),
            'stale_minutes': round(stale_minutes, 1),
            'status': status,
        }

    # ----- Pool-Level Assessment -----

    def assess_pool_oracle_risk(self, pool, chain_id: int = None) -> Dict[str, Any]:
        """
        Assess oracle risk for a specific pool.

        Checks:
        1. Stablecoin peg risk for pool assets
        2. Oracle freshness for pool's chain

        Returns:
            dict with: is_valid (bool), reason (str), warnings (list), checks (dict)
        """
        warnings = []
        blocks = []
        checks = {}

        # 1. Check stablecoin peg for pool symbol
        if pool and hasattr(pool, 'symbol'):
            peg_check = self.check_stablecoin_peg(pool.symbol)
            checks['stablecoin_peg'] = peg_check

            if peg_check.get('status') == 'critical':
                blocks.append(
                    f"{pool.symbol} has depegged by "
                    f"{peg_check.get('deviation_pct', 0):.2%} from ${peg_check.get('peg', 1)}. "
                    f"Transactions are blocked until the peg is restored."
                )
            elif peg_check.get('status') == 'warning':
                warnings.append(
                    f"{pool.symbol} is showing minor depeg "
                    f"({peg_check.get('deviation_pct', 0):.2%} deviation). "
                    f"Monitor closely."
                )

        # 2. Check oracle freshness for chain
        effective_chain_id = chain_id
        if not effective_chain_id and pool and hasattr(pool, 'chain_id'):
            effective_chain_id = pool.chain_id

        if effective_chain_id:
            freshness = self.check_oracle_freshness(effective_chain_id)
            checks['oracle_freshness'] = freshness

            if freshness.get('status') == 'critical':
                blocks.append(
                    f"Oracle data is stale "
                    f"({freshness.get('stale_minutes', 0):.0f} min since last update). "
                    f"Transactions are blocked for your protection."
                )
            elif freshness.get('status') == 'warning':
                warnings.append(
                    f"Oracle data may be delayed "
                    f"({freshness.get('stale_minutes', 0):.0f} min since last update). "
                    f"Prices may not reflect current market conditions."
                )

        is_valid = len(blocks) == 0
        reason = blocks[0] if blocks else ''

        return {
            'is_valid': is_valid,
            'reason': reason,
            'warnings': warnings,
            'checks': checks,
        }

    # ----- Price Caching Helper -----

    @staticmethod
    def cache_stablecoin_price(symbol: str, price: float, ttl: int = 600):
        """
        Cache a stablecoin price for oracle risk checking.
        Called by defi_data_service.py when fetching yield data.

        Args:
            symbol: Token symbol (e.g., 'USDC')
            price: Current price in USD
            ttl: Cache timeout in seconds (default 10 min)
        """
        key = PRICE_KEY.format(symbol=symbol.upper())
        cache.set(key, str(price), timeout=ttl)

    @staticmethod
    def record_oracle_update(chain_id: int):
        """
        Record that oracle data was refreshed for a chain.
        Called after successful data fetch.
        """
        key = ORACLE_UPDATE_KEY.format(chain_id=chain_id)
        cache.set(key, timezone.now().isoformat(), timeout=7200)  # 2h TTL


def check_oracle_health_all_chains() -> Dict[str, Any]:
    """
    Check oracle health across all monitored chains.
    Called from the alert service periodic task.
    """
    from .defi_validation_service import SUPPORTED_CHAINS

    service = OracleRiskService()
    results = {
        'stablecoins': service.check_all_stablecoins(),
        'chains': {},
        'depegs_detected': 0,
        'stale_oracles': 0,
    }

    for chain_id in SUPPORTED_CHAINS:
        freshness = service.check_oracle_freshness(chain_id)
        results['chains'][chain_id] = freshness
        if freshness.get('status') in ('warning', 'critical'):
            results['stale_oracles'] += 1

    for symbol, check in results['stablecoins'].items():
        if check.get('status') in ('warning', 'critical'):
            results['depegs_detected'] += 1

    return results


# Singleton
_oracle_risk_service = None


def get_oracle_risk_service() -> OracleRiskService:
    global _oracle_risk_service
    if _oracle_risk_service is None:
        _oracle_risk_service = OracleRiskService()
    return _oracle_risk_service
