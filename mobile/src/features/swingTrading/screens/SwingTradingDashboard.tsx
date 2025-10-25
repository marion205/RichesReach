import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  ScrollView,
  Alert,
} from 'react-native';
import { Feather as Icon } from '@expo/vector-icons';
import LinearGradient from 'expo-linear-gradient';

interface SwingTradingDashboardProps {
  navigateTo: (screen: string) => void;
}

const SwingTradingDashboard: React.FC<SwingTradingDashboardProps> = ({ navigateTo }) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'features'>('overview');

  const features = [
    {
      id: 'signals',
      title: 'Live Signals',
      description: 'AI-powered trading signals',
      details: 'ML scores • Real-time',
      icon: 'activity',
      color: '#FF6B35',
      onPress: () => navigateTo('swing-signals'),
    },
    {
      id: 'risk-coach',
      title: 'Risk Coach',
      description: 'Position sizing & risk management',
      details: 'Calculator • Analysis',
      icon: 'shield',
      color: '#10B981',
      onPress: () => navigateTo('swing-risk-coach'),
    },
    {
      id: 'backtesting',
      title: 'Backtesting',
      description: 'Test strategies with historical data',
      details: 'Performance • Analytics',
      icon: 'bar-chart-2',
      color: '#3B82F6',
      onPress: () => navigateTo('swing-backtesting'),
    },
    {
      id: 'leaderboard',
      title: 'Leaderboard',
      description: 'Top traders & performance rankings',
      details: 'Community • Competition',
      icon: 'award',
      color: '#F59E0B',
      onPress: () => navigateTo('swing-leaderboard'),
    },
  ];

  const renderHeader = () => (
    <View style={styles.header}>
      <TouchableOpacity
        style={styles.backButton}
        onPress={() => navigateTo('home')}
      >
        <Icon name="arrow-left" size={24} color="#6B7280" />
      </TouchableOpacity>
      <View style={styles.headerTitleContainer}>
        <Icon name="trending-up" size={24} color="#FF6B35" />
        <Text style={styles.headerTitle}>Swing Trading</Text>
      </View>
      <TouchableOpacity
        style={styles.helpButton}
        onPress={() => Alert.alert(
          'Swing Trading',
          'Swing trading involves holding positions for several days to weeks, capturing price swings in trending markets. Use our tools to identify opportunities and manage risk.'
        )}
      >
        <Icon name="help-circle" size={20} color="#6B7280" />
      </TouchableOpacity>
    </View>
  );

  const renderOverview = () => (
    <View style={styles.overviewContainer}>
      <View style={styles.welcomeCard}>
        <LinearGradient
          colors={['#FF6B35', '#FF8E53']}
          style={styles.welcomeGradient}
        >
          <Text style={styles.welcomeTitle}>Welcome to Swing Trading</Text>
          <Text style={styles.welcomeDescription}>
            Master the art of capturing multi-day price movements with our comprehensive suite of tools
          </Text>
        </LinearGradient>
      </View>

      <View style={styles.statsContainer}>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>24</Text>
          <Text style={styles.statLabel}>Active Signals</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>87%</Text>
          <Text style={styles.statLabel}>Win Rate</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>+12.5%</Text>
          <Text style={styles.statLabel}>This Month</Text>
        </View>
      </View>

      <View style={styles.quickActionsContainer}>
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        <View style={styles.quickActionsGrid}>
          <TouchableOpacity
            style={styles.quickActionCard}
            onPress={() => navigateTo('swing-signals')}
          >
            <Icon name="activity" size={24} color="#FF6B35" />
            <Text style={styles.quickActionText}>View Signals</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.quickActionCard}
            onPress={() => navigateTo('swing-risk-coach')}
          >
            <Icon name="shield" size={24} color="#10B981" />
            <Text style={styles.quickActionText}>Risk Calculator</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.quickActionCard}
            onPress={() => navigateTo('swing-backtesting')}
          >
            <Icon name="bar-chart-2" size={24} color="#3B82F6" />
            <Text style={styles.quickActionText}>Backtest</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.quickActionCard}
            onPress={() => navigateTo('swing-leaderboard')}
          >
            <Icon name="award" size={24} color="#F59E0B" />
            <Text style={styles.quickActionText}>Leaderboard</Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );

  const renderFeatures = () => (
    <View style={styles.featuresContainer}>
      <Text style={styles.sectionTitle}>All Features</Text>
      {features.map((feature) => (
        <TouchableOpacity
          key={feature.id}
          style={styles.featureCard}
          onPress={feature.onPress}
        >
          <View style={[styles.featureIcon, { backgroundColor: `${feature.color}20` }]}>
            <Icon name={feature.icon as any} size={24} color={feature.color} />
          </View>
          <View style={styles.featureContent}>
            <Text style={styles.featureTitle}>{feature.title}</Text>
            <Text style={styles.featureDescription}>{feature.description}</Text>
            <Text style={styles.featureDetails}>{feature.details}</Text>
          </View>
          <Icon name="chevron-right" size={16} color="#8E8E93" />
        </TouchableOpacity>
      ))}
    </View>
  );

  const renderTabs = () => (
    <View style={styles.tabs}>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'overview' && styles.tabActive]}
        onPress={() => setActiveTab('overview')}
      >
        <Text style={[styles.tabText, activeTab === 'overview' && styles.tabTextActive]}>
          Overview
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'features' && styles.tabActive]}
        onPress={() => setActiveTab('features')}
      >
        <Text style={[styles.tabText, activeTab === 'features' && styles.tabTextActive]}>
          All Features
        </Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      {renderHeader()}
      {renderTabs()}
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {activeTab === 'overview' ? renderOverview() : renderFeatures()}
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  backButton: {
    padding: 8,
  },
  headerTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1F2937',
    marginLeft: 8,
  },
  helpButton: {
    padding: 8,
  },
  tabs: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  tabActive: {
    borderBottomColor: '#FF6B35',
  },
  tabText: {
    fontSize: 16,
    fontWeight: '500',
    color: '#6B7280',
  },
  tabTextActive: {
    color: '#FF6B35',
  },
  content: {
    flex: 1,
  },
  overviewContainer: {
    padding: 16,
  },
  welcomeCard: {
    borderRadius: 12,
    marginBottom: 24,
    overflow: 'hidden',
  },
  welcomeGradient: {
    padding: 20,
  },
  welcomeTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  welcomeDescription: {
    fontSize: 16,
    color: '#FFFFFF',
    opacity: 0.9,
    lineHeight: 22,
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 24,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginHorizontal: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statNumber: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1F2937',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    color: '#6B7280',
    textAlign: 'center',
  },
  quickActionsContainer: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 16,
  },
  quickActionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  quickActionCard: {
    width: '48%',
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  quickActionText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#1F2937',
    marginTop: 8,
    textAlign: 'center',
  },
  featuresContainer: {
    padding: 16,
  },
  featureCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  featureIcon: {
    width: 48,
    height: 48,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  featureContent: {
    flex: 1,
  },
  featureTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 4,
  },
  featureDescription: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 2,
  },
  featureDetails: {
    fontSize: 12,
    color: '#9CA3AF',
  },
});

export default SwingTradingDashboard;
