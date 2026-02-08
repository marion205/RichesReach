"""
DeFi Data Service - Fetches live yield data from DefiLlama API
Runs as a Celery periodic task every 5 minutes.
Caches results in Redis and persists to Postgres.
"""
import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import requests
from django.utils import timezone
from django.utils.text import slugify

logger = logging.getLogger(__name__)

# DefiLlama API endpoints (free, no API key required)
DEFI_LLAMA_POOLS_URL = 'https://yields.llama.fi/pools'

# Protocols we track (curated for quality and relevance)
TRACKED_PROTOCOLS = {
    'aave-v3': {'name': 'Aave V3', 'risk_score': 0.15, 'audit_firms': ['OpenZeppelin', 'Trail of Bits', 'Certora']},
    'compound-v3': {'name': 'Compound V3', 'risk_score': 0.15, 'audit_firms': ['OpenZeppelin', 'Trail of Bits']},
    'lido': {'name': 'Lido', 'risk_score': 0.20, 'audit_firms': ['Quantstamp', 'MixBytes']},
    'curve-dex': {'name': 'Curve', 'risk_score': 0.25, 'audit_firms': ['Trail of Bits', 'Quantstamp']},
    'yearn-finance': {'name': 'Yearn', 'risk_score': 0.30, 'audit_firms': ['Trail of Bits', 'MixBytes']},
    'convex-finance': {'name': 'Convex', 'risk_score': 0.30, 'audit_firms': ['MixBytes']},
    'balancer-v2': {'name': 'Balancer V2', 'risk_score': 0.25, 'audit_firms': ['Trail of Bits', 'OpenZeppelin']},
    'morpho': {'name': 'Morpho', 'risk_score': 0.20, 'audit_firms': ['Spearbit']},
    'pendle': {'name': 'Pendle', 'risk_score': 0.35, 'audit_firms': ['Ackee Blockchain']},
    'uniswap-v3': {'name': 'Uniswap V3', 'risk_score': 0.25, 'audit_firms': ['Trail of Bits']},
}

# Chain name mapping from DefiLlama to our format
CHAIN_MAP = {
    'Ethereum': ('ethereum', 1),
    'Polygon': ('polygon', 137),
    'Arbitrum': ('arbitrum', 42161),
    'Base': ('base', 8453),
    'Optimism': ('optimism', 10),
    'Avalanche': ('avalanche', 43114),
}

# Redis cache keys
CACHE_KEY_PREFIX = 'defi:top_yields'
CACHE_TTL_SECONDS = 300  # 5 minutes


def get_redis_client():
    """Get Redis client, return None if unavailable."""
    try:
        from django.core.cache import cache
        return cache
    except Exception:
        return None


def fetch_defi_llama_pools() -> List[Dict]:
    """
    Fetch pool data from DefiLlama yields API.
    Returns filtered list of pools from tracked protocols.
    """
    try:
        response = requests.get(
            DEFI_LLAMA_POOLS_URL,
            timeout=30,
            headers={'Accept': 'application/json'}
        )
        response.raise_for_status()
        data = response.json()

        if not data or 'data' not in data:
            logger.warning("DefiLlama returned empty or invalid response")
            return []

        pools = data['data']
        logger.info(f"DefiLlama returned {len(pools)} total pools")

        # Filter for tracked protocols and supported chains
        filtered = []
        for pool in pools:
            project = pool.get('project', '').lower()
            chain = pool.get('chain', '')

            if project not in TRACKED_PROTOCOLS:
                continue
            if chain not in CHAIN_MAP:
                continue

            # Skip pools with very low TVL (below $100k)
            tvl = pool.get('tvlUsd', 0) or 0
            if tvl < 100_000:
                continue

            # Skip pools with null/negative APY
            apy = pool.get('apy', 0) or 0
            if apy <= 0 or apy > 1000:  # Filter unrealistic APYs
                continue

            filtered.append(pool)

        logger.info(f"Filtered to {len(filtered)} pools from tracked protocols")
        return filtered

    except requests.RequestException as e:
        logger.error(f"Failed to fetch DefiLlama data: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching DefiLlama data: {e}", exc_info=True)
        return []


