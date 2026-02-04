"""
AlpacaConnection token encryption (Phase 1 security).
Encrypts access_token and refresh_token at rest using Fernet.
"""
import base64
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from cryptography.fernet import Fernet, InvalidToken
    FERNET_AVAILABLE = True
except ImportError:
    FERNET_AVAILABLE = False
    InvalidToken = Exception  # type: ignore
    logger.warning("cryptography not available; Alpaca tokens will be stored in plaintext")

_fernet_instance: Optional["Fernet"] = None


def _get_fernet() -> Optional["Fernet"]:
    """Lazy-init Fernet with key from env/settings."""
    global _fernet_instance
    if _fernet_instance is not None:
        return _fernet_instance
    if not FERNET_AVAILABLE:
        return None
    key = os.getenv("ALPACA_TOKEN_ENCRYPTION_KEY") or os.getenv("FERNET_KEY") or ""
    if not key:
        logger.warning(
            "ALPACA_TOKEN_ENCRYPTION_KEY (or FERNET_KEY) not set; "
            "Alpaca tokens will be stored in plaintext"
        )
        return None
    try:
        if isinstance(key, str):
            key = key.encode()
        _fernet_instance = Fernet(key)
    except Exception as e:
        logger.error("Failed to init Fernet for Alpaca tokens: %s", e)
    return _fernet_instance


def _looks_fernet(ciphertext: str) -> bool:
    """Heuristic: Fernet tokens are URL-safe base64, 44+ chars."""
    if not ciphertext or len(ciphertext) < 44:
        return False
    try:
        base64.urlsafe_b64decode(ciphertext)
        return True
    except Exception:
        return False


def encrypt_token(plain: str, key: Optional[bytes] = None) -> str:
    """
    Encrypt a token for storage. Returns base64-encoded ciphertext.
    If Fernet is unavailable or key missing, returns plaintext unchanged.
    """
    if not plain:
        return plain
    fernet = _get_fernet()
    if fernet is None:
        return plain
    try:
        encrypted = fernet.encrypt(plain.encode())
        return encrypted.decode()
    except Exception as e:
        logger.warning("Alpaca token encrypt failed: %s", e)
        return plain


def decrypt_token(ciphertext: str, key: Optional[bytes] = None) -> str:
    """
    Decrypt a stored token. Expects base64-encoded ciphertext.
    If Fernet is unavailable or decrypt fails (e.g. plaintext), returns as-is.
    """
    if not ciphertext:
        return ciphertext
    fernet = _get_fernet()
    if fernet is None:
        return ciphertext
    try:
        decrypted = fernet.decrypt(ciphertext.encode())
        return decrypted.decode()
    except InvalidToken:
        # Already plaintext (e.g. before encryption was enabled)
        return ciphertext
    except Exception as e:
        logger.warning("Alpaca token decrypt failed: %s", e)
        return ciphertext
