# Social Trading API Views for RichesReach AI

## 🎮 **SOCIAL TRADING API ENDPOINTS**

### **Core API Endpoints:**
- **POST /api/social/launch-meme** - Launch meme coin
- **GET /api/social/feed** - Get social trading feed
- **POST /api/social/voice-command** - Process voice commands
- **POST /api/social/join-raid** - Join trading raid
- **POST /api/social/create-post** - Create social post
- **GET /api/social/meme-templates** - Get meme templates
- **POST /api/social/stake-yield** - Stake meme for DeFi yield

---

## 🛠️ **API IMPLEMENTATION**

### **Social Trading Views**
```python
# backend/backend/core/social_trading_views.py
"""
Social Trading API Views - MemeQuest Integration
================================================

This module provides REST API endpoints for social trading features:
1. Meme coin launches via Pump.fun
2. Social feed management
3. Voice command processing
4. Raid coordination
5. DeFi integration
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.views import View
import json
import asyncio
import logging
from decimal import Decimal
from typing import Dict, Any, List
from dataclasses import asdict

from .social_trading_service import SocialTradingService, MemeTemplate, SocialPost, Raid
from .models import User, UserProfile

logger = logging.getLogger(__name__)

# =============================================================================
# Meme Coin Launch API
# =============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def launch_meme(request):
    """
    Launch a meme coin via Pump.fun integration.
    
    POST /api/social/launch-meme
    {
        "user_id": "user123",
        "meme_data": {
            "name": "RichesFrog",
            "template": "wealth-frog",
            "description": "Hop to financial freedom!",
            "cultural_theme": "BIPOC Wealth Building",
            "ai_generated": false
        }
    }
    """
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        meme_data = data.get('meme_data')
        
        if not user_id or not meme_data:
            return JsonResponse({
                'success': False,
                'error': 'user_id and meme_data are required'
            }, status=400)
        
        # Validate meme data
        required_fields = ['name', 'template']
        for field in required_fields:
            if not meme_data.get(field):
                return JsonResponse({
                    'success': False,
                    'error': f'{field} is required'
                }, status=400)
        
        # Launch meme coin
        service = SocialTradingService()
        meme_coin = asyncio.run(service.launch_meme_coin(user_id, meme_data))
        
        return JsonResponse({
            'success': True,
            'meme_coin': {
                'id': meme_coin.id,
                'name': meme_coin.name,
                'symbol': meme_coin.symbol,
                'template': meme_coin.template,
                'status': meme_coin.status.value,
                'contract_address': meme_coin.contract_address,
                'initial_price': float(meme_coin.initial_price),
                'current_price': float(meme_coin.current_price),
                'market_cap': float(meme_coin.market_cap),
                'holders': meme_coin.holders,
                'volume_24h': float(meme_coin.volume_24h),
                'bonding_curve_active': meme_coin.bonding_curve_active,
                'graduation_threshold': float(meme_coin.graduation_threshold),
                'created_at': meme_coin.created_at.isoformat(),
                'performance_metrics': meme_coin.performance_metrics
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f"Error launching meme coin: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# =============================================================================
# Social Feed API
# =============================================================================

@csrf_exempt
@require_http_methods(["GET"])
@cache_page(60)  # Cache for 1 minute
def get_social_feed(request):
    """
    Get social trading feed.
    
    GET /api/social/feed?user_id=user123&limit=20&type=all
    """
    try:
        user_id = request.GET.get('user_id')
        limit = int(request.GET.get('limit', 20))
        post_type = request.GET.get('type', 'all')
        
        if not user_id:
            return JsonResponse({
                'success': False,
                'error': 'user_id is required'
            }, status=400)
        
        # Get social feed
        service = SocialTradingService()
        posts = asyncio.run(service.get_social_feed(user_id, limit))
        
        # Filter by post type if specified
        if post_type != 'all':
            posts = [post for post in posts if post.post_type.value == post_type]
        
        return JsonResponse({
            'success': True,
            'posts': [asdict(post) for post in posts],
            'total_count': len(posts),
            'limit': limit
        })
        
    except Exception as e:
        logger.error(f"Error fetching social feed: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_social_post(request):
    """
    Create a social trading post.
    
    POST /api/social/create-post
    {
        "user_id": "user123",
        "post_data": {
            "type": "meme_launch",
            "content": "🚀 Launched $RICHESFROG! Hop to the moon!",
            "video_url": "https://example.com/video.mp4",
            "meme_coin_id": "meme123",
            "raid_id": "raid456",
            "xp_reward": 100,
            "is_spotlight": true
        }
    }
    """
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        post_data = data.get('post_data')
        
        if not user_id or not post_data:
            return JsonResponse({
                'success': False,
                'error': 'user_id and post_data are required'
            }, status=400)
        
        # Create social post
        service = SocialTradingService()
        post = asyncio.run(service.create_social_post(user_id, post_data))
        
        return JsonResponse({
            'success': True,
            'post': asdict(post)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f"Error creating social post: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# =============================================================================
# Voice Command API
# =============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def process_voice_command(request):
    """
    Process voice command for meme creation.
    
    POST /api/social/voice-command
    {
        "user_id": "user123",
        "command": "Launch RichesFrog meme"
    }
    """
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        command = data.get('command')
        
        if not user_id or not command:
            return JsonResponse({
                'success': False,
                'error': 'user_id and command are required'
            }, status=400)
        
        # Process voice command
        service = SocialTradingService()
        result = asyncio.run(service.process_voice_command(user_id, command))
        
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f"Error processing voice command: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# =============================================================================
# Raid Management API
# =============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def create_raid(request):
    """
    Create a trading raid.
    
    POST /api/social/create-raid
    {
        "user_id": "user123",
        "raid_data": {
            "name": "RichesFrog Pump",
            "meme_coin_id": "meme123",
            "target_amount": 1000,
            "xp_reward": 50,
            "success_bonus": 100
        }
    }
    """
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        raid_data = data.get('raid_data')
        
        if not user_id or not raid_data:
            return JsonResponse({
                'success': False,
                'error': 'user_id and raid_data are required'
            }, status=400)
        
        # Create raid
        service = SocialTradingService()
        raid = asyncio.run(service.create_raid(user_id, raid_data))
        
        return JsonResponse({
            'success': True,
            'raid': asdict(raid)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f"Error creating raid: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def join_raid(request):
    """
    Join a trading raid.
    
    POST /api/social/join-raid
    {
        "user_id": "user123",
        "raid_id": "raid456",
        "amount": 0.1
    }
    """
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        raid_id = data.get('raid_id')
        amount = data.get('amount')
        
        if not user_id or not raid_id or not amount:
            return JsonResponse({
                'success': False,
                'error': 'user_id, raid_id, and amount are required'
            }, status=400)
        
        # Join raid
        service = SocialTradingService()
        result = asyncio.run(service.join_raid(user_id, raid_id, Decimal(str(amount))))
        
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f"Error joining raid: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# =============================================================================
# Meme Templates API
# =============================================================================

@csrf_exempt
@require_http_methods(["GET"])
@cache_page(300)  # Cache for 5 minutes
def get_meme_templates(request):
    """
    Get available meme templates.
    
    GET /api/social/meme-templates
    """
    try:
        service = SocialTradingService()
        templates = service.meme_templates
        
        return JsonResponse({
            'success': True,
            'templates': [asdict(template) for template in templates]
        })
        
    except Exception as e:
        logger.error(f"Error fetching meme templates: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# =============================================================================
# DeFi Integration API
# =============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def stake_meme_yield(request):
    """
    Stake meme coin for DeFi yield.
    
    POST /api/social/stake-yield
    {
        "user_id": "user123",
        "meme_coin_id": "meme123",
        "amount": 1000
    }
    """
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        meme_coin_id = data.get('meme_coin_id')
        amount = data.get('amount')
        
        if not user_id or not meme_coin_id or not amount:
            return JsonResponse({
                'success': False,
                'error': 'user_id, meme_coin_id, and amount are required'
            }, status=400)
        
        # Stake for yield
        service = SocialTradingService()
        result = asyncio.run(service.stake_meme_for_yield(user_id, meme_coin_id, Decimal(str(amount))))
        
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f"Error staking meme for yield: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# =============================================================================
# Analytics API
# =============================================================================

@csrf_exempt
@require_http_methods(["GET"])
def get_meme_analytics(request):
    """
    Get meme coin analytics.
    
    GET /api/social/meme-analytics?meme_coin_id=meme123
    """
    try:
        meme_coin_id = request.GET.get('meme_coin_id')
        
        if not meme_coin_id:
            return JsonResponse({
                'success': False,
                'error': 'meme_coin_id is required'
            }, status=400)
        
        # Get meme analytics
        service = SocialTradingService()
        meme_coin = asyncio.run(service._get_meme_coin(meme_coin_id))
        
        if not meme_coin:
            return JsonResponse({
                'success': False,
                'error': 'Meme coin not found'
            }, status=404)
        
        return JsonResponse({
            'success': True,
            'analytics': {
                'id': meme_coin.id,
                'name': meme_coin.name,
                'symbol': meme_coin.symbol,
                'status': meme_coin.status.value,
                'current_price': float(meme_coin.current_price),
                'market_cap': float(meme_coin.market_cap),
                'holders': meme_coin.holders,
                'volume_24h': float(meme_coin.volume_24h),
                'price_change_24h': float(meme_coin.current_price - meme_coin.initial_price),
                'price_change_percent': float((meme_coin.current_price - meme_coin.initial_price) / meme_coin.initial_price * 100),
                'bonding_curve_active': meme_coin.bonding_curve_active,
                'graduation_progress': float(meme_coin.market_cap / meme_coin.graduation_threshold * 100),
                'performance_metrics': meme_coin.performance_metrics
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching meme analytics: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# =============================================================================
# Leaderboard API
# =============================================================================

@csrf_exempt
@require_http_methods(["GET"])
@cache_page(60)  # Cache for 1 minute
def get_leaderboard(request):
    """
    Get social trading leaderboard.
    
    GET /api/social/leaderboard?type=raiders&limit=10
    """
    try:
        leaderboard_type = request.GET.get('type', 'raiders')
        limit = int(request.GET.get('limit', 10))
        
        # Get leaderboard data
        service = SocialTradingService()
        
        if leaderboard_type == 'raiders':
            # Top raiders by XP
            leaderboard = asyncio.run(service._get_top_raiders(limit))
        elif leaderboard_type == 'creators':
            # Top meme creators
            leaderboard = asyncio.run(service._get_top_creators(limit))
        elif leaderboard_type == 'yield_farmers':
            # Top yield farmers
            leaderboard = asyncio.run(service._get_top_yield_farmers(limit))
        else:
            return JsonResponse({
                'success': False,
                'error': 'Invalid leaderboard type'
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'leaderboard': leaderboard,
            'type': leaderboard_type,
            'limit': limit
        })
        
    except Exception as e:
        logger.error(f"Error fetching leaderboard: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# =============================================================================
# Health Check API
# =============================================================================

@csrf_exempt
@require_http_methods(["GET"])
def social_trading_health(request):
    """
    Health check for social trading service.
    
    GET /api/social/health
    """
    try:
        service = SocialTradingService()
        
        # Check service health
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'services': {
                'pump_fun_api': await service._check_pump_fun_health(),
                'social_media': await service._check_social_media_health(),
                'ai_risk_model': await service._check_ai_model_health(),
                'defi_protocols': await service._check_defi_health(),
            }
        }
        
        return JsonResponse(health_status)
        
    except Exception as e:
        logger.error(f"Error checking social trading health: {str(e)}")
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }, status=500)
```

