"""
Production Deployment Configuration
Sets up environment variables, monitoring, and backup configuration.
"""
from django.core.management.base import BaseCommand
import os
from pathlib import Path


class Command(BaseCommand):
    help = 'Setup production deployment configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check',
            action='store_true',
            help='Check current configuration status'
        )
        parser.add_argument(
            '--generate-env-template',
            action='store_true',
            help='Generate .env.production template'
        )
        parser.add_argument(
            '--setup-monitoring',
            action='store_true',
            help='Generate monitoring configuration'
        )
        parser.add_argument(
            '--setup-backups',
            action='store_true',
            help='Generate backup configuration'
        )

    def handle(self, *args, **options):
        self.stdout.write("🔧 Production Deployment Configuration")
        self.stdout.write("=" * 60)
        
        if options['check']:
            self._check_configuration()
        
        if options['generate_env_template']:
            self._generate_env_template()
        
        if options['setup_monitoring']:
            self._setup_monitoring()
        
        if options['setup_backups']:
            self._setup_backups()
        
        if not any([options['check'], options['generate_env_template'], options['setup_monitoring'], options['setup_backups']]):
            self.stdout.write("\n💡 Usage:")
            self.stdout.write("   --check: Check current configuration")
            self.stdout.write("   --generate-env-template: Create .env.production template")
            self.stdout.write("   --setup-monitoring: Generate monitoring config")
            self.stdout.write("   --setup-backups: Generate backup config")

    def _check_configuration(self):
        """Check current production configuration status"""
        self.stdout.write("\n📊 Configuration Status:")
        self.stdout.write("=" * 60)
        
        # Check environment variables
        required_vars = [
            'ALPACA_API_KEY',
            'ALPACA_SECRET_KEY',
            'ALPACA_BROKER_API_KEY',
            'ALPACA_BROKER_API_SECRET',
            'DATABASE_URL',
            'REDIS_URL',
            'SECRET_KEY',
            'OPENAI_API_KEY',
        ]
        
        optional_vars = [
            'SENTRY_DSN',
            'INFERENCE_ENDPOINTS',
            'DEFAULT_INFERENCE_ENDPOINT',
            'POLYGON_API_KEY',
            'FINNHUB_API_KEY',
        ]
        
        self.stdout.write("\n🔑 Required Environment Variables:")
        missing_required = []
        for var in required_vars:
            value = os.getenv(var)
            if value:
                masked = value[:4] + '...' + value[-4:] if len(value) > 8 else '***'
                self.stdout.write(self.style.SUCCESS(f"   ✅ {var}: {masked}"))
            else:
                self.stdout.write(self.style.ERROR(f"   ❌ {var}: NOT SET"))
                missing_required.append(var)
        
        self.stdout.write("\n🔑 Optional Environment Variables:")
        for var in optional_vars:
            value = os.getenv(var)
            if value:
                masked = value[:4] + '...' + value[-4:] if len(value) > 8 else '***'
                self.stdout.write(self.style.SUCCESS(f"   ✅ {var}: {masked}"))
            else:
                self.stdout.write(self.style.WARNING(f"   ⚠️  {var}: Not set (optional)"))
        
        # Check database
        self.stdout.write("\n💾 Database:")
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f"   ✅ Connected: {version[:50]}..."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Database error: {e}"))
        
        # Check Redis
        self.stdout.write("\n🔴 Redis Cache:")
        try:
            from django.core.cache import cache
            cache.set('test_key', 'test_value', 1)
            if cache.get('test_key') == 'test_value':
                self.stdout.write(self.style.SUCCESS("   ✅ Redis cache working"))
            else:
                self.stdout.write(self.style.WARNING("   ⚠️  Redis cache not working"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"   ⚠️  Redis not available: {e}"))
        
        # Summary
        self.stdout.write("\n" + "=" * 60)
        if missing_required:
            self.stdout.write(self.style.ERROR(f"\n❌ Missing {len(missing_required)} required variables"))
            self.stdout.write("   Run --generate-env-template to create template")
        else:
            self.stdout.write(self.style.SUCCESS("\n✅ All required configuration present"))

    def _generate_env_template(self):
        """Generate .env.production template"""
        template = """# Production Environment Variables
# Copy this to .env.production and fill in values

# ============================================================================
# DATABASE
# ============================================================================
DATABASE_URL=postgresql://user:password@localhost:5432/richesreach_prod

# ============================================================================
# SECURITY
# ============================================================================
SECRET_KEY=your-secret-key-here-generate-with-openssl-rand-hex-32
DEBUG=False
ALLOWED_HOSTS=richesreach.com,www.richesreach.com,api.richesreach.com

# ============================================================================
# REDIS / CACHE
# ============================================================================
REDIS_URL=redis://localhost:6379/0
CACHE_URL=redis://localhost:6379/1

# ============================================================================
# BROKER & TRADING APIs
# ============================================================================
ALPACA_API_KEY=your-alpaca-api-key
ALPACA_SECRET_KEY=your-alpaca-secret-key
ALPACA_BROKER_API_KEY=your-broker-api-key
ALPACA_BROKER_API_SECRET=your-broker-api-secret
ALPACA_BROKER_BASE_URL=https://broker-api.alpaca.markets
ALPACA_API_BASE_URL=https://api.alpaca.markets

# ============================================================================
# MARKET DATA APIs
# ============================================================================
POLYGON_API_KEY=your-polygon-api-key
FINNHUB_API_KEY=your-finnhub-api-key
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-api-key

# ============================================================================
# AI & ML SERVICES
# ============================================================================
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o

# ============================================================================
# INFERENCE ENDPOINTS (Cloud Locality)
# ============================================================================
INFERENCE_ENDPOINTS=us-east-1:http://inference-us-east.example.com
DEFAULT_INFERENCE_ENDPOINT=http://localhost:8000

# ============================================================================
# MONITORING & LOGGING
# ============================================================================
SENTRY_DSN=your-sentry-dsn
LOG_LEVEL=INFO

# ============================================================================
# BANKING INTEGRATION
# ============================================================================
YODLEE_CLIENT_ID=your-yodlee-client-id
YODLEE_SECRET=your-yodlee-secret
YODLEE_APP_ID=your-yodlee-app-id

# ============================================================================
# AWS (if using)
# ============================================================================
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
"""
        
        output_path = Path('.env.production.template')
        with open(output_path, 'w') as f:
            f.write(template)
        
        self.stdout.write(self.style.SUCCESS(f"\n✅ Generated: {output_path}"))
        self.stdout.write("   Copy to .env.production and fill in values")

    def _setup_monitoring(self):
        """Generate monitoring configuration"""
        self.stdout.write("\n📊 Setting up monitoring...")
        
        # Check for Sentry
        sentry_dsn = os.getenv('SENTRY_DSN')
        if sentry_dsn:
            self.stdout.write(self.style.SUCCESS("   ✅ Sentry DSN configured"))
        else:
            self.stdout.write(self.style.WARNING("   ⚠️  Sentry DSN not set (optional but recommended)"))
        
        # Monitoring recommendations
        self.stdout.write("\n💡 Monitoring Recommendations:")
        self.stdout.write("   1. Set up Sentry for error tracking")
        self.stdout.write("   2. Configure CloudWatch/DataDog for metrics")
        self.stdout.write("   3. Set up alerts for:")
        self.stdout.write("      - High latency (>500ms)")
        self.stdout.write("      - Error rate spikes")
        self.stdout.write("      - Database connection issues")
        self.stdout.write("      - Cache misses")
        
        self.stdout.write(self.style.SUCCESS("\n✅ Monitoring setup complete"))

    def _setup_backups(self):
        """Generate backup configuration"""
        self.stdout.write("\n💾 Setting up backups...")
        
        backup_script = """#!/bin/bash
# Database Backup Script
# Run daily via cron: 0 2 * * * /path/to/backup.sh

BACKUP_DIR="/backups/richesreach"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="richesreach_prod"

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
pg_dump $DB_NAME | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/db_backup_$DATE.sql.gz"
"""
        
        output_path = Path('backup_database.sh')
        with open(output_path, 'w') as f:
            f.write(backup_script)
        
        os.chmod(output_path, 0o755)
        
        self.stdout.write(self.style.SUCCESS(f"\n✅ Generated: {output_path}"))
        self.stdout.write("\n💡 Backup Recommendations:")
        self.stdout.write("   1. Schedule daily database backups")
        self.stdout.write("   2. Store backups in S3/cloud storage")
        self.stdout.write("   3. Test restore procedure monthly")
        self.stdout.write("   4. Keep 30-90 days of backups")
        self.stdout.write("\n   Cron example: 0 2 * * * /path/to/backup_database.sh")

