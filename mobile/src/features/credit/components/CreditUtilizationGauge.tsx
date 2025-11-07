/**
 * Credit Utilization Gauge Component
 * Visual gauge showing credit utilization percentage
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { CreditUtilization } from '../types/CreditTypes';

interface CreditUtilizationGaugeProps {
  utilization: CreditUtilization;
}

export const CreditUtilizationGauge: React.FC<CreditUtilizationGaugeProps> = ({
  utilization,
}) => {
  const percentage = Math.round(utilization.currentUtilization * 100);
  const optimalPercentage = Math.round(utilization.optimalUtilization * 100);
  
  // Get color based on utilization
  const getColor = (util: number): string => {
    if (util <= 0.3) return '#34C759'; // Green
    if (util <= 0.5) return '#FF9500'; // Orange
    return '#FF3B30'; // Red
  };

  const color = getColor(utilization.currentUtilization);
  const barWidth = Math.min(percentage, 100);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Credit Utilization</Text>
        <Text style={[styles.percentage, { color }]}>
          {percentage}%
        </Text>
      </View>
      
      <View style={styles.gaugeContainer}>
        <View style={styles.gaugeBackground}>
          <View 
            style={[
              styles.gaugeFill, 
              { 
                width: `${barWidth}%`,
                backgroundColor: color,
              }
            ]} 
          />
          <View 
            style={[
              styles.optimalMarker,
              { left: `${optimalPercentage}%` }
            ]} 
          />
        </View>
        <View style={styles.labels}>
          <Text style={styles.label}>0%</Text>
          <Text style={[styles.label, styles.optimalLabel]}>
            Optimal: {optimalPercentage}%
          </Text>
          <Text style={styles.label}>100%</Text>
        </View>
      </View>

      {utilization.paydownSuggestion > 0 && (
        <View style={styles.suggestion}>
          <Text style={styles.suggestionText}>
            Pay down ${utilization.paydownSuggestion.toFixed(0)} → 
            +{utilization.projectedScoreGain} points
          </Text>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  percentage: {
    fontSize: 20,
    fontWeight: '700',
  },
  gaugeContainer: {
    marginBottom: 8,
  },
  gaugeBackground: {
    height: 8,
    backgroundColor: '#F2F2F7',
    borderRadius: 4,
    position: 'relative',
    overflow: 'visible',
  },
  gaugeFill: {
    height: '100%',
    borderRadius: 4,
  },
  optimalMarker: {
    position: 'absolute',
    top: -4,
    width: 2,
    height: 16,
    backgroundColor: '#34C759',
    borderRadius: 1,
  },
  labels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  label: {
    fontSize: 12,
    color: '#8E8E93',
  },
  optimalLabel: {
    color: '#34C759',
    fontWeight: '600',
  },
  suggestion: {
    marginTop: 12,
    padding: 12,
    backgroundColor: '#F0F8FF',
    borderRadius: 8,
  },
  suggestionText: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '600',
    textAlign: 'center',
  },
});