---

## 🎯 **URL CONFIGURATION**

### **URL Patterns**
```python
# backend/backend/richesreach/urls.py
from django.urls import path
from .core.social_trading_views import (
    launch_meme,
    get_social_feed,
    create_social_post,
    process_voice_command,
    create_raid,
    join_raid,
    get_meme_templates,
    stake_meme_yield,
    get_meme_analytics,
    get_leaderboard,
    social_trading_health,
)

urlpatterns = [
    # Social Trading API
    path('api/social/launch-meme', launch_meme, name='launch_meme'),
    path('api/social/feed', get_social_feed, name='get_social_feed'),
    path('api/social/create-post', create_social_post, name='create_social_post'),
    path('api/social/voice-command', process_voice_command, name='process_voice_command'),
    path('api/social/create-raid', create_raid, name='create_raid'),
    path('api/social/join-raid', join_raid, name='join_raid'),
    path('api/social/meme-templates', get_meme_templates, name='get_meme_templates'),
    path('api/social/stake-yield', stake_meme_yield, name='stake_meme_yield'),
    path('api/social/meme-analytics', get_meme_analytics, name='get_meme_analytics'),
    path('api/social/leaderboard', get_leaderboard, name='get_leaderboard'),
    path('api/social/health', social_trading_health, name='social_trading_health'),
]
```

