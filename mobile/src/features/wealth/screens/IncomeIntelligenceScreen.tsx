/**
 * IncomeIntelligenceScreen — 2026 Premium Design
 * ===============================================
 * Classifies your income: salary vs side hustle vs freelance vs investment.
 * Shows income diversity score and breakdown.
 *
 * Sections:
 *  - Dark navy hero with total monthly income
 *  - Income diversity score (0–100) ring
 *  - Income stream cards with progress bars and insights
 *  - Headline sentence card
 */

import React, { useState, useRef, useEffect } from 'react';
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
import { useNavigation } from '@react-navigation/native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useQuery, gql } from '@apollo/client';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

// ── GraphQL Query ─────────────────────────────────────────────────────────────

const GET_INCOME_INTELLIGENCE = gql`
  query GetIncomeIntelligence {
    incomeIntelligence {
      userId
      totalMonthlyIncome
      totalAnnualIncome
      primaryIncomeMonthly
      secondaryIncomeMonthly
      incomeDiversityScore
      streamCount
      lookbackDays
      headlineSentence
      dataQuality
      streams {
        streamType
        label
        monthlyAmount
        annualAmount
        transactionCount
        topSources
        pctOfTotal
        insight
      }
    }
  }
`;

// ── Design Tokens ─────────────────────────────────────────────────────────────

const D = {
  navy:          '#0B1426',
  navyMid:       '#0F1E35',
  blue:          '#3B82F6',
  green:         '#10B981',
  red:           '#EF4444',
  amber:         '#F59E0B',
  indigo:        '#6366F1',
  purple:        '#7C3AED',
  cyan:          '#06B6D4',
  white:         '#FFFFFF',
  textPrimary:   '#0F172A',
  textSecondary: '#64748B',
  textMuted:     '#94A3B8',
  card:          '#FFFFFF',
  bg:            '#F1F5F9',
  greenFaint:    '#D1FAE5',
  blueFaint:     '#EFF6FF',
  indigoFaint:   '#EEF2FF',
  amberFaint:    '#FEF3C7',
  purpleFaint:   '#F3E8FF',
  cyanFaint:     '#CFFAFE',
};

// ── Stream type config ────────────────────────────────────────────────────────

const STREAM_CONFIG: Record<string, { color: string; faint: string; icon: keyof typeof Feather.glyphMap }> = {
  salary:     { color: D.green,  faint: D.greenFaint,  icon: 'briefcase' },
  side_hustle:{ color: D.amber,  faint: D.amberFaint,  icon: 'zap' },
  freelance:  { color: D.purple, faint: D.purpleFaint, icon: 'edit-3' },
  investment: { color: D.blue,   faint: D.blueFaint,   icon: 'trending-up' },
  other:      { color: D.textMuted, faint: D.bg,       icon: 'more-horizontal' },
};

function getStreamConfig(type: string) {
  return STREAM_CONFIG[type] ?? STREAM_CONFIG.other;
}

// ── Formatting ────────────────────────────────────────────────────────────────

const fmt = (n: number) => '$' + Math.abs(n).toLocaleString('en-US', { maximumFractionDigits: 0 });
const fmtK = (n: number) => {
  if (n >= 1000) return '$' + (n / 1000).toFixed(1) + 'K';
  return fmt(n);
};

// ── Skeleton Shimmer ──────────────────────────────────────────────────────────

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
        <View key={i} style={[styles.card, { padding: 18, gap: 12 }]}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
            <SkeletonLine width={40} height={40} style={{ borderRadius: 12 }} />
            <View style={{ flex: 1, gap: 6 }}>
              <SkeletonLine width="60%" height={16} />
              <SkeletonLine width="40%" height={12} />
            </View>
            <SkeletonLine width={60} height={20} />
          </View>
          <SkeletonLine width="100%" height={8} style={{ borderRadius: 4 }} />
        </View>
      ))}
    </View>
  );
}

// ── Diversity Score Ring ──────────────────────────────────────────────────────

function DiversityRing({ score }: { score: number }) {
  const size = 100;
  const strokeWidth = 8;
  const pct = Math.min(score / 100, 1);

  const color = score >= 70 ? D.green : score >= 40 ? D.amber : D.red;

  return (
    <View style={styles.diversityRingContainer}>
      <View style={[styles.diversityRingBg, { width: size, height: size, borderRadius: size / 2, borderWidth: strokeWidth }]} />
      <View
        style={[
          styles.diversityRingProgress,
          {
            width: size, height: size, borderRadius: size / 2, borderWidth: strokeWidth,
            borderColor: color,
            borderTopColor: pct > 0.25 ? color : 'transparent',
            borderRightColor: pct > 0.5 ? color : 'transparent',
            borderBottomColor: pct > 0.75 ? color : 'transparent',
            borderLeftColor: pct > 0 ? color : 'transparent',
            transform: [{ rotate: '-90deg' }],
          },
        ]}
      />
      <View style={styles.diversityRingCenter}>
        <Text style={styles.diversityScore}>{Math.round(score)}</Text>
        <Text style={styles.diversityLabel}>Diversity</Text>
      </View>
    </View>
  );
}

