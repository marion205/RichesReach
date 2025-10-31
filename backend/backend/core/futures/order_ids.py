"""
Idempotent Order IDs
====================
Generate deterministic client_order_id to prevent duplicate orders.
"""

import json
import blake3
from typing import Dict, Any
from datetime import datetime


def client_order_id(order: Dict[str, Any]) -> str:
    """
    Generate deterministic client order ID.
    
    Uses BLAKE3 hash of order parameters to ensure idempotency.
    Same order params = same ID = can safely retry.
    
    Args:
        order: Order dictionary with symbol, side, quantity, etc.
        
    Returns:
        Deterministic 24-character hex ID
    """
    # Normalize order for hashing
    normalized = {
        "symbol": order.get("symbol", "").upper(),
        "side": order.get("side", "").upper(),
        "quantity": int(order.get("quantity", 0)),
        "order_type": order.get("order_type", "MARKET").upper(),
        "limit_price": round(float(order.get("limit_price", 0)), 2) if order.get("limit_price") else None,
        # Exclude timestamp/user_id to ensure idempotency
    }
    
    # Create stable JSON string
    stable = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    
    # Hash with BLAKE3 (fallback to SHA256 if not available)
    try:
        hashed = blake3.blake3(stable.encode()).hexdigest()[:24]
    except (ImportError, AttributeError):
        import hashlib
        hashed = hashlib.sha256(stable.encode()).hexdigest()[:24]
    
    return f"RR{hashed}"


def is_duplicate_order(order_id: str, seen_orders: set) -> bool:
    """
    Check if order ID has been seen before.
    
    Args:
        order_id: Client order ID
        seen_orders: Set of previously seen order IDs
        
    Returns:
        True if duplicate
    """
    if order_id in seen_orders:
        return True
    seen_orders.add(order_id)
    return False

