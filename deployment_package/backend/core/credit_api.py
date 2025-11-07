"""
Credit Building API
FastAPI endpoints for credit score tracking, card management, and projections
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional, List
import logging
import sys
import os
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

# Try to import credit models
try:
    from .credit_models import CreditScore, CreditCard, CreditAction, CreditProjection
    CREDIT_MODELS_AVAILABLE = True
except ImportError:
    CREDIT_MODELS_AVAILABLE = False
    logger.warning("Credit models not available")

router = APIRouter(prefix="/api/credit", tags=["credit"])

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
                password='test123'
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
                password='test123'
            )
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, get_user_sync)
    
    # Real JWT token handling would go here
    import asyncio
    def get_user_sync():
        connections.close_all()
        return User.objects.first() or User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='test123'
        )
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_user_sync)

# ============================================================================
# Request/Response Models
# ============================================================================

class CreditScoreResponse(BaseModel):
    score: int
    scoreRange: str
    lastUpdated: str
    provider: str
    factors: Optional[dict] = None

class CreditCardResponse(BaseModel):
    id: int
    name: str
    limit: float
    balance: float
    utilization: float
    yodleeAccountId: Optional[str] = None
    lastSynced: Optional[str] = None
    paymentDueDate: Optional[str] = None
    minimumPayment: Optional[float] = None

class CreditProjectionResponse(BaseModel):
    scoreGain6m: int
    topAction: str
    confidence: float
    factors: Optional[dict] = None

class CreditSnapshotResponse(BaseModel):
    score: CreditScoreResponse
    cards: List[CreditCardResponse]
    utilization: dict
    projection: Optional[CreditProjectionResponse] = None
    actions: List[dict]
    shield: Optional[List[dict]] = None

class CreditCardRecommendationResponse(BaseModel):
    id: str
    name: str
    type: str
    deposit: Optional[float] = None
    annualFee: float
    apr: float
    description: str
    benefits: List[str]
    preQualified: bool
    applicationUrl: Optional[str] = None

# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/score", response_model=CreditScoreResponse)
async def get_credit_score(user: User = Depends(get_current_user)):
    """Get user's current credit score"""
    if not CREDIT_MODELS_AVAILABLE:
        # Return mock data for development
        return CreditScoreResponse(
            score=580,
            scoreRange="Fair",
            lastUpdated=datetime.now().isoformat(),
            provider="self_reported",
            factors={
                "paymentHistory": 35,
                "utilization": 30,
                "creditAge": 15,
                "creditMix": 10,
                "inquiries": 10
            }
        )
    
    try:
        import asyncio
        
        def get_score_sync():
            connections.close_all()
            from django.utils import timezone as django_timezone
            score_obj = CreditScore.objects.filter(user=user).order_by('-date').first()
            if not score_obj:
                # Create default score if none exists
                score_obj = CreditScore.objects.create(
                    user=user,
                    score=580,
                    provider='self_reported',
                    date=django_timezone.now().date()
                )
            return score_obj
        
        loop = asyncio.get_event_loop()
        score_obj = await loop.run_in_executor(None, get_score_sync)
        
        return CreditScoreResponse(
            score=score_obj.score,
            scoreRange=score_obj.get_score_range(),
            lastUpdated=score_obj.date.isoformat(),
            provider=score_obj.provider,
            factors=score_obj.factors or {}
        )
    except Exception as e:
        logger.error(f"Error fetching credit score: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class RefreshScoreRequest(BaseModel):
    score: Optional[int] = None
    provider: str = "self_reported"

@router.post("/score/refresh", response_model=CreditScoreResponse)
async def refresh_credit_score(
    request: RefreshScoreRequest,
    user: User = Depends(get_current_user)
):
    """Refresh or update credit score (self-reported or from API)"""
    if not CREDIT_MODELS_AVAILABLE:
        return CreditScoreResponse(
            score=request.score or 580,
            scoreRange="Fair",
            lastUpdated=datetime.now().isoformat(),
            provider=request.provider
        )
    
    try:
        import asyncio
        
        def update_score_sync():
            connections.close_all()
            from django.utils import timezone as django_timezone
            today = django_timezone.now().date()
            score_obj, created = CreditScore.objects.update_or_create(
                user=user,
                date=today,
                provider=request.provider,
                defaults={
                    'score': request.score or 580,
                    'factors': {}
                }
            )
            return score_obj
        
        loop = asyncio.get_event_loop()
        score_obj = await loop.run_in_executor(None, update_score_sync)
        
        return CreditScoreResponse(
            score=score_obj.score,
            scoreRange=score_obj.get_score_range(),
            lastUpdated=score_obj.date.isoformat(),
            provider=score_obj.provider,
            factors=score_obj.factors or {}
        )
    except Exception as e:
        logger.error(f"Error refreshing credit score: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cards", response_model=List[CreditCardResponse])
async def get_credit_cards(user: User = Depends(get_current_user)):
    """Get user's credit cards"""
    if not CREDIT_MODELS_AVAILABLE:
        return []
    
    try:
        import asyncio
        
        def get_cards_sync():
            connections.close_all()
            cards = CreditCard.objects.filter(user=user)
            return list(cards)
        
        loop = asyncio.get_event_loop()
        cards = await loop.run_in_executor(None, get_cards_sync)
        
        return [
            CreditCardResponse(
                id=card.id,
                name=card.name,
                limit=float(card.limit),
                balance=float(card.balance),
                utilization=card.utilization,
                yodleeAccountId=card.yodlee_account_id,
                lastSynced=card.last_synced.isoformat() if card.last_synced else None,
                paymentDueDate=card.payment_due_date.isoformat() if card.payment_due_date else None,
                minimumPayment=float(card.minimum_payment) if card.minimum_payment else None
            )
            for card in cards
        ]
    except Exception as e:
        logger.error(f"Error fetching credit cards: {e}")
        return []


@router.get("/utilization", response_model=dict)
async def get_credit_utilization(user: User = Depends(get_current_user)):
    """Calculate credit utilization"""
    if not CREDIT_MODELS_AVAILABLE:
        return {
            "totalLimit": 1000,
            "totalBalance": 450,
            "currentUtilization": 0.45,
            "optimalUtilization": 0.3,
            "paydownSuggestion": 150,
            "projectedScoreGain": 8
        }
    
    try:
        import asyncio
        
        def calculate_utilization_sync():
            connections.close_all()
            cards = CreditCard.objects.filter(user=user)
            total_limit = sum(float(card.limit) for card in cards)
            total_balance = sum(float(card.balance) for card in cards)
            current_util = total_balance / total_limit if total_limit > 0 else 0
            optimal_util = 0.3
            target_balance = total_limit * optimal_util
            paydown_suggestion = max(0, total_balance - target_balance)
            
            # Estimate score gain (rough calculation)
            if current_util > 0.5:
                projected_gain = 15
            elif current_util > 0.3:
                projected_gain = 8
            else:
                projected_gain = 0
            
            return {
                "totalLimit": total_limit,
                "totalBalance": total_balance,
                "currentUtilization": current_util,
                "optimalUtilization": optimal_util,
                "paydownSuggestion": paydown_suggestion,
                "projectedScoreGain": projected_gain
            }
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, calculate_utilization_sync)
    except Exception as e:
        logger.error(f"Error calculating utilization: {e}")
        return {
            "totalLimit": 0,
            "totalBalance": 0,
            "currentUtilization": 0,
            "optimalUtilization": 0.3,
            "paydownSuggestion": 0,
            "projectedScoreGain": 0
        }


