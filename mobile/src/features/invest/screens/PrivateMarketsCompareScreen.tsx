/**
 * Private Markets — Compare 2–4 deals across score, components, valuation, liquidity, fit, risk, diligence completeness.
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  ActivityIndicator,
} from 'react-native';
import Feather from '@expo/vector-icons/Feather';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { COLORS } from '../theme/privateMarketsTheme';
import { getPrivateMarketsService } from '../services/privateMarketsService';
import type { DealComparison } from '../types/privateMarketsTypes';

type CompareParams = { dealIds?: string[] };

const formatValue = (v: number | string | null): string => {
  if (v == null) return '—';
  if (typeof v === 'number') return String(v);
  return v;
};

export default function PrivateMarketsCompareScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<RouteProp<{ params: CompareParams }, 'params'>>();
  const paramIds = route.params?.dealIds ?? [];
  const dealIds = paramIds.length >= 2 ? paramIds.slice(0, 4) : ['1', '2', '3'];

  const [comparison, setComparison] = useState<DealComparison | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPrivateMarketsService()
      .getComparison(dealIds)
      .then(setComparison)
      .catch(() => setComparison(null))
      .finally(() => setLoading(false));
  }, [dealIds.join(',')]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.loadingText}>Building comparison…</Text>
      </View>
    );
  }

  if (!comparison || comparison.deals.length < 2) {
    return (
      <View style={styles.center}>
        <Feather name="layers" size={48} color="#94A3B8" />
        <Text style={styles.emptyTitle}>Select 2–4 deals to compare</Text>
        <Text style={styles.emptySub}>From a deal detail, tap Compare and add deals.</Text>
        <Pressable style={styles.backBtn} onPress={() => navigation.goBack()}>
          <Text style={styles.backBtnText}>Go back</Text>
        </Pressable>
      </View>
    );
  }

  const { deals, rows, generatedAt, summary } = comparison;
  const hasSummary = summary?.lines && summary.lines.length > 0;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
      <Pressable style={({ pressed }) => [styles.backRow, pressed && styles.backRowPressed]} onPress={() => navigation.goBack()}>
        <Feather name="chevron-left" size={24} color={COLORS.primary} />
        <Text style={styles.backLabel}>Back</Text>
      </Pressable>

      <Text style={styles.title}>Compare deals</Text>
      <Text style={styles.subtitle}>Same methodology • Green = stronger, Amber = concern</Text>

      {hasSummary && summary?.lines && (
        <View style={styles.summaryCard}>
          <Text style={styles.summaryCardTitle}>Summary</Text>
          {summary.lines.map((line, i) => (
            <Text key={i} style={styles.summaryCardLine}>{line}</Text>
          ))}
        </View>
      )}

      <View style={styles.table}>
        <View style={styles.tableHeader}>
          <View style={styles.dimCol} />
          {deals.map((d) => (
            <Pressable
              key={d.id}
              style={styles.dealHeaderCell}
              onPress={() => navigation.navigate('PrivateMarketsDealDetail', { dealId: d.id, deal: d })}
            >
              <Text style={styles.dealName} numberOfLines={2}>{d.name}</Text>
              <Text style={styles.dealScore}>{d.score}</Text>
              {'confidence' in d && d.confidence && (
                <View style={[styles.confidenceBadge, styles[`conf_${d.confidence}` as keyof typeof styles]]}>
                  <Text style={styles.confidenceText}>{d.confidence}</Text>
                </View>
              )}
            </Pressable>
          ))}
        </View>
        {rows.map((row, i) => (
          <View key={row.dimensionId} style={[styles.row, i % 2 === 1 && styles.rowAlt]}>
            <View style={styles.dimCol}>
              <Text style={styles.dimLabel}>{row.dimensionLabel}</Text>
            </View>
            {dealIds.map((id) => {
              const isBest = row.bestDealId === id;
              const isWorst = row.worstDealId === id && row.bestDealId !== id;
              return (
                <View key={id} style={[styles.cell, isBest && styles.cellBest, isWorst && styles.cellWorst]}>
                  <Text style={styles.cellValue}>{formatValue(row.values[id])}</Text>
                  {isBest && <Text style={styles.cellBestLabel}>Best</Text>}
                  {isWorst && <Text style={styles.cellWorstLabel}>Watch</Text>}
                </View>
              );
            })}
          </View>
        ))}
      </View>

      <View style={styles.legend}>
        <View style={styles.legendRow}>
          <View style={styles.legendDotBest} />
          <Text style={styles.legendText}>Strongest on this dimension</Text>
        </View>
        <View style={styles.legendRow}>
          <View style={styles.legendDotWorst} />
          <Text style={styles.legendText}>Highest concern / weakest</Text>
        </View>
      </View>

      <Text style={styles.generated}>Comparison generated {new Date(generatedAt).toLocaleDateString()}</Text>
      <View style={styles.bottomPad} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8FAFC' },
  content: { paddingHorizontal: 16, paddingTop: 12, paddingBottom: 40 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#F8FAFC', padding: 24 },
  loadingText: { marginTop: 12, fontSize: 15, color: COLORS.textSecondary },
  emptyTitle: { fontSize: 18, fontWeight: '700', color: COLORS.primary, marginTop: 16, textAlign: 'center' },
  emptySub: { fontSize: 14, color: COLORS.textSecondary, marginTop: 8, textAlign: 'center' },
  backBtn: { marginTop: 24, paddingVertical: 12, paddingHorizontal: 24, backgroundColor: COLORS.primary, borderRadius: 12 },
  backBtnText: { fontSize: 16, fontWeight: '600', color: '#FFF' },
  backRow: { flexDirection: 'row', alignItems: 'center', alignSelf: 'flex-start', gap: 4, marginBottom: 16 },
  backRowPressed: { opacity: 0.7 },
  backLabel: { fontSize: 16, fontWeight: '600', color: COLORS.primary },
  title: { fontSize: 24, fontWeight: '700', color: COLORS.primary, marginBottom: 4 },
  subtitle: { fontSize: 14, color: COLORS.textSecondary, marginBottom: 12 },
  summaryCard: { backgroundColor: '#FFF', borderRadius: 12, borderWidth: 1, borderColor: '#E2E8F0', padding: 14, marginBottom: 20 },
  summaryCardTitle: { fontSize: 14, fontWeight: '700', color: COLORS.primary, marginBottom: 8 },
  summaryCardLine: { fontSize: 13, color: COLORS.textSecondary, lineHeight: 20, marginBottom: 4 },
  table: { backgroundColor: '#FFF', borderRadius: 16, borderWidth: 1, borderColor: '#E2E8F0', overflow: 'hidden' },
  tableHeader: { flexDirection: 'row', borderBottomWidth: 2, borderBottomColor: COLORS.primary, paddingVertical: 12, paddingHorizontal: 8 },
  dimCol: { width: 120, justifyContent: 'center', paddingRight: 8 },
  dealHeaderCell: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 4 },
  dealName: { fontSize: 12, fontWeight: '600', color: COLORS.primary, textAlign: 'center' },
  dealScore: { fontSize: 18, fontWeight: '800', color: COLORS.accent, marginTop: 4 },
  confidenceBadge: { marginTop: 6, paddingHorizontal: 6, paddingVertical: 2, borderRadius: 6 },
  conf_high: { backgroundColor: '#D1FAE5' },
  conf_moderate: { backgroundColor: '#FEF3C7' },
  conf_limited: { backgroundColor: '#FEE2E2' },
  confidenceText: { fontSize: 10, fontWeight: '600', color: '#1E293B', textTransform: 'capitalize' },
  row: { flexDirection: 'row', paddingVertical: 12, paddingHorizontal: 8, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: '#E2E8F0' },
  rowAlt: { backgroundColor: '#F8FAFC' },
  dimLabel: { fontSize: 12, fontWeight: '600', color: '#64748B' },
  cell: { flex: 1, justifyContent: 'center', alignItems: 'center', paddingVertical: 4 },
  cellBest: { backgroundColor: 'rgba(16, 185, 129, 0.12)' },
  cellWorst: { backgroundColor: 'rgba(245, 158, 11, 0.15)' },
  cellValue: { fontSize: 13, color: COLORS.primary, fontWeight: '500' },
  cellBestLabel: { fontSize: 10, fontWeight: '700', color: '#059669', marginTop: 2 },
  cellWorstLabel: { fontSize: 10, fontWeight: '700', color: '#B45309', marginTop: 2 },
  legend: { flexDirection: 'row', flexWrap: 'wrap', gap: 16, marginTop: 16, paddingHorizontal: 8 },
  legendRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  legendDotBest: { width: 10, height: 10, borderRadius: 5, backgroundColor: '#10B981' },
  legendDotWorst: { width: 10, height: 10, borderRadius: 5, backgroundColor: '#F59E0B' },
  legendText: { fontSize: 12, color: '#64748B' },
  generated: { fontSize: 12, color: '#94A3B8', marginTop: 16, textAlign: 'center' },
  bottomPad: { height: 40 },
});
