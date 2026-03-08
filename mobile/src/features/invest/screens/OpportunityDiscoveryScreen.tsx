/**
 * Opportunity Discovery Screen — 2026 Premium Redesign
 * =====================================================
 * Tabbed multi-asset discovery: Fixed Income | Real Estate | Alternatives
 * + "Private" tab that hands off to the existing PrivateMarketsScreen.
 *
 * Design language:
 *  - Dark navy hero header with gradient
 *  - Frosted stat row (graph intelligence summary)
 *  - Pill tab bar with smooth active state
 *  - Score arc badge with asset-class accent color
 *  - Graph rationale chip (indigo tint, link icon)
 *  - Liquidity / risk / return meta row
 *  - Pull-to-refresh, save/unsave, loading skeleton
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  ActivityIndicator,
  RefreshControl,
  Animated,
  Dimensions,
  StatusBar,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Feather from '@expo/vector-icons/Feather';
import { useNavigation } from '@react-navigation/native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  getOpportunityDiscoveryService,
} from '../services/opportunityDiscoveryService';
import type { Opportunity, FinancialGraph, AssetClass } from '../types/opportunityTypes';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

// ── Design tokens ────────────────────────────────────────────────────────────

const D = {
  // Core palette
  navy: '#0B1426',
  navyMid: '#0F1E35',
  navyLight: '#162642',
  white: '#FFFFFF',
  offWhite: '#F8FAFC',
  // Accents
  blue: '#3B82F6',
  blueLight: '#60A5FA',
  blueFaint: '#EFF6FF',
  indigo: '#6366F1',
  indigoFaint: '#EEF2FF',
  // Semantic
  green: '#10B981',
  greenFaint: '#D1FAE5',
  amber: '#F59E0B',
  amberFaint: '#FEF3C7',
  red: '#EF4444',
  redFaint: '#FEE2E2',
  // Text
  textPrimary: '#0F172A',
  textSecondary: '#64748B',
  textMuted: '#94A3B8',
  // Surfaces
  card: '#FFFFFF',
  cardBorder: '#E2E8F0',
  bg: '#F1F5F9',
  // Spacing
  r4: 4, r8: 8, r12: 12, r16: 16, r20: 20, r24: 24,
};

// ── Asset class config ────────────────────────────────────────────────────────

type Tab = 'fixed_income' | 'real_estate' | 'alternatives' | 'private_markets';

const TABS: { key: Tab; label: string; icon: keyof typeof Feather.glyphMap }[] = [
  { key: 'fixed_income',    label: 'Fixed Income',  icon: 'shield' },
  { key: 'real_estate',     label: 'Real Estate',   icon: 'home' },
  { key: 'alternatives',    label: 'Alternatives',  icon: 'trending-up' },
  { key: 'private_markets', label: 'Private',       icon: 'lock' },
];

const ASSET_ACCENT: Record<string, string> = {
  fixed_income:    '#10B981',
  real_estate:     '#3B82F6',
  alternatives:    '#F59E0B',
  private_markets: '#7C3AED',
};

const ASSET_GRADIENT: Record<string, [string, string]> = {
  fixed_income:    ['#065F46', '#10B981'],
  real_estate:     ['#1E40AF', '#3B82F6'],
  alternatives:    ['#92400E', '#F59E0B'],
  private_markets: ['#4C1D95', '#7C3AED'],
};

const CATEGORY_ACCENT: Record<string, string> = {
  treasury: '#10B981', bond_ladder: '#059669', cd: '#34D399',
  reit: '#3B82F6', direct: '#1D4ED8',
  commodity: '#F59E0B', hedge_fund: '#7C3AED',
};

const RISK_STYLES: Record<string, { color: string; bg: string; label: string }> = {
  low:      { color: '#059669', bg: '#D1FAE5', label: 'Low risk' },
  moderate: { color: '#D97706', bg: '#FEF3C7', label: 'Moderate' },
  high:     { color: '#DC2626', bg: '#FEE2E2', label: 'High risk' },
};

const LIQUIDITY_ICON: Record<string, keyof typeof Feather.glyphMap> = {
  daily:     'refresh-cw',
  quarterly: 'calendar',
  illiquid:  'lock',
};

// ── Main component ────────────────────────────────────────────────────────────

export default function OpportunityDiscoveryScreen() {
  const navigation = useNavigation<any>();
  const insets = useSafeAreaInsets();
  const [activeTab, setActiveTab] = useState<Tab>('fixed_income');
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [financialGraph, setFinancialGraph] = useState<FinancialGraph | null>(null);
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Entrance animation
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(24)).current;

  const service = getOpportunityDiscoveryService();

  const loadData = useCallback(async () => {
    try {
      const [opps, graph, saved] = await Promise.all([
        service.getOpportunities({ includeGraphContext: true }),
        service.getFinancialGraph(),
        service.getSavedOpportunityIds(),
      ]);
      setOpportunities(opps);
      setFinancialGraph(graph);
      setSavedIds(new Set(saved));
      setError(null);
    } catch {
      setError('Could not load opportunities.');
    }
  }, [service]);

  useEffect(() => {
    setLoading(true);
    loadData().finally(() => {
      setLoading(false);
      Animated.parallel([
        Animated.timing(fadeAnim, { toValue: 1, duration: 500, useNativeDriver: true }),
        Animated.timing(slideAnim, { toValue: 0, duration: 500, useNativeDriver: true }),
      ]).start();
    });
  }, [loadData]);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const toggleSave = async (id: string) => {
    const next = new Set(savedIds);
    if (next.has(id)) { next.delete(id); await service.unsaveOpportunity(id); }
    else              { next.add(id);    await service.saveOpportunity(id); }
    setSavedIds(next);
  };

  const handleTabPress = (tab: Tab) => {
    if (tab === 'private_markets') { navigation.navigate('PrivateMarkets'); return; }
    setActiveTab(tab);
  };

  const tabOpps = opportunities.filter(o => o.assetClass === (activeTab as AssetClass));
  const accent = ASSET_ACCENT[activeTab] ?? D.blue;
  const [gradStart, gradEnd] = ASSET_GRADIENT[activeTab] ?? [D.navyMid, D.navy];

  // Graph summary stats
  const graphStats: { label: string; value: string; icon: keyof typeof Feather.glyphMap }[] = [];
  if (financialGraph) {
    if (financialGraph.totalCcMinPayments)
      graphStats.push({ label: 'Freed/mo', value: `$${financialGraph.totalCcMinPayments.toLocaleString()}`, icon: 'arrow-up-right' });
    if (financialGraph.emergencyFundMonths)
      graphStats.push({ label: 'Emerg. fund', value: `${financialGraph.emergencyFundMonths.toFixed(1)}mo`, icon: 'shield' });
    if (financialGraph.avgCreditUtilization != null)
      graphStats.push({ label: 'Utilization', value: `${(financialGraph.avgCreditUtilization * 100).toFixed(0)}%`, icon: 'credit-card' });
    if (financialGraph.investableSurplusMonthly)
      graphStats.push({ label: 'Surplus', value: `$${financialGraph.investableSurplusMonthly.toLocaleString()}`, icon: 'zap' });
  }

  return (
    <View style={[styles.root, { paddingTop: insets.top }]}>
      <StatusBar barStyle="light-content" />

      {/* ── Hero Header ──────────────────────────────────────────────────── */}
      <LinearGradient colors={[D.navy, D.navyMid]} style={styles.hero}>
        <View style={styles.heroTop}>
          <View>
            <Text style={styles.heroEyebrow}>OPPORTUNITY DISCOVERY</Text>
            <Text style={styles.heroTitle}>Discover</Text>
            <Text style={styles.heroSubtitle}>Matched to your financial picture</Text>
          </View>
          <View style={[styles.heroIconWrap, { backgroundColor: `${accent}22` }]}>
            <Feather name="compass" size={26} color={accent} />
          </View>
        </View>

        {/* Graph stats strip */}
        {graphStats.length > 0 && (
          <View style={styles.statsRow}>
            {graphStats.map((s, i) => (
              <View key={i} style={styles.statPill}>
                <Feather name={s.icon} size={11} color={accent} />
                <Text style={styles.statValue}>{s.value}</Text>
                <Text style={styles.statLabel}>{s.label}</Text>
              </View>
            ))}
          </View>
        )}
      </LinearGradient>

      {/* ── Tab bar ──────────────────────────────────────────────────────── */}
      <View style={styles.tabBarWrap}>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.tabBarContent}
        >
          {TABS.map(({ key, label, icon }) => {
            const isActive = activeTab === key && key !== 'private_markets';
            const tabAccent = ASSET_ACCENT[key] ?? D.blue;
            return (
              <Pressable
                key={key}
                onPress={() => handleTabPress(key)}
                style={({ pressed }) => [styles.tabPill, pressed && { opacity: 0.7 }]}
                accessibilityRole="tab"
                accessibilityState={{ selected: isActive }}
              >
                <LinearGradient
                  colors={isActive ? [tabAccent, tabAccent] : ['transparent', 'transparent']}
                  style={[styles.tabPillInner, isActive && styles.tabPillActive]}
                >
                  <Feather name={icon} size={13} color={isActive ? '#fff' : D.textSecondary} />
                  <Text style={[styles.tabLabel, isActive && styles.tabLabelActive]}>
                    {label}
                  </Text>
                </LinearGradient>
              </Pressable>
            );
          })}
        </ScrollView>
      </View>

      {/* ── Graph Intelligence Banner ─────────────────────────────────────── */}
      {financialGraph?.summarySentences?.[0] && (
        <View style={styles.bannerWrap}>
          <View style={[styles.banner, { borderLeftColor: accent }]}>
            <View style={[styles.bannerDot, { backgroundColor: accent }]} />
            <Text style={styles.bannerText} numberOfLines={2}>
              {financialGraph.summarySentences[0]}
            </Text>
            <Feather name="chevron-right" size={14} color={D.textMuted} />
          </View>
        </View>
      )}

      {/* ── Content ──────────────────────────────────────────────────────── */}
      <Animated.ScrollView
        style={{ opacity: fadeAnim, transform: [{ translateY: slideAnim }] }}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={accent} />
        }
      >
        {loading ? (
          <View style={styles.center}>
            <ActivityIndicator size="large" color={accent} />
            <Text style={styles.centerText}>Loading opportunities…</Text>
          </View>
        ) : error ? (
          <View style={styles.center}>
            <View style={styles.errorIconWrap}>
              <Feather name="alert-circle" size={28} color={D.red} />
            </View>
            <Text style={styles.errorTitle}>Something went wrong</Text>
            <Text style={styles.centerText}>{error}</Text>
          </View>
        ) : tabOpps.length === 0 ? (
          <View style={styles.center}>
            <View style={styles.emptyIconWrap}>
              <Feather name="inbox" size={28} color={D.textMuted} />
            </View>
            <Text style={styles.emptyTitle}>Coming soon</Text>
            <Text style={styles.centerText}>No opportunities in this category yet.</Text>
          </View>
        ) : (
          <>
            <Text style={styles.sectionHeader}>
              {tabOpps.length} OPPORTUNITIES
            </Text>
            {tabOpps.map((opp, idx) => (
              <OpportunityCard
                key={opp.id}
                opportunity={opp}
                isSaved={savedIds.has(opp.id)}
                assetAccent={ASSET_ACCENT[opp.assetClass] ?? D.blue}
                onSave={() => toggleSave(opp.id)}
                onPress={() => navigation.navigate('OpportunityDetail', { opportunityId: opp.id })}
                index={idx}
              />
            ))}
            <View style={{ height: 32 }} />
          </>
        )}
      </Animated.ScrollView>
    </View>
  );
}