---

## 🚀 **INTEGRATION WITH EXISTING SYSTEM**

### **Database Models**
```python
# backend/backend/core/models.py
from django.db import models
from django.contrib.auth.models import User

class MemeCoin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=20)
    template = models.CharField(max_length=50)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    network = models.CharField(max_length=20, default='solana')
    contract_address = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=20, default='creating')
    initial_price = models.DecimalField(max_digits=20, decimal_places=10, default=0.0001)
    current_price = models.DecimalField(max_digits=20, decimal_places=10, default=0.0001)
    market_cap = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_supply = models.DecimalField(max_digits=20, decimal_places=0, default=1000000000)
    holders = models.IntegerField(default=0)
    volume_24h = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    bonding_curve_active = models.BooleanField(default=True)
    graduation_threshold = models.DecimalField(max_digits=20, decimal_places=2, default=69000)
    created_at = models.DateTimeField(auto_now_add=True)
    graduated_at = models.DateTimeField(null=True, blank=True)
    performance_metrics = models.JSONField(default=dict)

class SocialPost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post_type = models.CharField(max_length=20)
    content = models.TextField()
    video_url = models.URLField(null=True, blank=True)
    meme_coin = models.ForeignKey(MemeCoin, on_delete=models.CASCADE, null=True, blank=True)
    raid = models.ForeignKey('Raid', on_delete=models.CASCADE, null=True, blank=True)
    likes = models.IntegerField(default=0)
    shares = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)
    views = models.IntegerField(default=0)
    xp_reward = models.IntegerField(default=0)
    is_spotlight = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Raid(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    meme_coin = models.ForeignKey(MemeCoin, on_delete=models.CASCADE)
    leader = models.ForeignKey(User, on_delete=models.CASCADE)
    participants = models.ManyToManyField(User, related_name='raid_participations')
    target_amount = models.DecimalField(max_digits=20, decimal_places=2)
    current_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    status = models.CharField(max_length=20, default='planning')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    xp_reward = models.IntegerField(default=50)
    success_bonus = models.IntegerField(default=100)
```

