# WebSocket Service for Real-Time Social Feed

## 🔌 **REAL-TIME WEBSOCKET SERVICE**

### **Core Features:**
- **Real-Time Updates**: Live social feed updates
- **Engagement Tracking**: Likes, shares, comments
- **Meme Launches**: Live meme launch notifications
- **Raid Coordination**: Real-time raid updates
- **Yield Farming**: Live yield farming updates
- **BIPOC Spotlight**: Community creator highlights

---

## 🛠️ **WEBSOCKET SERVICE IMPLEMENTATION**

### **WebSocket Consumer**
```python
# backend/backend/core/websocket_service.py
"""
Real-Time WebSocket Service for Social Feed
==========================================

This service provides real-time updates for:
1. New social posts
2. Engagement updates (likes, shares, comments)
3. Meme launches and updates
4. Raid coordination
5. Yield farming updates
6. BIPOC spotlight features
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.core.cache import cache
from datetime import datetime, timezone
import uuid

logger = logging.getLogger(__name__)

class SocialFeedConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time social feed updates.
    
    Handles:
    - New post notifications
    - Engagement updates
    - Meme launch events
    - Raid coordination
    - Yield farming updates
    - BIPOC spotlight features
    """
    
    async def connect(self):
        """Connect to WebSocket and join social feed group."""
        self.room_name = 'social_feed'
        self.room_group_name = f'feed_{self.room_name}'
        self.user_id = None
        self.subscribed_feeds = set()
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to social feed',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }))
        
        logger.info(f'WebSocket connected: {self.channel_name}')
    
    async def disconnect(self, close_code):
        """Disconnect from WebSocket and leave all groups."""
        # Leave main room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Leave all subscribed feed groups
        for feed_type in self.subscribed_feeds:
            await self.channel_layer.group_discard(
                f'feed_{feed_type}',
                self.channel_name
            )
        
        logger.info(f'WebSocket disconnected: {self.channel_name}')
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.handle_ping(data)
            elif message_type == 'subscribe':
                await self.handle_subscription(data)
            elif message_type == 'unsubscribe':
                await self.handle_unsubscription(data)
            elif message_type == 'interaction':
                await self.handle_interaction(data)
            elif message_type == 'authenticate':
                await self.handle_authentication(data)
            elif message_type == 'get_feed':
                await self.handle_get_feed(data)
            else:
                logger.warning(f'Unknown message type: {message_type}')
                
        except json.JSONDecodeError:
            logger.error('Invalid JSON received')
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f'Error processing message: {str(e)}')
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error'
            }))
    
    async def handle_ping(self, data):
        """Handle ping messages for connection health check."""
        await self.send(text_data=json.dumps({
            'type': 'pong',
            'timestamp': data.get('timestamp'),
            'server_time': datetime.now(timezone.utc).isoformat()
        }))

    async def handle_subscription(self, data):
        """Handle user subscription to specific feeds."""
        feed_type = data.get('feed_type', 'all')
        user_id = data.get('user_id')
        
        if user_id:
            self.user_id = user_id
        
        # Add user to specific feed group
        if feed_type != 'all':
            self.subscribed_feeds.add(feed_type)
            await self.channel_layer.group_add(
                f'feed_{feed_type}',
                self.channel_name
            )
            
            await self.send(text_data=json.dumps({
                'type': 'subscription_confirmed',
                'feed_type': feed_type,
                'message': f'Subscribed to {feed_type} feed'
            }))

    async def handle_unsubscription(self, data):
        """Handle user unsubscription from specific feeds."""
        feed_type = data.get('feed_type', 'all')
        
        if feed_type in self.subscribed_feeds:
            self.subscribed_feeds.remove(feed_type)
            await self.channel_layer.group_discard(
                f'feed_{feed_type}',
                self.channel_name
            )
            
            await self.send(text_data=json.dumps({
                'type': 'unsubscription_confirmed',
                'feed_type': feed_type,
                'message': f'Unsubscribed from {feed_type} feed'
            }))

    async def handle_interaction(self, data):
        """Handle social interactions (like, share, comment)."""
        post_id = data.get('post_id')
        action = data.get('action')
        user_id = data.get('user_id')
        
        if not all([post_id, action, user_id]):
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Missing required fields for interaction'
            }))
            return
        
        # Update engagement in database
        await self.update_engagement(post_id, action, user_id)
        
        # Broadcast interaction to all connected clients
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'engagement_update',
                'post_id': post_id,
                'action': action,
                'user_id': user_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        )

    async def handle_authentication(self, data):
        """Handle user authentication."""
        user_id = data.get('user_id')
        token = data.get('token')
        
        if user_id and token:
            # Validate token (implement your auth logic)
            is_valid = await self.validate_token(user_id, token)
            
            if is_valid:
                self.user_id = user_id
                await self.send(text_data=json.dumps({
                    'type': 'authentication_success',
                    'user_id': user_id,
                    'message': 'Authentication successful'
                }))
            else:
                await self.send(text_data=json.dumps({
                    'type': 'authentication_failed',
                    'message': 'Invalid token'
                }))

    async def handle_get_feed(self, data):
        """Handle feed data requests."""
        feed_type = data.get('feed_type', 'all')
        limit = data.get('limit', 20)
        offset = data.get('offset', 0)
        
        # Get feed data from database
        feed_data = await self.get_feed_data(feed_type, limit, offset)
        
        await self.send(text_data=json.dumps({
            'type': 'feed_data',
            'feed_type': feed_type,
            'data': feed_data,
            'limit': limit,
            'offset': offset
        }))

    # =========================================================================
    # WebSocket Event Handlers
    # =========================================================================

    async def new_post(self, event):
        """Send new post to WebSocket group."""
        await self.send(text_data=json.dumps({
            'type': 'new_post',
            'post': event['post'],
            'timestamp': event.get('timestamp', datetime.now(timezone.utc).isoformat())
        }))
    
    async def post_update(self, event):
        """Send post update to WebSocket group."""
        await self.send(text_data=json.dumps({
            'type': 'post_update',
            'post_id': event['post_id'],
            'updates': event['updates'],
            'timestamp': event.get('timestamp', datetime.now(timezone.utc).isoformat())
        }))

    async def engagement_update(self, event):
        """Send engagement update to WebSocket group."""
        await self.send(text_data=json.dumps({
            'type': 'engagement_update',
            'post_id': event['post_id'],
            'action': event['action'],
            'user_id': event['user_id'],
            'timestamp': event['timestamp']
        }))

    async def spotlight_update(self, event):
        """Send spotlight update to WebSocket group."""
        await self.send(text_data=json.dumps({
            'type': 'spotlight_update',
            'post_id': event['post_id'],
            'is_spotlight': event['is_spotlight'],
            'timestamp': event.get('timestamp', datetime.now(timezone.utc).isoformat())
        }))

    async def meme_launch(self, event):
        """Send meme launch update to WebSocket group."""
            await self.send(text_data=json.dumps({
            'type': 'meme_launch',
            'meme_data': event['meme_data'],
            'timestamp': event.get('timestamp', datetime.now(timezone.utc).isoformat())
        }))

    async def raid_update(self, event):
        """Send raid update to WebSocket group."""
            await self.send(text_data=json.dumps({
            'type': 'raid_update',
            'raid_data': event['raid_data'],
            'timestamp': event.get('timestamp', datetime.now(timezone.utc).isoformat())
        }))

    async def yield_update(self, event):
        """Send yield farming update to WebSocket group."""
                await self.send(text_data=json.dumps({
            'type': 'yield_update',
            'yield_data': event['yield_data'],
            'timestamp': event.get('timestamp', datetime.now(timezone.utc).isoformat())
        }))

    async def bipoc_spotlight(self, event):
        """Send BIPOC spotlight update to WebSocket group."""
                await self.send(text_data=json.dumps({
            'type': 'bipoc_spotlight',
            'creator_data': event['creator_data'],
            'timestamp': event.get('timestamp', datetime.now(timezone.utc).isoformat())
        }))

    # =========================================================================
    # Database Operations
    # =========================================================================

    @database_sync_to_async
    def update_engagement(self, post_id: str, action: str, user_id: str):
        """Update engagement in database."""
        try:
            # This would update your database
            # For now, just log the interaction
            logger.info(f'Engagement update: {action} on post {post_id} by user {user_id}')
            
            # Update cache for real-time stats
            cache_key = f'engagement_{post_id}_{action}'
            current_count = cache.get(cache_key, 0)
            cache.set(cache_key, current_count + 1, 300)  # 5 minutes
                
        except Exception as e:
            logger.error(f'Error updating engagement: {str(e)}')
    
    @database_sync_to_async
    def validate_token(self, user_id: str, token: str) -> bool:
        """Validate user token."""
        try:
            # Implement your token validation logic
            # For now, return True for demo
            return True
        except Exception as e:
            logger.error(f'Error validating token: {str(e)}')
            return False
    
    @database_sync_to_async
    def get_feed_data(self, feed_type: str, limit: int, offset: int) -> List[Dict[str, Any]]:
        """Get feed data from database."""
        try:
            # This would fetch from your database
            # For now, return mock data
            mock_posts = [
                {
                    'id': str(uuid.uuid4()),
                    'user': {
                        'id': 'user1',
                        'username': 'BIPOCTrader',
                        'avatar': 'https://example.com/avatar1.png',
                        'isVerified': True,
                        'isBIPOC': True,
                        'followers': 1250
                    },
                    'content': {
                        'type': 'meme_launch',
                        'text': 'Just launched $FROG! Hop to the moon! 🚀',
                        'memeData': {
                            'name': 'RichesFrog',
                            'symbol': 'FROG',
                            'price': 0.0001,
                            'change24h': 12.5,
                            'contractAddress': '0x123...'
                        }
                    },
                    'engagement': {
                        'likes': 45,
                        'shares': 12,
                        'comments': 8,
                        'views': 234
                    },
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'isLiked': False,
                    'isShared': False,
                    'isSpotlight': True,
                    'xpReward': 100
                },
                {
                    'id': str(uuid.uuid4()),
                    'user': {
                        'id': 'user2',
                        'username': 'CommunityHero',
                        'avatar': 'https://example.com/avatar2.png',
                        'isVerified': True,
                        'isBIPOC': True,
                        'followers': 890
                    },
                    'content': {
                        'type': 'raid_join',
                        'text': 'Joining the $BEAR raid! Let\'s pump together! ⚔️',
                        'raidData': {
                            'name': 'Bear Pump',
                            'targetAmount': 1000,
                            'currentAmount': 750,
                            'participants': 25
                        }
                    },
                    'engagement': {
                        'likes': 32,
                        'shares': 8,
                        'comments': 15,
                        'views': 156
                    },
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'isLiked': False,
                    'isShared': False,
                    'isSpotlight': True,
                    'xpReward': 75
                }
            ]
            
            return mock_posts[offset:offset + limit]
            
        except Exception as e:
            logger.error(f'Error getting feed data: {str(e)}')
            return []

# =============================================================================
# WebSocket Broadcasting Service
# =============================================================================

class SocialFeedBroadcaster:
    """
    Service for broadcasting social feed events to WebSocket groups.
    """
    
    def __init__(self, channel_layer):
        self.channel_layer = channel_layer
    
    async def broadcast_new_post(self, post_data: Dict[str, Any]):
        """Broadcast new post to all connected clients."""
        await self.channel_layer.group_send(
            'feed_social_feed',
            {
                'type': 'new_post',
                'post': post_data,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        )
    
    async def broadcast_engagement_update(self, post_id: str, action: str, user_id: str):
        """Broadcast engagement update to all connected clients."""
        await self.channel_layer.group_send(
            'feed_social_feed',
            {
                'type': 'engagement_update',
                'post_id': post_id,
                'action': action,
                'user_id': user_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        )
    
    async def broadcast_meme_launch(self, meme_data: Dict[str, Any]):
        """Broadcast meme launch to all connected clients."""
        await self.channel_layer.group_send(
            'feed_social_feed',
            {
                'type': 'meme_launch',
                'meme_data': meme_data,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        )
    
    async def broadcast_raid_update(self, raid_data: Dict[str, Any]):
        """Broadcast raid update to all connected clients."""
        await self.channel_layer.group_send(
            'feed_social_feed',
            {
                'type': 'raid_update',
                'raid_data': raid_data,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        )
    
    async def broadcast_yield_update(self, yield_data: Dict[str, Any]):
        """Broadcast yield farming update to all connected clients."""
        await self.channel_layer.group_send(
            'feed_social_feed',
            {
                'type': 'yield_update',
                'yield_data': yield_data,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        )
    
    async def broadcast_bipoc_spotlight(self, creator_data: Dict[str, Any]):
        """Broadcast BIPOC spotlight update to all connected clients."""
        await self.channel_layer.group_send(
            'feed_social_feed',
            {
                'type': 'bipoc_spotlight',
                'creator_data': creator_data,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        )
```

