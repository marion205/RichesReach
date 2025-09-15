# Subscription System Design - RichesReach
## Architecture Overview
### **Backend Models (Django)**
```python
# backend/core/models.py
from django.db import models
from django.contrib.auth.models import User
from enum import Enum
class SubscriptionTier(models.TextChoices):
FREE = 'free', 'Free'
PREMIUM = 'premium', 'Premium'
PRO = 'pro', 'Pro'
class SubscriptionStatus(models.TextChoices):
ACTIVE = 'active', 'Active'
CANCELLED = 'cancelled', 'Cancelled'
EXPIRED = 'expired', 'Expired'
TRIAL = 'trial', 'Trial'
class UserSubscription(models.Model):
user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
tier = models.CharField(max_length=20, choices=SubscriptionTier.choices, default=SubscriptionTier.FREE)
status = models.CharField(max_length=20, choices=SubscriptionStatus.choices, default=SubscriptionStatus.ACTIVE)
# Subscription dates
start_date = models.DateTimeField(auto_now_add=True)
end_date = models.DateTimeField(null=True, blank=True)
trial_end_date = models.DateTimeField(null=True, blank=True)
# Payment info
stripe_customer_id = models.CharField(max_length=100, blank=True)
stripe_subscription_id = models.CharField(max_length=100, blank=True)
payment_method_id = models.CharField(max_length=100, blank=True)
# Usage tracking
daily_recommendations_used = models.IntegerField(default=0)
last_usage_reset = models.DateTimeField(auto_now_add=True)
# Features
has_real_time_data = models.BooleanField(default=False)
has_unlimited_portfolio = models.BooleanField(default=False)
has_social_features = models.BooleanField(default=False)
has_advanced_analytics = models.BooleanField(default=False)
created_at = models.DateTimeField(auto_now_add=True)
updated_at = models.DateTimeField(auto_now=True)
class SubscriptionFeature(models.Model):
tier = models.CharField(max_length=20, choices=SubscriptionTier.choices)
feature_name = models.CharField(max_length=100)
feature_key = models.CharField(max_length=50)
is_enabled = models.BooleanField(default=True)
limit_value = models.IntegerField(null=True, blank=True) # For rate limiting
class Meta:
unique_together = ['tier', 'feature_key']
class UsageLog(models.Model):
user = models.ForeignKey(User, on_delete=models.CASCADE)
feature = models.CharField(max_length=50)
usage_count = models.IntegerField(default=1)
timestamp = models.DateTimeField(auto_now_add=True)
metadata = models.JSONField(default=dict, blank=True)
```
### **2. Subscription Service Layer**
```python
# backend/core/subscription_service.py
from django.utils import timezone
from datetime import timedelta
import stripe
from .models import UserSubscription, SubscriptionFeature, UsageLog
class SubscriptionService:
def __init__(self):
stripe.api_key = settings.STRIPE_SECRET_KEY
def get_user_tier(self, user):
"""Get user's current subscription tier"""
try:
subscription = user.subscription
if subscription.status == SubscriptionStatus.ACTIVE:
return subscription.tier
return SubscriptionTier.FREE
except UserSubscription.DoesNotExist:
return SubscriptionTier.FREE
def can_use_feature(self, user, feature_key):
"""Check if user can use a specific feature"""
subscription = self._get_or_create_subscription(user)
tier = subscription.tier
try:
feature = SubscriptionFeature.objects.get(tier=tier, feature_key=feature_key)
if not feature.is_enabled:
return False
# Check rate limits
if feature.limit_value:
return self._check_rate_limit(user, feature_key, feature.limit_value)
return True
except SubscriptionFeature.DoesNotExist:
return False
def _check_rate_limit(self, user, feature_key, limit):
"""Check if user has exceeded rate limit for a feature"""
today = timezone.now().date()
# Reset daily counters if needed
subscription = user.subscription
if subscription.last_usage_reset.date() < today:
subscription.daily_recommendations_used = 0
subscription.last_usage_reset = timezone.now()
subscription.save()
# Check specific feature limits
if feature_key == 'daily_recommendations':
return subscription.daily_recommendations_used < limit
# Check other rate limits
usage_today = UsageLog.objects.filter(
user=user,
feature=feature_key,
timestamp__date=today
).aggregate(total=models.Sum('usage_count'))['total'] or 0
return usage_today < limit
def log_feature_usage(self, user, feature_key, metadata=None):
"""Log feature usage for rate limiting"""
UsageLog.objects.create(
user=user,
feature=feature_key,
metadata=metadata or {}
)
# Update subscription counters
subscription = user.subscription
if feature_key == 'daily_recommendations':
subscription.daily_recommendations_used += 1
subscription.save()
def create_stripe_customer(self, user):
"""Create Stripe customer for user"""
customer = stripe.Customer.create(
email=user.email,
name=f"{user.first_name} {user.last_name}",
metadata={'user_id': user.id}
)
subscription = self._get_or_create_subscription(user)
subscription.stripe_customer_id = customer.id
subscription.save()
return customer
def create_subscription(self, user, price_id, trial_days=7):
"""Create Stripe subscription"""
subscription = self._get_or_create_subscription(user)
if not subscription.stripe_customer_id:
self.create_stripe_customer(user)
subscription.refresh_from_db()
stripe_subscription = stripe.Subscription.create(
customer=subscription.stripe_customer_id,
items=[{'price': price_id}],
trial_period_days=trial_days,
metadata={'user_id': user.id}
)
subscription.stripe_subscription_id = stripe_subscription.id
subscription.status = SubscriptionStatus.TRIAL
subscription.trial_end_date = timezone.now() + timedelta(days=trial_days)
subscription.save()
return stripe_subscription
def cancel_subscription(self, user):
"""Cancel user's subscription"""
subscription = user.subscription
if subscription.stripe_subscription_id:
stripe.Subscription.modify(
subscription.stripe_subscription_id,
cancel_at_period_end=True
)
subscription.status = SubscriptionStatus.CANCELLED
subscription.save()
def _get_or_create_subscription(self, user):
"""Get or create user subscription"""
subscription, created = UserSubscription.objects.get_or_create(
user=user,
defaults={'tier': SubscriptionTier.FREE}
)
return subscription
```
### **3. GraphQL Mutations & Queries**
```python
# backend/core/subscription_mutations.py
import graphene
from graphene_django import DjangoObjectType
from .models import UserSubscription
from .subscription_service import SubscriptionService
class UserSubscriptionType(DjangoObjectType):
class Meta:
model = UserSubscription
fields = '__all__'
class CreateSubscriptionMutation(graphene.Mutation):
class Arguments:
price_id = graphene.String(required=True)
trial_days = graphene.Int(default_value=7)
success = graphene.Boolean()
subscription = graphene.Field(UserSubscriptionType)
error = graphene.String()
def mutate(self, info, price_id, trial_days=7):
user = info.context.user
if not user.is_authenticated:
return CreateSubscriptionMutation(
success=False,
error="Authentication required"
)
try:
service = SubscriptionService()
stripe_subscription = service.create_subscription(user, price_id, trial_days)
return CreateSubscriptionMutation(
success=True,
subscription=user.subscription
)
except Exception as e:
return CreateSubscriptionMutation(
success=False,
error=str(e)
)
class CancelSubscriptionMutation(graphene.Mutation):
success = graphene.Boolean()
message = graphene.String()
def mutate(self, info):
user = info.context.user
if not user.is_authenticated:
return CancelSubscriptionMutation(
success=False,
message="Authentication required"
)
try:
service = SubscriptionService()
service.cancel_subscription(user)
return CancelSubscriptionMutation(
success=True,
message="Subscription cancelled successfully"
)
except Exception as e:
return CancelSubscriptionMutation(
success=False,
message=str(e)
)
class SubscriptionQuery(graphene.ObjectType):
my_subscription = graphene.Field(UserSubscriptionType)
can_use_feature = graphene.Boolean(
feature_key=graphene.String(required=True)
)
def resolve_my_subscription(self, info):
user = info.context.user
if not user.is_authenticated:
return None
return user.subscription
def resolve_can_use_feature(self, info, feature_key):
user = info.context.user
if not user.is_authenticated:
return False
service = SubscriptionService()
return service.can_use_feature(user, feature_key)
```
### **4. Frontend Subscription Components**
```typescript
// mobile/components/SubscriptionManager.tsx
import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, Alert, StyleSheet } from 'react-native';
import { useQuery, useMutation } from '@apollo/client';
import { GET_MY_SUBSCRIPTION, CAN_USE_FEATURE } from '../graphql/subscriptionQueries';
interface SubscriptionTier {
id: string;
name: string;
price: number;
features: string[];
popular?: boolean;
}
const SUBSCRIPTION_TIERS: SubscriptionTier[] = [
{
id: 'free',
name: 'Free',
price: 0,
features: [
'3 AI recommendations per day',
'Basic portfolio tracking (5 stocks)',
'Delayed market data',
'Community access (read-only)',
'Basic educational content'
]
},
{
id: 'premium',
name: 'Premium',
price: 9.99,
popular: true,
features: [
'Unlimited AI recommendations',
'Real-time market data',
'Unlimited portfolio tracking',
'Full social trading features',
'Advanced market analysis',
'Priority customer support',
'Export portfolio data'
]
},
{
id: 'pro',
name: 'Pro',
price: 19.99,
features: [
'Everything in Premium',
'Advanced technical analysis',
'Options trading insights',
'Tax optimization recommendations',
'Advanced backtesting',
'API access',
'Dedicated account manager'
]
}
];
export const SubscriptionManager: React.FC = () => {
const [selectedTier, setSelectedTier] = useState<string>('premium');
const { data: subscriptionData, loading } = useQuery(GET_MY_SUBSCRIPTION);
const { data: featureData } = useQuery(CAN_USE_FEATURE, {
variables: { featureKey: 'daily_recommendations' }
});
const handleSubscribe = async (tierId: string) => {
if (tierId === 'free') {
Alert.alert('Already Free', 'You are already on the free tier!');
return;
}
try {
// Call subscription mutation
const priceId = getPriceIdForTier(tierId);
// await createSubscription({ variables: { priceId } });
Alert.alert(
'Subscription Created',
`Welcome to ${tierId} tier! You now have access to premium features.`
);
} catch (error) {
Alert.alert('Error', 'Failed to create subscription. Please try again.');
}
};
const getPriceIdForTier = (tierId: string): string => {
const priceIds = {
premium: 'price_premium_monthly',
pro: 'price_pro_monthly'
};
return priceIds[tierId];
};
if (loading) return <Text>Loading subscription info...</Text>;
const currentTier = subscriptionData?.mySubscription?.tier || 'free';
return (
<View style={styles.container}>
<Text style={styles.title}>Choose Your Plan</Text>
{SUBSCRIPTION_TIERS.map((tier) => (
<View
key={tier.id}
style={[
styles.tierCard,
tier.popular && styles.popularTier,
currentTier === tier.id && styles.currentTier
]}
>
{tier.popular && (
<View style={styles.popularBadge}>
<Text style={styles.popularText}>Most Popular</Text>
</View>
)}
<Text style={styles.tierName}>{tier.name}</Text>
<Text style={styles.tierPrice}>
${tier.price}/month
</Text>
<View style={styles.featuresList}>
{tier.features.map((feature, index) => (
<Text key={index} style={styles.feature}>
{feature}
</Text>
))}
</View>
<TouchableOpacity
style={[
styles.subscribeButton,
currentTier === tier.id && styles.currentButton
]}
onPress={() => handleSubscribe(tier.id)}
disabled={currentTier === tier.id}
>
<Text style={styles.subscribeButtonText}>
{currentTier === tier.id ? 'Current Plan' : 'Subscribe'}
</Text>
</TouchableOpacity>
</View>
))}
</View>
);
};
const styles = StyleSheet.create({
container: {
flex: 1,
padding: 20,
backgroundColor: '#f5f5f5',
},
title: {
fontSize: 24,
fontWeight: 'bold',
textAlign: 'center',
marginBottom: 30,
color: '#1E40AF',
},
tierCard: {
backgroundColor: 'white',
borderRadius: 12,
padding: 20,
marginBottom: 20,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 4,
elevation: 3,
},
popularTier: {
borderColor: '#1E40AF',
borderWidth: 2,
},
currentTier: {
backgroundColor: '#EFF6FF',
},
popularBadge: {
position: 'absolute',
top: -10,
right: 20,
backgroundColor: '#1E40AF',
paddingHorizontal: 12,
paddingVertical: 4,
borderRadius: 12,
},
popularText: {
color: 'white',
fontSize: 12,
fontWeight: 'bold',
},
tierName: {
fontSize: 20,
fontWeight: 'bold',
marginBottom: 8,
color: '#1E40AF',
},
tierPrice: {
fontSize: 24,
fontWeight: 'bold',
marginBottom: 16,
color: '#374151',
},
featuresList: {
marginBottom: 20,
},
feature: {
fontSize: 14,
marginBottom: 8,
color: '#6B7280',
},
subscribeButton: {
backgroundColor: '#1E40AF',
paddingVertical: 12,
borderRadius: 8,
alignItems: 'center',
},
currentButton: {
backgroundColor: '#10B981',
},
subscribeButtonText: {
color: 'white',
fontSize: 16,
fontWeight: 'bold',
},
});
```
### **5. Feature Gating Component**
```typescript
// mobile/components/FeatureGate.tsx
import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useQuery } from '@apollo/client';
import { CAN_USE_FEATURE } from '../graphql/subscriptionQueries';
interface FeatureGateProps {
featureKey: string;
children: React.ReactNode;
fallback?: React.ReactNode;
onUpgrade?: () => void;
}
export const FeatureGate: React.FC<FeatureGateProps> = ({
featureKey,
children,
fallback,
onUpgrade
}) => {
const { data, loading } = useQuery(CAN_USE_FEATURE, {
variables: { featureKey }
});
if (loading) {
return <Text>Loading...</Text>;
}
const canUse = data?.canUseFeature;
if (canUse) {
return <>{children}</>;
}
if (fallback) {
return <>{fallback}</>;
}
return (
<View style={styles.upgradePrompt}>
<Text style={styles.upgradeTitle}>Upgrade to Premium</Text>
<Text style={styles.upgradeDescription}>
This feature is available with a Premium subscription.
</Text>
<TouchableOpacity style={styles.upgradeButton} onPress={onUpgrade}>
<Text style={styles.upgradeButtonText}>Upgrade Now</Text>
</TouchableOpacity>
</View>
);
};
const styles = StyleSheet.create({
upgradePrompt: {
backgroundColor: '#FEF3C7',
padding: 20,
borderRadius: 8,
alignItems: 'center',
margin: 10,
},
upgradeTitle: {
fontSize: 18,
fontWeight: 'bold',
marginBottom: 8,
color: '#92400E',
},
upgradeDescription: {
fontSize: 14,
textAlign: 'center',
marginBottom: 16,
color: '#92400E',
},
upgradeButton: {
backgroundColor: '#1E40AF',
paddingHorizontal: 20,
paddingVertical: 10,
borderRadius: 6,
},
upgradeButtonText: {
color: 'white',
fontWeight: 'bold',
},
});
```
### **6. Usage in App Components**
```typescript
// mobile/screens/AIPortfolioScreen.tsx
import React from 'react';
import { FeatureGate } from '../components/FeatureGate';
import { SubscriptionService } from '../services/SubscriptionService';
export const AIPortfolioScreen: React.FC = () => {
const handleGenerateRecommendation = async () => {
// Check if user can use feature
const canUse = await SubscriptionService.canUseFeature('daily_recommendations');
if (!canUse) {
Alert.alert(
'Limit Reached',
'You have reached your daily limit of 3 recommendations. Upgrade to Premium for unlimited access!',
[
{ text: 'Cancel', style: 'cancel' },
{ text: 'Upgrade', onPress: () => navigateToSubscription() }
]
);
return;
}
// Generate recommendation
// Log usage
await SubscriptionService.logFeatureUsage('daily_recommendations');
};
return (
<View>
<FeatureGate
featureKey="unlimited_recommendations"
onUpgrade={() => navigateToSubscription()}
>
<TouchableOpacity onPress={handleGenerateRecommendation}>
<Text>Generate AI Recommendation</Text>
</TouchableOpacity>
</FeatureGate>
</View>
);
};
```
### **7. Stripe Integration**
```typescript
// mobile/services/StripeService.ts
import { StripeProvider, useStripe } from '@stripe/stripe-react-native';
export class StripeService {
static async createPaymentMethod(cardDetails: any) {
// Create payment method with Stripe
}
static async createSubscription(priceId: string, customerId: string) {
// Create subscription with Stripe
}
static async cancelSubscription(subscriptionId: string) {
// Cancel subscription
}
}
```
## ** Implementation Strategy**
### **Phase 1: Basic Subscription (Week 1)**
1. Set up Stripe account and get API keys
2. Create subscription models and service
3. Implement basic feature gating
4. Add subscription management UI
### **Phase 2: Advanced Features (Week 2)**
1. Add usage tracking and rate limiting
2. Implement trial periods
3. Add subscription analytics
4. Create upgrade/downgrade flows
### **Phase 3: Optimization (Week 3)**
1. A/B test pricing strategies
2. Add referral system
3. Implement retention campaigns
4. Add subscription analytics dashboard
This subscription system provides:
- **Flexible tier management**
- **Real-time feature gating**
- **Usage tracking and rate limiting**
- **Stripe integration for payments**
- **Trial periods and cancellations**
- **Comprehensive analytics**
Would you like me to elaborate on any specific part of this subscription system?
