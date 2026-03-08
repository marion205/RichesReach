/**
 * Opportunity Discovery Screen
 * ============================
 * Tabbed multi-asset discovery hub: Real Estate | Alternatives | Fixed Income
 * Plus a "Private Markets" tab that navigates to the existing PrivateMarketsScreen.
 *
 * Features:
 *  - Graph Intelligence banner: cross-silo insight from the financial graph
 *  - Opportunity cards: score badge, tagline, graph rationale, meta chips
 *  - Saved watchlist (persisted via AsyncStorage through the demo service)
 *  - Loading / error / empty states
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import Feather from '@expo/vector-icons/Feather';
import { useNavigation } from '@react-navigation/native';

import { COLORS, SPACING, RADIUS } from '../theme/privateMarketsTheme';
import {
  getOpportunityDiscoveryService,
} from '../services/opportunityDiscoveryService';
import type { Opportunity, FinancialGraph, AssetClass } from '../types/opportunityTypes';

// ── Tab config ──────────────────────────────────────────────────────────────

type Tab = 'fixed_income' | 'real_estate' | 'alternatives' | 'private_markets';

const TABS: { key: Tab; label: string }[] = [
  { key: 'fixed_income', label: 'Fixed Income' },
  { key: 'real_estate', label: 'Real Estate' },
  { key: 'alternatives', label: 'Alternatives' },
  { key: 'private_markets', label: 'Private' },
];

// Category → accent colour for left stripe
const CATEGORY_COLOR: Record<string, string> = {
  treasury: '#10B981',    // green
  bond_ladder: '#059669',
  cd: '#34D399',
  reit: '#3B82F6',        // blue
  direct: '#1D4ED8',
  commodity: '#F59E0B',   // amber
  hedge_fund: '#7C3AED',  // purple
  venture: '#EF4444',     // red
  buyout: '#DC2626',
};

const RISK_COLOR: Record<string, string> = {
  low: '#059669',
  moderate: '#D97706',
  high: '#DC2626',
};

const RISK_BG: Record<string, string> = {
  low: '#D1FAE5',
  moderate: '#FEF3C7',
  high: '#FEE2E2',
};

// ── Component ───────────────────────────────────────────────────────────────

export default function OpportunityDiscoveryScreen() {
  const navigation = useNavigation<any>();
  const [activeTab, setActiveTab] = useState<Tab>('fixed_income');
  const [allOpportunities, setAllOpportunities] = useState<Opportunity[]>([]);
  const [financialGraph, setFinancialGraph] = useState<FinancialGraph | null>(null);
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const service = getOpportunityDiscoveryService();

  const loadData = useCallback(async () => {
    try {
      const [opps, graph, saved] = await Promise.all([
        service.getOpportunities({ includeGraphContext: true }),
        service.getFinancialGraph(),
        service.getSavedOpportunityIds(),
      ]);
      setAllOpportunities(opps);
      setFinancialGraph(graph);
      setSavedIds(new Set(saved));
      setError(null);
    } catch {
      setError('Could not load opportunities. Please try again.');
    }
  }, [service]);

  useEffect(() => {
    setLoading(true);
    loadData().finally(() => setLoading(false));
  }, [loadData]);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const toggleSave = async (id: string) => {
    const next = new Set(savedIds);
    if (next.has(id)) {
      next.delete(id);
      await service.unsaveOpportunity(id);
    } else {
      next.add(id);
      await service.saveOpportunity(id);
    }
    setSavedIds(next);
  };

  // Navigate to Private Markets when that tab is selected
  const handleTabPress = (tab: Tab) => {
    if (tab === 'private_markets') {
      navigation.navigate('PrivateMarkets');
      return;
    }
    setActiveTab(tab);
  };

  const tabOpportunities = allOpportunities.filter(
    (o) => o.assetClass === (activeTab as AssetClass),
  );

  const graphBannerText = financialGraph?.summarySentences?.[0] ?? null;

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={COLORS.accent} />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Discover</Text>
        <Text style={styles.subtitle}>Opportunities matched to your financial picture.</Text>
      </View>

      {/* Graph Intelligence Banner */}
      {graphBannerText && (
        <View style={styles.graphBanner}>
          <Feather name="activity" size={15} color={COLORS.accent} style={styles.bannerIcon} />
          <Text style={styles.graphBannerText}>{graphBannerText}</Text>
        </View>
      )}

      {/* Tab Bar */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.tabRowContent}
        style={styles.tabRow}
      >
        {TABS.map(({ key, label }) => (
          <Pressable
            key={key}
            onPress={() => handleTabPress(key)}
            accessibilityRole="tab"
            accessibilityState={{ selected: activeTab === key && key !== 'private_markets' }}
            style={styles.tabTouch}
          >
            <View
              style={[
                styles.tab,
                activeTab === key && key !== 'private_markets' && styles.tabActive,
              ]}
            >
              <Text
                style={[
                  styles.tabText,
                  activeTab === key && key !== 'private_markets' && styles.tabActiveText,
                ]}
              >
                {label}
              </Text>
            </View>
          </Pressable>
        ))}
      </ScrollView>

      {/* Content */}
      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={COLORS.accent} />
          <Text style={styles.loadingText}>Loading opportunities…</Text>
        </View>
      ) : error ? (
        <View style={styles.center}>
          <Feather name="alert-circle" size={32} color="#DC2626" />
          <Text style={styles.errorText}>{error}</Text>
        </View>
      ) : tabOpportunities.length === 0 ? (
        <View style={styles.center}>
          <Feather name="inbox" size={32} color={COLORS.textSecondary} />
          <Text style={styles.emptyText}>No opportunities in this category yet.</Text>
        </View>
      ) : (
        tabOpportunities.map((opp) => (
          <OpportunityCard
            key={opp.id}
            opportunity={opp}
            isSaved={savedIds.has(opp.id)}
            onSave={() => toggleSave(opp.id)}
            onPress={() =>
              navigation.navigate('OpportunityDetail', { opportunityId: opp.id })
            }
          />
        ))
      )}
    </ScrollView>
  );
}

