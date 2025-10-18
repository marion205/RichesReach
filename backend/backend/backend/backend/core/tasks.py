"""
Celery Background Tasks for DeFi Yield Farming
Production-grade background jobs for yield refresh and position updates
"""
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
import logging
from decimal import Decimal

from .models_defi import Chain, Protocol, Pool, FarmPosition, FarmAction
from .services.defi_service import fetch_top_yields, verify_tx
from .services.ai_yield_optimizer import ai_optimize_yields

logger = logging.getLogger(__name__)

@shared_task(name="core.tasks.defi_yield_refresh")
def defi_yield_refresh(chain_slug="ethereum", limit=20):
    """
    Background task to refresh DeFi yield data from DeFiLlama
    Updates existing pools and creates new ones as needed
    """
    data = fetch_top_yields(chain_slug, limit)
    protos = {}
    chain = Chain.objects.filter(name__iexact=chain_slug).first()
    if not chain:
        return f"Chain {chain_slug} not found"
    with transaction.atomic():
        for p in data:
            proto = protos.get(p["protocol"]) or Protocol.objects.get_or_create(
                slug=p["protocol"].lower().replace(" ", "-"),
                defaults={"name": p["protocol"]}
            )[0]
            protos[p["protocol"]] = proto
            Pool.objects.update_or_create(
                chain=chain, pool_address=p["poolAddress"],
                defaults={
                    "protocol": proto,
                    "symbol": p["symbol"],
                    "tvl_usd": Decimal(str(p["tvl"] or 0)),
                    "apy_base": float(p["apy"]) if p["apy"] else 0.0,
                    "apy_reward": 0.0,  # if you split components later
                }
            )
    return f"Refreshed {len(data)} pools"

@shared_task(name="core.tasks.defi_positions_refresh")
def defi_positions_refresh():
    """Walk user positions; pull on-chain pending rewards/LP balances."""
    from .services.defi_positions import compute_position_snapshot
    
    updated = 0
    for pos in FarmPosition.objects.select_related("pool", "pool__chain").all():
        snap = compute_position_snapshot(pos)  # returns dict with staked_lp, rewards_earned, realized_apy
        if not snap: 
            continue
        pos.staked_lp = snap.get("staked_lp", pos.staked_lp)
        pos.rewards_earned = snap.get("rewards_earned", pos.rewards_earned)
        pos.realized_apy = snap.get("realized_apy", pos.realized_apy)
        pos.save(update_fields=["staked_lp", "rewards_earned", "realized_apy", "updated_at"])
        updated += 1
    return f"Updated {updated} positions"

@shared_task(name="core.tasks.defi_analytics_daily")
def defi_analytics_daily():
    """Daily task to compute analytics for all pools"""
    from .services.analytics import compute_pool_analytics
    
    updated = 0
    for pool in Pool.objects.all():
        try:
            analytics = compute_pool_analytics(pool)
            if analytics:
                # Store analytics in PoolAnalytics model (to be created)
                updated += 1
        except Exception as e:
            logger.error(f"Failed to compute analytics for pool {pool.id}: {e}")
            continue
    
    return f"Computed analytics for {updated} pools"

@shared_task(name="core.tasks.warm_top_yields_cache")
def warm_top_yields_cache():
    """
    Background task to warm the top yields cache
    Runs every 10 minutes to keep cache fresh
    """
    chains = ["ethereum", "base", "polygon", "arbitrum"]
    limits = [10, 25, 50]
    
    warmed = 0
    for chain in chains:
        for limit in limits:
            try:
                # This will fetch and cache the data
                fetch_top_yields(chain, limit)
                warmed += 1
                logger.info(f"Warmed cache for {chain} with limit {limit}")
            except Exception as e:
                logger.error(f"Failed to warm cache for {chain}:{limit}: {e}")
                continue
    
    return f"Warmed {warmed} yield caches"