/**
 * WeeklyDigestScreen — Your Weekly Wealth Report
 * ================================================
 * The "Variable Reward" from the Hooked model.
 * Shows personalized weekly progress with archetype-based coaching.
 */

import React, { useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  Animated,
  StatusBar,
  Share,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Feather } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';

// ── Design Tokens ────────────────────────────────────────────────────────────

const D = {
  navy:          '#0B1426',
  navyMid:       '#0F1E35',
  navyLight:     '#162642',
  white:         '#FFFFFF',
  green:         '#10B981',
  greenFaint:    '#D1FAE5',
  indigo:        '#6366F1',
  indigoFaint:   '#EEF2FF',
  amber:         '#F59E0B',
  amberFaint:    '#FEF3C7',
  red:           '#EF4444',
  textPrimary:   '#0F172A',
  textSecondary: '#64748B',
  textMuted:     '#94A3B8',
  card:          '#FFFFFF',
  bg:            '#F1F5F9',
  border:        '#E2E8F0',
};

// ── Demo Data ────────────────────────────────────────────────────────────────

const DEMO_DIGEST = {
  weekEnding: 'March 9, 2026',
  portfolioValue: 47832,
  portfolioChangeAmount: 1247,
  portfolioChangePercent: 2.68,
  daysCloserToGoal: 14,
  goalProgressPercent: 4.78,
  estimatedGoalDate: 'August 2041',
  leaksRedirectedAmount: 127,
  contributionsThisWeek: 287,
  contributionStreakDays: 23,
  sp500ChangePercent: 1.92,
  beatMarket: true,
  coachingHeadline: 'The System Is Working',
  coachingMessage: "+$1,247 this week — the math of compounding in action. You're now 14 days ahead of schedule. Plus, you redirected $127/mo in leaks — worth $63,450 long-term!",
  coachingTone: 'the_architect',
  nextActionHeadline: 'Review your portfolio allocation',
  nextActionScreen: 'AIPortfolioBuilder',
  highlights: [
    {
      type: 'portfolio_growth',
      headline: 'Portfolio Growth',
      value: '+$1,247',
      subtext: '+2.68% this week',
      icon: 'trending-up',
      color: D.green,
      isPositive: true,
    },
    {
      type: 'leak_savings',
      headline: 'Leaks Redirected',
      value: '$127/mo',
      subtext: 'Worth $63,450 in 20 years',
      icon: 'shield',
      color: D.indigo,
      isPositive: true,
    },
    {
      type: 'goal_acceleration',
      headline: 'Goal Acceleration',
      value: '14 days closer',
      subtext: 'To your millionaire date',
      icon: 'zap',
      color: D.green,
      isPositive: true,
    },
    {
      type: 'market_beat',
      headline: 'Beat the Market',
      value: '+0.76%',
      subtext: 'S&P 500 was +1.92%',
      icon: 'award',
      color: D.amber,
      isPositive: true,
    },
  ],
};

// ── Highlight Card Component ─────────────────────────────────────────────────

