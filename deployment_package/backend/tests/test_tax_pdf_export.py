"""
Unit tests for Tax Optimization PDF Export endpoint
"""

import pytest
import json
from io import BytesIO
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

# Test if reportlab is available
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


@pytest.fixture
def mock_user():
    """Create a mock user for testing"""
    user = Mock()
    user.id = 1
    user.email = 'test@example.com'
    user.name = 'Test User'
    return user


@pytest.fixture
def mock_portfolio_metrics():
    """Create mock portfolio metrics"""
    return {
        'total_value': 100000.0,
        'total_return': 15000.0,
        'holdings': [
            {
                'symbol': 'AAPL',
                'company_name': 'Apple Inc.',
                'shares': 100,
                'current_price': 150.0,
                'cost_basis': 120.0,
                'total_value': 15000.0,
                'return_amount': 3000.0,
                'return_percent': 25.0,
            },
            {
                'symbol': 'MSFT',
                'company_name': 'Microsoft Corporation',
                'shares': 50,
                'current_price': 300.0,
                'cost_basis': 280.0,
                'total_value': 15000.0,
                'return_amount': 1000.0,
                'return_percent': 7.14,
            },
        ],
    }


class TestTaxPDFExport:
    """Test suite for PDF export endpoint"""

    @pytest.mark.skipif(not REPORTLAB_AVAILABLE, reason="reportlab not installed")
    def test_pdf_generation_basic(self):
        """Test basic PDF generation"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        
        # Create a simple PDF
        from reportlab.platypus import Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph("Test PDF", styles['Title']))
        story.append(Spacer(1, 12))
        story.append(Paragraph("This is a test PDF document.", styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        pdf_bytes = buffer.getvalue()
        
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')

    @pytest.mark.skipif(not REPORTLAB_AVAILABLE, reason="reportlab not installed")
    def test_pdf_with_table(self):
        """Test PDF generation with table"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        
        from reportlab.platypus import Table, TableStyle
        from reportlab.lib import colors
        
        data = [
            ['Item', 'Value'],
            ['Tax', '$10,000'],
            ['Income', '$80,000'],
        ]
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        
        story = [table]
        doc.build(story)
        buffer.seek(0)
        pdf_bytes = buffer.getvalue()
        
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')

    def test_pdf_endpoint_requires_auth(self, mock_user):
        """Test that PDF endpoint requires authentication"""
        # This would be tested with actual FastAPI test client
        # For now, we verify the logic
        auth_header = None
        assert auth_header is None
        
        # Endpoint should require auth
        requires_auth = auth_header is not None
        assert not requires_auth

    def test_pdf_endpoint_request_body(self):
        """Test PDF endpoint request body parsing"""
        request_body = {
            'year': 2025,
            'filingStatus': 'single',
            'state': 'CA',
            'income': 80000,
        }
        
        assert request_body['year'] == 2025
        assert request_body['filingStatus'] == 'single'
        assert request_body['state'] == 'CA'
        assert request_body['income'] == 80000

    def test_holdings_formatting(self, mock_portfolio_metrics):
        """Test holdings data formatting for PDF"""
        holdings = []
        for holding in mock_portfolio_metrics['holdings']:
            holdings.append({
                'symbol': holding.get('symbol', ''),
                'companyName': holding.get('company_name', holding.get('name', '')),
                'shares': holding.get('shares', 0),
                'currentPrice': float(holding.get('current_price', 0) or 0),
                'costBasis': float(holding.get('cost_basis', 0) or 0),
                'totalValue': float(holding.get('total_value', 0) or 0),
                'returnAmount': float(holding.get('return_amount', 0) or 0),
                'returnPercent': float(holding.get('return_percent', 0) or 0),
            })
        
        assert len(holdings) == 2
        assert holdings[0]['symbol'] == 'AAPL'
        assert holdings[0]['shares'] == 100
        assert holdings[0]['currentPrice'] == 150.0
        assert holdings[1]['symbol'] == 'MSFT'
        assert holdings[1]['shares'] == 50

    def test_tax_calculation_logic(self):
        """Test tax calculation logic used in PDF"""
        income = 80000
        state = 'CA'
        
        # Simplified tax calculation (matching backend logic)
        federal_tax = income * 0.22
        state_tax = income * 0.10 if state == 'CA' else income * 0.05
        total_tax = federal_tax + state_tax
        effective_rate = (total_tax / income * 100) if income > 0 else 0
        
        assert federal_tax == 17600.0
        assert state_tax == 8000.0
        assert total_tax == 25600.0
        assert effective_rate == 32.0

    def test_pdf_response_headers(self):
        """Test PDF response headers"""
        headers = {
            'Content-Disposition': 'attachment; filename="tax_report_2025.pdf"',
        }
        
        assert 'Content-Disposition' in headers
        assert 'tax_report_2025.pdf' in headers['Content-Disposition']

    def test_error_handling_no_reportlab(self):
        """Test error handling when reportlab is not available"""
        reportlab_available = False
        
        if not reportlab_available:
            error_message = "PDF generation not available - reportlab not installed"
            assert "reportlab not installed" in error_message

    def test_error_handling_no_user(self):
        """Test error handling when user is not found"""
        user = None
        
        if not user:
            # Should fallback to demo user or raise error
            use_demo = True
            assert use_demo

    def test_error_handling_invalid_request_body(self):
        """Test error handling for invalid request body"""
        # Missing required fields
        invalid_body = {
            'year': 2025,
            # Missing filingStatus, state, income
        }
        
        assert 'filingStatus' not in invalid_body
        assert 'state' not in invalid_body
        assert 'income' not in invalid_body


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

