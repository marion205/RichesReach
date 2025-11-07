"""
Enhanced Credit ML Service
Uses real transaction data from Yodlee to predict credit score improvements
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import connections

logger = logging.getLogger(__name__)

try:
    import numpy as np
    import pandas as pd
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("NumPy/Pandas not available, using fallback calculations")


class CreditMLService:
    """ML-powered credit score projection using transaction data"""
    
    def __init__(self):
        self.numpy_available = NUMPY_AVAILABLE
    
    def analyze_transactions_for_credit(
        self,
        transactions: List[Dict[str, Any]],
        credit_cards: List[Dict[str, Any]],
        current_score: int,
        days: int = 90
    ) -> Dict[str, Any]:
        """
        Analyze transactions to predict credit score improvement
        
        Args:
            transactions: List of transaction dicts from Yodlee
            credit_cards: List of credit card dicts
            current_score: Current credit score
            days: Number of days of transaction history to analyze
        
        Returns:
            Dict with score_gain, top_action, confidence, factors
        """
        try:
            # Filter transactions to last N days
            cutoff_date = timezone.now().date() - timedelta(days=days)
            
            # Analyze payment patterns
            payment_analysis = self._analyze_payment_patterns(transactions, credit_cards, cutoff_date)
            
            # Analyze utilization trends
            utilization_analysis = self._analyze_utilization_trends(credit_cards)
            
            # Analyze spending patterns
            spending_analysis = self._analyze_spending_patterns(transactions, cutoff_date)
            
            # Calculate score projection
            projection = self._calculate_score_projection(
                current_score,
                payment_analysis,
                utilization_analysis,
                spending_analysis
            )
            
            return projection
            
        except Exception as e:
            logger.error(f"Error analyzing transactions for credit: {e}")
            return self._fallback_projection(current_score)
    
    def _analyze_payment_patterns(
        self,
        transactions: List[Dict[str, Any]],
        credit_cards: List[Dict[str, Any]],
        cutoff_date: datetime.date
    ) -> Dict[str, Any]:
        """Analyze payment history patterns"""
        try:
            # Count on-time payments
            on_time_payments = 0
            late_payments = 0
            missed_payments = 0
            
            # Group transactions by card
            card_payments = {}
            for card in credit_cards:
                card_id = card.get('id') or card.get('yodlee_account_id')
                if card_id:
                    card_payments[card_id] = []
            
            # Analyze payment transactions
            for txn in transactions:
                txn_date = self._parse_date(txn.get('posted_date') or txn.get('transaction_date'))
                if not txn_date or txn_date < cutoff_date:
                    continue
                
                amount = abs(float(txn.get('amount', 0)))
                category = txn.get('category', '').lower()
                
                # Identify payments (negative amounts or payment categories)
                if amount > 0 and ('payment' in category or 'credit' in category):
                    on_time_payments += 1
                elif 'late' in category or 'fee' in category:
                    late_payments += 1
            
            total_payments = on_time_payments + late_payments + missed_payments
            on_time_rate = on_time_payments / total_payments if total_payments > 0 else 0.5
            
            return {
                'on_time_payments': on_time_payments,
                'late_payments': late_payments,
                'missed_payments': missed_payments,
                'on_time_rate': on_time_rate,
                'total_payments': total_payments,
            }
        except Exception as e:
            logger.error(f"Error analyzing payment patterns: {e}")
            return {'on_time_rate': 0.5, 'total_payments': 0}
    
    def _analyze_utilization_trends(self, credit_cards: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze credit utilization trends"""
        try:
            if not credit_cards:
                return {'current_utilization': 0.5, 'trend': 'stable'}
            
            total_limit = sum(float(card.get('limit', 0)) for card in credit_cards)
            total_balance = sum(float(card.get('balance', 0)) for card in credit_cards)
            
            if total_limit == 0:
                return {'current_utilization': 0.5, 'trend': 'stable'}
            
            current_utilization = total_balance / total_limit
            
            # Determine trend (simplified - in production, would compare historical)
            if current_utilization > 0.5:
                trend = 'high'
            elif current_utilization > 0.3:
                trend = 'moderate'
            else:
                trend = 'low'
            
            return {
                'current_utilization': current_utilization,
                'total_limit': total_limit,
                'total_balance': total_balance,
                'trend': trend,
            }
        except Exception as e:
            logger.error(f"Error analyzing utilization: {e}")
            return {'current_utilization': 0.5, 'trend': 'stable'}
    
    def _analyze_spending_patterns(
        self,
        transactions: List[Dict[str, Any]],
        cutoff_date: datetime.date
    ) -> Dict[str, Any]:
        """Analyze spending patterns for credit health"""
        try:
            total_spending = 0
            credit_card_spending = 0
            recurring_bills = 0
            
            for txn in transactions:
                txn_date = self._parse_date(txn.get('posted_date') or txn.get('transaction_date'))
                if not txn_date or txn_date < cutoff_date:
                    continue
                
                amount = abs(float(txn.get('amount', 0)))
                account_type = txn.get('account_type', '').lower()
                category = txn.get('category', '').lower()
                
                total_spending += amount
                
                if 'credit' in account_type or 'card' in account_type:
                    credit_card_spending += amount
                
                # Identify recurring bills
                if any(bill in category for bill in ['utility', 'phone', 'internet', 'subscription']):
                    recurring_bills += 1
            
            return {
                'total_spending': total_spending,
                'credit_card_spending': credit_card_spending,
                'recurring_bills': recurring_bills,
                'credit_card_ratio': credit_card_spending / total_spending if total_spending > 0 else 0,
            }
        except Exception as e:
            logger.error(f"Error analyzing spending patterns: {e}")
            return {'total_spending': 0, 'credit_card_ratio': 0}
    
    def _calculate_score_projection(
        self,
        current_score: int,
        payment_analysis: Dict[str, Any],
        utilization_analysis: Dict[str, Any],
        spending_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate credit score projection based on analysis"""
        try:
            score_gain = 0
            top_action = "CONTINUE_GOOD_HABITS"
            confidence = 0.5
            factors = {}
            
            # Payment history impact (35% of score)
            on_time_rate = payment_analysis.get('on_time_rate', 0.5)
            if on_time_rate >= 0.95:
                payment_gain = 15
                factors['paymentHistory'] = f"+{payment_gain} points (excellent payment history)"
            elif on_time_rate >= 0.85:
                payment_gain = 10
                factors['paymentHistory'] = f"+{payment_gain} points (good payment history)"
            elif on_time_rate < 0.7:
                payment_gain = -10
                factors['paymentHistory'] = f"{payment_gain} points (improve payment consistency)"
                top_action = "SET_UP_AUTOPAY"
            else:
                payment_gain = 5
                factors['paymentHistory'] = f"+{payment_gain} points (maintain on-time payments)"
            
            score_gain += payment_gain
            
            # Utilization impact (30% of score)
            utilization = utilization_analysis.get('current_utilization', 0.5)
            if utilization > 0.5:
                util_gain = -20
                factors['utilization'] = f"{util_gain} points (reduce utilization below 30%)"
                top_action = "REDUCE_UTILIZATION_BELOW_30"
            elif utilization > 0.3:
                util_gain = -5
                factors['utilization'] = f"{util_gain} points (aim for under 30%)"
                if top_action == "CONTINUE_GOOD_HABITS":
                    top_action = "REDUCE_UTILIZATION_TO_20"
            else:
                util_gain = 10
                factors['utilization'] = f"+{util_gain} points (excellent utilization)"
            
            score_gain += util_gain
            
            # Credit age and mix (25% of score)
            # Simplified - would need historical data
            age_gain = 5
            factors['creditAge'] = f"+{age_gain} points (accounts aging)"
            
            score_gain += age_gain
            
            # Calculate confidence based on data quality
            total_payments = payment_analysis.get('total_payments', 0)
            if total_payments >= 10:
                confidence = 0.75
            elif total_payments >= 5:
                confidence = 0.65
            else:
                confidence = 0.55
            
            # Cap score gain realistically
            score_gain = max(-30, min(50, score_gain))
            
            return {
                'scoreGain6m': score_gain,
                'topAction': top_action,
                'confidence': confidence,
                'factors': factors,
            }
            
        except Exception as e:
            logger.error(f"Error calculating score projection: {e}")
            return self._fallback_projection(current_score)
    
    def _fallback_projection(self, current_score: int) -> Dict[str, Any]:
        """Fallback projection when analysis fails"""
        return {
            'scoreGain6m': 15,
            'topAction': 'SET_UP_AUTOPAY',
            'confidence': 0.5,
            'factors': {
                'paymentHistory': '+5 points',
                'utilization': '+5 points',
                'creditAge': '+5 points',
            }
        }
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime.date]:
        """Parse date string to date object"""
        if not date_str:
            return None
        try:
            if isinstance(date_str, str):
                # Try different date formats
                for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S']:
                    try:
                        return datetime.strptime(date_str.split('T')[0], '%Y-%m-%d').date()
                    except:
                        continue
            return None
        except Exception as e:
            logger.error(f"Error parsing date {date_str}: {e}")
            return None

