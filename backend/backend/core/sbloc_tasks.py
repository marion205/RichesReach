"""
SBLOC Celery Tasks
Background tasks for SBLOC aggregator integration
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging
from .models import SBLOCReferral
from .sbloc_service import SBLOCDataProcessor

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def reconcile_sbloc_statuses(self):
    """
    Reconcile SBLOC referral statuses with aggregator
    This task runs periodically to check for status updates that might have been missed
    """
    try:
        processor = SBLOCDataProcessor()
        
        # Get referrals that are in active states and haven't been updated recently
        stale_threshold = timezone.now() - timedelta(hours=24)
        stale_referrals = SBLOCReferral.objects.filter(
            status__in=['SUBMITTED', 'IN_REVIEW', 'CONDITIONAL_APPROVAL'],
            updated_at__lt=stale_threshold
        ).order_by('updated_at')[:50]  # Process up to 50 at a time
        
        updated_count = 0
        for referral in stale_referrals:
            try:
                if not referral.aggregator_app_id:
                    logger.warning(f"Referral {referral.id} has no aggregator app ID")
                    continue
                
                # Get current status from aggregator
                status_data = processor.aggregator_service.get_application_status(
                    referral.aggregator_app_id
                )
                
                # Map aggregator status to our status
                new_status = processor.aggregator_service._map_aggregator_status(
                    status_data.get('status', '')
                )
                
                # Update if status changed
                if new_status != referral.status:
                    processor.update_referral_status(
                        referral=referral,
                        new_status=new_status,
                        note=f"Status updated via reconciliation task",
                        source="reconciliation"
                    )
                    updated_count += 1
                    logger.info(f"Updated referral {referral.id} status: {referral.status} → {new_status}")
                
            except Exception as e:
                logger.error(f"Failed to reconcile referral {referral.id}: {e}")
                continue
        
        logger.info(f"SBLOC reconciliation completed: {updated_count} referrals updated")
        return f"Updated {updated_count} referrals"
        
    except Exception as e:
        logger.error(f"SBLOC reconciliation task failed: {e}")
        # Retry with exponential backoff
        raise self.retry(countdown=60 * (2 ** self.request.retries))


@shared_task
def sync_sbloc_banks():
    """
    Sync SBLOC banks from aggregator
    This task runs daily to keep the bank catalog up to date
    """
    try:
        processor = SBLOCDataProcessor()
        banks_created = processor.sync_banks_from_aggregator()
        
        logger.info(f"SBLOC bank sync completed: {banks_created} banks created/updated")
        return f"Synced {banks_created} banks"
        
    except Exception as e:
        logger.error(f"SBLOC bank sync task failed: {e}")
        raise


@shared_task
def cleanup_expired_sbloc_sessions():
    """
    Clean up expired SBLOC sessions
    This task runs hourly to remove old session data
    """
    try:
        from .models import SBLOCSession
        
        # Delete sessions that expired more than 24 hours ago
        cutoff_time = timezone.now() - timedelta(hours=24)
        expired_sessions = SBLOCSession.objects.filter(
            expires_at__lt=cutoff_time
        )
        
        count = expired_sessions.count()
        expired_sessions.delete()
        
        logger.info(f"Cleaned up {count} expired SBLOC sessions")
        return f"Cleaned up {count} sessions"
        
    except Exception as e:
        logger.error(f"SBLOC session cleanup task failed: {e}")
        raise


@shared_task
def send_sbloc_notifications():
    """
    Send notifications for SBLOC status changes
    This task runs every few minutes to check for status changes that need notifications
    """
    try:
        from .models import SBLOCReferral
        
        # Find referrals with recent status changes that haven't been notified
        recent_threshold = timezone.now() - timedelta(minutes=5)
        recent_changes = SBLOCReferral.objects.filter(
            updated_at__gte=recent_threshold,
            status__in=['APPROVED', 'DECLINED', 'FUNDED']
        )
        
        notification_count = 0
        for referral in recent_changes:
            try:
                # Check if we've already sent a notification for this status
                timeline = referral.timeline or []
                last_event = timeline[-1] if timeline else {}
                
                if last_event.get('source') == 'notification':
                    continue  # Already notified
                
                # Send notification (this would integrate with your notification system)
                # For now, just log it
                logger.info(f"Sending notification for referral {referral.id} status: {referral.status}")
                
                # Mark as notified in timeline
                timeline.append({
                    "status": referral.status,
                    "timestamp": timezone.now().isoformat(),
                    "note": "Notification sent",
                    "source": "notification"
                })
                referral.timeline = timeline
                referral.save()
                
                notification_count += 1
                
            except Exception as e:
                logger.error(f"Failed to send notification for referral {referral.id}: {e}")
                continue
        
        logger.info(f"SBLOC notifications sent: {notification_count}")
        return f"Sent {notification_count} notifications"
        
    except Exception as e:
        logger.error(f"SBLOC notification task failed: {e}")
        raise
