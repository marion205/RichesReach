#!/bin/bash
# Documentation Consolidation Script
# Organizes markdown files into a structured docs directory

set -e

DOCS_DIR="docs"
ARCHIVE_DIR="$DOCS_DIR/archive"

echo "📚 Consolidating documentation..."

# Create directory structure
mkdir -p "$DOCS_DIR"/{guides,api,deployment,testing,features,week-summaries}
mkdir -p "$ARCHIVE_DIR"/{old,duplicates}

# Move week summaries
echo "📅 Organizing week summaries..."
mv -f WEEK*.md "$DOCS_DIR/week-summaries/" 2>/dev/null || true
mv -f *WEEK*.md "$DOCS_DIR/week-summaries/" 2>/dev/null || true

# Move Alpaca Connect docs
echo "🔐 Organizing Alpaca Connect docs..."
mkdir -p "$DOCS_DIR/features/alpaca-connect"
mv -f ALPACA_CONNECT*.md "$DOCS_DIR/features/alpaca-connect/" 2>/dev/null || true

# Move trading screen docs
echo "📊 Organizing trading screen docs..."
mkdir -p "$DOCS_DIR/features/trading"
mv -f TRADING_SCREEN*.md "$DOCS_DIR/features/trading/" 2>/dev/null || true

# Move deployment docs
echo "🚀 Organizing deployment docs..."
mv -f DEPLOYMENT*.md "$DOCS_DIR/deployment/" 2>/dev/null || true
mv -f PRODUCTION*.md "$DOCS_DIR/deployment/" 2>/dev/null || true
mv -f START*.md "$DOCS_DIR/deployment/" 2>/dev/null || true

# Move testing docs
echo "🧪 Organizing testing docs..."
mv -f TEST*.md "$DOCS_DIR/testing/" 2>/dev/null || true
mv -f *TEST*.md "$DOCS_DIR/testing/" 2>/dev/null || true

# Move API docs
echo "🔌 Organizing API docs..."
mv -f API*.md "$DOCS_DIR/api/" 2>/dev/null || true

# Move feature docs
echo "✨ Organizing feature docs..."
mkdir -p "$DOCS_DIR/features"/{day-trading,credit,voice,family,portfolio}
mv -f DAY_TRADING*.md "$DOCS_DIR/features/day-trading/" 2>/dev/null || true
mv -f CREDIT*.md "$DOCS_DIR/features/credit/" 2>/dev/null || true
mv -f VOICE*.md "$DOCS_DIR/features/voice/" 2>/dev/null || true
mv -f FAMILY*.md "$DOCS_DIR/features/family/" 2>/dev/null || true
mv -f PORTFOLIO*.md "$DOCS_DIR/features/portfolio/" 2>/dev/null || true

# Move guides
echo "📖 Organizing guides..."
mv -f *GUIDE*.md "$DOCS_DIR/guides/" 2>/dev/null || true
mv -f HOW_TO*.md "$DOCS_DIR/guides/" 2>/dev/null || true
mv -f QUICK*.md "$DOCS_DIR/guides/" 2>/dev/null || true

# Create main README
cat > "$DOCS_DIR/README.md" << 'EOF'
# RichesReach Documentation

This directory contains all project documentation organized by category.

## Structure

- **guides/** - How-to guides and quick start documentation
- **api/** - API documentation and endpoint references
- **deployment/** - Deployment guides and production setup
- **testing/** - Test plans, results, and checklists
- **features/** - Feature-specific documentation
  - **alpaca-connect/** - Alpaca OAuth Connect implementation
  - **trading/** - Trading screen and order management
  - **day-trading/** - Day trading features
  - **credit/** - Credit building features
  - **voice/** - Voice AI features
  - **family/** - Family sharing features
  - **portfolio/** - Portfolio management
- **week-summaries/** - Weekly progress summaries
- **archive/** - Archived and duplicate documentation

## Quick Links

- [Week 1 Summary](week-summaries/WEEK1_COMPLETE.md)
- [Week 2 Summary](week-summaries/WEEK2_COMPLETE.md)
- [Week 3 Summary](week-summaries/WEEK3_COMPLETE_SUMMARY.md)
- [Alpaca Connect Guide](features/alpaca-connect/ALPACA_CONNECT_OAUTH_GUIDE.md)
- [Trading Screen Refactor](features/trading/TRADING_SCREEN_REFACTOR_COMPLETE.md)
- [Deployment Guide](deployment/DEPLOYMENT_GUIDE.md)

## Contributing

When adding new documentation:
1. Place it in the appropriate category directory
2. Update this README with a link if it's important
3. Use descriptive filenames
EOF

echo "✅ Documentation consolidated!"
echo "📁 Documentation structure created in $DOCS_DIR"
echo "📝 Main README created at $DOCS_DIR/README.md"

