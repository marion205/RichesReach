"""
Family Sharing API - Multi-user orb sharing and family management
Updated to use database models
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta
import sys
import os
import secrets
import uuid

# Setup logger first
logger = logging.getLogger(__name__)

# Django imports
import django
from django.conf import settings
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
    django.setup()

from django.contrib.auth import get_user_model
from django.db import connections
from channels.db import database_sync_to_async

# Try to import graphql_jwt, but make it optional
try:
    from graphql_jwt.shortcuts import get_user_by_token
    from graphql_jwt.exceptions import PermissionDenied
    GRAPHQL_JWT_AVAILABLE = True
except ImportError:
    GRAPHQL_JWT_AVAILABLE = False
    logger.warning("graphql_jwt not available. Using fallback authentication.")

# Import family models
try:
    from .family_models import FamilyGroup, FamilyMember, FamilyInvite, OrbSyncEvent
except ImportError:
    # Fallback if models not migrated yet
    FamilyGroup = None
    FamilyMember = None
    FamilyInvite = None
    OrbSyncEvent = None

User = get_user_model()

backend_path = os.path.join(os.path.dirname(__file__))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

router = APIRouter(prefix="/api/family", tags=["Family Sharing"])

# ============================================================================
# Authentication Helper
# ============================================================================

# Helper function to get or create test user (sync function)
@database_sync_to_async
def get_or_create_test_user():
    """Get first user or create test user (async-safe using channels.db)"""
    user = User.objects.first()
    if user:
        return user
    # Create test user if none exists
    return User.objects.create_user(
        email='test@example.com',
        name='Test User',
        password='test123'
    )

async def get_current_user(authorization: Optional[str] = Header(None)) -> User:
    """
    Get current user from JWT token in Authorization header.
    Falls back to mock user in development if graphql_jwt is not available or token is invalid.
    """
    # Handle missing or invalid authorization header
    if not authorization or not authorization.startswith('Bearer '):
        logger.info("No authorization header, using development fallback")
        # Try to get user from database, but don't fail if it doesn't work
        try:
            user = await get_or_create_test_user()
            logger.info(f"Using fallback user: {user.email}")
            return user
        except Exception as e:
            logger.warning(f"Could not get/create test user: {e}, creating mock user")
            # Create a mock user object without database
            from django.contrib.auth.models import AnonymousUser
            # For development, we'll use a workaround: get any user synchronously in a thread
            import asyncio
            loop = asyncio.get_event_loop()
            user = await loop.run_in_executor(None, lambda: User.objects.first() or User.objects.create_user(
                email='test@example.com', name='Test User', password='test123'
            ))
            return user
    
    token = authorization[7:]  # Remove 'Bearer ' prefix
    
    # Check if it's a dev token (starts with "dev-token-")
    if token.startswith('dev-token-'):
        logger.info("Dev token detected, using development fallback")
        try:
            # Use executor to run sync code in a thread, closing connections first
            import asyncio
            def get_or_create_user_sync():
                # Close all database connections before running ORM
                connections.close_all()
                user = User.objects.first()
                if user:
                    # Materialize all attributes to avoid lazy loading
                    _ = user.id
                    _ = user.email
                    _ = getattr(user, 'name', None) or getattr(user, 'username', None)
                    return user
                user = User.objects.create_user(
                    email='test@example.com', name='Test User', password='test123'
                )
                # Materialize all attributes
                _ = user.id
                _ = user.email
                return user
            
            loop = asyncio.get_event_loop()
            user = await loop.run_in_executor(None, get_or_create_user_sync)
            logger.info(f"Using fallback user for dev token: {user.email}")
            return user
        except Exception as e:
            logger.warning(f"Could not get/create test user for dev token: {e}")
            raise HTTPException(status_code=401, detail="Authentication failed")
    
    # Try to validate real JWT token
    if GRAPHQL_JWT_AVAILABLE:
        try:
            # Use executor to run sync code in a thread
            import asyncio
            loop = asyncio.get_event_loop()
            user = await loop.run_in_executor(None, lambda: get_user_by_token(token))
            logger.info(f"JWT authentication successful: {user.email}")
            return user
        except (PermissionDenied, Exception) as e:
            logger.warning(f"JWT authentication failed: {e}, using fallback")
            # Fall through to fallback instead of raising error
            pass
    
    # Fallback: use first available user (for development)
    logger.warning("JWT validation failed or unavailable, using fallback authentication")
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        user = await loop.run_in_executor(None, lambda: User.objects.first() or User.objects.create_user(
            email='test@example.com', name='Test User', password='test123'
        ))
        logger.info(f"Using fallback user: {user.email}")
        return user
    except Exception as e:
        logger.error(f"Fallback authentication failed: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")

# ============================================================================
# Request/Response Models
# ============================================================================

class CreateFamilyGroupRequest(BaseModel):
    name: str

class InviteMemberRequest(BaseModel):
    email: str
    role: str = "member"  # member or teen

class AcceptInviteRequest(BaseModel):
    inviteCode: str

class UpdatePermissionsRequest(BaseModel):
    permissions: Dict[str, Any]

class SyncOrbStateRequest(BaseModel):
    netWorth: float
    gesture: Optional[str] = None
    viewMode: Optional[str] = None

class FamilyMemberResponse(BaseModel):
    id: str
    userId: str
    name: str
    email: str
    role: str
    avatar: Optional[str] = None
    permissions: Dict[str, Any]
    joinedAt: str
    lastActive: Optional[str] = None

class FamilyGroupResponse(BaseModel):
    id: str
    name: str
    ownerId: str
    members: List[FamilyMemberResponse]
    sharedOrb: Dict[str, Any]
    settings: Dict[str, Any]
    createdAt: str

class OrbSyncEventResponse(BaseModel):
    type: str
    userId: str
    userName: str
    timestamp: str
    data: Optional[Dict[str, Any]] = None

# ============================================================================
# Helper Functions
# ============================================================================

def family_group_to_response(group: FamilyGroup) -> FamilyGroupResponse:
    """Convert FamilyGroup model to response"""
    members = []
    for member in group.members.all():
        # Get user name - try different field names
        user_name = getattr(member.user, 'name', None) or \
                   getattr(member.user, 'username', None) or \
                   (f"{getattr(member.user, 'first_name', '')} {getattr(member.user, 'last_name', '')}".strip() or member.user.email.split('@')[0])
        
        # Get user email
        user_email = getattr(member.user, 'email', '')
        
        # Get avatar/profile pic
        user_avatar = getattr(member.user, 'profile_pic', None) or \
                     getattr(member.user, 'avatar', None) or \
                     getattr(member.user, 'profile_picture', None)
        
        members.append(FamilyMemberResponse(
            id=member.id,
            userId=str(member.user.id),
            name=user_name,
            email=user_email,
            role=member.role,
            avatar=user_avatar,
            permissions=member.get_permissions(),
            joinedAt=member.joined_at.isoformat(),
            lastActive=member.last_active.isoformat() if member.last_active else None,
        ))
    
    return FamilyGroupResponse(
        id=group.id,
        name=group.name,
        ownerId=str(group.owner.id),
        members=members,
        sharedOrb={
            "enabled": group.shared_orb_enabled,
            "netWorth": float(group.shared_orb_net_worth),
            "lastSynced": group.shared_orb_last_synced.isoformat() if group.shared_orb_last_synced else None,
        },
        settings=group.get_settings(),
        createdAt=group.created_at.isoformat(),
    )

def orb_event_to_response(event: OrbSyncEvent) -> OrbSyncEventResponse:
    """Convert OrbSyncEvent model to response"""
    return OrbSyncEventResponse(
        type=event.event_type,
        userId=str(event.user.id),
        userName=event.user.name,
        timestamp=event.timestamp.isoformat(),
        data=event.data,
    )

# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/group", response_model=FamilyGroupResponse)
async def create_family_group(
    request: CreateFamilyGroupRequest,
    user: User = Depends(get_current_user)
):
    """
    Create a new family group for orb sharing.
    """
    if FamilyGroup is None:
        raise HTTPException(status_code=501, detail="Database models not available. Run migrations first.")
    
    try:
        import asyncio
        
        def create_and_convert_sync():
            """Create family group and convert to response synchronously"""
            connections.close_all()  # Close connections before ORM operations
            
            # Get user ID to avoid passing user object (which might have lazy attributes)
            user_id = user.id if hasattr(user, 'id') else None
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid user")
            
            # Check if user already has a family group
            existing = FamilyGroup.objects.filter(owner_id=user_id).first()
            if existing:
                raise HTTPException(status_code=400, detail="User already has a family group")
            
            # Get user object for creation
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user_obj = User.objects.get(id=user_id)
            
            # Create family group
            group = FamilyGroup.objects.create(
                id=f"family_{uuid.uuid4().hex[:12]}",
                name=request.name,
                owner=user_obj,
            )
            
            # Add owner as first member
            FamilyMember.objects.create(
                id=f"member_{uuid.uuid4().hex[:12]}",
                family_group=group,
                user=user_obj,
                role='owner',
            )
            
            # Reload group with prefetched relationships
            group = FamilyGroup.objects.select_related('owner').prefetch_related('members__user').get(id=group.id)
            
            # Force evaluation of all relationships
            _ = group.owner
            members_list = list(group.members.all())
            for member in members_list:
                _ = member.user
            
            # Convert to response (all ORM access happens here)
            return family_group_to_response(group)
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, create_and_convert_sync)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating family group: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/group", response_model=FamilyGroupResponse)
async def get_family_group(user: User = Depends(get_current_user)):
    """
    Get current user's family group.
    """
    if FamilyGroup is None:
        raise HTTPException(status_code=404, detail="No family group found")
    
    try:
        import asyncio
        
        def get_and_convert_sync():
            """Get family group and convert to response synchronously"""
            connections.close_all()  # Close connections before ORM operations
            
            # Get user ID to avoid passing user object (which might have lazy attributes)
            user_id = user.id if hasattr(user, 'id') else None
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid user")
            
            # Try to find group where user is owner or member
            # Use select_related and prefetch_related to eagerly load relationships
            group = FamilyGroup.objects.select_related('owner').prefetch_related('members__user').filter(owner_id=user_id).first()
            if not group:
                member = FamilyMember.objects.select_related('family_group__owner', 'user').prefetch_related('family_group__members__user').filter(user_id=user_id).first()
                if member:
                    group = member.family_group
                    # Reload with prefetch to ensure all relationships are loaded
                    group = FamilyGroup.objects.select_related('owner').prefetch_related('members__user').get(id=group.id)
                else:
                    raise HTTPException(status_code=404, detail="No family group found")
            
            # Force evaluation of all relationships to ensure they're loaded
            _ = group.owner  # Access owner
            members_list = list(group.members.all())  # Force evaluation of members
            for member in members_list:
                _ = member.user  # Access user for each member
            
            # Convert to response (all ORM access happens here)
            return family_group_to_response(group)
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, get_and_convert_sync)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching family group: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invite")
async def invite_member(
    request: InviteMemberRequest,
    user: User = Depends(get_current_user)
):
    """
    Invite a family member to join the group.
    """
    if not FamilyInvite:
        raise HTTPException(status_code=501, detail="Database models not available")
    
    try:
        # Get user's family group
        group = FamilyGroup.objects.filter(owner=user).first()
        if not group:
            member = FamilyMember.objects.filter(user=user).first()
            if not member or not member.get_permissions().get('canInvite', False):
                raise HTTPException(status_code=403, detail="No permission to invite")
            group = member.family_group
        
        # Generate invite code
        invite_code = secrets.token_urlsafe(16)
        
        # Create invite (expires in 7 days)
        invite = FamilyInvite.objects.create(
            id=f"invite_{uuid.uuid4().hex[:12]}",
            family_group=group,
            email=request.email,
            role=request.role,
            invite_code=invite_code,
            invited_by=user,
            expires_at=datetime.now() + timedelta(days=7),
        )
        
        # TODO: Send email invitation
        
        return {
            "success": True,
            "inviteCode": invite_code,
            "message": f"Invite sent to {request.email}",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inviting member: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invite/accept", response_model=FamilyGroupResponse)
async def accept_invite(
    request: AcceptInviteRequest,
    user: User = Depends(get_current_user)
):
    """
    Accept a family group invitation.
    """
    if not FamilyInvite or not FamilyMember:
        raise HTTPException(status_code=501, detail="Database models not available")
    
    try:
        # Find invite
        invite = FamilyInvite.objects.filter(
            invite_code=request.inviteCode,
            accepted_at__isnull=True
        ).first()
        
        if not invite:
            raise HTTPException(status_code=404, detail="Invalid invite code")
        
        if invite.is_expired():
            raise HTTPException(status_code=400, detail="Invite has expired")
        
        # Check if user is already a member
        existing = FamilyMember.objects.filter(
            family_group=invite.family_group,
            user=user
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Already a member of this group")
        
        # Add user as member
        member = FamilyMember.objects.create(
            id=f"member_{uuid.uuid4().hex[:12]}",
            family_group=invite.family_group,
            user=user,
            role=invite.role,
        )
        
        # Mark invite as accepted
        invite.accepted_at = datetime.now()
        invite.accepted_by = user
        invite.save()
        
        return family_group_to_response(invite.family_group)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accepting invite: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/members/{member_id}/permissions", response_model=FamilyMemberResponse)
async def update_member_permissions(
    member_id: str,
    request: UpdatePermissionsRequest,
    user: User = Depends(get_current_user)
):
    """
    Update permissions for a family member (parental controls).
    """
    if not FamilyMember:
        raise HTTPException(status_code=501, detail="Database models not available")
    
    try:
        # Get member
        member = FamilyMember.objects.filter(id=member_id).first()
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        
        # Verify user is owner or has permission
        is_owner = member.family_group.owner == user
        user_member = FamilyMember.objects.filter(
            family_group=member.family_group,
            user=user
        ).first()
        
        if not is_owner and (not user_member or not user_member.get_permissions().get('canInvite', False)):
            raise HTTPException(status_code=403, detail="No permission to update")
        
        # Update permissions
        member.set_permissions(**request.permissions)
        member.save()
        
        return FamilyMemberResponse(
            id=member.id,
            userId=str(member.user.id),
            name=member.user.name,
            email=member.user.email,
            role=member.role,
            avatar=member.user.profile_pic,
            permissions=member.get_permissions(),
            joinedAt=member.joined_at.isoformat(),
            lastActive=member.last_active.isoformat() if member.last_active else None,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating permissions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orb/sync")
async def sync_orb_state(
    request: SyncOrbStateRequest,
    user: User = Depends(get_current_user)
):
    """
    Sync orb state across family members.
    """
    if not OrbSyncEvent:
        raise HTTPException(status_code=501, detail="Database models not available")
    
    try:
        # Get user's family group
        group = FamilyGroup.objects.filter(owner=user).first()
        if not group:
            member = FamilyMember.objects.filter(user=user).first()
            if not member:
                raise HTTPException(status_code=404, detail="No family group found")
            group = member.family_group
        
        # Update shared orb state
        group.shared_orb_net_worth = request.netWorth
        group.shared_orb_last_synced = datetime.now()
        group.save()
        
        # Create sync event
        event = OrbSyncEvent.objects.create(
            id=f"event_{uuid.uuid4().hex[:12]}",
            family_group=group,
            user=user,
            event_type='gesture' if request.gesture else 'update',
            data={
                "netWorth": request.netWorth,
                "gesture": request.gesture,
                "viewMode": request.viewMode,
            }
        )
        
        # TODO: Broadcast to other family members via WebSocket
        
        return {
            "success": True,
            "syncedAt": datetime.now().isoformat(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing orb state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orb/events", response_model=List[OrbSyncEventResponse])
async def get_orb_sync_events(
    since: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """
    Get real-time orb sync events.
    """
    if not OrbSyncEvent:
        return []
    
    try:
        # Get user's family group
        group = FamilyGroup.objects.filter(owner=user).first()
        if not group:
            member = FamilyMember.objects.filter(user=user).first()
            if not member:
                return []
            group = member.family_group
        
        # Query events
        events_query = OrbSyncEvent.objects.filter(family_group=group)
        
        if since:
            try:
                since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
                events_query = events_query.filter(timestamp__gte=since_dt)
            except ValueError:
                pass
        
        events = events_query.order_by('-timestamp')[:50]  # Last 50 events
        
        return [orb_event_to_response(event) for event in events]
        
    except Exception as e:
        logger.error(f"Error fetching orb events: {e}")
        return []


@router.delete("/members/{member_id}")
async def remove_member(
    member_id: str,
    user: User = Depends(get_current_user)
):
    """
    Remove a family member from the group.
    """
    if not FamilyMember:
        raise HTTPException(status_code=501, detail="Database models not available")
    
    try:
        # Get member
        member = FamilyMember.objects.filter(id=member_id).first()
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        
        # Verify user is owner
        if member.family_group.owner != user:
            raise HTTPException(status_code=403, detail="Only owner can remove members")
        
        # Don't allow removing owner
        if member.role == 'owner':
            raise HTTPException(status_code=400, detail="Cannot remove owner")
        
        # Remove member
        member.delete()
        
        return {"success": True, "message": "Member removed"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing member: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/group/leave")
async def leave_family_group(user: User = Depends(get_current_user)):
    """
    Leave the current family group.
    """
    if not FamilyMember:
        raise HTTPException(status_code=501, detail="Database models not available")
    
    try:
        # Get user's membership
        member = FamilyMember.objects.filter(user=user).first()
        if not member:
            raise HTTPException(status_code=404, detail="Not a member of any group")
        
        # Don't allow owner to leave (must transfer ownership first)
        if member.role == 'owner':
            raise HTTPException(status_code=400, detail="Owner cannot leave. Transfer ownership first.")
        
        # Remove membership
        group_id = member.family_group.id
        member.delete()
        
        return {"success": True, "message": "Left family group"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error leaving family group: {e}")
        raise HTTPException(status_code=500, detail=str(e))
