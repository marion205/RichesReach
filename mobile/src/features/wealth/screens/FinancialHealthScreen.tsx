/**
 * FinancialHealthScreen — 2026 Premium Design
 * =============================================
 * Gamified financial health score with 4 pillars.
 * Think "credit score meets Duolingo" — a single number users
 * can obsess over and improve.
 *
 * Sections:
 *  - Dark navy hero with animated score circle + letter grade
 *  - Headline sentence card (indigo tint)
 *  - 4 pillar cards: Savings Rate, Emergency Fund, Debt Ratio, Credit Utilization
 *  - Each pillar: progress bar, grade badge, insight, action CTA
 *  - Pull-to-refresh, loading skeleton, insufficient-data state
 */

import React, { useState, useEffect, useRef } from 'react';
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

const GET_FINANCIAL_HEALTH = gql`
  query GetFinancialHealth {
    financialHealth {
      userId
      score
      grade
      headlineSentence
      dataQuality
      savingsRatePct
      monthlyIncome
      monthlyDebtService
      debtToIncomePct
      emergencyFundMonths
      creditUtilizationPct
      pillars {
        name
        label
        score
        grade
        value
        unit
        insight
        action
        weight
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
  blueLight:     '#60A5FA',
  green:         '#10B981',
  greenDark:     '#059669',
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
  redFaint:      '#FEE2E2',
};

// ── Grade colors ──────────────────────────────────────────────────────────────

function gradeColor(grade: string): string {
  switch (grade) {
    case 'A': return D.green;
    case 'B': return D.blue;
    case 'C': return D.amber;
    case 'D': return '#F97316';
    case 'F': return D.red;
    default:  return D.textMuted;
  }
}

function gradeFaint(grade: string): string {
  switch (grade) {
    case 'A': return D.greenFaint;
    case 'B': return D.blueFaint;
    case 'C': return D.amberFaint;
    case 'D': return '#FFEDD5';
    case 'F': return D.redFaint;
    default:  return D.bg;
  }
}

// ── Pillar icons ──────────────────────────────────────────────────────────────

function pillarIcon(name: string): keyof typeof Feather.glyphMap {
  switch (name) {
    case 'savings_rate':       return 'trending-up';
    case 'emergency_fund':     return 'shield';
    case 'debt_ratio':         return 'credit-card';
    case 'credit_utilization': return 'percent';
    default:                   return 'activity';
  }
}

// ── Formatting ────────────────────────────────────────────────────────────────

const fmt = (n: number) => n.toLocaleString('en-US', { maximumFractionDigits: 0 });
const fmtPct = (n: number) => `${n.toFixed(1)}%`;
const fmtMonths = (n: number) => `${n.toFixed(1)} mo`;

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

  return (
    <Animated.View
      style={[
        { width, height, borderRadius: 6, backgroundColor: D.textMuted, opacity },
        style,
      ]}
    />
  );
}

function LoadingSkeleton() {
  return (
    <View style={{ paddingHorizontal: 16, paddingTop: 24 }}>
      {[1, 2, 3, 4].map(i => (
        <View key={i} style={[styles.card, { padding: 18, gap: 12 }]}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
            <SkeletonLine width="50%" height={18} />
            <SkeletonLine width={36} height={24} />
          </View>
          <SkeletonLine width="100%" height={8} style={{ borderRadius: 4 }} />
          <SkeletonLine width="80%" height={12} />
        </View>
      ))}
    </View>
  );
}

// ── Score Ring Component ──────────────────────────────────────────────────────

interface ScoreRingProps {
  score: number;
  grade: string;
}

function ScoreRing({ score, grade }: ScoreRingProps) {
  const size = 180;
  const strokeWidth = 12;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.min(score / 100, 1);
  const strokeDashoffset = circumference * (1 - progress);

  const animatedValue = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(animatedValue, {
      toValue: score,
      duration: 1200,
      useNativeDriver: false,
    }).start();
  }, [score, animatedValue]);

  const gColor = gradeColor(grade);

  return (
    <View style={styles.scoreRingContainer}>
      {/* Background circle */}
      <View
        style={[
          styles.scoreRingBg,
          { width: size, height: size, borderRadius: size / 2, borderWidth: strokeWidth },
        ]}
      />
      {/* Progress arc (simulated with border) */}
      <View
        style={[
          styles.scoreRingProgress,
          {
            width: size,
            height: size,
            borderRadius: size / 2,
            borderWidth: strokeWidth,
            borderColor: gColor,
            borderTopColor: progress > 0.25 ? gColor : 'transparent',
            borderRightColor: progress > 0.5 ? gColor : 'transparent',
            borderBottomColor: progress > 0.75 ? gColor : 'transparent',
            borderLeftColor: progress > 0 ? gColor : 'transparent',
            transform: [{ rotate: '-90deg' }],
          },
        ]}
      />
      {/* Center content */}
      <View style={styles.scoreRingCenter}>
        <Text style={styles.scoreNumber}>{Math.round(score)}</Text>
        <View style={[styles.gradeBadgeLarge, { backgroundColor: gColor }]}>  
          <Text style={styles.gradeBadgeLargeText}>{grade}</Text>
        </View>
      </View>
    </View>
  );
}

// ── Pillar Card Component ─────────────────────────────────────────────────────

interface Pillar {
  name: string;
  label: string;
  score: number;
  grade: string;
  value: number | null;
  unit: string;
  insight: string;
  action: string;
  weight: number;
}

function PillarCard({ pillar }: { pillar: Pillar }) {
  const scaleAnim = useRef(new Animated.Value(1)).current;

  const onPressIn = () =>
    Animated.spring(scaleAnim, { toValue: 0.98, useNativeDriver: true, speed: 50 }).start();
  const onPressOut = () =>
    Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true, speed: 50 }).start();

  const gColor = gradeColor(pillar.grade);
  const gFaint = gradeFaint(pillar.grade);
  const icon = pillarIcon(pillar.name);
  const pct = Math.min(pillar.score / 100, 1);

  let valueDisplay = '—';
  if (pillar.value !== null) {
    if (pillar.unit === '%') {
      valueDisplay = fmtPct(pillar.value);
    } else if (pillar.unit === 'months') {
      valueDisplay = fmtMonths(pillar.value);
    } else {
      valueDisplay = `${pillar.value.toFixed(1)} ${pillar.unit}`;
    }
  }

  return (
    <Animated.View style={{ transform: [{ scale: scaleAnim }] }}>
      <Pressable
        onPressIn={onPressIn}
        onPressOut={onPressOut}
        style={styles.card}
        accessibilityRole="button"
        accessibilityLabel={`${pillar.label}: ${pillar.grade}`}
      >
        {/* Header row */}
        <View style={styles.pillarHeader}>
          <View style={[styles.pillarIconWrap, { backgroundColor: gFaint }]}>
            <Feather name={icon} size={18} color={gColor} />
          </View>
          <View style={{ flex: 1, marginLeft: 12 }}>
            <Text style={styles.pillarLabel}>{pillar.label}</Text>
            <Text style={styles.pillarValue}>{valueDisplay}</Text>
          </View>
          <View style={[styles.gradeBadgeSmall, { backgroundColor: gColor }]}>
            <Text style={styles.gradeBadgeSmallText}>{pillar.grade}</Text>
          </View>
        </View>

        {/* Progress bar */}
        <View style={styles.progressTrack}>
          <View style={[styles.progressFill, { width: `${pct * 100}%`, backgroundColor: gColor }]} />
        </View>

        {/* Insight */}
        <Text style={styles.pillarInsight}>{pillar.insight}</Text>

        {/* Action CTA */}
        <View style={[styles.actionBadge, { backgroundColor: gFaint, borderColor: `${gColor}33` }]}>
          <Feather name="zap" size={12} color={gColor} />
          <Text style={[styles.actionText, { color: gColor }]}>{pillar.action}</Text>
        </View>

        {/* Weight indicator */}
        <Text style={styles.weightText}>{Math.round(pillar.weight * 100)}% of score</Text>
      </Pressable>
    </Animated.View>
  );
}

// ── Main Screen ───────────────────────────────────────────────────────────────

export default function FinancialHealthScreen() {
  const navigation = useNavigation<any>();
  const insets = useSafeAreaInsets();
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(30)).current;

  const { data, loading, error, refetch } = useQuery(GET_FINANCIAL_HEALTH, {
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });

  const health = data?.financialHealth;
  const hasData = !loading && health && health.score != null;

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

  const score = health?.score ?? 0;
  const grade = health?.grade ?? '—';
  const headline = health?.headlineSentence;
  const pillars: Pillar[] = health?.pillars ?? [];

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" />

      {/* ── Hero Header ──────────────────────────────────────────────────── */}
      <LinearGradient
        colors={['#0B1426', '#1A0F2E']}
        style={[styles.hero, { paddingTop: insets.top + 8 }]}
      >
        {/* Top row: back + title */}
        <View style={styles.heroTop}>
          <Pressable
            onPress={() => navigation.goBack()}
            style={({ pressed }) => [styles.backBtn, { opacity: pressed ? 0.6 : 1 }]}
            accessibilityLabel="Go back"
          >
            <Feather name="chevron-left" size={26} color={D.white} />
          </Pressable>

          <View style={{ flex: 1 }}>
            <Text style={styles.heroEyebrow}>FINANCIAL GPS</Text>
            <Text style={styles.heroTitle}>Health Score</Text>
          </View>

          <View style={styles.heroIconBadge}>
            <Feather name="heart" size={22} color={D.green} />
          </View>
        </View>

        {/* Score ring */}
        {hasData && <ScoreRing score={score} grade={grade} />}

        {loading && (
          <View style={styles.loadingRing}>
            <SkeletonLine width={180} height={180} style={{ borderRadius: 90 }} />
          </View>
        )}
      </LinearGradient>

      {/* ── Scrollable Body ─────────────────────────────────────────────── */}
      <Animated.ScrollView
        style={{ flex: 1, opacity: fadeAnim, transform: [{ translateY: slideAnim }] }}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={D.indigo} />
        }
      >
        {/* Loading skeleton */}
        {loading && <LoadingSkeleton />}

        {/* Error state */}
        {!loading && error && (
          <View style={styles.center}>
            <View style={styles.errorIconWrap}>
              <Feather name="wifi-off" size={26} color={D.red} />
            </View>
            <Text style={styles.emptyTitle}>Could not load</Text>
            <Text style={styles.centerText}>Pull down to retry.</Text>
          </View>
        )}

        {/* Insufficient data */}
        {!loading && !error && health?.dataQuality === 'insufficient' && (
          <View style={styles.center}>
            <View style={styles.emptyIconWrap}>
              <Feather name="database" size={28} color={D.amber} />
            </View>
            <Text style={styles.emptyTitle}>Not enough data</Text>
            <Text style={styles.centerText}>
              Connect your bank accounts so we can calculate your financial health score.
            </Text>
          </View>
        )}

        {/* Main content */}
        {hasData && health?.dataQuality !== 'insufficient' && (
          <>
            {/* Headline sentence */}
            {headline && (
              <View style={styles.headlineCard}>
                <View style={styles.headlineAccent} />
                <View style={styles.headlineInner}>
                  <Feather name="message-circle" size={16} color={D.indigo} style={{ marginRight: 10 }} />
                  <Text style={styles.headlineText}>{headline}</Text>
                </View>
              </View>
            )}

            {/* Section label */}
            <Text style={styles.sectionHeader}>YOUR 4 PILLARS</Text>

            {/* Pillar cards */}
            {pillars.map((p, idx) => (
              <PillarCard key={p.name || idx} pillar={p} />
            ))}

            {/* Bottom spacer */}
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

  // ── Hero ──────────────────────────────────────────────────────────────────
  hero: {
    paddingHorizontal: 20,
    paddingBottom: 16,
    alignItems: 'center',
  },
  heroTop: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    width: '100%',
    marginBottom: 10,
  },
  backBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255,255,255,0.1)',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  heroEyebrow: {
    fontSize: 10,
    fontWeight: '700',
    color: 'rgba(255,255,255,0.6)',
    letterSpacing: 1.6,
    marginBottom: 3,
  },
  heroTitle: {
    fontSize: 24,
    fontWeight: '800',
    color: D.white,
    letterSpacing: -0.5,
  },
  heroIconBadge: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(16,185,129,0.18)',
    borderWidth: 1,
    borderColor: 'rgba(16,185,129,0.35)',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },

  // ── Score Ring ────────────────────────────────────────────────────────────
  scoreRingContainer: {
    width: 180,
    height: 180,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scoreRingBg: {
    position: 'absolute',
    borderColor: 'rgba(255,255,255,0.1)',
  },
  scoreRingProgress: {
    position: 'absolute',
  },
  scoreRingCenter: {
    alignItems: 'center',
    gap: 8,
  },
  scoreNumber: {
    fontSize: 56,
    fontWeight: '800',
    color: D.white,
    letterSpacing: -2,
  },
  gradeBadgeLarge: {
    paddingHorizontal: 14,
    paddingVertical: 4,
    borderRadius: 99,
  },
  gradeBadgeLargeText: {
    fontSize: 16,
    fontWeight: '800',
    color: D.white,
    letterSpacing: 1,
  },
  loadingRing: {
    marginTop: 20,
  },

  // ── Scroll Body ───────────────────────────────────────────────────────────
  scrollContent: {
    paddingHorizontal: 16,
    paddingTop: 14,
  },

  // ── Headline Card ─────────────────────────────────────────────────────────
  headlineCard: {
    backgroundColor: D.card,
    borderRadius: 16,
    marginBottom: 20,
    shadowColor: D.indigo,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 12,
    elevation: 3,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: `${D.indigo}22`,
  },
  headlineAccent: {
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    width: 4,
    backgroundColor: D.indigo,
  },
  headlineInner: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    padding: 16,
    paddingLeft: 20,
  },
  headlineText: {
    flex: 1,
    fontSize: 15,
    fontWeight: '500',
    color: D.textPrimary,
    lineHeight: 22,
    fontStyle: 'italic',
  },

  // ── Section Header ────────────────────────────────────────────────────────
  sectionHeader: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.2,
    color: D.textMuted,
    marginBottom: 12,
    marginLeft: 2,
  },

  // ── Card ──────────────────────────────────────────────────────────────────
  card: {
    backgroundColor: D.card,
    borderRadius: 20,
    marginBottom: 14,
    padding: 18,
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07,
    shadowRadius: 12,
    elevation: 3,
  },

  // ── Pillar Card ───────────────────────────────────────────────────────────
  pillarHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 14,
  },
  pillarIconWrap: {
    width: 40,
    height: 40,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  pillarLabel: {
    fontSize: 16,
    fontWeight: '700',
    color: D.textPrimary,
    letterSpacing: -0.2,
  },
  pillarValue: {
    fontSize: 13,
    fontWeight: '600',
    color: D.textSecondary,
    marginTop: 2,
  },
  gradeBadgeSmall: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 99,
  },
  gradeBadgeSmallText: {
    fontSize: 13,
    fontWeight: '800',
    color: D.white,
    letterSpacing: 0.5,
  },

  // Progress bar
  progressTrack: {
    height: 8,
    backgroundColor: D.bg,
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 14,
  },
  progressFill: {
    height: '100%',
    borderRadius: 4,
  },

  // Insight
  pillarInsight: {
    fontSize: 14,
    fontWeight: '400',
    color: D.textSecondary,
    lineHeight: 20,
    marginBottom: 12,
  },

  // Action badge
  actionBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 99,
    borderWidth: 1,
    marginBottom: 8,
  },
  actionText: {
    fontSize: 12,
    fontWeight: '600',
  },

  // Weight
  weightText: {
    fontSize: 11,
    color: D.textMuted,
    fontWeight: '500',
  },

  // ── Center / empty / error states ─────────────────────────────────────────
  center: {
    alignItems: 'center',
    paddingVertical: 64,
    gap: 10,
    paddingHorizontal: 32,
  },
  centerText: {
    fontSize: 14,
    color: D.textSecondary,
    textAlign: 'center',
    lineHeight: 20,
  },
  emptyIconWrap: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: D.amberFaint,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: D.textPrimary,
  },
  errorIconWrap: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: D.redFaint,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
});