def sync_pools_to_database(pools: List[Dict]) -> int:
    """
    Upsert pool data from DefiLlama into the database.
    Creates DeFiProtocol, DeFiPool, and YieldSnapshot records.
    Returns count of snapshots created.
    """
    from .defi_models import DeFiProtocol, DeFiPool, YieldSnapshot

    snapshot_count = 0

    for pool_data in pools:
        try:
            project = pool_data.get('project', '').lower()
            chain_name = pool_data.get('chain', '')
            protocol_info = TRACKED_PROTOCOLS.get(project)
            chain_info = CHAIN_MAP.get(chain_name)

            if not protocol_info or not chain_info:
                continue

            chain_slug, chain_id = chain_info

            # Upsert protocol
            protocol, _ = DeFiProtocol.objects.update_or_create(
                slug=project,
                defaults={
                    'name': protocol_info['name'],
                    'risk_score': protocol_info['risk_score'],
                    'audit_firms': protocol_info.get('audit_firms', []),
                    'is_active': True,
                }
            )

            # Determine pool type from DefiLlama data
            pool_type = 'lending'
            pool_meta = pool_data.get('poolMeta', '') or ''
            symbol = pool_data.get('symbol', 'UNKNOWN')
            if '/' in symbol or '-' in symbol:
                pool_type = 'lp'
            elif 'stake' in pool_meta.lower() or 'staking' in project:
                pool_type = 'staking'
            elif 'vault' in pool_meta.lower():
                pool_type = 'vault'

            # Upsert pool
            defi_llama_id = pool_data.get('pool', '')
            defi_pool, _ = DeFiPool.objects.update_or_create(
                defi_llama_pool_id=defi_llama_id,
                defaults={
                    'protocol': protocol,
                    'chain': chain_slug,
                    'chain_id': chain_id,
                    'symbol': symbol,
                    'pool_address': pool_data.get('poolAddress', '') or '',
                    'pool_type': pool_type,
                    'url': pool_data.get('url', '') or '',
                    'is_active': True,
                }
            )

            # Create yield snapshot
            apy_base = pool_data.get('apyBase', 0) or 0
            apy_reward = pool_data.get('apyReward', 0) or 0
            apy_total = pool_data.get('apy', 0) or 0
            tvl_usd = pool_data.get('tvlUsd', 0) or 0

            # Calculate risk score based on protocol risk + pool characteristics
            risk_score = protocol_info['risk_score']
            if pool_type == 'lp':
                risk_score = min(1.0, risk_score + 0.15)  # LP pools have IL risk
            if apy_total > 20:
                risk_score = min(1.0, risk_score + 0.10)  # High APY = higher risk

            YieldSnapshot.objects.create(
                pool=defi_pool,
                apy_base=apy_base,
                apy_reward=apy_reward,
                apy_total=apy_total,
                tvl_usd=tvl_usd,
                risk_score=risk_score,
                il_estimate=pool_data.get('ilRisk', None),
                volume_24h_usd=pool_data.get('volumeUsd1d', None),
            )
            snapshot_count += 1

        except Exception as e:
            logger.error(f"Error syncing pool {pool_data.get('pool', 'unknown')}: {e}")
            continue

    logger.info(f"Created {snapshot_count} yield snapshots")
    return snapshot_count


