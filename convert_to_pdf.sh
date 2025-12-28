#!/bin/bash
# Convert Security Documentation Markdown Files to PDF
# Requires: pandoc (install via: brew install pandoc basictex)

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}📄 Converting Security Documentation to PDF${NC}"
echo "============================================================"

# Check if pandoc is installed
if ! command -v pandoc &> /dev/null; then
    echo -e "${RED}❌ pandoc is not installed${NC}"
    echo "Install with: brew install pandoc basictex"
    echo "Or use online converter: https://www.markdowntopdf.com/"
    exit 1
fi

# Create output directory
OUTPUT_DIR="security_docs_pdf"
mkdir -p "$OUTPUT_DIR"

# List of markdown files to convert
FILES=(
    "VULNERABILITY_PATCH_PROGRAM.md"
    "INCIDENT_RESPONSE_PLAN.md"
    "DATA_FLOW_DIAGRAM.md"
    "KEY_ROTATION_RUNBOOK.md"
    "WAF_CONFIGURATION.md"
    "CSRF_VERIFICATION_CHECKLIST.md"
    "RAW_SQL_AUDIT.md"
    "SECURITY_FIXES_SUMMARY.md"
    "PRODUCTION_SECURITY_PLAN.md"
)

# Convert each file
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${YELLOW}Converting: $file${NC}"
        
        # Get base filename without extension
        base_name=$(basename "$file" .md)
        
        # Convert to PDF with better formatting
        pandoc "$file" \
            -o "$OUTPUT_DIR/${base_name}.pdf" \
            --pdf-engine=pdflatex \
            -V geometry:margin=1in \
            -V fontsize=11pt \
            -V documentclass=article \
            --toc \
            --toc-depth=2 \
            -V colorlinks=true \
            -V linkcolor=blue \
            -V urlcolor=blue \
            -V toccolor=gray \
            2>/dev/null || {
                echo -e "${RED}⚠️  Failed to convert $file (may need LaTeX)${NC}"
                echo "   Trying without LaTeX..."
                # Fallback: convert to HTML first, then use browser print
                pandoc "$file" -o "$OUTPUT_DIR/${base_name}.html" --standalone --css=github-markdown.css 2>/dev/null || {
                    echo -e "${RED}❌ Failed to convert $file${NC}"
                }
            }
        
        if [ -f "$OUTPUT_DIR/${base_name}.pdf" ]; then
            echo -e "${GREEN}✅ Created: $OUTPUT_DIR/${base_name}.pdf${NC}"
        elif [ -f "$OUTPUT_DIR/${base_name}.html" ]; then
            echo -e "${YELLOW}⚠️  Created HTML (convert to PDF manually): $OUTPUT_DIR/${base_name}.html${NC}"
            echo "   Open in browser and use Print > Save as PDF"
        fi
    else
        echo -e "${RED}⚠️  File not found: $file${NC}"
    fi
done

echo ""
echo -e "${GREEN}✅ Conversion complete!${NC}"
echo "PDFs saved in: $OUTPUT_DIR/"
echo ""
echo "📋 Next steps:"
echo "   1. Review PDFs for formatting"
echo "   2. Add Dependabot screenshot to VULNERABILITY_PATCH_PROGRAM.pdf"
echo "   3. Add tabletop exercise notes to INCIDENT_RESPONSE_PLAN.pdf"
echo "   4. Create visual data flow diagram"

