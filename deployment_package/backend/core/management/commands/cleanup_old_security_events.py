"""
Django management command to clean up old security events
Compliance: GDPR/CCPA data retention policy

Usage:
    python manage.py cleanup_old_security_events --days=90
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import SecurityEvent
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up old security events based on retention policy'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days to retain events (default: 90)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Find old events
        old_events = SecurityEvent.objects.filter(created_at__lt=cutoff_date)
        count = old_events.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would delete {count} security events older than {days} days '
                    f'(before {cutoff_date.date()})'
                )
            )
            if count > 0:
                self.stdout.write('Sample events to be deleted:')
                for event in old_events[:10]:
                    self.stdout.write(
                        f'  - {event.id} | {event.event_type} | {event.created_at.date()} | '
                        f'User: {event.user.email[:20]}...'
                    )
        else:
            if count > 0:
                # Delete old events
                deleted_count, _ = old_events.delete()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Deleted {deleted_count} security events older than {days} days'
                    )
                )
                logger.info(f"Cleaned up {deleted_count} security events older than {days} days")
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'No security events older than {days} days to clean up')
                )