---

## 📈 **TESTING & VALIDATION**

### **API Testing**
```python
# tests/test_social_trading_api.py
import pytest
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User

class SocialTradingAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_launch_meme(self):
        """Test meme coin launch API."""
        data = {
            'user_id': str(self.user.id),
            'meme_data': {
                'name': 'TestFrog',
                'template': 'wealth-frog',
                'description': 'Test meme for wealth building',
                'cultural_theme': 'BIPOC Wealth Building'
            }
        }
        
        response = self.client.post(
            '/api/social/launch-meme',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        self.assertEqual(result['meme_coin']['name'], 'TestFrog')
    
    def test_get_social_feed(self):
        """Test social feed API."""
        response = self.client.get(
            f'/api/social/feed?user_id={self.user.id}&limit=10'
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        self.assertIn('posts', result)
    
    def test_process_voice_command(self):
        """Test voice command processing."""
        data = {
            'user_id': str(self.user.id),
            'command': 'Launch TestFrog meme'
        }
        
        response = self.client.post(
            '/api/social/voice-command',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
```

---

## 🎯 **DEPLOYMENT CHECKLIST**

### **Environment Variables**
```bash
# Add to .env file
PUMP_FUN_API_URL=https://api.pump.fun
PUMP_FUN_API_KEY=your_pump_fun_api_key
TWITTER_API_KEY=your_twitter_api_key
TIKTOK_API_KEY=your_tiktok_api_key
ML_MODEL_PATH=/path/to/ml/model
AAVE_LENDING_POOL_ADDRESS=0x...
COMPOUND_COMPTROLLER_ADDRESS=0x...
```

### **Dependencies**
```bash
# Add to requirements.txt
web3>=6.0.0
eth-account>=0.8.0
requests>=2.28.0
asyncio
```

### **Database Migration**
```bash
python manage.py makemigrations core
python manage.py migrate
```

---

## 🚀 **NEXT STEPS**

1. **Integrate MemeQuestScreen** into TutorScreen
2. **Add API endpoints** to URL configuration
3. **Create database models** and run migrations
4. **Test API endpoints** with Postman/curl
5. **Integrate Pump.fun SDK** for real meme launches
6. **Add voice command processing** to existing voice AI
7. **Implement social feed** with real-time updates
8. **Add DeFi integration** for yield farming

This MemeQuest integration will make RichesReach AI the **"TikTok of hybrid DeFi"** - combining viral meme trading with institutional-grade AI and voice-first accessibility! 🚀
