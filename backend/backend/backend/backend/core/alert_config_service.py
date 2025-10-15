import logging
from typing import Dict, Any, Optional
from django.contrib.auth.models import User
from .models_smart_alerts import AlertThreshold, AlertDeliveryPreference

logger = logging.getLogger(__name__)

class AlertConfigService:
    """Service for managing alert thresholds and user preferences"""
    
    # Default thresholds for new users
    DEFAULT_THRESHOLDS = {
        'performance_underperformance': {
            'performance_diff_threshold': 2.0,
            'cooldown_period': 168,  # 7 days
        },
        'performance_outperformance': {
            'performance_diff_threshold': 2.0,
            'cooldown_period': 168,  # 7 days
        },
        'risk_sharpe_deterioration': {
            'sharpe_min_threshold': 0.5,
            'cooldown_period': 72,  # 3 days
        },
        'risk_high_volatility': {
            'volatility_max_threshold': 20.0,
            'cooldown_period': 24,  # 1 day
        },
        'risk_high_drawdown': {
            'drawdown_max_threshold': -15.0,
            'cooldown_period': 24,  # 1 day
        },
        'risk_high_var': {
            'var95_max_threshold': -3.0,
            'cooldown_period': 12,  # 12 hours
        },
        'allocation_tech_overweight': {
            'tech_weight_max_threshold': 0.35,
            'cooldown_period': 168,  # 7 days
        },
        'allocation_high_concentration': {
            'sector_concentration_max_threshold': 0.40,
            'cooldown_period': 168,  # 7 days
        },
        'allocation_stock_concentration': {
            'concentration_max_threshold': 0.15,
            'cooldown_period': 168,  # 7 days
        },
        'yodlee_portfolio_decline': {
            'performance_diff_threshold': 5.0,
            'cooldown_period': 24,  # 1 day
        },
        'yodlee_portfolio_growth': {
            'performance_diff_threshold': 5.0,
            'cooldown_period': 168,  # 7 days
        },
        'yodlee_high_cash_position': {
            'cash_max_threshold': 0.20,
            'cooldown_period': 168,  # 7 days
        },
        'yodlee_low_cash_position': {
            'cash_min_threshold': 0.02,
            'cooldown_period': 168,  # 7 days
        },
        'yodlee_large_transaction': {
            'transaction_amount_threshold': 10000.0,
            'cooldown_period': 24,  # 1 day
        },
        'yodlee_frequent_trading': {
            'trading_frequency_max_threshold': 10,
            'cooldown_period': 168,  # 7 days
        },
        'yodlee_negative_cashflow': {
            'cooldown_period': 24,  # 1 day
        },
        'yodlee_high_expense_ratio': {
            'expense_ratio_max_threshold': 0.90,
            'cooldown_period': 168,  # 7 days
        },
        'yodlee_stock_concentration': {
            'concentration_max_threshold': 0.15,
            'cooldown_period': 168,  # 7 days
        },
        'yodlee_sector_concentration': {
            'sector_concentration_max_threshold': 0.40,
            'cooldown_period': 168,  # 7 days
        },
        'yodlee_low_diversification': {
            'min_holdings_threshold': 10,
            'min_portfolio_value_threshold': 50000.0,
            'cooldown_period': 168,  # 7 days
        },
    }
    
    # Default delivery preferences
    DEFAULT_DELIVERY_PREFERENCES = {
        'performance': {
            'critical': {'delivery_method': 'push', 'max_alerts_per_day': 5},
            'important': {'delivery_method': 'in_app', 'max_alerts_per_day': 10},
            'informational': {'delivery_method': 'in_app', 'max_alerts_per_day': 20},
        },
        'risk': {
            'critical': {'delivery_method': 'push', 'max_alerts_per_day': 3},
            'important': {'delivery_method': 'push', 'max_alerts_per_day': 5},
            'informational': {'delivery_method': 'in_app', 'max_alerts_per_day': 10},
        },
        'allocation': {
            'critical': {'delivery_method': 'in_app', 'max_alerts_per_day': 5},
            'important': {'delivery_method': 'in_app', 'max_alerts_per_day': 10},
            'informational': {'delivery_method': 'in_app', 'max_alerts_per_day': 15},
        },
        'portfolio': {
            'critical': {'delivery_method': 'push', 'max_alerts_per_day': 3},
            'important': {'delivery_method': 'in_app', 'max_alerts_per_day': 5},
            'informational': {'delivery_method': 'in_app', 'max_alerts_per_day': 10},
        },
        'transaction': {
            'critical': {'delivery_method': 'push', 'max_alerts_per_day': 5},
            'important': {'delivery_method': 'in_app', 'max_alerts_per_day': 10},
            'informational': {'delivery_method': 'in_app', 'max_alerts_per_day': 20},
        },
        'cashflow': {
            'critical': {'delivery_method': 'push', 'max_alerts_per_day': 2},
            'important': {'delivery_method': 'in_app', 'max_alerts_per_day': 5},
            'informational': {'delivery_method': 'in_app', 'max_alerts_per_day': 10},
        },
        'concentration': {
            'critical': {'delivery_method': 'in_app', 'max_alerts_per_day': 3},
            'important': {'delivery_method': 'in_app', 'max_alerts_per_day': 5},
            'informational': {'delivery_method': 'in_app', 'max_alerts_per_day': 10},
        },
        'diversification': {
            'critical': {'delivery_method': 'in_app', 'max_alerts_per_day': 3},
            'important': {'delivery_method': 'in_app', 'max_alerts_per_day': 5},
            'informational': {'delivery_method': 'in_app', 'max_alerts_per_day': 10},
        },
        'behavior': {
            'critical': {'delivery_method': 'push', 'max_alerts_per_day': 3},
            'important': {'delivery_method': 'in_app', 'max_alerts_per_day': 5},
            'informational': {'delivery_method': 'in_app', 'max_alerts_per_day': 10},
        },
        'spending': {
            'critical': {'delivery_method': 'push', 'max_alerts_per_day': 2},
            'important': {'delivery_method': 'in_app', 'max_alerts_per_day': 5},
            'informational': {'delivery_method': 'in_app', 'max_alerts_per_day': 10},
        },
        'attribution': {
            'critical': {'delivery_method': 'in_app', 'max_alerts_per_day': 3},
            'important': {'delivery_method': 'in_app', 'max_alerts_per_day': 5},
            'informational': {'delivery_method': 'in_app', 'max_alerts_per_day': 10},
        },
        'market_regime': {
            'critical': {'delivery_method': 'push', 'max_alerts_per_day': 2},
            'important': {'delivery_method': 'in_app', 'max_alerts_per_day': 3},
            'informational': {'delivery_method': 'in_app', 'max_alerts_per_day': 5},
        },
        'rebalancing': {
            'critical': {'delivery_method': 'in_app', 'max_alerts_per_day': 3},
            'important': {'delivery_method': 'in_app', 'max_alerts_per_day': 5},
            'informational': {'delivery_method': 'in_app', 'max_alerts_per_day': 10},
        },
        'opportunity': {
            'critical': {'delivery_method': 'in_app', 'max_alerts_per_day': 2},
            'important': {'delivery_method': 'in_app', 'max_alerts_per_day': 5},
            'informational': {'delivery_method': 'in_app', 'max_alerts_per_day': 10},
        },
    }
    
    def __init__(self):
        pass
    
    def get_user_thresholds(self, user: User, alert_type: str) -> Dict[str, Any]:
        """Get user-specific thresholds for an alert type"""
        try:
            threshold_obj = AlertThreshold.objects.get(user=user, alert_type=alert_type)
            return {
                'performance_diff_threshold': threshold_obj.performance_diff_threshold,
                'sharpe_min_threshold': threshold_obj.sharpe_min_threshold,
                'volatility_max_threshold': threshold_obj.volatility_max_threshold,
                'drawdown_max_threshold': threshold_obj.drawdown_max_threshold,
                'var95_max_threshold': threshold_obj.var95_max_threshold,
                'tech_weight_max_threshold': threshold_obj.tech_weight_max_threshold,
                'cash_min_threshold': threshold_obj.cash_min_threshold,
                'cash_max_threshold': threshold_obj.cash_max_threshold,
                'concentration_max_threshold': threshold_obj.concentration_max_threshold,
                'sector_concentration_max_threshold': threshold_obj.sector_concentration_max_threshold,
                'trading_frequency_max_threshold': threshold_obj.trading_frequency_max_threshold,
                'expense_ratio_max_threshold': threshold_obj.expense_ratio_max_threshold,
                'cooldown_period': threshold_obj.cooldown_period,
                'enabled': threshold_obj.enabled,
            }
        except AlertThreshold.DoesNotExist:
            # Return default thresholds
            return self.DEFAULT_THRESHOLDS.get(alert_type, {})
    
    def set_user_thresholds(self, user: User, alert_type: str, thresholds: Dict[str, Any]) -> AlertThreshold:
        """Set user-specific thresholds for an alert type"""
        try:
            threshold_obj = AlertThreshold.objects.get(user=user, alert_type=alert_type)
            # Update existing thresholds
            for key, value in thresholds.items():
                if hasattr(threshold_obj, key):
                    setattr(threshold_obj, key, value)
            threshold_obj.save()
            return threshold_obj
        except AlertThreshold.DoesNotExist:
            # Create new thresholds
            threshold_data = {
                'user': user,
                'alert_type': alert_type,
                **thresholds
            }
            return AlertThreshold.objects.create(**threshold_data)
    
    def get_user_delivery_preferences(self, user: User, category: str, priority_level: str) -> Dict[str, Any]:
        """Get user delivery preferences for a category and priority level"""
        try:
            pref_obj = AlertDeliveryPreference.objects.get(
                user=user, 
                alert_category=category, 
                priority_level=priority_level
            )
            return {
                'delivery_method': pref_obj.delivery_method,
                'quiet_hours_enabled': pref_obj.quiet_hours_enabled,
                'quiet_hours_start': pref_obj.quiet_hours_start,
                'quiet_hours_end': pref_obj.quiet_hours_end,
                'max_alerts_per_day': pref_obj.max_alerts_per_day,
                'digest_frequency': pref_obj.digest_frequency,
                'enabled': pref_obj.enabled,
            }
        except AlertDeliveryPreference.DoesNotExist:
            # Return default preferences
            return self.DEFAULT_DELIVERY_PREFERENCES.get(category, {}).get(priority_level, {
                'delivery_method': 'in_app',
                'quiet_hours_enabled': True,
                'quiet_hours_start': '22:00',
                'quiet_hours_end': '08:00',
                'max_alerts_per_day': 10,
                'digest_frequency': 'daily',
                'enabled': True,
            })
    
    def set_user_delivery_preferences(self, user: User, category: str, priority_level: str, 
                                    preferences: Dict[str, Any]) -> AlertDeliveryPreference:
        """Set user delivery preferences for a category and priority level"""
        try:
            pref_obj = AlertDeliveryPreference.objects.get(
                user=user, 
                alert_category=category, 
                priority_level=priority_level
            )
            # Update existing preferences
            for key, value in preferences.items():
                if hasattr(pref_obj, key):
                    setattr(pref_obj, key, value)
            pref_obj.save()
            return pref_obj
        except AlertDeliveryPreference.DoesNotExist:
            # Create new preferences
            pref_data = {
                'user': user,
                'alert_category': category,
                'priority_level': priority_level,
                **preferences
            }
            return AlertDeliveryPreference.objects.create(**pref_data)
    
    def initialize_user_defaults(self, user: User) -> None:
        """Initialize default thresholds and preferences for a new user"""
        try:
            # Create default thresholds for all alert types
            for alert_type, default_thresholds in self.DEFAULT_THRESHOLDS.items():
                AlertThreshold.objects.get_or_create(
                    user=user,
                    alert_type=alert_type,
                    defaults=default_thresholds
                )
            
            # Create default delivery preferences
            for category, priority_prefs in self.DEFAULT_DELIVERY_PREFERENCES.items():
                for priority_level, prefs in priority_prefs.items():
                    AlertDeliveryPreference.objects.get_or_create(
                        user=user,
                        alert_category=category,
                        priority_level=priority_level,
                        defaults=prefs
                    )
            
            logger.info(f"Initialized default alert configs for user {user.id}")
            
        except Exception as e:
            logger.error(f"Error initializing user defaults for {user.id}: {e}")
    
    def get_all_user_thresholds(self, user: User) -> Dict[str, Dict[str, Any]]:
        """Get all thresholds for a user"""
        thresholds = {}
        for alert_type in self.DEFAULT_THRESHOLDS.keys():
            thresholds[alert_type] = self.get_user_thresholds(user, alert_type)
        return thresholds
    
    def get_all_user_delivery_preferences(self, user: User) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Get all delivery preferences for a user"""
        preferences = {}
        for category, priority_prefs in self.DEFAULT_DELIVERY_PREFERENCES.items():
            preferences[category] = {}
            for priority_level in priority_prefs.keys():
                preferences[category][priority_level] = self.get_user_delivery_preferences(
                    user, category, priority_level
                )
        return preferences
    
    def is_alert_enabled(self, user: User, alert_type: str) -> bool:
        """Check if an alert type is enabled for a user"""
        try:
            threshold_obj = AlertThreshold.objects.get(user=user, alert_type=alert_type)
            return threshold_obj.enabled
        except AlertThreshold.DoesNotExist:
            return True  # Default to enabled if no specific config
    
    def get_cooldown_period(self, user: User, alert_type: str) -> int:
        """Get cooldown period in hours for an alert type"""
        thresholds = self.get_user_thresholds(user, alert_type)
        return thresholds.get('cooldown_period', 168)  # Default 7 days
    
    def should_deliver_alert(self, user: User, category: str, priority_level: str) -> bool:
        """Check if an alert should be delivered based on user preferences"""
        try:
            pref_obj = AlertDeliveryPreference.objects.get(
                user=user, 
                alert_category=category, 
                priority_level=priority_level
            )
            return pref_obj.enabled
        except AlertDeliveryPreference.DoesNotExist:
            return True  # Default to enabled if no specific config

# Global instance
alert_config_service = AlertConfigService()
