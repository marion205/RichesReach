"""
Premium Subscription Billing Configuration
Defines subscription tiers, pricing, and feature access
"""
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass

class SubscriptionTier(Enum):
    FREE = "free"
    PREMIUM = "premium"
    PRO = "pro"

@dataclass
class SubscriptionPlan:
    """Subscription plan configuration"""
    tier: SubscriptionTier
    name: str
    price_monthly: float
    price_yearly: float
    features: List[str]
    max_portfolio_value: Optional[float] = None
    max_trades_per_month: Optional[int] = None
    priority_support: bool = False
    advanced_analytics: bool = False
    api_access: bool = False

# Subscription Plans Configuration
SUBSCRIPTION_PLANS = {
    SubscriptionTier.FREE: SubscriptionPlan(
        tier=SubscriptionTier.FREE,
        name="Free",
        price_monthly=0.0,
        price_yearly=0.0,
        features=[
            "Basic portfolio tracking",
            "Stock price alerts",
            "Basic market data",
            "Community features",
        ],
        max_portfolio_value=10000.0,
        max_trades_per_month=10,
    ),
    
    SubscriptionTier.PREMIUM: SubscriptionPlan(
        tier=SubscriptionTier.PREMIUM,
        name="Premium",
        price_monthly=9.99,
        price_yearly=99.99,  # ~17% discount
        features=[
            "Everything in Free",
            "Tax-loss harvesting recommendations",
            "Capital gains optimization",
            "Tax-efficient rebalancing",
            "Tax bracket analysis",
            "Smart lot optimizer",
            "Wash-sale guard",
            "Advanced portfolio analytics",
            "Priority customer support",
        ],
        max_portfolio_value=100000.0,
        max_trades_per_month=100,
        priority_support=True,
        advanced_analytics=True,
    ),
    
    SubscriptionTier.PRO: SubscriptionPlan(
        tier=SubscriptionTier.PRO,
        name="Pro",
        price_monthly=19.99,
        price_yearly=199.99,  # ~17% discount
        features=[
            "Everything in Premium",
            "Two-year gains planner",
            "Borrow vs sell advisor",
            "Privacy mode (on-device inference)",
            "Audit-grade explainability",
            "Unlimited portfolio value",
            "Unlimited trades",
            "API access",
            "White-label options",
            "Dedicated account manager",
        ],
        priority_support=True,
        advanced_analytics=True,
        api_access=True,
    ),
}

# Feature access mapping
FEATURE_ACCESS = {
    "tax_loss_harvesting": [SubscriptionTier.PREMIUM, SubscriptionTier.PRO],
    "capital_gains_optimization": [SubscriptionTier.PREMIUM, SubscriptionTier.PRO],
    "tax_efficient_rebalancing": [SubscriptionTier.PREMIUM, SubscriptionTier.PRO],
    "tax_bracket_analysis": [SubscriptionTier.PREMIUM, SubscriptionTier.PRO],
    "smart_lot_optimizer": [SubscriptionTier.PREMIUM, SubscriptionTier.PRO],
    "wash_sale_guard": [SubscriptionTier.PREMIUM, SubscriptionTier.PRO],
    "two_year_gains_planner": [SubscriptionTier.PRO],
    "borrow_vs_sell_advisor": [SubscriptionTier.PRO],
    "privacy_mode": [SubscriptionTier.PRO],
    "audit_grade_explainability": [SubscriptionTier.PRO],
    "api_access": [SubscriptionTier.PRO],
    "advanced_analytics": [SubscriptionTier.PREMIUM, SubscriptionTier.PRO],
    "priority_support": [SubscriptionTier.PREMIUM, SubscriptionTier.PRO],
}

def get_plan(tier: SubscriptionTier) -> SubscriptionPlan:
    """Get subscription plan by tier"""
    return SUBSCRIPTION_PLANS[tier]

def get_all_plans() -> Dict[SubscriptionTier, SubscriptionPlan]:
    """Get all subscription plans"""
    return SUBSCRIPTION_PLANS

def has_feature_access(tier: SubscriptionTier, feature: str) -> bool:
    """Check if a subscription tier has access to a feature"""
    if feature not in FEATURE_ACCESS:
        return False
    return tier in FEATURE_ACCESS[feature]

def get_available_features(tier: SubscriptionTier) -> List[str]:
    """Get all features available for a subscription tier"""
    available_features = []
    for feature, required_tiers in FEATURE_ACCESS.items():
        if tier in required_tiers:
            available_features.append(feature)
    return available_features

def get_upgrade_options(current_tier: SubscriptionTier) -> List[SubscriptionPlan]:
    """Get available upgrade options for a subscription tier"""
    upgrade_options = []
    for tier, plan in SUBSCRIPTION_PLANS.items():
        if tier != current_tier and tier != SubscriptionTier.FREE:
            upgrade_options.append(plan)
    return upgrade_options

# Stripe configuration
STRIPE_CONFIG = {
    "publishable_key": "pk_test_...",  # Replace with actual Stripe publishable key
    "secret_key": "sk_test_...",       # Replace with actual Stripe secret key
    "webhook_secret": "whsec_...",     # Replace with actual webhook secret
    "currency": "usd",
    "trial_period_days": 7,
}

# RevenueCat configuration (for mobile)
REVENUECAT_CONFIG = {
    "api_key": "appl_...",  # Replace with actual RevenueCat API key
    "entitlements": {
        "premium": "premium_features",
        "pro": "pro_features",
    },
    "products": {
        "premium_monthly": "premium_monthly",
        "premium_yearly": "premium_yearly",
        "pro_monthly": "pro_monthly",
        "pro_yearly": "pro_yearly",
    },
}

# Billing webhook handlers
def handle_stripe_webhook(event_type: str, data: dict) -> bool:
    """Handle Stripe webhook events"""
    try:
        if event_type == "customer.subscription.created":
            # Handle new subscription
            subscription_id = data["id"]
            customer_id = data["customer"]
            # Update user subscription in database
            return True
            
        elif event_type == "customer.subscription.updated":
            # Handle subscription update
            subscription_id = data["id"]
            status = data["status"]
            # Update subscription status
            return True
            
        elif event_type == "customer.subscription.deleted":
            # Handle subscription cancellation
            subscription_id = data["id"]
            # Cancel subscription
            return True
            
        elif event_type == "invoice.payment_succeeded":
            # Handle successful payment
            subscription_id = data["subscription"]
            # Update payment status
            return True
            
        elif event_type == "invoice.payment_failed":
            # Handle failed payment
            subscription_id = data["subscription"]
            # Handle payment failure
            return True
            
    except Exception as e:
        print(f"Error handling Stripe webhook: {e}")
        return False
    
    return False

def handle_revenuecat_webhook(event_type: str, data: dict) -> bool:
    """Handle RevenueCat webhook events"""
    try:
        if event_type == "INITIAL_PURCHASE":
            # Handle initial purchase
            user_id = data["app_user_id"]
            product_id = data["product_id"]
            # Grant access to features
            return True
            
        elif event_type == "RENEWAL":
            # Handle subscription renewal
            user_id = data["app_user_id"]
            product_id = data["product_id"]
            # Extend subscription
            return True
            
        elif event_type == "CANCELLATION":
            # Handle subscription cancellation
            user_id = data["app_user_id"]
            # Revoke access at end of period
            return True
            
    except Exception as e:
        print(f"Error handling RevenueCat webhook: {e}")
        return False
    
    return False
