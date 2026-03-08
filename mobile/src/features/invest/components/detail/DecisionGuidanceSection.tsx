/**
 * Decision guidance card: confidence alert, recommended allocation, concentration warning, tradeoff summary.
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Feather from '@expo/vector-icons/Feather';
import { COLORS, SPACING, RADIUS } from '../../theme/privateMarketsTheme';
import type { DecisionSupport, DealConfidence } from '../../types/privateMarketsTypes';

export interface DecisionGuidanceSectionProps {
  decisionSupport: DecisionSupport | null | undefined;
  confidence: DealConfidence | undefined;
}

export function DecisionGuidanceSection({ decisionSupport, confidence }: DecisionGuidanceSectionProps) {
  if (!decisionSupport) return null;
  return (
    <View style={styles.card}>
      {confidence && confidence !== 'high' && (
        <View style={styles.impactRow}>
          <Feather name="info" size={16} color="#B45309" />
          <Text style={styles.impactText}>
            Diligence is {confidence === 'moderate' ? 'partial' : 'limited'}; recommendation confidence is {confidence}.
          </Text>
        </View>
      )}
      {decisionSupport.suggestedPositionSize && (
        <View style={styles.highlight}>
          <Text style={styles.highlightLabel}>Recommended allocation</Text>
          <Text style={styles.highlightValue}>{decisionSupport.suggestedPositionSize}</Text>
        </View>
      )}
      {decisionSupport.concentrationWarning && (
        <View style={styles.concentrationCard}>
          <View style={styles.concentrationHeader}>
            <Feather name="alert-circle" size={16} color="#F59E0B" />
            <Text style={styles.concentrationLabel}>Concentration</Text>
          </View>
          <Text style={styles.concentrationText}>{decisionSupport.concentrationWarning}</Text>
        </View>
      )}
      {decisionSupport.tradeoffSummary && (
        <Text style={styles.tradeoff}>{decisionSupport.tradeoffSummary}</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: { backgroundColor: '#F0F9FF', borderColor: '#BAE6FD', borderRadius: RADIUS.md, padding: SPACING.xl, borderWidth: 1 },
  impactRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12, padding: 10, backgroundColor: 'rgba(245, 158, 11, 0.12)', borderRadius: 10 },
  impactText: { flex: 1, fontSize: 13, color: '#92400E', lineHeight: 18 },
  highlight: { alignItems: 'center', padding: 16, backgroundColor: 'rgba(59,130,246,0.08)', borderRadius: RADIUS.md, marginBottom: 12 },
  highlightLabel: { fontSize: 15, fontWeight: '600', color: '#1E293B' },
  highlightValue: { fontSize: 28, fontWeight: '800', color: COLORS.accent, marginTop: 4 },
  concentrationCard: { padding: 12, borderRadius: RADIUS.md, backgroundColor: 'rgba(245, 158, 11, 0.12)', marginBottom: 12 },
  concentrationHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 6 },
  concentrationLabel: { fontSize: 14, fontWeight: '600', color: '#0C4A6E' },
  concentrationText: { fontSize: 14, color: '#0369A1', lineHeight: 20 },
  tradeoff: { fontSize: 13, color: '#64748B', lineHeight: 20, marginTop: 6 },
});
