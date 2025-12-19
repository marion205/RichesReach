"""
WebSocket Broadcast Helper for Security Events
PRODUCTION-SAFE: Django publishes JSON to Redis, Socket.IO instances listen and emit

Architecture:
- Django → Redis Pub/Sub (plain JSON) → Socket.IO instances → Clients
- This works across multiple instances/containers
"""
import logging
import uuid
import json
from datetime import datetime

logger = logging.getLogger(__name__)

# Redis client for publishing (Django side)
_redis_client = None
_redis_channel = 'socketio:security:events'

def set_redis_client(redis_client):
    """Set Redis client for publishing events"""
    global _redis_client
    _redis_client = redis_client
    if redis_client:
        logger.info("Redis client set for security event broadcasting (multi-instance safe)")

def broadcast_security_event(user_id, event_data, action='created'):
    """
    Broadcast a security event via Redis pub/sub (multi-instance safe)
    
    PRODUCTION PATTERN: Django publishes plain JSON to Redis.
    Socket.IO instances subscribe to Redis and emit to rooms.
    
    Event Envelope Format (standardized):
    {
        "type": "security-event-created|resolved",
        "eventId": "uuid",
        "correlationId": "uuid",
        "userId": 123,
        "occurredAt": "ISO8601",
        "version": 1,
        "data": { ... }
    }
    
    Args:
        user_id: User ID to broadcast to
        event_data: Event data dictionary
        action: 'created' or 'resolved'
    """
    correlation_id = str(uuid.uuid4())[:8]
    event_id = event_data.get('id', 'unknown')
    
    # Sanitize user_id for logging (no PII)
    user_id_hash = str(hash(str(user_id)))[:8] if user_id else 'unknown'
    
    logger.info(
        f"[Security] [{correlation_id}] Broadcasting {action} | "
        f"event_id={event_id} user_id_hash={user_id_hash}"
    )
    
    # Standardized event envelope
    envelope = {
        'type': f'security-event-{action}',
        'eventId': str(event_id),
        'correlationId': correlation_id,
        'userId': str(user_id),  # Only in payload, not logs
        'occurredAt': datetime.utcnow().isoformat() + 'Z',
        'version': 1,
        'data': {
            'eventType': event_data.get('eventType'),
            'threatLevel': event_data.get('threatLevel'),
            'description': event_data.get('description'),
            'resolved': event_data.get('resolved', False),
            'createdAt': event_data.get('created_at'),
            'resolvedAt': event_data.get('resolved_at'),
        }
    }
    
    if _redis_client:
        try:
            # Publish to Redis (any Socket.IO instance can pick it up)
            _redis_client.publish(_redis_channel, json.dumps(envelope))
            
            logger.info(
                f"[Security] [{correlation_id}] Published to Redis | "
                f"channel={_redis_channel} event_id={event_id}"
            )
            return True
        except Exception as e:
            logger.error(f"[Security] [{correlation_id}] Redis publish failed: {e}")
            return False
    else:
        logger.warning(
            f"[Security] [{correlation_id}] No Redis client - event not broadcast "
            f"(multi-instance will fail without Redis)"
        )
        return False