---

## 🎯 **WEBSOCKET URL CONFIGURATION**

### **URL Patterns**
```python
# backend/backend/richesreach/routing.py
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/social-feed/', consumers.SocialFeedConsumer.as_asgi()),
]
```

### **ASGI Configuration**
```python
# backend/backend/richesreach/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from .routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
```

---

## 🚀 **INTEGRATION WITH SOCIAL FEED**

### **Updated Social Feed Integration**
```typescript
// In SocialFeed.tsx - Enhanced WebSocket integration
const connectWebSocket = () => {
  try {
    const wsUrl = process.env.EXPO_PUBLIC_WS_URL || 'ws://localhost:8000/ws/social-feed/';
    webSocketRef.current = new WebSocket(wsUrl);

    webSocketRef.current.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      
      // Send authentication
      webSocketRef.current?.send(JSON.stringify({
        type: 'authenticate',
        user_id: address,
        token: 'your_auth_token'
      }));
      
      // Subscribe to all feeds
      webSocketRef.current?.send(JSON.stringify({
        type: 'subscribe',
        feed_type: 'all',
        user_id: address
      }));
    };

    webSocketRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    webSocketRef.current.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      // Reconnect after 3 seconds
      setTimeout(connectWebSocket, 3000);
    };

    webSocketRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };
  } catch (error) {
    console.error('Error connecting WebSocket:', error);
  }
};

const handleWebSocketMessage = (data: any) => {
  switch (data.type) {
    case 'new_post':
      setPosts(prev => [data.post, ...prev]);
      break;
    case 'post_update':
      setPosts(prev => prev.map(post => 
        post.id === data.post_id ? { ...post, ...data.updates } : post
      ));
      break;
    case 'engagement_update':
      setPosts(prev => prev.map(post => 
        post.id === data.post_id ? {
          ...post,
          engagement: { ...post.engagement, ...data.engagement }
        } : post
      ));
      break;
    case 'spotlight_update':
      setPosts(prev => prev.map(post => 
        post.id === data.post_id ? { ...post, isSpotlight: data.is_spotlight } : post
      ));
      break;
    case 'meme_launch':
      // Handle meme launch notification
      console.log('New meme launched:', data.meme_data);
      break;
    case 'raid_update':
      // Handle raid update notification
      console.log('Raid updated:', data.raid_data);
      break;
    case 'yield_update':
      // Handle yield farming update notification
      console.log('Yield farming updated:', data.yield_data);
      break;
    case 'bipoc_spotlight':
      // Handle BIPOC spotlight notification
      console.log('BIPOC creator spotlighted:', data.creator_data);
      break;
  }
};
```

