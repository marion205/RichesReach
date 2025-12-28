"""
AWS Secrets Manager Integration
Loads secrets at startup, caches in memory for performance
"""
import os
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

_secrets_cache: Dict[str, Any] = {}


def get_secret(secret_name: str, use_cache: bool = True, default: Optional[str] = None) -> Optional[str]:
    """
    Get secret from AWS Secrets Manager or environment variable.
    
    Priority:
    1. Environment variable (for local dev) - format: SECRET_NAME (uppercase, underscores)
    2. Secrets Manager cache (if enabled)
    3. Secrets Manager (for production)
    4. Default value (if provided)
    
    Args:
        secret_name: Secret name (e.g., 'alpha_vantage_key_1')
        use_cache: Whether to use cache (default: True)
        default: Default value if secret not found (optional)
    
    Returns:
        Secret value or None if not found
    """
    # Check environment first (local dev) - convert secret_name to env var format
    env_key = secret_name.upper().replace('-', '_')
    env_value = os.getenv(env_key)
    if env_value:
        logger.debug(f"Loaded {secret_name} from environment variable")
        return env_value
    
    # Check cache
    if use_cache and secret_name in _secrets_cache:
        logger.debug(f"Loaded {secret_name} from cache")
        return _secrets_cache[secret_name]
    
    # Load from Secrets Manager (production)
    environment = os.getenv('ENVIRONMENT', 'development').lower()
    if environment == 'production':
        try:
            import boto3
            region = os.getenv('AWS_REGION', 'us-east-1')
            client = boto3.client('secretsmanager', region_name=region)
            
            # Try to get secret (may be stored as JSON or plain string)
            response = client.get_secret_value(SecretId=secret_name)
            secret_string = response['SecretString']
            
            # Try to parse as JSON first (common format)
            try:
                secret_data = json.loads(secret_string)
                # If it's a dict, try common keys
                if isinstance(secret_data, dict):
                    secret = secret_data.get('value') or secret_data.get('password') or secret_data.get('api_key')
                    if secret:
                        if use_cache:
                            _secrets_cache[secret_name] = secret
                        return secret
            except json.JSONDecodeError:
                pass
            
            # Use as plain string
            if use_cache:
                _secrets_cache[secret_name] = secret_string
            logger.info(f"Loaded {secret_name} from AWS Secrets Manager")
            return secret_string
            
        except ImportError:
            logger.warning("boto3 not available - cannot load from Secrets Manager")
        except Exception as e:
            logger.error(f"Failed to load secret {secret_name} from Secrets Manager: {e}")
    
    # Return default if provided
    if default is not None:
        logger.debug(f"Using default value for {secret_name}")
        return default
    
    return None


def clear_secrets_cache():
    """Clear the secrets cache (useful for testing or rotation)"""
    global _secrets_cache
    _secrets_cache.clear()
    logger.info("Secrets cache cleared")

