"""
Encryption Manager - Phase 3
Comprehensive encryption, key management, and data protection
"""

import asyncio
import json
import logging
import time
import hashlib
import hmac
import secrets
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import jwt
import bcrypt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization, padding
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
import uuid
from enum import Enum
import os
import threading
from collections import defaultdict
import weakref

logger = logging.getLogger("richesreach")

class EncryptionType(Enum):
    """Encryption type enumeration"""
    AES_256_GCM = "aes_256_gcm"
    AES_256_CBC = "aes_256_cbc"
    RSA_2048 = "rsa_2048"
    RSA_4096 = "rsa_4096"
    CHACHA20_POLY1305 = "chacha20_poly1305"

class KeyPurpose(Enum):
    """Key purpose enumeration"""
    DATA_ENCRYPTION = "data_encryption"
    API_ENCRYPTION = "api_encryption"
    SESSION_ENCRYPTION = "session_encryption"
    JWT_SIGNING = "jwt_signing"
    PASSWORD_HASHING = "password_hashing"
    FILE_ENCRYPTION = "file_encryption"

@dataclass
class EncryptionKey:
    """Encryption key data structure"""
    key_id: str
    purpose: KeyPurpose
    encryption_type: EncryptionType
    key_data: bytes
    created_at: datetime
    expires_at: Optional[datetime] = None
    rotation_count: int = 0
    metadata: Dict[str, Any] = None

@dataclass
class EncryptionResult:
    """Encryption result data structure"""
    encrypted_data: bytes
    key_id: str
    iv: Optional[bytes] = None
    tag: Optional[bytes] = None
    algorithm: str = None

@dataclass
class DecryptionResult:
    """Decryption result data structure"""
    decrypted_data: bytes
    success: bool
    error_message: Optional[str] = None

