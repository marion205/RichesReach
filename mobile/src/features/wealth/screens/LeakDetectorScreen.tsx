/**
 * LeakDetectorScreen — 2026 Premium Redesign
 * ===========================================
 * Subscription scanner & money leak detector.
 * Surfaces recurring charges, ranks by cost, and projects
 * the 5-year opportunity cost of each wasted dollar.
 *
 * Design language:
 *  - Navy-to-dark-red hero gradient (thriller/detective aesthetic)
 *  - Frosted glass summary hero card inside the header
 *  - Category-coloured chips, confidence bars, cost highlights
 *  - "What if you cancelled?" projection card (7% FV)
 *  - Pull-to-refresh, loading skeleton, press-scale animation
 */

import React, { useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  RefreshControl,
  Animated,
  StatusBar,
  ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Feather from '@expo/vector-icons/Feather';
import { useNavigation } from '@react-navigation/native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useQuery } from '@apollo/client';

import { GET_FINANCIAL_LEAKS } from '../../../graphql/financialGps';

// ── Design tokens ─────────────────────────────────────────────────────────────

const D = {
  navy: '#0B1426',
  navyMid: '#0F1E35',
  navyLight: '#162642',
  blue: '#3B82F6',
  green: '#10B981',
  red: '#EF4444',
  orange: '#F97316',
  amber: '#F59E0B',
  indigo: '#6366F1',
  white: '#FFFFFF',
  textPrimary: '#0F172A',
  textSecondary: '#64748B',
  textMuted: '#94A3B8',
  card: '#FFFFFF',
  cardBorder: '#E2E8F0',
  bg: '#F1F5F9',
  // Faint tints
  redFaint: '#FEE2E2',
  amberFaint: '#FEF3C7',
  greenFaint: '#D1FAE5',
  indigoFaint: '#EEF2FF',
  // Spacing radii
  r4: 4, r8: 8, r12: 12, r16: 16, r20: 20,
};

// ── Category colour map ───────────────────────────────────────────────────────

const CATEGORY_COLOR: Record<string, string> = {
  Streaming:       '#EF4444',
  Music:           '#EC4899',
  'Software/Tools': '#3B82F6',
  Software:        '#3B82F6',
  Tools:           '#3B82F6',
  'Cloud Storage': '#6366F1',
  Cloud:           '#6366F1',
  'Health/Fitness': '#10B981',
  Health:          '#10B981',
  Fitness:         '#10B981',
  Gaming:          '#7C3AED',
  'Shopping/Prime': '#F59E0B',
  Shopping:        '#F59E0B',
  Prime:           '#F59E0B',
  'News/Media':    '#64748B',
  News:            '#64748B',
  Media:           '#64748B',
  Dating:          '#F97316',
};

function categoryColor(cat?: string | null): string {
  if (!cat) return '#94A3B8';
  return CATEGORY_COLOR[cat] ?? '#94A3B8';
}

// ── Formatting helpers ────────────────────────────────────────────────────────

const fmt = (n: number) =>
  '$' + Math.abs(n).toLocaleString('en-US', { maximumFractionDigits: 0 });

const fmtMonthly = (n: number) => fmt(n) + '/mo';

/** Future Value of a monthly PMT over 60 months at 7% annual (r = 7/12 %). */
function fv60(monthlyPmt: number): number {
  const r = 0.07 / 12;
  return monthlyPmt * ((Math.pow(1 + r, 60) - 1) / r);
}

// ── Skeleton shimmer ──────────────────────────────────────────────────────────

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
    <View style={{ paddingHorizontal: 16, paddingTop: 20 }}>
      {[1, 2, 3].map(i => (
        <View key={i} style={[styles.card, { padding: 18, gap: 10 }]}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
            <SkeletonLine width="55%" height={16} />
            <SkeletonLine width={52} height={20} />
          </View>
          <SkeletonLine width="30%" height={12} />
          <SkeletonLine width="100%" height={6} style={{ borderRadius: 3 }} />
          <SkeletonLine width="20%" height={11} />
        </View>
      ))}
    </View>
  );
}

