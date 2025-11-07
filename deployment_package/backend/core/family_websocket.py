"""
WebSocket consumer for real-time Family Sharing orb synchronization
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

try:
    from .family_models import FamilyGroup, FamilyMember, OrbSyncEvent
except ImportError:
    FamilyGroup = None
    FamilyMember = None
    OrbSyncEvent = None

User = get_user_model()
logger = logging.getLogger(__name__)


class FamilyOrbSyncConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time orb synchronization across family members.
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope.get('user')
        
        if not self.user or self.user.is_anonymous:
            await self.close()
            return
        
        # Get user's family group
        self.family_group = await self.get_family_group()
        
        if not self.family_group:
            await self.close()
            return
        
        # Join family group room
        self.room_group_name = f"family_{self.family_group.id}"
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"User {self.user.email} connected to family orb sync")
        
        # Send current orb state
        await self.send_initial_state()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        logger.info(f"User {self.user.email} disconnected from family orb sync")
    
    async def receive(self, text_data):
        """Handle messages from WebSocket client"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'sync_orb':
                await self.handle_orb_sync(data)
            elif message_type == 'gesture':
                await self.handle_gesture(data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def handle_orb_sync(self, data):
        """Handle orb state synchronization"""
        net_worth = data.get('netWorth', 0)
        gesture = data.get('gesture')
        view_mode = data.get('viewMode')
        
        # Update family group orb state
        await self.update_orb_state(net_worth)
        
        # Create sync event
        await self.create_sync_event('update', {
            'netWorth': net_worth,
            'viewMode': view_mode,
        })
        
        # Broadcast to all family members
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'orb_sync',
                'netWorth': net_worth,
                'userId': str(self.user.id),
                'userName': self.user.name,
                'viewMode': view_mode,
            }
        )
    
    async def handle_gesture(self, data):
        """Handle gesture events"""
        gesture = data.get('gesture')
        
        # Create sync event
        await self.create_sync_event('gesture', {
            'gesture': gesture,
        })
        
        # Broadcast gesture to all family members
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'gesture_event',
                'gesture': gesture,
                'userId': str(self.user.id),
                'userName': self.user.name,
            }
        )
    
    async def orb_sync(self, event):
        """Send orb sync event to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'orb_sync',
            'netWorth': event['netWorth'],
            'userId': event['userId'],
            'userName': event['userName'],
            'viewMode': event.get('viewMode'),
        }))
    
    async def gesture_event(self, event):
        """Send gesture event to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'gesture',
            'gesture': event['gesture'],
            'userId': event['userId'],
            'userName': event['userName'],
        }))
    
    async def send_initial_state(self):
        """Send initial orb state to newly connected client"""
        if not self.family_group:
            return
        
        state = await self.get_orb_state()
        await self.send(text_data=json.dumps({
            'type': 'initial_state',
            'netWorth': float(state['netWorth']),
            'lastSynced': state['lastSynced'],
            'enabled': state['enabled'],
        }))
    
    # Database operations
    
    @database_sync_to_async
    def get_family_group(self):
        """Get user's family group"""
        if not FamilyGroup:
            return None
        
        try:
            # Try as owner
            group = FamilyGroup.objects.filter(owner=self.user).first()
            if group:
                return group
            
            # Try as member
            member = FamilyMember.objects.filter(user=self.user).first()
            if member:
                return member.family_group
            
            return None
        except Exception as e:
            logger.error(f"Error getting family group: {e}")
            return None
    
    @database_sync_to_async
    def update_orb_state(self, net_worth):
        """Update family group orb state"""
        if not self.family_group or not FamilyGroup:
            return
        
        from django.utils import timezone
        self.family_group.shared_orb_net_worth = net_worth
        self.family_group.shared_orb_last_synced = timezone.now()
        self.family_group.save(update_fields=['shared_orb_net_worth', 'shared_orb_last_synced'])
    
    @database_sync_to_async
    def get_orb_state(self):
        """Get current orb state"""
        if not self.family_group:
            return {
                'netWorth': 0,
                'lastSynced': None,
                'enabled': False,
            }
        
        return {
            'netWorth': float(self.family_group.shared_orb_net_worth),
            'lastSynced': self.family_group.shared_orb_last_synced.isoformat() if self.family_group.shared_orb_last_synced else None,
            'enabled': self.family_group.shared_orb_enabled,
        }
    
    @database_sync_to_async
    def create_sync_event(self, event_type, data):
        """Create orb sync event"""
        if not OrbSyncEvent or not self.family_group:
            return
        
        import uuid
        from django.utils import timezone
        
        OrbSyncEvent.objects.create(
            id=f"event_{uuid.uuid4().hex[:12]}",
            family_group=self.family_group,
            user=self.user,
            event_type=event_type,
            data=data,
            timestamp=timezone.now(),
        )

