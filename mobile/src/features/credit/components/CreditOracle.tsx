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
    if (section.includes('Insights') || section.includes('Trends')) return '#5AC8FA';
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

        {/* ── Feature 1: Negotiation Script ── */}
        {insight.negotiationScript && (
          <View style={styles.negotiationBox}>
            <View style={styles.featureHeaderRow}>
              <Icon name="phone" size={13} color="#007AFF" />
              <Text style={styles.featureLabel}>CALL SCRIPT</Text>
              <View style={styles.successRatePill}>
                <Text style={styles.successRateText}>
                  {Math.round(insight.negotiationScript.successRate * 100)}% success rate
                </Text>
              </View>
            </View>
            <Text style={styles.creditorName}>Call {insight.negotiationScript.creditor}</Text>
            <Text style={styles.scriptText} numberOfLines={5}>
              {insight.negotiationScript.scriptText}
            </Text>
            {insight.negotiationScript.bestTimeToCall && (
              <View style={styles.bestTimeRow}>
                <Icon name="clock" size={11} color="#34C759" />
                <Text style={styles.bestTimeText}>Best time: {insight.negotiationScript.bestTimeToCall}</Text>
              </View>
            )}
          </View>
        )}

        {/* ── Feature 2: Bureau Arbitrage ── */}
        {insight.bureauArbitrage && (
          <View style={styles.bureauBox}>
            <View style={styles.featureHeaderRow}>
              <Icon name="bar-chart-2" size={13} color="#AF52DE" />
              <Text style={[styles.featureLabel, { color: '#AF52DE' }]}>BUREAU ARBITRAGE</Text>
            </View>
            <View style={styles.bureauScoreRow}>
              <View style={styles.bureauScoreItem}>
                <Text style={styles.bureauLabel}>{insight.bureauArbitrage.highBureau.toUpperCase()}</Text>
                <Text style={styles.bureauScoreHigh}>{insight.bureauArbitrage.highScore}</Text>
                <View style={styles.useThisBadge}>
                  <Text style={styles.useThisText}>USE THIS</Text>
                </View>
              </View>
              <View style={styles.bureauDivider}>
                <Text style={styles.bureauDeltaText}>+{insight.bureauArbitrage.scoreDelta}</Text>
                <Text style={styles.bureauDeltaLabel}>pts higher</Text>
              </View>
              <View style={styles.bureauScoreItem}>
                <Text style={styles.bureauLabel}>{insight.bureauArbitrage.lowBureau.toUpperCase()}</Text>
                <Text style={styles.bureauScoreLow}>{insight.bureauArbitrage.lowScore}</Text>
              </View>
            </View>
            <Text style={styles.lendersLabel}>Lenders pulling {insight.bureauArbitrage.highBureau}:</Text>
            <Text style={styles.lendersList}>{insight.bureauArbitrage.recommendedLenders.join(' · ')}</Text>
            <Text style={styles.windowText}>Act within {insight.bureauArbitrage.windowDays} days</Text>
          </View>
        )}

        {/* ── Feature 4: Dollar Impact ── */}
        {insight.dollarImpact && (
          <View style={styles.dollarBox}>
            <View style={styles.featureHeaderRow}>
              <Icon name="dollar-sign" size={13} color="#15803D" />
              <Text style={[styles.featureLabel, { color: '#15803D' }]}>REAL DOLLAR IMPACT</Text>
            </View>
            <Text style={styles.dollarSavings}>${insight.dollarImpact.savings.toLocaleString()} saved</Text>
            <Text style={styles.dollarDetail}>
              on ${insight.dollarImpact.loanAmount.toLocaleString()} {insight.dollarImpact.loanType} loan
            </Text>
            <View style={styles.rateCompareRow}>
              <View style={styles.rateItem}>
                <Text style={styles.rateLabel}>Now</Text>
                <Text style={styles.rateBad}>{insight.dollarImpact.currentRate}%</Text>
              </View>
              <Icon name="arrow-right" size={16} color="#9CA3AF" />
              <View style={styles.rateItem}>
                <Text style={styles.rateLabel}>At {insight.dollarImpact.projectedScoreNeeded}+</Text>
                <Text style={styles.rateGood}>{insight.dollarImpact.qualifyingRate}%</Text>
              </View>
            </View>
            <Text style={styles.dollarTimeline}>{insight.dollarImpact.timeToQualify}</Text>
          </View>
        )}

        {/* ── Feature 5: Score Unlock Map ── */}
        {insight.scoreUnlocks && insight.scoreUnlocks.length > 0 && (
          <View style={styles.unlocksBox}>
            <View style={styles.featureHeaderRow}>
              <Icon name="unlock" size={13} color="#92400E" />
              <Text style={[styles.featureLabel, { color: '#92400E' }]}>SCORE UNLOCK MAP</Text>
            </View>
            {insight.scoreUnlocks.map((tier, idx) => (
              <View key={idx} style={[styles.unlockTier, idx === insight.scoreUnlocks!.length - 1 && { borderBottomWidth: 0 }]}>
                <View style={styles.unlockTierHeader}>
                  <Icon name="chevrons-up" size={12} color="#FF9500" />
                  <Text style={styles.unlockTierScore}>+{tier.scoreThreshold - (insight.scoreUnlocks![0].scoreThreshold - 20)} pts:</Text>
                </View>
                {tier.products.map((p, pIdx) => (
                  <View key={pIdx} style={styles.unlockProduct}>
                    <Text style={styles.unlockProductName}>{p.name}</Text>
                    {p.rate && <Text style={styles.unlockProductRate}>{p.rate}</Text>}
                  </View>
                ))}
              </View>
            ))}
          </View>
        )}

        {/* ── Feature 6: Soft-Pull Offers ── */}
        {insight.softPullOffers && insight.softPullOffers.length > 0 && (
          <View style={styles.softPullBox}>
            <View style={styles.featureHeaderRow}>
              <Icon name="check-circle" size={13} color="#34C759" />
              <Text style={[styles.featureLabel, { color: '#166534' }]}>NO HARD PULL</Text>
            </View>
            {insight.softPullOffers.map((offer, idx) => (
              <View key={idx} style={[styles.softPullOffer, idx === insight.softPullOffers!.length - 1 && { borderBottomWidth: 0 }]}>
                <View style={styles.softPullOfferLeft}>
                  <Text style={styles.softPullLender}>{offer.lender}</Text>
                  <Text style={styles.softPullProduct}>{offer.productName}</Text>
                  <Text style={styles.softPullRate}>{offer.apr}</Text>
                </View>
                {offer.expiresInDays && (
                  <View style={styles.expiryPill}>
                    <Text style={styles.expiryText}>{offer.expiresInDays}d left</Text>
                  </View>
                )}
              </View>
            ))}
          </View>
        )}

        {/* ── Feature 7: Shadow Score Coaching ── */}
        {insight.scoringModelInsight && (
          <View style={styles.shadowBox}>
            <View style={styles.featureHeaderRow}>
              <Icon name="layers" size={13} color="#FF6B6B" />
              <Text style={[styles.featureLabel, { color: '#FF6B6B' }]}>
                {insight.scoringModelInsight.model} MODEL
              </Text>
              <Text style={styles.shadowScore}>{insight.scoringModelInsight.modelScore}</Text>
            </View>
            <Text style={styles.shadowUsedFor}>Used for: {insight.scoringModelInsight.relevantFor}</Text>
            <Text style={styles.shadowDragLabel}>Primary drag:</Text>
            <Text style={styles.shadowDrag}>{insight.scoringModelInsight.primaryDrag}</Text>
          </View>
        )}

        {/* ── Feature 8: Community Playbook ── */}
        {insight.communityPlaybook && (
          <View style={styles.communityBox}>
            <View style={styles.featureHeaderRow}>
              <Icon name="users" size={13} color="#AF52DE" />
              <Text style={[styles.featureLabel, { color: '#AF52DE' }]}>COMMUNITY PLAYBOOK</Text>
            </View>
            <Text style={styles.communityPeerGroup}>{insight.communityPlaybook.peerGroup}</Text>
            <View style={styles.communityStatsRow}>
              <View style={styles.communityStatItem}>
                <Text style={styles.communityStatValue}>{insight.communityPlaybook.result}</Text>
                <Text style={styles.communityStatLabel}>avg result</Text>
              </View>
              <View style={styles.communityStatItem}>
                <Text style={styles.communityStatValue}>{insight.communityPlaybook.timeline}</Text>
                <Text style={styles.communityStatLabel}>timeline</Text>
              </View>
              <View style={styles.communityStatItem}>
                <Text style={styles.communityStatValue}>{Math.round(insight.communityPlaybook.successRate * 100)}%</Text>
                <Text style={styles.communityStatLabel}>success rate</Text>
              </View>
            </View>
            <Text style={styles.communitySampleSize}>Based on {insight.communityPlaybook.sampleSize} users</Text>
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
      {renderSection('Insights & Trends', '💡', oracle.insights.filter(i => i.type === 'trend'))}
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

  // ── Shared feature block ─────────────────────────────────────────────────
  featureHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 8,
  },
  featureLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: '#007AFF',
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    flex: 1,
  },

  // ── Feature 1: Negotiation Script ────────────────────────────────────────
  negotiationBox: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#DBEAFE',
    backgroundColor: '#EFF6FF',
    borderRadius: 10,
    padding: 12,
  },
  successRatePill: {
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  successRateText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#166534',
  },
  creditorName: {
    fontSize: 15,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 6,
  },
  scriptText: {
    fontSize: 13,
    color: '#374151',
    lineHeight: 19,
    fontStyle: 'italic',
    marginBottom: 8,
  },
  bestTimeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  bestTimeText: {
    fontSize: 12,
    color: '#34C759',
    fontWeight: '600',
  },

  // ── Feature 2: Bureau Arbitrage ──────────────────────────────────────────
  bureauBox: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#E9D5FF',
    backgroundColor: '#FAF5FF',
    borderRadius: 10,
    padding: 12,
  },
  bureauScoreRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  bureauScoreItem: {
    flex: 1,
    alignItems: 'center',
    gap: 4,
  },
  bureauLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: '#6B7280',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  bureauScoreHigh: {
    fontSize: 30,
    fontWeight: '800',
    color: '#34C759',
  },
  bureauScoreLow: {
    fontSize: 30,
    fontWeight: '800',
    color: '#9CA3AF',
  },
  useThisBadge: {
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  useThisText: {
    fontSize: 9,
    fontWeight: '700',
    color: '#166534',
  },
  bureauDivider: {
    alignItems: 'center',
    paddingHorizontal: 8,
  },
  bureauDeltaText: {
    fontSize: 16,
    fontWeight: '800',
    color: '#AF52DE',
  },
  bureauDeltaLabel: {
    fontSize: 10,
    color: '#AF52DE',
    fontWeight: '600',
  },
  lendersLabel: {
    fontSize: 11,
    color: '#6B7280',
    marginBottom: 2,
  },
  lendersList: {
    fontSize: 13,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 6,
  },
  windowText: {
    fontSize: 12,
    color: '#FF9500',
    fontWeight: '700',
  },

  // ── Feature 4: Dollar Impact ─────────────────────────────────────────────
  dollarBox: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#BBF7D0',
    backgroundColor: '#F0FDF4',
    borderRadius: 10,
    padding: 12,
  },
  dollarSavings: {
    fontSize: 30,
    fontWeight: '800',
    color: '#15803D',
    marginBottom: 2,
  },
  dollarDetail: {
    fontSize: 13,
    color: '#6B7280',
    marginBottom: 10,
  },
  rateCompareRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 8,
    justifyContent: 'center',
  },
  rateItem: {
    flex: 1,
    alignItems: 'center',
  },
  rateLabel: {
    fontSize: 10,
    color: '#9CA3AF',
    textTransform: 'uppercase',
    fontWeight: '600',
    marginBottom: 2,
  },
  rateBad: {
    fontSize: 22,
    fontWeight: '800',
    color: '#FF6B6B',
  },
  rateGood: {
    fontSize: 22,
    fontWeight: '800',
    color: '#34C759',
  },
  dollarTimeline: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6B7280',
    textAlign: 'center',
  },

  // ── Feature 5: Score Unlock Map ──────────────────────────────────────────
  unlocksBox: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#FDE68A',
    backgroundColor: '#FFFBEB',
    borderRadius: 10,
    padding: 12,
  },
  unlockTier: {
    marginBottom: 8,
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#FDE68A',
  },
  unlockTierHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginBottom: 4,
  },
  unlockTierScore: {
    fontSize: 12,
    fontWeight: '700',
    color: '#92400E',
  },
  unlockProduct: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 2,
  },
  unlockProductName: {
    fontSize: 13,
    color: '#111827',
    fontWeight: '500',
    flex: 1,
  },
  unlockProductRate: {
    fontSize: 12,
    color: '#6B7280',
  },

  // ── Feature 6: Soft-Pull Offers ──────────────────────────────────────────
  softPullBox: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#BBF7D0',
    backgroundColor: '#F0FDF4',
    borderRadius: 10,
    padding: 12,
  },
  softPullOffer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#D1FAE5',
  },
  softPullOfferLeft: {
    flex: 1,
  },
  softPullLender: {
    fontSize: 13,
    fontWeight: '700',
    color: '#111827',
  },
  softPullProduct: {
    fontSize: 12,
    color: '#4B5563',
  },
  softPullRate: {
    fontSize: 11,
    color: '#9CA3AF',
  },
  expiryPill: {
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 10,
    marginLeft: 8,
  },
  expiryText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#92400E',
  },

  // ── Feature 7: Shadow Score ──────────────────────────────────────────────
  shadowBox: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#FECACA',
    backgroundColor: '#FFF1F2',
    borderRadius: 10,
    padding: 12,
  },
  shadowScore: {
    fontSize: 20,
    fontWeight: '800',
    color: '#FF6B6B',
  },
  shadowUsedFor: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 6,
  },
  shadowDragLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: '#9CA3AF',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  shadowDrag: {
    fontSize: 13,
    fontWeight: '600',
    color: '#111827',
  },

  // ── Feature 8: Community Playbook ────────────────────────────────────────
  communityBox: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#E9D5FF',
    backgroundColor: '#FAF5FF',
    borderRadius: 10,
    padding: 12,
  },
  communityPeerGroup: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 10,
    fontStyle: 'italic',
  },
  communityStatsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  communityStatItem: {
    flex: 1,
    alignItems: 'center',
  },
  communityStatValue: {
    fontSize: 15,
    fontWeight: '800',
    color: '#AF52DE',
    textAlign: 'center',
  },
  communityStatLabel: {
    fontSize: 10,
    color: '#9CA3AF',
    textTransform: 'uppercase',
    fontWeight: '600',
    textAlign: 'center',
  },
  communitySampleSize: {
    fontSize: 11,
    color: '#9CA3AF',
    textAlign: 'right',
  },
});