---

## 📈 **REAL-TIME ANALYTICS**

### **Analytics Service**
```python
# backend/backend/core/social_analytics_service.py
class SocialAnalyticsService:
    """Service for tracking social feed analytics."""
    
    def __init__(self):
        self.engagement_stats = {}
        self.user_behavior = {}
    
    async def track_engagement(self, post_id: str, action: str, user_id: str):
        """Track engagement metrics."""
        key = f"{post_id}_{action}"
        self.engagement_stats[key] = self.engagement_stats.get(key, 0) + 1
        
        # Store in cache for real-time access
        cache.set(f'engagement_{key}', self.engagement_stats[key], 300)
    
    async def track_user_behavior(self, user_id: str, behavior: Dict[str, Any]):
        """Track user behavior patterns."""
        if user_id not in self.user_behavior:
            self.user_behavior[user_id] = []
        
        self.user_behavior[user_id].append({
            **behavior,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    def get_analytics(self) -> Dict[str, Any]:
        """Get analytics data."""
        return {
            'engagement_stats': self.engagement_stats,
            'user_behavior': self.user_behavior,
            'total_engagements': sum(self.engagement_stats.values())
        }
```

---

## 🎯 **NEXT STEPS**

1. **Set up WebSocket** routing and ASGI configuration
2. **Integrate SocialFeed** component into MemeQuestScreen
3. **Add real-time engagement** tracking
4. **Implement BIPOC spotlight** features
5. **Add voice comments** for social interactions
6. **Test WebSocket** connections with multiple users
7. **Add social analytics** for user insights

This real-time WebSocket service will make MemeQuest **highly engaging** with **live social interactions** and **instant updates**! 🔌🚀