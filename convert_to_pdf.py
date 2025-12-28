#!/usr/bin/env python3
"""
Convert Security Documentation Markdown Files to PDF
Uses markdown and weasyprint for PDF generation
"""

import os
import sys
from pathlib import Path

try:
    import markdown
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
except ImportError:
    print("❌ Required packages not installed")
    print("Install with: pip install markdown weasyprint")
    sys.exit(1)

# Colors for output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'  # No Color

def create_css():
    """Create CSS for PDF styling"""
    return """
    @page {
        size: A4;
        margin: 1in;
    }
    body {
        font-family: 'Helvetica', 'Arial', sans-serif;
        font-size: 11pt;
        line-height: 1.6;
        color: #333;
    }
    h1 {
        font-size: 24pt;
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 10px;
        margin-top: 30px;
    }
    h2 {
        font-size: 18pt;
        color: #34495e;
        margin-top: 25px;
        border-bottom: 1px solid #ecf0f1;
        padding-bottom: 5px;
    }
    h3 {
        font-size: 14pt;
        color: #7f8c8d;
        margin-top: 20px;
    }
    code {
        background-color: #f4f4f4;
        padding: 2px 6px;
        border-radius: 3px;
        font-family: 'Courier New', monospace;
        font-size: 10pt;
    }
    pre {
        background-color: #f4f4f4;
        padding: 15px;
        border-radius: 5px;
        overflow-x: auto;
        border-left: 4px solid #3498db;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
    }
    th, td {
        border: 1px solid #ddd;
        padding: 12px;
        text-align: left;
    }
    th {
        background-color: #3498db;
        color: white;
        font-weight: bold;
    }
    tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    blockquote {
        border-left: 4px solid #3498db;
        margin: 20px 0;
        padding-left: 20px;
        color: #7f8c8d;
        font-style: italic;
    }
    ul, ol {
        margin: 15px 0;
        padding-left: 30px;
    }
    li {
        margin: 5px 0;
    }
    hr {
        border: none;
        border-top: 2px solid #ecf0f1;
        margin: 30px 0;
    }
    """

def convert_markdown_to_pdf(md_file, output_dir):
    """Convert a markdown file to PDF"""
    try:
        # Read markdown file
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Convert markdown to HTML
        md = markdown.Markdown(extensions=['tables', 'fenced_code', 'toc'])
        html_content = md.convert(md_content)
        
        # Add CSS styling
        css = create_css()
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>{css}</style>
        </head>
        <body>
        {html_content}
        </body>
        </html>
        """
        
        # Generate PDF
        base_name = Path(md_file).stem
        pdf_path = os.path.join(output_dir, f"{base_name}.pdf")
        
        HTML(string=full_html).write_pdf(pdf_path)
        
        return pdf_path, None
        
    except Exception as e:
        return None, str(e)

def main():
    """Main conversion function"""
    print(f"{GREEN}📄 Converting Security Documentation to PDF{NC}")
    print("=" * 60)
    
    # Create output directory
    output_dir = "security_docs_pdf"
    os.makedirs(output_dir, exist_ok=True)
    
    # List of markdown files to convert
    files = [
        "VULNERABILITY_PATCH_PROGRAM.md",
        "INCIDENT_RESPONSE_PLAN.md",
        "DATA_FLOW_DIAGRAM.md",
        "KEY_ROTATION_RUNBOOK.md",
        "WAF_CONFIGURATION.md",
        "CSRF_VERIFICATION_CHECKLIST.md",
        "RAW_SQL_AUDIT.md",
        "SECURITY_FIXES_SUMMARY.md",
        "PRODUCTION_SECURITY_PLAN.md",
    ]
    
    converted = 0
    failed = 0
    
    for file in files:
        if os.path.exists(file):
            print(f"{YELLOW}Converting: {file}{NC}")
            pdf_path, error = convert_markdown_to_pdf(file, output_dir)
            
            if pdf_path:
                print(f"{GREEN}✅ Created: {pdf_path}{NC}")
                converted += 1
            else:
                print(f"{RED}❌ Failed: {error}{NC}")
                failed += 1
        else:
            print(f"{RED}⚠️  File not found: {file}{NC}")
            failed += 1
    
    print("")
    print(f"{GREEN}✅ Conversion complete!{NC}")
    print(f"   Converted: {converted}")
    print(f"   Failed: {failed}")
    print(f"   PDFs saved in: {output_dir}/")
    print("")
    print("📋 Next steps:")
    print("   1. Review PDFs for formatting")
    print("   2. Add Dependabot screenshot to VULNERABILITY_PATCH_PROGRAM.pdf")
    print("   3. Add tabletop exercise notes to INCIDENT_RESPONSE_PLAN.pdf")
    print("   4. Create visual data flow diagram")

if __name__ == "__main__":
    main()

