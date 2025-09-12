from django.core.management.base import BaseCommand, CommandError
from core.backup_service import backup_service
from core.data_validation import data_validation_service
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Create a backup of all user data and validate data integrity'

    def add_arguments(self, parser):
        parser.add_argument(
            '--validate-only',
            action='store_true',
            help='Only run data validation without creating backup',
        )
        parser.add_argument(
            '--fix-issues',
            action='store_true',
            help='Automatically fix common data issues',
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up old backup files',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to keep backups (default: 30)',
        )

    def handle(self, *args, **options):
        try:
            # Run data validation
            self.stdout.write('Starting data validation...')
            is_valid, errors = data_validation_service.validate_all_data()
            
            if not is_valid:
                self.stdout.write(
                    self.style.WARNING(f'Data validation found {len(errors)} issues:')
                )
                for error in errors:
                    self.stdout.write(f'  - {error}')
                
                if options['fix_issues']:
                    self.stdout.write('Applying automatic fixes...')
                    fixes = data_validation_service.fix_common_issues()
                    
                    if fixes:
                        self.stdout.write(
                            self.style.SUCCESS(f'Applied {len(fixes)} fixes:')
                        )
                        for fix in fixes:
                            self.stdout.write(f'  - {fix}')
                    else:
                        self.stdout.write('No automatic fixes were needed')
                    
                    # Re-validate after fixes
                    self.stdout.write('Re-validating data after fixes...')
                    is_valid, errors = data_validation_service.validate_all_data()
                    
                    if is_valid:
                        self.stdout.write(
                            self.style.SUCCESS('Data validation passed after fixes')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'Still {len(errors)} issues remain after fixes')
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING('Use --fix-issues to automatically fix common problems')
                    )
            else:
                self.stdout.write(
                    self.style.SUCCESS('Data validation passed successfully')
                )
            
            # Create backup if not validation-only
            if not options['validate_only']:
                self.stdout.write('Creating data backup...')
                backup_name = backup_service.create_full_backup()
                self.stdout.write(
                    self.style.SUCCESS(f'Backup created successfully: {backup_name}')
                )
            
            # Cleanup old backups if requested
            if options['cleanup']:
                self.stdout.write(f'Cleaning up backups older than {options["days"]} days...')
                backup_service.cleanup_old_backups(options['days'])
                self.stdout.write(
                    self.style.SUCCESS('Old backups cleanup completed')
                )
            
            # Show backup status
            self.stdout.write('\nBackup Status:')
            backups = backup_service.get_backup_status()
            
            if backups:
                for backup in backups[:5]:  # Show last 5 backups
                    self.stdout.write(f'  - {backup["backup_name"]} ({backup["created_at"]})')
            else:
                self.stdout.write('  No backups found')
            
        except Exception as e:
            raise CommandError(f'Backup failed: {e}')
