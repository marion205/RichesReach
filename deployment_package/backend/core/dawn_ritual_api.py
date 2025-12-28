"""
Dawn Ritual API
Daily ritual that syncs Yodlee transactions and returns motivational haikus
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional
import logging
import sys
import os
import secrets
from datetime import datetime, timedelta

# Setup logger
logger = logging.getLogger(__name__)

# Django imports
import django
from django.conf import settings
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
    django.setup()

from django.contrib.auth import get_user_model
from django.db import connections
from asgiref.sync import sync_to_async

User = get_user_model()

# Try to import Yodlee client
try:
    from .yodlee_client import YodleeClient
    from .banking_models import BankAccount, BankTransaction
    YODLEE_AVAILABLE = True
except ImportError:
    YODLEE_AVAILABLE = False
    logger.warning("Yodlee not available for Dawn Ritual")

router = APIRouter(prefix="/api/rituals/dawn", tags=["rituals"])

# ============================================================================
# Haiku Generator
# ============================================================================

HAIKUS = [
    "From grocery shadows to investment light\nYour wealth awakens, bold and bright.",
    "Each transaction, a seed in the ground\nWatch your fortune grow, without a sound.",
    "Morning sun rises, accounts align\nFinancial freedom, truly divine.",
    "Small steps today, mountains tomorrow\nYour wealth path, no need to borrow.",
    "Dawn breaks through, clearing the way\nYour financial future, bright as day.",
    "Pennies saved today, dollars earned tomorrow\nYour wealth journey, no need to borrow.",
    "Transactions flow, like morning streams\nBuilding wealth, fulfilling dreams.",
    "From daily spending to smart investing\nYour financial future, truly uplifting.",
    "Each dollar tracked, each goal in sight\nYour wealth awakens, bold and bright.",
    "Morning ritual, wealth aligned\nFinancial peace, truly refined.",
]

def generate_haiku(transactions_synced: int = 0) -> str:
    """Generate a motivational haiku based on transaction sync"""
    import random
    
    # Select haiku based on sync success
    if transactions_synced > 0:
        # Use success-themed haikus
        success_haikus = [
            "From grocery shadows to investment light\nYour wealth awakens, bold and bright.",
            "Each transaction, a seed in the ground\nWatch your fortune grow, without a sound.",
            "Transactions flow, like morning streams\nBuilding wealth, fulfilling dreams.",
        ]
        return random.choice(success_haikus)
    else:
        # Use general motivational haikus
        return random.choice(HAIKUS)

# ============================================================================
# Authentication Helper
# ============================================================================

async def get_current_user(authorization: Optional[str] = Header(None)) -> User:
    """Get current user from token"""
    if not authorization or not authorization.startswith('Bearer '):
        # Development fallback
        import asyncio
        def get_user_sync():
            connections.close_all()
            user = User.objects.first()
            if user:
                return user
            return User.objects.create_user(
                email='test@example.com',
                name='Test User',
                password=os.getenv('DEV_TEST_USER_PASSWORD', secrets.token_urlsafe(16))
            )
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, get_user_sync)
    
    token = authorization[7:]
    
    # Dev token handling
    if token.startswith('dev-token-'):
        import asyncio
        def get_user_sync():
            connections.close_all()
            user = User.objects.first()
            if user:
                return user
            return User.objects.create_user(
                email='test@example.com',
                name='Test User',
                password=os.getenv('DEV_TEST_USER_PASSWORD', secrets.token_urlsafe(16))
            )
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, get_user_sync)
    
    # Real JWT token handling would go here
    # For now, use fallback
    import asyncio
    def get_user_sync():
        connections.close_all()
        return User.objects.first() or User.objects.create_user(
            email='test@example.com',
            name='Test User',
                password=os.getenv('DEV_TEST_USER_PASSWORD', secrets.token_urlsafe(16))
        )
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_user_sync)

# ============================================================================
# Request/Response Models
# ============================================================================

class DawnRitualRequest(BaseModel):
    pass  # No parameters needed

class DawnRitualResponse(BaseModel):
    transactionsSynced: int
    haiku: str
    timestamp: str

# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/perform", response_model=DawnRitualResponse)
async def perform_dawn_ritual(
    request: DawnRitualRequest,
    user: User = Depends(get_current_user)
):
    """
    Perform the dawn ritual: sync Yodlee transactions and return haiku
    """
    try:
        import asyncio
        
        def sync_transactions_sync():
            """Sync transactions synchronously"""
            connections.close_all()
            
            if not YODLEE_AVAILABLE:
                logger.warning("Yodlee not available, skipping transaction sync")
                return 0
            
            # Check if Yodlee is enabled
            if os.getenv('USE_YODLEE', 'false').lower() != 'true':
                logger.info("Yodlee disabled, skipping sync")
                return 0
            
            try:
                yodlee = YodleeClient()
                user_id_str = str(user.id)
                
                # Get all bank accounts for user
                bank_accounts = BankAccount.objects.filter(user=user)
                if not bank_accounts.exists():
                    logger.info(f"No bank accounts found for user {user.id}")
                    return 0
                
                # Sync transactions for last 24 hours
                to_date = datetime.now().date()
                from_date = to_date - timedelta(days=1)
                
                total_synced = 0
                for account in bank_accounts:
                    if not account.yodlee_account_id:
                        continue
                    
                    try:
                        transactions = yodlee.get_transactions(
                            user_id_str,
                            account_id=account.yodlee_account_id,
                            from_date=from_date.strftime('%Y-%m-%d'),
                            to_date=to_date.strftime('%Y-%m-%d'),
                        )
                        
                        # Count new transactions
                        for txn in transactions:
                            normalized = YodleeClient.normalize_transaction(txn)
                            txn_obj, created = BankTransaction.objects.update_or_create(
                                bank_account=account,
                                yodlee_transaction_id=normalized['yodlee_transaction_id'],
                                defaults={
                                    'user': user,
                                    'amount': normalized['amount'],
                                    'currency': normalized['currency'],
                                    'description': normalized['description'],
                                    'merchant_name': normalized['merchant_name'],
                                    'category': normalized['category'],
                                    'subcategory': normalized['subcategory'],
                                    'transaction_type': normalized['transaction_type'],
                                    'posted_date': datetime.strptime(normalized['posted_date'], '%Y-%m-%d').date() if normalized['posted_date'] else to_date,
                                    'transaction_date': datetime.strptime(normalized['transaction_date'], '%Y-%m-%d').date() if normalized['transaction_date'] else None,
                                    'status': normalized['status'],
                                    'raw_json': normalized['raw_json'],
                                }
                            )
                            if created:
                                total_synced += 1
                    except Exception as e:
                        logger.warning(f"Error syncing account {account.id}: {e}")
                        continue
                
                logger.info(f"Synced {total_synced} transactions for dawn ritual")
                return total_synced
                
            except Exception as e:
                logger.error(f"Error in Yodlee sync: {e}")
                return 0
        
        loop = asyncio.get_event_loop()
        transactions_synced = await loop.run_in_executor(None, sync_transactions_sync)
        
        # Generate haiku
        haiku = generate_haiku(transactions_synced)
        
        return DawnRitualResponse(
            transactionsSynced=transactions_synced,
            haiku=haiku,
            timestamp=datetime.now().isoformat(),
        )
        
    except Exception as e:
        logger.error(f"Error performing dawn ritual: {e}")
        # Return fallback response
        return DawnRitualResponse(
            transactionsSynced=0,
            haiku=generate_haiku(0),
            timestamp=datetime.now().isoformat(),
        )

