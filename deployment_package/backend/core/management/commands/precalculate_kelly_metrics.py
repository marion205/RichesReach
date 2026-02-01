"""
Django management command to pre-calculate Kelly Criterion metrics
Can be run manually or via cron for cache warming
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.kelly_tasks import precalculate_kelly_metrics_task

User = get_user_model()


class Command(BaseCommand):
    help = 'Pre-calculate Kelly Criterion metrics for all user portfolios to warm the cache'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            default=None,
            help='User ID to pre-calculate for (default: all users)',
        )
        parser.add_argument(
            '--async',
            action='store_true',
            help='Run as Celery task (async)',
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        use_async = options.get('async', False)
        
        if use_async:
            # Queue as Celery task
            task = precalculate_kelly_metrics_task.delay(user_id=user_id)
            self.stdout.write(
                self.style.SUCCESS(f'✅ Queued Kelly pre-calculation task: {task.id}')
            )
            self.stdout.write('Check Celery logs for progress.')
        else:
            # Run synchronously
            self.stdout.write('Pre-calculating Kelly metrics...')
            result = precalculate_kelly_metrics_task(user_id=user_id)
            
            self.stdout.write('')
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Pre-calculation complete!'
                )
            )
            self.stdout.write(f'   Processed: {result.get("processed", 0)} symbols')
            self.stdout.write(f'   Already cached: {result.get("cached", 0)} symbols')
            self.stdout.write(f'   Errors: {result.get("errors", 0)}')
            self.stdout.write(f'   Total users: {result.get("total_users", 0)}')

