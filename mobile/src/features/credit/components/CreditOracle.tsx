/**
 * Predictive Credit Oracle - Crowdsourced Insights with Bias Detection
 * Redesigned 2025 — clean card layout, proper breathing room
 */

import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { CreditOracle as CreditOracleType, OracleInsight } from '../types/CreditTypes';
import { LinearGradient } from 'expo-linear-gradient';

interface CreditOracleProps {
  oracle: CreditOracleType;
  onInsightPress?: (insight: OracleInsight) => void;
}

export const CreditOracle: React.FC<CreditOracleProps> = ({
  oracle,
  onInsightPress,
}) => {
  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'trend': return 'trending-up';
      case 'warning': return 'alert-triangle';
      case 'opportunity': return 'zap';
      case 'local': return 'map-pin';
      default: return 'info';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'trend': return '#5AC8FA';
      case 'warning': return '#FF6B6B';
      case 'opportunity': return '#34C759';
      case 'local': return '#AF52DE';
      default: return '#007AFF';
    }
  };

  const getSectionColor = (section: string) => {
    if (section.includes('Warnings')) return '#FF6B6B';
    if (section.includes('Opportunities')) return '#34C759';
    if (section.includes('Local')) return '#AF52DE';
    return '#007AFF';
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return '#34C759';
    if (confidence >= 0.6) return '#FF9500';
    return '#FF3B30';
  };

  const renderInsight = (insight: OracleInsight, sectionColor: string) => {
    const accentColor = getTypeColor(insight.type);
    const confColor = getConfidenceColor(insight.confidence);

    return (
      <TouchableOpacity
        key={insight.id}
        style={[styles.insightCard, { borderLeftColor: accentColor }]}
        onPress={() => onInsightPress?.(insight)}
        activeOpacity={0.75}
      >
        {/* ── Top row: icon + title + optional location badge ── */}
        <View style={styles.cardTop}>
          <View style={[styles.iconCircle, { backgroundColor: accentColor + '18' }]}>
            <Icon name={getTypeIcon(insight.type)} size={20} color={accentColor} />
          </View>
          <View style={styles.cardTopText}>
            <Text style={styles.insightTitle} numberOfLines={2}>{insight.title}</Text>
            {insight.location && (
              <View style={[styles.locationBadge, { backgroundColor: sectionColor + '15' }]}>
                <Icon name="map-pin" size={11} color={sectionColor} />
                <Text style={[styles.locationText, { color: sectionColor }]}>{insight.location}</Text>
              </View>
            )}
          </View>
        </View>

        {/* ── Description ── */}
        <Text style={styles.description}>{insight.description}</Text>

        {/* ── Tip / recommendation ── */}
        <View style={styles.tipRow}>
          <Icon name="star" size={14} color="#E6B800" style={{ marginTop: 1 }} />
          <Text style={styles.tipText}>{insight.recommendation}</Text>
        </View>

        {/* ── Footer: confidence bar + time horizon ── */}
        <View style={styles.footer}>
          <View style={styles.confidenceWrap}>
            <Text style={styles.confidenceLabel}>Confidence</Text>
            <View style={styles.barRow}>
              <View style={styles.barTrack}>
                <View
                  style={[
                    styles.barFill,
                    {
                      width: `${insight.confidence * 100}%` as any,
                      backgroundColor: confColor,
                    },
                  ]}
                />
              </View>
              <Text style={[styles.confPct, { color: confColor }]}>
                {Math.round(insight.confidence * 100)}%
              </Text>
            </View>
          </View>
          <View style={[styles.horizonPill, { backgroundColor: accentColor + '15' }]}>
            <Text style={[styles.horizonText, { color: accentColor }]}>{insight.timeHorizon}</Text>
          </View>
        </View>

        {/* ── Bias badge (optional) ── */}
        {insight.biasCheck?.detected && (
          <View style={styles.biasBadge}>
            <Icon name="shield" size={12} color="#007AFF" />
            <Text style={styles.biasText}>
              {insight.biasCheck.adjusted ? 'Bias detected & adjusted' : 'Bias detected'}
            </Text>
          </View>
        )}
      </TouchableOpacity>
    );
  };

  const renderSection = (title: string, emoji: string, insights: OracleInsight[] | undefined) => {
    if (!insights || insights.length === 0) return null;

    const color = getSectionColor(title);
    return (
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionEmoji}>{emoji}</Text>
          <Text style={[styles.sectionTitle, { color }]}>{title}</Text>
          <View style={[styles.countPill, { backgroundColor: color + '18' }]}>
            <Text style={[styles.countText, { color }]}>{insights.length}</Text>
          </View>
        </View>
        {insights.map((insight) => renderInsight(insight, color))}
      </View>
    );
  };

  return (
    <ScrollView
      contentContainerStyle={styles.scrollContainer}
      showsVerticalScrollIndicator={false}
    >
      {/* ── Header ── */}
      <View style={styles.oracleHeader}>
        <View style={styles.oracleTitleRow}>
          <View style={styles.oracleIconWrap}>
            <Icon name="eye" size={22} color="#007AFF" />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.oracleTitle}>Credit Oracle</Text>
            <Text style={styles.oracleSubtitle}>AI-powered predictive insights</Text>
          </View>
          <View style={styles.updatedChip}>
            <Text style={styles.updatedText}>
              {new Date(oracle.lastUpdated).toLocaleString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </Text>
          </View>
        </View>
      </View>

      {/* ── Sections ── */}
      {renderSection('Warnings', '⚠️', oracle.warnings)}
      {renderSection('Opportunities', '✨', oracle.opportunities)}
      {renderSection('Local Trends', '📍', oracle.localTrends)}
      {renderSection('Insights', '💡', oracle.insights)}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  scrollContainer: {
    flexGrow: 1,
    backgroundColor: '#F5F7FA',
    paddingBottom: 24,
  },

  // ── Header ──────────────────────────────────────────────────────────────────
  oracleHeader: {
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 20,
    paddingVertical: 18,
    marginBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#EFEFEF',
  },
  oracleTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  oracleIconWrap: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#007AFF15',
    alignItems: 'center',
    justifyContent: 'center',
  },
  oracleTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 2,
  },
  oracleSubtitle: {
    fontSize: 13,
    color: '#6B7280',
  },
  updatedChip: {
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 20,
  },
  updatedText: {
    fontSize: 11,
    color: '#6B7280',
    fontWeight: '500',
  },

  // ── Section ─────────────────────────────────────────────────────────────────
  section: {
    paddingHorizontal: 16,
    paddingTop: 20,
    paddingBottom: 4,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 14,
    gap: 8,
  },
  sectionEmoji: {
    fontSize: 18,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    flex: 1,
  },
  countPill: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  countText: {
    fontSize: 12,
    fontWeight: '700',
  },

  // ── Insight Card ─────────────────────────────────────────────────────────────
  insightCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderLeftWidth: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 3,
  },

  // Top row
  cardTop: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    marginBottom: 12,
  },
  iconCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  cardTopText: {
    flex: 1,
    gap: 6,
  },
  insightTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#111827',
    lineHeight: 21,
  },
  locationBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 10,
    alignSelf: 'flex-start',
  },
  locationText: {
    fontSize: 11,
    fontWeight: '600',
  },

  // Description
  description: {
    fontSize: 14,
    color: '#4B5563',
    lineHeight: 21,
    marginBottom: 14,
  },

  // Tip
  tipRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    backgroundColor: '#FFFBEB',
    borderRadius: 12,
    paddingVertical: 10,
    paddingHorizontal: 12,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: '#FDE68A',
  },
  tipText: {
    flex: 1,
    fontSize: 13,
    color: '#92400E',
    lineHeight: 19,
    fontWeight: '500',
  },

  // Footer
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  confidenceWrap: {
    flex: 1,
  },
  confidenceLabel: {
    fontSize: 11,
    color: '#9CA3AF',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 5,
    fontWeight: '600',
  },
  barRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  barTrack: {
    flex: 1,
    height: 5,
    backgroundColor: '#E5E7EB',
    borderRadius: 3,
    overflow: 'hidden',
  },
  barFill: {
    height: '100%',
    borderRadius: 3,
  },
  confPct: {
    fontSize: 13,
    fontWeight: '700',
    minWidth: 36,
    textAlign: 'right',
  },
  horizonPill: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 20,
  },
  horizonText: {
    fontSize: 12,
    fontWeight: '600',
  },

  // Bias badge
  biasBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 10,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
  },
  biasText: {
    fontSize: 12,
    color: '#007AFF',
    fontWeight: '600',
  },
});