class EncryptionManager:
    """Comprehensive encryption and key management system"""
    
    def __init__(self):
        self.encryption_keys = {}
        self.key_rotation_schedule = {}
        self.encryption_cache = {}
        self.key_derivation_cache = {}
        self.master_key = None
        self.key_derivation_salt = None
        
        # Initialize encryption system
        asyncio.create_task(self._initialize_encryption())
        
        # Start background tasks
        asyncio.create_task(self._rotate_keys())
        asyncio.create_task(self._cleanup_expired_keys())
        asyncio.create_task(self._monitor_key_usage())
    
    async def _initialize_encryption(self):
        """Initialize encryption system"""
        try:
            # Generate or load master key
            await self._initialize_master_key()
            
            # Generate key derivation salt
            self.key_derivation_salt = os.urandom(32)
            
            # Generate initial encryption keys
            await self._generate_initial_keys()
            
            # Set up key rotation schedule
            await self._setup_key_rotation()
            
            logger.info("✅ Encryption manager initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize encryption manager: {e}")
            raise
    
    async def _initialize_master_key(self):
        """Initialize master key"""
        try:
            # In production, this would be loaded from a secure key management service
            # For now, we'll generate a new master key
            self.master_key = Fernet.generate_key()
            
            logger.info("✅ Master key initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize master key: {e}")
            raise
    
    async def _generate_initial_keys(self):
        """Generate initial encryption keys"""
        try:
            # Generate keys for different purposes
            key_purposes = [
                (KeyPurpose.DATA_ENCRYPTION, EncryptionType.AES_256_GCM),
                (KeyPurpose.API_ENCRYPTION, EncryptionType.AES_256_GCM),
                (KeyPurpose.SESSION_ENCRYPTION, EncryptionType.AES_256_GCM),
                (KeyPurpose.JWT_SIGNING, EncryptionType.RSA_2048),
                (KeyPurpose.PASSWORD_HASHING, EncryptionType.AES_256_GCM),
                (KeyPurpose.FILE_ENCRYPTION, EncryptionType.AES_256_GCM)
            ]
            
            for purpose, encryption_type in key_purposes:
                key = await self._generate_key(purpose, encryption_type)
                self.encryption_keys[key.key_id] = key
            
            logger.info(f"✅ Generated {len(self.encryption_keys)} initial encryption keys")
            
        except Exception as e:
            logger.error(f"❌ Failed to generate initial keys: {e}")
            raise
    
    async def _generate_key(self, purpose: KeyPurpose, encryption_type: EncryptionType) -> EncryptionKey:
        """Generate a new encryption key"""
        try:
            key_id = str(uuid.uuid4())
            current_time = datetime.now()
            
            if encryption_type in [EncryptionType.AES_256_GCM, EncryptionType.AES_256_CBC]:
                # Generate AES key
                key_data = os.urandom(32)  # 256 bits
                
            elif encryption_type in [EncryptionType.RSA_2048, EncryptionType.RSA_4096]:
                # Generate RSA key pair
                key_size = 2048 if encryption_type == EncryptionType.RSA_2048 else 4096
                private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=key_size,
                    backend=default_backend()
                )
                key_data = private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
                
            elif encryption_type == EncryptionType.CHACHA20_POLY1305:
                # Generate ChaCha20-Poly1305 key
                key_data = os.urandom(32)  # 256 bits
                
            else:
                raise ValueError(f"Unsupported encryption type: {encryption_type}")
            
            key = EncryptionKey(
                key_id=key_id,
                purpose=purpose,
                encryption_type=encryption_type,
                key_data=key_data,
                created_at=current_time,
                expires_at=current_time + timedelta(days=90),  # 90-day expiration
                metadata={"generated_by": "encryption_manager"}
            )
            
            return key
            
        except Exception as e:
            logger.error(f"❌ Failed to generate key: {e}")
            raise
    
    async def _setup_key_rotation(self):
        """Set up key rotation schedule"""
        try:
            # Set up rotation schedule for different key types
            self.key_rotation_schedule = {
                KeyPurpose.DATA_ENCRYPTION: timedelta(days=30),
                KeyPurpose.API_ENCRYPTION: timedelta(days=30),
                KeyPurpose.SESSION_ENCRYPTION: timedelta(days=7),
                KeyPurpose.JWT_SIGNING: timedelta(days=90),
                KeyPurpose.PASSWORD_HASHING: timedelta(days=30),
                KeyPurpose.FILE_ENCRYPTION: timedelta(days=30)
            }
            
            logger.info("✅ Key rotation schedule configured")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup key rotation: {e}")
            raise
    
    async def _rotate_keys(self):
        """Rotate encryption keys based on schedule"""
        while True:
            try:
                current_time = datetime.now()
                
                for key_id, key in self.encryption_keys.items():
                    rotation_interval = self.key_rotation_schedule.get(key.purpose)
                    if not rotation_interval:
                        continue
                    
                    # Check if key needs rotation
                    if current_time - key.created_at > rotation_interval:
                        await self._rotate_key(key_id)
                
                await asyncio.sleep(3600)  # Check every hour
                
            except Exception as e:
                logger.error(f"Error in key rotation: {e}")
                await asyncio.sleep(3600)
    
    async def _rotate_key(self, key_id: str):
        """Rotate a specific encryption key"""
        try:
            old_key = self.encryption_keys.get(key_id)
            if not old_key:
                return
            
            # Generate new key
            new_key = await self._generate_key(old_key.purpose, old_key.encryption_type)
            new_key.rotation_count = old_key.rotation_count + 1
            
            # Store new key
            self.encryption_keys[new_key.key_id] = new_key
            
            # Mark old key for cleanup
            old_key.expires_at = datetime.now() + timedelta(days=7)  # Grace period
            
            logger.info(f"✅ Rotated key {key_id} -> {new_key.key_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to rotate key {key_id}: {e}")
    
    async def _cleanup_expired_keys(self):
        """Clean up expired encryption keys"""
        while True:
            try:
                current_time = datetime.now()
                expired_keys = []
                
                for key_id, key in self.encryption_keys.items():
                    if key.expires_at and current_time > key.expires_at:
                        expired_keys.append(key_id)
                
                for key_id in expired_keys:
                    del self.encryption_keys[key_id]
                
                if expired_keys:
                    logger.info(f"✅ Cleaned up {len(expired_keys)} expired keys")
                
                await asyncio.sleep(86400)  # Cleanup daily
                
            except Exception as e:
                logger.error(f"Error cleaning up expired keys: {e}")
                await asyncio.sleep(86400)
    
    async def _monitor_key_usage(self):
        """Monitor key usage and performance"""
        while True:
            try:
                # Monitor key usage statistics
                usage_stats = {
                    "total_keys": len(self.encryption_keys),
                    "keys_by_purpose": defaultdict(int),
                    "keys_by_type": defaultdict(int)
                }
                
                for key in self.encryption_keys.values():
                    usage_stats["keys_by_purpose"][key.purpose.value] += 1
                    usage_stats["keys_by_type"][key.encryption_type.value] += 1
                
                logger.info(f"Key usage stats: {usage_stats}")
                
                await asyncio.sleep(3600)  # Monitor every hour
                
            except Exception as e:
                logger.error(f"Error monitoring key usage: {e}")
                await asyncio.sleep(3600)
    
    async def encrypt_data(self, data: Union[str, bytes], purpose: KeyPurpose, 
                          context: Optional[Dict[str, Any]] = None) -> EncryptionResult:
        """Encrypt data using appropriate key"""
        try:
            # Convert string to bytes if needed
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            # Get encryption key
            key = await self._get_key_for_purpose(purpose)
            if not key:
                raise ValueError(f"No key available for purpose: {purpose}")
            
            # Encrypt based on key type
            if key.encryption_type == EncryptionType.AES_256_GCM:
                return await self._encrypt_aes_gcm(data, key)
            elif key.encryption_type == EncryptionType.AES_256_CBC:
                return await self._encrypt_aes_cbc(data, key)
            elif key.encryption_type == EncryptionType.RSA_2048:
                return await self._encrypt_rsa(data, key)
            elif key.encryption_type == EncryptionType.CHACHA20_POLY1305:
                return await self._encrypt_chacha20_poly1305(data, key)
            else:
                raise ValueError(f"Unsupported encryption type: {key.encryption_type}")
            
        except Exception as e:
            logger.error(f"❌ Failed to encrypt data: {e}")
            raise
    
    async def decrypt_data(self, encrypted_result: EncryptionResult, 
                          purpose: KeyPurpose) -> DecryptionResult:
        """Decrypt data using appropriate key"""
        try:
            # Get encryption key
            key = await self._get_key_for_purpose(purpose)
            if not key:
                return DecryptionResult(
                    decrypted_data=b"",
                    success=False,
                    error_message=f"No key available for purpose: {purpose}"
                )
            
            # Decrypt based on key type
            if key.encryption_type == EncryptionType.AES_256_GCM:
                return await self._decrypt_aes_gcm(encrypted_result, key)
            elif key.encryption_type == EncryptionType.AES_256_CBC:
                return await self._decrypt_aes_cbc(encrypted_result, key)
            elif key.encryption_type == EncryptionType.RSA_2048:
                return await self._decrypt_rsa(encrypted_result, key)
            elif key.encryption_type == EncryptionType.CHACHA20_POLY1305:
                return await self._decrypt_chacha20_poly1305(encrypted_result, key)
            else:
                return DecryptionResult(
                    decrypted_data=b"",
                    success=False,
                    error_message=f"Unsupported encryption type: {key.encryption_type}"
                )
            
        except Exception as e:
            logger.error(f"❌ Failed to decrypt data: {e}")
            return DecryptionResult(
                decrypted_data=b"",
                success=False,
                error_message=str(e)
            )
    
    async def _get_key_for_purpose(self, purpose: KeyPurpose) -> Optional[EncryptionKey]:
        """Get the most recent key for a specific purpose"""
        try:
            purpose_keys = [key for key in self.encryption_keys.values() 
                          if key.purpose == purpose]
            
            if not purpose_keys:
                return None
            
            # Return the most recently created key
            return max(purpose_keys, key=lambda k: k.created_at)
            
        except Exception as e:
            logger.error(f"❌ Failed to get key for purpose {purpose}: {e}")
            return None
    
    async def _encrypt_aes_gcm(self, data: bytes, key: EncryptionKey) -> EncryptionResult:
        """Encrypt data using AES-256-GCM"""
        try:
            # Generate random IV
            iv = os.urandom(12)  # 96 bits for GCM
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key.key_data),
                modes.GCM(iv),
                backend=default_backend()
            )
            
            # Encrypt data
            encryptor = cipher.encryptor()
            encrypted_data = encryptor.update(data) + encryptor.finalize()
            
            return EncryptionResult(
                encrypted_data=encrypted_data,
                key_id=key.key_id,
                iv=iv,
                tag=encryptor.tag,
                algorithm="AES-256-GCM"
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to encrypt with AES-GCM: {e}")
            raise
    
    async def _decrypt_aes_gcm(self, encrypted_result: EncryptionResult, 
                              key: EncryptionKey) -> DecryptionResult:
        """Decrypt data using AES-256-GCM"""
        try:
            if not encrypted_result.iv or not encrypted_result.tag:
                return DecryptionResult(
                    decrypted_data=b"",
                    success=False,
                    error_message="Missing IV or tag for AES-GCM decryption"
                )
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key.key_data),
                modes.GCM(encrypted_result.iv, encrypted_result.tag),
                backend=default_backend()
            )
            
            # Decrypt data
            decryptor = cipher.decryptor()
            decrypted_data = decryptor.update(encrypted_result.encrypted_data) + decryptor.finalize()
            
            return DecryptionResult(
                decrypted_data=decrypted_data,
                success=True
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to decrypt with AES-GCM: {e}")
            return DecryptionResult(
                decrypted_data=b"",
                success=False,
                error_message=str(e)
            )
    
    async def _encrypt_aes_cbc(self, data: bytes, key: EncryptionKey) -> EncryptionResult:
        """Encrypt data using AES-256-CBC"""
        try:
            # Generate random IV
            iv = os.urandom(16)  # 128 bits for CBC
            
            # Pad data to block size
            pad_length = 16 - (len(data) % 16)
            padded_data = data + bytes([pad_length] * pad_length)
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key.key_data),
                modes.CBC(iv),
                backend=default_backend()
            )
            
            # Encrypt data
            encryptor = cipher.encryptor()
            encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
            
            return EncryptionResult(
                encrypted_data=encrypted_data,
                key_id=key.key_id,
                iv=iv,
                algorithm="AES-256-CBC"
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to encrypt with AES-CBC: {e}")
            raise
    
    async def _decrypt_aes_cbc(self, encrypted_result: EncryptionResult, 
                              key: EncryptionKey) -> DecryptionResult:
        """Decrypt data using AES-256-CBC"""
        try:
            if not encrypted_result.iv:
                return DecryptionResult(
                    decrypted_data=b"",
                    success=False,
                    error_message="Missing IV for AES-CBC decryption"
                )
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key.key_data),
                modes.CBC(encrypted_result.iv),
                backend=default_backend()
            )
            
            # Decrypt data
            decryptor = cipher.decryptor()
            decrypted_data = decryptor.update(encrypted_result.encrypted_data) + decryptor.finalize()
            
            # Remove padding
            pad_length = decrypted_data[-1]
            decrypted_data = decrypted_data[:-pad_length]
            
            return DecryptionResult(
                decrypted_data=decrypted_data,
                success=True
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to decrypt with AES-CBC: {e}")
            return DecryptionResult(
                decrypted_data=b"",
                success=False,
                error_message=str(e)
            )
    
    async def _encrypt_rsa(self, data: bytes, key: EncryptionKey) -> EncryptionResult:
        """Encrypt data using RSA"""
        try:
            # Load private key
            private_key = serialization.load_pem_private_key(
                key.key_data,
                password=None,
                backend=default_backend()
            )
            
            # Get public key
            public_key = private_key.public_key()
            
            # Encrypt data (RSA has size limitations)
            encrypted_data = public_key.encrypt(
                data,
                asym_padding.OAEP(
                    mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            return EncryptionResult(
                encrypted_data=encrypted_data,
                key_id=key.key_id,
                algorithm="RSA-2048"
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to encrypt with RSA: {e}")
            raise
    
    async def _decrypt_rsa(self, encrypted_result: EncryptionResult, 
                          key: EncryptionKey) -> DecryptionResult:
        """Decrypt data using RSA"""
        try:
            # Load private key
            private_key = serialization.load_pem_private_key(
                key.key_data,
                password=None,
                backend=default_backend()
            )
            
            # Decrypt data
            decrypted_data = private_key.decrypt(
                encrypted_result.encrypted_data,
                asym_padding.OAEP(
                    mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            return DecryptionResult(
                decrypted_data=decrypted_data,
                success=True
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to decrypt with RSA: {e}")
            return DecryptionResult(
                decrypted_data=b"",
                success=False,
                error_message=str(e)
            )
    
    async def _encrypt_chacha20_poly1305(self, data: bytes, key: EncryptionKey) -> EncryptionResult:
        """Encrypt data using ChaCha20-Poly1305"""
        try:
            # Generate random nonce
            nonce = os.urandom(12)  # 96 bits for ChaCha20-Poly1305
            
            # Create cipher
            cipher = Cipher(
                algorithms.ChaCha20(key.key_data, nonce),
                None,  # ChaCha20-Poly1305 doesn't use a mode
                backend=default_backend()
            )
            
            # Encrypt data
            encryptor = cipher.encryptor()
            encrypted_data = encryptor.update(data) + encryptor.finalize()
            
            return EncryptionResult(
                encrypted_data=encrypted_data,
                key_id=key.key_id,
                iv=nonce,  # Using iv field for nonce
                algorithm="ChaCha20-Poly1305"
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to encrypt with ChaCha20-Poly1305: {e}")
            raise
    
    async def _decrypt_chacha20_poly1305(self, encrypted_result: EncryptionResult, 
                                        key: EncryptionKey) -> DecryptionResult:
        """Decrypt data using ChaCha20-Poly1305"""
        try:
            if not encrypted_result.iv:  # Using iv field for nonce
                return DecryptionResult(
                    decrypted_data=b"",
                    success=False,
                    error_message="Missing nonce for ChaCha20-Poly1305 decryption"
                )
            
            # Create cipher
            cipher = Cipher(
                algorithms.ChaCha20(key.key_data, encrypted_result.iv),
                None,  # ChaCha20-Poly1305 doesn't use a mode
                backend=default_backend()
            )
            
            # Decrypt data
            decryptor = cipher.decryptor()
            decrypted_data = decryptor.update(encrypted_result.encrypted_data) + decryptor.finalize()
            
            return DecryptionResult(
                decrypted_data=decrypted_data,
                success=True
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to decrypt with ChaCha20-Poly1305: {e}")
            return DecryptionResult(
                decrypted_data=b"",
                success=False,
                error_message=str(e)
            )
    
    async def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        try:
            # Generate salt and hash password
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')
            
        except Exception as e:
            logger.error(f"❌ Failed to hash password: {e}")
            raise
    
    async def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
            
        except Exception as e:
            logger.error(f"❌ Failed to verify password: {e}")
            return False
    
    async def generate_jwt_token(self, payload: Dict[str, Any], 
                                expires_in: timedelta = timedelta(hours=24)) -> str:
        """Generate JWT token"""
        try:
            # Get JWT signing key
            jwt_key = await self._get_key_for_purpose(KeyPurpose.JWT_SIGNING)
            if not jwt_key:
                raise ValueError("No JWT signing key available")
            
            # Add expiration
            payload['exp'] = datetime.now() + expires_in
            payload['iat'] = datetime.now()
            
            # Sign token
            token = jwt.encode(
                payload,
                jwt_key.key_data,
                algorithm='RS256'
            )
            
            return token
            
        except Exception as e:
            logger.error(f"❌ Failed to generate JWT token: {e}")
            raise
    
    async def verify_jwt_token(self, token: str) -> Tuple[bool, Dict[str, Any]]:
        """Verify JWT token"""
        try:
            # Get JWT signing key
            jwt_key = await self._get_key_for_purpose(KeyPurpose.JWT_SIGNING)
            if not jwt_key:
                return False, {"error": "No JWT signing key available"}
            
            # Verify token
            payload = jwt.decode(
                token,
                jwt_key.key_data,
                algorithms=['RS256']
            )
            
            return True, payload
            
        except jwt.ExpiredSignatureError:
            return False, {"error": "Token expired"}
        except jwt.InvalidTokenError as e:
            return False, {"error": f"Invalid token: {str(e)}"}
        except Exception as e:
            logger.error(f"❌ Failed to verify JWT token: {e}")
            return False, {"error": str(e)}
    
    def get_encryption_metrics(self) -> Dict[str, Any]:
        """Get encryption metrics"""
        try:
            return {
                "total_keys": len(self.encryption_keys),
                "keys_by_purpose": {
                    purpose.value: len([k for k in self.encryption_keys.values() if k.purpose == purpose])
                    for purpose in KeyPurpose
                },
                "keys_by_type": {
                    enc_type.value: len([k for k in self.encryption_keys.values() if k.encryption_type == enc_type])
                    for enc_type in EncryptionType
                },
                "expired_keys": len([k for k in self.encryption_keys.values() 
                                   if k.expires_at and datetime.now() > k.expires_at]),
                "rotation_schedule": {
                    purpose.value: str(interval) for purpose, interval in self.key_rotation_schedule.items()
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get encryption metrics: {e}")
            return {}

# Global encryption manager
encryption_manager = EncryptionManager()
