/**
 * ReallocateScreen — Money Reallocation Engine
 * =============================================
 * "You freed $120/mo — here's how to grow it."
 *
 * Receives a monthly amount (typically from LeakDetector) and shows:
 *  - Hero with freed amount + headline projection
 *  - Strategy category cards (Growth, Dividend, AI, Fixed Income, Real Estate)
 *  - Each card shows fit score, graph rationale, examples, projections
 *  - "Explore" CTA to open Opportunity Discovery filtered by category
 *
 * 2026 Premium Design Language:
 *  - Dark navy hero with gradient
 *  - Frosted projection card
 *  - Strategy cards with accent colors and progress indicators
 *  - Animated micro-interactions
 */

import React, { useRef, useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  RefreshControl,
  Animated,
  StatusBar,
  Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Feather from '@expo/vector-icons/Feather';
import { useNavigation, useRoute } from '@react-navigation/native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useQuery, gql } from '@apollo/client';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

// ── GraphQL Query ─────────────────────────────────────────────────────────────

const GET_REALLOCATION_STRATEGIES = gql`
  query GetReallocationStrategies($monthlyAmount: Float!) {
    reallocationStrategies(monthlyAmount: $monthlyAmount) {
      userId
      monthlyAmount
      annualAmount
      headlineSentence
      currentPortfolioSummary
      dataQuality
      strategies {
        id
        name
        tagline
        icon
        color
        riskLevel
        timeHorizon
        fitScore
        graphRationale
        warning
        examples {
          symbol
          name
          description
          assetClass
        }
        projections {
          returnRate
          returnLabel
          value10yr
          value20yr
          value30yr
        }
      }
    }
  }
`;

// ── Design Tokens ─────────────────────────────────────────────────────────────

const D = {
  navy:          '#0B1426',
  navyMid:       '#0F1E35',
  navyLight:     '#162642',
  blue:          '#3B82F6',
  green:         '#10B981',
  red:           '#EF4444',
  amber:         '#F59E0B',
  indigo:        '#6366F1',
  purple:        '#7C3AED',
  white:         '#FFFFFF',
  textPrimary:   '#0F172A',
  textSecondary: '#64748B',
  textMuted:     '#94A3B8',
  card:          '#FFFFFF',
  cardBorder:    '#E2E8F0',
  bg:            '#F1F5F9',
  greenFaint:    '#D1FAE5',
  blueFaint:     '#EFF6FF',
  indigoFaint:   '#EEF2FF',
  amberFaint:    '#FEF3C7',
  purpleFaint:   '#F3E8FF',
  redFaint:      '#FEE2E2',
};

// ── Formatting ────────────────────────────────────────────────────────────────

const fmt = (n: number) => '$' + Math.abs(n).toLocaleString('en-US', { maximumFractionDigits: 0 });
const fmtK = (n: number) => {
  if (n >= 1000000) return '$' + (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return '$' + (n / 1000).toFixed(0) + 'K';
  return fmt(n);
};

// ── Skeleton ──────────────────────────────────────────────────────────────────

function SkeletonLine({ width, height = 14, style }: { width: number | string; height?: number; style?: object }) {
  const shimmer = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(shimmer, { toValue: 1, duration: 850, useNativeDriver: true }),
        Animated.timing(shimmer, { toValue: 0, duration: 850, useNativeDriver: true }),
      ])
    ).start();
  }, [shimmer]);
  const opacity = shimmer.interpolate({ inputRange: [0, 1], outputRange: [0.25, 0.55] });
  return <Animated.View style={[{ width, height, borderRadius: 6, backgroundColor: D.textMuted, opacity }, style]} />;
}

function LoadingSkeleton() {
  return (
    <View style={{ paddingHorizontal: 16, paddingTop: 24 }}>
      {[1, 2, 3].map(i => (
        <View key={i} style={[styles.card, { padding: 18, gap: 14 }]}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
            <SkeletonLine width={48} height={48} style={{ borderRadius: 14 }} />
            <View style={{ flex: 1, gap: 6 }}>
              <SkeletonLine width="70%" height={18} />
              <SkeletonLine width="50%" height={12} />
            </View>
          </View>
          <SkeletonLine width="100%" height={60} style={{ borderRadius: 12 }} />
          <SkeletonLine width="40%" height={36} style={{ borderRadius: 10 }} />
        </View>
      ))}
    </View>
  );
}