@router.get("/projection", response_model=CreditProjectionResponse)
async def get_credit_projection(user: User = Depends(get_current_user)):
    """Get ML-powered credit score projection using real transaction data"""
    try:
        import asyncio
        from .credit_ml_service import CreditMLService
        from .yodlee_client import YodleeClient
        from .banking_models import BankTransaction, BankAccount
        
        def get_projection_sync():
            connections.close_all()
            ml_service = CreditMLService()
            
            # Get current score
            current_score_obj = CreditScore.objects.filter(user=user).order_by('-date').first()
            if not current_score_obj:
                current_score = 580
            else:
                current_score = current_score_obj.score
            
            # Get credit cards
            cards = CreditCard.objects.filter(user=user)
            cards_data = [
                {
                    'id': card.id,
                    'name': card.name,
                    'limit': float(card.limit),
                    'balance': float(card.balance),
                    'utilization': card.utilization,
                    'yodlee_account_id': card.yodlee_account_id,
                }
                for card in cards
            ]
            
            # Get transactions from Yodlee (last 90 days)
            transactions = []
            try:
                yodlee = YodleeClient()
                user_id_str = str(user.id)
                
                # Get bank accounts
                bank_accounts = BankAccount.objects.filter(user=user)
                
                # Get transactions for credit card accounts
                from django.utils import timezone as django_timezone
                from_date = (django_timezone.now() - timedelta(days=90)).strftime('%Y-%m-%d')
                to_date = django_timezone.now().strftime('%Y-%m-%d')
                
                for account in bank_accounts:
                    if account.yodlee_account_id:
                        try:
                            yodlee_txns = yodlee.get_transactions(
                                user_id_str,
                                account_id=account.yodlee_account_id,
                                from_date=from_date,
                                to_date=to_date,
                            )
                            
                            # Also get from database
                            from django.utils import timezone as django_timezone
                            db_txns = BankTransaction.objects.filter(
                                bank_account=account,
                                posted_date__gte=django_timezone.now().date() - timedelta(days=90)
                            )
                            
                            # Combine and normalize
                            for txn in yodlee_txns + list(db_txns):
                                transactions.append({
                                    'amount': float(txn.get('amount', 0) if isinstance(txn, dict) else getattr(txn, 'amount', 0)),
                                    'posted_date': str(txn.get('posted_date', '') if isinstance(txn, dict) else getattr(txn, 'posted_date', '')),
                                    'category': txn.get('category', '') if isinstance(txn, dict) else getattr(txn, 'category', ''),
                                    'account_type': account.account_type or '',
                                })
                        except Exception as e:
                            logger.warning(f"Error fetching transactions for account {account.id}: {e}")
            except Exception as e:
                logger.warning(f"Error fetching Yodlee transactions: {e}")
            
            # Use ML service to analyze
            projection = ml_service.analyze_transactions_for_credit(
                transactions=transactions,
                credit_cards=cards_data,
                current_score=current_score,
                days=90
            )
            
            return CreditProjectionResponse(
                scoreGain6m=projection.get('scoreGain6m', 15),
                topAction=projection.get('topAction', 'SET_UP_AUTOPAY'),
                confidence=projection.get('confidence', 0.5),
                factors=projection.get('factors', {})
            )
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, get_projection_sync)
    except Exception as e:
        logger.error(f"Error getting projection: {e}")
        return CreditProjectionResponse(
            scoreGain6m=42,
            topAction="SET_UP_AUTOPAY",
            confidence=0.71,
            factors={}
        )