// ── Subscription card ─────────────────────────────────────────────────────────

interface Subscription {
  merchantName?: string | null;
  normalizedName?: string | null;
  cadence?: string | null;
  confidence?: number | null;
  monthlyEquivalent?: number | null;
  annualEquivalent?: number | null;
  category?: string | null;
  easyToForget?: boolean | null;
  occurrenceCount?: number | null;
  lastSeen?: string | null;
  amountVariance?: number | null;
}

interface SubCardProps {
  sub: Subscription;
  isTopLeak?: boolean;
}

function SubscriptionCard({ sub, isTopLeak = false }: SubCardProps) {
  const scaleAnim = useRef(new Animated.Value(1)).current;

  const onPressIn  = () =>
    Animated.spring(scaleAnim, { toValue: 0.975, useNativeDriver: true, speed: 50 }).start();
  const onPressOut = () =>
    Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true, speed: 50 }).start();

  const name       = sub.normalizedName ?? sub.merchantName ?? 'Unknown';
  const monthly    = sub.monthlyEquivalent ?? 0;
  const conf       = sub.confidence ?? 0;
  const cat        = sub.category ?? 'Other';
  const catColor   = categoryColor(cat);
  const cadence    = sub.cadence ?? '';

  const costColor  = monthly > 50 ? D.red : monthly > 20 ? D.amber : D.textPrimary;
  const confColor  = conf > 0.8 ? D.green : conf > 0.5 ? D.amber : D.red;
  const confPct    = Math.round(conf * 100);

  return (
    <Animated.View style={{ transform: [{ scale: scaleAnim }] }}>
      <Pressable
        onPressIn={onPressIn}
        onPressOut={onPressOut}
        style={[
          styles.card,
          isTopLeak && styles.topLeakCard,
        ]}
        accessibilityRole="button"
        accessibilityLabel={`${name}, ${fmtMonthly(monthly)}`}
      >
        {/* Left accent bar for top leak */}
        {isTopLeak && <View style={styles.topLeakAccent} />}

        <View style={[styles.cardInner, isTopLeak && { paddingLeft: 20 }]}>
          {/* Header row */}
          <View style={styles.subHeader}>
            <View style={{ flex: 1, gap: 4 }}>
              {isTopLeak && (
                <View style={styles.topLeakPill}>
                  <Text style={styles.topLeakPillText}>TOP LEAK</Text>
                </View>
              )}
              <Text
                style={[styles.subName, isTopLeak && { fontSize: 20, fontWeight: '700' }]}
                numberOfLines={1}
              >
                {name}
              </Text>
              <View style={{ flexDirection: 'row', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
                {/* Category chip */}
                <View style={[styles.catChip, { backgroundColor: `${catColor}18` }]}>
                  <View style={[styles.catDot, { backgroundColor: catColor }]} />
                  <Text style={[styles.catChipText, { color: catColor }]}>{cat}</Text>
                </View>
                {/* Cadence badge */}
                {cadence ? (
                  <View style={styles.cadenceBadge}>
                    <Feather name="repeat" size={9} color={D.textMuted} />
                    <Text style={styles.cadenceText}>{cadence}</Text>
                  </View>
                ) : null}
                {/* Easy-to-forget badge */}
                {sub.easyToForget && (
                  <View style={styles.forgetBadge}>
                    <Text style={styles.forgetBadgeText}>😴 Easy to forget</Text>
                  </View>
                )}
              </View>
            </View>

            {/* Monthly cost */}
            <Text style={[styles.subCost, { color: costColor }]}>
              {fmtMonthly(monthly)}
            </Text>
          </View>

          {/* Confidence bar */}
          <View style={{ marginTop: 12, gap: 4 }}>
            <View style={styles.confBarTrack}>
              <View
                style={[
                  styles.confBarFill,
                  { width: `${confPct}%` as any, backgroundColor: confColor },
                ]}
              />
            </View>
            <Text style={styles.confLabel}>{confPct}% match confidence</Text>
          </View>
        </View>
      </Pressable>
    </Animated.View>
  );
}

// ── Main screen ───────────────────────────────────────────────────────────────

export default function LeakDetectorScreen() {
  const navigation  = useNavigation<any>();
  const insets      = useSafeAreaInsets();
  const fadeAnim    = useRef(new Animated.Value(0)).current;
  const slideAnim   = useRef(new Animated.Value(30)).current;

  const { data, loading, error, refetch } = useQuery(GET_FINANCIAL_LEAKS, {
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });

  const leaks = data?.financialLeaks;
  const subs: Subscription[] = [...(leaks?.detectedSubscriptions ?? [])].sort(
    (a, b) => (b.monthlyEquivalent ?? 0) - (a.monthlyEquivalent ?? 0)
  );
  const hasData = !loading && subs.length > 0;

  // Entrance animation once data arrives
  useEffect(() => {
    if (!loading) {
      Animated.parallel([
        Animated.timing(fadeAnim, { toValue: 1, duration: 500, useNativeDriver: true }),
        Animated.timing(slideAnim, { toValue: 0, duration: 500, useNativeDriver: true }),
      ]).start();
    }
  }, [loading, fadeAnim, slideAnim]);

  const [refreshing, setRefreshing] = React.useState(false);
  const onRefresh = async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  };

  const totalMonthly = leaks?.totalMonthlyLeak ?? 0;
  const totalAnnual  = leaks?.totalAnnualLeak  ?? 0;
  const impact5yr    = leaks?.savingsImpact5yr ?? 0;
  const subCount     = subs.length;
  const topLeak      = leaks?.topLeak;

  // "What if you cancelled top N?" — use top 3 (or all if fewer)
  const cancelCount  = Math.min(3, subs.length);
  const cancelTotal  = subs.slice(0, cancelCount).reduce((acc, s) => acc + (s.monthlyEquivalent ?? 0), 0);
  const cancelFV     = fv60(cancelTotal);

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" />

      {/* ── Hero Header ──────────────────────────────────────────────────── */}
      <LinearGradient
        colors={['#0B1426', '#1F0A0A']}
        style={[styles.hero, { paddingTop: insets.top + 8 }]}
      >
        {/* Top row: back + title + icon badge */}
        <View style={styles.heroTop}>
          <Pressable
            onPress={() => navigation.goBack()}
            style={({ pressed }) => [styles.backBtn, { opacity: pressed ? 0.6 : 1 }]}
            accessibilityLabel="Go back"
          >
            <Feather name="chevron-left" size={26} color={D.white} />
          </Pressable>

          <View style={{ flex: 1 }}>
            <Text style={styles.heroEyebrow}>SUBSCRIPTION SCANNER</Text>
            <Text style={styles.heroTitle}>
              {loading
                ? 'Scanning…'
                : subCount > 0
                ? 'Money Leaks Detected'
                : 'No Leaks Found'}
            </Text>
          </View>

          <View style={styles.heroIconBadge}>
            <Feather name="target" size={22} color={D.red} />
          </View>
        </View>

        {/* Glass summary card */}
        {!loading && totalMonthly > 0 && (
          <View style={styles.glassCard}>
            <Text style={styles.glassAmount}>{fmtMonthly(totalMonthly)}</Text>
            <Text style={styles.glassAnnual}>{fmt(totalAnnual)}/year</Text>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 4 }}>
              <Text style={styles.glassFive}>
                {'🔥 5-year cost: '}
                <Text style={{ fontWeight: '700' }}>{fmt(impact5yr)}</Text>
              </Text>
            </View>
            <Text style={styles.glassIfInvested}>if invested instead</Text>
          </View>
        )}

        {/* Subscriptions found pill */}
        {!loading && subCount > 0 && (
          <View style={styles.countPill}>
            <Feather name="alert-circle" size={12} color={D.red} />
            <Text style={styles.countPillText}>{subCount} SUBSCRIPTIONS FOUND</Text>
          </View>
        )}
      </LinearGradient>

      {/* ── Scrollable body ───────────────────────────────────────────────── */}
      <Animated.ScrollView
        style={{ flex: 1, opacity: fadeAnim, transform: [{ translateY: slideAnim }] }}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={D.red} />
        }
      >
        {/* ── Loading skeleton ──────────────────────────────────────────── */}
        {loading && <LoadingSkeleton />}

        {/* ── Error state ───────────────────────────────────────────────── */}
        {!loading && error && (
          <View style={styles.center}>
            <View style={styles.errorIconWrap}>
              <Feather name="wifi-off" size={26} color={D.red} />
            </View>
            <Text style={styles.emptyTitle}>Scan failed</Text>
            <Text style={styles.centerText}>
              Could not load subscription data. Pull down to retry.
            </Text>
          </View>
        )}

        {/* ── Empty state ───────────────────────────────────────────────── */}
        {!loading && !error && subCount === 0 && (
          <View style={styles.center}>
            <View style={styles.emptyIconWrap}>
              <Feather name="check-circle" size={32} color={D.green} />
            </View>
            <Text style={styles.emptyTitle}>You're leak-free</Text>
            <Text style={styles.centerText}>
              No subscription leaks detected in the last 6 months.
            </Text>
            <Text style={[styles.centerText, { marginTop: 6 }]}>
              We'll keep scanning as new transactions come in.
            </Text>
          </View>
        )}

        {/* ── Main content ──────────────────────────────────────────────── */}
        {hasData && (
          <>
            {/* Impact breakdown row */}
            <View style={styles.impactRow}>
              {/* Monthly drain */}
              <View style={[styles.impactCard, { backgroundColor: '#FEF2F2', borderColor: '#FECACA' }]}>
                <Text style={[styles.impactAmount, { color: D.red }]}>{fmt(totalMonthly)}</Text>
                <Text style={styles.impactLabel}>Monthly Drain</Text>
              </View>
              {/* 5-Year opportunity */}
              <View style={[styles.impactCard, { backgroundColor: '#FFFBEB', borderColor: '#FDE68A' }]}>
                <Text style={[styles.impactAmount, { color: '#B45309' }]}>{fmt(impact5yr)}</Text>
                <Text style={styles.impactLabel}>5-Year Opp. Cost</Text>
              </View>
            </View>

            {/* Section label */}
            <Text style={styles.sectionHeader}>DETECTED SUBSCRIPTIONS</Text>

            {/* Top leak spotlight */}
            {topLeak && (
              <SubscriptionCard
                sub={{
                  merchantName:    topLeak.merchantName,
                  normalizedName:  topLeak.normalizedName,
                  cadence:         topLeak.cadence,
                  confidence:      topLeak.confidence,
                  monthlyEquivalent: topLeak.monthlyEquivalent,
                  category:        topLeak.category,
                  easyToForget:    topLeak.easyToForget,
                }}
                isTopLeak
              />
            )}

            {/* Rest of subscriptions (skip the top leak if it matches normalizedName) */}
            {subs
              .filter(s =>
                !topLeak ||
                (s.normalizedName ?? s.merchantName) !==
                  (topLeak.normalizedName ?? topLeak.merchantName)
              )
              .map((sub, idx) => (
                <SubscriptionCard key={`${sub.normalizedName ?? sub.merchantName}-${idx}`} sub={sub} />
              ))}

            {/* "What if you cancelled?" card */}
            {cancelTotal > 0 && (
              <View style={styles.whatIfCard}>
                <View style={styles.whatIfAccent} />
                <View style={styles.whatIfInner}>
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                    <View style={styles.whatIfIconWrap}>
                      <Feather name="scissors" size={14} color={D.indigo} />
                    </View>
                    <Text style={styles.whatIfEyebrow}>WHAT IF YOU CANCELLED?</Text>
                  </View>
                  <Text style={styles.whatIfHeadline}>
                    Cancelling your top{' '}
                    <Text style={styles.whatIfHighlight}>{cancelCount}</Text>{' '}
                    subscription{cancelCount !== 1 ? 's' : ''} would free{' '}
                    <Text style={styles.whatIfHighlight}>{fmtMonthly(cancelTotal)}</Text>
                  </Text>
                  <View style={styles.whatIfProjection}>
                    <Feather name="trending-up" size={15} color={D.indigo} />
                    <Text style={styles.whatIfProjectionText}>
                      Invested at 7% for 5 years:{' '}
                      <Text style={[styles.whatIfHighlight, { fontSize: 16 }]}>
                        {fmt(cancelFV)}
                      </Text>
                    </Text>
                  </View>
                  <Text style={styles.whatIfDisclaimer}>
                    Projection uses a monthly compound model (FV formula). Not financial advice.
                  </Text>
                </View>
              </View>
            )}

            {/* ── Invest This Money CTA ─────────────────────────────────────── */}
            {totalMonthly > 0 && (
              <Pressable
                style={({ pressed }) => [styles.investCta, { opacity: pressed ? 0.85 : 1 }]}
                onPress={() => navigation.navigate('Reallocate', { monthlyAmount: totalMonthly })}
              >
                <View style={styles.investCtaIcon}>
                  <Feather name="refresh-cw" size={20} color={D.white} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.investCtaTitle}>Invest This Money</Text>
                  <Text style={styles.investCtaSubtitle}>
                    Turn {fmtMonthly(totalMonthly)} into wealth-building strategies
                  </Text>
                </View>
                <Feather name="chevron-right" size={22} color={D.white} />
              </Pressable>
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

  // ── Hero ──────────────────────────────────────────────────────────────────
  hero: {
    paddingHorizontal: 20,
    paddingBottom: 14,
  },
  heroTop: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
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
    backgroundColor: 'rgba(239,68,68,0.18)',
    borderWidth: 1,
    borderColor: 'rgba(239,68,68,0.35)',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },

  // Glass summary card
  glassCard: {
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderRadius: D.r16,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.14)',
    padding: 14,
    marginBottom: 10,
    alignItems: 'center',
  },
  glassAmount: {
    fontSize: 40,
    fontWeight: '800',
    color: D.white,
    letterSpacing: -1.5,
    lineHeight: 46,
  },
  glassAnnual: {
    fontSize: 16,
    fontWeight: '600',
    color: D.amber,
    marginTop: 0,
  },
  glassFive: {
    fontSize: 13,
    color: 'rgba(255,255,255,0.75)',
    marginTop: 4,
  },
  glassIfInvested: {
    fontSize: 11,
    color: 'rgba(255,255,255,0.4)',
    marginTop: 1,
  },

  // Count pill
  countPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    alignSelf: 'flex-start',
    backgroundColor: 'rgba(239,68,68,0.18)',
    borderWidth: 1,
    borderColor: 'rgba(239,68,68,0.35)',
    borderRadius: 99,
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  countPillText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#FCA5A5',
    letterSpacing: 0.8,
  },

  // ── Scroll body ────────────────────────────────────────────────────────────
  scrollContent: {
    paddingHorizontal: 16,
    paddingTop: 14,
  },

  // Impact row
  impactRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 12,
  },
  impactCard: {
    flex: 1,
    borderRadius: D.r16,
    borderWidth: 1,
    padding: 12,
    alignItems: 'center',
    gap: 2,
  },
  impactAmount: {
    fontSize: 22,
    fontWeight: '800',
    letterSpacing: -0.5,
  },
  impactLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: D.textSecondary,
    letterSpacing: 0.3,
  },

  // Section header
  sectionHeader: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.2,
    color: D.textMuted,
    marginBottom: 12,
    marginLeft: 2,
  },

  // ── Card ───────────────────────────────────────────────────────────────────
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
  cardInner: { padding: 16 },

  // Top leak variant
  topLeakCard: {
    borderWidth: 1,
    borderColor: 'rgba(239,68,68,0.25)',
    shadowColor: D.red,
    shadowOpacity: 0.12,
    shadowRadius: 16,
  },
  topLeakAccent: {
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    width: 4,
    backgroundColor: D.red,
  },

  // ── Subscription card internals ────────────────────────────────────────────
  subHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  subName: {
    fontSize: 16,
    fontWeight: '700',
    color: D.textPrimary,
    letterSpacing: -0.2,
    marginBottom: 6,
  },
  subCost: {
    fontSize: 17,
    fontWeight: '800',
    letterSpacing: -0.3,
    flexShrink: 0,
    marginTop: 2,
  },

  // Category chip
  catChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    borderRadius: 99,
    paddingHorizontal: 9,
    paddingVertical: 3,
  },
  catDot: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
  },
  catChipText: {
    fontSize: 11,
    fontWeight: '600',
  },

  // Cadence badge
  cadenceBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: D.bg,
    borderRadius: 99,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  cadenceText: {
    fontSize: 10,
    fontWeight: '500',
    color: D.textMuted,
  },

  // Easy to forget badge
  forgetBadge: {
    backgroundColor: '#FFF7ED',
    borderRadius: 99,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderWidth: 1,
    borderColor: '#FED7AA',
  },
  forgetBadgeText: {
    fontSize: 10,
    fontWeight: '500',
    color: '#9A3412',
  },

  // Top leak pill
  topLeakPill: {
    alignSelf: 'flex-start',
    backgroundColor: D.red,
    borderRadius: 99,
    paddingHorizontal: 10,
    paddingVertical: 3,
    marginBottom: 6,
  },
  topLeakPillText: {
    fontSize: 9,
    fontWeight: '800',
    color: D.white,
    letterSpacing: 1.2,
  },

  // Confidence bar
  confBarTrack: {
    height: 5,
    backgroundColor: D.bg,
    borderRadius: 3,
    overflow: 'hidden',
  },
  confBarFill: {
    height: '100%',
    borderRadius: 3,
  },
  confLabel: {
    fontSize: 10,
    color: D.textMuted,
    fontWeight: '500',
  },

  // ── "What if you cancelled?" card ─────────────────────────────────────────
  whatIfCard: {
    backgroundColor: D.card,
    borderRadius: D.r20,
    marginBottom: 14,
    shadowColor: D.indigo,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 14,
    elevation: 3,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: `${D.indigo}22`,
  },
  whatIfAccent: {
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    width: 4,
    backgroundColor: D.indigo,
  },
  whatIfInner: {
    padding: 18,
    paddingLeft: 22,
  },
  whatIfIconWrap: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: D.indigoFaint,
    alignItems: 'center',
    justifyContent: 'center',
  },
  whatIfEyebrow: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.2,
    color: D.indigo,
  },
  whatIfHeadline: {
    fontSize: 15,
    fontWeight: '500',
    color: D.textPrimary,
    lineHeight: 22,
    marginBottom: 14,
  },
  whatIfHighlight: {
    fontWeight: '800',
    color: D.indigo,
  },
  whatIfProjection: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: D.indigoFaint,
    borderRadius: D.r12,
    paddingHorizontal: 14,
    paddingVertical: 10,
    marginBottom: 10,
  },
  whatIfProjectionText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#3730A3',
    flex: 1,
    lineHeight: 20,
  },
  whatIfDisclaimer: {
    fontSize: 11,
    color: D.textMuted,
    lineHeight: 16,
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
    backgroundColor: D.greenFaint,
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
    backgroundColor: '#FEE2E2',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },

  // ── Invest This Money CTA ───────────────────────────────────────────────────
  investCta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    backgroundColor: '#10B981',
    borderRadius: 18,
    padding: 18,
    marginTop: 16,
    shadowColor: '#10B981',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 12,
    elevation: 4,
  },
  investCtaIcon: {
    width: 44,
    height: 44,
    borderRadius: 14,
    backgroundColor: 'rgba(255,255,255,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  investCtaTitle: {
    fontSize: 17,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: -0.3,
  },
  investCtaSubtitle: {
    fontSize: 12,
    fontWeight: '500',
    color: 'rgba(255,255,255,0.8)',
    marginTop: 2,
  },
});
