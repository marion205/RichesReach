/**
 * Score hero: circular score, confidence strip, benchmark, "What feeds this score", diligence checklist, score components.
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Feather from '@expo/vector-icons/Feather';
import { COLORS, SPACING, RADIUS } from '../../theme/privateMarketsTheme';
import CircularScore from '../CircularScore';
import { DiligenceChecklistSection } from './DiligenceChecklistSection';
import type { DealDetail, DiligenceItemStatus, ScoreInputCategory } from '../../types/privateMarketsTypes';

const getProgressColor = (score: number) => {
  if (score >= 80) return '#10B981';
  if (score >= 60) return '#3B82F6';
  return '#F59E0B';
};

export interface ScoreHeroSectionProps {
  detail: DealDetail;
  diligenceStatus: Record<string, DiligenceItemStatus>;
  onDiligenceStatusChange: (line: string, status: DiligenceItemStatus) => void;
  onRequestFromGP: (line: string) => void;
}

export function ScoreHeroSection({
  detail,
  diligenceStatus,
  onDiligenceStatusChange,
  onRequestFromGP,
}: ScoreHeroSectionProps) {
  const scoreBreakdown = detail.scoreBreakdown;
  if (!scoreBreakdown) return null;

  const confidenceLevel = detail.confidenceDetail?.level ?? detail.confidence;
  const confidencePercent = detail.confidenceDetail?.percent;

  return (
    <View style={styles.section}>
      <View style={styles.hero}>
        <CircularScore
          score={scoreBreakdown.overall}
          size={180}
          strokeWidth={16}
          progressColor={getProgressColor(scoreBreakdown.overall)}
          trackColor="#E2E8F0"
          textColor={COLORS.primary}
        />
      </View>
      {(detail.confidence || detail.confidenceDetail) && (
        <View style={[styles.confidenceStrip, styles[`confidence_${confidenceLevel}` as keyof typeof styles]]}>
          <Feather
            name={confidenceLevel === 'high' ? 'shield' : confidenceLevel === 'moderate' ? 'info' : 'alert-circle'}
            size={18}
            color={confidenceLevel === 'high' ? '#059669' : confidenceLevel === 'moderate' ? '#B45309' : '#DC2626'}
          />
          <View style={styles.confidenceTextBlock}>
            <Text style={styles.confidenceLabel}>
              {confidenceLevel === 'high'
                ? 'High confidence'
                : confidenceLevel === 'moderate'
                  ? `Moderate confidence${confidencePercent != null ? ` (${confidencePercent}%)` : ''}`
                  : `Limited data${confidencePercent != null ? ` (${confidencePercent}%)` : ''}`}
            </Text>
            {detail.confidenceDetail?.factors && detail.confidenceDetail.factors.length > 0 ? (
              <>
                <Text style={styles.confidenceFactorsLabel}>Affected by:</Text>
                <Text style={styles.confidenceSub}>{detail.confidenceDetail.factors.join(', ')}</Text>
              </>
            ) : (
              <Text style={styles.confidenceSub}>
                {confidenceLevel === 'high'
                  ? 'Score and fit based on full diligence.'
                  : confidenceLevel === 'moderate'
                    ? 'Based on partial diligence; consider additional verification.'
                    : 'Diligence limited; score and recommendation have lower confidence.'}
              </Text>
            )}
          </View>
        </View>
      )}
      {scoreBreakdown.benchmark && (
        <View style={styles.benchmarkBadge}>
          <Feather name="bar-chart-2" size={16} color="#64748B" />
          <Text style={styles.benchmarkText}>
            {scoreBreakdown.benchmark.trend === 'above_peer' ? 'Above' : 'Below or in line with'} peers
            {scoreBreakdown.benchmark.percentileAmongPeers != null &&
              ` • Top ${100 - scoreBreakdown.benchmark.percentileAmongPeers}%`}
          </Text>
        </View>
      )}
      {detail.scoreInputs && detail.scoreInputs.length > 0 && (
        <View style={styles.scoreInputsCard}>
          <Text style={styles.subsectionTitle}>What feeds this score</Text>
          {detail.scoreInputs.map((cat: ScoreInputCategory) => (
            <View key={cat.id} style={styles.scoreInputCategory}>
              <Text style={styles.scoreInputCatLabel}>{cat.label}</Text>
              {cat.items.map((item, i) => (
                <View key={i} style={styles.scoreInputItem}>
                  <Text style={styles.scoreInputItemLabel}>{item.label}</Text>
                  <Text style={styles.scoreInputItemValue}>{item.value}</Text>
                  {item.source && <Text style={styles.scoreInputSource}>{item.source}</Text>}
                </View>
              ))}
            </View>
          ))}
        </View>
      )}
      {detail.whatWouldChangeScore && detail.whatWouldChangeScore.length > 0 && (
        <DiligenceChecklistSection
          lines={detail.whatWouldChangeScore}
          statusByLine={diligenceStatus}
          onStatusChange={onDiligenceStatusChange}
          onRequestFromGP={onRequestFromGP}
        />
      )}
      <View style={styles.componentsCard}>
        <Text style={styles.subsectionTitle}>Score components</Text>
        <View style={styles.componentsList}>
          {scoreBreakdown.components.map((c, i) => (
            <View key={i} style={styles.componentRow}>
              <View style={styles.componentMain}>
                <Text style={styles.componentLabel}>{c.label}</Text>
                <Text style={styles.componentWeight}>Weight: {c.weight}</Text>
              </View>
              <View style={styles.componentRight}>
                <Text style={[styles.componentScore, { color: getProgressColor(c.score) }]}>{c.score}</Text>
              </View>
              <Text style={styles.componentReason}>{c.shortReason}</Text>
            </View>
          ))}
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  section: {},
  hero: { alignItems: 'center', marginVertical: 20 },
  confidenceStrip: { flexDirection: 'row', alignItems: 'flex-start', padding: 14, borderRadius: RADIUS.md, marginBottom: 16, borderWidth: 1 },
  confidence_high: { backgroundColor: '#ECFDF5', borderColor: '#A7F3D0' },
  confidence_moderate: { backgroundColor: '#FFFBEB', borderColor: '#FDE68A' },
  confidence_limited: { backgroundColor: '#FEF2F2', borderColor: '#FECACA' },
  confidenceTextBlock: { flex: 1, marginLeft: 12 },
  confidenceLabel: { fontSize: 15, fontWeight: '700', color: COLORS.primary },
  confidenceSub: { fontSize: 13, color: COLORS.textSecondary, marginTop: 4, lineHeight: 18 },
  confidenceFactorsLabel: { fontSize: 12, fontWeight: '600', color: COLORS.textSecondary, marginTop: 4 },
  benchmarkBadge: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8,
    backgroundColor: '#F1F5F9', paddingVertical: 8, paddingHorizontal: 16, borderRadius: 20, alignSelf: 'center', marginBottom: 20,
  },
  benchmarkText: { fontSize: 14, color: '#475569', fontWeight: '500' },
  subsectionTitle: { fontSize: 15, fontWeight: '700', color: COLORS.primary, marginBottom: 12 },
  scoreInputsCard: {
    backgroundColor: COLORS.bgCard, borderRadius: RADIUS.lg, padding: SPACING.xl, borderWidth: 1, borderColor: COLORS.border,
    marginBottom: 16,
  },
  scoreInputCategory: { marginBottom: 14 },
  scoreInputCatLabel: { fontSize: 14, fontWeight: '700', color: COLORS.primary, marginBottom: 6 },
  scoreInputItem: { marginBottom: 4 },
  scoreInputItemLabel: { fontSize: 13, color: '#64748B' },
  scoreInputItemValue: { fontSize: 14, fontWeight: '600', color: COLORS.primary },
  scoreInputSource: { fontSize: 11, color: '#94A3B8', marginTop: 1 },
  componentsCard: {
    backgroundColor: COLORS.bgCard, borderRadius: RADIUS.lg, padding: SPACING.xl, borderWidth: 1, borderColor: COLORS.border,
  },
  componentsList: { gap: 0 },
  componentRow: {
    flexDirection: 'row', flexWrap: 'wrap', alignItems: 'flex-start', paddingVertical: 12,
    borderBottomWidth: 1, borderBottomColor: '#F1F5F9',
  },
  componentMain: { marginBottom: 4, flex: 1, minWidth: 100 },
  componentRight: { alignSelf: 'flex-start', marginBottom: 4 },
  componentScore: { fontSize: 20, fontWeight: '800' },
  componentWeight: { fontSize: 12, color: '#94A3B8', marginTop: 2 },
  componentLabel: { fontSize: 14, fontWeight: '600', color: COLORS.primary },
  componentReason: { width: '100%', fontSize: 13, color: COLORS.textSecondary, lineHeight: 20, marginTop: 4 },
});
