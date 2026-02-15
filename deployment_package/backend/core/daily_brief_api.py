"""
Daily Brief API
FastAPI endpoints for daily brief generation, retrieval, and progress tracking
"""
from fastapi import APIRouter, HTTPException, Request, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date, datetime, timedelta
from decimal import Decimal
import logging
import os
import sys

# Setup Django
try:
    import django
    if 'DJANGO_SETTINGS_MODULE' not in os.environ:
        backend_path = os.path.join(os.path.dirname(__file__), '..')
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
    django.setup()
    
    from django.contrib.auth import get_user_model
    from django.utils import timezone
    from asgiref.sync import sync_to_async
    from core.daily_brief_models import (
        DailyBrief, UserStreak, UserProgress, UserAchievement, DailyBriefCompletion
    )
    from core.models import User
    DJANGO_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Django not available for Daily Brief API: {e}")
    DJANGO_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/daily-brief", tags=["daily-brief"])

# Initialize services (use market data facade for consistency)
_portfolio_service = None

def _get_market_data_service():
    """Return shared market data service via facade (MarketDataAPIService)."""
    try:
        from .market_data_manager import get_market_data_service
        return get_market_data_service()
    except Exception as e:
        logger.warning(f"Market data service not available: {e}")
        return None

def _get_portfolio_service():
    """Lazy load portfolio service"""
    global _portfolio_service
    if _portfolio_service is None:
        try:
            from .portfolio_service import PortfolioService
            _portfolio_service = PortfolioService()
        except Exception as e:
            logger.warning(f"Portfolio service not available: {e}")
            _portfolio_service = None
    return _portfolio_service


# Pydantic models
class DailyBriefResponse(BaseModel):
    id: str
    date: str
    market_summary: str
    personalized_action: str
    action_type: str
    lesson_id: Optional[str] = None
    lesson_title: Optional[str] = None
    lesson_content: Optional[str] = None
    experience_level: str
    is_completed: bool
    streak: int
    weekly_progress: Dict[str, Any]
    confidence_score: int


class CompleteBriefRequest(BaseModel):
    brief_id: Optional[str] = None  # For idempotency
    time_spent_seconds: int
    sections_viewed: List[str]
    lesson_completed: bool = False
    action_completed: bool = False


class ProgressResponse(BaseModel):
    streak: int
    longest_streak: int
    weekly_briefs_completed: int
    weekly_goal: int
    weekly_lessons_completed: int
    monthly_lessons_completed: int
    monthly_goal: int
    concepts_learned: int
    current_level: str
    confidence_score: int
    achievements: List[Dict[str, Any]]


# Helper function to get user from token
async def get_user_from_token(request: Request) -> Optional[User]:
    """Extract user from Authorization token (JWT or dev-token)."""
    if not DJANGO_AVAILABLE:
        return None

    try:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header:
            return None

        token = None
        if auth_header.startswith("Token "):
            token = auth_header.replace("Token ", "")
        elif auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")

        if not token:
            return None

        User = get_user_model()

        # Dev tokens: use same logic as core.authentication.get_user_from_token
        if token.startswith("dev-token-"):
            user = await sync_to_async(User.objects.filter(email='demo@example.com').first)()
            if not user:
                user = await sync_to_async(User.objects.first)()
            if user:
                return user
            # No users at all: get_or_create demo so daily brief works
            user, _ = await sync_to_async(User.objects.get_or_create)(
                email='demo@example.com',
                defaults={'name': 'Demo User'}
            )
            user.set_password('demo123')
            await sync_to_async(user.save)()
            return user

        # JWT: graphql_jwt
        try:
            from graphql_jwt.shortcuts import get_user_by_token
            user = await sync_to_async(get_user_by_token)(token)
            return user
        except Exception:
            user = await sync_to_async(User.objects.filter(email='demo@example.com').first)()
            if not user:
                user = await sync_to_async(User.objects.first)()
            if user:
                return user
            # Token present but invalid and no users: get_or_create demo for dev UX
            user, _ = await sync_to_async(User.objects.get_or_create)(
                email='demo@example.com',
                defaults={'name': 'Demo User'}
            )
            user.set_password('demo123')
            await sync_to_async(user.save)()
            return user
    except Exception as e:
        logger.error(f"Error getting user from token: {e}")
        return None


