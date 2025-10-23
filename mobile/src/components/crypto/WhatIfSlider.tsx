// What-if stress test slider for SBLOC risk analysis
import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Slider from '@react-native-community/slider';
import { fmtUsd, fmtPercent } from '../../shared/utils/format';

interface WhatIfSliderProps {
  collateralUsd: number;
  loanUsd: number;
  onStressChange: (stress: StressTestResult) => void;
  style?: any;
}

interface StressTestResult {
  shock: number;
  ltvPct: number;
  tier: string;
  collateralValue: number;
  loanAmount: number;
}

const WhatIfSlider: React.FC<WhatIfSliderProps> = ({
  collateralUsd,
  loanUsd,
  onStressChange,
  style,
}) => {
  const [shock, setShock] = useState(0);
  const [stress, setStress] = useState<StressTestResult>({
    shock: 0,
    ltvPct: 0,
    tier: 'SAFE',
    collateralValue: collateralUsd,
    loanAmount: loanUsd,
  });

  useEffect(() => {
    const stressedCollateral = collateralUsd * (1 + shock);
    const ltvPct = loanUsd > 0 ? (loanUsd / stressedCollateral) * 100 : 0;
    
    let tier = 'SAFE';
    if (ltvPct >= 50) tier = 'LIQUIDATE';
    else if (ltvPct >= 45) tier = 'AT_RISK';
    else if (ltvPct >= 40) tier = 'TOP_UP';
    else if (ltvPct >= 35) tier = 'WARN';

    const newStress: StressTestResult = {
      shock,
      ltvPct,
      tier,
      collateralValue: stressedCollateral,
      loanAmount: loanUsd,
    };

    setStress(newStress);
    onStressChange(newStress);
  }, [shock, collateralUsd, loanUsd, onStressChange]);

  const getTierColor = (tier: string): string => {
    const colors: Record<string, string> = {
      'SAFE': '#10B981',
      'WARN': '#F59E0B',
      'TOP_UP': '#EF4444',
      'AT_RISK': '#DC2626',
      'LIQUIDATE': '#7C2D12',
    };
    return colors[tier] || '#6B7280';
  };

  const getTierMessage = (tier: string, ltvPct: number): string => {
    const messages: Record<string, string> = {
      'SAFE': `Portfolio is healthy at ${(ltvPct || 0).toFixed(1)}% LTV`,
      'WARN': `Monitor closely - LTV at ${(ltvPct || 0).toFixed(1)}%`,
      'TOP_UP': `Consider adding collateral - LTV at ${(ltvPct || 0).toFixed(1)}%`,
      'AT_RISK': `Immediate action needed - LTV at ${(ltvPct || 0).toFixed(1)}%`,
      'LIQUIDATE': `Liquidation risk - LTV at ${(ltvPct || 0).toFixed(1)}%`,
    };
    return messages[tier] || 'Unknown risk level';
  };

  return (
    <View style={[styles.container, style]}>
      <Text style={styles.title}>Stress Test Scenario</Text>
      
      <View style={styles.sliderContainer}>
        <Text style={styles.label}>Market Shock: {fmtPercent(shock * 100)}</Text>
        <Slider
          style={styles.slider}
          minimumValue={-0.5}
          maximumValue={0.2}
          step={0.01}
          value={shock}
          onValueChange={setShock}
          minimumTrackTintColor={getTierColor(stress.tier)}
          maximumTrackTintColor="#E5E7EB"
          thumbStyle={styles.thumb}
        />
        <View style={styles.rangeLabels}>
          <Text style={styles.rangeLabel}>-50%</Text>
          <Text style={styles.rangeLabel}>0%</Text>
          <Text style={styles.rangeLabel}>+20%</Text>
        </View>
      </View>

      <View style={[styles.resultCard, { borderLeftColor: getTierColor(stress.tier) }]}>
        <View style={styles.resultHeader}>
          <Text style={styles.resultTitle}>Stress Test Results</Text>
          <View style={[styles.tierBadge, { backgroundColor: getTierColor(stress.tier) }]}>
            <Text style={styles.tierText}>{stress.tier}</Text>
          </View>
        </View>
        
        <View style={styles.metrics}>
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>Collateral Value</Text>
            <Text style={styles.metricValue}>{fmtUsd(stress.collateralValue)}</Text>
          </View>
          
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>Loan Amount</Text>
            <Text style={styles.metricValue}>{fmtUsd(stress.loanAmount)}</Text>
          </View>
          
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>LTV Ratio</Text>
            <Text style={[styles.metricValue, { color: getTierColor(stress.tier) }]}>
              {(stress.ltvPct || 0).toFixed(1)}%
            </Text>
          </View>
        </View>
        
        <Text style={[styles.message, { color: getTierColor(stress.tier) }]}>
          {getTierMessage(stress.tier, stress.ltvPct)}
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 16,
  },
  sliderContainer: {
    marginBottom: 20,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 8,
  },
  slider: {
    width: '100%',
    height: 40,
  },
  thumb: {
    backgroundColor: '#007AFF',
    width: 20,
    height: 20,
  },
  rangeLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  rangeLabel: {
    fontSize: 12,
    color: '#6B7280',
  },
  resultCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
    padding: 16,
    borderLeftWidth: 4,
  },
  resultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  resultTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  tierBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  tierText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  metrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  metric: {
    flex: 1,
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
  },
  message: {
    fontSize: 14,
    fontWeight: '500',
    textAlign: 'center',
  },
});

export default WhatIfSlider;
