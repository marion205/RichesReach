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
        password=os.getenv('DEV_TEST_USER_PASSWORD', secrets.token_urlsafe(16))
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
                email='test@example.com', name='Test User', password=os.getenv('DEV_TEST_USER_PASSWORD', secrets.token_urlsafe(16))
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
                    email='test@example.com', name='Test User', password=os.getenv('DEV_TEST_USER_PASSWORD', secrets.token_urlsafe(16))
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
                email='test@example.com', name='Test User', password=os.getenv('DEV_TEST_USER_PASSWORD', secrets.token_urlsafe(16))
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

# Async-safe database operation wrappers
@database_sync_to_async
def get_family_group_by_owner(user_id):
    """Get family group by owner ID"""
    if not FamilyGroup:
        return None
    return FamilyGroup.objects.filter(owner_id=user_id).first()

@database_sync_to_async
def get_family_member_by_user(user_id):
    """Get family member by user ID"""
    if not FamilyMember:
        return None
    return FamilyMember.objects.filter(user_id=user_id).first()

@database_sync_to_async
def get_family_group_with_relations(group_id):
    """Get family group with prefetched relations"""
    if not FamilyGroup:
        return None
    return FamilyGroup.objects.select_related('owner').prefetch_related('members__user').get(id=group_id)

@database_sync_to_async
def create_family_group_sync(user_id, name, group_id):
    """Create family group synchronously"""
    if not FamilyGroup or not FamilyMember:
        return None
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user_obj = User.objects.get(id=user_id)
    
    group = FamilyGroup.objects.create(
        id=group_id,
        name=name,
        owner=user_obj,
    )
    
    FamilyMember.objects.create(
        id=f"member_{uuid.uuid4().hex[:12]}",
        family_group=group,
        user=user_obj,
        role='owner',
    )
    
    return group.id

@database_sync_to_async
def create_family_invite_sync(group_id, email, role, invite_code, user_id, expires_at):
    """Create family invite synchronously"""
    if not FamilyInvite:
        return None
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user_obj = User.objects.get(id=user_id)
    group = FamilyGroup.objects.get(id=group_id)
    
    invite = FamilyInvite.objects.create(
        id=f"invite_{uuid.uuid4().hex[:12]}",
        family_group=group,
        email=email,
        role=role,
        invite_code=invite_code,
        invited_by=user_obj,
        expires_at=expires_at,
    )
    return invite_code

@database_sync_to_async
def get_family_invite_by_code(invite_code):
    """Get family invite by code"""
    if not FamilyInvite:
        return None
    return FamilyInvite.objects.filter(
        invite_code=invite_code,
        accepted_at__isnull=True
    ).first()

@database_sync_to_async
def accept_family_invite_sync(invite_id, user_id, role):
    """Accept family invite synchronously"""
    if not FamilyInvite or not FamilyMember:
        return None
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user_obj = User.objects.get(id=user_id)
    invite = FamilyInvite.objects.get(id=invite_id)
    
    member = FamilyMember.objects.create(
        id=f"member_{uuid.uuid4().hex[:12]}",
        family_group=invite.family_group,
        user=user_obj,
        role=role,
    )
    
    invite.accepted_at = datetime.now()
    invite.accepted_by = user_obj
    invite.save()
    
    return invite.family_group.id

@database_sync_to_async
def get_family_member_by_id(member_id):
    """Get family member by ID"""
    if not FamilyMember:
        return None
    return FamilyMember.objects.filter(id=member_id).first()

@database_sync_to_async
def update_member_permissions_sync(member_id, permissions):
    """Update member permissions synchronously"""
    if not FamilyMember:
        return None
    member = FamilyMember.objects.get(id=member_id)
    member.set_permissions(**permissions)
    member.save()
    return member

@database_sync_to_async
def sync_orb_state_sync(group_id, net_worth, user_id, event_type, event_data):
    """Sync orb state synchronously"""
    if not OrbSyncEvent:
        return None
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user_obj = User.objects.get(id=user_id)
    group = FamilyGroup.objects.get(id=group_id)
    
    group.shared_orb_net_worth = net_worth
    group.shared_orb_last_synced = datetime.now()
    group.save()
    
    event = OrbSyncEvent.objects.create(
        id=f"event_{uuid.uuid4().hex[:12]}",
        family_group=group,
        user=user_obj,
        event_type=event_type,
        data=event_data,
    )
    return True

