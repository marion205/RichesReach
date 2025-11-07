"""
Unit Tests for Credit ML Service
Tests transaction analysis and ML-powered projections
"""

import pytest
from datetime import datetime, timedelta
from django.utils import timezone
from core.credit_ml_service import CreditMLService


class TestCreditMLService:
    """Test credit ML service functionality"""
    
    def test_analyze_payment_patterns(self):
        """Test payment pattern analysis"""
        ml_service = CreditMLService()
        
        transactions = [
            {'amount': -100, 'posted_date': '2024-01-15', 'category': 'payment'},
            {'amount': -50, 'posted_date': '2024-01-20', 'category': 'payment'},
            {'amount': 25, 'posted_date': '2024-01-25', 'category': 'purchase'},
        ]
        
        credit_cards = [
            {'id': 1, 'limit': 1000, 'balance': 200}
        ]
        
        cutoff_date = timezone.now().date() - timedelta(days=90)
        
        result = ml_service._analyze_payment_patterns(transactions, credit_cards, cutoff_date)
        
        assert 'on_time_rate' in result
        assert 'total_payments' in result
        assert 0 <= result['on_time_rate'] <= 1
    
    def test_analyze_utilization_trends(self):
        """Test utilization trend analysis"""
        ml_service = CreditMLService()
        
        credit_cards = [
            {'limit': 1000, 'balance': 450},
            {'limit': 500, 'balance': 100},
        ]
        
        result = ml_service._analyze_utilization_trends(credit_cards)
        
        assert 'current_utilization' in result
        assert 'trend' in result
        assert 0 <= result['current_utilization'] <= 1
        assert result['trend'] in ['high', 'moderate', 'low']
    
    def test_calculate_score_projection(self):
        """Test score projection calculation"""
        ml_service = CreditMLService()
        
        payment_analysis = {
            'on_time_rate': 0.95,
            'total_payments': 10,
        }
        
        utilization_analysis = {
            'current_utilization': 0.45,
            'trend': 'moderate',
        }
        
        spending_analysis = {
            'total_spending': 2000,
            'credit_card_ratio': 0.3,
        }
        
        result = ml_service._calculate_score_projection(
            current_score=580,
            payment_analysis=payment_analysis,
            utilization_analysis=utilization_analysis,
            spending_analysis=spending_analysis
        )
        
        assert 'scoreGain6m' in result
        assert 'topAction' in result
        assert 'confidence' in result
        assert 'factors' in result
        assert isinstance(result['scoreGain6m'], int)
        assert 0 <= result['confidence'] <= 1
    
    def test_analyze_transactions_for_credit(self):
        """Test full transaction analysis"""
        ml_service = CreditMLService()
        
        transactions = [
            {'amount': -100, 'posted_date': '2024-01-15', 'category': 'payment', 'account_type': 'credit'},
            {'amount': 50, 'posted_date': '2024-01-20', 'category': 'purchase', 'account_type': 'credit'},
        ]
        
        credit_cards = [
            {'id': 1, 'limit': 1000, 'balance': 450, 'utilization': 0.45}
        ]
        
        result = ml_service.analyze_transactions_for_credit(
            transactions=transactions,
            credit_cards=credit_cards,
            current_score=580,
            days=90
        )
        
        assert 'scoreGain6m' in result
        assert 'topAction' in result
        assert 'confidence' in result
        assert 'factors' in result
    
    def test_fallback_projection(self):
        """Test fallback projection when analysis fails"""
        ml_service = CreditMLService()
        
        result = ml_service._fallback_projection(580)
        
        assert 'scoreGain6m' in result
        assert 'topAction' in result
        assert 'confidence' in result
        assert result['topAction'] == 'SET_UP_AUTOPAY'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

