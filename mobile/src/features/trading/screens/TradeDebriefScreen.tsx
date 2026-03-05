import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useQuery } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import { GET_TRADE_DEBRIEF } from '../../../graphql/tradeDebrief';

interface SectorStat {
  sector: string;
  trades: number;
  wins: number;
  losses: number;
  totalPnl: number;
}

interface PatternFlag {
  code: string;
  severity: string;
  description: string;
  impactDollars: number;
}

interface TradeDebrief {
  headline: string | null;
  narrative: string | null;
  topInsight: string | null;
  recommendations: string[] | null;
  statsSummary: string | null;
  patternCodes: string[] | null;
  sectorStats: SectorStat[] | null;
  patternFlags: PatternFlag[] | null;
  dataSource: string | null;
  hasEnoughData: boolean | null;
  totalTrades: number | null;
  winRatePct: number | null;
  totalPnl: number | null;
  bestSector: string | null;
  worstSector: string | null;
  counterfactualExtraPnl: number | null;
  lookbackDays: number | null;
  generatedAt: string | null;
}

const LOOKBACK_OPTIONS = [30, 60, 90, 180];

const severityColor: Record<string, string> = {
  HIGH: '#EF4444',
  MEDIUM: '#F59E0B',
  LOW: '#6366F1',
};

interface TradeDebriefScreenProps {
  onBack?: () => void;
}

