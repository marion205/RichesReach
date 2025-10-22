#!/usr/bin/env python3
"""
Generate comprehensive test coverage reports for RichesReach AI platform.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any
import argparse
from datetime import datetime

class CoverageReportGenerator:
    """Generate comprehensive test coverage reports."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.report_data = {
            "timestamp": datetime.now().isoformat(),
            "backend": {"coverage": 0, "files": []},
            "mobile": {"coverage": 0, "files": []},
            "overall": {"coverage": 0, "files_covered": 0, "total_files": 0}
        }
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def run_command(self, command: List[str], cwd: str = None) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        if self.verbose:
            self.log(f"Running: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=60
            )
            return result
        except subprocess.TimeoutExpired:
            self.log(f"Command timed out: {' '.join(command)}", "ERROR")
            return subprocess.CompletedProcess(command, 1, "", "Timeout")
        except Exception as e:
            self.log(f"Error running command: {e}", "ERROR")
            return subprocess.CompletedProcess(command, 1, "", str(e))
    
    def generate_backend_coverage(self) -> Dict[str, Any]:
        """Generate backend test coverage report."""
        self.log("Generating backend coverage report...")
        
        # Run pytest with coverage
        cmd = [
            sys.executable, "-m", "pytest",
            "--cov=backend",
            "--cov-report=json",
            "--cov-report=html",
            "--cov-report=term",
            "tests/"
        ]
        
        result = self.run_command(cmd)
        
        if result.returncode != 0:
            self.log(f"Backend coverage generation failed: {result.stderr}", "ERROR")
            return {"coverage": 0, "files": []}
        
        # Parse coverage.json if it exists
        coverage_data = {"coverage": 0, "files": []}
        
        if os.path.exists("coverage.json"):
            with open("coverage.json", "r") as f:
                data = json.load(f)
                coverage_data["coverage"] = data.get("totals", {}).get("percent_covered", 0)
                
                # Get file coverage details
                for filename, file_data in data.get("files", {}).items():
                    if filename.startswith("backend/"):
                        coverage_data["files"].append({
                            "file": filename,
                            "coverage": file_data.get("summary", {}).get("percent_covered", 0),
                            "lines_covered": file_data.get("summary", {}).get("covered_lines", 0),
                            "total_lines": file_data.get("summary", {}).get("num_statements", 0)
                        })
        
        return coverage_data
    
    def generate_mobile_coverage(self) -> Dict[str, Any]:
        """Generate mobile test coverage report."""
        self.log("Generating mobile coverage report...")
        
        if not os.path.exists("mobile"):
            self.log("Mobile directory not found, skipping mobile coverage")
            return {"coverage": 0, "files": []}
        
        # Change to mobile directory
        os.chdir("mobile")
        
        try:
            # Run Jest with coverage
            cmd = ["npm", "test", "--", "--coverage", "--watchAll=false"]
            result = self.run_command(cmd)
            
            coverage_data = {"coverage": 0, "files": []}
            
            if result.returncode == 0:
                # Parse Jest coverage report
                if os.path.exists("coverage/coverage-summary.json"):
                    with open("coverage/coverage-summary.json", "r") as f:
                        data = json.load(f)
                        coverage_data["coverage"] = data.get("total", {}).get("lines", {}).get("pct", 0)
                        
                        # Get file coverage details
                        for filename, file_data in data.items():
                            if filename != "total" and filename.endswith((".ts", ".tsx", ".js", ".jsx")):
                                coverage_data["files"].append({
                                    "file": filename,
                                    "coverage": file_data.get("lines", {}).get("pct", 0),
                                    "lines_covered": file_data.get("lines", {}).get("covered", 0),
                                    "total_lines": file_data.get("lines", {}).get("total", 0)
                                })
            
            return coverage_data
        
        finally:
            # Change back to root directory
            os.chdir("..")
    
    def analyze_test_coverage(self) -> Dict[str, Any]:
        """Analyze overall test coverage."""
        self.log("Analyzing test coverage...")
        
        # Count total files
        backend_files = []
        mobile_files = []
        
        # Count backend files
        for root, dirs, files in os.walk("backend"):
            for file in files:
                if file.endswith((".py",)):
                    backend_files.append(os.path.join(root, file))
        
        # Count mobile files
        if os.path.exists("mobile/src"):
            for root, dirs, files in os.walk("mobile/src"):
                for file in files:
                    if file.endswith((".ts", ".tsx", ".js", ".jsx")):
                        mobile_files.append(os.path.join(root, file))
        
        total_files = len(backend_files) + len(mobile_files)
        covered_files = len(self.report_data["backend"]["files"]) + len(self.report_data["mobile"]["files"])
        
        overall_coverage = 0
        if total_files > 0:
            overall_coverage = (covered_files / total_files) * 100
        
        return {
            "coverage": overall_coverage,
            "files_covered": covered_files,
            "total_files": total_files,
            "backend_files": len(backend_files),
            "mobile_files": len(mobile_files)
        }
    
    def generate_html_report(self) -> str:
        """Generate HTML coverage report."""
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RichesReach AI - Test Coverage Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 30px;
        }}
        .summary-card {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            border-left: 4px solid #667eea;
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #333;
        }}
        .summary-card .number {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .coverage-bar {{
            width: 100%;
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .coverage-fill {{
            height: 100%;
            background: linear-gradient(90deg, #28a745, #20c997);
            transition: width 0.3s ease;
        }}
        .details {{
            padding: 30px;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section h2 {{
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        .file-list {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
        }}
        .file-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #dee2e6;
        }}
        .file-item:last-child {{
            border-bottom: none;
        }}
        .file-name {{
            font-family: 'Monaco', 'Menlo', monospace;
            color: #495057;
        }}
        .coverage-percent {{
            font-weight: bold;
            padding: 4px 8px;
            border-radius: 4px;
            color: white;
        }}
        .coverage-high {{ background: #28a745; }}
        .coverage-medium {{ background: #ffc107; color: #333; }}
        .coverage-low {{ background: #dc3545; }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #6c757d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 Test Coverage Report</h1>
            <p>RichesReach AI Platform - {self.report_data['timestamp']}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Overall Coverage</h3>
                <div class="number">{self.report_data['overall']['coverage']:.1f}%</div>
                <div class="coverage-bar">
                    <div class="coverage-fill" style="width: {self.report_data['overall']['coverage']}%"></div>
                </div>
                <p>{self.report_data['overall']['files_covered']} of {self.report_data['overall']['total_files']} files covered</p>
            </div>
            
            <div class="summary-card">
                <h3>Backend Coverage</h3>
                <div class="number">{self.report_data['backend']['coverage']:.1f}%</div>
                <div class="coverage-bar">
                    <div class="coverage-fill" style="width: {self.report_data['backend']['coverage']}%"></div>
                </div>
                <p>{len(self.report_data['backend']['files'])} files covered</p>
            </div>
            
            <div class="summary-card">
                <h3>Mobile Coverage</h3>
                <div class="number">{self.report_data['mobile']['coverage']:.1f}%</div>
                <div class="coverage-bar">
                    <div class="coverage-fill" style="width: {self.report_data['mobile']['coverage']}%"></div>
                </div>
                <p>{len(self.report_data['mobile']['files'])} files covered</p>
            </div>
        </div>
        
        <div class="details">
            <div class="section">
                <h2>📊 Backend Coverage Details</h2>
                <div class="file-list">
                    {"".join([f'''
                    <div class="file-item">
                        <span class="file-name">{file['file']}</span>
                        <span class="coverage-percent {'coverage-high' if file['coverage'] >= 80 else 'coverage-medium' if file['coverage'] >= 60 else 'coverage-low'}">
                            {file['coverage']:.1f}%
                        </span>
                    </div>
                    ''' for file in self.report_data['backend']['files']])}
                </div>
            </div>
            
            <div class="section">
                <h2>📱 Mobile Coverage Details</h2>
                <div class="file-list">
                    {"".join([f'''
                    <div class="file-item">
                        <span class="file-name">{file['file']}</span>
                        <span class="coverage-percent {'coverage-high' if file['coverage'] >= 80 else 'coverage-medium' if file['coverage'] >= 60 else 'coverage-low'}">
                            {file['coverage']:.1f}%
                        </span>
                    </div>
                    ''' for file in self.report_data['mobile']['files']])}
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | RichesReach AI Platform</p>
        </div>
    </div>
</body>
</html>
        """
        
        return html_content
    
    def generate_markdown_report(self) -> str:
        """Generate Markdown coverage report."""
        md_content = f"""# 🧪 Test Coverage Report

**Generated:** {self.report_data['timestamp']}

## 📊 Summary

| Metric | Value |
|--------|-------|
| **Overall Coverage** | {self.report_data['overall']['coverage']:.1f}% |
| **Files Covered** | {self.report_data['overall']['files_covered']} / {self.report_data['overall']['total_files']} |
| **Backend Coverage** | {self.report_data['backend']['coverage']:.1f}% |
| **Mobile Coverage** | {self.report_data['mobile']['coverage']:.1f}% |

## 🐍 Backend Coverage

| File | Coverage | Lines Covered | Total Lines |
|------|----------|---------------|-------------|
"""
        
        for file in self.report_data['backend']['files']:
            md_content += f"| `{file['file']}` | {file['coverage']:.1f}% | {file['lines_covered']} | {file['total_lines']} |\n"
        
        md_content += f"""
## 📱 Mobile Coverage

| File | Coverage | Lines Covered | Total Lines |
|------|----------|---------------|-------------|
"""
        
        for file in self.report_data['mobile']['files']:
            md_content += f"| `{file['file']}` | {file['coverage']:.1f}% | {file['lines_covered']} | {file['total_lines']} |\n"
        
        md_content += f"""
## 🎯 Recommendations

"""
        
        if self.report_data['overall']['coverage'] < 80:
            md_content += "- ⚠️ Overall coverage is below 80%. Consider adding more tests.\n"
        
        if self.report_data['backend']['coverage'] < 80:
            md_content += "- 🐍 Backend coverage is below 80%. Focus on testing core services.\n"
        
        if self.report_data['mobile']['coverage'] < 80:
            md_content += "- 📱 Mobile coverage is below 80%. Add more component tests.\n"
        
        if self.report_data['overall']['coverage'] >= 90:
            md_content += "- ✅ Excellent coverage! Maintain this level of testing.\n"
        
        md_content += f"""
## 📈 Coverage Trends

- **Backend Files:** {self.report_data['overall']['backend_files']}
- **Mobile Files:** {self.report_data['overall']['mobile_files']}
- **Total Files:** {self.report_data['overall']['total_files']}

---
*Generated by RichesReach AI Test Coverage Generator*
"""
        
        return md_content
    
    def generate_report(self) -> bool:
        """Generate comprehensive coverage report."""
        self.log("Starting coverage report generation...")
        
        # Generate backend coverage
        self.report_data["backend"] = self.generate_backend_coverage()
        
        # Generate mobile coverage
        self.report_data["mobile"] = self.generate_mobile_coverage()
        
        # Analyze overall coverage
        self.report_data["overall"] = self.analyze_test_coverage()
        
        # Generate reports
        self.log("Generating report files...")
        
        # Save JSON report
        with open("coverage_report.json", "w") as f:
            json.dump(self.report_data, f, indent=2)
        
        # Generate HTML report
        html_content = self.generate_html_report()
        with open("coverage_report.html", "w") as f:
            f.write(html_content)
        
        # Generate Markdown report
        md_content = self.generate_markdown_report()
        with open("coverage_report.md", "w") as f:
            f.write(md_content)
        
        self.log("Coverage reports generated successfully!")
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """Print coverage summary."""
        print("\n" + "="*60)
        print("📊 TEST COVERAGE SUMMARY")
        print("="*60)
        print(f"🎯 Overall Coverage: {self.report_data['overall']['coverage']:.1f}%")
        print(f"🐍 Backend Coverage: {self.report_data['backend']['coverage']:.1f}%")
        print(f"📱 Mobile Coverage: {self.report_data['mobile']['coverage']:.1f}%")
        print(f"📁 Files Covered: {self.report_data['overall']['files_covered']}/{self.report_data['overall']['total_files']}")
        print("="*60)
        print("📄 Reports generated:")
        print("  • coverage_report.json")
        print("  • coverage_report.html")
        print("  • coverage_report.md")
        print("="*60)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate test coverage reports for RichesReach AI")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--backend-only", action="store_true", help="Generate only backend coverage")
    parser.add_argument("--mobile-only", action="store_true", help="Generate only mobile coverage")
    
    args = parser.parse_args()
    
    generator = CoverageReportGenerator(verbose=args.verbose)
    
    if args.backend_only:
        generator.report_data["backend"] = generator.generate_backend_coverage()
        generator.report_data["mobile"] = {"coverage": 0, "files": []}
    elif args.mobile_only:
        generator.report_data["backend"] = {"coverage": 0, "files": []}
        generator.report_data["mobile"] = generator.generate_mobile_coverage()
    else:
        success = generator.generate_report()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
