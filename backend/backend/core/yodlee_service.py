"""
Yodlee Integration Service
Handles all Yodlee API interactions for bank account linking and data fetching
"""
import requests
import time
import json
from django.conf import settings
from django.utils import timezone
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class YodleeService:
    """Service class for Yodlee API interactions"""
    
    def __init__(self):
        self.base_url = settings.YODLEE_BASE_URL
        self.client_id = settings.YODLEE_CLIENT_ID
        self.secret = settings.YODLEE_SECRET
        self.login_name = settings.YODLEE_LOGIN_NAME
        self.fastlink_url = settings.YODLEE_FASTLINK_URL
        
    def _get_headers(self, access_token: Optional[str] = None) -> Dict[str, str]:
        """Get headers for Yodlee API requests"""
        headers = {
            "Api-Version": "1.1",
            "Content-Type": "application/json",
            "loginName": self.login_name,
            "clientId": self.client_id,
            "secret": self.secret,
        }
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        return headers
    
    def get_access_token(self) -> str:
        """Get Yodlee access token"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/token",
                headers=self._get_headers(),
                json={
                    "clientId": self.client_id,
                    "secret": self.secret
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()["accessToken"]["token"]
        except Exception as e:
            logger.error(f"Failed to get Yodlee access token: {e}")
            raise
    
    def create_fastlink_session(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Create a FastLink session for bank account linking"""
        try:
            access_token = self.get_access_token()
            
            # FastLink configuration
            config = {
                "config": {
                    "fastLinkURL": self.fastlink_url,
                    "params": {
                        "userExperienceFlow": "Aggregation",
                        "force_link": "true"
                    }
                }
            }
            
            return {
                "accessToken": access_token,
                "fastlink": config,
                "expiresAt": int(time.time()) + 900,  # 15 minutes
                "userId": user_id
            }
        except Exception as e:
            logger.error(f"Failed to create FastLink session: {e}")
            raise
    
    def get_accounts(self, access_token: str, provider_account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch accounts from Yodlee"""
        try:
            url = f"{self.base_url}/accounts"
            params = {}
            if provider_account_id:
                params["providerAccountId"] = provider_account_id
                
            response = requests.get(
                url,
                headers=self._get_headers(access_token),
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json().get("account", [])
        except Exception as e:
            logger.error(f"Failed to fetch accounts: {e}")
            raise
    
    def get_transactions(self, access_token: str, account_id: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch transactions for a specific account"""
        try:
            url = f"{self.base_url}/transactions"
            params = {"accountId": account_id}
            
            if from_date:
                params["fromDate"] = from_date
            if to_date:
                params["toDate"] = to_date
                
            response = requests.get(
                url,
                headers=self._get_headers(access_token),
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json().get("transaction", [])
        except Exception as e:
            logger.error(f"Failed to fetch transactions: {e}")
            raise
    
    def refresh_account(self, access_token: str, provider_account_id: str) -> Dict[str, Any]:
        """Trigger account refresh in Yodlee"""
        try:
            response = requests.put(
                f"{self.base_url}/providerAccounts/{provider_account_id}",
                headers=self._get_headers(access_token),
                json={"providerAccount": {"refreshInfo": [{"refreshMode": "NORMAL"}]}},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to refresh account {provider_account_id}: {e}")
            raise
    
    def get_provider_accounts(self, access_token: str) -> List[Dict[str, Any]]:
        """Get all provider accounts for the user"""
        try:
            response = requests.get(
                f"{self.base_url}/providerAccounts",
                headers=self._get_headers(access_token),
                timeout=30
            )
            response.raise_for_status()
            return response.json().get("providerAccount", [])
        except Exception as e:
            logger.error(f"Failed to fetch provider accounts: {e}")
            raise
    
    def delete_provider_account(self, access_token: str, provider_account_id: str) -> bool:
        """Delete a provider account"""
        try:
            response = requests.delete(
                f"{self.base_url}/providerAccounts/{provider_account_id}",
                headers=self._get_headers(access_token),
                timeout=30
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to delete provider account {provider_account_id}: {e}")
            return False


class YodleeDataProcessor:
    """Process and store Yodlee data in Django models"""
    
    def __init__(self):
        self.yodlee_service = YodleeService()
    
    def process_fastlink_callback(self, user_id: int, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process FastLink callback data and create/update models"""
        from .models import BankLink, BankAccount
        
        try:
            provider_account_id = str(callback_data["providerAccountId"])
            accounts_data = callback_data.get("accounts", [])
            institution_data = callback_data.get("institution", {})
            
            # Create or update BankLink
            bank_link, created = BankLink.objects.get_or_create(
                provider_account_id=provider_account_id,
                defaults={
                    'user_id': user_id,
                    'institution_name': institution_data.get('name', ''),
                    'institution_id': institution_data.get('id', ''),
                    'status': 'linked',
                    'last_sync': timezone.now()
                }
            )
            
            if not created:
                # Update existing link
                bank_link.institution_name = institution_data.get('name', bank_link.institution_name)
                bank_link.institution_id = institution_data.get('id', bank_link.institution_id)
                bank_link.status = 'linked'
                bank_link.last_sync = timezone.now()
                bank_link.save()
            
            # Process accounts
            processed_accounts = []
            for account_data in accounts_data:
                account, created = BankAccount.objects.get_or_create(
                    link=bank_link,
                    account_id=account_data['accountId'],
                    defaults={
                        'name': account_data.get('accountName', ''),
                        'type': account_data.get('accountType', 'OTHER'),
                        'mask': account_data.get('accountNumber', '')[-4:] if account_data.get('accountNumber') else '',
                        'currency': account_data.get('currency', 'USD'),
                        'balance': account_data.get('balance', {}).get('amount', 0),
                        'available_balance': account_data.get('availableBalance', {}).get('amount', 0),
                        'provider_id': account_data.get('providerId', ''),
                        'last_updated': timezone.now()
                    }
                )
                
                if not created:
                    # Update existing account
                    account.name = account_data.get('accountName', account.name)
                    account.type = account_data.get('accountType', account.type)
                    account.mask = account_data.get('accountNumber', '')[-4:] if account_data.get('accountNumber') else account.mask
                    account.currency = account_data.get('currency', account.currency)
                    account.balance = account_data.get('balance', {}).get('amount', account.balance)
                    account.available_balance = account_data.get('availableBalance', {}).get('amount', account.available_balance)
                    account.last_updated = timezone.now()
                    account.save()
                
                processed_accounts.append(account)
            
            return {
                'success': True,
                'bank_link': bank_link,
                'accounts': processed_accounts,
                'message': f"Successfully linked {len(processed_accounts)} accounts"
            }
            
        except Exception as e:
            logger.error(f"Failed to process FastLink callback: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': "Failed to process bank account linking"
            }
    
    def sync_account_data(self, bank_link) -> bool:
        """Sync account data from Yodlee"""
        try:
            access_token = self.yodlee_service.get_access_token()
            accounts_data = self.yodlee_service.get_accounts(access_token, bank_link.provider_account_id)
            
            for account_data in accounts_data:
                try:
                    account = BankAccount.objects.get(
                        link=bank_link,
                        account_id=account_data['id']
                    )
                    
                    # Update account data
                    account.balance = account_data.get('balance', {}).get('amount', account.balance)
                    account.available_balance = account_data.get('availableBalance', {}).get('amount', account.available_balance)
                    account.last_updated = timezone.now()
                    account.save()
                    
                except BankAccount.DoesNotExist:
                    # Create new account if it doesn't exist
                    BankAccount.objects.create(
                        link=bank_link,
                        account_id=account_data['id'],
                        name=account_data.get('accountName', ''),
                        type=account_data.get('accountType', 'OTHER'),
                        mask=account_data.get('accountNumber', '')[-4:] if account_data.get('accountNumber') else '',
                        currency=account_data.get('currency', 'USD'),
                        balance=account_data.get('balance', {}).get('amount', 0),
                        available_balance=account_data.get('availableBalance', {}).get('amount', 0),
                        provider_id=account_data.get('providerId', ''),
                        last_updated=timezone.now()
                    )
            
            # Update bank link sync time
            bank_link.last_sync = timezone.now()
            bank_link.status = 'active'
            bank_link.save()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync account data for {bank_link.provider_account_id}: {e}")
            bank_link.status = 'error'
            bank_link.error_message = str(e)
            bank_link.save()
            return False


# Create a singleton instance
yodlee_service = YodleeService()
