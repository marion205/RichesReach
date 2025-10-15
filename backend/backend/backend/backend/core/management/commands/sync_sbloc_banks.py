"""
Django management command to sync SBLOC banks from aggregator
"""
from django.core.management.base import BaseCommand
from core.sbloc_service import SBLOCDataProcessor


class Command(BaseCommand):
    help = 'Sync SBLOC banks from aggregator'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        try:
            processor = SBLOCDataProcessor()
            
            if dry_run:
                # In dry run mode, just show what would be synced
                self.stdout.write('Would sync banks from aggregator...')
                self.stdout.write(
                    self.style.SUCCESS('Dry run completed successfully')
                )
            else:
                banks_created = processor.sync_banks_from_aggregator()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully synced {banks_created} banks from aggregator'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to sync banks: {e}')
            )
            raise
