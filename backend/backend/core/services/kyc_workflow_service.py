"""
KYC/AML Workflow Service
Handles complete Know Your Customer and Anti-Money Laundering workflows through Alpaca
"""
import os
import requests
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from django.conf import settings

# Note: User model import removed to avoid Django dependency issues in testing
logger = logging.getLogger(__name__)

class KYCWorkflowService:
    """Service for managing KYC/AML workflows through Alpaca"""
    
    def __init__(self):
        # Try Django settings first, then environment variables
        self.api_key = getattr(settings, 'ALPACA_API_KEY', os.getenv('ALPACA_API_KEY', ''))
        self.secret_key = getattr(settings, 'ALPACA_SECRET_KEY', os.getenv('ALPACA_SECRET_KEY', ''))
        self.base_url = getattr(settings, 'ALPACA_BASE_URL', os.getenv('ALPACA_BASE_URL', 'https://broker-api.sandbox.alpaca.markets'))
        self.environment = getattr(settings, 'ALPACA_ENVIRONMENT', os.getenv('ALPACA_ENVIRONMENT', 'sandbox'))
        
        if not self.api_key or not self.secret_key:
            logger.warning("Alpaca API credentials not configured for KYC")
        
        self.headers = {
            'APCA-API-KEY-ID': self.api_key,
            'APCA-API-SECRET-KEY': self.secret_key,
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make HTTP request to Alpaca API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=self.headers, json=data)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Alpaca KYC API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise
    
    # =============================================================================
    # ACCOUNT CREATION & KYC
    # =============================================================================
    
    def create_brokerage_account(self, user, kyc_data: Dict) -> Dict:
        """Create a new brokerage account with KYC data"""
        try:
            # Prepare account creation data
            account_data = {
                "contact": {
                    "email_address": user.email,
                    "phone_number": kyc_data.get('phone_number', ''),
                    "street_address": [kyc_data.get('street_address', '')],
                    "city": kyc_data.get('city', ''),
                    "state": kyc_data.get('state', ''),
                    "postal_code": kyc_data.get('postal_code', ''),
                    "country": kyc_data.get('country', 'USA')
                },
                "identity": {
                    "given_name": user.first_name or kyc_data.get('first_name', ''),
                    "family_name": user.last_name or kyc_data.get('last_name', ''),
                    "date_of_birth": kyc_data.get('date_of_birth', ''),
                    "tax_id": kyc_data.get('tax_id', ''),
                    "ssn_sin": kyc_data.get('ssn', ''),
                    "country_of_citizenship": kyc_data.get('citizenship', 'USA'),
                    "country_of_birth": kyc_data.get('birth_country', 'USA'),
                    "country_of_tax_residence": kyc_data.get('tax_residence', 'USA'),
                    "visa_type": kyc_data.get('visa_type', 'NONE')
                },
                "disclosures": {
                    "is_control_person": kyc_data.get('is_control_person', False),
                    "is_affiliated_exchange_or_finra": kyc_data.get('is_affiliated', False),
                    "is_politically_exposed": kyc_data.get('is_politically_exposed', False),
                    "is_us_citizen": kyc_data.get('is_us_citizen', True),
                    "is_us_resident": kyc_data.get('is_us_resident', True),
                    "is_us_tax_payer": kyc_data.get('is_us_tax_payer', True)
                },
                "agreements": [
                    {
                        "agreement": "customer_agreement",
                        "signed_at": datetime.now().isoformat(),
                        "ip_address": kyc_data.get('ip_address', '127.0.0.1')
                    },
                    {
                        "agreement": "disclosure_day_trading",
                        "signed_at": datetime.now().isoformat(),
                        "ip_address": kyc_data.get('ip_address', '127.0.0.1')
                    }
                ],
                "trusted_contact": {
                    "given_name": kyc_data.get('trusted_contact_first_name', ''),
                    "family_name": kyc_data.get('trusted_contact_last_name', ''),
                    "email_address": kyc_data.get('trusted_contact_email', '')
                }
            }
            
            # Create account in Alpaca
            response = self._make_request('POST', '/v1/accounts', account_data)
            
            logger.info(f"Alpaca account creation response: {response}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to create brokerage account: {e}")
            raise
    
    def create_crypto_account(self, user, kyc_data: Dict) -> Dict:
        """Create a new crypto account with KYC data"""
        try:
            # For crypto accounts, we typically need to enable crypto trading on existing brokerage account
            # This is a simplified version - actual implementation may vary
            crypto_data = {
                "user_id": str(user.id),
                "crypto_enabled": True,
                "state": kyc_data.get('state', ''),
                "kyc_completed": True,
                "created_at": datetime.now().isoformat()
            }
            
            # In a real implementation, this would call Alpaca's crypto account creation endpoint
            # For now, we'll return a mock response
            response = {
                "id": f"crypto_{user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "status": "PENDING",
                "crypto_enabled": True,
                "created_at": datetime.now().isoformat()
            }
            
            logger.info(f"Crypto account creation response: {response}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to create crypto account: {e}")
            raise
    
    # =============================================================================
    # DOCUMENT UPLOAD & VERIFICATION
    # =============================================================================
    
    def upload_kyc_document(self, account_id: str, document_data: Dict) -> Dict:
        """Upload KYC documents for verification"""
        try:
            # Prepare document upload data
            document_payload = {
                "document_type": document_data.get('document_type', 'IDENTITY'),
                "content": document_data.get('content', ''),  # Base64 encoded content
                "content_type": document_data.get('content_type', 'application/pdf'),
                "uploaded_at": datetime.now().isoformat()
            }
            
            # Upload document to Alpaca
            response = self._make_request('POST', f'/v1/accounts/{account_id}/documents', document_payload)
            
            logger.info(f"KYC document upload response: {response}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to upload KYC document: {e}")
            raise
    
    def get_kyc_documents(self, account_id: str) -> List[Dict]:
        """Get KYC documents for an account"""
        try:
            response = self._make_request('GET', f'/v1/accounts/{account_id}/documents')
            return response if isinstance(response, list) else response.get('documents', [])
            
        except Exception as e:
            logger.error(f"Failed to get KYC documents: {e}")
            return []
    
    def get_kyc_status(self, account_id: str) -> Dict:
        """Get KYC verification status for an account"""
        try:
            account_data = self._make_request('GET', f'/v1/accounts/{account_id}')
            
            kyc_status = {
                "account_id": account_id,
                "status": account_data.get('status', 'UNKNOWN'),
                "kyc_required": account_data.get('kyc_required', True),
                "documents_uploaded": len(account_data.get('documents', [])),
                "verification_status": account_data.get('verification_status', 'PENDING'),
                "last_updated": account_data.get('updated_at', datetime.now().isoformat())
            }
            
            return kyc_status
            
        except Exception as e:
            logger.error(f"Failed to get KYC status: {e}")
            return {
                "account_id": account_id,
                "status": "ERROR",
                "error": str(e)
            }
    
    # =============================================================================
    # ACCOUNT MANAGEMENT
    # =============================================================================
    
    def get_account_status(self, account_id: str) -> Dict:
        """Get comprehensive account status"""
        try:
            account_data = self._make_request('GET', f'/v1/accounts/{account_id}')
            
            status = {
                "account_id": account_id,
                "status": account_data.get('status', 'UNKNOWN'),
                "trading_enabled": account_data.get('trading_enabled', False),
                "crypto_enabled": account_data.get('crypto_enabled', False),
                "buying_power": account_data.get('buying_power', 0),
                "cash": account_data.get('cash', 0),
                "portfolio_value": account_data.get('portfolio_value', 0),
                "created_at": account_data.get('created_at', ''),
                "updated_at": account_data.get('updated_at', '')
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get account status: {e}")
            return {
                "account_id": account_id,
                "status": "ERROR",
                "error": str(e)
            }
    
    def update_account_info(self, account_id: str, update_data: Dict) -> Dict:
        """Update account information"""
        try:
            response = self._make_request('PUT', f'/v1/accounts/{account_id}', update_data)
            logger.info(f"Account update response: {response}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to update account: {e}")
            raise
    
    # =============================================================================
    # COMPLIANCE & MONITORING
    # =============================================================================
    
    def check_compliance_status(self, account_id: str) -> Dict:
        """Check compliance and monitoring status"""
        try:
            # Get account data
            account_data = self._make_request('GET', f'/v1/accounts/{account_id}')
            
            compliance_status = {
                "account_id": account_id,
                "kyc_complete": account_data.get('kyc_complete', False),
                "aml_clear": account_data.get('aml_clear', False),
                "sanctions_clear": account_data.get('sanctions_clear', True),
                "risk_level": account_data.get('risk_level', 'LOW'),
                "monitoring_active": account_data.get('monitoring_active', True),
                "last_review": account_data.get('last_compliance_review', ''),
                "next_review": account_data.get('next_compliance_review', '')
            }
            
            return compliance_status
            
        except Exception as e:
            logger.error(f"Failed to check compliance status: {e}")
            return {
                "account_id": account_id,
                "error": str(e)
            }
    
    def get_account_activities(self, account_id: str, activity_type: Optional[str] = None) -> List[Dict]:
        """Get account activities for monitoring"""
        try:
            endpoint = f'/v1/accounts/{account_id}/activities'
            params = {}
            if activity_type:
                params['activity_type'] = activity_type
            
            url = f"{self.base_url}{endpoint}"
            if params:
                url += '?' + '&'.join([f"{k}={v}" for k, v in params.items()])
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            return data if isinstance(data, list) else data.get('activities', [])
            
        except Exception as e:
            logger.error(f"Failed to get account activities: {e}")
            return []
    
    # =============================================================================
    # WORKFLOW MANAGEMENT
    # =============================================================================
    
    def initiate_kyc_workflow(self, user, workflow_type: str = 'brokerage') -> Dict:
        """Initiate KYC workflow for a user"""
        try:
            workflow_data = {
                "user_id": str(user.id),
                "workflow_type": workflow_type,
                "status": "INITIATED",
                "steps_required": self._get_required_steps(workflow_type),
                "current_step": 1,
                "created_at": datetime.now().isoformat(),
                "estimated_completion": (datetime.now() + timedelta(days=3)).isoformat()
            }
            
            logger.info(f"KYC workflow initiated for user {user.id}: {workflow_data}")
            return workflow_data
            
        except Exception as e:
            logger.error(f"Failed to initiate KYC workflow: {e}")
            raise
    
    def _get_required_steps(self, workflow_type: str) -> List[Dict]:
        """Get required steps for KYC workflow"""
        if workflow_type == 'brokerage':
            return [
                {"step": 1, "name": "Personal Information", "required": True, "status": "PENDING"},
                {"step": 2, "name": "Identity Verification", "required": True, "status": "PENDING"},
                {"step": 3, "name": "Address Verification", "required": True, "status": "PENDING"},
                {"step": 4, "name": "Tax Information", "required": True, "status": "PENDING"},
                {"step": 5, "name": "Disclosures", "required": True, "status": "PENDING"},
                {"step": 6, "name": "Document Upload", "required": True, "status": "PENDING"},
                {"step": 7, "name": "Review & Approval", "required": True, "status": "PENDING"}
            ]
        elif workflow_type == 'crypto':
            return [
                {"step": 1, "name": "State Eligibility", "required": True, "status": "PENDING"},
                {"step": 2, "name": "Identity Verification", "required": True, "status": "PENDING"},
                {"step": 3, "name": "Crypto Disclosures", "required": True, "status": "PENDING"},
                {"step": 4, "name": "Document Upload", "required": True, "status": "PENDING"},
                {"step": 5, "name": "Review & Approval", "required": True, "status": "PENDING"}
            ]
        else:
            return []
    
    def update_workflow_step(self, user_id: str, step: int, status: str, data: Optional[Dict] = None) -> Dict:
        """Update KYC workflow step status"""
        try:
            update_data = {
                "user_id": user_id,
                "step": step,
                "status": status,
                "updated_at": datetime.now().isoformat()
            }
            
            if data:
                update_data.update(data)
            
            logger.info(f"KYC workflow step updated for user {user_id}: {update_data}")
            return update_data
            
        except Exception as e:
            logger.error(f"Failed to update workflow step: {e}")
            raise
    
    def complete_kyc_workflow(self, user_id: str, workflow_type: str) -> Dict:
        """Complete KYC workflow"""
        try:
            completion_data = {
                "user_id": user_id,
                "workflow_type": workflow_type,
                "status": "COMPLETED",
                "completed_at": datetime.now().isoformat(),
                "next_steps": self._get_next_steps(workflow_type)
            }
            
            logger.info(f"KYC workflow completed for user {user_id}: {completion_data}")
            return completion_data
            
        except Exception as e:
            logger.error(f"Failed to complete KYC workflow: {e}")
            raise
    
    def _get_next_steps(self, workflow_type: str) -> List[str]:
        """Get next steps after KYC completion"""
        if workflow_type == 'brokerage':
            return [
                "Account will be reviewed by compliance team",
                "You will receive email notification within 1-2 business days",
                "Once approved, you can start trading stocks and ETFs",
                "Consider enabling crypto trading if available in your state"
            ]
        elif workflow_type == 'crypto':
            return [
                "Crypto account will be reviewed by compliance team",
                "You will receive email notification within 1-2 business days",
                "Once approved, you can start trading cryptocurrencies",
                "Check your state's crypto trading eligibility"
            ]
        else:
            return ["Account review in progress"]
