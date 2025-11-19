/**
 * GrowthProjectionView
 * Shows growth projections and scenarios
 * Triggered by swipe right gesture on Constellation Orb
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
import { constellationAIService, MLGrowthProjection } from '../services/ConstellationAIService';

interface ProjectionScenario {
  id: string;
  title: string;
  description: string;
  growthRate: number; // Annual percentage (ML-predicted)
  timeframe: number; // Months
  projectedValue: number;
  color: string;
  confidence?: number;
  mlFactors?: {
    marketRegime: string;
    volatility: number;
    momentum: number;
    riskLevel: string;
  };
}

interface GrowthProjectionViewProps {
  visible: boolean;
  onClose: () => void;
  snapshot: MoneySnapshot;
}

export const GrowthProjectionView: React.FC<GrowthProjectionViewProps> = ({
  visible,
  onClose,
  snapshot,
}) => {
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null);
  const [timeframe, setTimeframe] = useState<number>(12); // Default 12 months
  const [scenarios, setScenarios] = useState<ProjectionScenario[]>([]);
  const [loadingML, setLoadingML] = useState(true);
  const [mlEnabled, setMlEnabled] = useState(false);

  const currentValue = snapshot.netWorth;
  const monthlySurplus = snapshot.cashflow.delta;

  // Calculate projections based on different scenarios
  const calculateProjection = (growthRate: number, months: number, monthlyContribution: number) => {
    const monthlyRate = growthRate / 12 / 100;
    let futureValue = currentValue;
    
    for (let i = 0; i < months; i++) {
      futureValue = futureValue * (1 + monthlyRate) + monthlyContribution;
    }
    
    return futureValue;
  };

  // Fetch ML-enhanced projections when modal opens
  useEffect(() => {
    if (visible && snapshot) {
      loadMLProjections();
    }
  }, [visible, snapshot, timeframe]);

  const loadMLProjections = async () => {
    try {
      setLoadingML(true);
      const mlProjections = await constellationAIService.getMLGrowthProjections(
        snapshot,
        [6, 12, 24, 36]
      );

      if (mlProjections && mlProjections.length > 0) {
        // Filter projections for current timeframe and convert to scenarios
        const filteredProjections = mlProjections.filter(p => p.timeframe === timeframe);
        
        if (filteredProjections.length > 0) {
          const convertedScenarios: ProjectionScenario[] = filteredProjections.map((mlProj, index) => {
            const scenarioNames = ['Conservative', 'Moderate', 'Aggressive', 'Very Aggressive', 'Dividend Focus', 'Balanced'];
            const scenarioColors = ['#34C759', '#007AFF', '#FF9500', '#FF3B30', '#AF52DE', '#5AC8FA'];
            
            return {
              id: mlProj.scenario.toLowerCase().replace(/\s+/g, '-'),
              title: mlProj.scenario,
              description: `${mlProj.mlFactors.marketRegime} market • ${mlProj.mlFactors.riskLevel} risk`,
              growthRate: mlProj.growthRate,
              timeframe: mlProj.timeframe,
              projectedValue: mlProj.projectedValue,
              color: scenarioColors[index % scenarioColors.length],
              confidence: mlProj.confidence,
              mlFactors: mlProj.mlFactors,
            };
          });
          
          setScenarios(convertedScenarios);
          setMlEnabled(true);
        } else {
          // Use fallback if no ML data for this timeframe
          setScenarios(getFallbackScenarios());
          setMlEnabled(false);
        }
      } else {
        setScenarios(getFallbackScenarios());
        setMlEnabled(false);
      }
    } catch (error) {
      console.warn('[GrowthProjectionView] ML loading failed, using fallback:', error);
      setScenarios(getFallbackScenarios());
      setMlEnabled(false);
    } finally {
      setLoadingML(false);
    }
  };

  const getFallbackScenarios = (): ProjectionScenario[] => {
    return [
      {
        id: 'conservative',
        title: 'Conservative Growth',
        description: 'Low-vol ETF allocation (5% annual)',
        growthRate: 5,
        timeframe: timeframe,
        projectedValue: calculateProjection(5, timeframe, monthlySurplus * 0.3),
        color: '#34C759',
      },
      {
        id: 'moderate',
        title: 'Moderate Growth',
        description: 'Balanced portfolio (8% annual)',
        growthRate: 8,
        timeframe: timeframe,
        projectedValue: calculateProjection(8, timeframe, monthlySurplus * 0.5),
        color: '#007AFF',
      },
      {
        id: 'aggressive',
        title: 'Aggressive Growth',
        description: 'Growth-focused allocation (12% annual)',
        growthRate: 12,
        timeframe: timeframe,
        projectedValue: calculateProjection(12, timeframe, monthlySurplus * 0.7),
        color: '#FF9500',
      },
      {
        id: 'very-aggressive',
        title: 'Very Aggressive',
        description: 'High-risk, high-reward (15% annual)',
        growthRate: 15,
        timeframe: timeframe,
        projectedValue: calculateProjection(15, timeframe, monthlySurplus * 0.8),
        color: '#FF3B30',
      },
      {
        id: 'dividend',
        title: 'Dividend Focus',
        description: 'Income-generating portfolio (6% annual + dividends)',
        growthRate: 6,
        timeframe: timeframe,
        projectedValue: calculateProjection(6, timeframe, monthlySurplus * 0.4),
        color: '#AF52DE',
      },
      {
        id: 'balanced',
        title: 'Balanced Approach',
        description: 'Mix of growth and stability (7% annual)',
        growthRate: 7,
        timeframe: timeframe,
        projectedValue: calculateProjection(7, timeframe, monthlySurplus * 0.45),
        color: '#5AC8FA',
      },
    ];
  };

  const formatCurrency = (amount: number) => {
    if (amount >= 1000000) return `$${(amount / 1000000).toFixed(1)}M`;
    if (amount >= 1000) return `$${(amount / 1000).toFixed(1)}K`;
    return `$${amount.toFixed(0)}`;
  };

  const getGrowthAmount = (projected: number) => {
    return projected - currentValue;
  };

  const getGrowthPercent = (projected: number) => {
    return ((projected - currentValue) / currentValue) * 100;
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
              <Icon name="trending-up" size={24} color="#34C759" />
              <Text style={styles.title}>Growth Projection</Text>
              {mlEnabled && (
                <View style={styles.mlBadge}>
                  <Icon name="cpu" size={12} color="#007AFF" />
                  <Text style={styles.mlBadgeText}>ML</Text>
                </View>
              )}
            </View>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Icon name="x" size={24} color="#8E8E93" />
            </TouchableOpacity>
          </View>
          <Text style={styles.subtitle}>
            {mlEnabled 
              ? 'ML-predicted growth rates based on current market conditions' 
              : 'See where your wealth could be in the future'}
          </Text>
        </View>

        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {loadingML && (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="small" color="#007AFF" />
              <Text style={styles.loadingText}>Loading ML predictions...</Text>
            </View>
          )}
          {/* Current Value */}
          <View style={styles.currentCard}>
            <Text style={styles.currentLabel}>Current Net Worth</Text>
            <Text style={styles.currentValue}>{formatCurrency(currentValue)}</Text>
            <Text style={styles.currentSubtext}>
              Monthly surplus: {formatCurrency(monthlySurplus)}
            </Text>
          </View>

          {/* Timeframe Selector */}
          <View style={styles.timeframeContainer}>
            <Text style={styles.timeframeLabel}>Projection Period</Text>
            <View style={styles.timeframeButtons}>
              {[6, 12, 24, 36].map((months) => (
                <TouchableOpacity
                  key={months}
                  style={[
                    styles.timeframeButton,
                    timeframe === months && styles.timeframeButtonActive,
                  ]}
                  onPress={() => setTimeframe(months)}
                >
                  <Text
                    style={[
                      styles.timeframeButtonText,
                      timeframe === months && styles.timeframeButtonTextActive,
                    ]}
                  >
                    {months}M
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Scenarios */}
          <Text style={styles.sectionTitle}>Growth Scenarios</Text>
          {scenarios.map((scenario) => {
            const growth = getGrowthAmount(scenario.projectedValue);
            const growthPercent = getGrowthPercent(scenario.projectedValue);
            const isSelected = selectedScenario === scenario.id;

            return (
              <TouchableOpacity
                key={scenario.id}
                style={[styles.scenarioCard, isSelected && styles.scenarioCardActive]}
                onPress={() => setSelectedScenario(isSelected ? null : scenario.id)}
                activeOpacity={0.7}
              >
                <View style={styles.scenarioHeader}>
                  <View style={[styles.scenarioIcon, { backgroundColor: `${scenario.color}20` }]}>
                    <Icon name="trending-up" size={20} color={scenario.color} />
                  </View>
                  <View style={styles.scenarioInfo}>
                    <Text style={styles.scenarioTitle}>{scenario.title}</Text>
                    <Text style={styles.scenarioDescription}>{scenario.description}</Text>
                  </View>
                  <View style={styles.growthBadge}>
                    <Text style={[styles.growthBadgeText, { color: scenario.color }]}>
                      +{scenario.growthRate}%
                    </Text>
                  </View>
                </View>

                <View style={styles.projectionRow}>
                  <View style={styles.projectionItem}>
                    <Text style={styles.projectionLabel}>Projected Value</Text>
                    <Text style={[styles.projectionValue, { color: scenario.color }]}>
                      {formatCurrency(scenario.projectedValue)}
                    </Text>
                  </View>
                  <View style={styles.projectionItem}>
                    <Text style={styles.projectionLabel}>Growth</Text>
                    <Text style={[styles.projectionValue, { color: scenario.color }]}>
                      +{formatCurrency(growth)} ({growthPercent.toFixed(1)}%)
                    </Text>
                  </View>
                </View>

                {isSelected && (
                  <View style={styles.scenarioDetails}>
                    <View style={styles.assumptionBox}>
                      <Icon name="info" size={16} color="#007AFF" />
                      <Text style={styles.assumptionText}>
                        Assumes {formatCurrency(monthlySurplus * 0.5)}/mo contribution
                        and {scenario.growthRate}% annual growth
                      </Text>
                    </View>
                    {scenario.mlFactors && (
                      <View style={styles.mlFactorsBox}>
                        <View style={styles.mlFactorsHeader}>
                          <Icon name="cpu" size={14} color="#007AFF" />
                          <Text style={styles.mlFactorsTitle}>ML Analysis</Text>
                          {scenario.confidence && (
                            <Text style={styles.mlConfidence}>
                              {Math.round(scenario.confidence * 100)}% confidence
                            </Text>
                          )}
                        </View>
                        <View style={styles.mlFactorsGrid}>
                          <View style={styles.mlFactorItem}>
                            <Text style={styles.mlFactorLabel}>Market Regime</Text>
                            <Text style={styles.mlFactorValue}>{scenario.mlFactors.marketRegime}</Text>
                          </View>
                          <View style={styles.mlFactorItem}>
                            <Text style={styles.mlFactorLabel}>Volatility</Text>
                            <Text style={styles.mlFactorValue}>{(scenario.mlFactors.volatility * 100).toFixed(1)}%</Text>
                          </View>
                          <View style={styles.mlFactorItem}>
                            <Text style={styles.mlFactorLabel}>Momentum</Text>
                            <Text style={styles.mlFactorValue}>{(scenario.mlFactors.momentum * 100).toFixed(0)}%</Text>
                          </View>
                          <View style={styles.mlFactorItem}>
                            <Text style={styles.mlFactorLabel}>Risk Level</Text>
                            <Text style={styles.mlFactorValue}>{scenario.mlFactors.riskLevel}</Text>
                          </View>
                        </View>
                      </View>
                    )}
                    <TouchableOpacity
                      style={[styles.actionButton, { backgroundColor: scenario.color }]}
                      onPress={() => {
                        // Future enhancement: Navigate to portfolio allocation screen with scenario applied
                        onClose();
                      }}
                    >
                      <Text style={styles.actionButtonText}>Optimize for This Scenario</Text>
                    </TouchableOpacity>
                  </View>
                )}
              </TouchableOpacity>
            );
          })}

          {/* Disclaimer */}
          <View style={styles.disclaimerCard}>
            <Icon name="alert-circle" size={16} color="#8E8E93" />
            <Text style={styles.disclaimerText}>
              Projections are estimates based on historical averages and do not guarantee future results.
              Past performance is not indicative of future returns.
            </Text>
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
  mlBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#007AFF20',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    gap: 4,
  },
  mlBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#007AFF',
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
  currentCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  currentLabel: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 8,
  },
  currentValue: {
    fontSize: 32,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  currentSubtext: {
    fontSize: 12,
    color: '#8E8E93',
  },
  timeframeContainer: {
    marginBottom: 24,
  },
  timeframeLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 12,
  },
  timeframeButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  timeframeButton: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E5E5EA',
    alignItems: 'center',
  },
  timeframeButtonActive: {
    backgroundColor: '#34C759',
    borderColor: '#34C759',
  },
  timeframeButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  timeframeButtonTextActive: {
    color: '#FFFFFF',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 12,
  },
  scenarioCard: {
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
  scenarioCardActive: {
    borderWidth: 2,
    borderColor: '#34C759',
  },
  scenarioHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    gap: 12,
  },
  scenarioIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  scenarioInfo: {
    flex: 1,
  },
  scenarioTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  scenarioDescription: {
    fontSize: 12,
    color: '#8E8E93',
  },
  growthBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    backgroundColor: '#F8F9FA',
  },
  growthBadgeText: {
    fontSize: 12,
    fontWeight: '700',
  },
  projectionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  projectionItem: {
    flex: 1,
  },
  projectionLabel: {
    fontSize: 12,
    color: '#8E8E93',
    marginBottom: 4,
  },
  projectionValue: {
    fontSize: 16,
    fontWeight: '700',
  },
  scenarioDetails: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  assumptionBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    backgroundColor: '#F0F8FF',
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
  },
  assumptionText: {
    fontSize: 12,
    color: '#007AFF',
    flex: 1,
  },
  actionButton: {
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
  },
  actionButtonText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  disclaimerCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    backgroundColor: '#FFF5E6',
    padding: 12,
    borderRadius: 8,
    marginTop: 8,
  },
  disclaimerText: {
    fontSize: 11,
    color: '#8E8E93',
    flex: 1,
    lineHeight: 16,
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
  mlFactorsBox: {
    marginTop: 12,
    backgroundColor: '#F0F8FF',
    borderRadius: 8,
    padding: 12,
    borderLeftWidth: 3,
    borderLeftColor: '#007AFF',
  },
  mlFactorsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 12,
  },
  mlFactorsTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#007AFF',
    flex: 1,
  },
  mlConfidence: {
    fontSize: 10,
    fontWeight: '600',
    color: '#007AFF',
    backgroundColor: '#007AFF20',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  mlFactorsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  mlFactorItem: {
    flex: 1,
    minWidth: '45%',
  },
  mlFactorLabel: {
    fontSize: 11,
    color: '#8E8E93',
    marginBottom: 4,
  },
  mlFactorValue: {
    fontSize: 14,
    fontWeight: '700',
    color: '#007AFF',
  },
});

export default GrowthProjectionView;

