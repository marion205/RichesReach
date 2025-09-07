import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Dimensions,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

const { width } = Dimensions.get('window');

interface SubscriptionScreenProps {
  navigateTo: (screen: string) => void;
}

const SubscriptionScreen: React.FC<SubscriptionScreenProps> = ({ navigateTo }) => {
  const [selectedPlan, setSelectedPlan] = useState<'basic' | 'pro' | 'elite'>('pro');

  const plans = [
    {
      id: 'basic',
      name: 'Basic Premium',
      price: '$9.99',
      period: '/month',
      description: 'Perfect for individual investors',
      features: [
        'Advanced Portfolio Analytics',
        'Enhanced Stock Screening',
        'Basic AI Recommendations',
        'Risk Analysis Tools',
        'Sector Allocation Insights',
        'Performance Metrics'
      ],
      popular: false,
    },
    {
      id: 'pro',
      name: 'Pro Premium',
      price: '$19.99',
      period: '/month',
      description: 'For serious investors and traders',
      features: [
        'Everything in Basic',
        'AI-Powered Stock Recommendations',
        'Market Timing Signals',
        'Portfolio Rebalancing Alerts',
        'Advanced ML Features',
        'Options Flow Analysis',
        'Priority Support'
      ],
      popular: true,
    },
    {
      id: 'elite',
      name: 'Elite Premium',
      price: '$49.99',
      period: '/month',
      description: 'Professional-grade tools',
      features: [
        'Everything in Pro',
        'Real-time Options Analysis',
        'Advanced Charting Tools',
        'Backtesting Capabilities',
        'Expert Analyst Reports',
        'White-label Solutions',
        'Dedicated Account Manager'
      ],
      popular: false,
    },
  ];

  const handleSubscribe = (planId: string) => {
    Alert.alert(
      'Subscribe to Premium',
      `Are you ready to upgrade to ${plans.find(p => p.id === planId)?.name}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Subscribe', 
          onPress: () => {
            // In production, you'd integrate with Stripe/PayPal
            Alert.alert(
              'Success!',
              'Your premium subscription is now active. Enjoy your new features!',
              [{ text: 'OK', onPress: () => navigateTo('premium-analytics') }]
            );
          }
        }
      ]
    );
  };

  const renderPlanCard = (plan: any) => (
    <TouchableOpacity
      key={plan.id}
      style={[
        styles.planCard,
        selectedPlan === plan.id && styles.selectedPlan,
        plan.popular && styles.popularPlan
      ]}
      onPress={() => setSelectedPlan(plan.id)}
    >
      {plan.popular && (
        <View style={styles.popularBadge}>
          <Text style={styles.popularText}>Most Popular</Text>
        </View>
      )}
      
      <View style={styles.planHeader}>
        <Text style={styles.planName}>{plan.name}</Text>
        <View style={styles.priceContainer}>
          <Text style={styles.price}>{plan.price}</Text>
          <Text style={styles.period}>{plan.period}</Text>
        </View>
      </View>
      
      <Text style={styles.planDescription}>{plan.description}</Text>
      
      <View style={styles.featuresContainer}>
        {plan.features.map((feature: string, index: number) => (
          <View key={index} style={styles.featureItem}>
            <Icon name="check" size={16} color="#34C759" />
            <Text style={styles.featureText}>{feature}</Text>
          </View>
        ))}
      </View>
      
      <TouchableOpacity
        style={[
          styles.subscribeButton,
          selectedPlan === plan.id && styles.selectedSubscribeButton
        ]}
        onPress={() => handleSubscribe(plan.id)}
      >
        <Text style={[
          styles.subscribeButtonText,
          selectedPlan === plan.id && styles.selectedSubscribeButtonText
        ]}>
          {selectedPlan === plan.id ? 'Selected' : 'Select Plan'}
        </Text>
      </TouchableOpacity>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigateTo('profile')}>
          <Icon name="arrow-left" size={24} color="#000" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Premium Plans</Text>
        <View style={{ width: 24 }} />
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Hero Section */}
        <View style={styles.heroSection}>
          <View style={styles.heroIcon}>
            <Icon name="star" size={48} color="#FFD700" />
          </View>
          <Text style={styles.heroTitle}>Unlock Premium Features</Text>
          <Text style={styles.heroSubtitle}>
            Get advanced analytics, AI recommendations, and professional-grade tools
          </Text>
        </View>

        {/* Benefits Section */}
        <View style={styles.benefitsSection}>
          <Text style={styles.sectionTitle}>Why Choose Premium?</Text>
          <View style={styles.benefitsGrid}>
            <View style={styles.benefitItem}>
              <Icon name="trending-up" size={24} color="#34C759" />
              <Text style={styles.benefitTitle}>Better Returns</Text>
              <Text style={styles.benefitText}>
                Our AI models help you outperform the market
              </Text>
            </View>
            <View style={styles.benefitItem}>
              <Icon name="shield" size={24} color="#007AFF" />
              <Text style={styles.benefitTitle}>Risk Management</Text>
              <Text style={styles.benefitText}>
                Advanced risk analysis and portfolio optimization
              </Text>
            </View>
            <View style={styles.benefitItem}>
              <Icon name="zap" size={24} color="#FF9500" />
              <Text style={styles.benefitTitle}>Real-time Insights</Text>
              <Text style={styles.benefitText}>
                Get instant alerts and market signals
              </Text>
            </View>
            <View style={styles.benefitItem}>
              <Icon name="users" size={24} color="#AF52DE" />
              <Text style={styles.benefitTitle}>Expert Support</Text>
              <Text style={styles.benefitText}>
                Priority support from our financial experts
              </Text>
            </View>
          </View>
        </View>

        {/* Plans Section */}
        <View style={styles.plansSection}>
          <Text style={styles.sectionTitle}>Choose Your Plan</Text>
          <View style={styles.plansContainer}>
            {plans.map(renderPlanCard)}
          </View>
        </View>

        {/* Testimonials */}
        <View style={styles.testimonialsSection}>
          <Text style={styles.sectionTitle}>What Our Users Say</Text>
          <View style={styles.testimonialCard}>
            <View style={styles.testimonialHeader}>
              <View style={styles.testimonialAvatar}>
                <Text style={styles.testimonialInitial}>S</Text>
              </View>
              <View style={styles.testimonialInfo}>
                <Text style={styles.testimonialName}>Sarah Chen</Text>
                <Text style={styles.testimonialRole}>Portfolio Manager</Text>
              </View>
              <View style={styles.testimonialRating}>
                <Icon name="star" size={16} color="#FFD700" />
                <Icon name="star" size={16} color="#FFD700" />
                <Icon name="star" size={16} color="#FFD700" />
                <Icon name="star" size={16} color="#FFD700" />
                <Icon name="star" size={16} color="#FFD700" />
              </View>
            </View>
            <Text style={styles.testimonialText}>
              "RichesReach's AI recommendations have helped me achieve 15% better returns than the market average. The risk analysis tools are incredibly accurate."
            </Text>
          </View>
        </View>

        {/* FAQ Section */}
        <View style={styles.faqSection}>
          <Text style={styles.sectionTitle}>Frequently Asked Questions</Text>
          <View style={styles.faqItem}>
            <Text style={styles.faqQuestion}>Can I cancel anytime?</Text>
            <Text style={styles.faqAnswer}>
              Yes, you can cancel your subscription at any time. You'll continue to have access to premium features until the end of your billing period.
            </Text>
          </View>
          <View style={styles.faqItem}>
            <Text style={styles.faqQuestion}>Is there a free trial?</Text>
            <Text style={styles.faqAnswer}>
              Yes! All premium plans come with a 7-day free trial. No credit card required to start.
            </Text>
          </View>
          <View style={styles.faqItem}>
            <Text style={styles.faqQuestion}>What payment methods do you accept?</Text>
            <Text style={styles.faqAnswer}>
              We accept all major credit cards, PayPal, and Apple Pay for secure payments.
            </Text>
          </View>
        </View>

        {/* CTA Section */}
        <View style={styles.ctaSection}>
          <Text style={styles.ctaTitle}>Ready to Start?</Text>
          <Text style={styles.ctaSubtitle}>
            Join thousands of investors who are already using RichesReach to build wealth
          </Text>
          <TouchableOpacity
            style={styles.ctaButton}
            onPress={() => handleSubscribe(selectedPlan)}
          >
            <Text style={styles.ctaButtonText}>
              Start Free Trial - {plans.find(p => p.id === selectedPlan)?.name}
            </Text>
          </TouchableOpacity>
          <Text style={styles.ctaNote}>
            7-day free trial • Cancel anytime • No commitment
          </Text>
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
  },
  content: {
    flex: 1,
  },
  heroSection: {
    alignItems: 'center',
    paddingVertical: 40,
    paddingHorizontal: 20,
    backgroundColor: '#fff',
  },
  heroIcon: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#FFF8E1',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  heroTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#000',
    textAlign: 'center',
    marginBottom: 12,
  },
  heroSubtitle: {
    fontSize: 16,
    color: '#8E8E93',
    textAlign: 'center',
    lineHeight: 24,
  },
  benefitsSection: {
    padding: 20,
    backgroundColor: '#fff',
    marginTop: 20,
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: '600',
    color: '#000',
    marginBottom: 20,
    textAlign: 'center',
  },
  benefitsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  benefitItem: {
    width: (width - 60) / 2,
    alignItems: 'center',
    marginBottom: 24,
  },
  benefitTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    marginTop: 12,
    marginBottom: 8,
    textAlign: 'center',
  },
  benefitText: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
    lineHeight: 20,
  },
  plansSection: {
    padding: 20,
    backgroundColor: '#fff',
    marginTop: 20,
  },
  plansContainer: {
    gap: 16,
  },
  planCard: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 20,
    borderWidth: 2,
    borderColor: '#E5E5EA',
    position: 'relative',
  },
  selectedPlan: {
    borderColor: '#007AFF',
    backgroundColor: '#F0F8FF',
  },
  popularPlan: {
    borderColor: '#FFD700',
  },
  popularBadge: {
    position: 'absolute',
    top: -10,
    left: 20,
    right: 20,
    backgroundColor: '#FFD700',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 12,
    alignItems: 'center',
  },
  popularText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#000',
  },
  planHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  planName: {
    fontSize: 20,
    fontWeight: '600',
    color: '#000',
    flex: 1,
  },
  priceContainer: {
    alignItems: 'flex-end',
  },
  price: {
    fontSize: 24,
    fontWeight: '700',
    color: '#007AFF',
  },
  period: {
    fontSize: 14,
    color: '#8E8E93',
  },
  planDescription: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 20,
  },
  featuresContainer: {
    marginBottom: 20,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  featureText: {
    fontSize: 14,
    color: '#000',
    marginLeft: 8,
    flex: 1,
  },
  subscribeButton: {
    backgroundColor: '#F2F2F7',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  selectedSubscribeButton: {
    backgroundColor: '#007AFF',
  },
  subscribeButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#8E8E93',
  },
  selectedSubscribeButtonText: {
    color: '#fff',
  },
  testimonialsSection: {
    padding: 20,
    backgroundColor: '#fff',
    marginTop: 20,
  },
  testimonialCard: {
    backgroundColor: '#F8F9FA',
    padding: 20,
    borderRadius: 12,
  },
  testimonialHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  testimonialAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  testimonialInitial: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  testimonialInfo: {
    flex: 1,
  },
  testimonialName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
  },
  testimonialRole: {
    fontSize: 14,
    color: '#8E8E93',
  },
  testimonialRating: {
    flexDirection: 'row',
  },
  testimonialText: {
    fontSize: 16,
    color: '#000',
    lineHeight: 24,
    fontStyle: 'italic',
  },
  faqSection: {
    padding: 20,
    backgroundColor: '#fff',
    marginTop: 20,
  },
  faqItem: {
    marginBottom: 20,
  },
  faqQuestion: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    marginBottom: 8,
  },
  faqAnswer: {
    fontSize: 14,
    color: '#8E8E93',
    lineHeight: 20,
  },
  ctaSection: {
    padding: 40,
    backgroundColor: '#007AFF',
    alignItems: 'center',
    marginTop: 20,
  },
  ctaTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#fff',
    marginBottom: 12,
    textAlign: 'center',
  },
  ctaSubtitle: {
    fontSize: 16,
    color: '#B3D9FF',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 32,
  },
  ctaButton: {
    backgroundColor: '#fff',
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
    marginBottom: 16,
  },
  ctaButtonText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#007AFF',
    textAlign: 'center',
  },
  ctaNote: {
    fontSize: 14,
    color: '#B3D9FF',
    textAlign: 'center',
  },
});

export default SubscriptionScreen;
