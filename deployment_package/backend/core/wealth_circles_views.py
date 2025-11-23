"""
REST API Views for Wealth Circles
"""
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
import json
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

User = get_user_model()


@method_decorator(csrf_exempt, name='dispatch')
class WealthCirclePostsView(View):
    """
    GET /api/wealth-circles/<circle_id>/posts/ - Get posts
    POST /api/wealth-circles/<circle_id>/posts/ - Create post
    """
    
    def get(self, request, circle_id):
        try:
            logger.info(f'📝 [Posts API] Fetching posts for circle: {circle_id}')
            
            # For now, return mock data that matches the frontend format
            # In production, this would query the database for actual posts
            mock_posts = [
                {
                    'id': '1',
                    'user': {
                        'id': 'user1',
                        'name': 'Marcus Johnson',
                        'avatar': 'https://via.placeholder.com/40/007AFF/ffffff?text=MJ'
                    },
                    'content': 'Just closed a deal on a multi-family property in Atlanta! Cash flow is looking strong. Building generational wealth one property at a time. #RealEstate #WealthBuilding #BIPOCInvesting',
                    'timestamp': '2h ago',
                    'created_at': (datetime.now() - timedelta(hours=2)).isoformat(),
                    'likes': 45,
                    'likes_count': 45,
                    'comments': 12,
                    'comments_count': 12,
                    'isLiked': False,
                    'is_liked': False,
                    'media': {
                        'uri': 'https://via.placeholder.com/300x200/34C759/ffffff?text=Property+Deal',
                        'url': 'https://via.placeholder.com/300x200/34C759/ffffff?text=Property+Deal',
                        'type': 'image'
                    }
                },
                {
                    'id': '2',
                    'user': {
                        'id': 'user2',
                        'name': 'Aisha Williams',
                        'avatar': 'https://via.placeholder.com/40/FF9500/ffffff?text=AW'
                    },
                    'content': 'Quick tip: Use tax-loss harvesting before year-end to offset gains. Saved me $8K last year! What\'s your go-to tax strategy? #TaxOptimization #FinancialLiteracy',
                    'timestamp': '5h ago',
                    'created_at': (datetime.now() - timedelta(hours=5)).isoformat(),
                    'likes': 23,
                    'likes_count': 23,
                    'comments': 8,
                    'comments_count': 8,
                    'isLiked': True,
                    'is_liked': True,
                    'media': None
                }
            ]
            
            logger.info(f'✅ [Posts API] Returning {len(mock_posts)} posts for circle {circle_id}')
            return JsonResponse(mock_posts, safe=False)
            
        except Exception as e:
            logger.error(f'❌ [Posts API] Error: {e}', exc_info=True)
            return JsonResponse({
                'error': str(e)
            }, status=500)
    
    def post(self, request, circle_id):
        """Create a new post in a wealth circle"""
        try:
            data = json.loads(request.body)
            logger.info(f'📝 [Posts API] Creating post for circle: {circle_id}')
            
            # For now, just return success
            # In production, this would save to database
            return JsonResponse({
                'id': str(datetime.now().timestamp()),
                'success': True,
                'message': 'Post created successfully'
            }, status=201)
            
        except Exception as e:
            logger.error(f'❌ [Posts API] Error creating post: {e}', exc_info=True)
            return JsonResponse({
                'error': str(e)
            }, status=500)

