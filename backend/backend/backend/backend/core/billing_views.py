"""
Billing Views for Premium Subscriptions
Handles subscription management, payments, and feature access
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
import json
import stripe
from .billing_config import (
    get_plan, get_all_plans, has_feature_access, get_available_features,
    get_upgrade_options, STRIPE_CONFIG, REVENUECAT_CONFIG
)
from .premium_models import PremiumSubscription, FeatureUsage
from django.contrib.auth import get_user_model

User = get_user_model()

# Configure Stripe
stripe.api_key = STRIPE_CONFIG["secret_key"]

@method_decorator(login_required, name='dispatch')
class SubscriptionPlansView(View):
    """Get available subscription plans"""
    
    def get(self, request):
        try:
            plans = get_all_plans()
            plans_data = []
            
            for tier, plan in plans.items():
                plans_data.append({
                    "tier": plan.tier.value,
                    "name": plan.name,
                    "price_monthly": plan.price_monthly,
                    "price_yearly": plan.price_yearly,
                    "features": plan.features,
                    "max_portfolio_value": plan.max_portfolio_value,
                    "max_trades_per_month": plan.max_trades_per_month,
                    "priority_support": plan.priority_support,
                    "advanced_analytics": plan.advanced_analytics,
                    "api_access": plan.api_access,
                })
            
            return JsonResponse({
                "success": True,
                "plans": plans_data
            })
            
        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": str(e)
            }, status=500)

@method_decorator(login_required, name='dispatch')
class CurrentSubscriptionView(View):
    """Get current user subscription"""
    
    def get(self, request):
        try:
            user = request.user
            
            # Get current subscription
            try:
                subscription = PremiumSubscription.objects.get(user=user)
                plan = get_plan(subscription.tier)
                
                return JsonResponse({
                    "success": True,
                    "subscription": {
                        "tier": subscription.tier,
                        "status": subscription.status,
                        "start_date": subscription.start_date.isoformat() if subscription.start_date else None,
                        "end_date": subscription.end_date.isoformat() if subscription.end_date else None,
                        "auto_renew": subscription.auto_renew,
                        "features": subscription.features,
                        "plan": {
                            "name": plan.name,
                            "price_monthly": plan.price_monthly,
                            "price_yearly": plan.price_yearly,
                            "features": plan.features,
                        }
                    }
                })
                
            except PremiumSubscription.DoesNotExist:
                # User has free tier
                free_plan = get_plan("free")
                return JsonResponse({
                    "success": True,
                    "subscription": {
                        "tier": "free",
                        "status": "active",
                        "features": free_plan.features,
                        "plan": {
                            "name": free_plan.name,
                            "price_monthly": free_plan.price_monthly,
                            "price_yearly": free_plan.price_yearly,
                            "features": free_plan.features,
                        }
                    }
                })
                
        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": str(e)
            }, status=500)

@method_decorator(login_required, name='dispatch')
class CreateSubscriptionView(View):
    """Create a new subscription"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            tier = data.get('tier')
            billing_cycle = data.get('billing_cycle', 'monthly')  # monthly or yearly
            
            if not tier or tier not in ['premium', 'pro']:
                return JsonResponse({
                    "success": False,
                    "error": "Invalid tier. Must be 'premium' or 'pro'"
                }, status=400)
            
            user = request.user
            plan = get_plan(tier)
            
            # Check if user already has a subscription
            try:
                existing_subscription = PremiumSubscription.objects.get(user=user)
                if existing_subscription.status == 'active':
                    return JsonResponse({
                        "success": False,
                        "error": "User already has an active subscription"
                    }, status=400)
            except PremiumSubscription.DoesNotExist:
                pass
            
            # Create Stripe customer if doesn't exist
            stripe_customer_id = getattr(user, 'stripe_customer_id', None)
            if not stripe_customer_id:
                customer = stripe.Customer.create(
                    email=user.email,
                    name=user.name,
                    metadata={'user_id': user.id}
                )
                stripe_customer_id = customer.id
                # Save customer ID to user model (you'll need to add this field)
                # user.stripe_customer_id = stripe_customer_id
                # user.save()
            
            # Create Stripe subscription
            price_key = f"{tier}_{billing_cycle}"
            price_id = REVENUECAT_CONFIG["products"].get(price_key)
            
            if not price_id:
                return JsonResponse({
                    "success": False,
                    "error": f"Price not found for {tier} {billing_cycle}"
                }, status=400)
            
            subscription = stripe.Subscription.create(
                customer=stripe_customer_id,
                items=[{
                    'price': price_id,
                }],
                trial_period_days=STRIPE_CONFIG["trial_period_days"],
                metadata={
                    'user_id': user.id,
                    'tier': tier,
                    'billing_cycle': billing_cycle
                }
            )
            
            # Create local subscription record
            local_subscription = PremiumSubscription.objects.create(
                user=user,
                tier=tier,
                status='trial',
                stripe_subscription_id=subscription.id,
                features=get_available_features(tier),
                auto_renew=True
            )
            
            return JsonResponse({
                "success": True,
                "subscription": {
                    "id": local_subscription.id,
                    "tier": local_subscription.tier,
                    "status": local_subscription.status,
                    "stripe_subscription_id": subscription.id,
                    "client_secret": subscription.latest_invoice.payment_intent.client_secret if subscription.latest_invoice else None
                }
            })
            
        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": str(e)
            }, status=500)

