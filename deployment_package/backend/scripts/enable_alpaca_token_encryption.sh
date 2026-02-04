#!/usr/bin/env bash
# Do-all: Alpaca token encryption quick win.
# Run from deployment_package/backend (or set DJANGO_SETTINGS_MODULE and PYTHONPATH).
# Usage:
#   ./scripts/enable_alpaca_token_encryption.sh              # generate key + dry-run + rotate if needed
#   ./scripts/enable_alpaca_token_encryption.sh --key-only   # only generate and print key
#   ./scripts/enable_alpaca_token_encryption.sh --rotate-only   # only dry-run then rotate (key must be set)

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$BACKEND_DIR"

KEY_ONLY=false
ROTATE_ONLY=false
for arg in "$@"; do
  case "$arg" in
    --key-only)     KEY_ONLY=true ;;
    --rotate-only)  ROTATE_ONLY=true ;;
  esac
done

if [ "$KEY_ONLY" = true ]; then
  echo "=== 1. Generate Fernet key (set this in production) ==="
  python manage.py generate_alpaca_encryption_key
  echo ""
  echo "Add the line above to ECS secrets, K8s Secret, or .env.production, then deploy and run:"
  echo "  $0 --rotate-only"
  exit 0
fi

if [ "$ROTATE_ONLY" != true ]; then
  echo "=== 1. Generate Fernet key (if not already set in production) ==="
  python manage.py generate_alpaca_encryption_key
  echo ""
  echo "If you haven't yet: add ALPACA_TOKEN_ENCRYPTION_KEY to production, deploy, then run:"
  echo "  $0 --rotate-only"
  echo ""
fi

echo "=== 2. Dry-run: see how many AlpacaConnection rows would be re-encrypted ==="
DRY_OUTPUT="$(python manage.py rotate_alpaca_token_encryption --dry-run 2>&1)" || true
echo "$DRY_OUTPUT"

if echo "$DRY_OUTPUT" | grep -q "ALPACA_TOKEN_ENCRYPTION_KEY.*not set"; then
  echo ""
  echo "Key not set in this environment. Set ALPACA_TOKEN_ENCRYPTION_KEY and run again (e.g. $0 --rotate-only)."
  exit 0
fi

if echo "$DRY_OUTPUT" | grep -q "Would re-encrypt [1-9]"; then
  echo ""
  echo "=== 3. Re-encrypt existing plaintext tokens ==="
  python manage.py rotate_alpaca_token_encryption
  echo "Done."
else
  echo ""
  echo "No plaintext rows to re-encrypt (or key not set). Done."
fi
