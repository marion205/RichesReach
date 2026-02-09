"""
EIP-712 typed data for RichesReach RepairForwarder (meta-tx).
User signs once; relayer submits the tx. Matches RepairForwarder.sol.
"""
import logging
from typing import Any, Dict

from .eip712_spend_permission import verify_signature as _verify

logger = logging.getLogger(__name__)

DOMAIN_NAME = "RichesReach RepairForwarder"
DOMAIN_VERSION = "1"


def get_domain(chain_id: int) -> Dict[str, Any]:
    return {
        "name": DOMAIN_NAME,
        "version": DOMAIN_VERSION,
        "chainId": chain_id,
    }


def get_repair_authorization_typed_data(
    from_vault: str,
    to_vault: str,
    amount_wei: str,
    deadline: int,
    nonce: int,
    chain_id: int,
) -> Dict[str, Any]:
    """Build EIP-712 typed data for RepairAuthorization (user signs; relayer submits)."""
    message = {
        "fromVault": from_vault,
        "toVault": to_vault,
        "amountWei": str(amount_wei),
        "deadline": deadline,
        "nonce": nonce,
    }
    return {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
            ],
            "RepairAuthorization": [
                {"name": "fromVault", "type": "address"},
                {"name": "toVault", "type": "address"},
                {"name": "amountWei", "type": "uint256"},
                {"name": "deadline", "type": "uint256"},
                {"name": "nonce", "type": "uint256"},
            ],
        },
        "primaryType": "RepairAuthorization",
        "domain": get_domain(chain_id),
        "message": message,
    }


def verify_repair_signature(
    user_address: str,
    typed_data: Dict[str, Any],
    signature: str,
) -> bool:
    return _verify(user_address, typed_data, signature)