@method_decorator(login_required, name='dispatch')
class CancelSubscriptionView(View):
    """Cancel a subscription"""
    
    def post(self, request):
        try:
            user = request.user
            
            try:
                subscription = PremiumSubscription.objects.get(user=user)
            except PremiumSubscription.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "error": "No active subscription found"
                }, status=404)
            
            # Cancel Stripe subscription
            if subscription.stripe_subscription_id:
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True
                )
            
            # Update local subscription
            subscription.auto_renew = False
            subscription.save()
            
            return JsonResponse({
                "success": True,
                "message": "Subscription will be cancelled at the end of the current period"
            })
            
        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": str(e)
            }, status=500)

@method_decorator(login_required, name='dispatch')
class FeatureAccessView(View):
    """Check feature access for current user"""
    
    def get(self, request):
        try:
            user = request.user
            feature = request.GET.get('feature')
            
            if not feature:
                return JsonResponse({
                    "success": False,
                    "error": "Feature parameter is required"
                }, status=400)
            
            # Get user's subscription tier
            try:
                subscription = PremiumSubscription.objects.get(user=user)
                tier = subscription.tier
            except PremiumSubscription.DoesNotExist:
                tier = "free"
            
            # Check feature access
            has_access = has_feature_access(tier, feature)
            
            return JsonResponse({
                "success": True,
                "feature": feature,
                "tier": tier,
                "has_access": has_access
            })
            
        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": str(e)
            }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    """Handle Stripe webhook events"""
    try:
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_CONFIG["webhook_secret"]
            )
        except ValueError:
            return JsonResponse({"error": "Invalid payload"}, status=400)
        except stripe.error.SignatureVerificationError:
            return JsonResponse({"error": "Invalid signature"}, status=400)
        
        # Handle the event
        event_type = event['type']
        data = event['data']['object']
        
        success = handle_stripe_webhook(event_type, data)
        
        if success:
            return JsonResponse({"status": "success"})
        else:
            return JsonResponse({"status": "error"}, status=500)
            
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def revenuecat_webhook(request):
    """Handle RevenueCat webhook events"""
    try:
        payload = json.loads(request.body)
        event_type = payload.get('type')
        data = payload.get('data', {})
        
        success = handle_revenuecat_webhook(event_type, data)
        
        if success:
            return JsonResponse({"status": "success"})
        else:
            return JsonResponse({"status": "error"}, status=500)
            
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def handle_stripe_webhook(event_type: str, data: dict) -> bool:
    """Handle Stripe webhook events"""
    try:
        if event_type == "customer.subscription.created":
            # Handle new subscription
            subscription_id = data["id"]
            customer_id = data["customer"]
            metadata = data.get("metadata", {})
            user_id = metadata.get("user_id")
            
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                    subscription = PremiumSubscription.objects.get(user=user)
                    subscription.status = "active"
                    subscription.stripe_subscription_id = subscription_id
                    subscription.save()
                except (User.DoesNotExist, PremiumSubscription.DoesNotExist):
                    pass
            
            return True
            
        elif event_type == "customer.subscription.updated":
            # Handle subscription update
            subscription_id = data["id"]
            status = data["status"]
            
            try:
                subscription = PremiumSubscription.objects.get(stripe_subscription_id=subscription_id)
                subscription.status = status
                subscription.save()
            except PremiumSubscription.DoesNotExist:
                pass
            
            return True
            
        elif event_type == "customer.subscription.deleted":
            # Handle subscription cancellation
            subscription_id = data["id"]
            
            try:
                subscription = PremiumSubscription.objects.get(stripe_subscription_id=subscription_id)
                subscription.status = "cancelled"
                subscription.save()
            except PremiumSubscription.DoesNotExist:
                pass
            
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
            
            # Map product ID to tier
            tier_mapping = {
                "premium_monthly": "premium",
                "premium_yearly": "premium",
                "pro_monthly": "pro",
                "pro_yearly": "pro",
            }
            
            tier = tier_mapping.get(product_id)
            if tier:
                try:
                    user = User.objects.get(id=user_id)
                    subscription, created = PremiumSubscription.objects.get_or_create(
                        user=user,
                        defaults={
                            "tier": tier,
                            "status": "active",
                            "features": get_available_features(tier),
                            "auto_renew": True
                        }
                    )
                    if not created:
                        subscription.tier = tier
                        subscription.status = "active"
                        subscription.features = get_available_features(tier)
                        subscription.save()
                except User.DoesNotExist:
                    pass
            
            return True
            
        elif event_type == "RENEWAL":
            # Handle subscription renewal
            user_id = data["app_user_id"]
            
            try:
                user = User.objects.get(id=user_id)
                subscription = PremiumSubscription.objects.get(user=user)
                subscription.status = "active"
                subscription.save()
            except (User.DoesNotExist, PremiumSubscription.DoesNotExist):
                pass
            
            return True
            
        elif event_type == "CANCELLATION":
            # Handle subscription cancellation
            user_id = data["app_user_id"]
            
            try:
                user = User.objects.get(id=user_id)
                subscription = PremiumSubscription.objects.get(user=user)
                subscription.status = "cancelled"
                subscription.save()
            except (User.DoesNotExist, PremiumSubscription.DoesNotExist):
                pass
            
            return True
            
    except Exception as e:
        print(f"Error handling RevenueCat webhook: {e}")
        return False
    
    return False