def cache_top_yields():
    """
    Cache the top yields per chain in Redis for fast GraphQL queries.
    """
    from .defi_models import DeFiPool, YieldSnapshot
    from django.db.models import Subquery, OuterRef

    cache = get_redis_client()
    if not cache:
        logger.warning("Redis cache not available, skipping yield caching")
        return

    chains = ['ethereum', 'polygon', 'arbitrum', 'base', 'optimism', 'avalanche']

    for chain in chains:
        try:
            # Get pools on this chain with their latest snapshot
            pools = DeFiPool.objects.filter(
                chain=chain,
                is_active=True,
            ).select_related('protocol')

            results = []
            for pool in pools:
                latest = pool.yield_snapshots.order_by('-timestamp').first()
                if not latest:
                    continue

                results.append({
                    'id': str(pool.id),
                    'protocol': pool.protocol.name,
                    'chain': pool.chain,
                    'symbol': pool.symbol,
                    'poolAddress': pool.pool_address,
                    'apy': round(latest.apy_total, 2),
                    'apyBase': round(latest.apy_base, 2),
                    'apyReward': round(latest.apy_reward, 2),
                    'tvl': latest.tvl_usd,
                    'risk': round(latest.risk_score, 2),
                    'poolType': pool.pool_type,
                    'url': pool.url,
                    'audits': pool.protocol.audit_firms,
                    'defiLlamaId': pool.defi_llama_pool_id,
                })

            # Sort by APY descending
            results.sort(key=lambda x: x['apy'], reverse=True)

            # Cache top 50 per chain
            cache_key = f"{CACHE_KEY_PREFIX}:{chain}"
            cache.set(cache_key, json.dumps(results[:50]), CACHE_TTL_SECONDS)
            logger.info(f"Cached {len(results[:50])} yields for {chain}")

        except Exception as e:
            logger.error(f"Error caching yields for {chain}: {e}")

    # Also cache an "all chains" aggregate
    try:
        all_results = []
        for chain in chains:
            cache_key = f"{CACHE_KEY_PREFIX}:{chain}"
            cached = cache.get(cache_key)
            if cached:
                all_results.extend(json.loads(cached))

        all_results.sort(key=lambda x: x['apy'], reverse=True)
        cache.set(f"{CACHE_KEY_PREFIX}:all", json.dumps(all_results[:100]), CACHE_TTL_SECONDS)
        logger.info(f"Cached {len(all_results[:100])} total yields across all chains")

    except Exception as e:
        logger.error(f"Error caching all-chain yields: {e}")


def get_cached_yields(chain: str = 'all', limit: int = 20) -> List[Dict]:
    """
    Retrieve cached yield data from Redis, falling back to database.
    This is what GraphQL resolvers call.
    """
    cache = get_redis_client()

    # Try Redis cache first
    if cache:
        cache_key = f"{CACHE_KEY_PREFIX}:{chain}"
        cached = cache.get(cache_key)
        if cached:
            try:
                data = json.loads(cached)
                return data[:limit]
            except (json.JSONDecodeError, TypeError):
                pass

    # Fall back to database query
    try:
        from .defi_models import DeFiPool

        query = DeFiPool.objects.filter(is_active=True).select_related('protocol')
        if chain != 'all':
            query = query.filter(chain=chain)

        results = []
        for pool in query[:limit * 2]:  # Fetch extra in case some have no snapshots
            latest = pool.yield_snapshots.order_by('-timestamp').first()
            if not latest:
                continue
            results.append({
                'id': str(pool.id),
                'protocol': pool.protocol.name,
                'chain': pool.chain,
                'symbol': pool.symbol,
                'poolAddress': pool.pool_address,
                'apy': round(latest.apy_total, 2),
                'apyBase': round(latest.apy_base, 2),
                'apyReward': round(latest.apy_reward, 2),
                'tvl': latest.tvl_usd,
                'risk': round(latest.risk_score, 2),
                'poolType': pool.pool_type,
                'url': pool.url,
                'audits': pool.protocol.audit_firms,
            })

        results.sort(key=lambda x: x['apy'], reverse=True)
        return results[:limit]

    except Exception as e:
        logger.error(f"Error fetching yields from database: {e}")
        return []


