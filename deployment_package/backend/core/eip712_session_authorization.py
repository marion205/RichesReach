"""
EIP-712 typed data for RichesReach session authorization (2026-style session key).
User signs once to authorize a session (by id) to request repairs for a wallet within bounds.
"""
import hashlib
import logging
from typing import Any, Dict

from .eip712_spend_permission import verify_signature as _verify

logger = logging.getLogger(__name__)

DOMAIN_NAME = "RichesReach SessionAuth"
DOMAIN_VERSION = "1"


def get_domain(chain_id: int) -> Dict[str, Any]:
    return {
        "name": DOMAIN_NAME,
        "version": DOMAIN_VERSION,
        "chainId": chain_id,
    }


def get_session_authorization_typed_data(
    session_id: str,
    wallet_address: str,
    chain_id: int,
    max_amount_wei: str,
    valid_until: int,
    nonce: str,
) -> Dict[str, Any]:
    """Build EIP-712 typed data for SessionAuthorization."""
    # Use keccak256(sessionId) as uint256 for simplicity in solidity-style types; we use string in backend
    message = {
        "sessionId": session_id,
        "wallet": wallet_address,
        "chainId": chain_id,
        "maxAmountWei": str(max_amount_wei),
        "validUntil": valid_until,
        "nonce": nonce,
    }
    return {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
            ],
            "SessionAuthorization": [
                {"name": "sessionId", "type": "string"},
                {"name": "wallet", "type": "address"},
                {"name": "chainId", "type": "uint256"},
                {"name": "maxAmountWei", "type": "uint256"},
                {"name": "validUntil", "type": "uint256"},
                {"name": "nonce", "type": "string"},
            ],
        },
        "primaryType": "SessionAuthorization",
        "domain": get_domain(chain_id),
        "message": message,
    }


def verify_session_signature(
    wallet_address: str,
    typed_data: Dict[str, Any],
    signature: str,
) -> bool:
    return _verify(wallet_address, typed_data, signature)
