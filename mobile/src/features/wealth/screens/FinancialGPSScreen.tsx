/**
 * FinancialGPSScreen — Hub for All Financial Tools
 * ==================================================
 * Central dashboard linking to all Financial GPS modules:
 * - Net Worth, Wealth Arrival, Leak Detector
 * - Health Score, Life Decision, Income Intelligence
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
  indigo:        '#6366F1',
  red:           '#EF4444',
  amber:         '#F59E0B',
  purple:        '#7C3AED',
  blue:          '#3B82F6',
  textPrimary:   '#0F172A',
  textSecondary: '#64748B',
  textMuted:     '#94A3B8',
  card:          '#FFFFFF',
  cardBorder:    '#E2E8F0',
  bg:            '#F1F5F9',
  greenFaint:    '#D1FAE5',
  indigoFaint:   '#EEF2FF',
  redFaint:      '#FEE2E2',
  amberFaint:    '#FEF3C7',
};

// ── Module Configuration ─────────────────────────────────────────────────────

interface ModuleConfig {
  key: string;
  screen: string;
  title: string;
  subtitle: string;
  icon: keyof typeof Feather.glyphMap;
  color: string;
  faint: string;
  tags: string[];
}

const MODULES: ModuleConfig[] = [
  {
    key: 'networth',
    screen: 'NetWorth',
    title: 'Net Worth',
    subtitle: 'Track your total wealth over time',
    icon: 'trending-up',
    color: D.green,
    faint: D.greenFaint,
    tags: ['History', 'Breakdown', 'Records'],
  },
  {
    key: 'arrival',
    screen: 'WealthArrival',
    title: 'Wealth Arrival',
    subtitle: 'When will you hit your goal?',
    icon: 'flag',
    color: D.indigo,
    faint: D.indigoFaint,
    tags: ['3 Scenarios', 'Year-by-Year'],
  },
  {
    key: 'leaks',
    screen: 'LeakDetector',
    title: 'Leak Detector',
    subtitle: 'Find subscriptions draining cash',
    icon: 'alert-circle',
    color: D.red,
    faint: D.redFaint,
    tags: ['Subscriptions', '5yr Cost'],
  },
  {
    key: 'health',
    screen: 'FinancialHealth',
    title: 'Health Score',
    subtitle: 'Your financial wellness grade',
    icon: 'heart',
    color: D.green,
    faint: D.greenFaint,
    tags: ['4 Pillars', 'A–F Grade'],
  },
  {
    key: 'decisions',
    screen: 'LifeDecision',
    title: 'Life Decision',
    subtitle: '"What if I buy a $60K car?"',
    icon: 'git-branch',
    color: D.amber,
    faint: D.amberFaint,
    tags: ['Opportunity Cost', '10yr Delta'],
  },
  {
    key: 'income',
    screen: 'IncomeIntelligence',
    title: 'Income Intelligence',
    subtitle: 'Classify your income streams',
    icon: 'dollar-sign',
    color: D.green,
    faint: D.greenFaint,
    tags: ['Salary', 'Side Hustle', 'Diversity'],
  },
];

// ── Module Card Component ────────────────────────────────────────────────────

function ModuleCard({ module, onPress, index }: { module: ModuleConfig; onPress: () => void; index: number }) {
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(20)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 400,
        delay: index * 80,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 400,
        delay: index * 80,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  const onPressIn = () => {
    Animated.spring(scaleAnim, { toValue: 0.97, useNativeDriver: true, speed: 50 }).start();
  };
  const onPressOut = () => {
    Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true, speed: 50 }).start();
  };

  return (
    <Animated.View
      style={{
        transform: [{ scale: scaleAnim }, { translateY: slideAnim }],
        opacity: fadeAnim,
      }}
    >
      <Pressable onPress={onPress} onPressIn={onPressIn} onPressOut={onPressOut} style={styles.card}>
        <View style={[styles.cardIconWrap, { backgroundColor: module.faint }]}>
          <Feather name={module.icon} size={22} color={module.color} />
        </View>
        <View style={styles.cardContent}>
          <Text style={styles.cardTitle}>{module.title}</Text>
          <Text style={styles.cardSubtitle}>{module.subtitle}</Text>
          <View style={styles.cardTags}>
            {module.tags.map((tag, i) => (
              <View key={i} style={[styles.tag, { backgroundColor: module.faint }]}>
                <Text style={[styles.tagText, { color: module.color }]}>{tag}</Text>
              </View>
            ))}
          </View>
        </View>
        <View style={[styles.cardArrow, { backgroundColor: module.color + '15' }]}>
          <Feather name="chevron-right" size={18} color={module.color} />
        </View>
      </Pressable>
    </Animated.View>
  );
}

// ── Main Component ───────────────────────────────────────────────────────────

export default function FinancialGPSScreen() {
  const navigation = useNavigation<any>();

  const handleModulePress = (screen: string) => {
    navigation.navigate(screen);
  };

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" />

      {/* ── Hero Header ──────────────────────────────────────────────────── */}
      <LinearGradient colors={[D.navy, D.navyMid]} style={styles.hero}>
        <SafeAreaView edges={['top']} style={styles.heroSafe}>
          <View style={styles.heroTop}>
            <Pressable
              onPress={() => navigation.goBack()}
              style={({ pressed }) => [styles.backBtn, { opacity: pressed ? 0.6 : 1 }]}
            >
              <Feather name="chevron-left" size={24} color={D.white} />
            </Pressable>
            <View style={styles.heroTitleWrap}>
              <Text style={styles.heroEyebrow}>FINANCIAL GPS</Text>
              <Text style={styles.heroTitle}>Your Money Dashboard</Text>
            </View>
            <View style={styles.heroIconBadge}>
              <Feather name="compass" size={22} color={D.green} />
            </View>
          </View>

          <Text style={styles.heroSubtitle}>
            Track, plan, and optimize your entire financial life in one place.
          </Text>
        </SafeAreaView>
      </LinearGradient>

      {/* ── Module Grid ──────────────────────────────────────────────────── */}
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {MODULES.map((module, index) => (
          <ModuleCard
            key={module.key}
            module={module}
            index={index}
            onPress={() => handleModulePress(module.screen)}
          />
        ))}

        {/* Footer */}
        <View style={styles.footer}>
          <Feather name="info" size={14} color={D.textMuted} />
          <Text style={styles.footerText}>
            All insights powered by your connected accounts
          </Text>
        </View>
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
    paddingBottom: 16,
  },
  heroTop: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
    marginBottom: 10,
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
    fontSize: 22,
    fontWeight: '800',
    color: D.white,
    letterSpacing: -0.3,
  },
  heroIconBadge: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(16,185,129,0.18)',
    borderWidth: 1,
    borderColor: 'rgba(16,185,129,0.35)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  heroSubtitle: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.65)',
    lineHeight: 20,
  },

  // Scroll
  scroll: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 32,
  },

  // Card
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: D.card,
    borderRadius: 16,
    padding: 14,
    marginBottom: 10,
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 10,
    elevation: 3,
  },
  cardIconWrap: {
    width: 48,
    height: 48,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardContent: {
    flex: 1,
    marginLeft: 12,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: D.textPrimary,
    letterSpacing: -0.2,
    marginBottom: 2,
  },
  cardSubtitle: {
    fontSize: 12,
    color: D.textSecondary,
    marginBottom: 6,
  },
  cardTags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 4,
  },
  tag: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  tagText: {
    fontSize: 10,
    fontWeight: '600',
  },
  cardArrow: {
    width: 32,
    height: 32,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 8,
  },

  // Footer
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginTop: 8,
    paddingVertical: 12,
  },
  footerText: {
    fontSize: 12,
    color: D.textMuted,
  },
});
