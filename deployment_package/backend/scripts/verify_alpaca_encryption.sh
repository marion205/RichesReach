#!/usr/bin/env bash
# Verify Alpaca token encryption is configured (key set, optional row check).
# Run from deployment_package/backend. Safe for staging/production (no secrets printed).
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$BACKEND_DIR"

echo "=== Alpaca token encryption verification ==="
python manage.py shell << 'PY'
from django.conf import settings
from core.models import AlpacaConnection

key_set = bool(
    getattr(settings, 'ALPACA_TOKEN_ENCRYPTION_KEY', None)
    or getattr(settings, 'FERNET_KEY', None)
)
print('Key set (ALPACA_TOKEN_ENCRYPTION_KEY or FERNET_KEY):', key_set)

try:
    count = AlpacaConnection.objects.count()
    print('AlpacaConnection rows:', count)
    if count:
        conn = AlpacaConnection.objects.first()
        at = (conn.access_token or '')[:12]
        print('Sample token prefix (eyJ = likely plaintext JWT):', (at[:10] + '..') if len(at) >= 10 else at)
except Exception as e:
    print('Error:', e)
PY
