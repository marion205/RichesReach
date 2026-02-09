"""
Token Encryption for Banking - Fernet/KMS encryption for sensitive tokens
"""
import os
import logging
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)

# Try to import Fernet (cryptography library)
try:
    from cryptography.fernet import Fernet
    FERNET_AVAILABLE = True
except ImportError:
    FERNET_AVAILABLE = False
    Fernet = None
    logger.warning("cryptography library not available, token encryption disabled")

# Try to import AWS KMS
try:
    import boto3
    KMS_AVAILABLE = True
except ImportError:
    KMS_AVAILABLE = False


class TokenEncryption:
    """Token encryption service using Fernet or AWS KMS"""
    
    def __init__(self):
        self.encryption_method = os.getenv('BANK_TOKEN_ENCRYPTION', 'fernet')  # 'fernet' or 'kms'
        self.fernet_key = None
        self.kms_key_id = os.getenv('AWS_KMS_KEY_ID', '')
        self.kms_client = None
        
        if self.encryption_method == 'fernet':
            self._init_fernet()
        elif self.encryption_method == 'kms':
            self._init_kms()
    
    def _init_fernet(self):
        """Initialize Fernet encryption"""
        if not FERNET_AVAILABLE:
            logger.warning("Fernet not available, token encryption disabled")
            return
        
        # Get encryption key from environment
        key = os.getenv('BANK_TOKEN_ENC_KEY', '')
        
        if not key:
            # Generate a key if not set (should be set in production)
            logger.warning("BANK_TOKEN_ENC_KEY not set, generating new key (not secure for production!)")
            key = Fernet.generate_key().decode()
            logger.warning(f"Generated key: {key} (save this to BANK_TOKEN_ENC_KEY)")
        
        try:
            if isinstance(key, str):
                key = key.encode()
            self.fernet_key = Fernet(key)
        except Exception as e:
            logger.error(f"Error initializing Fernet: {e}")
            self.fernet_key = None
    
    def _init_kms(self):
        """Initialize AWS KMS encryption"""
        if not KMS_AVAILABLE:
            logger.warning("boto3 not available, KMS encryption disabled")
            return
        
        if not self.kms_key_id:
            logger.warning("AWS_KMS_KEY_ID not set, KMS encryption disabled")
            return
        
        try:
            self.kms_client = boto3.client('kms', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        except Exception as e:
            logger.error(f"Error initializing KMS client: {e}")
            self.kms_client = None
    
    def encrypt(self, plaintext: str) -> Optional[str]:
        """
        Encrypt a token
        
        Args:
            plaintext: Token to encrypt
            
        Returns:
            Encrypted token (base64 string) or None if encryption fails
        """
        if not plaintext:
            return None
        
        try:
            if self.encryption_method == 'fernet' and self.fernet_key:
                encrypted = self.fernet_key.encrypt(plaintext.encode())
                return encrypted.decode()
            
            elif self.encryption_method == 'kms' and self.kms_client:
                response = self.kms_client.encrypt(
                    KeyId=self.kms_key_id,
                    Plaintext=plaintext.encode()
                )
                import base64
                return base64.b64encode(response['CiphertextBlob']).decode()
            
            else:
                logger.warning("Encryption not available, storing plaintext (not secure!)")
                return plaintext
        
        except Exception as e:
            logger.error(f"Error encrypting token: {e}")
            return None
    
    def decrypt(self, ciphertext: str) -> Optional[str]:
        """
        Decrypt a token
        
        Args:
            ciphertext: Encrypted token (base64 string)
            
        Returns:
            Decrypted token or None if decryption fails
        """
        if not ciphertext:
            return None
        
        try:
            if self.encryption_method == 'fernet' and self.fernet_key:
                decrypted = self.fernet_key.decrypt(ciphertext.encode())
                return decrypted.decode()
            
            elif self.encryption_method == 'kms' and self.kms_client:
                import base64
                ciphertext_blob = base64.b64decode(ciphertext)
                response = self.kms_client.decrypt(CiphertextBlob=ciphertext_blob)
                return response['Plaintext'].decode()
            
            else:
                # Assume plaintext if encryption not available
                return ciphertext
        
        except Exception as e:
            logger.error(f"Error decrypting token: {e}")
            return None


# Global instance
_token_encryption = None


def get_token_encryption() -> TokenEncryption:
    """Get global token encryption instance"""
    global _token_encryption
    if _token_encryption is None:
        _token_encryption = TokenEncryption()
    return _token_encryption


def encrypt_token(token: str) -> Optional[str]:
    """Encrypt a token (convenience function)"""
    return get_token_encryption().encrypt(token)


def decrypt_token(encrypted_token: str) -> Optional[str]:
    """Decrypt a token (convenience function)"""
    return get_token_encryption().decrypt(encrypted_token)

