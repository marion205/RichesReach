#!/bin/bash
# Run comprehensive banking tests

set -e

echo "🧪 Running Banking Integration Tests"
echo "===================================="
echo ""

cd "$(dirname "$0")"
source venv/bin/activate

# Run tests with coverage
echo "📊 Running tests with coverage..."
python -m pytest core/tests/test_banking*.py \
    --cov=core.banking_views \
    --cov=core.yodlee_client \
    --cov=core.yodlee_client_enhanced \
    --cov=core.banking_models \
    --cov=core.banking_encryption \
    --cov=core.banking_queries \
    --cov=core.banking_mutations \
    --cov=core.banking_tasks \
    --cov-report=html \
    --cov-report=term-missing \
    -v

# Also run Django tests
echo ""
echo "📊 Running Django tests..."
python manage.py test core.tests --verbosity=2

echo ""
echo "✅ All tests complete!"