// ── Opportunity Card ─────────────────────────────────────────────────────────

interface OpportunityCardProps {
  opportunity: Opportunity;
  isSaved: boolean;
  onSave: () => void;
  onPress: () => void;
}

function OpportunityCard({ opportunity: opp, isSaved, onSave, onPress }: OpportunityCardProps) {
  const stripeColor =
    CATEGORY_COLOR[opp.category as string] ?? COLORS.accent;

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.card, pressed && styles.cardPressed]}
      accessibilityRole="button"
      accessibilityLabel={`${opp.name}, score ${opp.score}`}
    >
      {/* Left category stripe */}
      <View style={[styles.categoryStripe, { backgroundColor: stripeColor }]} />

      <View style={styles.cardBody}>
        {/* Top row: name + score + save */}
        <View style={styles.cardTop}>
          <Text style={styles.cardName} numberOfLines={2}>
            {opp.name}
          </Text>
          <View style={styles.cardTopRight}>
            <View style={styles.scoreBadge}>
              <Text style={styles.scoreText}>{opp.score}</Text>
            </View>
            <Pressable
              onPress={onSave}
              hitSlop={8}
              accessibilityLabel={isSaved ? 'Remove from saved' : 'Save opportunity'}
            >
              <Feather
                name={isSaved ? 'bookmark' : 'bookmark'}
                size={18}
                color={isSaved ? COLORS.accent : COLORS.textSecondary}
                style={{ opacity: isSaved ? 1 : 0.5 }}
              />
            </Pressable>
          </View>
        </View>

        {/* Tagline */}
        <Text style={styles.cardTagline}>{opp.tagline}</Text>

        {/* Graph rationale */}
        {opp.graphRationale && (
          <View style={styles.rationaleBadge}>
            <Feather name="link" size={11} color={COLORS.accent} />
            <Text style={styles.rationaleText} numberOfLines={2}>
              {opp.graphRationale}
            </Text>
          </View>
        )}

        {/* Meta chips */}
        <View style={styles.chips}>
          {opp.expectedReturnRange && (
            <View style={styles.chip}>
              <Text style={styles.chipText}>{opp.expectedReturnRange}</Text>
            </View>
          )}
          {opp.liquidity && (
            <View style={styles.chip}>
              <Text style={styles.chipText}>{opp.liquidity}</Text>
            </View>
          )}
          {opp.riskLevel && (
            <View
              style={[
                styles.chip,
                { backgroundColor: RISK_BG[opp.riskLevel] ?? '#F1F5F9' },
              ]}
            >
              <Text
                style={[
                  styles.chipText,
                  { color: RISK_COLOR[opp.riskLevel] ?? COLORS.textSecondary },
                ]}
              >
                {opp.riskLevel} risk
              </Text>
            </View>
          )}
          {opp.minimumInvestment != null && (
            <View style={styles.chip}>
              <Text style={styles.chipText}>
                Min ${opp.minimumInvestment >= 1000
                  ? `${(opp.minimumInvestment / 1000).toFixed(0)}k`
                  : opp.minimumInvestment}
              </Text>
            </View>
          )}
        </View>
      </View>
    </Pressable>
  );
}

// ── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.promiseBg },
  content: { padding: SPACING.lg, paddingBottom: 40 },

  // Header
  header: { marginBottom: SPACING.lg },
  title: { fontSize: 26, fontWeight: '700', color: COLORS.text },
  subtitle: { fontSize: 14, color: COLORS.textSecondary, marginTop: 3 },

  // Graph banner
  graphBanner: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#EFF6FF',
    borderRadius: RADIUS.md,
    padding: SPACING.md,
    marginBottom: SPACING.md,
    borderLeftWidth: 3,
    borderLeftColor: COLORS.accent,
    gap: SPACING.sm,
  },
  bannerIcon: { marginTop: 1 },
  graphBannerText: {
    flex: 1,
    fontSize: 13,
    color: COLORS.text,
    lineHeight: 19,
    fontStyle: 'italic',
  },

  // Tab bar
  tabRow: { marginBottom: SPACING.md },
  tabRowContent: { gap: SPACING.sm, paddingRight: SPACING.lg },
  tabTouch: {},
  tab: {
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderRadius: RADIUS.xl,
    backgroundColor: '#E2E8F0',
  },
  tabActive: { backgroundColor: COLORS.accent },
  tabText: { fontSize: 13, fontWeight: '500', color: COLORS.textSecondary },
  tabActiveText: { color: '#FFFFFF' },

  // States
  center: { alignItems: 'center', paddingVertical: 40, gap: SPACING.md },
  loadingText: { fontSize: 14, color: COLORS.textSecondary },
  errorText: { fontSize: 14, color: '#DC2626', textAlign: 'center' },
  emptyText: { fontSize: 14, color: COLORS.textSecondary, textAlign: 'center' },

  // Card
  card: {
    flexDirection: 'row',
    backgroundColor: COLORS.bgCard,
    borderRadius: RADIUS.lg,
    marginBottom: SPACING.md,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: COLORS.border,
    overflow: 'hidden',
  },
  cardPressed: { opacity: 0.75 },
  categoryStripe: { width: 4 },
  cardBody: { flex: 1, padding: SPACING.lg },
  cardTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: SPACING.xs,
    gap: SPACING.sm,
  },
  cardTopRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    flexShrink: 0,
  },
  cardName: {
    flex: 1,
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.text,
    lineHeight: 20,
  },
  scoreBadge: {
    backgroundColor: COLORS.scoreBg,
    borderRadius: RADIUS.sm,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  scoreText: { color: '#FFFFFF', fontSize: 12, fontWeight: '700' },
  cardTagline: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginBottom: SPACING.sm,
    lineHeight: 18,
  },

  // Graph rationale
  rationaleBadge: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 5,
    backgroundColor: '#EFF6FF',
    borderRadius: RADIUS.sm,
    padding: SPACING.sm,
    marginBottom: SPACING.sm,
  },
  rationaleText: {
    flex: 1,
    fontSize: 12,
    color: '#1D4ED8',
    lineHeight: 17,
    fontStyle: 'italic',
  },

  // Meta chips
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  chip: {
    backgroundColor: '#F1F5F9',
    borderRadius: 99,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  chipText: { fontSize: 11, color: COLORS.textSecondary, fontWeight: '500' },
});
