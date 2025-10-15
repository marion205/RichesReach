import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { useAuth } from '../contexts/AuthContext';

interface SubscriptionPlan {
  tier: string;
  name: string;
  price_monthly: number;
  price_yearly: number;
  features: string[];
  max_portfolio_value?: number;
  max_trades_per_month?: number;
  priority_support: boolean;
  advanced_analytics: boolean;
  api_access: boolean;
}

interface CurrentSubscription {
  tier: string;
  status: string;
  start_date?: string;
  end_date?: string;
  auto_renew: boolean;
  features: string[];
  plan: SubscriptionPlan;
}

const SubscriptionScreen: React.FC = () => {
  const { token } = useAuth();
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [currentSubscription, setCurrentSubscription] = useState<CurrentSubscription | null>(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedBillingCycle, setSelectedBillingCycle] = useState<'monthly' | 'yearly'>('monthly');

  const loadData = async () => {
    if (!token) {
      Alert.alert('Authentication Required', 'Please log in to view subscription options.');
      return;
    }

    setLoading(true);
    try {
      const [plansResponse, subscriptionResponse] = await Promise.allSettled([
        fetch('http://riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com/api/billing/plans/', {
          headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json',
          },
        }),
        fetch('http://riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com/api/billing/subscription/', {
          headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json',
          },
        }),
      ]);

      if (plansResponse.status === 'fulfilled' && plansResponse.value.ok) {
        const plansData = await plansResponse.value.json();
        setPlans(plansData.plans || []);
      }

      if (subscriptionResponse.status === 'fulfilled' && subscriptionResponse.value.ok) {
        const subscriptionData = await subscriptionResponse.value.json();
        setCurrentSubscription(subscriptionData.subscription || null);
      }
    } catch (error) {
      console.error('Error loading subscription data:', error);
      Alert.alert('Error', 'Failed to load subscription data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const handleSubscribe = async (tier: string) => {
    if (!token) {
      Alert.alert('Authentication Required', 'Please log in to subscribe.');
      return;
    }

    try {
      const response = await fetch('http://riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com/api/billing/subscribe/', {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tier: tier,
          billing_cycle: selectedBillingCycle,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        Alert.alert('Success', 'Subscription created successfully!');
        loadData(); // Refresh data
      } else {
        const errorData = await response.json();
        Alert.alert('Error', errorData.error || 'Failed to create subscription.');
      }
    } catch (error) {
      console.error('Error creating subscription:', error);
      Alert.alert('Error', 'Failed to create subscription. Please try again.');
    }
  };

  const handleCancel = async () => {
    if (!token) {
      Alert.alert('Authentication Required', 'Please log in to cancel subscription.');
      return;
    }

    Alert.alert(
      'Cancel Subscription',
      'Are you sure you want to cancel your subscription? You will lose access to premium features at the end of your billing period.',
      [
        { text: 'Keep Subscription', style: 'cancel' },
        {
          text: 'Cancel Subscription',
          style: 'destructive',
          onPress: async () => {
            try {
              const response = await fetch('http://riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com/api/billing/cancel/', {
                method: 'POST',
                headers: {
                  'Authorization': `Token ${token}`,
                  'Content-Type': 'application/json',
                },
              });

              if (response.ok) {
                Alert.alert('Success', 'Subscription will be cancelled at the end of your billing period.');
                loadData(); // Refresh data
              } else {
                const errorData = await response.json();
                Alert.alert('Error', errorData.error || 'Failed to cancel subscription.');
              }
            } catch (error) {
              console.error('Error cancelling subscription:', error);
              Alert.alert('Error', 'Failed to cancel subscription. Please try again.');
            }
          },
        },
      ]
    );
  };

  useEffect(() => {
    loadData();
  }, [token]);

  const renderPlan = (plan: SubscriptionPlan) => {
    const isCurrentPlan = currentSubscription?.tier === plan.tier;
    const isFree = plan.tier === 'free';
    const price = selectedBillingCycle === 'yearly' ? plan.price_yearly : plan.price_monthly;
    const savings = selectedBillingCycle === 'yearly' && plan.price_yearly > 0 
      ? Math.round((1 - plan.price_yearly / (plan.price_monthly * 12)) * 100)
      : 0;

    return (
      <View key={plan.tier} style={[styles.planCard, isCurrentPlan && styles.currentPlanCard]}>
        {isCurrentPlan && (
          <View style={styles.currentPlanBadge}>
            <Text style={styles.currentPlanText}>Current Plan</Text>
          </View>
        )}
        
        <Text style={styles.planName}>{plan.name}</Text>
        
        {!isFree && (
          <View style={styles.priceContainer}>
            <Text style={styles.price}>${price.toFixed(2)}</Text>
            <Text style={styles.billingCycle}>
              /{selectedBillingCycle === 'yearly' ? 'year' : 'month'}
            </Text>
            {savings > 0 && (
              <Text style={styles.savings}>Save {savings}%</Text>
            )}
          </View>
        )}
        
        {isFree && (
          <Text style={styles.freePrice}>Free</Text>
        )}

        <View style={styles.featuresContainer}>
          {plan.features.map((feature, index) => (
            <Text key={index} style={styles.feature}>
              ✓ {feature}
            </Text>
          ))}
        </View>

        {plan.max_portfolio_value && (
          <Text style={styles.limit}>
            Portfolio limit: ${plan.max_portfolio_value.toLocaleString()}
          </Text>
        )}

        {plan.max_trades_per_month && (
          <Text style={styles.limit}>
            Trades per month: {plan.max_trades_per_month}
          </Text>
        )}

        {!isCurrentPlan && !isFree && (
          <TouchableOpacity
            style={styles.subscribeButton}
            onPress={() => handleSubscribe(plan.tier)}
          >
            <Text style={styles.subscribeButtonText}>
              Subscribe to {plan.name}
            </Text>
          </TouchableOpacity>
        )}

        {isCurrentPlan && !isFree && (
          <TouchableOpacity
            style={styles.cancelButton}
            onPress={handleCancel}
          >
            <Text style={styles.cancelButtonText}>Cancel Subscription</Text>
          </TouchableOpacity>
        )}
      </View>
    );
  };

  if (loading && !refreshing) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading subscription options...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <Text style={styles.title}>Subscription Plans</Text>
      <Text style={styles.subtitle}>Choose the plan that's right for you</Text>

      {currentSubscription && (
        <View style={styles.currentSubscriptionCard}>
          <Text style={styles.currentSubscriptionTitle}>Current Subscription</Text>
          <Text style={styles.currentSubscriptionTier}>{currentSubscription.plan.name}</Text>
          <Text style={styles.currentSubscriptionStatus}>
            Status: {currentSubscription.status}
          </Text>
          {currentSubscription.end_date && (
            <Text style={styles.currentSubscriptionEnd}>
              Renews: {new Date(currentSubscription.end_date).toLocaleDateString()}
            </Text>
          )}
        </View>
      )}

      <View style={styles.billingCycleContainer}>
        <TouchableOpacity
          style={[
            styles.billingCycleButton,
            selectedBillingCycle === 'monthly' && styles.selectedBillingCycleButton,
          ]}
          onPress={() => setSelectedBillingCycle('monthly')}
        >
          <Text
            style={[
              styles.billingCycleText,
              selectedBillingCycle === 'monthly' && styles.selectedBillingCycleText,
            ]}
          >
            Monthly
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[
            styles.billingCycleButton,
            selectedBillingCycle === 'yearly' && styles.selectedBillingCycleButton,
          ]}
          onPress={() => setSelectedBillingCycle('yearly')}
        >
          <Text
            style={[
              styles.billingCycleText,
              selectedBillingCycle === 'yearly' && styles.selectedBillingCycleText,
            ]}
          >
            Yearly
          </Text>
        </TouchableOpacity>
      </View>

      {plans.map(renderPlan)}

      <View style={styles.infoContainer}>
        <Text style={styles.infoTitle}>Why Upgrade?</Text>
        <Text style={styles.infoText}>
          • Advanced tax optimization tools to minimize your tax burden
        </Text>
        <Text style={styles.infoText}>
          • Smart lot optimization to maximize after-tax returns
        </Text>
        <Text style={styles.infoText}>
          • Priority customer support and advanced analytics
        </Text>
        <Text style={styles.infoText}>
          • Cancel anytime with no long-term commitments
        </Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 16,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 24,
  },
  currentSubscriptionCard: {
    backgroundColor: '#e8f5e8',
    padding: 16,
    borderRadius: 12,
    marginBottom: 24,
    borderWidth: 2,
    borderColor: '#4caf50',
  },
  currentSubscriptionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2e7d32',
    marginBottom: 8,
  },
  currentSubscriptionTier: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#2e7d32',
    marginBottom: 4,
  },
  currentSubscriptionStatus: {
    fontSize: 14,
    color: '#2e7d32',
    marginBottom: 4,
  },
  currentSubscriptionEnd: {
    fontSize: 14,
    color: '#2e7d32',
  },
  billingCycleContainer: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 4,
    marginBottom: 24,
  },
  billingCycleButton: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    borderRadius: 6,
  },
  selectedBillingCycleButton: {
    backgroundColor: '#007AFF',
  },
  billingCycleText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#666',
  },
  selectedBillingCycleText: {
    color: '#fff',
  },
  planCard: {
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 12,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
    position: 'relative',
  },
  currentPlanCard: {
    borderWidth: 2,
    borderColor: '#007AFF',
  },
  currentPlanBadge: {
    position: 'absolute',
    top: -8,
    right: 16,
    backgroundColor: '#007AFF',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  currentPlanText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  planName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  priceContainer: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginBottom: 16,
  },
  price: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  billingCycle: {
    fontSize: 16,
    color: '#666',
    marginLeft: 4,
  },
  savings: {
    fontSize: 14,
    color: '#4caf50',
    fontWeight: 'bold',
    marginLeft: 8,
  },
  freePrice: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#4caf50',
    marginBottom: 16,
  },
  featuresContainer: {
    marginBottom: 16,
  },
  feature: {
    fontSize: 14,
    color: '#333',
    marginBottom: 8,
  },
  limit: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  subscribeButton: {
    backgroundColor: '#007AFF',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 8,
  },
  subscribeButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  cancelButton: {
    backgroundColor: '#ff4444',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 8,
  },
  cancelButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  infoContainer: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 24,
  },
  infoTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  infoText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
});

export default SubscriptionScreen;