// ── Stream Card ───────────────────────────────────────────────────────────────

interface IncomeStream {
  streamType: string;
  label: string;
  monthlyAmount: number;
  annualAmount: number;
  transactionCount: number;
  topSources: string[];
  pctOfTotal: number;
  insight: string;
}

function StreamCard({ stream }: { stream: IncomeStream }) {
  const config = getStreamConfig(stream.streamType);
  const scaleAnim = useRef(new Animated.Value(1)).current;

  const onPressIn = () => Animated.spring(scaleAnim, { toValue: 0.98, useNativeDriver: true, speed: 50 }).start();
  const onPressOut = () => Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true, speed: 50 }).start();

  const pct = Math.min((stream.pctOfTotal ?? 0) / 100, 1);

  return (
    <Animated.View style={{ transform: [{ scale: scaleAnim }] }}>
      <Pressable onPressIn={onPressIn} onPressOut={onPressOut} style={styles.card}>
        {/* Header */}
        <View style={styles.streamHeader}>
          <View style={[styles.streamIconWrap, { backgroundColor: config.faint }]}>
            <Feather name={config.icon} size={18} color={config.color} />
          </View>
          <View style={{ flex: 1, marginLeft: 12 }}>
            <Text style={styles.streamLabel}>{stream.label}</Text>
            <Text style={styles.streamSources} numberOfLines={1}>
              {stream.topSources?.slice(0, 2).join(', ') || '—'}
            </Text>
          </View>
          <View style={{ alignItems: 'flex-end' }}>
            <Text style={[styles.streamAmount, { color: config.color }]}>{fmtK(stream.monthlyAmount)}/mo</Text>
            <Text style={styles.streamPct}>{Math.round(stream.pctOfTotal ?? 0)}%</Text>
          </View>
        </View>

        {/* Progress bar */}
        <View style={styles.progressTrack}>
          <View style={[styles.progressFill, { width: `${pct * 100}%`, backgroundColor: config.color }]} />
        </View>

        {/* Insight */}
        {stream.insight && <Text style={styles.streamInsight}>{stream.insight}</Text>}

        {/* Transaction count */}
        <View style={styles.txCountRow}>
          <Feather name="activity" size={12} color={D.textMuted} />
          <Text style={styles.txCountText}>{stream.transactionCount} deposits (90d)</Text>
        </View>
      </Pressable>
    </Animated.View>
  );
}

// ── Main Screen ───────────────────────────────────────────────────────────────