function HighlightCard({
  highlight,
  index,
}: {
  highlight: typeof DEMO_DIGEST.highlights[0];
  index: number;
}) {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(20)).current;
  const scaleAnim = useRef(new Animated.Value(0.95)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 400,
        delay: index * 100 + 300,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 400,
        delay: index * 100 + 300,
        useNativeDriver: true,
      }),
      Animated.spring(scaleAnim, {
        toValue: 1,
        delay: index * 100 + 300,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  return (
    <Animated.View
      style={[
        styles.highlightCard,
        {
          opacity: fadeAnim,
          transform: [{ translateY: slideAnim }, { scale: scaleAnim }],
        },
      ]}
    >
      <View style={[styles.highlightIcon, { backgroundColor: highlight.color + '20' }]}>
        <Feather name={highlight.icon as any} size={20} color={highlight.color} />
      </View>
      <Text style={styles.highlightHeadline}>{highlight.headline}</Text>
      <Text style={[styles.highlightValue, { color: highlight.color }]}>
        {highlight.value}
      </Text>
      <Text style={styles.highlightSubtext}>{highlight.subtext}</Text>
    </Animated.View>
  );
}

// ── Main Component ───────────────────────────────────────────────────────────

export default function WeeklyDigestScreen() {
  const navigation = useNavigation<any>();
  const heroFadeAnim = useRef(new Animated.Value(0)).current;
  const heroSlideAnim = useRef(new Animated.Value(-30)).current;
  const countAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(heroFadeAnim, {
        toValue: 1,
        duration: 600,
        useNativeDriver: true,
      }),
      Animated.timing(heroSlideAnim, {
        toValue: 0,
        duration: 600,
        useNativeDriver: true,
      }),
      Animated.timing(countAnim, {
        toValue: DEMO_DIGEST.portfolioChangeAmount,
        duration: 1000,
        useNativeDriver: false,
      }),
    ]).start();
  }, []);

  const handleShare = async () => {
    try {
      await Share.share({
        message: `My wealth grew by $${DEMO_DIGEST.portfolioChangeAmount.toLocaleString()} this week! 📈 I'm ${DEMO_DIGEST.daysCloserToGoal} days closer to my financial goal. #WealthBuilding`,
      });
    } catch (error) {
      console.log('Share error:', error);
    }
  };

  const handleNextAction = () => {
    navigation.navigate(DEMO_DIGEST.nextActionScreen);
  };

  const isPositiveWeek = DEMO_DIGEST.portfolioChangeAmount >= 0;

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" />
      
      {/* Hero Header */}
      <LinearGradient
        colors={isPositiveWeek ? [D.navy, '#0A2518'] : [D.navy, D.navyMid]}
        style={styles.hero}
      >
        <SafeAreaView edges={['top']} style={styles.heroSafe}>
          <View style={styles.heroTop}>
            <Pressable onPress={() => navigation.goBack()} style={styles.backBtn}>
              <Feather name="x" size={24} color={D.white} />
            </Pressable>
            <View style={styles.heroTitleWrap}>
              <Text style={styles.heroEyebrow}>WEEKLY WEALTH DIGEST</Text>
              <Text style={styles.heroTitle}>Week of {DEMO_DIGEST.weekEnding}</Text>
            </View>
            <Pressable onPress={handleShare} style={styles.shareBtn}>
              <Feather name="share" size={20} color={D.white} />
            </Pressable>
          </View>
          
          {/* Hero Number */}
          <Animated.View
            style={[
              styles.heroNumber,
              {
                opacity: heroFadeAnim,
                transform: [{ translateY: heroSlideAnim }],
              },
            ]}
          >
            <Text style={styles.heroChangeLabel}>This Week's Progress</Text>
            <View style={styles.heroChangeRow}>
              <Text style={[styles.heroChangeAmount, { color: isPositiveWeek ? D.green : D.red }]}>
                {isPositiveWeek ? '+' : ''}${DEMO_DIGEST.portfolioChangeAmount.toLocaleString()}
              </Text>
              <View style={[styles.heroChangePill, { backgroundColor: isPositiveWeek ? D.green + '30' : D.red + '30' }]}>
                <Feather
                  name={isPositiveWeek ? 'trending-up' : 'trending-down'}
                  size={14}
                  color={isPositiveWeek ? D.green : D.red}
                />
                <Text style={[styles.heroChangePercent, { color: isPositiveWeek ? D.green : D.red }]}>
                  {isPositiveWeek ? '+' : ''}{DEMO_DIGEST.portfolioChangePercent.toFixed(2)}%
                </Text>
              </View>
            </View>
            <Text style={styles.heroPortfolioValue}>
              Portfolio: ${DEMO_DIGEST.portfolioValue.toLocaleString()}
            </Text>
          </Animated.View>
          
          {/* Days Closer Badge */}
          <Animated.View
            style={[
              styles.daysCloserBadge,
              { opacity: heroFadeAnim },
            ]}
          >
            <Feather name="zap" size={16} color={D.green} />
            <Text style={styles.daysCloserText}>
              {DEMO_DIGEST.daysCloserToGoal} days closer to your goal
            </Text>
            <Text style={styles.daysCloserSubtext}>
              Est. arrival: {DEMO_DIGEST.estimatedGoalDate}
            </Text>
          </Animated.View>
        </SafeAreaView>
      </LinearGradient>
      
      {/* Content */}
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Highlights Grid */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>This Week's Highlights</Text>
          <View style={styles.highlightsGrid}>
            {DEMO_DIGEST.highlights.map((highlight, index) => (
              <HighlightCard key={highlight.type} highlight={highlight} index={index} />
            ))}
          </View>
        </View>
        
        {/* Coaching Message */}
        <View style={styles.section}>
          <View style={styles.coachingCard}>
            <View style={styles.coachingHeader}>
              <View style={styles.coachingIconWrap}>
                <Feather name="message-circle" size={18} color={D.indigo} />
              </View>
              <View>
                <Text style={styles.coachingTone}>
                  {DEMO_DIGEST.coachingTone.replace('the_', '').replace('_', ' ').toUpperCase()}
                </Text>
                <Text style={styles.coachingHeadline}>{DEMO_DIGEST.coachingHeadline}</Text>
              </View>
            </View>
            <Text style={styles.coachingMessage}>{DEMO_DIGEST.coachingMessage}</Text>
          </View>
        </View>
        
        {/* Stats Row */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>By the Numbers</Text>
          <View style={styles.statsRow}>
            <View style={styles.statCard}>
              <Feather name="repeat" size={18} color={D.green} />
              <Text style={styles.statValue}>${DEMO_DIGEST.contributionsThisWeek}</Text>
              <Text style={styles.statLabel}>Contributed</Text>
            </View>
            <View style={styles.statCard}>
              <Feather name="flame" size={18} color={D.red} />
              <Text style={styles.statValue}>{DEMO_DIGEST.contributionStreakDays}</Text>
              <Text style={styles.statLabel}>Day Streak</Text>
            </View>
            <View style={styles.statCard}>
              <Feather name="pie-chart" size={18} color={D.indigo} />
              <Text style={styles.statValue}>{DEMO_DIGEST.goalProgressPercent.toFixed(1)}%</Text>
              <Text style={styles.statLabel}>To Goal</Text>
            </View>
          </View>
        </View>
        
        {/* Market Context */}
        {DEMO_DIGEST.beatMarket && (
          <View style={styles.marketContext}>
            <Feather name="award" size={16} color={D.amber} />
            <Text style={styles.marketContextText}>
              You outperformed the S&P 500 by {(DEMO_DIGEST.portfolioChangePercent - DEMO_DIGEST.sp500ChangePercent).toFixed(2)}% this week
            </Text>
          </View>
        )}
        
        {/* Next Action */}
        <Pressable style={styles.nextActionCard} onPress={handleNextAction}>
          <View style={styles.nextActionLeft}>
            <Text style={styles.nextActionLabel}>SUGGESTED NEXT STEP</Text>
            <Text style={styles.nextActionHeadline}>{DEMO_DIGEST.nextActionHeadline}</Text>
          </View>
          <View style={styles.nextActionBtn}>
            <Feather name="arrow-right" size={20} color={D.white} />
          </View>
        </Pressable>
        
        <View style={{ height: 40 }} />
      </ScrollView>
    </View>
  );
}

// ── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: D.bg,
  },
  
  // Hero
  hero: {},
  heroSafe: {
    paddingHorizontal: 20,
    paddingBottom: 24,
  },
  heroTop: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
    marginBottom: 20,
    gap: 12,
  },
  backBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255,255,255,0.1)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  shareBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255,255,255,0.1)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  heroTitleWrap: {
    flex: 1,
  },
  heroEyebrow: {
    fontSize: 9,
    fontWeight: '700',
    color: 'rgba(255,255,255,0.5)',
    letterSpacing: 1.5,
    marginBottom: 2,
  },
  heroTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: D.white,
  },
  heroNumber: {
    alignItems: 'center',
    marginBottom: 20,
  },
  heroChangeLabel: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.6)',
    marginBottom: 8,
  },
  heroChangeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  heroChangeAmount: {
    fontSize: 48,
    fontWeight: '800',
    letterSpacing: -2,
  },
  heroChangePill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 12,
  },
  heroChangePercent: {
    fontSize: 14,
    fontWeight: '700',
  },
  heroPortfolioValue: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.6)',
    marginTop: 8,
  },
  daysCloserBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    flexWrap: 'wrap',
    gap: 8,
    backgroundColor: 'rgba(16,185,129,0.15)',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 14,
  },
  daysCloserText: {
    fontSize: 14,
    fontWeight: '700',
    color: D.green,
  },
  daysCloserSubtext: {
    fontSize: 12,
    color: 'rgba(16,185,129,0.7)',
  },
  
  // Scroll
  scroll: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 16,
    paddingTop: 20,
  },
  
  // Section
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: D.textPrimary,
    marginBottom: 12,
  },
  
  // Highlights
  highlightsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  highlightCard: {
    width: '48%',
    backgroundColor: D.card,
    borderRadius: 14,
    padding: 14,
    alignItems: 'center',
  },
  highlightIcon: {
    width: 40,
    height: 40,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  highlightHeadline: {
    fontSize: 11,
    color: D.textSecondary,
    marginBottom: 4,
  },
  highlightValue: {
    fontSize: 20,
    fontWeight: '800',
    marginBottom: 2,
  },
  highlightSubtext: {
    fontSize: 10,
    color: D.textMuted,
    textAlign: 'center',
  },
  
  // Coaching
  coachingCard: {
    backgroundColor: D.card,
    borderRadius: 16,
    padding: 16,
    borderLeftWidth: 4,
    borderLeftColor: D.indigo,
  },
  coachingHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 12,
  },
  coachingIconWrap: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: D.indigoFaint,
    alignItems: 'center',
    justifyContent: 'center',
  },
  coachingTone: {
    fontSize: 9,
    fontWeight: '700',
    color: D.indigo,
    letterSpacing: 1,
  },
  coachingHeadline: {
    fontSize: 16,
    fontWeight: '700',
    color: D.textPrimary,
  },
  coachingMessage: {
    fontSize: 14,
    color: D.textSecondary,
    lineHeight: 22,
  },
  
  // Stats
  statsRow: {
    flexDirection: 'row',
    gap: 10,
  },
  statCard: {
    flex: 1,
    backgroundColor: D.card,
    borderRadius: 12,
    padding: 14,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 20,
    fontWeight: '800',
    color: D.textPrimary,
    marginTop: 6,
  },
  statLabel: {
    fontSize: 11,
    color: D.textSecondary,
    marginTop: 2,
  },
  
  // Market Context
  marketContext: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: D.amberFaint,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 12,
    marginBottom: 20,
  },
  marketContextText: {
    fontSize: 13,
    fontWeight: '600',
    color: D.amber,
  },
  
  // Next Action
  nextActionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: D.green,
    borderRadius: 16,
    padding: 18,
  },
  nextActionLeft: {
    flex: 1,
  },
  nextActionLabel: {
    fontSize: 9,
    fontWeight: '700',
    color: 'rgba(255,255,255,0.7)',
    letterSpacing: 1,
    marginBottom: 4,
  },
  nextActionHeadline: {
    fontSize: 16,
    fontWeight: '700',
    color: D.white,
  },
  nextActionBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
});
