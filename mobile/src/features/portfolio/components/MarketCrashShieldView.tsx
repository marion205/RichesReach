/**
 * MarketCrashShieldView
 * Shows protection strategies for market downturns
 * Triggered by swipe left gesture on Constellation Orb
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
import { constellationAIService, AIShieldAnalysis } from '../services/ConstellationAIService';

interface ShieldStrategy {
  id: string;
  title: string;
  description: string;
  icon: string;
  action: string;
  riskLevel: 'low' | 'medium' | 'high';
  impact: string;
  priority?: number;
  aiReasoning?: string;
  expectedImpact?: string;
}

interface MarketCrashShieldViewProps {
  visible: boolean;
  onClose: () => void;
  snapshot: MoneySnapshot;
}

export const MarketCrashShieldView: React.FC<MarketCrashShieldViewProps> = ({
  visible,
  onClose,
  snapshot,
}) => {
  const [activeStrategy, setActiveStrategy] = useState<string | null>(null);
  const [strategies, setStrategies] = useState<ShieldStrategy[]>([]);
  const [aiAnalysis, setAiAnalysis] = useState<AIShieldAnalysis | null>(null);
  const [loadingAI, setLoadingAI] = useState(true);
  const [aiEnabled, setAiEnabled] = useState(false);

  // Calculate portfolio risk metrics
  const portfolioValue = snapshot?.breakdown?.portfolioValue ?? 0;
  const bankBalance = snapshot?.breakdown?.bankBalance ?? 0;
  const totalExposure = portfolioValue;
  const cashReserve = bankBalance;
  const cashRatio = cashReserve / (cashReserve + portfolioValue || 1);

  // Fetch AI analysis when modal opens
  useEffect(() => {
    if (visible && snapshot) {
      loadAIShieldAnalysis();
    }
  }, [visible, snapshot]);

  const loadAIShieldAnalysis = async () => {
    try {
      setLoadingAI(true);
      const analysis = await constellationAIService.getAIShieldAnalysis(snapshot);
      
      if (analysis) {
        setAiAnalysis(analysis);
        
        // Merge AI recommendations with base strategies
        const baseStrategies = getFallbackStrategies();
        const aiStrategies = analysis.recommendedStrategies || [];
        
        // Enhance base strategies with AI data
        const enhancedStrategies = baseStrategies.map((strategy) => {
          const aiMatch = aiStrategies.find((ai: any) => ai.id === strategy.id);
          if (aiMatch) {
            return {
              ...strategy,
              priority: aiMatch.priority,
              aiReasoning: aiMatch.aiReasoning,
              expectedImpact: aiMatch.expectedImpact,
            };
          }
          return strategy;
        }).sort((a, b) => (b.priority || 0) - (a.priority || 0));
        
        setStrategies(enhancedStrategies);
        setAiEnabled(true);
      } else {
        setStrategies(getFallbackStrategies());
        setAiEnabled(false);
      }
    } catch (error) {
      console.warn('[MarketCrashShieldView] AI loading failed, using fallback:', error);
      setStrategies(getFallbackStrategies());
      setAiEnabled(false);
    } finally {
      setLoadingAI(false);
    }
  };

  // Generate fallback shield strategies
  const getFallbackStrategies = (): ShieldStrategy[] => {
    return [
      {
        id: 'increase-cash',
        title: 'Increase Cash Reserves',
        description: `Build cash buffer to ${(cashRatio * 100 + 10).toFixed(0)}% of portfolio`,
        icon: 'dollar-sign',
        action: 'Transfer funds to savings',
        riskLevel: 'low' as const,
        impact: 'Reduces portfolio volatility by 10-15%',
      },
      {
        id: 'pause-risky',
        title: 'Pause High-Risk Orders',
        description: 'Temporarily halt options trading and margin positions',
        icon: 'pause-circle',
      action: 'Auto-pause enabled',
      riskLevel: 'low',
      impact: 'Protects against margin calls during volatility',
    },
    {
      id: 'increase-cash',
      title: 'Increase Cash Reserve',
      description: `Move $${Math.floor(portfolioValue * 0.1).toLocaleString()} to cash buffer`,
      icon: 'shield',
      action: 'Rebalance to 20% cash',
      riskLevel: 'low',
      impact: `Adds $${Math.floor(portfolioValue * 0.1).toLocaleString()} safety buffer`,
    },
    {
      id: 'stop-loss',
      title: 'Set Stop-Loss Orders',
      description: 'Protect existing positions with 5-10% stop losses',
      icon: 'trending-down',
      action: 'Set stops on all positions',
      riskLevel: 'medium',
      impact: 'Limits downside to 5-10% per position',
    },
    {
      id: 'hedge-positions',
      title: 'Hedge with Inverse ETFs',
      description: 'Add defensive positions to offset portfolio risk',
      icon: 'activity',
      action: 'Add 10% hedge allocation',
      riskLevel: 'medium',
      impact: 'Reduces portfolio correlation to market',
    },
    ];
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return '#34C759';
      case 'medium': return '#FF9500';
      case 'high': return '#FF3B30';
      default: return '#8E8E93';
    }
  };

  const formatCurrency = (amount: number) => {
    if (amount >= 1000000) return `$${(amount / 1000000).toFixed(1)}M`;
    if (amount >= 1000) return `$${(amount / 1000).toFixed(1)}K`;
    return `$${amount.toFixed(0)}`;
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
              <Icon name="shield" size={24} color="#FF9500" />
              <Text style={styles.title}>Market Crash Shield</Text>
            </View>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Icon name="x" size={24} color="#8E8E93" />
            </TouchableOpacity>
          </View>
          <Text style={styles.subtitle}>
            Protect your portfolio during market volatility
          </Text>
        </View>

        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {/* Current Position Summary */}
          <View style={styles.summaryCard}>
            <Text style={styles.summaryTitle}>Current Position</Text>
            <View style={styles.summaryRow}>
              <View style={styles.summaryItem}>
                <Text style={styles.summaryLabel}>Portfolio Value</Text>
                <Text style={styles.summaryValue}>
                  {formatCurrency(portfolioValue)}
                </Text>
              </View>
              <View style={styles.summaryItem}>
                <Text style={styles.summaryLabel}>Cash Reserve</Text>
                <Text style={styles.summaryValue}>
                  {formatCurrency(cashReserve)}
                </Text>
              </View>
            </View>
            <View style={styles.riskIndicator}>
              <View style={styles.riskBar}>
                <View
                  style={[
                    styles.riskFill,
                    {
                      width: `${cashRatio * 100}%`,
                      backgroundColor: cashRatio > 0.2 ? '#34C759' : '#FF9500',
                    },
                  ]}
                />
              </View>
              <Text style={styles.riskText}>
                Cash Ratio: {(cashRatio * 100).toFixed(0)}%
                {cashRatio < 0.2 && ' (Consider increasing)'}
              </Text>
            </View>
          </View>

          {/* Shield Strategies */}
          <Text style={styles.sectionTitle}>Protection Strategies</Text>
          {strategies.map((strategy) => {
            const isActive = activeStrategy === strategy.id;
            const riskColor = getRiskColor(strategy.riskLevel);

            return (
              <TouchableOpacity
                key={strategy.id}
                style={[styles.strategyCard, isActive && styles.strategyCardActive]}
                onPress={() => setActiveStrategy(isActive ? null : strategy.id)}
                activeOpacity={0.7}
              >
                <View style={styles.strategyHeader}>
                  <View style={[styles.strategyIcon, { backgroundColor: `${riskColor}20` }]}>
                    <Icon name={strategy.icon as any} size={20} color={riskColor} />
                  </View>
                  <View style={styles.strategyInfo}>
                    <Text style={styles.strategyTitle}>{strategy.title}</Text>
                    <Text style={styles.strategyDescription}>{strategy.description}</Text>
                  </View>
                  <View style={[styles.riskBadge, { backgroundColor: `${riskColor}20` }]}>
                    <Text style={[styles.riskBadgeText, { color: riskColor }]}>
                      {strategy.riskLevel.toUpperCase()}
                    </Text>
                  </View>
                </View>

                {isActive && (
                  <View style={styles.strategyDetails}>
                    <View style={styles.actionBox}>
                      <Icon name="zap" size={16} color={riskColor} />
                      <Text style={[styles.actionText, { color: riskColor }]}>
                        {strategy.action}
                      </Text>
                    </View>
                    <View style={styles.impactBox}>
                      <Icon name="trending-up" size={16} color="#007AFF" />
                      <Text style={styles.impactText}>{strategy.impact}</Text>
                    </View>
                    <TouchableOpacity
                      style={[styles.applyButton, { backgroundColor: riskColor }]}
                      onPress={() => {
                        // TODO: Implement strategy application
                        onClose();
                      }}
                    >
                      <Text style={styles.applyButtonText}>Apply Strategy</Text>
                    </TouchableOpacity>
                  </View>
                )}
              </TouchableOpacity>
            );
          })}

          {/* Emergency Actions */}
          <View style={styles.emergencyCard}>
            <Icon name="alert-triangle" size={24} color="#FF3B30" />
            <Text style={styles.emergencyTitle}>Emergency Actions</Text>
            <Text style={styles.emergencyText}>
              In extreme market conditions, consider liquidating 20-30% of positions
              to cash for maximum protection.
            </Text>
            <TouchableOpacity
              style={styles.emergencyButton}
              onPress={() => {
                // TODO: Show emergency liquidation flow
                onClose();
              }}
            >
              <Text style={styles.emergencyButtonText}>View Emergency Options</Text>
            </TouchableOpacity>
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
  summaryCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginBottom: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  summaryTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 12,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  summaryItem: {
    flex: 1,
  },
  summaryLabel: {
    fontSize: 12,
    color: '#8E8E93',
    marginBottom: 4,
  },
  summaryValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  riskIndicator: {
    marginTop: 12,
  },
  riskBar: {
    height: 8,
    backgroundColor: '#E5E5EA',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 8,
  },
  riskFill: {
    height: '100%',
    borderRadius: 4,
  },
  riskText: {
    fontSize: 12,
    color: '#8E8E93',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 12,
  },
  strategyCard: {
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
  strategyCardActive: {
    borderWidth: 2,
    borderColor: '#007AFF',
  },
  strategyHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  strategyIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  strategyInfo: {
    flex: 1,
  },
  strategyTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  strategyDescription: {
    fontSize: 14,
    color: '#8E8E93',
  },
  riskBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  riskBadgeText: {
    fontSize: 10,
    fontWeight: '700',
  },
  strategyDetails: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  actionBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#F8F9FA',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
  },
  actionText: {
    fontSize: 14,
    fontWeight: '600',
    flex: 1,
  },
  impactBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#F0F8FF',
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
  },
  impactText: {
    fontSize: 14,
    color: '#007AFF',
    flex: 1,
  },
  applyButton: {
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
  },
  applyButtonText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  emergencyCard: {
    backgroundColor: '#FFF5F5',
    borderRadius: 16,
    padding: 16,
    marginTop: 8,
    borderWidth: 1,
    borderColor: '#FFE5E5',
    alignItems: 'center',
  },
  emergencyTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FF3B30',
    marginTop: 8,
    marginBottom: 8,
  },
  emergencyText: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
    marginBottom: 12,
  },
  emergencyButton: {
    backgroundColor: '#FF3B30',
    borderRadius: 8,
    padding: 12,
    paddingHorizontal: 24,
  },
  emergencyButtonText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
  },
});

export default MarketCrashShieldView;