// ── Fit Score Badge ───────────────────────────────────────────────────────────

function FitScoreBadge({ score }: { score: number }) {
  const color = score >= 70 ? D.green : score >= 50 ? D.amber : D.red;
  const label = score >= 70 ? 'Great Fit' : score >= 50 ? 'Good Fit' : 'Consider';
  
  return (
    <View style={[styles.fitBadge, { backgroundColor: color + '22', borderColor: color + '44' }]}>
      <Text style={[styles.fitBadgeScore, { color }]}>{score}</Text>
      <Text style={[styles.fitBadgeLabel, { color }]}>{label}</Text>
    </View>
  );
}

// ── Strategy Card ─────────────────────────────────────────────────────────────

interface Strategy {
  id: string;
  name: string;
  tagline: string;
  icon: string;
  color: string;
  riskLevel: string;
  timeHorizon: string;
  fitScore: number;
  graphRationale?: string;
  warning?: string;
  examples: Array<{ symbol: string; name: string; description: string; assetClass: string }>;
  projections: Array<{ returnRate: number; returnLabel: string; value10yr: number; value20yr: number; value30yr: number }>;
}

function StrategyCard({ strategy, onExplore }: { strategy: Strategy; onExplore: () => void }) {
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const [expanded, setExpanded] = useState(false);
  
  const onPressIn = () => Animated.spring(scaleAnim, { toValue: 0.98, useNativeDriver: true, speed: 50 }).start();
  const onPressOut = () => Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true, speed: 50 }).start();
  
  const iconName = (strategy.icon || 'trending-up') as keyof typeof Feather.glyphMap;
  const bestProjection = strategy.projections?.reduce((best, p) => p.value30yr > best.value30yr ? p : best, strategy.projections[0]);
  
  return (
    <Animated.View style={{ transform: [{ scale: scaleAnim }] }}>
      <Pressable
        onPressIn={onPressIn}
        onPressOut={onPressOut}
        onPress={() => setExpanded(!expanded)}
        style={styles.card}
      >
        {/* Header */}
        <View style={styles.strategyHeader}>
          <View style={[styles.strategyIconWrap, { backgroundColor: strategy.color + '22' }]}>
            <Feather name={iconName} size={22} color={strategy.color} />
          </View>
          <View style={{ flex: 1, marginLeft: 12 }}>
            <Text style={styles.strategyName}>{strategy.name}</Text>
            <Text style={styles.strategyTagline}>{strategy.tagline}</Text>
          </View>
          <FitScoreBadge score={strategy.fitScore} />
        </View>
        
        {/* Graph rationale */}
        {strategy.graphRationale && (
          <View style={[styles.rationaleCard, { borderColor: D.indigo + '33' }]}>
            <Feather name="compass" size={14} color={D.indigo} />
            <Text style={styles.rationaleText}>{strategy.graphRationale}</Text>
          </View>
        )}
        
        {/* Warning */}
        {strategy.warning && (
          <View style={[styles.warningCard, { borderColor: D.amber + '44' }]}>
            <Feather name="alert-triangle" size={14} color={D.amber} />
            <Text style={styles.warningText}>{strategy.warning}</Text>
          </View>
        )}
        
        {/* Projection highlight */}
        {bestProjection && (
          <View style={styles.projectionRow}>
            <View style={styles.projectionItem}>
              <Text style={styles.projectionLabel}>10yr</Text>
              <Text style={styles.projectionValue}>{fmtK(bestProjection.value10yr)}</Text>
            </View>
            <View style={styles.projectionDivider} />
            <View style={styles.projectionItem}>
              <Text style={styles.projectionLabel}>20yr</Text>
              <Text style={styles.projectionValue}>{fmtK(bestProjection.value20yr)}</Text>
            </View>
            <View style={styles.projectionDivider} />
            <View style={styles.projectionItem}>
              <Text style={styles.projectionLabel}>30yr</Text>
              <Text style={[styles.projectionValue, { color: D.green }]}>{fmtK(bestProjection.value30yr)}</Text>
            </View>
          </View>
        )}
        
        {/* Expandable: Example assets */}
        {expanded && strategy.examples?.length > 0 && (
          <View style={styles.examplesSection}>
            <Text style={styles.examplesHeader}>EXAMPLE ASSETS</Text>
            {strategy.examples.map((ex, idx) => (
              <View key={idx} style={styles.exampleRow}>
                <View style={styles.exampleSymbolWrap}>
                  <Text style={styles.exampleSymbol}>{ex.symbol}</Text>
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.exampleName}>{ex.name}</Text>
                  <Text style={styles.exampleDesc}>{ex.description}</Text>
                </View>
              </View>
            ))}
          </View>
        )}
        
        {/* Meta row */}
        <View style={styles.metaRow}>
          <View style={styles.metaChip}>
            <Feather name="activity" size={12} color={D.textMuted} />
            <Text style={styles.metaText}>{strategy.riskLevel} risk</Text>
          </View>
          <View style={styles.metaChip}>
            <Feather name="clock" size={12} color={D.textMuted} />
            <Text style={styles.metaText}>{strategy.timeHorizon} term</Text>
          </View>
          <Pressable
            style={({ pressed }) => [styles.exploreBtn, { opacity: pressed ? 0.8 : 1, backgroundColor: strategy.color }]}
            onPress={onExplore}
          >
            <Text style={styles.exploreBtnText}>Explore</Text>
            <Feather name="arrow-right" size={14} color={D.white} />
          </Pressable>
        </View>
      </Pressable>
    </Animated.View>
  );
}