# Helper function to generate daily brief content
async def generate_brief_content(user: User, target_date: date) -> Dict[str, Any]:
    """Generate daily brief content based on user profile with real market and portfolio data"""
    
    # Get user progress
    progress, _ = await sync_to_async(UserProgress.objects.get_or_create)(
        user=user,
        defaults={'current_level': 'beginner', 'confidence_score': 5}
    )
    
    # Fetch real market data
    market_summary = await _generate_real_market_summary()
    
    # Get real portfolio data for personalized actions
    portfolio_data = await _get_user_portfolio_analysis(user)
    
    # Generate personalized action based on real portfolio data and user level
    personalized_result = await _generate_personalized_action(
        user, progress, portfolio_data
    )
    personalized_action = personalized_result['action']
    action_type = personalized_result['action_type']
    lesson_title = personalized_result.get('lesson_title')
    lesson_content = personalized_result.get('lesson_content')
    
    return {
        'market_summary': market_summary,
        'personalized_action': personalized_action,
        'action_type': action_type,
        'lesson_title': lesson_title,
        'lesson_content': lesson_content,
        'experience_level': progress.current_level,
    }


def _normalize_market_overview_for_brief(overview: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Normalize facade overview (indices/average_change) to brief shape (change_percent, change, etc.)."""
    if not overview:
        return None
    # Facade (MarketDataAPIService) returns: indices, sentiment, average_change, timestamp
    avg = overview.get("average_change")
    if avg is not None:
        # Use ^GSPC if present for price/change
        indices = overview.get("indices") or {}
        gspc = indices.get("^GSPC") or {}
        change = gspc.get("change") if isinstance(gspc.get("change"), (int, float)) else None
        current_price = gspc.get("price") or gspc.get("current_price")
        return {
            "change_percent": float(avg),
            "change": change if change is not None else 0,
            "current_price": current_price or 0,
            "volatility": overview.get("volatility", 0.15),
        }
    # Legacy MarketDataService shape: change_percent, sp500_return, etc.
    if overview.get("change_percent") is not None or overview.get("sp500_return") is not None:
        return overview
    return None


async def _generate_real_market_summary() -> str:
    """Generate market summary using real market data (via market data facade)."""
    try:
        market_service = _get_market_data_service()
        if market_service:
            # MarketDataAPIService.get_market_overview is async (facade)
            market_overview = await market_service.get_market_overview()
            logger.info(f"Market overview fetched: {market_overview}")
            
            # Normalize to brief shape (facade returns indices/average_change; legacy returns change_percent/sp500_return)
            normalized = _normalize_market_overview_for_brief(market_overview)
            if normalized:
                market_overview = normalized
            elif market_overview and market_overview.get("method") == "synthetic":
                logger.warning("⚠️ Market data service returned synthetic data - using generic message")
                return (
                    "Markets are active today. Check your portfolio to see how your investments "
                    "are performing. Remember: daily moves are normal—focus on your long-term goals."
                )
            
            # Handle both normalized (change_percent) and legacy (sp500_return)
            change_pct = None
            if market_overview and market_overview.get("change_percent") is not None:
                change_pct = market_overview.get("change_percent", 0)
            elif market_overview and market_overview.get("sp500_return") is not None:
                change_pct = market_overview.get("sp500_return", 0) * 100
            
            if change_pct is not None:
                change = market_overview.get('change', 0)
                current_price = market_overview.get('current_price', 0)
                volatility = market_overview.get('volatility', 0.15)
                
                # Format in plain English
                direction = "up" if change_pct > 0 else "down" if change_pct < 0 else "flat"
                abs_change_pct = abs(change_pct)
                
                summary_parts = [
                    f"Markets are {direction} {abs_change_pct:.2f}% today."
                ]
                
                # Add context based on magnitude
                if abs_change_pct > 2:
                    summary_parts.append("That's a significant move—markets are reacting to major news.")
                elif abs_change_pct > 1:
                    summary_parts.append("That's a notable move worth paying attention to.")
                else:
                    summary_parts.append("Markets are relatively calm today.")
                
                # Add volatility context
                if volatility and volatility > 0.02:
                    summary_parts.append("Volatility is elevated, which means prices are moving more than usual.")
                elif volatility and volatility < 0.01:
                    summary_parts.append("Volatility is low, indicating a calm trading day.")
                
                # Add simple explanation
                if change_pct > 0:
                    summary_parts.append("When markets go up, it generally means investors are optimistic about the economy.")
                elif change_pct < 0:
                    summary_parts.append("When markets go down, it often reflects concerns about economic conditions.")
                
                return " ".join(summary_parts)
        
        # Fallback to simple message if service unavailable
        logger.warning("Market data service unavailable, using fallback message")
        return (
            "Markets are active today. Check your portfolio to see how your investments "
            "are performing. Remember: daily moves are normal—focus on your long-term goals."
        )
    except Exception as e:
        logger.error(f"Error generating market summary: {e}", exc_info=True)
        return (
            "Markets are active today. Check your portfolio to see how your investments "
            "are performing. Remember: daily moves are normal—focus on your long-term goals."
        )


async def _get_user_portfolio_analysis(user: User) -> Dict[str, Any]:
    """Get real portfolio analysis for user"""
    try:
        portfolio_service = _get_portfolio_service()
        if portfolio_service:
            portfolios_data = await sync_to_async(portfolio_service.get_user_portfolios)(user)
            
            if portfolios_data and portfolios_data.get('portfolios'):
                total_value = float(portfolios_data.get('total_value', 0))
                portfolios = portfolios_data.get('portfolios', [])
                
                # Analyze holdings
                all_holdings = []
                sector_allocation = {}
                total_shares_value = Decimal('0')
                
                for portfolio in portfolios:
                    for holding in portfolio.get('holdings', []):
                        stock = holding.get('stock')
                        if stock:
                            symbol = stock.symbol if hasattr(stock, 'symbol') else str(stock)
                            shares = float(holding.get('shares', 0))
                            current_price = float(holding.get('current_price', 0) or holding.get('average_price', 0))
                            value = shares * current_price
                            
                            all_holdings.append({
                                'symbol': symbol,
                                'shares': shares,
                                'value': value,
                                'current_price': current_price,
                            })
                            total_shares_value += Decimal(str(value))
                
                # Calculate concentration
                if all_holdings and total_shares_value > 0:
                    sorted_holdings = sorted(all_holdings, key=lambda x: x['value'], reverse=True)
                    top_holding = sorted_holdings[0]
                    top_holding_pct = (float(top_holding['value']) / float(total_shares_value)) * 100
                    
                    return {
                        'has_portfolio': True,
                        'total_value': float(total_shares_value),
                        'holdings_count': len(all_holdings),
                        'top_holding': top_holding['symbol'],
                        'top_holding_pct': top_holding_pct,
                        'holdings': sorted_holdings[:5],  # Top 5
                        'is_concentrated': top_holding_pct > 50,
                    }
        
        return {
            'has_portfolio': False,
            'total_value': 0,
            'holdings_count': 0,
        }
    except Exception as e:
        logger.error(f"Error analyzing portfolio: {e}", exc_info=True)
        return {
            'has_portfolio': False,
            'total_value': 0,
            'holdings_count': 0,
        }


async def _generate_personalized_action(
    user: User, 
    progress: 'UserProgress', 
    portfolio_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate personalized action based on real portfolio data"""
    
    # If user has no portfolio, suggest starting one
    if not portfolio_data.get('has_portfolio') or portfolio_data.get('holdings_count', 0) == 0:
        if progress.current_level == 'beginner':
            return {
                'action': (
                    "Today's action: Start building your portfolio. "
                    "You don't have any investments yet. Want to learn how to get started? "
                    "We'll walk you through your first investment step by step."
                ),
                'action_type': 'learn_lesson',
                'lesson_title': "How to start investing",
                'lesson_content': (
                    "Starting your investment journey can feel overwhelming, but it's simpler than you think.\n\n"
                    "Here's the basics:\n\n"
                    "1. Start small: You don't need thousands of dollars. Many platforms let you start with just $1.\n\n"
                    "2. Diversify: Don't put all your money in one stock. Spread it across different companies and sectors.\n\n"
                    "3. Think long-term: Investing is a marathon, not a sprint. Focus on building wealth over years, not days.\n\n"
                    "4. Keep learning: The more you understand, the better decisions you'll make.\n\n"
                    "Ready to make your first investment? We can help you get started."
                ),
            }
        else:
            return {
                'action': (
                    "Today's action: Build your portfolio. "
                    "You don't have any positions yet. Start by adding your first investment."
                ),
                'action_type': 'set_goal',
            }
    
    # User has portfolio - analyze it
    total_value = portfolio_data.get('total_value', 0)
    holdings_count = portfolio_data.get('holdings_count', 0)
    is_concentrated = portfolio_data.get('is_concentrated', False)
    top_holding = portfolio_data.get('top_holding', '')
    top_holding_pct = portfolio_data.get('top_holding_pct', 0)
    
    if progress.current_level == 'beginner':
        # Beginner: Focus on diversification
        if is_concentrated:
            return {
                'action': (
                    f"Today's action: Review your portfolio diversification. "
                    f"You're {top_holding_pct:.0f}% invested in {top_holding}. "
                    f"That's risky if {top_holding} drops. Want to learn about diversification? (2-min lesson)"
                ),
                'action_type': 'learn_lesson',
                'lesson_title': "Why diversification matters",
                'lesson_content': (
                    f"You've been asking about diversification. Here's why it matters:\n\n"
                    f"Think of your portfolio like a pizza. If you only order pepperoni, "
                    f"and pepperoni goes bad, you're stuck. But if you have pepperoni, "
                    f"cheese, and veggies, you're safer.\n\n"
                    f"Same with stocks. If you only own {top_holding} and it crashes, "
                    f"you lose a big chunk of your portfolio. But if you own {top_holding}, "
                    f"plus stocks from other sectors, you're protected.\n\n"
                    f"Your portfolio is {top_holding_pct:.0f}% in {top_holding}. "
                    f"Consider spreading your investments across different companies and sectors."
                ),
            }
        else:
            return {
                'action': (
                    f"Today's action: Review your portfolio. "
                    f"You have {holdings_count} holdings worth ${total_value:,.0f}. "
                    f"Your diversification looks good! Want to learn about rebalancing?"
                ),
                'action_type': 'learn_lesson',
                'lesson_title': "Portfolio rebalancing basics",
                'lesson_content': (
                    "Rebalancing means adjusting your portfolio to maintain your target allocation.\n\n"
                    "Over time, some investments grow faster than others. This changes your "
                    "risk level. Rebalancing helps you stay on track with your goals.\n\n"
                    "For example, if you want 60% stocks and 40% bonds, but stocks have "
                    "grown to 70%, you'd sell some stocks and buy bonds to get back to 60/40."
                ),
            }
    
    elif progress.current_level == 'intermediate':
        # Intermediate: Focus on optimization
        # Check for tax-loss harvesting opportunities (simplified)
        return {
            'action': (
                f"Today's action: Review your portfolio performance. "
                f"You have {holdings_count} positions worth ${total_value:,.0f}. "
                f"Check for tax-loss harvesting opportunities or rebalancing needs."
            ),
            'action_type': 'review_portfolio',
            'lesson_title': "Advanced portfolio optimization",
            'lesson_content': (
                "As an intermediate investor, you can start optimizing your portfolio.\n\n"
                "Tax-loss harvesting: Sell losing positions to offset gains and reduce taxes.\n\n"
                "Rebalancing: Adjust your allocation to maintain your target risk level.\n\n"
                "Review your positions regularly to ensure they still align with your goals."
            ),
        }
    
    else:  # advanced
        # Advanced: Focus on sophisticated strategies
        return {
            'action': (
                f"Today's action: Optimize your portfolio. "
                f"Your portfolio is worth ${total_value:,.0f} with {holdings_count} positions. "
                f"Review for rebalancing, tax optimization, or risk adjustments."
            ),
            'action_type': 'rebalance',
            'lesson_title': "Advanced portfolio management",
            'lesson_content': (
                "As an advanced investor, you can use sophisticated strategies:\n\n"
                "1. Tax-loss harvesting: Systematically realize losses to offset gains\n\n"
                "2. Sector rotation: Adjust allocations based on market cycles\n\n"
                "3. Risk management: Use options or hedging to protect gains\n\n"
                "4. Rebalancing: Maintain target allocations automatically"
            ),
        }


@router.get("/today", response_model=DailyBriefResponse)
async def get_today_brief(
    request: Request, 
    regenerate: bool = Query(False, description="Force regeneration of brief content")
):
    """Get today's daily brief for the user
    
    Args:
        regenerate: If True, force regeneration of brief content (useful for testing)
    """
    if not DJANGO_AVAILABLE:
        raise HTTPException(status_code=503, detail="Daily brief service not available")
    
    user = await get_user_from_token(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    today = timezone.now().date()
    
    # Get or create today's brief
    brief, created = await sync_to_async(DailyBrief.objects.get_or_create)(
        user=user,
        date=today,
        defaults={
            'market_summary': '',
            'personalized_action': '',
            'experience_level': 'beginner',
        }
    )
    
    # ALWAYS regenerate if brief contains old mock data patterns
    # Check for old mock data patterns to force regeneration
    old_mock_patterns = [
        "Markets are up 0.5% today. The Fed kept interest rates steady",
        "You're 80% in tech stocks",
        "You have $500 in unrealized losses",
        "Your allocation has drifted 5% from your target",
        "Your portfolio is doing fine—no action needed"  # Another mock pattern
    ]
    market_summary_text = brief.market_summary or ''
    personalized_action_text = brief.personalized_action or ''
    has_old_mock_data = (
        any(pattern in market_summary_text for pattern in old_mock_patterns) or
        any(pattern in personalized_action_text for pattern in old_mock_patterns)
    )
    
    # Force regeneration if we detect old mock data OR if regenerate is requested
    should_regenerate = created or not brief.market_summary or has_old_mock_data or regenerate
    
    if has_old_mock_data:
        logger.warning(f"⚠️ Detected old mock data in brief - forcing regeneration")
        logger.info(f"Market summary: {market_summary_text[:150]}")
        logger.info(f"Personalized action: {personalized_action_text[:150]}")
    
    if should_regenerate:
        logger.info(f"Regenerating daily brief for user {user.id} - created={created}, has_old_mock={has_old_mock_data}, regenerate={regenerate}")
        # Regenerate with real data
        content = await generate_brief_content(user, today)
        brief.market_summary = content['market_summary']
        brief.personalized_action = content['personalized_action']
        brief.action_type = content['action_type']
        brief.lesson_title = content['lesson_title']
        brief.lesson_content = content['lesson_content']
        brief.experience_level = content['experience_level']
        await sync_to_async(brief.save)()
        logger.info(f"Daily brief regenerated - market_summary preview: {brief.market_summary[:100]}...")
    
    # Get streak
    streak_obj, _ = await sync_to_async(UserStreak.objects.get_or_create)(user=user)
    
    # Get progress
    progress, _ = await sync_to_async(UserProgress.objects.get_or_create)(user=user)
    
    return DailyBriefResponse(
        id=str(brief.id),
        date=brief.date.isoformat(),
        market_summary=brief.market_summary,
        personalized_action=brief.personalized_action,
        action_type=brief.action_type,
        lesson_id=brief.lesson_id,
        lesson_title=brief.lesson_title,
        lesson_content=brief.lesson_content,
        experience_level=brief.experience_level,
        is_completed=brief.is_completed,
        streak=streak_obj.current_streak,
        weekly_progress={
            'briefs_completed': progress.weekly_briefs_completed,
            'goal': progress.weekly_goal,
            'lessons_completed': progress.weekly_lessons_completed,
        },
        confidence_score=progress.confidence_score,
    )


@router.delete("/today")
async def delete_today_brief(request: Request):
    """Delete today's brief to force regeneration (for testing)"""
    if not DJANGO_AVAILABLE:
        raise HTTPException(status_code=503, detail="Daily brief service not available")
    
    user = await get_user_from_token(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    today = timezone.now().date()
    
    try:
        brief = await sync_to_async(DailyBrief.objects.get)(user=user, date=today)
        await sync_to_async(brief.delete)()
        return {"success": True, "message": "Brief deleted. Next request will generate a new one."}
    except DailyBrief.DoesNotExist:
        return {"success": True, "message": "Brief does not exist."}


@router.post("/complete")
async def complete_brief(request: Request, completion: CompleteBriefRequest):
    """Mark daily brief as completed and update progress"""
    if not DJANGO_AVAILABLE:
        raise HTTPException(status_code=503, detail="Daily brief service not available")
    
    user = await get_user_from_token(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    today = timezone.now().date()
    
    # Get today's brief (by ID if provided, otherwise by date)
    try:
        if completion.brief_id:
            brief = await sync_to_async(DailyBrief.objects.get)(user=user, id=completion.brief_id)
        else:
            brief = await sync_to_async(DailyBrief.objects.get)(user=user, date=today)
    except DailyBrief.DoesNotExist:
        raise HTTPException(status_code=404, detail="Daily brief not found")
    
    # Check if already completed (idempotency)
    already_completed = brief.is_completed
    if already_completed:
        # Still return success data, but don't update again
        streak_obj, _ = await sync_to_async(UserStreak.objects.get_or_create)(user=user)
        progress, _ = await sync_to_async(UserProgress.objects.get_or_create)(user=user)
        
        return {
            "success": True,
            "already_completed": True,
            "streak": streak_obj.current_streak,
            "achievements_unlocked": []
        }
    
    # Mark as completed
    brief.is_completed = True
    brief.completed_at = timezone.now()
    brief.time_spent_seconds = completion.time_spent_seconds
    await sync_to_async(brief.save)()
    
    # Record completion (only if not already recorded)
    existing_completion = await sync_to_async(
        lambda: DailyBriefCompletion.objects.filter(brief=brief, user=user).exists()
    )()
    if not existing_completion:
        completion_record = await sync_to_async(DailyBriefCompletion.objects.create)(
            brief=brief,
            user=user,
            time_spent_seconds=completion.time_spent_seconds,
            sections_viewed=completion.sections_viewed,
            lesson_completed=completion.lesson_completed,
            action_completed=completion.action_completed,
        )
    
    # Update streak
    streak_obj, _ = await sync_to_async(UserStreak.objects.get_or_create)(user=user)
    await sync_to_async(streak_obj.update_streak)(today)
    
    # Update progress (only increment if not already completed)
    progress, _ = await sync_to_async(UserProgress.objects.get_or_create)(user=user)
    if not already_completed:
        progress.weekly_briefs_completed += 1
    if completion.lesson_completed:
        progress.weekly_lessons_completed += 1
        progress.monthly_lessons_completed += 1
        progress.concepts_learned += 1
        progress.lessons_completed += 1
    await sync_to_async(progress.save)()
    
    # Check for achievements
    achievements_unlocked = []
    
    # Streak achievements
    if streak_obj.current_streak == 3:
        achievement, created = await sync_to_async(UserAchievement.objects.get_or_create)(
            user=user,
            achievement_type='streak_3',
        )
        if created:
            achievements_unlocked.append('streak_3')
    
    if streak_obj.current_streak == 7:
        achievement, created = await sync_to_async(UserAchievement.objects.get_or_create)(
            user=user,
            achievement_type='streak_7',
        )
        if created:
            achievements_unlocked.append('streak_7')
    
    if streak_obj.current_streak == 30:
        achievement, created = await sync_to_async(UserAchievement.objects.get_or_create)(
            user=user,
            achievement_type='streak_30',
        )
        if created:
            achievements_unlocked.append('streak_30')
    
    # Lesson achievements
    if progress.concepts_learned == 10:
        achievement, created = await sync_to_async(UserAchievement.objects.get_or_create)(
            user=user,
            achievement_type='lessons_10',
        )
        if created:
            achievements_unlocked.append('lessons_10')
    
    if progress.concepts_learned == 25:
        achievement, created = await sync_to_async(UserAchievement.objects.get_or_create)(
            user=user,
            achievement_type='lessons_25',
        )
        if created:
            achievements_unlocked.append('lessons_25')
    
    if progress.concepts_learned == 50:
        achievement, created = await sync_to_async(UserAchievement.objects.get_or_create)(
            user=user,
            achievement_type='lessons_50',
        )
        if created:
            achievements_unlocked.append('lessons_50')
    
    # Weekly goal achievement
    if progress.weekly_briefs_completed >= progress.weekly_goal:
        achievement, created = await sync_to_async(UserAchievement.objects.get_or_create)(
            user=user,
            achievement_type='weekly_goal',
        )
        if created:
            achievements_unlocked.append('weekly_goal')
    
    # Confidence milestones
    if progress.confidence_score >= 7 and progress.confidence_score < 8:
        achievement, created = await sync_to_async(UserAchievement.objects.get_or_create)(
            user=user,
            achievement_type='confidence_7',
        )
        if created:
            achievements_unlocked.append('confidence_7')
    
    if progress.confidence_score >= 9:
        achievement, created = await sync_to_async(UserAchievement.objects.get_or_create)(
            user=user,
            achievement_type='confidence_9',
        )
        if created:
            achievements_unlocked.append('confidence_9')
    
    return JSONResponse({
        "success": True,
        "message": "Daily brief completed",
        "achievements_unlocked": achievements_unlocked,
        "streak": streak_obj.current_streak,
    })


@router.get("/progress", response_model=ProgressResponse)
async def get_progress(request: Request):
    """Get user's progress and achievements"""
    if not DJANGO_AVAILABLE:
        raise HTTPException(status_code=503, detail="Daily brief service not available")
    
    user = await get_user_from_token(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Get streak
    streak_obj, _ = await sync_to_async(UserStreak.objects.get_or_create)(user=user)
    
    # Get progress
    progress, _ = await sync_to_async(UserProgress.objects.get_or_create)(user=user)
    
    # Get achievements
    achievements = await sync_to_async(list)(
        UserAchievement.objects.filter(user=user).values('achievement_type', 'unlocked_at')
    )
    
    return ProgressResponse(
        streak=streak_obj.current_streak,
        longest_streak=streak_obj.longest_streak,
        weekly_briefs_completed=progress.weekly_briefs_completed,
        weekly_goal=progress.weekly_goal,
        weekly_lessons_completed=progress.weekly_lessons_completed,
        monthly_lessons_completed=progress.monthly_lessons_completed,
        monthly_goal=progress.monthly_goal,
        concepts_learned=progress.concepts_learned,
        current_level=progress.current_level,
        confidence_score=progress.confidence_score,
        achievements=[dict(a) for a in achievements],
    )

