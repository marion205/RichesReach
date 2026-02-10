"""
Relayer: submit RepairForwarder.executeRepair on behalf of the user.
Uses RELAYER_PRIVATE_KEY to pay gas. User signs EIP-712 RepairAuthorization once.
"""
import logging
import os
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

REPAIR_FORWARDER_ABI = [
    {
        "inputs": [
            {"name": "user", "type": "address"},
            {"name": "fromVault", "type": "address"},
            {"name": "toVault", "type": "address"},
            {"name": "amountWei", "type": "uint256"},
            {"name": "deadline", "type": "uint256"},
            {"name": "nonce", "type": "uint256"},
            {"name": "v", "type": "uint8"},
            {"name": "r", "type": "bytes32"},
            {"name": "s", "type": "bytes32"},
        ],
        "name": "executeRepair",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]


def _signature_to_vrs(signature: str) -> Tuple[int, bytes, bytes]:
    """Convert 0x-prefixed 65-byte hex signature to (v, r, s)."""
    if not signature or len(signature) < 132:
        raise ValueError("Invalid signature length")
    sig = bytes.fromhex(signature[2:] if signature.startswith("0x") else signature)
    r = sig[:32]
    s = sig[32:64]
    v = sig[64] if len(sig) > 64 else 27
    if v in (0, 1):
        v += 27
    return (v, r, s)


def is_relayer_configured() -> bool:
    key = os.environ.get("RELAYER_PRIVATE_KEY")
    addr = os.environ.get("REPAIR_FORWARDER_ADDRESS")
    rpc = os.environ.get("RELAYER_RPC_URL") or os.environ.get("ETHEREUM_RPC_URL")
    return bool(key and addr and rpc)


def get_forwarder_nonce(chain_id: int, user_address: str) -> Optional[int]:
    """Return current nonce for user on RepairForwarder contract, or None if not configured."""
    if not is_relayer_configured():
        return None
    try:
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider(os.environ.get("RELAYER_RPC_URL") or os.environ.get("ETHEREUM_RPC_URL")))
        forwarder_address = os.environ.get("REPAIR_FORWARDER_ADDRESS")
        abi = [{"inputs": [{"name": "user", "type": "address"}], "name": "getNonce", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"}]
        contract = w3.eth.contract(address=Web3.to_checksum_address(forwarder_address), abi=abi)
        nonce = contract.functions.getNonce(Web3.to_checksum_address(user_address)).call()
        return nonce
    except Exception as e:
        logger.warning(f"get_forwarder_nonce failed: {e}")
        return None


def submit_repair_via_relayer(
    chain_id: int,
    user_address: str,
    from_vault: str,
    to_vault: str,
    amount_wei: int,
    deadline: int,
    nonce: int,
    signature: str,
) -> Dict[str, Any]:
    """
    Verify the repair authorization signature and submit executeRepair to the forwarder.
    Returns {"success": True, "tx_hash": "0x..."} or {"success": False, "message": "..."}.
    """
    if not is_relayer_configured():
        return {"success": False, "message": "Relayer not configured (RELAYER_PRIVATE_KEY, REPAIR_FORWARDER_ADDRESS, RPC)."}

    try:
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider(os.environ.get("RELAYER_RPC_URL") or os.environ.get("ETHEREUM_RPC_URL")))
        # Circuit breaker: pause relayer when gas spikes (e.g. 300% in 5 min)
        try:
            current_gas_wei = w3.eth.gas_price
            current_gwei = float(current_gas_wei) / 1e9
            from .defi_circuit_breaker import relayer_submission_allowed, record_gas_for_relayer
            allowed = relayer_submission_allowed(chain_id, current_gwei)
            if not allowed.get("allowed"):
                return {"success": False, "message": allowed.get("reason", "Relayer paused.")}
            record_gas_for_relayer(chain_id, current_gwei)
        except Exception as e:
            logger.warning(f"Relayer circuit breaker check failed: {e}")
            # Proceed without gas check if Redis/cache unavailable

        from .eip712_repair_authorization import verify_repair_signature, get_repair_authorization_typed_data
        typed_data = get_repair_authorization_typed_data(
            from_vault, to_vault, str(amount_wei), deadline, nonce, chain_id
        )
        if not verify_repair_signature(user_address, typed_data, signature):
            return {"success": False, "message": "Invalid repair signature."}

        v, r_bytes, s_bytes = _signature_to_vrs(signature)
        forwarder_address = os.environ.get("REPAIR_FORWARDER_ADDRESS")
        relayer_acct = w3.eth.account.from_key(os.environ["RELAYER_PRIVATE_KEY"])
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(forwarder_address),
            abi=REPAIR_FORWARDER_ABI,
        )
        tx = contract.functions.executeRepair(
            Web3.to_checksum_address(user_address),
            Web3.to_checksum_address(from_vault),
            Web3.to_checksum_address(to_vault),
            amount_wei,
            deadline,
            nonce,
            v,
            r_bytes,
            s_bytes,
        ).build_transaction({
            "from": relayer_acct.address,
            # web3 v7 requires explicit nonce when building the tx
            "nonce": w3.eth.get_transaction_count(relayer_acct.address),
            "chainId": chain_id,
            "gas": 300_000,
        })
        signed = relayer_acct.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        return {"success": True, "tx_hash": tx_hash.hex()}
    except Exception as e:
        logger.exception("Relayer submit_repair failed")
        return {"success": False, "message": str(e)}
