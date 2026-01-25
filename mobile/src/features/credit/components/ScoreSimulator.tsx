/**
 * Score Simulator - 3-Slider Interactive Tool
 * Shows score impact from utilization, payment history, and inquiries
 */

import React, { useState, useCallback, useMemo } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Modal, ScrollView } from 'react-native';
import Slider from '@react-native-community/slider';
import Icon from 'react-native-vector-icons/Feather';
import { ScoreSimulatorInputs, ScoreSimulation } from '../types/CreditTypes';
import logger from '../../../utils/logger';


interface ScoreSimulatorProps {
  currentScore: number;
  onSimulate: (inputs: ScoreSimulatorInputs) => ScoreSimulation;
}

function ScoreSimulator({
  currentScore,
  onSimulate,
}: ScoreSimulatorProps) {
  const [visible, setVisible] = useState(false);
  const [inputs, setInputs] = useState<ScoreSimulatorInputs>({
    utilizationPercent: 30,
    onTimeStreak: 12,
    recentInquiries: 0,
  });

  // Safely get simulation with fallback
  let simulation: ScoreSimulation;
  try {
    simulation = onSimulate ? onSimulate(inputs) : {
      minScore: currentScore - 30,
      likelyScore: currentScore,
      maxScore: currentScore + 30,
      timeToImpact: '1-2 cycles',
      factors: {
        utilization: { impact: 0, note: 'Unable to calculate' },
        paymentHistory: { impact: 0, note: 'Unable to calculate' },
        inquiries: { impact: 0, note: 'Unable to calculate' },
      },
    };
  } catch (error) {
    logger.error('ScoreSimulator: onSimulate error', error);
    simulation = {
      minScore: currentScore - 30,
      likelyScore: currentScore,
      maxScore: currentScore + 30,
      timeToImpact: '1-2 cycles',
      factors: {
        utilization: { impact: 0, note: 'Unable to calculate' },
        paymentHistory: { impact: 0, note: 'Unable to calculate' },
        inquiries: { impact: 0, note: 'Unable to calculate' },
      },
    };
  }

  const handleUtilizationChange = useCallback((value: number) => {
    setInputs(prev => ({ ...prev, utilizationPercent: value }));
  }, []);

  const handleStreakChange = useCallback((value: number) => {
    setInputs(prev => ({ ...prev, onTimeStreak: Math.round(value) }));
  }, []);

  const handleInquiriesChange = useCallback((value: number) => {
    setInputs(prev => ({ ...prev, recentInquiries: value }));
  }, []);

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

  // Safety check - if Icon is undefined, use a fallback
  const IconComponent = Icon || (() => null);
  
  return (
    <>
      <TouchableOpacity
        style={styles.triggerButton}
        onPress={() => setVisible(true)}
        activeOpacity={0.7}
      >
        {Icon && <Icon name="sliders" size={20} color="#007AFF" />}
        <Text style={styles.triggerText}>Simulate Score</Text>
      </TouchableOpacity>

      <Modal
        visible={visible}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setVisible(false)}
      >
        <View style={styles.modalContainer}>
          {/* Header */}
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Score Simulator</Text>
            <TouchableOpacity onPress={() => setVisible(false)}>
              <Icon name="x" size={24} color="#8E8E93" />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalContent} contentContainerStyle={{ paddingBottom: 40 }}>
            {/* Current Score Reference */}
            <View style={styles.currentScoreBox}>
              <Text style={styles.currentScoreLabel}>Current Score</Text>
              <Text style={[styles.currentScoreValue, { color: getScoreColor(currentScore) }]}>
                {currentScore}
              </Text>
              <Text style={styles.currentScoreRange}>{getScoreRange(currentScore)}</Text>
            </View>

            {/* Slider 1: Utilization */}
            <View style={styles.sliderSection}>
              <View style={styles.sliderHeader}>
                <Text style={styles.sliderLabel}>Credit Utilization</Text>
                <Text style={[styles.sliderValue, inputs.utilizationPercent > 30 && styles.sliderValueHigh]}>
                  {Math.round(inputs.utilizationPercent)}%
                </Text>
              </View>
              {Slider ? (
                <Slider
                  style={styles.slider}
                  minimumValue={0}
                  maximumValue={100}
                  value={inputs.utilizationPercent}
                  onValueChange={handleUtilizationChange}
                  minimumTrackTintColor={inputs.utilizationPercent > 30 ? '#FF3B30' : '#34C759'}
                  maximumTrackTintColor="#E5E5EA"
                  thumbTintColor={inputs.utilizationPercent > 30 ? '#FF3B30' : '#34C759'}
                />
              ) : (
                <Text style={styles.sliderNote}>Slider component not available</Text>
              )}
              <Text style={styles.sliderNote}>
                {simulation.factors.utilization.note}
              </Text>
            </View>

            {/* Slider 2: Payment History */}
            <View style={styles.sliderSection}>
              <View style={styles.sliderHeader}>
                <Text style={styles.sliderLabel}>On-Time Payment Streak</Text>
                <Text style={styles.sliderValue}>
                  {Math.round(inputs.onTimeStreak)} months
                </Text>
              </View>
              {Slider ? (
                <Slider
                  style={styles.slider}
                  minimumValue={0}
                  maximumValue={60}
                  value={inputs.onTimeStreak}
                  onValueChange={handleStreakChange}
                  step={1}
                  minimumTrackTintColor="#34C759"
                  maximumTrackTintColor="#E5E5EA"
                  thumbTintColor="#34C759"
                />
              ) : (
                <Text style={styles.sliderNote}>Slider not available</Text>
              )}
              <Text style={styles.sliderNote}>
                {simulation.factors.paymentHistory.note}
              </Text>
            </View>

            {/* Slider 3: Inquiries */}
            <View style={styles.sliderSection}>
              <View style={styles.sliderHeader}>
                <Text style={styles.sliderLabel}>Recent Credit Inquiries</Text>
                <Text style={[styles.sliderValue, inputs.recentInquiries > 2 && styles.sliderValueHigh]}>
                  {inputs.recentInquiries} (last 12 months)
                </Text>
              </View>
              {Slider ? (
                <Slider
                  style={styles.slider}
                  minimumValue={0}
                  maximumValue={10}
                  value={inputs.recentInquiries}
                  onValueChange={handleInquiriesChange}
                  step={1}
                  minimumTrackTintColor={inputs.recentInquiries > 2 ? '#FF9500' : '#34C759'}
                  maximumTrackTintColor="#E5E5EA"
                  thumbTintColor={inputs.recentInquiries > 2 ? '#FF9500' : '#34C759'}
                />
              ) : (
                <Text style={styles.sliderNote}>Slider not available</Text>
              )}
              <Text style={styles.sliderNote}>
                {simulation.factors.inquiries.note}
              </Text>
            </View>

            {/* Projected Score Range */}
            <View style={styles.resultBox}>
              <Text style={styles.resultTitle}>Projected Score Range</Text>
              <View style={styles.scoreRangeRow}>
                <View style={styles.scoreBox}>
                  <Text style={styles.scoreLabel}>Min</Text>
                  <Text style={[styles.scoreValue, { color: getScoreColor(simulation.minScore) }]}>
                    {simulation.minScore}
                  </Text>
                </View>
                <View style={styles.scoreBox}>
                  <Text style={styles.scoreLabel}>Likely</Text>
                  <Text style={[styles.scoreValue, { color: getScoreColor(simulation.likelyScore) }]}>
                    {simulation.likelyScore}
                  </Text>
                </View>
                <View style={styles.scoreBox}>
                  <Text style={styles.scoreLabel}>Max</Text>
                  <Text style={[styles.scoreValue, { color: getScoreColor(simulation.maxScore) }]}>
                    {simulation.maxScore}
                  </Text>
                </View>
              </View>
              <View style={styles.impactBox}>
                <Icon name="clock" size={16} color="#8E8E93" />
                <Text style={styles.impactText}>
                  Expected impact: {simulation.timeToImpact}
                </Text>
              </View>
            </View>

            {/* Factor Breakdown */}
            <View style={styles.factorsBox}>
              <Text style={styles.factorsTitle}>Impact Breakdown</Text>
              {Object.entries(simulation.factors).map(([key, factor]) => (
                <View key={key} style={styles.factorRow}>
                  <Text style={styles.factorName}>
                    {key === 'utilization' ? 'Utilization' : 
                     key === 'paymentHistory' ? 'Payment History' : 'Inquiries'}
                  </Text>
                  <Text style={[styles.factorImpact, factor.impact >= 0 && styles.factorImpactPositive]}>
                    {factor.impact >= 0 ? '+' : ''}{factor.impact} points
                  </Text>
                </View>
              ))}
            </View>
          </ScrollView>
        </View>
      </Modal>
    </>
  );
}

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
  modalContent: {
    flex: 1,
    padding: 20,
    gap: 24,
  },
  currentScoreBox: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 20,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  currentScoreLabel: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 8,
  },
  currentScoreValue: {
    fontSize: 48,
    fontWeight: '700',
    marginBottom: 4,
  },
  currentScoreRange: {
    fontSize: 16,
    color: '#8E8E93',
    fontWeight: '600',
  },
  sliderSection: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  sliderHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sliderLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  sliderValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#34C759',
  },
  sliderValueHigh: {
    color: '#FF3B30',
  },
  slider: {
    width: '100%',
    height: 40,
  },
  sliderNote: {
    fontSize: 12,
    color: '#8E8E93',
    marginTop: 8,
    fontStyle: 'italic',
  },
  resultBox: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  resultTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 16,
    textAlign: 'center',
  },
  scoreRangeRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 16,
  },
  scoreBox: {
    alignItems: 'center',
  },
  scoreLabel: {
    fontSize: 12,
    color: '#8E8E93',
    marginBottom: 8,
  },
  scoreValue: {
    fontSize: 32,
    fontWeight: '700',
  },
  impactBox: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  impactText: {
    fontSize: 14,
    color: '#8E8E93',
    fontWeight: '600',
  },
  factorsBox: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  factorsTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 12,
  },
  factorRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#F2F2F7',
  },
  factorName: {
    fontSize: 14,
    color: '#1C1C1E',
  },
  factorImpact: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FF3B30',
  },
  factorImpactPositive: {
    color: '#34C759',
  },
});

export default ScoreSimulator;
export { ScoreSimulator };