const TradeDebriefScreen: React.FC<TradeDebriefScreenProps> = ({ onBack }) => {
  const insets = useSafeAreaInsets();
  const [lookbackDays, setLookbackDays] = useState(90);

  const { data, loading, error, refetch } = useQuery(GET_TRADE_DEBRIEF, {
    variables: { lookbackDays },
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });

  const debrief: TradeDebrief | null = data?.tradeDebrief ?? null;

  const statsSummary = React.useMemo(() => {
    if (!debrief?.statsSummary) return null;
    try {
      return typeof debrief.statsSummary === 'string'
        ? JSON.parse(debrief.statsSummary)
        : debrief.statsSummary;
    } catch {
      return null;
    }
  }, [debrief?.statsSummary]);

  const pnlColor = (val: number | null) => {
    if (val == null) return '#8E8E93';
    return val >= 0 ? '#10B981' : '#EF4444';
  };

  const formatPnl = (val: number | null) => {
    if (val == null) return '—';
    const sign = val >= 0 ? '+' : '';
    return `${sign}$${Math.abs(val).toFixed(2)}`;
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        {onBack && (
          <TouchableOpacity onPress={onBack} style={styles.backButton}>
            <Icon name="arrow-left" size={22} color="#1C1C1E" />
          </TouchableOpacity>
        )}
        <Icon name="bar-chart" size={20} color="#6366F1" />
        <Text style={styles.headerTitle}>AI Trade Debrief</Text>
      </View>

      {/* Lookback selector */}
      <View style={styles.lookbackRow}>
        {LOOKBACK_OPTIONS.map((days) => (
          <TouchableOpacity
            key={days}
            style={[
              styles.lookbackPill,
              lookbackDays === days && styles.lookbackPillActive,
            ]}
            onPress={() => setLookbackDays(days)}
          >
            <Text
              style={[
                styles.lookbackPillText,
                lookbackDays === days && styles.lookbackPillTextActive,
              ]}
            >
              {days}d
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading && !debrief ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color="#6366F1" />
          <Text style={styles.loadingText}>Analysing your trades...</Text>
        </View>
      ) : error && !debrief ? (
        <View style={styles.centered}>
          <Icon name="alert-circle" size={40} color="#EF4444" />
          <Text style={styles.errorText}>Could not load debrief.</Text>
          <TouchableOpacity onPress={() => refetch()} style={styles.retryButton}>
            <Text style={styles.retryText}>Retry</Text>
          </TouchableOpacity>
        </View>
      ) : debrief && !debrief.hasEnoughData ? (
        <View style={styles.centered}>
          <Icon name="inbox" size={48} color="#8E8E93" />
          <Text style={styles.emptyTitle}>Not enough trades yet</Text>
          <Text style={styles.emptySubtitle}>
            Complete at least 5 trades in the last {lookbackDays} days to unlock your AI debrief.
          </Text>
        </View>
      ) : debrief ? (
        <ScrollView
          style={styles.scroll}
          contentContainerStyle={{ paddingBottom: insets.bottom + 32 }}
          refreshControl={
            <RefreshControl refreshing={loading} onRefresh={() => refetch()} />
          }
          showsVerticalScrollIndicator={false}
        >
          {/* Headline */}
          {!!debrief.headline && (
            <View style={styles.headlineCard}>
              <Icon name="zap" size={18} color="#6366F1" />
              <Text style={styles.headlineText}>{debrief.headline}</Text>
            </View>
          )}

          {/* Stats row */}
          <View style={styles.statsGrid}>
            <View style={styles.statCard}>
              <Text style={styles.statLabel}>Trades</Text>
              <Text style={styles.statValue}>{debrief.totalTrades ?? '—'}</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statLabel}>Win Rate</Text>
              <Text style={styles.statValue}>
                {debrief.winRatePct != null ? `${debrief.winRatePct.toFixed(1)}%` : '—'}
              </Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statLabel}>Total P&L</Text>
              <Text style={[styles.statValue, { color: pnlColor(debrief.totalPnl) }]}>
                {formatPnl(debrief.totalPnl)}
              </Text>
            </View>
            {debrief.counterfactualExtraPnl != null && debrief.counterfactualExtraPnl !== 0 && (
              <View style={styles.statCard}>
                <Text style={styles.statLabel}>Left on table</Text>
                <Text style={[styles.statValue, { color: '#F59E0B' }]}>
                  {formatPnl(debrief.counterfactualExtraPnl)}
                </Text>
              </View>
            )}
          </View>

          {/* Narrative */}
          {!!debrief.narrative && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Coach Analysis</Text>
              <View style={styles.narrativeCard}>
                <Text style={styles.narrativeText}>{debrief.narrative}</Text>
              </View>
            </View>
          )}

          {/* Top Insight */}
          {!!debrief.topInsight && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Top Insight</Text>
              <View style={[styles.narrativeCard, { borderLeftColor: '#6366F1', borderLeftWidth: 3 }]}>
                <Text style={styles.narrativeText}>{debrief.topInsight}</Text>
              </View>
            </View>
          )}

          {/* Recommendations */}
          {debrief.recommendations && debrief.recommendations.length > 0 && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Recommendations</Text>
              {debrief.recommendations.map((rec, i) => (
                <View key={i} style={styles.recRow}>
                  <View style={styles.recBullet} />
                  <Text style={styles.recText}>{rec}</Text>
                </View>
              ))}
            </View>
          )}

          {/* Pattern Flags */}
          {debrief.patternFlags && debrief.patternFlags.length > 0 && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Detected Patterns</Text>
              {debrief.patternFlags.map((flag, i) => {
                const sc = severityColor[flag.severity] ?? '#8E8E93';
                return (
                  <View key={i} style={styles.patternCard}>
                    <View style={styles.patternHeader}>
                      <View style={[styles.severityPill, { backgroundColor: sc + '22' }]}>
                        <Text style={[styles.severityText, { color: sc }]}>{flag.severity}</Text>
                      </View>
                      <Text style={styles.patternCode}>{flag.code}</Text>
                      {flag.impactDollars !== 0 && (
                        <Text style={[styles.patternImpact, { color: pnlColor(-Math.abs(flag.impactDollars)) }]}>
                          {formatPnl(-Math.abs(flag.impactDollars))} impact
                        </Text>
                      )}
                    </View>
                    <Text style={styles.patternDesc}>{flag.description}</Text>
                  </View>
                );
              })}
            </View>
          )}

          {/* Sector breakdown */}
          {debrief.sectorStats && debrief.sectorStats.length > 0 && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>By Sector</Text>
              {debrief.sectorStats.map((s, i) => (
                <View key={i} style={styles.sectorRow}>
                  <Text style={styles.sectorName}>{s.sector}</Text>
                  <View style={styles.sectorMetrics}>
                    <Text style={styles.sectorMeta}>{s.trades} trades</Text>
                    <Text style={styles.sectorMeta}>{s.trades > 0 ? ((s.wins / s.trades) * 100).toFixed(0) : 0}% WR</Text>
                    <Text style={[styles.sectorMeta, { color: pnlColor(s.totalPnl) }]}>
                      {formatPnl(s.totalPnl)}
                    </Text>
                  </View>
                </View>
              ))}
            </View>
          )}

          {/* Best / Worst sectors */}
          {(debrief.bestSector || debrief.worstSector) && (
            <View style={styles.sectorHighlightRow}>
              {debrief.bestSector && (
                <View style={[styles.sectorHighlight, { backgroundColor: '#D1FAE5' }]}>
                  <Icon name="trending-up" size={14} color="#10B981" />
                  <Text style={[styles.sectorHighlightText, { color: '#065F46' }]}>
                    Best: {debrief.bestSector}
                  </Text>
                </View>
              )}
              {debrief.worstSector && (
                <View style={[styles.sectorHighlight, { backgroundColor: '#FEE2E2' }]}>
                  <Icon name="trending-down" size={14} color="#EF4444" />
                  <Text style={[styles.sectorHighlightText, { color: '#991B1B' }]}>
                    Worst: {debrief.worstSector}
                  </Text>
                </View>
              )}
            </View>
          )}

          {/* Data source footer */}
          {debrief.dataSource && (
            <Text style={styles.footerText}>
              Source: {debrief.dataSource}
              {debrief.generatedAt ? ` · ${new Date(debrief.generatedAt).toLocaleDateString()}` : ''}
            </Text>
          )}
        </ScrollView>
      ) : null}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 20,
    paddingVertical: 14,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  backButton: {
    marginRight: 4,
    padding: 2,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1C1C1E',
    flex: 1,
  },
  lookbackRow: {
    flexDirection: 'row',
    gap: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  lookbackPill: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#F3F4F6',
  },
  lookbackPillActive: {
    backgroundColor: '#6366F1',
  },
  lookbackPillText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#6B7280',
  },
  lookbackPillTextActive: {
    color: '#FFFFFF',
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
    gap: 12,
  },
  loadingText: {
    fontSize: 15,
    color: '#8E8E93',
    marginTop: 8,
  },
  errorText: {
    fontSize: 15,
    color: '#EF4444',
    textAlign: 'center',
  },
  retryButton: {
    marginTop: 8,
    paddingHorizontal: 20,
    paddingVertical: 10,
    backgroundColor: '#6366F1',
    borderRadius: 10,
  },
  retryText: {
    color: '#FFFFFF',
    fontWeight: '600',
    fontSize: 14,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
    textAlign: 'center',
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
    lineHeight: 20,
  },
  scroll: {
    flex: 1,
  },
  headlineCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    margin: 16,
    padding: 16,
    backgroundColor: '#EEF2FF',
    borderRadius: 12,
  },
  headlineText: {
    flex: 1,
    fontSize: 15,
    fontWeight: '600',
    color: '#3730A3',
    lineHeight: 22,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 12,
    gap: 8,
    marginBottom: 8,
  },
  statCard: {
    flex: 1,
    minWidth: '22%',
    backgroundColor: '#FFFFFF',
    borderRadius: 10,
    padding: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 3,
    elevation: 2,
  },
  statLabel: {
    fontSize: 11,
    color: '#8E8E93',
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.3,
    marginBottom: 4,
  },
  statValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  section: {
    paddingHorizontal: 16,
    marginTop: 20,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#8E8E93',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 10,
  },
  narrativeCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 14,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 3,
    elevation: 2,
  },
  narrativeText: {
    fontSize: 14,
    color: '#374151',
    lineHeight: 21,
  },
  recRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    marginBottom: 8,
  },
  recBullet: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#6366F1',
    marginTop: 7,
  },
  recText: {
    flex: 1,
    fontSize: 14,
    color: '#374151',
    lineHeight: 21,
  },
  patternCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 3,
    elevation: 2,
  },
  patternHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 6,
  },
  severityPill: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
  },
  severityText: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.3,
  },
  patternCode: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6B7280',
    flex: 1,
  },
  patternImpact: {
    fontSize: 12,
    fontWeight: '600',
  },
  patternDesc: {
    fontSize: 13,
    color: '#4B5563',
    lineHeight: 19,
  },
  sectorRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#E5E7EB',
  },
  sectorName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
    flex: 1,
  },
  sectorMetrics: {
    flexDirection: 'row',
    gap: 12,
  },
  sectorMeta: {
    fontSize: 13,
    color: '#6B7280',
    fontWeight: '500',
  },
  sectorHighlightRow: {
    flexDirection: 'row',
    gap: 10,
    paddingHorizontal: 16,
    marginTop: 20,
  },
  sectorHighlight: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    padding: 10,
    borderRadius: 10,
  },
  sectorHighlightText: {
    fontSize: 13,
    fontWeight: '600',
  },
  footerText: {
    textAlign: 'center',
    fontSize: 12,
    color: '#9CA3AF',
    marginTop: 24,
    marginBottom: 8,
  },
});

export default TradeDebriefScreen;