export default function IncomeIntelligenceScreen() {
  const navigation = useNavigation<any>();
  const insets = useSafeAreaInsets();
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(30)).current;

  const { data, loading, error, refetch } = useQuery(GET_INCOME_INTELLIGENCE, {
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });

  const intel = data?.incomeIntelligence;
  const hasData = !loading && intel;

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

  const totalMonthly = intel?.totalMonthlyIncome ?? 0;
  const totalAnnual = intel?.totalAnnualIncome ?? 0;
  const diversityScore = intel?.incomeDiversityScore ?? 0;
  const streams: IncomeStream[] = intel?.streams ?? [];
  const headline = intel?.headlineSentence;

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" />

      {/* ── Hero Header ──────────────────────────────────────────────────── */}
      <LinearGradient
        colors={['#0B1426', '#0F2027']}
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
            <Text style={styles.heroEyebrow}>FINANCIAL GPS</Text>
            <Text style={styles.heroTitle}>Income Intelligence</Text>
          </View>
          <View style={styles.heroIconBadge}>
            <Feather name="dollar-sign" size={22} color={D.green} />
          </View>
        </View>

        {/* Stats row */}
        {hasData && (
          <View style={styles.heroStats}>
            <View style={styles.heroStat}>
              <Text style={styles.heroStatAmount}>{fmtK(totalMonthly)}</Text>
              <Text style={styles.heroStatLabel}>Monthly</Text>
            </View>
            <DiversityRing score={diversityScore} />
            <View style={styles.heroStat}>
              <Text style={styles.heroStatAmount}>{fmtK(totalAnnual)}</Text>
              <Text style={styles.heroStatLabel}>Annual</Text>
            </View>
          </View>
        )}

        {loading && (
          <View style={styles.heroStats}>
            <SkeletonLine width={80} height={32} />
            <SkeletonLine width={100} height={100} style={{ borderRadius: 50 }} />
            <SkeletonLine width={80} height={32} />
          </View>
        )}
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
            <Text style={styles.emptyTitle}>Could not load</Text>
            <Text style={styles.centerText}>Pull down to retry.</Text>
          </View>
        )}

        {!loading && !error && intel?.dataQuality === 'insufficient' && (
          <View style={styles.center}>
            <View style={styles.emptyIconWrap}>
              <Feather name="database" size={28} color={D.amber} />
            </View>
            <Text style={styles.emptyTitle}>Not enough data</Text>
            <Text style={styles.centerText}>
              Connect your bank accounts so we can classify your income streams.
            </Text>
          </View>
        )}

        {hasData && intel?.dataQuality !== 'insufficient' && (
          <>
            {/* Headline */}
            {headline && (
              <View style={styles.headlineCard}>
                <View style={styles.headlineAccent} />
                <Text style={styles.headlineText}>{headline}</Text>
              </View>
            )}

            {/* Section header */}
            <Text style={styles.sectionHeader}>YOUR INCOME STREAMS</Text>

            {/* Stream cards */}
            {streams.map((s, idx) => (
              <StreamCard key={s.streamType || idx} stream={s} />
            ))}

            {streams.length === 0 && (
              <View style={styles.center}>
                <Text style={styles.centerText}>No income streams detected in the last 90 days.</Text>
              </View>
            )}

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

  heroStats: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-around' },
  heroStat: { alignItems: 'center' },
  heroStatAmount: { fontSize: 24, fontWeight: '800', color: D.white, letterSpacing: -0.5 },
  heroStatLabel: { fontSize: 12, fontWeight: '600', color: 'rgba(255,255,255,0.6)', marginTop: 4 },

  diversityRingContainer: { width: 100, height: 100, justifyContent: 'center', alignItems: 'center' },
  diversityRingBg: { position: 'absolute', borderColor: 'rgba(255,255,255,0.1)' },
  diversityRingProgress: { position: 'absolute' },
  diversityRingCenter: { alignItems: 'center' },
  diversityScore: { fontSize: 28, fontWeight: '800', color: D.white },
  diversityLabel: { fontSize: 10, fontWeight: '600', color: 'rgba(255,255,255,0.5)', letterSpacing: 0.5 },

  scrollContent: { paddingHorizontal: 16, paddingTop: 14 },

  headlineCard: {
    backgroundColor: D.card, borderRadius: 16, marginBottom: 20, overflow: 'hidden',
    borderWidth: 1, borderColor: D.green + '22',
  },
  headlineAccent: { position: 'absolute', left: 0, top: 0, bottom: 0, width: 4, backgroundColor: D.green },
  headlineText: { padding: 16, paddingLeft: 20, fontSize: 15, fontWeight: '500', color: D.textPrimary, fontStyle: 'italic', lineHeight: 22 },

  sectionHeader: { fontSize: 10, fontWeight: '700', letterSpacing: 1.2, color: D.textMuted, marginBottom: 12, marginLeft: 2 },

  card: {
    backgroundColor: D.card, borderRadius: 20, padding: 18, marginBottom: 14,
    shadowColor: '#0F172A', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.07, shadowRadius: 12, elevation: 3,
  },

  streamHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 14 },
  streamIconWrap: { width: 40, height: 40, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  streamLabel: { fontSize: 16, fontWeight: '700', color: D.textPrimary, letterSpacing: -0.2 },
  streamSources: { fontSize: 12, color: D.textMuted, marginTop: 2 },
  streamAmount: { fontSize: 17, fontWeight: '800', letterSpacing: -0.3 },
  streamPct: { fontSize: 11, color: D.textMuted, marginTop: 2 },

  progressTrack: { height: 8, backgroundColor: D.bg, borderRadius: 4, overflow: 'hidden', marginBottom: 12 },
  progressFill: { height: '100%', borderRadius: 4 },

  streamInsight: { fontSize: 13, color: D.textSecondary, lineHeight: 18, marginBottom: 10 },

  txCountRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  txCountText: { fontSize: 11, color: D.textMuted },

  center: { alignItems: 'center', paddingVertical: 64, gap: 10, paddingHorizontal: 32 },
  centerText: { fontSize: 14, color: D.textSecondary, textAlign: 'center', lineHeight: 20 },
  emptyIconWrap: { width: 64, height: 64, borderRadius: 32, backgroundColor: D.amberFaint, alignItems: 'center', justifyContent: 'center', marginBottom: 4 },
  emptyTitle: { fontSize: 18, fontWeight: '700', color: D.textPrimary },
  errorIconWrap: { width: 64, height: 64, borderRadius: 32, backgroundColor: '#FEE2E2', alignItems: 'center', justifyContent: 'center', marginBottom: 4 },
});
