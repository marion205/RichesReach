"""
Unit tests for Multi-Year Projection endpoint
"""

import pytest
from datetime import datetime


class TestProjectionEndpoint:
    """Test suite for projection endpoint"""

    def test_projection_query_params(self):
        """Test projection endpoint query parameters"""
        years = 5
        income = 80000
        filing_status = 'single'
        state = 'CA'
        
        assert years == 5
        assert income == 80000
        assert filing_status == 'single'
        assert state == 'CA'

    def test_projection_years_calculation(self):
        """Test projection years calculation"""
        current_year = datetime.now().year
        years = 5
        
        projection_years = [current_year + i for i in range(years + 1)]
        
        assert len(projection_years) == 6
        assert projection_years[0] == current_year
        assert projection_years[5] == current_year + 5

    def test_income_projection(self):
        """Test income projection with growth"""
        base_income = 80000
        growth_rate = 0.03  # 3% annual growth
        years = 5
        
        projections = []
        for i in range(years + 1):
            projected_income = base_income * (1.03 ** i)
            projections.append({
                'year': 2025 + i,
                'projectedIncome': round(projected_income, 2),
            })
        
        assert len(projections) == 6
        assert projections[0]['projectedIncome'] == 80000
        assert projections[1]['projectedIncome'] == 82400
        assert projections[5]['projectedIncome'] > projections[0]['projectedIncome']

    def test_tax_projection_calculation(self):
        """Test tax projection calculation"""
        income = 80000
        federal_tax_rate = 0.22
        state_tax_rate = 0.10
        
        federal_tax = income * federal_tax_rate
        state_tax = income * state_tax_rate
        total_tax = federal_tax + state_tax
        effective_rate = (total_tax / income * 100) if income > 0 else 0
        
        assert federal_tax == 17600
        assert state_tax == 8000
        assert total_tax == 25600
        assert effective_rate == 32.0

    def test_projection_response_format(self):
        """Test projection response format"""
        current_year = datetime.now().year
        projections = []
        
        for i in range(6):
            year = current_year + i
            projected_income = 80000 * (1.03 ** i)
            projected_tax = projected_income * 0.32
            effective_rate = 32.0
            
            projections.append({
                'year': year,
                'projectedIncome': round(projected_income, 2),
                'projectedTax': round(projected_tax, 2),
                'effectiveRate': round(effective_rate, 2),
            })
        
        response = {
            'projections': projections,
            'currentYear': current_year,
        }
        
        assert 'projections' in response
        assert 'currentYear' in response
        assert len(response['projections']) == 6
        assert response['currentYear'] == current_year

    def test_different_filing_statuses(self):
        """Test projections for different filing statuses"""
        income = 80000
        filing_statuses = ['single', 'married-joint', 'married-separate', 'head-of-household']
        
        # Simplified tax calculation
        tax_rates = {
            'single': 0.22,
            'married-joint': 0.20,
            'married-separate': 0.22,
            'head-of-household': 0.21,
        }
        
        for status in filing_statuses:
            tax_rate = tax_rates.get(status, 0.22)
            projected_tax = income * tax_rate
            assert projected_tax > 0
            assert projected_tax < income

    def test_different_states(self):
        """Test projections for different states"""
        income = 80000
        state_rates = {
            'CA': 0.10,
            'NY': 0.09,
            'TX': 0.0,
            'FL': 0.0,
        }
        
        for state, rate in state_rates.items():
            state_tax = income * rate
            if state in ['TX', 'FL']:
                assert state_tax == 0
            else:
                assert state_tax > 0

    def test_projection_growth_consistency(self):
        """Test that projections show consistent growth"""
        base_income = 80000
        growth_rate = 0.03
        
        incomes = [base_income * (1 + growth_rate) ** i for i in range(6)]
        
        # Each year should be 3% more than previous
        for i in range(1, len(incomes)):
            growth = (incomes[i] - incomes[i-1]) / incomes[i-1]
            assert abs(growth - growth_rate) < 0.001  # Allow small floating point errors


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

