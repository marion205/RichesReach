"""
Django management command to sync transactions for ML training
Run: python manage.py sync_transactions_for_training
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class Command(BaseCommand):
    help = 'Sync bank transactions for all users (for ML training)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--months',
            type=int,
            default=36,
            help='Number of months of historical data to sync (default: 36)'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            default=None,
            help='Sync for specific user ID only'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔄 Syncing Bank Transactions for ML Training'))
        self.stdout.write('=' * 80)
        
        months = options['months']
        user_id = options.get('user_id')
        
        try:
            from core.banking_models import BankAccount
            from core.banking_tasks import sync_transactions_task
            
            # Get users
            if user_id:
                users = User.objects.filter(id=user_id)
            else:
                users = User.objects.filter(is_active=True)
            
            self.stdout.write(f'📊 Syncing transactions for {users.count()} users')
            self.stdout.write(f'📅 Date range: Last {months} months')
            
            total_synced = 0
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=months * 30)
            
            for user in users:
                # Get user's bank accounts
                accounts = BankAccount.objects.filter(user=user)
                
                if not accounts.exists():
                    self.stdout.write(self.style.WARNING(f'  ⚠️  User {user.id} has no bank accounts'))
                    continue
                
                for account in accounts:
                    try:
                        # Trigger async sync
                        sync_transactions_task.delay(
                            user.id,
                            account.id,
                            start_date.strftime('%Y-%m-%d'),
                            end_date.strftime('%Y-%m-%d')
                        )
                        self.stdout.write(f'  ✅ Queued sync for user {user.id}, account {account.id}')
                        total_synced += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  ❌ Error syncing account {account.id}: {e}'))
            
            self.stdout.write(self.style.SUCCESS(f'\n✅ Queued {total_synced} transaction syncs'))
            self.stdout.write('⏳ Transactions are syncing in background. Check back in a few minutes.')
            self.stdout.write('\n💡 To check transaction count:')
            self.stdout.write('   python manage.py shell')
            self.stdout.write('   >>> from core.banking_models import BankTransaction')
            self.stdout.write('   >>> BankTransaction.objects.filter(transaction_type="DEBIT").count()')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))
            import traceback
            traceback.print_exc()

