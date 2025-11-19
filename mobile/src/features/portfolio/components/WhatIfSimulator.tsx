/**
 * WhatIfSimulator
 * Interactive what-if calculator for financial scenarios
 * Triggered by pinch gesture on Constellation Orb
 */

import React, { useState, useMemo } from 'react';
import {
  Modal,
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  TextInput,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/Feather';
import { MoneySnapshot } from '../services/MoneySnapshotService';

interface WhatIfSimulatorProps {
  visible: boolean;
  onClose: () => void;
  snapshot: MoneySnapshot;
}

export const WhatIfSimulator: React.FC<WhatIfSimulatorProps> = ({
  visible,
  onClose,
  snapshot,
}) => {
  const [monthlyContribution, setMonthlyContribution] = useState(
    Math.max(100, Math.floor(snapshot.cashflow.delta * 0.3)).toString()
  );
  const [annualGrowth, setAnnualGrowth] = useState('8');
  const [timeframe, setTimeframe] = useState('12');
  const [selectedScenario, setSelectedScenario] = useState<'contribution' | 'growth' | 'time'>('contribution');

  // Calculate projection
  const projection = useMemo(() => {
    const contribution = parseFloat(monthlyContribution) || 0;
    const growth = parseFloat(annualGrowth) || 0;
    const months = parseInt(timeframe) || 12;
    
    const monthlyRate = growth / 12 / 100;
    let futureValue = snapshot.netWorth;
    
    for (let i = 0; i < months; i++) {
      futureValue = futureValue * (1 + monthlyRate) + contribution;
    }
    
    return {
      futureValue,
      totalContributed: contribution * months,
      growthAmount: futureValue - snapshot.netWorth - (contribution * months),
      growthPercent: ((futureValue - snapshot.netWorth) / snapshot.netWorth) * 100,
    };
  }, [monthlyContribution, annualGrowth, timeframe, snapshot.netWorth]);

  const formatCurrency = (amount: number) => {
    if (amount >= 1000000) return `$${(amount / 1000000).toFixed(2)}M`;
    if (amount >= 1000) return `$${(amount / 1000).toFixed(1)}K`;
    return `$${amount.toFixed(0)}`;
  };

  const quickScenarios = [
    { label: 'Shift $200/mo from dining', contribution: 200, growth: 8 },
    { label: 'Invest 50% of surplus', contribution: Math.floor(snapshot.cashflow.delta * 0.5), growth: 8 },
    { label: 'Aggressive growth (12%)', contribution: Math.floor(snapshot.cashflow.delta * 0.3), growth: 12 },
    { label: 'Conservative (5%)', contribution: Math.floor(snapshot.cashflow.delta * 0.3), growth: 5 },
  ];

  const applyQuickScenario = (contribution: number, growth: number) => {
    setMonthlyContribution(contribution.toString());
    setAnnualGrowth(growth.toString());
    setSelectedScenario('contribution');
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
              <Icon name="sliders" size={24} color="#007AFF" />
              <Text style={styles.title}>What-If Simulator</Text>
            </View>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Icon name="x" size={24} color="#8E8E93" />
            </TouchableOpacity>
          </View>
          <Text style={styles.subtitle}>
            Adjust parameters to see how your wealth could grow
          </Text>
        </View>

        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {/* Current vs Projected */}
          <View style={styles.comparisonCard}>
            <View style={styles.comparisonItem}>
              <Text style={styles.comparisonLabel}>Current</Text>
              <Text style={styles.comparisonValue}>
                {formatCurrency(snapshot.netWorth)}
              </Text>
            </View>
            <Icon name="arrow-right" size={20} color="#8E8E93" />
            <View style={styles.comparisonItem}>
              <Text style={styles.comparisonLabel}>Projected</Text>
              <Text style={[styles.comparisonValue, styles.comparisonValueProjected]}>
                {formatCurrency(projection.futureValue)}
              </Text>
            </View>
          </View>

          {/* Quick Scenarios */}
          <Text style={styles.sectionTitle}>Quick Scenarios</Text>
          <View style={styles.quickScenarios}>
            {quickScenarios.map((scenario, index) => (
              <TouchableOpacity
                key={index}
                style={styles.quickScenarioButton}
                onPress={() => applyQuickScenario(scenario.contribution, scenario.growth)}
              >
                <Text style={styles.quickScenarioText}>{scenario.label}</Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* Input Controls */}
          <Text style={styles.sectionTitle}>Adjust Parameters</Text>

          {/* Monthly Contribution */}
          <View style={styles.inputCard}>
            <View style={styles.inputHeader}>
              <Icon name="dollar-sign" size={20} color="#34C759" />
              <Text style={styles.inputLabel}>Monthly Contribution</Text>
            </View>
            <View style={styles.inputRow}>
              <TextInput
                style={styles.input}
                value={monthlyContribution}
                onChangeText={setMonthlyContribution}
                keyboardType="numeric"
                placeholder="0"
              />
              <View style={styles.inputButtons}>
                <TouchableOpacity
                  style={styles.inputButton}
                  onPress={() => {
                    const val = Math.max(0, (parseFloat(monthlyContribution) || 0) - 50);
                    setMonthlyContribution(val.toString());
                  }}
                >
                  <Icon name="minus" size={16} color="#8E8E93" />
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.inputButton}
                  onPress={() => {
                    const val = (parseFloat(monthlyContribution) || 0) + 50;
                    setMonthlyContribution(val.toString());
                  }}
                >
                  <Icon name="plus" size={16} color="#8E8E93" />
                </TouchableOpacity>
              </View>
            </View>
            <Text style={styles.inputHint}>
              Current surplus: {formatCurrency(snapshot.cashflow.delta)}/mo
            </Text>
          </View>

          {/* Annual Growth Rate */}
          <View style={styles.inputCard}>
            <View style={styles.inputHeader}>
              <Icon name="trending-up" size={20} color="#007AFF" />
              <Text style={styles.inputLabel}>Annual Growth Rate (%)</Text>
            </View>
            <View style={styles.inputRow}>
              <TextInput
                style={styles.input}
                value={annualGrowth}
                onChangeText={setAnnualGrowth}
                keyboardType="numeric"
                placeholder="8"
              />
              <View style={styles.sliderButtons}>
                {[5, 8, 10, 12].map((rate) => (
                  <TouchableOpacity
                    key={rate}
                    style={[
                      styles.sliderButton,
                      parseFloat(annualGrowth) === rate && styles.sliderButtonActive,
                    ]}
                    onPress={() => setAnnualGrowth(rate.toString())}
                  >
                    <Text
                      style={[
                        styles.sliderButtonText,
                        parseFloat(annualGrowth) === rate && styles.sliderButtonTextActive,
                      ]}
                    >
                      {rate}%
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
            <Text style={styles.inputHint}>
              Historical average: 8-10% for balanced portfolios
            </Text>
          </View>

          {/* Timeframe */}
          <View style={styles.inputCard}>
            <View style={styles.inputHeader}>
              <Icon name="calendar" size={20} color="#FF9500" />
              <Text style={styles.inputLabel}>Timeframe (months)</Text>
            </View>
            <View style={styles.inputRow}>
              <TextInput
                style={styles.input}
                value={timeframe}
                onChangeText={setTimeframe}
                keyboardType="numeric"
                placeholder="12"
              />
              <View style={styles.sliderButtons}>
                {[6, 12, 24, 36].map((months) => (
                  <TouchableOpacity
                    key={months}
                    style={[
                      styles.sliderButton,
                      parseInt(timeframe) === months && styles.sliderButtonActive,
                    ]}
                    onPress={() => setTimeframe(months.toString())}
                  >
                    <Text
                      style={[
                        styles.sliderButtonText,
                        parseInt(timeframe) === months && styles.sliderButtonTextActive,
                      ]}
                    >
                      {months}M
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </View>

          {/* Results Breakdown */}
          <View style={styles.resultsCard}>
            <Text style={styles.resultsTitle}>Projection Breakdown</Text>
            <View style={styles.resultsRow}>
              <Text style={styles.resultsLabel}>Total Contributed</Text>
              <Text style={styles.resultsValue}>
                {formatCurrency(projection.totalContributed)}
              </Text>
            </View>
            <View style={styles.resultsRow}>
              <Text style={styles.resultsLabel}>Growth</Text>
              <Text style={[styles.resultsValue, { color: '#34C759' }]}>
                +{formatCurrency(projection.growthAmount)}
              </Text>
            </View>
            <View style={styles.resultsRow}>
              <Text style={styles.resultsLabel}>Total Growth</Text>
              <Text style={[styles.resultsValue, { color: '#34C759', fontSize: 18 }]}>
                +{projection.growthPercent.toFixed(1)}%
              </Text>
            </View>
          </View>

          {/* Action Button */}
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => {
              // Future enhancement: Save scenario to user's saved scenarios or create investment plan
              onClose();
            }}
          >
            <Icon name="target" size={20} color="#FFFFFF" />
            <Text style={styles.actionButtonText}>Create Plan from This Scenario</Text>
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
  comparisonCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  comparisonItem: {
    flex: 1,
    alignItems: 'center',
  },
  comparisonLabel: {
    fontSize: 12,
    color: '#8E8E93',
    marginBottom: 8,
  },
  comparisonValue: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  comparisonValueProjected: {
    color: '#34C759',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 12,
  },
  quickScenarios: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 24,
  },
  quickScenarioButton: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  quickScenarioText: {
    fontSize: 12,
    color: '#1C1C1E',
    fontWeight: '500',
  },
  inputCard: {
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
  inputHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  inputLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#E5E5EA',
    borderRadius: 8,
    padding: 12,
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  inputButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  inputButton: {
    width: 40,
    height: 40,
    borderRadius: 8,
    backgroundColor: '#F8F9FA',
    alignItems: 'center',
    justifyContent: 'center',
  },
  inputHint: {
    fontSize: 12,
    color: '#8E8E93',
    marginTop: 8,
  },
  sliderButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  sliderButton: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    backgroundColor: '#F8F9FA',
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  sliderButtonActive: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  sliderButtonText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  sliderButtonTextActive: {
    color: '#FFFFFF',
  },
  resultsCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginTop: 8,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  resultsTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 16,
  },
  resultsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  resultsLabel: {
    fontSize: 14,
    color: '#8E8E93',
  },
  resultsValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1C1C1E',
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
});

export default WhatIfSimulator;

