/**
 * Credit Twin Simulator - What-If Scenario Branching
 * Interactive tool to simulate credit decisions and see outcomes
 */

import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Modal } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { CreditTwinState, CreditTwinScenario } from '../types/CreditTypes';

interface CreditTwinSimulatorProps {
  initialState: CreditTwinState;
  scenarios: CreditTwinScenario[];
  onScenarioSelect: (scenario: CreditTwinScenario) => void;
  onReset: () => void;
}

export const CreditTwinSimulator: React.FC<CreditTwinSimulatorProps> = ({
  initialState,
  scenarios,
  onScenarioSelect,
  onReset,
}) => {
  const [visible, setVisible] = useState(false);
  const [currentState, setCurrentState] = useState<CreditTwinState>(initialState);
  const [selectedScenario, setSelectedScenario] = useState<CreditTwinScenario | null>(null);

  const handleScenarioSelect = (scenario: CreditTwinScenario) => {
    setSelectedScenario(scenario);
    const newScore = currentState.projectedScore + scenario.projectedOutcome.scoreChange;
    setCurrentState({
      ...currentState,
      projectedScore: Math.max(300, Math.min(850, newScore)),
      currentScenario: scenario,
      scenarioHistory: [...currentState.scenarioHistory, scenario],
    });
    onScenarioSelect(scenario);
  };

  const handleReset = () => {
    setCurrentState(initialState);
    setSelectedScenario(null);
    onReset();
  };

  const getScoreColor = (score: number) => {
    if (score >= 750) return '#34C759';
    if (score >= 700) return '#5AC8FA';
    if (score >= 650) return '#FF9500';
    return '#FF3B30';
  };

  const getScoreRange = (score: number) => {
    if (score >= 800) return 'Excellent';
    if (score >= 740) return 'Very Good';
    if (score >= 670) return 'Good';
    if (score >= 580) return 'Fair';
    return 'Poor';
  };

  return (
    <>
      <TouchableOpacity
        style={styles.triggerButton}
        onPress={() => setVisible(true)}
        activeOpacity={0.7}
      >
        <Icon name="git-branch" size={20} color="#007AFF" />
        <Text style={styles.triggerText}>Credit Twin Simulator</Text>
      </TouchableOpacity>

      <Modal
        visible={visible}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setVisible(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <View>
              <Text style={styles.modalTitle}>Credit Twin</Text>
              <Text style={styles.modalSubtitle}>Simulate decisions, see outcomes</Text>
            </View>
            <TouchableOpacity onPress={() => setVisible(false)}>
              <Icon name="x" size={24} color="#8E8E93" />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalContent}>
            {/* Current State */}
            <View style={styles.stateBox}>
              <View style={styles.stateHeader}>
                <Text style={styles.stateLabel}>Base Score</Text>
                <Text style={[styles.stateScore, { color: getScoreColor(currentState.baseScore) }]}>
                  {currentState.baseScore}
                </Text>
                <Text style={styles.stateRange}>{getScoreRange(currentState.baseScore)}</Text>
              </View>
              <View style={styles.stateDivider} />
              <View style={styles.stateHeader}>
                <Text style={styles.stateLabel}>Projected Score</Text>
                <Text style={[styles.stateScore, { color: getScoreColor(currentState.projectedScore) }]}>
                  {currentState.projectedScore}
                </Text>
                <Text style={styles.stateRange}>{getScoreRange(currentState.projectedScore)}</Text>
              </View>
              {currentState.projectedScore !== currentState.baseScore && (
                <View style={styles.changeBox}>
                  <Icon 
                    name={currentState.projectedScore > currentState.baseScore ? "trending-up" : "trending-down"} 
                    size={16} 
                    color={currentState.projectedScore > currentState.baseScore ? "#34C759" : "#FF3B30"} 
                  />
                  <Text style={[
                    styles.changeText,
                    { color: currentState.projectedScore > currentState.baseScore ? "#34C759" : "#FF3B30" }
                  ]}>
                    {currentState.projectedScore > currentState.baseScore ? '+' : ''}
                    {currentState.projectedScore - currentState.baseScore} points
                  </Text>
                </View>
              )}
            </View>

            {/* Scenario History */}
            {currentState.scenarioHistory.length > 0 && (
              <View style={styles.historyBox}>
                <Text style={styles.sectionTitle}>Scenario Timeline</Text>
                {currentState.scenarioHistory.map((scenario, index) => (
                  <View key={index} style={styles.historyItem}>
                    <View style={styles.historyIcon}>
                      <Icon name="git-commit" size={16} color="#007AFF" />
                    </View>
                    <View style={styles.historyContent}>
                      <Text style={styles.historyName}>{scenario.name}</Text>
                      <Text style={styles.historyOutcome}>
                        {scenario.projectedOutcome.scoreChange > 0 ? '+' : ''}
                        {scenario.projectedOutcome.scoreChange} points • {scenario.projectedOutcome.timeToImpact}
                      </Text>
                    </View>
                  </View>
                ))}
                <TouchableOpacity style={styles.resetButton} onPress={handleReset}>
                  <Icon name="refresh-cw" size={16} color="#FF3B30" />
                  <Text style={styles.resetText}>Reset Simulation</Text>
                </TouchableOpacity>
              </View>
            )}

            {/* Available Scenarios */}
            <View style={styles.scenariosBox}>
              <Text style={styles.sectionTitle}>What If Scenarios</Text>
              {scenarios.map((scenario) => (
                <TouchableOpacity
                  key={scenario.id}
                  style={styles.scenarioCard}
                  onPress={() => handleScenarioSelect(scenario)}
                  activeOpacity={0.7}
                >
                  <View style={styles.scenarioHeader}>
                    <Text style={styles.scenarioName}>{scenario.name}</Text>
                    <Icon name="chevron-right" size={20} color="#8E8E93" />
                  </View>
                  <Text style={styles.scenarioDescription}>{scenario.description}</Text>
                  <View style={styles.scenarioOutcome}>
                    <Icon 
                      name={scenario.projectedOutcome.scoreChange >= 0 ? "trending-up" : "trending-down"} 
                      size={16} 
                      color={scenario.projectedOutcome.scoreChange >= 0 ? "#34C759" : "#FF3B30"} 
                    />
                    <Text style={[
                      styles.scenarioImpact,
                      { color: scenario.projectedOutcome.scoreChange >= 0 ? "#34C759" : "#FF3B30" }
                    ]}>
                      {scenario.projectedOutcome.scoreChange >= 0 ? '+' : ''}
                      {scenario.projectedOutcome.scoreChange} points
                    </Text>
                    <Text style={styles.scenarioTime}>
                      • {scenario.projectedOutcome.timeToImpact}
                    </Text>
                  </View>
                </TouchableOpacity>
              ))}
            </View>

            {/* Selected Scenario Details */}
            {selectedScenario && (
              <View style={styles.detailsBox}>
                <Text style={styles.detailsTitle}>Scenario Details</Text>
                <Text style={styles.detailsName}>{selectedScenario.name}</Text>
                <Text style={styles.detailsDescription}>{selectedScenario.description}</Text>
                
                <View style={styles.factorsBox}>
                  <Text style={styles.factorsTitle}>Affected Factors:</Text>
                  {selectedScenario.projectedOutcome.factors.map((factor, index) => (
                    <View key={index} style={styles.factorItem}>
                      <Icon name="check-circle" size={14} color="#34C759" />
                      <Text style={styles.factorText}>{factor}</Text>
                    </View>
                  ))}
                </View>

                {selectedScenario.branches && selectedScenario.branches.length > 0 && (
                  <View style={styles.branchesBox}>
                    <Text style={styles.branchesTitle}>Next Steps:</Text>
                    {selectedScenario.branches.map((branch) => (
                      <TouchableOpacity
                        key={branch.id}
                        style={styles.branchCard}
                        onPress={() => handleScenarioSelect(branch)}
                      >
                        <Text style={styles.branchName}>{branch.name}</Text>
                        <Text style={styles.branchDescription}>{branch.description}</Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                )}
              </View>
            )}
          </ScrollView>
        </View>
      </Modal>
    </>
  );
};

const styles = StyleSheet.create({
  triggerButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#E3F2FD',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#007AFF',
  },
  triggerText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#007AFF',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  modalTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  modalSubtitle: {
    fontSize: 14,
    color: '#8E8E93',
    marginTop: 4,
  },
  modalContent: {
    flex: 1,
    padding: 20,
  },
  stateBox: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  stateHeader: {
    alignItems: 'center',
    marginBottom: 16,
  },
  stateLabel: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 8,
  },
  stateScore: {
    fontSize: 48,
    fontWeight: '700',
    marginBottom: 4,
  },
  stateRange: {
    fontSize: 16,
    color: '#8E8E93',
    fontWeight: '600',
  },
  stateDivider: {
    height: 1,
    backgroundColor: '#E5E5EA',
    marginVertical: 16,
  },
  changeBox: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginTop: 8,
  },
  changeText: {
    fontSize: 16,
    fontWeight: '700',
  },
  historyBox: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 16,
  },
  historyItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F2F2F7',
  },
  historyIcon: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#E3F2FD',
    alignItems: 'center',
    justifyContent: 'center',
  },
  historyContent: {
    flex: 1,
  },
  historyName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  historyOutcome: {
    fontSize: 13,
    color: '#8E8E93',
  },
  resetButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    padding: 12,
    backgroundColor: '#FEF2F2',
    borderRadius: 8,
    marginTop: 8,
  },
  resetText: {
    fontSize: 14,
    color: '#FF3B30',
    fontWeight: '600',
  },
  scenariosBox: {
    marginBottom: 20,
  },
  scenarioCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  scenarioHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  scenarioName: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  scenarioDescription: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 12,
    lineHeight: 20,
  },
  scenarioOutcome: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  scenarioImpact: {
    fontSize: 14,
    fontWeight: '700',
  },
  scenarioTime: {
    fontSize: 13,
    color: '#8E8E93',
  },
  detailsBox: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
  },
  detailsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#007AFF',
    textTransform: 'uppercase',
    marginBottom: 12,
  },
  detailsName: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 8,
  },
  detailsDescription: {
    fontSize: 14,
    color: '#8E8E93',
    lineHeight: 20,
    marginBottom: 16,
  },
  factorsBox: {
    marginBottom: 16,
  },
  factorsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 8,
  },
  factorItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 6,
  },
  factorText: {
    fontSize: 13,
    color: '#8E8E93',
  },
  branchesBox: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  branchesTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 12,
  },
  branchCard: {
    backgroundColor: '#F8F9FA',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
  },
  branchName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  branchDescription: {
    fontSize: 13,
    color: '#8E8E93',
  },
});

