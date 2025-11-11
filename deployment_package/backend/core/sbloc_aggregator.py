"""
SBLOC Aggregator Service
Handles integration with SBLOC aggregator services (if using third-party aggregator)
"""
import os
import logging
import requests
from typing import List, Dict, Optional, Any
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


class SBLOCAggregatorService:
    """Service for interacting with SBLOC aggregator APIs"""
    
    def __init__(self):
        self.base_url = os.getenv('SBLOC_AGGREGATOR_URL', '')
        self.api_key = os.getenv('SBLOC_AGGREGATOR_API_KEY', '')
        self.api_secret = os.getenv('SBLOC_AGGREGATOR_API_SECRET', '')
        self.enabled = os.getenv('USE_SBLOC_AGGREGATOR', 'false').lower() == 'true'
        
        if not self.enabled:
            logger.info("SBLOC aggregator service is disabled")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = {
            'Content-Type': 'application/json',
        }
        
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        if self.api_secret:
            headers['X-API-Secret'] = self.api_secret
        
        return headers
    
    def get_available_banks(self) -> List[Dict[str, Any]]:
        """
        Get list of available SBLOC banks from aggregator
        
        Returns:
            List of bank dictionaries with structure:
            {
                'id': str,
                'name': str,
                'logoUrl': str,
                'minApr': float,
                'maxApr': float,
                'minLtv': float,
                'maxLtv': float,
                'notes': str,
                'regions': List[str],
                'minLoanUsd': int,
            }
        """
        if not self.enabled or not self.base_url:
            logger.warning("SBLOC aggregator not configured, returning empty list")
            return []
        
        try:
            url = f"{self.base_url}/banks"
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            
            data = response.json()
            banks = data.get('banks', []) if isinstance(data, dict) else data
            
            # Normalize bank data
            normalized_banks = []
            for bank in banks:
                normalized_banks.append({
                    'id': bank.get('id', ''),
                    'name': bank.get('name', ''),
                    'logoUrl': bank.get('logoUrl') or bank.get('logo_url'),
                    'minApr': bank.get('minApr') or bank.get('min_apr'),
                    'maxApr': bank.get('maxApr') or bank.get('max_apr'),
                    'minLtv': bank.get('minLtv') or bank.get('min_ltv'),
                    'maxLtv': bank.get('maxLtv') or bank.get('max_ltv'),
                    'notes': bank.get('notes', ''),
                    'regions': bank.get('regions', []),
                    'minLoanUsd': bank.get('minLoanUsd') or bank.get('min_loan_usd'),
                })
            
            return normalized_banks
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching SBLOC banks from aggregator: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_available_banks: {e}")
            return []
    
    def create_session(
        self,
        user: User,
        bank_id: str,
        amount_usd: int
    ) -> Dict[str, Any]:
        """
        Create a new SBLOC application session
        
        Args:
            user: Django User object
            bank_id: SBLOC bank ID
            amount_usd: Requested loan amount in USD
        
        Returns:
            Dictionary with session information:
            {
                'session_id': str,
                'application_url': str,
                'status': str,
            }
        """
        if not self.enabled or not self.base_url:
            logger.warning("SBLOC aggregator not configured, returning mock session")
            return {
                'session_id': f"mock_{user.id}_{bank_id}",
                'application_url': f"https://example.com/sbloc/apply?session=mock_{user.id}_{bank_id}",
                'status': 'PENDING',
            }
        
        try:
            url = f"{self.base_url}/sessions"
            payload = {
                'user_id': str(user.id),
                'user_email': user.email,
                'bank_id': bank_id,
                'amount_usd': amount_usd,
            }
            
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'session_id': data.get('session_id') or data.get('sessionId', ''),
                'application_url': data.get('application_url') or data.get('applicationUrl', ''),
                'status': data.get('status', 'PENDING'),
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating SBLOC session: {e}")
            raise Exception(f"Failed to create SBLOC session: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in create_session: {e}")
            raise
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get status of an existing SBLOC session
        
        Args:
            session_id: Session ID
        
        Returns:
            Dictionary with session status
        """
        if not self.enabled or not self.base_url:
            return {'status': 'UNKNOWN'}
        
        try:
            url = f"{self.base_url}/sessions/{session_id}"
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return {
                'status': data.get('status', 'UNKNOWN'),
                'application_url': data.get('application_url') or data.get('applicationUrl'),
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching SBLOC session status: {e}")
            return {'status': 'ERROR'}
        except Exception as e:
            logger.error(f"Unexpected error in get_session_status: {e}")
            return {'status': 'ERROR'}

