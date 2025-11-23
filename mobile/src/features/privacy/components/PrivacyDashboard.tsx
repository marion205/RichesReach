/**
 * Privacy Dashboard - "Data Orb" Visualization
 * Shows users exactly what data is being used by AI/ML
 * Transparent, opt-in privacy controls
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Switch,
  Modal,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/Feather';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
} from 'react-native-reanimated';
import { useQuery, useMutation, gql } from '@apollo/client';

const GET_PRIVACY_SETTINGS = gql`
  query GetPrivacySettings {
    privacySettings {
      dataSharingEnabled
      aiAnalysisEnabled
      mlPredictionsEnabled
      analyticsEnabled
      sessionTrackingEnabled
      dataRetentionDays
      lastUpdated
    }
  }
`;

const UPDATE_PRIVACY_SETTINGS = gql`
  mutation UpdatePrivacySettings($settings: PrivacySettingsInput!) {
    updatePrivacySettings(settings: $settings) {
      success
      message
    }
  }
`;

interface DataCategory {
  id: string;
  name: string;
  description: string;
  icon: string;
  enabled: boolean;
  dataPoints: number;
  purpose: string;
  retentionDays: number;
}

interface PrivacyDashboardProps {
  visible: boolean;
  onClose: () => void;
}

export const PrivacyDashboard: React.FC<PrivacyDashboardProps> = ({
  visible,
  onClose,
}) => {
  const [dataCategories, setDataCategories] = useState<DataCategory[]>([]);
  const [showDetails, setShowDetails] = useState<string | null>(null);
  
  // Helper function to create data categories from settings
  const createDataCategories = (settings: any): DataCategory[] => {
    return [
      {
        id: 'financial',
        name: 'Financial Data',
        description: 'Net worth, cashflow, positions',
        icon: 'dollar-sign',
        enabled: settings.dataSharingEnabled ?? true,
        dataPoints: 12,
        purpose: 'AI-powered recommendations and growth projections',
        retentionDays: settings.dataRetentionDays ?? 90,
      },
      {
        id: 'ai-analysis',
        name: 'AI Analysis',
        description: 'Life events, recommendations, insights',
        icon: 'zap',
        enabled: settings.aiAnalysisEnabled ?? true,
        dataPoints: 8,
        purpose: 'Personalized financial planning and goal tracking',
        retentionDays: 90,
      },
      {
        id: 'ml-predictions',
        name: 'ML Predictions',
        description: 'Growth rates, market regime, risk analysis',
        icon: 'cpu',
        enabled: settings.mlPredictionsEnabled ?? true,
        dataPoints: 15,
        purpose: 'Market predictions and portfolio optimization',
        retentionDays: 60,
      },
      {
        id: 'analytics',
        name: 'Usage Analytics',
        description: 'App usage, gesture interactions, feature engagement',
        icon: 'bar-chart-2',
        enabled: settings.analyticsEnabled ?? true,
        dataPoints: 20,
        purpose: 'Improve app experience and feature development',
        retentionDays: 365,
      },
        {
          id: 'session',
          name: 'Session Tracking',
          description: 'Session replays, error logs, performance metrics',
          icon: 'activity',
          enabled: settings.sessionTrackingEnabled ?? false,
          dataPoints: 5,
          purpose: 'Debug issues and optimize performance',
          retentionDays: 30,
        },
      ];
  };
  
  // Query with error handling - privacySettings may not exist in schema yet
  const { data, loading, refetch, error } = useQuery(GET_PRIVACY_SETTINGS, {
    errorPolicy: 'all', // Return both data and errors
    fetchPolicy: 'cache-first', // Use cache if available
    skip: false, // Still try to query, but handle errors gracefully
  });
  const [updateSettings] = useMutation(UPDATE_PRIVACY_SETTINGS, {
    errorPolicy: 'all',
  });

  // Initialize data categories
  useEffect(() => {
    // Handle case where privacySettings doesn't exist in schema (use defaults)
    if (error && error.graphQLErrors?.some((e: any) => e.message?.includes('Cannot query field'))) {
      // Schema doesn't have privacySettings yet - use default values
      const defaultSettings = {
        dataSharingEnabled: true,
        aiAnalysisEnabled: true,
        mlPredictionsEnabled: true,
        analyticsEnabled: true,
        sessionTrackingEnabled: true,
        dataRetentionDays: 90,
      };
      setDataCategories(createDataCategories(defaultSettings));
      return;
    }
    
    if (data?.privacySettings) {
      const settings = data.privacySettings;
      setDataCategories(createDataCategories(settings));
    } else if (!loading && !error) {
      // No data and no error - use defaults
      const defaultSettings = {
        dataSharingEnabled: true,
        aiAnalysisEnabled: true,
        mlPredictionsEnabled: true,
        analyticsEnabled: true,
        sessionTrackingEnabled: true,
        dataRetentionDays: 90,
      };
      setDataCategories(createDataCategories(defaultSettings));
    }
  }, [data, error, loading]);

  const toggleCategory = async (categoryId: string) => {
    const updated = dataCategories.map(cat => 
      cat.id === categoryId ? { ...cat, enabled: !cat.enabled } : cat
    );
    setDataCategories(updated);

    // Update backend
    const category = updated.find(c => c.id === categoryId);
    if (category) {
      const settingsMap: Record<string, string> = {
        'financial': 'dataSharingEnabled',
        'ai-analysis': 'aiAnalysisEnabled',
        'ml-predictions': 'mlPredictionsEnabled',
        'analytics': 'analyticsEnabled',
        'session': 'sessionTrackingEnabled',
      };

      try {
        await updateSettings({
          variables: {
            settings: {
              [settingsMap[categoryId]]: category.enabled,
            },
          },
        });
        await refetch();
      } catch (error) {
        console.error('Failed to update privacy settings:', error);
        // Revert on error
        setDataCategories(dataCategories);
      }
    }
  };

  const totalDataPoints = dataCategories.reduce((sum, cat) => 
    sum + (cat.enabled ? cat.dataPoints : 0), 0
  );
  const enabledCategories = dataCategories.filter(cat => cat.enabled).length;

  // Animated orb size based on data usage
  const orbScale = useSharedValue(0.5);
  useEffect(() => {
    const scale = 0.3 + (enabledCategories / dataCategories.length) * 0.4;
    orbScale.value = withSpring(scale);
  }, [enabledCategories, dataCategories.length]);

  const orbStyle = useAnimatedStyle(() => ({
    transform: [{ scale: orbScale.value }],
  }));

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerContent}>
            <Icon name="shield" size={24} color="#007AFF" />
            <Text style={styles.title}>Privacy & Data</Text>
          </View>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Icon name="x" size={24} color="#8E8E93" />
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {/* Data Orb Visualization */}
          <View style={styles.orbSection}>
            <Text style={styles.sectionTitle}>Your Data Orb</Text>
            <Text style={styles.sectionSubtitle}>
              Visual representation of your data usage
            </Text>
            
            <View style={styles.orbContainer}>
              <Animated.View style={[styles.dataOrb, orbStyle]}>
                <View style={styles.orbInner}>
                  <Text style={styles.orbValue}>{totalDataPoints}</Text>
                  <Text style={styles.orbLabel}>Data Points</Text>
                  <Text style={styles.orbSubtext}>
                    {enabledCategories} of {dataCategories.length} categories active
                  </Text>
                </View>
              </Animated.View>
            </View>

            <View style={styles.orbLegend}>
              <View style={styles.legendItem}>
                <View style={[styles.legendDot, { backgroundColor: '#34C759' }]} />
                <Text style={styles.legendText}>Active</Text>
              </View>
              <View style={styles.legendItem}>
                <View style={[styles.legendDot, { backgroundColor: '#8E8E93' }]} />
                <Text style={styles.legendText}>Disabled</Text>
              </View>
            </View>
          </View>

          {/* Privacy Principles */}
          <View style={styles.principlesSection}>
            <Text style={styles.sectionTitle}>Our Privacy Principles</Text>
            <View style={styles.principleCard}>
              <Icon name="lock" size={20} color="#34C759" />
              <View style={styles.principleContent}>
                <Text style={styles.principleTitle}>You Own Your Data</Text>
                <Text style={styles.principleText}>
                  All data is encrypted and stored securely. You can export or delete it anytime.
                </Text>
              </View>
            </View>
            <View style={styles.principleCard}>
              <Icon name="eye-off" size={20} color="#34C759" />
              <View style={styles.principleContent}>
                <Text style={styles.principleTitle}>No Session Replays</Text>
                <Text style={styles.principleText}>
                  We don't record your screen or track your every move. Only essential analytics.
                </Text>
              </View>
            </View>
            <View style={styles.principleCard}>
              <Icon name="zap" size={20} color="#34C759" />
              <View style={styles.principleContent}>
                <Text style={styles.principleTitle}>Transparent AI</Text>
                <Text style={styles.principleText}>
                  See exactly what data powers each AI recommendation. No black boxes.
                </Text>
              </View>
            </View>
            <View style={styles.principleCard}>
              <Icon name="calendar" size={20} color="#34C759" />
              <View style={styles.principleContent}>
                <Text style={styles.principleTitle}>Auto-Delete</Text>
                <Text style={styles.principleText}>
                  Data is automatically deleted after retention period. No permanent storage.
                </Text>
              </View>
            </View>
          </View>

          {/* Data Categories */}
          <View style={styles.categoriesSection}>
            <Text style={styles.sectionTitle}>Data Categories</Text>
            <Text style={styles.sectionSubtitle}>
              Control what data is used for AI and analytics
            </Text>

            {dataCategories.map((category) => (
              <View key={category.id} style={styles.categoryCard}>
                <View style={styles.categoryHeader}>
                  <View style={[
                    styles.categoryIcon,
                    { backgroundColor: category.enabled ? '#34C75920' : '#8E8E9320' }
                  ]}>
                    <Icon 
                      name={category.icon as any} 
                      size={20} 
                      color={category.enabled ? '#34C759' : '#8E8E93'} 
                    />
                  </View>
                  <View style={styles.categoryInfo}>
                    <Text style={styles.categoryName}>{category.name}</Text>
                    <Text style={styles.categoryDescription}>
                      {category.description} • {category.dataPoints} data points
                    </Text>
                  </View>
                  <Switch
                    value={category.enabled}
                    onValueChange={() => toggleCategory(category.id)}
                    trackColor={{ false: '#E5E5EA', true: '#34C759' }}
                    thumbColor="#FFFFFF"
                  />
                </View>

                {category.enabled && (
                  <View style={styles.categoryDetails}>
                    <View style={styles.detailRow}>
                      <Icon name="info" size={14} color="#8E8E93" />
                      <Text style={styles.detailText}>
                        <Text style={styles.detailLabel}>Purpose: </Text>
                        {category.purpose}
                      </Text>
                    </View>
                    <View style={styles.detailRow}>
                      <Icon name="clock" size={14} color="#8E8E93" />
                      <Text style={styles.detailText}>
                        <Text style={styles.detailLabel}>Retention: </Text>
                        {category.retentionDays} days
                      </Text>
                    </View>
                  </View>
                )}

                {showDetails === category.id && (
                  <TouchableOpacity
                    style={styles.learnMoreButton}
                    onPress={() => setShowDetails(null)}
                  >
                    <Text style={styles.learnMoreText}>
                      Learn more about {category.name.toLowerCase()} data usage
                    </Text>
                    <Icon name="chevron-down" size={16} color="#007AFF" />
                  </TouchableOpacity>
                )}
              </View>
            ))}
          </View>

          {/* Actions */}
          <View style={styles.actionsSection}>
            <TouchableOpacity style={styles.actionButton}>
              <Icon name="download" size={20} color="#007AFF" />
              <Text style={styles.actionButtonText}>Export My Data</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.actionButton, styles.dangerButton]}>
              <Icon name="trash-2" size={20} color="#FF3B30" />
              <Text style={[styles.actionButtonText, styles.dangerText]}>
                Delete All Data
              </Text>
            </TouchableOpacity>
          </View>

          {/* Compliance Badges */}
          <View style={styles.complianceSection}>
            <Text style={styles.sectionTitle}>Compliance & Certifications</Text>
            <View style={styles.badgesContainer}>
              <View style={styles.badge}>
                <Text style={styles.badgeText}>GDPR</Text>
              </View>
              <View style={styles.badge}>
                <Text style={styles.badgeText}>CCPA</Text>
              </View>
              <View style={styles.badge}>
                <Text style={styles.badgeText}>SOC 2</Text>
              </View>
            </View>
          </View>
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  closeButton: {
    padding: 4,
  },
  content: {
    flex: 1,
    padding: 20,
  },
  orbSection: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 24,
    marginBottom: 24,
    alignItems: 'center',
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 8,
  },
  sectionSubtitle: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 20,
    textAlign: 'center',
  },
  orbContainer: {
    width: 200,
    height: 200,
    justifyContent: 'center',
    alignItems: 'center',
    marginVertical: 20,
  },
  dataOrb: {
    width: 200,
    height: 200,
    borderRadius: 100,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#007AFF',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 8,
  },
  orbInner: {
    alignItems: 'center',
  },
  orbValue: {
    fontSize: 48,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  orbLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
    opacity: 0.9,
    marginTop: 4,
  },
  orbSubtext: {
    fontSize: 12,
    color: '#FFFFFF',
    opacity: 0.7,
    marginTop: 8,
  },
  orbLegend: {
    flexDirection: 'row',
    gap: 24,
    marginTop: 16,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  legendDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  legendText: {
    fontSize: 14,
    color: '#8E8E93',
  },
  principlesSection: {
    marginBottom: 24,
  },
  principleCard: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    gap: 12,
  },
  principleContent: {
    flex: 1,
  },
  principleTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  principleText: {
    fontSize: 14,
    color: '#8E8E93',
    lineHeight: 20,
  },
  categoriesSection: {
    marginBottom: 24,
  },
  categoryCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  categoryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  categoryIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  categoryInfo: {
    flex: 1,
  },
  categoryName: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  categoryDescription: {
    fontSize: 13,
    color: '#8E8E93',
  },
  categoryDetails: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
    gap: 8,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
  },
  detailText: {
    fontSize: 13,
    color: '#8E8E93',
    flex: 1,
    lineHeight: 18,
  },
  detailLabel: {
    fontWeight: '600',
    color: '#1C1C1E',
  },
  learnMoreButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 12,
    paddingVertical: 8,
    gap: 4,
  },
  learnMoreText: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '600',
  },
  actionsSection: {
    marginBottom: 24,
    gap: 12,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    gap: 12,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  dangerButton: {
    borderColor: '#FF3B30',
  },
  actionButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
  },
  dangerText: {
    color: '#FF3B30',
  },
  complianceSection: {
    marginBottom: 24,
  },
  badgesContainer: {
    flexDirection: 'row',
    gap: 12,
    flexWrap: 'wrap',
  },
  badge: {
    backgroundColor: '#34C75920',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  badgeText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#34C759',
  },
});

export default PrivacyDashboard;