// ── Opportunity Card ──────────────────────────────────────────────────────────

interface CardProps {
  opportunity: Opportunity;
  isSaved: boolean;
  assetAccent: string;
  onSave: () => void | Promise<void>;
  onPress: () => void;
  index: number;
}

function OpportunityCard({ opportunity: opp, isSaved, assetAccent, onSave, onPress, index }: CardProps) {
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const catAccent = CATEGORY_ACCENT[opp.category as string] ?? assetAccent;
  const riskStyle = RISK_STYLES[opp.riskLevel ?? ''] ?? null;
  const liquidityIcon = LIQUIDITY_ICON[opp.liquidity ?? ''] ?? 'clock';

  const onPressIn  = () => Animated.spring(scaleAnim, { toValue: 0.975, useNativeDriver: true, speed: 50 }).start();
  const onPressOut = () => Animated.spring(scaleAnim, { toValue: 1,     useNativeDriver: true, speed: 50 }).start();

  return (
    <Animated.View style={{ transform: [{ scale: scaleAnim }] }}>
      <Pressable
        onPress={onPress}
        onPressIn={onPressIn}
        onPressOut={onPressOut}
        style={styles.card}
        accessibilityRole="button"
        accessibilityLabel={`${opp.name}, score ${opp.score}`}
      >
        {/* Top accent line */}
        <View style={[styles.cardAccentLine, { backgroundColor: catAccent }]} />

        <View style={styles.cardInner}>
          {/* Header row */}
          <View style={styles.cardHeader}>
            <View style={styles.cardHeaderLeft}>
              {/* Score ring */}
              <View style={[styles.scoreWrap, { borderColor: catAccent }]}>
                <Text style={[styles.scoreNum, { color: catAccent }]}>{opp.score}</Text>
              </View>
              <View style={styles.cardTitleWrap}>
                <Text style={styles.cardName} numberOfLines={2}>{opp.name}</Text>
                <Text style={styles.cardTagline} numberOfLines={1}>{opp.tagline}</Text>
              </View>
            </View>
            <Pressable onPress={onSave} hitSlop={10} style={styles.saveBtn}>
              <Feather
                name="bookmark"
                size={19}
                color={isSaved ? assetAccent : D.textMuted}
                style={{ opacity: isSaved ? 1 : 0.45 }}
              />
            </Pressable>
          </View>

          {/* Graph rationale */}
          {opp.graphRationale && (
            <View style={styles.rationaleRow}>
              <View style={styles.rationaleIcon}>
                <Feather name="link-2" size={11} color={D.indigo} />
              </View>
              <Text style={styles.rationaleText} numberOfLines={2}>
                {opp.graphRationale}
              </Text>
            </View>
          )}

          {/* Meta row */}
          <View style={styles.metaRow}>
            {opp.expectedReturnRange && (
              <View style={styles.metaChip}>
                <Feather name="trending-up" size={10} color={D.green} />
                <Text style={[styles.metaChipText, { color: D.green }]}>{opp.expectedReturnRange}</Text>
              </View>
            )}
            {opp.liquidity && (
              <View style={styles.metaChip}>
                <Feather name={liquidityIcon} size={10} color={D.textSecondary} />
                <Text style={styles.metaChipText}>{opp.liquidity}</Text>
              </View>
            )}
            {riskStyle && (
              <View style={[styles.metaChip, { backgroundColor: riskStyle.bg }]}>
                <Text style={[styles.metaChipText, { color: riskStyle.color }]}>{riskStyle.label}</Text>
              </View>
            )}
            {opp.minimumInvestment != null && (
              <View style={[styles.metaChip, styles.metaChipRight]}>
                <Text style={styles.metaChipText}>
                  Min {opp.minimumInvestment >= 1000
                    ? `$${(opp.minimumInvestment / 1000).toFixed(0)}k`
                    : `$${opp.minimumInvestment}`}
                </Text>
              </View>
            )}
          </View>

          {/* CTA footer */}
          <View style={styles.cardFooter}>
            <Text style={[styles.cardCta, { color: catAccent }]}>View details →</Text>
          </View>
        </View>
      </Pressable>
    </Animated.View>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: D.bg },

  // Hero
  hero: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 20,
  },
  heroTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  heroEyebrow: {
    fontSize: 10,
    fontWeight: '700',
    color: 'rgba(255,255,255,0.45)',
    letterSpacing: 1.5,
    marginBottom: 4,
  },
  heroTitle: {
    fontSize: 30,
    fontWeight: '800',
    color: D.white,
    letterSpacing: -0.5,
  },
  heroSubtitle: {
    fontSize: 13,
    color: 'rgba(255,255,255,0.55)',
    marginTop: 3,
  },
  heroIconWrap: {
    width: 52,
    height: 52,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },

  // Stats strip
  statsRow: {
    flexDirection: 'row',
    gap: 8,
    flexWrap: 'wrap',
  },
  statPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderRadius: 99,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: 'rgba(255,255,255,0.12)',
  },
  statValue: {
    fontSize: 12,
    fontWeight: '700',
    color: D.white,
  },
  statLabel: {
    fontSize: 10,
    color: 'rgba(255,255,255,0.5)',
    fontWeight: '500',
  },

  // Tab bar
  tabBarWrap: {
    backgroundColor: D.white,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: D.cardBorder,
  },
  tabBarContent: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    gap: 8,
  },
  tabPill: { borderRadius: 99 },
  tabPillInner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: 99,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: D.cardBorder,
  },
  tabPillActive: { borderColor: 'transparent' },
  tabLabel: {
    fontSize: 13,
    fontWeight: '500',
    color: D.textSecondary,
  },
  tabLabelActive: { color: D.white, fontWeight: '600' },

  // Banner
  bannerWrap: {
    backgroundColor: D.white,
    paddingHorizontal: 16,
    paddingBottom: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: D.cardBorder,
  },
  banner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: D.indigoFaint,
    borderRadius: D.r12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderLeftWidth: 3,
    borderLeftColor: D.indigo,
  },
  bannerDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  bannerText: {
    flex: 1,
    fontSize: 12,
    color: '#312E81',
    fontWeight: '500',
    lineHeight: 17,
  },

  // List
  listContent: {
    paddingHorizontal: 16,
    paddingTop: 16,
  },
  sectionHeader: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.2,
    color: D.textMuted,
    marginBottom: 12,
    marginLeft: 2,
  },

  // Center states
  center: {
    alignItems: 'center',
    paddingVertical: 60,
    gap: 10,
  },
  centerText: { fontSize: 14, color: D.textSecondary, textAlign: 'center' },
  errorIconWrap: {
    width: 52, height: 52, borderRadius: 26,
    backgroundColor: D.redFaint,
    alignItems: 'center', justifyContent: 'center',
  },
  errorTitle: { fontSize: 16, fontWeight: '700', color: D.textPrimary },
  emptyIconWrap: {
    width: 52, height: 52, borderRadius: 26,
    backgroundColor: D.bg,
    alignItems: 'center', justifyContent: 'center',
  },
  emptyTitle: { fontSize: 16, fontWeight: '700', color: D.textPrimary },

  // Card
  card: {
    backgroundColor: D.card,
    borderRadius: D.r20,
    marginBottom: 14,
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07,
    shadowRadius: 12,
    elevation: 3,
    overflow: 'hidden',
  },
  cardAccentLine: {
    height: 3,
    width: '100%',
  },
  cardInner: { padding: 18 },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  cardHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    flex: 1,
    gap: 12,
  },
  scoreWrap: {
    width: 46,
    height: 46,
    borderRadius: 23,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    backgroundColor: D.offWhite,
  },
  scoreNum: {
    fontSize: 15,
    fontWeight: '800',
    letterSpacing: -0.3,
  },
  cardTitleWrap: { flex: 1 },
  cardName: {
    fontSize: 16,
    fontWeight: '700',
    color: D.textPrimary,
    letterSpacing: -0.2,
    lineHeight: 22,
    marginBottom: 2,
  },
  cardTagline: {
    fontSize: 12,
    color: D.textSecondary,
    lineHeight: 17,
  },
  saveBtn: { paddingLeft: 8 },

  // Graph rationale
  rationaleRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    backgroundColor: D.indigoFaint,
    borderRadius: D.r8,
    padding: 10,
    marginBottom: 12,
  },
  rationaleIcon: {
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: `${D.indigo}18`,
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    marginTop: 1,
  },
  rationaleText: {
    flex: 1,
    fontSize: 12,
    color: '#3730A3',
    lineHeight: 17,
    fontStyle: 'italic',
  },

  // Meta
  metaRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginBottom: 14,
  },
  metaChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: D.bg,
    borderRadius: 99,
    paddingHorizontal: 9,
    paddingVertical: 4,
  },
  metaChipRight: { marginLeft: 'auto' },
  metaChipText: {
    fontSize: 11,
    fontWeight: '500',
    color: D.textSecondary,
  },

  // Footer
  cardFooter: {
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: D.cardBorder,
    paddingTop: 12,
  },
  cardCta: {
    fontSize: 13,
    fontWeight: '600',
  },
});
