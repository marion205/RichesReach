/**
 * DetailedBreakdownModal
 * Detailed financial breakdown triggered by long press on Constellation Orb
 */

import React, { useState, useEffect } from 'react';
import {
  Modal,
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/Feather';
import { MoneySnapshot } from '../services/MoneySnapshotService';
import { constellationAIService, PersonalizedRecommendation } from '../services/ConstellationAIService';
import logger from '../../../utils/logger';

interface BreakdownItem {
  label: string;
  value: number;
  icon: string;
  color: string;
  percentage?: number;
}

interface DetailedBreakdownModalProps {
  visible: boolean;
  onClose: () => void;
  snapshot: MoneySnapshot;
}

export const DetailedBreakdownModal: React.FC<DetailedBreakdownModalProps> = ({
  visible,
  onClose,
  snapshot,
}) => {
  const [recommendations, setRecommendations] = useState<PersonalizedRecommendation[]>([]);
  const [loadingAI, setLoadingAI] = useState(true);
  const [aiEnabled, setAiEnabled] = useState(false);

  const netWorth = snapshot?.netWorth ?? 0;
  const bankBalance = snapshot?.breakdown?.bankBalance ?? 0;
  const portfolioValue = snapshot?.breakdown?.portfolioValue ?? 0;
  const cashflowIn = snapshot?.cashflow?.in ?? 0;
  const cashflowOut = snapshot?.cashflow?.out ?? 0;
  const cashflowDelta = snapshot?.cashflow?.delta ?? 0;

  // Modal visibility tracking removed (debug logging)

  // Fetch AI recommendations when modal opens
  useEffect(() => {
    if (visible && snapshot) {
      loadAIRecommendations();
    }
  }, [visible, snapshot]);

  const loadAIRecommendations = async () => {
    try {
      setLoadingAI(true);
      const aiRecs = await constellationAIService.getPersonalizedRecommendations(snapshot);
      
      if (aiRecs && aiRecs.length > 0) {
        setRecommendations(aiRecs);
        setAiEnabled(true);
      } else {
        setRecommendations([]);
        setAiEnabled(false);
      }
    } catch (error) {
      logger.warn('[DetailedBreakdownModal] AI loading failed:', error);
      setRecommendations([]);
      setAiEnabled(false);
    } finally {
      setLoadingAI(false);
    }
  };

  const breakdownItems: BreakdownItem[] = [
    {
      label: 'Bank Balance',
      value: bankBalance,
      icon: 'credit-card',
      color: '#34C759',
      percentage: netWorth > 0 ? (bankBalance / netWorth) * 100 : 0,
    },
    {
      label: 'Portfolio Value',
      value: portfolioValue,
      icon: 'trending-up',
      color: '#007AFF',
      percentage: netWorth > 0 ? (portfolioValue / netWorth) * 100 : 0,
    },
  ];

  const formatCurrency = (amount: number) => {
    // Always show at least 2 decimal places for clarity
    if (amount >= 1000000) return `$${(amount / 1000000).toFixed(2)}M`;
    if (amount >= 1000) return `$${(amount / 1000).toFixed(1)}K`;
    // Show decimals for amounts less than $1000
    if (amount >= 1) return `$${amount.toFixed(2)}`;
    // Show $0.00 for zero or very small amounts
    return `$${amount.toFixed(2)}`;
  };

  const getRecommendationIcon = (type: string) => {
    switch (type) {
      case 'life_event': return 'calendar';
      case 'investment': return 'trending-up';
      case 'savings': return 'dollar-sign';
      case 'risk_management': return 'shield';
      default: return 'info';
    }
  };

  const getRecommendationColor = (type: string) => {
    switch (type) {
      case 'life_event': return '#AF52DE';
      case 'investment': return '#34C759';
      case 'savings': return '#007AFF';
      case 'risk_management': return '#FF3B30';
      default: return '#8E8E93';
    }
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
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
              <Icon name="pie-chart" size={24} color="#007AFF" />
              <Text style={styles.title}>Financial Breakdown</Text>
              {aiEnabled && (
                <View style={styles.aiBadge}>
                  <Icon name="zap" size={12} color="#FFD700" />
                  <Text style={styles.aiBadgeText}>AI</Text>
                </View>
              )}
            </View>
          </View>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Icon name="x" size={24} color="#8E8E93" />
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {/* Net Worth Summary */}
          <View style={styles.summaryCard}>
            <Text style={styles.summaryLabel}>Total Net Worth</Text>
            <Text style={styles.summaryValue}>{formatCurrency(netWorth)}</Text>
          </View>

          {/* Cash Flow Breakdown - Moved to top for prominence */}
          <View style={styles.cashflowSectionHeader}>
            <Icon name="trending-up" size={20} color="#007AFF" />
            <Text style={styles.sectionTitle}>Cash Flow (This Month)</Text>
          </View>
          <View style={styles.cashflowCard}>
            <View style={styles.cashflowRow}>
              <View style={styles.cashflowItem}>
                <View style={[styles.cashflowIconContainer, { backgroundColor: '#34C75920' }]}>
                  <Icon name="arrow-down" size={24} color="#34C759" />
                </View>
                <Text style={styles.cashflowLabel}>Income</Text>
                <Text style={[styles.cashflowValue, { color: '#34C759' }]}>
                  {formatCurrency(cashflowIn)}
                </Text>
              </View>
              <View style={styles.cashflowItem}>
                <View style={[styles.cashflowIconContainer, { backgroundColor: '#FF3B3020' }]}>
                  <Icon name="arrow-up" size={24} color="#FF3B30" />
                </View>
                <Text style={styles.cashflowLabel}>Expenses</Text>
                <Text style={[styles.cashflowValue, { color: '#FF3B30' }]}>
                  {formatCurrency(cashflowOut)}
                </Text>
              </View>
            </View>
            <View style={styles.cashflowDelta}>
              <View style={styles.cashflowDeltaHeader}>
                <Icon 
                  name={cashflowDelta >= 0 ? "trending-up" : "trending-down"} 
                  size={18} 
                  color={cashflowDelta >= 0 ? '#34C759' : '#FF3B30'} 
                />
                <Text style={styles.cashflowDeltaLabel}>Net Change</Text>
              </View>
              <Text
                style={[
                  styles.cashflowDeltaValue,
                  { color: cashflowDelta >= 0 ? '#34C759' : '#FF3B30' },
                ]}
              >
                {cashflowDelta >= 0 ? '+' : ''}
                {formatCurrency(cashflowDelta)}
              </Text>
            </View>
          </View>

          {/* Asset Breakdown */}
          <Text style={styles.sectionTitle}>Asset Allocation</Text>
          {breakdownItems.map((item, index) => (
            <View key={index} style={styles.breakdownCard}>
              <View style={styles.breakdownHeader}>
                <View style={[styles.iconContainer, { backgroundColor: `${item.color}20` }]}>
                  <Icon name={item.icon as any} size={20} color={item.color} />
                </View>
                <View style={styles.breakdownInfo}>
                  <Text style={styles.breakdownLabel}>{item.label}</Text>
                  <Text style={styles.breakdownValue}>{formatCurrency(item.value)}</Text>
                </View>
                {item.percentage !== undefined && (
                  <Text style={[styles.breakdownPercentage, { color: item.color }]}>
                    {formatPercentage(item.percentage)}
                  </Text>
                )}
              </View>
              {item.percentage !== undefined && (
                <View style={styles.progressBar}>
                  <View
                    style={[
                      styles.progressFill,
                      {
                        width: `${item.percentage}%`,
                        backgroundColor: item.color,
                      },
                    ]}
                  />
                </View>
              )}
            </View>
          ))}

          {/* AI Recommendations */}
          {aiEnabled && recommendations.length > 0 && (
            <View style={styles.section}>
              <View style={styles.sectionHeader}>
                <Icon name="zap" size={20} color="#FFD700" />
                <Text style={styles.sectionTitle}>AI Recommendations</Text>
              </View>
              {loadingAI && (
                <View style={styles.loadingContainer}>
                  <ActivityIndicator size="small" color="#FFD700" />
                  <Text style={styles.loadingText}>Loading personalized recommendations...</Text>
                </View>
              )}
              {recommendations.map((rec, index) => (
                <View key={index} style={styles.recommendationCard}>
                  <View style={styles.recommendationHeader}>
                    <View style={[styles.recommendationIcon, { backgroundColor: getRecommendationColor(rec.type) + '20' }]}>
                      <Icon name={getRecommendationIcon(rec.type) as any} size={18} color={getRecommendationColor(rec.type)} />
                    </View>
                    <View style={styles.recommendationInfo}>
                      <Text style={styles.recommendationTitle}>{rec.title}</Text>
                      <Text style={styles.recommendationDescription}>{rec.description}</Text>
                    </View>
                    {rec.aiConfidence && (
                      <View style={styles.confidenceBadge}>
                        <Text style={styles.confidenceText}>
                          {Math.round(rec.aiConfidence * 100)}%
                        </Text>
                      </View>
                    )}
                  </View>
                  <View style={styles.recommendationAction}>
                    <Text style={styles.recommendationActionText}>{rec.action}</Text>
                    {rec.reasoning && (
                      <View style={styles.reasoningBox}>
                        <Icon name="info" size={14} color="#856404" />
                        <Text style={styles.reasoningText}>
                          {rec.reasoning.replace(/^\?+\s*/, '')}
                        </Text>
                      </View>
                    )}
                  </View>
                </View>
              ))}
            </View>
          )}

          {/* Portfolio Positions */}
          {snapshot?.positions && snapshot.positions.length > 0 && (
            <>
              <Text style={styles.sectionTitle}>Top Positions</Text>
              {snapshot.positions.slice(0, 5).map((position, index) => (
                <View key={index} style={styles.positionCard}>
                  <View style={styles.positionInfo}>
                    <Text style={styles.positionSymbol}>{position.symbol}</Text>
                    <Text style={styles.positionShares}>
                      {position.shares} shares
                    </Text>
                  </View>
                  <Text style={styles.positionValue}>
                    {formatCurrency(position.value)}
                  </Text>
                </View>
              ))}
            </>
          )}
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
  content: {
    flex: 1,
    padding: 20,
  },
  summaryCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    marginBottom: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  summaryLabel: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 8,
  },
  summaryValue: {
    fontSize: 36,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  section: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  cashflowSectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
    marginTop: 8,
  },
  breakdownCard: {
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
  breakdownHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    gap: 12,
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  breakdownInfo: {
    flex: 1,
  },
  breakdownLabel: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 4,
  },
  breakdownValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  breakdownPercentage: {
    fontSize: 16,
    fontWeight: '700',
  },
  progressBar: {
    height: 8,
    backgroundColor: '#E5E5EA',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 4,
  },
  cashflowCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  cashflowRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
    gap: 12,
  },
  cashflowItem: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 8,
  },
  cashflowIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  cashflowLabel: {
    fontSize: 12,
    color: '#8E8E93',
    marginTop: 8,
    marginBottom: 4,
  },
  cashflowValue: {
    fontSize: 18,
    fontWeight: '700',
  },
  cashflowDelta: {
    paddingTop: 16,
    borderTopWidth: 2,
    borderTopColor: '#E5E5EA',
    marginTop: 8,
  },
  cashflowDeltaHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  cashflowDeltaLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  cashflowDeltaValue: {
    fontSize: 24,
    fontWeight: '700',
  },
  positionCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
  },
  positionInfo: {
    flex: 1,
  },
  positionSymbol: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 2,
  },
  positionShares: {
    fontSize: 12,
    color: '#8E8E93',
  },
  positionValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1C1C1E',
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
  recommendationCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E5EA',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  recommendationHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  recommendationIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  recommendationInfo: {
    flex: 1,
  },
  recommendationTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  recommendationDescription: {
    fontSize: 14,
    color: '#8E8E93',
    lineHeight: 20,
  },
  confidenceBadge: {
    backgroundColor: '#FFD70020',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  confidenceText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#FFD700',
  },
  recommendationAction: {
    marginTop: 8,
  },
  recommendationActionText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#007AFF',
    marginBottom: 8,
  },
  reasoningBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#FFF9E6',
    padding: 10,
    borderRadius: 8,
    gap: 8,
  },
  reasoningText: {
    fontSize: 12,
    color: '#856404',
    flex: 1,
    lineHeight: 16,
  },
});

export default DetailedBreakdownModal;