def get_pool_analytics(pool_id: str, days: int = 30) -> List[Dict]:
    """
    Get historical yield data for a specific pool.
    Returns daily data points for charting.
    """
    try:
        from .defi_models import YieldSnapshot

        cutoff = timezone.now() - timedelta(days=days)
        snapshots = YieldSnapshot.objects.filter(
            pool_id=pool_id,
            timestamp__gte=cutoff,
        ).order_by('timestamp')

        results = []
        for snap in snapshots:
            results.append({
                'date': snap.timestamp.strftime('%Y-%m-%d'),
                'feeApy': round(snap.apy_base, 2),
                'ilEstimate': round(snap.il_estimate, 2) if snap.il_estimate else 0,
                'netApy': round(snap.apy_total, 2),
                'volume24hUsd': snap.volume_24h_usd or 0,
                'tvlUsd': snap.tvl_usd,
                'riskScore': round(snap.risk_score, 2),
            })

        return results

    except Exception as e:
        logger.error(f"Error fetching pool analytics: {e}")
        return []


def get_ai_optimized_portfolio(
    risk_tolerance: float = 0.5,
    chain: str = 'ethereum',
    limit: int = 8
) -> Dict:
    """
    Generate AI-optimized yield portfolio based on user's risk tolerance.
    Uses a simple risk-weighted allocation strategy.
    """
    yields = get_cached_yields(chain=chain, limit=50)

    if not yields:
        return {
            'expectedApy': 0,
            'totalRisk': 0,
            'explanation': 'No yield data available. Please try again later.',
            'optimizationStatus': 'NO_DATA',
            'allocations': [],
        }

    # Filter pools by risk tolerance
    # Low risk tolerance (0.0-0.3) = only low-risk pools
    # Medium (0.3-0.7) = balanced
    # High (0.7-1.0) = all pools including risky ones
    max_risk = 0.3 + (risk_tolerance * 0.7)  # Maps 0-1 to 0.3-1.0
    filtered = [y for y in yields if y['risk'] <= max_risk]

    if not filtered:
        filtered = yields[:5]  # Fallback to top 5 regardless of risk

    # Select top pools and calculate weights
    selected = filtered[:limit]
    total_tvl = sum(p['tvl'] for p in selected) or 1

    allocations = []
    weighted_apy = 0
    weighted_risk = 0

    for pool in selected:
        # Weight by TVL (larger pools get more allocation = safer)
        weight = round(pool['tvl'] / total_tvl, 4)
        weighted_apy += pool['apy'] * weight
        weighted_risk += pool['risk'] * weight

        allocations.append({
            'id': pool['id'],
            'protocol': pool['protocol'],
            'apy': pool['apy'],
            'tvl': pool['tvl'],
            'risk': pool['risk'],
            'symbol': pool['symbol'],
            'chain': pool.get('chain', chain),
            'weight': round(weight, 4),
        })

    # Sort allocations by weight descending
    allocations.sort(key=lambda x: x['weight'], reverse=True)

    risk_label = 'conservative' if risk_tolerance < 0.3 else 'moderate' if risk_tolerance < 0.7 else 'aggressive'

    return {
        'expectedApy': round(weighted_apy, 2),
        'totalRisk': round(weighted_risk, 2),
        'explanation': (
            f"Optimized {risk_label} portfolio across {len(allocations)} pools on {chain}. "
            f"Expected APY: {weighted_apy:.1f}% with {weighted_risk:.0%} risk score. "
            f"Weighted by TVL for safety — larger pools receive higher allocation."
        ),
        'optimizationStatus': 'OPTIMIZED',
        'allocations': allocations,
    }


def cleanup_old_snapshots(days_to_keep: int = 90):
    """
    Remove yield snapshots older than the retention period.
    Run as a weekly maintenance task.
    """
    try:
        from .defi_models import YieldSnapshot

        cutoff = timezone.now() - timedelta(days=days_to_keep)
        deleted_count, _ = YieldSnapshot.objects.filter(
            timestamp__lt=cutoff
        ).delete()
        logger.info(f"Cleaned up {deleted_count} old yield snapshots (older than {days_to_keep} days)")
        return deleted_count

    except Exception as e:
        logger.error(f"Error cleaning up old snapshots: {e}")
        return 0
