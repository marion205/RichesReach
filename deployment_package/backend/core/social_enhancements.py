"""
Enhanced Social Features
- Portfolio sharing and leaderboards
- Enhanced activity feed
- User following improvements
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg, Max
from django.core.cache import cache
from .models import User, Portfolio, Stock, Follow, Post, StockDiscussion
from decimal import Decimal

logger = logging.getLogger(__name__)


class SocialEnhancementsService:
    """Service for enhanced social features"""
    
    CACHE_TTL = 1800  # 30 minutes
    
    def get_portfolio_leaderboard(
        self,
        timeframe: str = 'all_time',  # 'daily', 'weekly', 'monthly', 'all_time'
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get portfolio performance leaderboard
        
        Returns list of users sorted by portfolio performance:
        [
            {
                'user_id': int,
                'user_name': str,
                'user_email': str,
                'total_return_pct': float,
                'total_value': float,
                'rank': int,
                'holdings_count': int,
                'best_performer': str,  # symbol
                'worst_performer': str,  # symbol
            },
            ...
        ]
        """
        cache_key = f"portfolio_leaderboard:{timeframe}:{limit}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        try:
            # Calculate date range
            now = timezone.now()
            if timeframe == 'daily':
                start_date = now - timedelta(days=1)
            elif timeframe == 'weekly':
                start_date = now - timedelta(days=7)
            elif timeframe == 'monthly':
                start_date = now - timedelta(days=30)
            else:
                start_date = None
            
            # Get all portfolios with recent activity
            portfolios = Portfolio.objects.filter(shares__gt=0)
            
            if start_date:
                portfolios = portfolios.filter(updated_at__gte=start_date)
            
            # Group by user and calculate metrics
            user_portfolios = {}
            for portfolio in portfolios.select_related('user', 'stock'):
                user_id = portfolio.user_id
                if user_id not in user_portfolios:
                    user_portfolios[user_id] = {
                        'user': portfolio.user,
                        'holdings': [],
                        'total_value': Decimal('0.00'),
                        'total_cost': Decimal('0.00'),
                    }
                
                current_value = portfolio.current_price * Decimal(portfolio.shares) if portfolio.current_price else Decimal('0.00')
                cost_basis = portfolio.average_price * Decimal(portfolio.shares) if portfolio.average_price else Decimal('0.00')
                
                user_portfolios[user_id]['holdings'].append({
                    'symbol': portfolio.stock.symbol,
                    'value': current_value,
                    'cost': cost_basis,
                    'return_pct': ((current_value - cost_basis) / cost_basis * 100) if cost_basis > 0 else Decimal('0.00'),
                })
                user_portfolios[user_id]['total_value'] += current_value
                user_portfolios[user_id]['total_cost'] += cost_basis
            
            # Calculate leaderboard
            leaderboard = []
            for user_id, data in user_portfolios.items():
                if data['total_cost'] == 0:
                    continue
                
                total_return_pct = float(
                    ((data['total_value'] - data['total_cost']) / data['total_cost']) * 100
                )
                
                # Find best and worst performers
                holdings = data['holdings']
                if holdings:
                    best = max(holdings, key=lambda x: float(x['return_pct']))
                    worst = min(holdings, key=lambda x: float(x['return_pct']))
                    best_performer = best['symbol']
                    worst_performer = worst['symbol']
                else:
                    best_performer = None
                    worst_performer = None
                
                leaderboard.append({
                    'user_id': user_id,
                    'user_name': data['user'].name,
                    'user_email': data['user'].email,
                    'total_return_pct': round(total_return_pct, 2),
                    'total_value': float(data['total_value']),
                    'holdings_count': len(holdings),
                    'best_performer': best_performer,
                    'worst_performer': worst_performer,
                })
            
            # Sort by return percentage
            leaderboard.sort(key=lambda x: x['total_return_pct'], reverse=True)
            
            # Add ranks
            for i, entry in enumerate(leaderboard, 1):
                entry['rank'] = i
            
            # Limit results
            leaderboard = leaderboard[:limit]
            
            cache.set(cache_key, leaderboard, self.CACHE_TTL)
            return leaderboard
            
        except Exception as e:
            logger.error(f"Error getting portfolio leaderboard: {e}", exc_info=True)
            return []
    
    def get_user_activity_feed(
        self,
        user_id: int,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get enhanced activity feed for a user (following + own activity)
        
        Returns:
        [
            {
                'type': 'portfolio_update' | 'discussion' | 'post' | 'follow',
                'user_id': int,
                'user_name': str,
                'timestamp': datetime,
                'content': {...},
            },
            ...
        ]
        """
        try:
            user = User.objects.get(id=user_id)
            
            # Get users being followed
            following_ids = Follow.objects.filter(follower=user).values_list('following_id', flat=True)
            following_ids = list(following_ids) + [user_id]  # Include own activity
            
            activities = []
            
            # Portfolio updates (simplified - would need portfolio history tracking)
            # For now, we'll use recent portfolio updates
            recent_portfolios = Portfolio.objects.filter(
                user_id__in=following_ids
            ).select_related('user', 'stock').order_by('-updated_at')[:20]
            
            for portfolio in recent_portfolios:
                activities.append({
                    'type': 'portfolio_update',
                    'user_id': portfolio.user_id,
                    'user_name': portfolio.user.name,
                    'timestamp': portfolio.updated_at,
                    'content': {
                        'symbol': portfolio.stock.symbol,
                        'shares': portfolio.shares,
                        'action': 'updated',
                    }
                })
            
            # Recent discussions
            recent_discussions = StockDiscussion.objects.filter(
                user_id__in=following_ids
            ).select_related('user', 'stock').order_by('-created_at')[:20]
            
            for discussion in recent_discussions:
                activities.append({
                    'type': 'discussion',
                    'user_id': discussion.user_id,
                    'user_name': discussion.user.name,
                    'timestamp': discussion.created_at,
                    'content': {
                        'title': discussion.title,
                        'symbol': discussion.stock.symbol if discussion.stock else None,
                        'upvotes': discussion.upvotes,
                        'comments': discussion.comment_count,
                    }
                })
            
            # Recent posts
            recent_posts = Post.objects.filter(
                user_id__in=following_ids
            ).select_related('user').order_by('-created_at')[:20]
            
            for post in recent_posts:
                activities.append({
                    'type': 'post',
                    'user_id': post.user_id,
                    'user_name': post.user.name,
                    'timestamp': post.created_at,
                    'content': {
                        'text': post.content[:200],  # Truncate
                        'likes': post.likes_count,
                        'comments': post.comments_count,
                    }
                })
            
            # Sort by timestamp
            activities.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return activities[:limit]
            
        except User.DoesNotExist:
            return []
        except Exception as e:
            logger.error(f"Error getting activity feed for user {user_id}: {e}", exc_info=True)
            return []
    
    def get_portfolio_sharing_info(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Get portfolio sharing information for a user
        
        Returns:
        {
            'is_public': bool,
            'share_token': str,  # For private sharing
            'total_followers': int,
            'portfolio_summary': {
                'total_value': float,
                'total_return_pct': float,
                'holdings_count': int,
            }
        }
        """
        try:
            user = User.objects.get(id=user_id)
            
            # Get portfolio summary
            portfolios = Portfolio.objects.filter(user=user, shares__gt=0).select_related('stock')
            
            total_value = Decimal('0.00')
            total_cost = Decimal('0.00')
            holdings_count = portfolios.count()
            
            for portfolio in portfolios:
                current_value = portfolio.current_price * Decimal(portfolio.shares) if portfolio.current_price else Decimal('0.00')
                cost_basis = portfolio.average_price * Decimal(portfolio.shares) if portfolio.average_price else Decimal('0.00')
                total_value += current_value
                total_cost += cost_basis
            
            total_return_pct = float(
                ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0.00
            )
            
            # Get follower count
            total_followers = Follow.objects.filter(following=user).count()
            
            # Generate share token (simplified - would use proper token generation)
            import hashlib
            share_token = hashlib.md5(f"{user_id}:{user.email}".encode()).hexdigest()[:16]
            
            return {
                'is_public': False,  # Default to private
                'share_token': share_token,
                'total_followers': total_followers,
                'portfolio_summary': {
                    'total_value': float(total_value),
                    'total_return_pct': round(total_return_pct, 2),
                    'holdings_count': holdings_count,
                }
            }
            
        except User.DoesNotExist:
            return {
                'is_public': False,
                'share_token': '',
                'total_followers': 0,
                'portfolio_summary': {
                    'total_value': 0.0,
                    'total_return_pct': 0.0,
                    'holdings_count': 0,
                }
            }
        except Exception as e:
            logger.error(f"Error getting portfolio sharing info for user {user_id}: {e}")
            return {
                'is_public': False,
                'share_token': '',
                'total_followers': 0,
                'portfolio_summary': {
                    'total_value': 0.0,
                    'total_return_pct': 0.0,
                    'holdings_count': 0,
                }
            }
    
    def get_trending_discussions(
        self,
        limit: int = 20,
        timeframe: str = '24h'  # '24h', '7d', '30d'
    ) -> List[Dict[str, Any]]:
        """
        Get trending stock discussions based on engagement
        
        Returns:
        [
            {
                'id': int,
                'title': str,
                'symbol': str,
                'user_name': str,
                'score': int,  # upvotes - downvotes
                'comments_count': int,
                'created_at': datetime,
                'trending_reason': str,
            },
            ...
        ]
        """
        try:
            # Calculate date range
            now = timezone.now()
            if timeframe == '24h':
                start_date = now - timedelta(hours=24)
            elif timeframe == '7d':
                start_date = now - timedelta(days=7)
            else:
                start_date = now - timedelta(days=30)
            
            discussions = StockDiscussion.objects.filter(
                created_at__gte=start_date
            ).select_related('user', 'stock').annotate(
                comment_count=Count('comments')
            ).order_by('-upvotes', '-comment_count', '-created_at')[:limit]
            
            trending = []
            for discussion in discussions:
                score = discussion.upvotes - discussion.downvotes
                
                # Determine trending reason
                if discussion.comment_count > 10:
                    reason = 'High engagement'
                elif score > 20:
                    reason = 'Highly upvoted'
                elif discussion.created_at > now - timedelta(hours=2):
                    reason = 'Recently posted'
                else:
                    reason = 'Trending'
                
                trending.append({
                    'id': discussion.id,
                    'title': discussion.title,
                    'symbol': discussion.stock.symbol if discussion.stock else None,
                    'user_name': discussion.user.name,
                    'score': score,
                    'comments_count': discussion.comment_count,
                    'created_at': discussion.created_at,
                    'trending_reason': reason,
                })
            
            return trending
            
        except Exception as e:
            logger.error(f"Error getting trending discussions: {e}", exc_info=True)
            return []

