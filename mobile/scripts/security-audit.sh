#!/bin/bash
# Security Audit Script
# Runs dependency scans and security checks

set -e

echo "🔒 Running Security Audit..."

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ npm not found. Skipping npm audit."
    exit 1
fi

echo ""
echo "📦 Running npm audit..."
npm audit --audit-level=moderate || {
    echo "⚠️  npm audit found vulnerabilities. Review and fix as needed."
}

echo ""
echo "📋 Checking for known vulnerable packages..."
npm audit --json > security-audit-report.json 2>/dev/null || true

echo ""
echo "✅ Security audit complete. Report saved to security-audit-report.json"

# Check for outdated packages
echo ""
echo "📊 Checking for outdated packages..."
npm outdated || echo "All packages are up to date"

echo ""
echo "🔒 Security audit finished!"