// ── Main Screen ───────────────────────────────────────────────────────────────

export default function ReallocateScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const insets = useSafeAreaInsets();
  
  const monthlyAmount = route.params?.monthlyAmount ?? 100;
  
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(30)).current;
  
  const { data, loading, error, refetch } = useQuery(GET_REALLOCATION_STRATEGIES, {
    variables: { monthlyAmount },
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });
  
  const result = data?.reallocationStrategies;
  const strategies: Strategy[] = result?.strategies ?? [];
  
  useEffect(() => {
    if (!loading) {
      Animated.parallel([
        Animated.timing(fadeAnim, { toValue: 1, duration: 500, useNativeDriver: true }),
        Animated.timing(slideAnim, { toValue: 0, duration: 500, useNativeDriver: true }),
      ]).start();
    }
  }, [loading, fadeAnim, slideAnim]);
  
  const [refreshing, setRefreshing] = useState(false);
  const onRefresh = async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  };
  
  const handleExplore = (strategyId: string) => {
    const assetClassMap: Record<string, string> = {
      growth_etf: 'real_estate',      // Mixed, default to browsing
      dividend_income: 'real_estate', 
      ai_sector: 'alternatives',
      fixed_income: 'fixed_income',
      real_estate: 'real_estate',
    };
    navigation.navigate('OpportunityDiscovery', {
      initialTab: assetClassMap[strategyId] ?? 'fixed_income',
      source: 'reallocate',
    });
  };
  
  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" />
      
      {/* ── Hero Header ──────────────────────────────────────────────────── */}
      <LinearGradient
        colors={['#0B1426', '#0D2818']}
        style={[styles.hero, { paddingTop: insets.top + 8 }]}
      >
        <View style={styles.heroTop}>
          <Pressable
            onPress={() => navigation.goBack()}
            style={({ pressed }) => [styles.backBtn, { opacity: pressed ? 0.6 : 1 }]}
          >
            <Feather name="chevron-left" size={26} color={D.white} />
          </Pressable>
          <View style={{ flex: 1 }}>
            <Text style={styles.heroEyebrow}>MONEY REALLOCATION</Text>
            <Text style={styles.heroTitle}>Invest Your Savings</Text>
          </View>
          <View style={styles.heroIconBadge}>
            <Feather name="refresh-cw" size={22} color={D.green} />
          </View>
        </View>
        
        {/* Freed amount hero card */}
        <View style={styles.heroCard}>
          <View style={styles.heroCardLeft}>
            <Text style={styles.heroAmountLabel}>You Freed</Text>
            <Text style={styles.heroAmount}>{fmt(monthlyAmount)}<Text style={styles.heroAmountUnit}>/mo</Text></Text>
            <Text style={styles.heroAnnual}>{fmt(monthlyAmount * 12)}/year</Text>
          </View>
          <View style={styles.heroCardDivider} />
          <View style={styles.heroCardRight}>
            <Feather name="trending-up" size={20} color={D.green} />
            <Text style={styles.heroCardLabel}>could become</Text>
            {strategies[0]?.projections?.[2] && (
              <Text style={styles.heroCardValue}>{fmtK(strategies[0].projections[2].value30yr)}</Text>
            )}
            <Text style={styles.heroCardMeta}>in 30 years @ 10%</Text>
          </View>
        </View>
      </LinearGradient>
      
      {/* ── Scrollable Body ─────────────────────────────────────────────── */}
      <Animated.ScrollView
        style={{ flex: 1, opacity: fadeAnim, transform: [{ translateY: slideAnim }] }}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={D.green} />}
      >
        {loading && <LoadingSkeleton />}
        
        {!loading && error && (
          <View style={styles.center}>
            <View style={styles.errorIconWrap}>
              <Feather name="wifi-off" size={26} color={D.red} />
            </View>
            <Text style={styles.emptyTitle}>Could not load strategies</Text>
            <Text style={styles.centerText}>Pull down to retry.</Text>
          </View>
        )}
        
        {!loading && !error && strategies.length > 0 && (
          <>
            {/* Headline */}
            {result?.headlineSentence && (
              <View style={styles.headlineCard}>
                <View style={styles.headlineAccent} />
                <Text style={styles.headlineText}>{result.headlineSentence}</Text>
              </View>
            )}
            
            {/* Portfolio context */}
            {result?.currentPortfolioSummary && (
              <View style={styles.portfolioSummary}>
                <Feather name="pie-chart" size={14} color={D.textMuted} />
                <Text style={styles.portfolioSummaryText}>
                  Current portfolio: {result.currentPortfolioSummary}
                </Text>
              </View>
            )}
            
            {/* AI Portfolio Builder CTA */}
            <Pressable
              style={({ pressed }) => [styles.buildPortfolioCta, { opacity: pressed ? 0.9 : 1 }]}
              onPress={() => navigation.navigate('AIPortfolioBuilder', { monthlyAmount })}
            >
              <View style={styles.buildPortfolioIcon}>
                <Feather name="cpu" size={20} color={D.purple} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.buildPortfolioTitle}>Build My Portfolio</Text>
                <Text style={styles.buildPortfolioSubtitle}>
                  Let AI create a personalized allocation for you
                </Text>
              </View>
              <View style={styles.buildPortfolioBadge}>
                <Text style={styles.buildPortfolioBadgeText}>AI</Text>
              </View>
              <Feather name="chevron-right" size={20} color={D.purple} />
            </Pressable>
            
            {/* Section header */}
            <Text style={styles.sectionHeader}>OR CHOOSE A STRATEGY</Text>
            
            {/* Strategy cards */}
            {strategies.map(s => (
              <StrategyCard key={s.id} strategy={s} onExplore={() => handleExplore(s.id)} />
            ))}
            
            {/* Disclaimer */}
            <View style={styles.disclaimer}>
              <Feather name="info" size={14} color={D.textMuted} />
              <Text style={styles.disclaimerText}>
                These are educational examples, not financial advice. 
                Past performance does not guarantee future results.
              </Text>
            </View>
            
            <View style={{ height: 32 }} />
          </>
        )}
      </Animated.ScrollView>
    </View>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: D.bg },
  
  hero: { paddingHorizontal: 20, paddingBottom: 14 },
  heroTop: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 10 },
  backBtn: {
    width: 36, height: 36, borderRadius: 18,
    backgroundColor: 'rgba(255,255,255,0.1)',
    alignItems: 'center', justifyContent: 'center',
  },
  heroEyebrow: { fontSize: 10, fontWeight: '700', color: 'rgba(255,255,255,0.6)', letterSpacing: 1.6, marginBottom: 3 },
  heroTitle: { fontSize: 24, fontWeight: '800', color: D.white, letterSpacing: -0.5 },
  heroIconBadge: {
    width: 48, height: 48, borderRadius: 24,
    backgroundColor: 'rgba(16,185,129,0.18)', borderWidth: 1, borderColor: 'rgba(16,185,129,0.35)',
    alignItems: 'center', justifyContent: 'center',
  },
  
  heroCard: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.08)', borderRadius: 16,
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.12)',
    padding: 16,
  },
  heroCardLeft: { flex: 1 },
  heroAmountLabel: { fontSize: 11, fontWeight: '600', color: 'rgba(255,255,255,0.5)', letterSpacing: 0.5 },
  heroAmount: { fontSize: 32, fontWeight: '800', color: D.white, letterSpacing: -1 },
  heroAmountUnit: { fontSize: 16, fontWeight: '600', color: 'rgba(255,255,255,0.6)' },
  heroAnnual: { fontSize: 12, color: 'rgba(255,255,255,0.5)', marginTop: 2 },
  heroCardDivider: { width: 1, height: 50, backgroundColor: 'rgba(255,255,255,0.15)', marginHorizontal: 16 },
  heroCardRight: { alignItems: 'center' },
  heroCardLabel: { fontSize: 10, color: 'rgba(255,255,255,0.5)', marginTop: 4 },
  heroCardValue: { fontSize: 22, fontWeight: '800', color: D.green, marginTop: 2 },
  heroCardMeta: { fontSize: 10, color: 'rgba(255,255,255,0.4)', marginTop: 2 },
  
  scrollContent: { paddingHorizontal: 16, paddingTop: 14 },
  
  headlineCard: {
    backgroundColor: D.card, borderRadius: 16, marginBottom: 16, overflow: 'hidden',
    borderWidth: 1, borderColor: D.green + '22',
  },
  headlineAccent: { position: 'absolute', left: 0, top: 0, bottom: 0, width: 4, backgroundColor: D.green },
  headlineText: { padding: 16, paddingLeft: 20, fontSize: 15, fontWeight: '500', color: D.textPrimary, fontStyle: 'italic', lineHeight: 22 },
  
  portfolioSummary: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 16, paddingHorizontal: 4 },
  portfolioSummaryText: { fontSize: 12, color: D.textMuted },
  
  sectionHeader: { fontSize: 10, fontWeight: '700', letterSpacing: 1.2, color: D.textMuted, marginBottom: 12, marginLeft: 2 },
  
  card: {
    backgroundColor: D.card, borderRadius: 20, padding: 18, marginBottom: 14,
    shadowColor: '#0F172A', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.07, shadowRadius: 12, elevation: 3,
  },
  
  strategyHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 14 },
  strategyIconWrap: { width: 48, height: 48, borderRadius: 14, alignItems: 'center', justifyContent: 'center' },
  strategyName: { fontSize: 17, fontWeight: '700', color: D.textPrimary, letterSpacing: -0.2 },
  strategyTagline: { fontSize: 12, color: D.textSecondary, marginTop: 2 },
  
  fitBadge: { paddingHorizontal: 10, paddingVertical: 6, borderRadius: 10, borderWidth: 1, alignItems: 'center' },
  fitBadgeScore: { fontSize: 16, fontWeight: '800' },
  fitBadgeLabel: { fontSize: 9, fontWeight: '600', letterSpacing: 0.3 },
  
  rationaleCard: {
    flexDirection: 'row', alignItems: 'flex-start', gap: 8,
    backgroundColor: D.indigoFaint, borderRadius: 10, padding: 12, marginBottom: 12,
    borderWidth: 1,
  },
  rationaleText: { flex: 1, fontSize: 13, color: D.textPrimary, lineHeight: 18 },
  
  warningCard: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    backgroundColor: D.amberFaint, borderRadius: 10, padding: 10, marginBottom: 12,
    borderWidth: 1,
  },
  warningText: { flex: 1, fontSize: 12, color: D.amber, fontWeight: '600' },
  
  projectionRow: { flexDirection: 'row', alignItems: 'center', backgroundColor: D.bg, borderRadius: 12, padding: 12, marginBottom: 12 },
  projectionItem: { flex: 1, alignItems: 'center' },
  projectionLabel: { fontSize: 10, fontWeight: '600', color: D.textMuted, letterSpacing: 0.5 },
  projectionValue: { fontSize: 18, fontWeight: '800', color: D.textPrimary, marginTop: 2 },
  projectionDivider: { width: 1, height: 30, backgroundColor: D.cardBorder },
  
  examplesSection: { marginBottom: 12 },
  examplesHeader: { fontSize: 9, fontWeight: '700', letterSpacing: 1, color: D.textMuted, marginBottom: 8 },
  exampleRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 10, marginBottom: 10, paddingLeft: 4 },
  exampleSymbolWrap: { backgroundColor: D.bg, borderRadius: 6, paddingHorizontal: 8, paddingVertical: 4 },
  exampleSymbol: { fontSize: 12, fontWeight: '700', color: D.textPrimary },
  exampleName: { fontSize: 13, fontWeight: '600', color: D.textPrimary },
  exampleDesc: { fontSize: 11, color: D.textSecondary, lineHeight: 15, marginTop: 2 },
  
  metaRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  metaChip: { flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: D.bg, borderRadius: 8, paddingHorizontal: 8, paddingVertical: 5 },
  metaText: { fontSize: 11, color: D.textMuted, textTransform: 'capitalize' },
  
  exploreBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    marginLeft: 'auto', borderRadius: 10, paddingHorizontal: 14, paddingVertical: 8,
  },
  exploreBtnText: { fontSize: 13, fontWeight: '700', color: D.white },
  
  center: { alignItems: 'center', paddingVertical: 64, gap: 10, paddingHorizontal: 32 },
  centerText: { fontSize: 14, color: D.textSecondary, textAlign: 'center', lineHeight: 20 },
  emptyTitle: { fontSize: 18, fontWeight: '700', color: D.textPrimary },
  errorIconWrap: { width: 64, height: 64, borderRadius: 32, backgroundColor: D.redFaint, alignItems: 'center', justifyContent: 'center', marginBottom: 4 },
  
  disclaimer: { flexDirection: 'row', alignItems: 'flex-start', gap: 8, paddingHorizontal: 4, marginTop: 8 },
  disclaimerText: { flex: 1, fontSize: 11, color: D.textMuted, lineHeight: 16 },
  
  // Build Portfolio CTA
  buildPortfolioCta: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    backgroundColor: D.card, borderRadius: 16, padding: 16, marginBottom: 20,
    borderWidth: 2, borderColor: D.purple + '33',
    shadowColor: D.purple, shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.15, shadowRadius: 12, elevation: 4,
  },
  buildPortfolioIcon: {
    width: 48, height: 48, borderRadius: 14,
    backgroundColor: D.purpleFaint, alignItems: 'center', justifyContent: 'center',
  },
  buildPortfolioTitle: { fontSize: 16, fontWeight: '800', color: D.textPrimary },
  buildPortfolioSubtitle: { fontSize: 12, color: D.textSecondary, marginTop: 2 },
  buildPortfolioBadge: {
    backgroundColor: D.purple, borderRadius: 6, paddingHorizontal: 8, paddingVertical: 4,
  },
  buildPortfolioBadgeText: { fontSize: 10, fontWeight: '800', color: D.white, letterSpacing: 0.5 },
});
