"""
EIP-712 typed data for RichesReach Auto-Pilot spend permissions.

The client (mobile) signs this structured message when granting spend permission.
Backend verifies the signature and stores the permission so repairs within
bounds can be auto-approved or executed via a relayer.

Domain: RichesReach SpendPermission
PrimaryType: SpendPermission
"""
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# EIP-712 domain name and version
DOMAIN_NAME = "RichesReach"
DOMAIN_VERSION = "1"

# Chain ID to domain separator (optional; we use chainId in domain)
def get_domain(chain_id: int) -> Dict[str, Any]:
    return {
        "name": DOMAIN_NAME,
        "version": DOMAIN_VERSION,
        "chainId": chain_id,
    }


def get_spend_permission_typed_data(
    chain_id: int,
    max_amount_wei: str,
    token_address: str,
    valid_until_seconds: int,
    nonce: str,
) -> Dict[str, Any]:
    """
    Build the full EIP-712 typed data payload for the client to sign.
    Client uses eth_signTypedData_v4 with this payload.
    """
    # Ensure addresses are checksummed for signing (client may send lowercase)
    token_address = _to_checksum_address(token_address) if _is_address(token_address) else token_address

    message = {
        "chainId": chain_id,
        "maxAmountWei": str(max_amount_wei),
        "tokenAddress": token_address,
        "validUntil": valid_until_seconds,
        "nonce": str(nonce),
    }

    typed_data = {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
            ],
            "SpendPermission": [
                {"name": "chainId", "type": "uint256"},
                {"name": "maxAmountWei", "type": "uint256"},
                {"name": "tokenAddress", "type": "address"},
                {"name": "validUntil", "type": "uint256"},
                {"name": "nonce", "type": "uint256"},
            ],
        },
        "primaryType": "SpendPermission",
        "domain": get_domain(chain_id),
        "message": message,
    }
    return typed_data


def verify_signature(
    signer_address: str,
    typed_data: Dict[str, Any],
    signature: str,
) -> bool:
    """
    Verify that the signature was produced by signer_address for the given typed data.
    Returns True if valid.
    """
    try:
        from eth_account import Account
        from eth_account.messages import encode_typed_data

        msg = encode_typed_data(full_message=typed_data)
        recovered = Account.recover_message(msg, signature=signature)
        return recovered.lower() == signer_address.lower()
    except Exception as e:
        logger.warning(f"EIP-712 verify_signature error: {e}")
        return False


def _is_address(s: str) -> bool:
    return isinstance(s, str) and len(s) == 42 and s.startswith("0x")


def _to_checksum_address(address: str) -> str:
    try:
        from eth_utils import to_checksum_address
        return to_checksum_address(address)
    except Exception:
        return address
