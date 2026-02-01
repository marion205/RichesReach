"""
Optimize Database Queries
Add indexes and optimize queries with select_related/prefetch_related.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command
import os


class Command(BaseCommand):
    help = 'Optimize database queries by adding indexes and checking query patterns'

    def add_arguments(self, parser):
        parser.add_argument(
            '--add-indexes',
            action='store_true',
            help='Create database indexes for common query patterns'
        )
        parser.add_argument(
            '--check-queries',
            action='store_true',
            help='Check for N+1 query patterns'
        )
        parser.add_argument(
            '--analyze',
            action='store_true',
            help='Analyze query performance'
        )

    def handle(self, *args, **options):
        self.stdout.write("🔍 Database Query Optimization")
        self.stdout.write("=" * 60)
        
        if options['add_indexes']:
            self._add_indexes()
        
        if options['check_queries']:
            self._check_queries()
        
        if options['analyze']:
            self._analyze_performance()
        
        if not any([options['add_indexes'], options['check_queries'], options['analyze']]):
            self.stdout.write("\n💡 Usage:")
            self.stdout.write("   --add-indexes: Create database indexes")
            self.stdout.write("   --check-queries: Check for N+1 patterns")
            self.stdout.write("   --analyze: Analyze query performance")
            self.stdout.write("\n   Example: python manage.py optimize_database_queries --add-indexes --check-queries")

    def _add_indexes(self):
        """Add database indexes for common query patterns"""
        self.stdout.write("\n📊 Adding Database Indexes...")
        
        # Note: Indexes should be added via migrations, but we can check existing ones
        with connection.cursor() as cursor:
            # Check existing indexes
            cursor.execute("""
                SELECT 
                    tablename, 
                    indexname, 
                    indexdef 
                FROM pg_indexes 
                WHERE schemaname = 'public' 
                AND tablename IN ('core_portfolio', 'core_watchlist', 'core_post', 'core_chatmessage', 'transparency_signals')
                ORDER BY tablename, indexname;
            """)
            
            indexes = cursor.fetchall()
            
            if indexes:
                self.stdout.write("\n✅ Existing Indexes:")
                for table, index, definition in indexes:
                    self.stdout.write(f"   {table}.{index}")
            else:
                self.stdout.write("\n⚠️  No indexes found (may need to run migrations)")
        
        self.stdout.write("\n💡 To add indexes, create a migration:")
        self.stdout.write("   python manage.py makemigrations --name add_performance_indexes")
        self.stdout.write("   python manage.py migrate")

    def _check_queries(self):
        """Check for N+1 query patterns"""
        self.stdout.write("\n🔍 Checking for N+1 Query Patterns...")
        
        # Common patterns to check
        patterns = [
            ("Portfolio queries", "Portfolio.objects.filter().select_related('stock', 'user')"),
            ("Watchlist queries", "Watchlist.objects.filter().select_related('stock', 'user')"),
            ("Post queries", "Post.objects.filter().select_related('user').prefetch_related('likes', 'comments')"),
            ("ChatMessage queries", "ChatMessage.objects.filter().select_related('session', 'session__user')"),
            ("SignalRecord queries", "SignalRecord.objects.filter().order_by('-entry_timestamp')"),
        ]
        
        self.stdout.write("\n✅ Recommended Query Patterns:")
        for name, pattern in patterns:
            self.stdout.write(f"   {name}:")
            self.stdout.write(f"      {pattern}")
        
        self.stdout.write("\n💡 Use Django Debug Toolbar or django-silk to identify N+1 queries in production")

    def _analyze_performance(self):
        """Analyze query performance"""
        self.stdout.write("\n📈 Analyzing Query Performance...")
        
        with connection.cursor() as cursor:
            # Get slow queries (if pg_stat_statements is available)
            try:
                cursor.execute("""
                    SELECT 
                        query,
                        calls,
                        total_exec_time,
                        mean_exec_time,
                        max_exec_time
                    FROM pg_stat_statements 
                    WHERE mean_exec_time > 100
                    ORDER BY mean_exec_time DESC
                    LIMIT 10;
                """)
                
                slow_queries = cursor.fetchall()
                
                if slow_queries:
                    self.stdout.write("\n⚠️  Slow Queries (>100ms average):")
                    for query, calls, total, mean, max_time in slow_queries:
                        self.stdout.write(f"   Calls: {calls}, Avg: {mean:.2f}ms, Max: {max_time:.2f}ms")
                        self.stdout.write(f"   {query[:100]}...")
                else:
                    self.stdout.write("\n✅ No slow queries found (or pg_stat_statements not enabled)")
            except Exception as e:
                self.stdout.write(f"\n⚠️  Could not analyze queries: {e}")
                self.stdout.write("   (pg_stat_statements extension may not be enabled)")
        
        self.stdout.write("\n" + "=" * 60)

