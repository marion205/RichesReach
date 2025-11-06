"""
Unit tests for banking token encryption
"""
import os
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase

from core.banking_encryption import (
    TokenEncryption,
    encrypt_token,
    decrypt_token,
    get_token_encryption,
)


class TokenEncryptionTestCase(TestCase):
    """Tests for TokenEncryption"""
    
    @patch.dict(os.environ, {'BANK_TOKEN_ENCRYPTION': 'fernet'})
    @patch('core.banking_encryption.FERNET_AVAILABLE', True)
    @patch('core.banking_encryption.Fernet')
    def test_fernet_encrypt_decrypt(self, mock_fernet_class):
        """Test Fernet encryption and decryption"""
        # Setup mock Fernet
        mock_fernet = MagicMock()
        mock_fernet.encrypt.return_value = b'encrypted_data'
        mock_fernet.decrypt.return_value = b'plaintext_data'
        mock_fernet_class.return_value = mock_fernet
        
        encryption = TokenEncryption()
        encrypted = encryption.encrypt('plaintext_data')
        decrypted = encryption.decrypt(encrypted)
        
        self.assertIsNotNone(encrypted)
        mock_fernet.encrypt.assert_called_once()
        mock_fernet.decrypt.assert_called_once()
    
    @patch.dict(os.environ, {'BANK_TOKEN_ENCRYPTION': 'fernet', 'BANK_TOKEN_ENC_KEY': 'test_key'})
    @patch('core.banking_encryption.FERNET_AVAILABLE', False)
    def test_fernet_not_available(self):
        """Test when Fernet is not available"""
        encryption = TokenEncryption()
        result = encryption.encrypt('test')
        
        # Should return plaintext when encryption not available
        self.assertEqual(result, 'test')
    
    @patch.dict(os.environ, {
        'BANK_TOKEN_ENCRYPTION': 'kms',
        'AWS_KMS_KEY_ID': 'arn:aws:kms:us-east-1:123456789:key/abc123',
        'AWS_REGION': 'us-east-1'
    })
    @patch('core.banking_encryption.KMS_AVAILABLE', True)
    @patch('core.banking_encryption.boto3')
    def test_kms_encrypt_decrypt(self, mock_boto3):
        """Test KMS encryption and decryption"""
        # Setup mock KMS client
        mock_kms_client = MagicMock()
        mock_kms_client.encrypt.return_value = {'CiphertextBlob': b'encrypted_data'}
        mock_kms_client.decrypt.return_value = {'Plaintext': b'plaintext_data'}
        mock_boto3.client.return_value = mock_kms_client
        
        encryption = TokenEncryption()
        encrypted = encryption.encrypt('plaintext_data')
        decrypted = encryption.decrypt(encrypted)
        
        self.assertIsNotNone(encrypted)
        mock_kms_client.encrypt.assert_called_once()
    
    @patch.dict(os.environ, {'BANK_TOKEN_ENCRYPTION': 'kms'})
    @patch('core.banking_encryption.KMS_AVAILABLE', False)
    def test_kms_not_available(self):
        """Test when KMS is not available"""
        encryption = TokenEncryption()
        result = encryption.encrypt('test')
        
        # Should return plaintext when encryption not available
        self.assertEqual(result, 'test')
    
    def test_encrypt_none(self):
        """Test encrypting None"""
        encryption = TokenEncryption()
        result = encryption.encrypt(None)
        
        self.assertIsNone(result)
    
    def test_decrypt_none(self):
        """Test decrypting None"""
        encryption = TokenEncryption()
        result = encryption.decrypt(None)
        
        self.assertIsNone(result)
    
    def test_encrypt_empty_string(self):
        """Test encrypting empty string"""
        encryption = TokenEncryption()
        result = encryption.encrypt('')
        
        self.assertIsNone(result)
    
    @patch.dict(os.environ, {'BANK_TOKEN_ENCRYPTION': 'invalid_method'})
    def test_invalid_encryption_method(self):
        """Test invalid encryption method"""
        encryption = TokenEncryption()
        result = encryption.encrypt('test')
        
        # Should return plaintext as fallback
        self.assertEqual(result, 'test')


class EncryptionFunctionsTestCase(TestCase):
    """Tests for convenience encryption functions"""
    
    @patch('core.banking_encryption.get_token_encryption')
    def test_encrypt_token(self, mock_get_encryption):
        """Test encrypt_token convenience function"""
        mock_encryption = MagicMock()
        mock_encryption.encrypt.return_value = 'encrypted_token'
        mock_get_encryption.return_value = mock_encryption
        
        result = encrypt_token('plaintext_token')
        
        self.assertEqual(result, 'encrypted_token')
        mock_encryption.encrypt.assert_called_once_with('plaintext_token')
    
    @patch('core.banking_encryption.get_token_encryption')
    def test_decrypt_token(self, mock_get_encryption):
        """Test decrypt_token convenience function"""
        mock_encryption = MagicMock()
        mock_encryption.decrypt.return_value = 'decrypted_token'
        mock_get_encryption.return_value = mock_encryption
        
        result = decrypt_token('encrypted_token')
        
        self.assertEqual(result, 'decrypted_token')
        mock_encryption.decrypt.assert_called_once_with('encrypted_token')
    
    def test_get_token_encryption_singleton(self):
        """Test that get_token_encryption returns singleton"""
        # Clear the global instance
        import core.banking_encryption
        core.banking_encryption._token_encryption = None
        
        encryption1 = get_token_encryption()
        encryption2 = get_token_encryption()
        
        # Should be the same instance
        self.assertIs(encryption1, encryption2)

