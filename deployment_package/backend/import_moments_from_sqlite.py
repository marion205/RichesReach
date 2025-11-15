#!/usr/bin/env python3
"""
Import StockMoment data from SQLite to PostgreSQL
"""
import os
import sys
import django
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Setup Django with SQLite first
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
# Force SQLite by explicitly setting it
os.environ['DB_NAME'] = ''
os.environ['DB_USER'] = ''
os.environ['DB_HOST'] = ''
os.environ.pop('DATABASE_URL', None)
# Also need to modify settings to use SQLite
import richesreach.settings as settings_module
settings_module.DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': backend_dir / 'db.sqlite3',
    }
}

django.setup()

from core.models import StockMoment
from django.db import connection

print(f"📖 Reading from SQLite: {connection.settings_dict['NAME']}")
print(f"   Total moments: {StockMoment.objects.count()}")

# Get all moments
moments = list(StockMoment.objects.all())
print(f"   Found {len(moments)} moments to import")

# Close SQLite connection
connection.close()

# Now switch to PostgreSQL
print("\n📝 Switching to PostgreSQL...")
os.environ['DB_NAME'] = 'richesreach_local'
os.environ['DB_USER'] = 'marioncollins'
os.environ['DB_HOST'] = 'localhost'
os.environ.pop('DATABASE_URL', None)

# Clear Django's connection cache
from django.db import connections
connections.close_all()

# Force PostgreSQL settings
settings_module.DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'richesreach_local',
        'USER': 'marioncollins',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Re-setup Django
django.setup()

from core.models import StockMoment as PGMoment
from django.db import connection as pg_connection

print(f"📝 Writing to PostgreSQL: {pg_connection.settings_dict['NAME']}")
print(f"   Current count: {PGMoment.objects.count()}")

# Import moments
imported = 0
errors = 0

for moment in moments:
    try:
        # Check if already exists
        if PGMoment.objects.filter(id=moment.id).exists():
            print(f"   ⚠️  Skipping {moment.id} (already exists)")
            continue
            
        PGMoment.objects.create(
            id=moment.id,
            symbol=moment.symbol,
            timestamp=moment.timestamp,
            category=moment.category,
            title=moment.title,
            quick_summary=moment.quick_summary,
            deep_summary=moment.deep_summary,
            importance_score=moment.importance_score,
            impact_1d=moment.impact_1d,
            impact_7d=moment.impact_7d,
            source_links=moment.source_links or [],
            created_at=moment.created_at,
            updated_at=moment.updated_at,
        )
        imported += 1
        if imported % 5 == 0:
            print(f"   ✅ Imported {imported}/{len(moments)}...")
    except Exception as e:
        errors += 1
        print(f"   ❌ Error importing {moment.id}: {e}")

print(f"\n✅ Import complete!")
print(f"   Imported: {imported}")
print(f"   Errors: {errors}")
print(f"   Total in PostgreSQL: {PGMoment.objects.count()}")

# Show breakdown by symbol
print(f"\n📊 Breakdown by symbol:")
for symbol in ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'NVDA']:
    count = PGMoment.objects.filter(symbol=symbol).count()
    print(f"   {symbol}: {count}")

