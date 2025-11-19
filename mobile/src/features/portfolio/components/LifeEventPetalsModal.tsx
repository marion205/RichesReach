/**
 * LifeEventPetalsModal
 * Shows life event planning petals (home buying, emergency fund, etc.)
 * Triggered by tap gesture on Constellation Orb
 */

import React, { useState, useEffect } from 'react';
import {
  Modal,
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Dimensions,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/Feather';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
} from 'react-native-reanimated';
import { MoneySnapshot } from '../services/MoneySnapshotService';
import { constellationAIService, PersonalizedLifeEvent } from '../services/ConstellationAIService';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

interface LifeEvent {
  id: string;
  title: string;
  icon: string;
  targetAmount: number;
  currentProgress: number;
  monthsAway: number;
  suggestion: string;
  color: string;
  aiConfidence?: number;
  aiReasoning?: string;
  personalizedFactors?: string[];
}

interface LifeEventPetalsModalProps {
  visible: boolean;
  onClose: () => void;
  snapshot: MoneySnapshot;
}

export const LifeEventPetalsModal: React.FC<LifeEventPetalsModalProps> = ({
  visible,
  onClose,
  snapshot,
}) => {
  const [selectedEvent, setSelectedEvent] = useState<LifeEvent | null>(null);
  const [lifeEvents, setLifeEvents] = useState<LifeEvent[]>([]);
  const [loadingAI, setLoadingAI] = useState(true);
  const [aiEnabled, setAiEnabled] = useState(false);

  // Generate fallback life events (with safety checks)
  const bankBalance = snapshot?.breakdown?.bankBalance ?? 0;
  const portfolioValue = snapshot?.breakdown?.portfolioValue ?? 0;
  const netWorth = snapshot?.netWorth ?? 0;
  const cashflowDelta = snapshot?.cashflow?.delta ?? 100;
  
  const fallbackLifeEvents: LifeEvent[] = [
    {
      id: 'emergency',
      title: 'Emergency Fund',
      icon: 'shield',
      targetAmount: netWorth * 0.1, // 10% of net worth
      currentProgress: bankBalance,
      monthsAway: Math.ceil((netWorth * 0.1 - bankBalance) / Math.max(cashflowDelta, 100)),
      suggestion: `Save $${Math.max(100, Math.floor(cashflowDelta * 0.3)).toFixed(0)}/mo to reach goal in ${Math.ceil((netWorth * 0.1 - bankBalance) / Math.max(cashflowDelta, 100))} months`,
      color: '#34C759',
    },
    {
      id: 'home',
      title: 'Home Down Payment',
      icon: 'home',
      targetAmount: 50000,
      currentProgress: bankBalance * 0.5,
      monthsAway: Math.ceil((50000 - bankBalance * 0.5) / Math.max(cashflowDelta, 100)),
      suggestion: `Shift $${Math.max(200, Math.floor(cashflowDelta * 0.4)).toFixed(0)}/mo from dining to savings`,
      color: '#007AFF',
    },
    {
      id: 'retirement',
      title: 'Retirement Nest Egg',
      icon: 'trending-up',
      targetAmount: netWorth * 10,
      currentProgress: portfolioValue,
      monthsAway: Math.ceil((netWorth * 10 - portfolioValue) / Math.max(cashflowDelta * 0.5, 100)),
      suggestion: `Invest $${Math.max(150, Math.floor(cashflowDelta * 0.5)).toFixed(0)}/mo in low-vol ETF`,
      color: '#FF9500',
    },
    {
      id: 'education',
      title: 'Education Fund',
      icon: 'book',
      targetAmount: 25000,
      currentProgress: bankBalance * 0.2,
      monthsAway: Math.ceil((25000 - bankBalance * 0.2) / Math.max(cashflowDelta * 0.25, 100)),
      suggestion: `Set aside $${Math.max(150, Math.floor(cashflowDelta * 0.25)).toFixed(0)}/mo for education savings`,
      color: '#AF52DE',
    },
    {
      id: 'vacation',
      title: 'Dream Vacation',
      icon: 'map',
      targetAmount: 10000,
      currentProgress: bankBalance * 0.1,
      monthsAway: Math.ceil((10000 - bankBalance * 0.1) / Math.max(cashflowDelta * 0.2, 100)),
      suggestion: `Save $${Math.max(100, Math.floor(cashflowDelta * 0.2)).toFixed(0)}/mo for your next adventure`,
      color: '#5AC8FA',
    },
    {
      id: 'debt',
      title: 'Debt Freedom',
      icon: 'credit-card',
      targetAmount: netWorth * 0.2,
      currentProgress: 0,
      monthsAway: Math.ceil((netWorth * 0.2) / Math.max(cashflowDelta * 0.4, 100)),
      suggestion: `Pay down $${Math.max(200, Math.floor(cashflowDelta * 0.4)).toFixed(0)}/mo to eliminate debt faster`,
      color: '#FF3B30',
    },
  ];

  // Fetch AI-powered life events when modal opens
  useEffect(() => {
    if (visible && snapshot) {
      loadAILifeEvents();
    } else {
      // Use fallback when modal is closed
      setLifeEvents(fallbackLifeEvents);
      setAiEnabled(false);
    }
  }, [visible, snapshot]);

  const loadAILifeEvents = async () => {
    try {
      setLoadingAI(true);
      const aiEvents = await constellationAIService.getPersonalizedLifeEvents(snapshot);
      
      if (aiEvents && aiEvents.length > 0) {
        // Convert AI events to LifeEvent format
        const convertedEvents: LifeEvent[] = aiEvents.map((aiEvent) => ({
          id: aiEvent.id,
          title: aiEvent.title,
          icon: aiEvent.icon,
          targetAmount: aiEvent.targetAmount,
          currentProgress: aiEvent.currentProgress,
          monthsAway: aiEvent.monthsAway,
          suggestion: aiEvent.suggestion,
          color: aiEvent.color,
          aiConfidence: aiEvent.aiConfidence,
          aiReasoning: aiEvent.aiReasoning,
          personalizedFactors: aiEvent.personalizedFactors,
        }));
        setLifeEvents(convertedEvents);
        setAiEnabled(true);
      } else {
        setLifeEvents(fallbackLifeEvents);
        setAiEnabled(false);
      }
    } catch (error) {
      console.warn('[LifeEventPetalsModal] AI loading failed, using fallback:', error);
      setLifeEvents(fallbackLifeEvents);
      setAiEnabled(false);
    } finally {
      setLoadingAI(false);
    }
  };

  const formatCurrency = (amount: number) => {
    if (amount >= 1000000) return `$${(amount / 1000000).toFixed(1)}M`;
    if (amount >= 1000) return `$${(amount / 1000).toFixed(1)}K`;
    return `$${amount.toFixed(0)}`;
  };

  const getProgressPercent = (current: number, target: number) => {
    return Math.min(100, Math.max(0, (current / target) * 100));
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
        <View style={styles.header}>
          <View style={styles.headerContent}>
            <View style={styles.titleContainer}>
              <Text style={styles.title}>Life Event Planning</Text>
              {aiEnabled && (
                <View style={styles.aiBadge}>
                  <Icon name="zap" size={12} color="#FFD700" />
                  <Text style={styles.aiBadgeText}>AI</Text>
                </View>
              )}
            </View>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Icon name="x" size={24} color="#8E8E93" />
            </TouchableOpacity>
          </View>
          <Text style={styles.subtitle}>
            {aiEnabled 
              ? 'AI-powered personalized financial milestones' 
              : 'Your financial milestones and how to reach them'}
          </Text>
        </View>

        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {loadingAI && (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="small" color="#007AFF" />
              <Text style={styles.loadingText}>Loading AI-powered suggestions...</Text>
            </View>
          )}
          {lifeEvents.map((event) => {
            const progress = getProgressPercent(event.currentProgress, event.targetAmount);
            const isSelected = selectedEvent?.id === event.id;

            return (
              <TouchableOpacity
                key={event.id}
                style={[styles.petalCard, isSelected && styles.petalCardSelected]}
                onPress={() => setSelectedEvent(isSelected ? null : event)}
                activeOpacity={0.7}
              >
                <View style={styles.petalHeader}>
                  <View style={[styles.iconContainer, { backgroundColor: `${event.color}20` }]}>
                    <Icon name={event.icon as any} size={24} color={event.color} />
                  </View>
                  <View style={styles.petalInfo}>
                    <Text style={styles.petalTitle}>{event.title}</Text>
                    <Text style={styles.petalTarget}>
                      {formatCurrency(event.currentProgress)} / {formatCurrency(event.targetAmount)}
                    </Text>
                  </View>
                  <Icon
                    name={isSelected ? 'chevron-up' : 'chevron-down'}
                    size={20}
                    color="#8E8E93"
                  />
                </View>

                {/* Progress Bar */}
                <View style={styles.progressContainer}>
                  <View style={styles.progressTrack}>
                    <View
                      style={[
                        styles.progressFill,
                        { width: `${progress}%`, backgroundColor: event.color },
                      ]}
                    />
                  </View>
                  <Text style={styles.progressText}>{progress.toFixed(0)}%</Text>
                </View>

                {/* Expanded Details */}
                {isSelected && (
                  <View style={styles.petalDetails}>
                    <View style={styles.detailRow}>
                      <Icon name="calendar" size={16} color="#8E8E93" />
                      <Text style={styles.detailText}>
                        {event.monthsAway} months away at current pace
                      </Text>
                    </View>
                    <View style={styles.suggestionBox}>
                      <Icon name="lightbulb" size={16} color={event.color} />
                      <Text style={[styles.suggestionText, { color: event.color }]}>
                        {event.suggestion}
                      </Text>
                    </View>
                    {event.aiReasoning && (
                      <View style={styles.aiReasoningBox}>
                        <View style={styles.aiReasoningHeader}>
                          <Icon name="zap" size={14} color="#FFD700" />
                          <Text style={styles.aiReasoningTitle}>AI Analysis</Text>
                          {event.aiConfidence && (
                            <Text style={styles.aiConfidence}>
                              {Math.round(event.aiConfidence * 100)}% confidence
                            </Text>
                          )}
                        </View>
                        <Text style={styles.aiReasoningText}>{event.aiReasoning}</Text>
                        {event.personalizedFactors && event.personalizedFactors.length > 0 && (
                          <View style={styles.factorsContainer}>
                            <Text style={styles.factorsTitle}>Personalized Factors:</Text>
                            {event.personalizedFactors.map((factor, idx) => (
                              <View key={idx} style={styles.factorTag}>
                                <Text style={styles.factorText}>{factor}</Text>
                              </View>
                            ))}
                          </View>
                        )}
                      </View>
                    )}
                  </View>
                )}
              </TouchableOpacity>
            );
          })}

          {/* Action Button */}
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => {
              // Future enhancement: Navigate to financial planning screen with life event context
              onClose();
            }}
          >
            <Icon name="target" size={20} color="#FFFFFF" />
            <Text style={styles.actionButtonText}>Create Custom Plan</Text>
          </TouchableOpacity>
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
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 12,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  titleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  aiBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFD70020',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    gap: 4,
  },
  aiBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#FFD700',
  },
  closeButton: {
    padding: 4,
  },
  subtitle: {
    fontSize: 14,
    color: '#8E8E93',
  },
  content: {
    flex: 1,
    padding: 16,
  },
  petalCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  petalCardSelected: {
    borderWidth: 2,
    borderColor: '#34C759',
  },
  petalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  iconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  petalInfo: {
    flex: 1,
  },
  petalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  petalTarget: {
    fontSize: 14,
    color: '#8E8E93',
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  progressTrack: {
    flex: 1,
    height: 8,
    backgroundColor: '#E5E5EA',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 4,
  },
  progressText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#8E8E93',
    minWidth: 40,
    textAlign: 'right',
  },
  petalDetails: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  detailText: {
    fontSize: 14,
    color: '#1C1C1E',
    flex: 1,
  },
  suggestionBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    backgroundColor: '#F8F9FA',
    padding: 12,
    borderRadius: 8,
  },
  suggestionText: {
    fontSize: 14,
    fontWeight: '500',
    flex: 1,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#34C759',
    borderRadius: 12,
    padding: 16,
    marginTop: 8,
    gap: 8,
  },
  actionButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    gap: 8,
  },
  loadingText: {
    fontSize: 14,
    color: '#8E8E93',
  },
  aiReasoningBox: {
    marginTop: 12,
    backgroundColor: '#FFF9E6',
    borderRadius: 8,
    padding: 12,
    borderLeftWidth: 3,
    borderLeftColor: '#FFD700',
  },
  aiReasoningHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 8,
  },
  aiReasoningTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#856404',
    flex: 1,
  },
  aiConfidence: {
    fontSize: 10,
    fontWeight: '600',
    color: '#856404',
    backgroundColor: '#FFD70040',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  aiReasoningText: {
    fontSize: 13,
    color: '#856404',
    lineHeight: 18,
    marginBottom: 8,
  },
  factorsContainer: {
    marginTop: 8,
  },
  factorsTitle: {
    fontSize: 11,
    fontWeight: '600',
    color: '#856404',
    marginBottom: 6,
  },
  factorTag: {
    backgroundColor: '#FFD70030',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    marginBottom: 4,
    alignSelf: 'flex-start',
  },
  factorText: {
    fontSize: 11,
    color: '#856404',
    fontWeight: '500',
  },
});

export default LifeEventPetalsModal;