@router.get("/snapshot", response_model=CreditSnapshotResponse)
async def get_credit_snapshot(user: User = Depends(get_current_user)):
    """Get complete credit snapshot (score, cards, utilization, projection)"""
    try:
        # Get all data
        score_response = await get_credit_score(user)
        cards_response = await get_credit_cards(user)
        utilization_response = await get_credit_utilization(user)
        projection_response = await get_credit_projection(user)
        
        # Get actions
        import asyncio
        def get_actions_sync():
            connections.close_all()
            if not CREDIT_MODELS_AVAILABLE:
                return []
            actions = CreditAction.objects.filter(user=user).order_by('-created_at')[:5]
            return [
                {
                    "id": action.id,
                    "type": action.action_type,
                    "title": action.title,
                    "description": action.description,
                    "completed": action.completed,
                    "projectedScoreGain": action.projected_score_gain,
                    "dueDate": action.due_date.isoformat() if action.due_date else None
                }
                for action in actions
            ]
        
        loop = asyncio.get_event_loop()
        actions = await loop.run_in_executor(None, get_actions_sync)
        
        # Get shield alerts
        shield = []
        for card in cards_response:
            if card.paymentDueDate:
                due_date = datetime.fromisoformat(card.paymentDueDate.replace('Z', '+00:00'))
                days_until = (due_date.date() - datetime.now().date()).days
                if 0 <= days_until <= 7:
                    shield.append({
                        "type": "PAYMENT_DUE",
                        "inDays": days_until,
                        "message": f"Payment due for {card.name} in {days_until} days",
                        "suggestion": "PAY_NOW"
                    })
        
        if utilization_response.get("currentUtilization", 0) > 0.5:
            shield.append({
                "type": "HIGH_UTILIZATION",
                "inDays": None,
                "message": f"Utilization is {utilization_response['currentUtilization']*100:.0f}% - aim for under 30%",
                "suggestion": "REDUCE_UTILIZATION"
            })
        
        return CreditSnapshotResponse(
            score=score_response,
            cards=cards_response,
            utilization=utilization_response,
            projection=projection_response,
            actions=actions,
            shield=shield if shield else None
        )
    except Exception as e:
        logger.error(f"Error getting credit snapshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cards/recommendations", response_model=List[CreditCardRecommendationResponse])
async def get_card_recommendations(user: User = Depends(get_current_user)):
    """Get credit card recommendations (secured cards for bad credit)"""
    # Mock recommendations - in production, integrate with card API
    recommendations = [
        CreditCardRecommendationResponse(
            id="capital_one_secured",
            name="Capital One Platinum Secured",
            type="secured",
            deposit=49,
            annualFee=0,
            apr=26.99,
            description="$49 deposit for $200 line. Auto-review for limit increases after 6 months.",
            benefits=["No annual fee", "Auto-review for upgrades", "Reports to all 3 bureaus"],
            preQualified=True,
            applicationUrl="https://www.capitalone.com/credit-cards/secured/"
        ),
        CreditCardRecommendationResponse(
            id="discover_secured",
            name="Discover it Secured",
            type="secured",
            deposit=200,
            annualFee=0,
            apr=27.24,
            description="Matches your deposit. Cashback rewards (1-2%). Path to unsecured upgrade.",
            benefits=["Cashback rewards", "No annual fee", "Upgrade path"],
            preQualified=True,
            applicationUrl="https://www.discover.com/credit-cards/secured/"
        ),
        CreditCardRecommendationResponse(
            id="opensky_secured",
            name="OpenSky Secured Visa",
            type="secured",
            deposit=200,
            annualFee=35,
            apr=17.39,
            description="No credit check required. $200 minimum deposit. $35 annual fee.",
            benefits=["No credit check", "Builds credit history", "Reports to all 3 bureaus"],
            preQualified=True,
            applicationUrl="https://www.openskycc.com/"
        )
    ]
    
    return recommendations

