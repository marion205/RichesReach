/**
 * Credit Quest Screen - "Freedom Canvas"
 * Single-screen experience for credit building (Jobs-level simplicity)
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/Feather';
import { CreditScoreOrb } from '../components/CreditScoreOrb';
import { CreditUtilizationGauge } from '../components/CreditUtilizationGauge';
import { CreditScoreTrendChart } from '../components/CreditScoreTrendChart';
import { creditScoreService } from '../services/CreditScoreService';
import { creditUtilizationService } from '../services/CreditUtilizationService';
import { creditNotificationService } from '../services/CreditNotificationService';
import { CreditSnapshot, CreditAction, CreditScore } from '../types/CreditTypes';

interface CreditQuestScreenProps {
  visible: boolean;
  onClose: () => void;
}

export const CreditQuestScreen: React.FC<CreditQuestScreenProps> = ({
  visible,
  onClose,
}) => {
  const insets = useSafeAreaInsets();
  const [loading, setLoading] = useState(true);
  const [snapshot, setSnapshot] = useState<CreditSnapshot | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [scoreHistory, setScoreHistory] = useState<CreditScore[]>([]);
  const [showTrends, setShowTrends] = useState(false);

  useEffect(() => {
    if (visible) {
      loadSnapshot();
    }
  }, [visible]);

  const loadSnapshot = async () => {
    try {
      setLoading(true);
      // getSnapshot() now returns fallback data on error, so it won't throw
      const data = await creditScoreService.getSnapshot();
      setSnapshot(data);
      
      // Load score history for trends
      try {
        // In production, fetch historical scores from API
        // For now, create mock history from current score
        const currentScore = data.score;
        if (currentScore && typeof currentScore.score === 'number') {
          const history: CreditScore[] = [];
          for (let i = 5; i >= 0; i--) {
            const date = new Date();
            date.setMonth(date.getMonth() - i);
            history.push({
              score: currentScore.score - (i * 5), // Mock progression
              scoreRange: currentScore.scoreRange || 'Fair',
              lastUpdated: date.toISOString(),
              provider: currentScore.provider || 'self_reported',
              factors: currentScore.factors,
            });
          }
          setScoreHistory(history);
        } else {
          // Fallback: create mock history with default values
          const history: CreditScore[] = [];
          for (let i = 5; i >= 0; i--) {
            const date = new Date();
            date.setMonth(date.getMonth() - i);
            history.push({
              score: 580 - (i * 5),
              scoreRange: 'Fair',
              lastUpdated: date.toISOString(),
              provider: 'self_reported',
            });
          }
          setScoreHistory(history);
        }
      } catch (error) {
        console.warn('[CreditQuest] Failed to load score history:', error);
        // Set empty history on error
        setScoreHistory([]);
      }
      
      // Schedule payment reminders
      if (data.cards && data.cards.length > 0) {
        for (const card of data.cards) {
          if (card.paymentDueDate) {
            const dueDate = new Date(card.paymentDueDate);
            await creditNotificationService.schedulePaymentReminder(
              card.name,
              dueDate,
              3
            );
          }
          
          // Schedule utilization alerts if high
          if (card.utilization > 0.5) {
            await creditNotificationService.scheduleUtilizationAlert(
              card.name,
              card.utilization
            );
          }
        }
      }
    } catch (error) {
      console.error('[CreditQuest] Failed to load snapshot:', error);
      // Don't show error alert - the service now provides fallback data
      // The snapshot will be set with fallback data from the service
      // Only show alert if snapshot is still null after fallback
      if (!snapshot) {
        Alert.alert(
          'Notice',
          'Using demo credit data. Connect to backend for real-time updates.',
          [{ text: 'OK' }]
        );
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadSnapshot();
    setRefreshing(false);
  };

  const handlePrimaryAction = () => {
    if (!snapshot) return;
    
    const topAction = snapshot.actions.find(a => !a.completed);
    if (topAction) {
      Alert.alert(
        topAction.title,
        topAction.description,
        [
          { text: 'Cancel', style: 'cancel' },
          { 
            text: 'Complete', 
            onPress: () => {
              // In production, mark action as completed via API
              Alert.alert('Success', 'Action completed! Your credit score may improve.');
              loadSnapshot();
            }
          }
        ]
      );
    } else {
      Alert.alert(
        'Great Job!',
        'You\'re on track with your credit building journey.',
        [{ text: 'OK' }]
      );
    }
  };

  if (!visible) return null;

  // Ensure snapshot has valid score before rendering
  if (!snapshot || !snapshot.score) {
    return (
      <View style={[styles.container, { paddingTop: insets.top }]}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Credit Quest</Text>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Icon name="x" size={24} color="#8E8E93" />
          </TouchableOpacity>
        </View>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading credit data...</Text>
        </View>
      </View>
    );
  }

  if (loading) {
    return (
      <View style={[styles.container, { paddingTop: insets.top }]}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Credit Quest</Text>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Icon name="x" size={24} color="#8E8E93" />
          </TouchableOpacity>
        </View>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading your credit journey...</Text>
        </View>
      </View>
    );
  }

  if (!snapshot) {
    return (
      <View style={[styles.container, { paddingTop: insets.top }]}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Credit Quest</Text>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Icon name="x" size={24} color="#8E8E93" />
          </TouchableOpacity>
        </View>
        <View style={styles.emptyContainer}>
          <Icon name="credit-card" size={64} color="#8E8E93" />
          <Text style={styles.emptyTitle}>Start Your Credit Journey</Text>
          <Text style={styles.emptySubtitle}>
            Link a credit card to begin building your credit score
          </Text>
          <TouchableOpacity 
            style={styles.primaryButton}
            onPress={handlePrimaryAction}
          >
            <Text style={styles.primaryButtonText}>Get Started</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  const topAction = snapshot.actions.find(a => !a.completed);
  const utilization = snapshot.utilization;

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Credit Quest</Text>
        <View style={styles.headerActions}>
          <TouchableOpacity onPress={handleRefresh} style={styles.refreshButton}>
            <Icon 
              name="refresh-cw" 
              size={20} 
              color={refreshing ? "#007AFF" : "#8E8E93"} 
            />
          </TouchableOpacity>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Icon name="x" size={24} color="#8E8E93" />
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView 
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        {/* Credit Score Orb */}
        <View style={styles.orbSection}>
          <CreditScoreOrb 
            score={snapshot?.score || undefined}
            projection={snapshot?.projection}
          />
        </View>

        {/* This Month Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>This Month</Text>
          <CreditUtilizationGauge utilization={utilization} />
        </View>

        {/* Top Action */}
        {topAction && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Top Action</Text>
            <TouchableOpacity 
              style={styles.primaryButton}
              onPress={handlePrimaryAction}
            >
              <Icon name="check-circle" size={20} color="#FFFFFF" />
              <Text style={styles.primaryButtonText}>{topAction.title}</Text>
            </TouchableOpacity>
            {topAction.projectedScoreGain && (
              <Text style={styles.actionProjection}>
                → +{topAction.projectedScoreGain} points in 3 months
              </Text>
            )}
          </View>
        )}

        {/* Shield Alerts */}
        {snapshot.shield && snapshot.shield.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Alerts</Text>
            {snapshot.shield.map((alert, index) => (
              <View key={index} style={styles.shieldAlert}>
                <Icon 
                  name="shield" 
                  size={20} 
                  color={alert.type === 'PAYMENT_DUE' ? '#FF9500' : '#FF3B30'} 
                />
                <View style={styles.shieldContent}>
                  <Text style={styles.shieldMessage}>{alert.message}</Text>
                  <Text style={styles.shieldSuggestion}>{alert.suggestion}</Text>
                </View>
              </View>
            ))}
          </View>
        )}

        {/* Actions List */}
        {snapshot.actions.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Your Actions</Text>
            {snapshot.actions.map((action) => (
              <View 
                key={action.id} 
                style={[
                  styles.actionCard,
                  action.completed && styles.actionCardCompleted
                ]}
              >
                <Icon 
                  name={action.completed ? "check-circle" : "circle"} 
                  size={20} 
                  color={action.completed ? "#34C759" : "#8E8E93"} 
                />
                <View style={styles.actionContent}>
                  <Text style={styles.actionTitle}>{action.title}</Text>
                  <Text style={styles.actionDescription}>{action.description}</Text>
                  {action.projectedScoreGain && (
                    <Text style={styles.actionGain}>
                      +{action.projectedScoreGain} points
                    </Text>
                  )}
                </View>
              </View>
            ))}
          </View>
        )}
      </ScrollView>
    </View>
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
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  headerActions: {
    flexDirection: 'row',
    gap: 12,
  },
  refreshButton: {
    padding: 4,
  },
  closeButton: {
    padding: 4,
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 20,
    paddingBottom: 40,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  loadingText: {
    fontSize: 16,
    color: '#8E8E93',
    marginTop: 16,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1C1C1E',
    marginTop: 16,
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
    marginBottom: 24,
  },
  orbSection: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 12,
  },
  primaryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    gap: 8,
  },
  primaryButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  actionProjection: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
    marginTop: 8,
  },
  shieldAlert: {
    flexDirection: 'row',
    backgroundColor: '#FFF8E1',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    gap: 12,
  },
  shieldContent: {
    flex: 1,
  },
  shieldMessage: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  shieldSuggestion: {
    fontSize: 12,
    color: '#8E8E93',
  },
  actionCard: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    gap: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  actionCardCompleted: {
    opacity: 0.6,
  },
  actionContent: {
    flex: 1,
  },
  actionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  actionDescription: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 4,
  },
  actionGain: {
    fontSize: 12,
    color: '#34C759',
    fontWeight: '600',
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  trendToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    padding: 8,
  },
  trendToggleText: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '600',
  },
  trendSection: {
    marginTop: 16,
  },
});