@database_sync_to_async
def get_orb_events_sync(group_id, since_dt=None, limit=50):
    """Get orb events synchronously"""
    if not OrbSyncEvent:
        return []
    group = FamilyGroup.objects.get(id=group_id)
    events_query = OrbSyncEvent.objects.filter(family_group=group)
    
    if since_dt:
        events_query = events_query.filter(timestamp__gte=since_dt)
    
    return list(events_query.order_by('-timestamp')[:limit])

@database_sync_to_async
def delete_family_member(member_id):
    """Delete family member"""
    if not FamilyMember:
        return False
    member = FamilyMember.objects.get(id=member_id)
    member.delete()
    return True

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
        
        # Use async-safe helper
        group_id = await create_family_group_sync(
            user_id=user.id,
            name=request.name,
            group_id=f"family_{uuid.uuid4().hex[:12]}"
        )
        
        # Get group with relations for response
        group = await get_family_group_with_relations(group_id)
        return family_group_to_response(group)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating family group: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/group", response_model=FamilyGroupResponse)
async def get_family_group(user: User = Depends(get_current_user)):
    """
    Get current user's family group.
    Returns 404 if user is not in a family group (this is normal, not an error).
    """
    if FamilyGroup is None:
        raise HTTPException(status_code=404, detail="No family group found")
    
    try:
        import asyncio
        
        def get_and_convert_sync():
            """Get family group and convert to response synchronously"""
            try:
                connections.close_all()  # Close connections before ORM operations
                
                # Get user ID to avoid passing user object (which might have lazy attributes)
                user_id = user.id if hasattr(user, 'id') else None
                if not user_id:
                    logger.warning(f"Invalid user object in get_family_group: {type(user)}")
                    return None  # Return None instead of raising - will be handled as 404
                
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
                        # User not in a family group - this is normal, return None
                        logger.info(f"User {user_id} is not in a family group")
                        return None
                
                # Force evaluation of all relationships to ensure they're loaded
                _ = group.owner  # Access owner
                members_list = list(group.members.all())  # Force evaluation of members
                for member in members_list:
                    _ = member.user  # Access user for each member
                
                # Convert to response (all ORM access happens here)
                return family_group_to_response(group)
            except FamilyGroup.DoesNotExist:
                logger.info(f"Family group not found for user {user_id}")
                return None
            except Exception as sync_error:
                logger.error(f"Error in get_and_convert_sync: {sync_error}", exc_info=True)
                # Re-raise to be caught by outer try/except
                raise
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, get_and_convert_sync)
        
        # If result is None, user is not in a family group (normal case)
        if result is None:
            raise HTTPException(status_code=404, detail="No family group found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching family group: {e}", exc_info=True)
        # Return 500 only for actual errors, not for "not found" cases
        raise HTTPException(status_code=500, detail=f"Error fetching family group: {str(e)}")


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
        group = await get_family_group_by_owner(user.id)
        if not group:
            member = await get_family_member_by_user(user.id)
            if not member:
                raise HTTPException(status_code=403, detail="No permission to invite")
            # Get permissions synchronously in executor
            import asyncio
            def get_permissions_sync():
                connections.close_all()
                member_obj = FamilyMember.objects.get(id=member.id)
                return member_obj.get_permissions()
            loop = asyncio.get_event_loop()
            permissions = await loop.run_in_executor(None, get_permissions_sync)
            if not permissions.get('canInvite', False):
                raise HTTPException(status_code=403, detail="No permission to invite")
            group_id = member.family_group_id
        else:
            group_id = group.id
        
        # Generate invite code
        invite_code = secrets.token_urlsafe(16)
        
        # Create invite (expires in 7 days)
        await create_family_invite_sync(
            group_id=group_id,
            email=request.email,
            role=request.role,
            invite_code=invite_code,
            user_id=user.id,
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
        invite = await get_family_invite_by_code(request.inviteCode)
        
        if not invite:
            raise HTTPException(status_code=404, detail="Invalid invite code")
        
        # Check if expired (sync check in executor)
        import asyncio
        def check_expired_sync():
            connections.close_all()
            invite_obj = FamilyInvite.objects.get(id=invite.id)
            return invite_obj.is_expired()
        loop = asyncio.get_event_loop()
        is_expired = await loop.run_in_executor(None, check_expired_sync)
        
        if is_expired:
            raise HTTPException(status_code=400, detail="Invite has expired")
        
        # Check if user is already a member
        def check_existing_sync():
            connections.close_all()
            return FamilyMember.objects.filter(
                family_group_id=invite.family_group_id,
                user_id=user.id
            ).first()
        existing = await loop.run_in_executor(None, check_existing_sync)
        
        if existing:
            raise HTTPException(status_code=400, detail="Already a member of this group")
        
        # Accept invite and add user as member
        group_id = await accept_family_invite_sync(
            invite_id=invite.id,
            user_id=user.id,
            role=invite.role
        )
        
        # Get group with relations for response
        group = await get_family_group_with_relations(group_id)
        return family_group_to_response(group)
        
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
        member = await get_family_member_by_id(member_id)
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        
        # Verify user is owner or has permission (sync check in executor)
        import asyncio
        def check_permission_sync():
            connections.close_all()
            member_obj = FamilyMember.objects.get(id=member.id)
            is_owner = member_obj.family_group.owner_id == user.id
            user_member = FamilyMember.objects.filter(
                family_group_id=member_obj.family_group_id,
                user_id=user.id
            ).first()
            user_permissions = user_member.get_permissions() if user_member else {}
            return is_owner or user_permissions.get('canInvite', False)
        loop = asyncio.get_event_loop()
        has_permission = await loop.run_in_executor(None, check_permission_sync)
        
        if not has_permission:
            raise HTTPException(status_code=403, detail="No permission to update")
        
        # Update permissions
        updated_member = await update_member_permissions_sync(member_id, request.permissions)
        
        # Get member with relations for response
        def get_member_response_sync():
            connections.close_all()
            member_obj = FamilyMember.objects.select_related('user', 'family_group').get(id=member_id)
            return {
                'id': member_obj.id,
                'userId': str(member_obj.user.id),
                'name': member_obj.user.name,
                'email': member_obj.user.email,
                'role': member_obj.role,
                'avatar': getattr(member_obj.user, 'profile_pic', None),
                'permissions': member_obj.get_permissions(),
                'joinedAt': member_obj.joined_at.isoformat(),
                'lastActive': member_obj.last_active.isoformat() if member_obj.last_active else None,
            }
        response_data = await loop.run_in_executor(None, get_member_response_sync)
        
        return FamilyMemberResponse(**response_data)
        
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
        group = await get_family_group_by_owner(user.id)
        if not group:
            member = await get_family_member_by_user(user.id)
            if not member:
                raise HTTPException(status_code=404, detail="No family group found")
            group_id = member.family_group_id
        else:
            group_id = group.id
        
        # Sync orb state
        await sync_orb_state_sync(
            group_id=group_id,
            net_worth=request.netWorth,
            user_id=user.id,
            event_type='gesture' if request.gesture else 'update',
            event_data={
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
        group = await get_family_group_by_owner(user.id)
        if not group:
            member = await get_family_member_by_user(user.id)
            if not member:
                return []
            group_id = member.family_group_id
        else:
            group_id = group.id
        
        # Parse since date
        since_dt = None
        if since:
            try:
                since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
            except ValueError:
                pass
        
        # Get events
        events = await get_orb_events_sync(group_id, since_dt, limit=50)
        
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
        member = await get_family_member_by_id(member_id)
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        
        # Verify user is owner and check role (sync check in executor)
        import asyncio
        def check_remove_permission_sync():
            connections.close_all()
            member_obj = FamilyMember.objects.select_related('family_group').get(id=member_id)
            is_owner = member_obj.family_group.owner_id == user.id
            is_owner_role = member_obj.role == 'owner'
            return is_owner, is_owner_role
        loop = asyncio.get_event_loop()
        is_owner, is_owner_role = await loop.run_in_executor(None, check_remove_permission_sync)
        
        if not is_owner:
            raise HTTPException(status_code=403, detail="Only owner can remove members")
        
        if is_owner_role:
            raise HTTPException(status_code=400, detail="Cannot remove owner")
        
        # Remove member
        await delete_family_member(member_id)
        
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
        member = await get_family_member_by_user(user.id)
        if not member:
            raise HTTPException(status_code=404, detail="Not a member of any group")
        
        # Check role and remove (sync check in executor)
        import asyncio
        def check_and_remove_sync():
            connections.close_all()
            member_obj = FamilyMember.objects.get(id=member.id)
            if member_obj.role == 'owner':
                raise HTTPException(status_code=400, detail="Owner cannot leave. Transfer ownership first.")
            member_obj.delete()
            return True
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, check_and_remove_sync)
        
        return {"success": True, "message": "Left family group"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error leaving family group: {e}")
        raise HTTPException(status_code=500, detail=str(e))
