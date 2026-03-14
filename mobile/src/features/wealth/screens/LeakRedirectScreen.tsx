/**
 * LeakRedirectScreen — Swipe-to-Wealth Redirector
 * =================================================
 * The "Variable Reward" screen from the Hooked model.
 * Users swipe through their leaks and redirect savings to wealth.
 */

import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  PanResponder,
  Dimensions,
  StatusBar,
  Pressable,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Feather } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');
const SWIPE_THRESHOLD = SCREEN_WIDTH * 0.25;

// ── Design Tokens ────────────────────────────────────────────────────────────

const D = {
  navy:          '#0B1426',
  navyMid:       '#0F1E35',
  white:         '#FFFFFF',
  green:         '#10B981',
  greenFaint:    '#D1FAE5',
  red:           '#EF4444',
  redFaint:      '#FEE2E2',
  amber:         '#F59E0B',
  textPrimary:   '#0F172A',
  textSecondary: '#64748B',
  textMuted:     '#94A3B8',
  card:          '#FFFFFF',
  bg:            '#F1F5F9',
  border:        '#E2E8F0',
};

// ── Demo Leaks ───────────────────────────────────────────────────────────────

interface Leak {
  id: string;
  name: string;
  category: string;
  monthlyAmount: number;
  annualAmount: number;
  futureValue20yr: number;
  lastUsed: string;
  usageScore: number; // 0-100, lower = less used
  icon: keyof typeof Feather.glyphMap;
  color: string;
}

const DEMO_LEAKS: Leak[] = [
  {
    id: '1',
    name: 'Adobe Creative Cloud',
    category: 'Software',
    monthlyAmount: 54.99,
    annualAmount: 659.88,
    futureValue20yr: 27450,
    lastUsed: '3 months ago',
    usageScore: 15,
    icon: 'image',
    color: '#FF0000',
  },
  {
    id: '2',
    name: 'Gym Membership',
    category: 'Fitness',
    monthlyAmount: 49.99,
    annualAmount: 599.88,
    futureValue20yr: 24950,
    lastUsed: '6 weeks ago',
    usageScore: 25,
    icon: 'activity',
    color: '#10B981',
  },
  {
    id: '3',
    name: 'Streaming Bundle',
    category: 'Entertainment',
    monthlyAmount: 22.99,
    annualAmount: 275.88,
    futureValue20yr: 11480,
    lastUsed: 'Active',
    usageScore: 85,
    icon: 'tv',
    color: '#6366F1',
  },
  {
    id: '4',
    name: 'Cloud Storage Pro',
    category: 'Storage',
    monthlyAmount: 9.99,
    annualAmount: 119.88,
    futureValue20yr: 4990,
    lastUsed: 'Using 5% of capacity',
    usageScore: 30,
    icon: 'cloud',
    color: '#3B82F6',
  },
];

// ── Swipe Card Component ─────────────────────────────────────────────────────

function SwipeCard({
  leak,
  isFirst,
  onSwipeLeft,
  onSwipeRight,
  totalSaved,
}: {
  leak: Leak;
  isFirst: boolean;
  onSwipeLeft: () => void;
  onSwipeRight: () => void;
  totalSaved: number;
}) {
  const pan = useRef(new Animated.ValueXY()).current;
  const scaleAnim = useRef(new Animated.Value(1)).current;

  const panResponder = useRef(
    PanResponder.create({
      onMoveShouldSetPanResponder: (_, gesture) => {
        return Math.abs(gesture.dx) > 10;
      },
      onPanResponderGrant: () => {
        Animated.spring(scaleAnim, { toValue: 0.98, useNativeDriver: true }).start();
      },
      onPanResponderMove: (_, gesture) => {
        pan.setValue({ x: gesture.dx, y: 0 });
      },
      onPanResponderRelease: (_, gesture) => {
        Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true }).start();
        
        if (gesture.dx > SWIPE_THRESHOLD) {
          // Swipe right = Redirect to Wealth
          Animated.timing(pan, {
            toValue: { x: SCREEN_WIDTH + 100, y: 0 },
            duration: 250,
            useNativeDriver: true,
          }).start(() => {
            onSwipeRight();
            pan.setValue({ x: 0, y: 0 });
          });
        } else if (gesture.dx < -SWIPE_THRESHOLD) {
          // Swipe left = Keep / Ignore
          Animated.timing(pan, {
            toValue: { x: -SCREEN_WIDTH - 100, y: 0 },
            duration: 250,
            useNativeDriver: true,
          }).start(() => {
            onSwipeLeft();
            pan.setValue({ x: 0, y: 0 });
          });
        } else {
          // Snap back
          Animated.spring(pan, {
            toValue: { x: 0, y: 0 },
            useNativeDriver: true,
            speed: 20,
          }).start();
        }
      },
    })
  ).current;

  const rotate = pan.x.interpolate({
    inputRange: [-SCREEN_WIDTH / 2, 0, SCREEN_WIDTH / 2],
    outputRange: ['-10deg', '0deg', '10deg'],
  });

  const redirectOpacity = pan.x.interpolate({
    inputRange: [0, SWIPE_THRESHOLD],
    outputRange: [0, 1],
    extrapolate: 'clamp',
  });

  const keepOpacity = pan.x.interpolate({
    inputRange: [-SWIPE_THRESHOLD, 0],
    outputRange: [1, 0],
    extrapolate: 'clamp',
  });

  if (!isFirst) {
    return (
      <Animated.View style={[styles.card, styles.cardBehind]}>
        <View style={styles.cardHeader}>
          <View style={[styles.cardIcon, { backgroundColor: leak.color + '20' }]}>
            <Feather name={leak.icon} size={24} color={leak.color} />
          </View>
          <View style={styles.cardTitleWrap}>
            <Text style={styles.cardTitle}>{leak.name}</Text>
            <Text style={styles.cardCategory}>{leak.category}</Text>
          </View>
        </View>
      </Animated.View>
    );
  }

  return (
    <Animated.View
      style={[
        styles.card,
        {
          transform: [
            { translateX: pan.x },
            { rotate },
            { scale: scaleAnim },
          ],
        },
      ]}
      {...panResponder.panHandlers}
    >
      {/* Redirect overlay */}
      <Animated.View style={[styles.overlayRight, { opacity: redirectOpacity }]}>
        <View style={styles.overlayContent}>
          <Feather name="trending-up" size={40} color={D.green} />
          <Text style={[styles.overlayText, { color: D.green }]}>REDIRECT</Text>
          <Text style={[styles.overlaySubtext, { color: D.green }]}>to Wealth</Text>
        </View>
      </Animated.View>

      {/* Keep overlay */}
      <Animated.View style={[styles.overlayLeft, { opacity: keepOpacity }]}>
        <View style={styles.overlayContent}>
          <Feather name="x" size={40} color={D.textMuted} />
          <Text style={[styles.overlayText, { color: D.textMuted }]}>KEEP</Text>
          <Text style={[styles.overlaySubtext, { color: D.textMuted }]}>this one</Text>
        </View>
      </Animated.View>

      {/* Card content */}
      <View style={styles.cardHeader}>
        <View style={[styles.cardIcon, { backgroundColor: leak.color + '20' }]}>
          <Feather name={leak.icon} size={24} color={leak.color} />
        </View>
        <View style={styles.cardTitleWrap}>
          <Text style={styles.cardTitle}>{leak.name}</Text>
          <Text style={styles.cardCategory}>{leak.category}</Text>
        </View>
        <View style={styles.usageBadge}>
          <Text style={styles.usageBadgeText}>
            {leak.usageScore < 30 ? 'Low Use' : leak.usageScore < 70 ? 'Moderate' : 'Active'}
          </Text>
        </View>
      </View>

      <View style={styles.cardBody}>
        <View style={styles.amountRow}>
          <Text style={styles.amountLabel}>Monthly Cost</Text>
          <Text style={styles.amountValue}>${leak.monthlyAmount.toFixed(2)}</Text>
        </View>
        <View style={styles.amountRow}>
          <Text style={styles.amountLabel}>Annual Cost</Text>
          <Text style={styles.amountValue}>${leak.annualAmount.toFixed(2)}</Text>
        </View>
        <View style={styles.lastUsedRow}>
          <Feather name="clock" size={14} color={D.textMuted} />
          <Text style={styles.lastUsedText}>Last used: {leak.lastUsed}</Text>
        </View>
      </View>

      <View style={styles.cardFooter}>
        <LinearGradient
          colors={[D.greenFaint, D.white]}
          style={styles.futureValueCard}
        >
          <Text style={styles.futureValueLabel}>20-YEAR WEALTH POTENTIAL</Text>
          <Text style={styles.futureValueAmount}>
            ${leak.futureValue20yr.toLocaleString()}
          </Text>
          <Text style={styles.futureValueSubtext}>
            if redirected to investments (7% avg return)
          </Text>
        </LinearGradient>
      </View>

      <View style={styles.swipeHint}>
        <Pressable onPress={onSwipeLeft} style={styles.swipeHintButton}>
          <Text style={styles.swipeHintText}>← Keep</Text>
        </Pressable>
        <Text style={styles.swipeHintDivider}>Swipe</Text>
        <Pressable onPress={onSwipeRight} style={styles.swipeHintButton}>
          <Text style={[styles.swipeHintText, { color: D.green }]}>Redirect →</Text>
        </Pressable>
      </View>
    </Animated.View>
  );
}

// ── Main Component ───────────────────────────────────────────────────────────

export default function LeakRedirectScreen() {
  const navigation = useNavigation<any>();
  const [leaks, setLeaks] = useState(DEMO_LEAKS);
  const [redirected, setRedirected] = useState<Leak[]>([]);
  const [showSummary, setShowSummary] = useState(false);

  const totalSaved = redirected.reduce((sum, l) => sum + l.monthlyAmount, 0);
  const totalFutureValue = redirected.reduce((sum, l) => sum + l.futureValue20yr, 0);

  const handleSwipeRight = useCallback(() => {
    const [removed, ...rest] = leaks;
    setRedirected(prev => [...prev, removed]);
    setLeaks(rest);
    
    if (rest.length === 0) {
      setTimeout(() => setShowSummary(true), 300);
    }
  }, [leaks]);

  const handleSwipeLeft = useCallback(() => {
    const [, ...rest] = leaks;
    setLeaks(rest);
    
    if (rest.length === 0) {
      setTimeout(() => setShowSummary(true), 300);
    }
  }, [leaks]);

  const handleConfirmRedirect = () => {
    navigation.navigate('AIPortfolioBuilder', {
      suggestedAmount: totalSaved,
      fromLeakRedirect: true,
    });
  };

  // ── Summary Screen ─────────────────────────────────────────────────────────

  if (showSummary) {
    return (
      <View style={styles.root}>
        <StatusBar barStyle="light-content" />
        <LinearGradient colors={[D.navy, D.navyMid]} style={styles.summaryContainer}>
          <SafeAreaView style={styles.summarySafe}>
            <View style={styles.summaryContent}>
              {redirected.length > 0 ? (
                <>
                  <View style={styles.summaryIconWrap}>
                    <Feather name="check-circle" size={60} color={D.green} />
                  </View>
                  <Text style={styles.summaryTitle}>
                    ${totalSaved.toFixed(0)}/mo Redirected!
                  </Text>
                  <Text style={styles.summarySubtitle}>
                    You just unlocked ${totalFutureValue.toLocaleString()} in future wealth
                  </Text>
                  
                  <View style={styles.summaryCard}>
                    <View style={styles.summaryRow}>
                      <Text style={styles.summaryLabel}>Monthly Savings</Text>
                      <Text style={styles.summaryValue}>${totalSaved.toFixed(2)}</Text>
                    </View>
                    <View style={styles.summaryRow}>
                      <Text style={styles.summaryLabel}>Annual Savings</Text>
                      <Text style={styles.summaryValue}>${(totalSaved * 12).toFixed(0)}</Text>
                    </View>
                    <View style={styles.summaryRow}>
                      <Text style={styles.summaryLabel}>20-Year Value</Text>
                      <Text style={[styles.summaryValue, { color: D.green }]}>
                        ${totalFutureValue.toLocaleString()}
                      </Text>
                    </View>
                  </View>
                  
                  <Pressable
                    style={styles.summaryButton}
                    onPress={handleConfirmRedirect}
                  >
                    <Text style={styles.summaryButtonText}>
                      Invest ${totalSaved.toFixed(0)}/mo Now
                    </Text>
                    <Feather name="arrow-right" size={20} color={D.white} />
                  </Pressable>
                </>
              ) : (
                <>
                  <View style={styles.summaryIconWrap}>
                    <Feather name="check" size={60} color={D.textMuted} />
                  </View>
                  <Text style={styles.summaryTitle}>All Reviewed!</Text>
                  <Text style={styles.summarySubtitle}>
                    No leaks to redirect this time.
                  </Text>
                </>
              )}
              
              <Pressable
                style={styles.summaryBackButton}
                onPress={() => navigation.goBack()}
              >
                <Text style={styles.summaryBackText}>Back to Financial GPS</Text>
              </Pressable>
            </View>
          </SafeAreaView>
        </LinearGradient>
      </View>
    );
  }

  // ── Main Swipe Screen ──────────────────────────────────────────────────────

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" />
      
      {/* Header */}
      <LinearGradient colors={[D.navy, D.navyMid]} style={styles.header}>
        <SafeAreaView edges={['top']} style={styles.headerSafe}>
          <View style={styles.headerTop}>
            <Pressable onPress={() => navigation.goBack()} style={styles.backBtn}>
              <Feather name="x" size={24} color={D.white} />
            </Pressable>
            <View style={styles.headerTitleWrap}>
              <Text style={styles.headerEyebrow}>LEAK REDIRECTOR</Text>
              <Text style={styles.headerTitle}>Swipe to Wealth</Text>
            </View>
            <View style={styles.counterBadge}>
              <Text style={styles.counterText}>{leaks.length} left</Text>
            </View>
          </View>
          
          {/* Progress indicator */}
          {totalSaved > 0 && (
            <View style={styles.savedBanner}>
              <Feather name="trending-up" size={16} color={D.green} />
              <Text style={styles.savedText}>
                ${totalSaved.toFixed(0)}/mo redirected
              </Text>
              <Text style={styles.savedSubtext}>
                (${totalFutureValue.toLocaleString()} in 20 yrs)
              </Text>
            </View>
          )}
        </SafeAreaView>
      </LinearGradient>
      
      {/* Card Stack */}
      <View style={styles.cardContainer}>
        {leaks.slice(0, 2).reverse().map((leak, index) => (
          <SwipeCard
            key={leak.id}
            leak={leak}
            isFirst={index === leaks.slice(0, 2).length - 1}
            onSwipeLeft={handleSwipeLeft}
            onSwipeRight={handleSwipeRight}
            totalSaved={totalSaved}
          />
        ))}
      </View>
      
      {/* Bottom hint - now tappable */}
      <SafeAreaView edges={['bottom']} style={styles.bottomHint}>
        <View style={styles.actionHints}>
          <Pressable 
            style={styles.actionButton}
            onPress={() => leaks.length > 0 && handleSwipeLeft()}
          >
            <Feather name="chevron-left" size={20} color={D.textMuted} />
            <Text style={styles.actionHintText}>Keep subscription</Text>
          </Pressable>
          <Pressable 
            style={[styles.actionButton, styles.actionButtonRight]}
            onPress={() => leaks.length > 0 && handleSwipeRight()}
          >
            <Text style={[styles.actionHintText, { color: D.green }]}>Redirect to wealth</Text>
            <Feather name="chevron-right" size={20} color={D.green} />
          </Pressable>
        </View>
      </SafeAreaView>
    </View>
  );
}

// ── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: D.bg,
  },
  
  // Header
  header: {},
  headerSafe: {
    paddingHorizontal: 20,
    paddingBottom: 16,
  },
  headerTop: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
    marginBottom: 8,
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
  headerTitleWrap: {
    flex: 1,
  },
  headerEyebrow: {
    fontSize: 9,
    fontWeight: '700',
    color: 'rgba(255,255,255,0.5)',
    letterSpacing: 1.5,
    marginBottom: 2,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: D.white,
    letterSpacing: -0.3,
  },
  counterBadge: {
    backgroundColor: 'rgba(255,255,255,0.15)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  counterText: {
    fontSize: 13,
    fontWeight: '700',
    color: D.white,
  },
  savedBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: 'rgba(16,185,129,0.15)',
    paddingVertical: 8,
    borderRadius: 10,
  },
  savedText: {
    fontSize: 14,
    fontWeight: '700',
    color: D.green,
  },
  savedSubtext: {
    fontSize: 12,
    color: 'rgba(16,185,129,0.7)',
  },
  
  // Cards
  cardContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 20,
  },
  card: {
    position: 'absolute',
    width: SCREEN_WIDTH - 40,
    backgroundColor: D.card,
    borderRadius: 20,
    padding: 20,
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.12,
    shadowRadius: 24,
    elevation: 8,
  },
  cardBehind: {
    transform: [{ scale: 0.95 }, { translateY: 10 }],
    opacity: 0.7,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 20,
  },
  cardIcon: {
    width: 48,
    height: 48,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardTitleWrap: {
    flex: 1,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: D.textPrimary,
    marginBottom: 2,
  },
  cardCategory: {
    fontSize: 13,
    color: D.textSecondary,
  },
  usageBadge: {
    backgroundColor: D.amberFaint,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  usageBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    color: D.amber,
  },
  cardBody: {
    gap: 12,
    marginBottom: 20,
  },
  amountRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  amountLabel: {
    fontSize: 14,
    color: D.textSecondary,
  },
  amountValue: {
    fontSize: 18,
    fontWeight: '700',
    color: D.textPrimary,
  },
  lastUsedRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: D.border,
  },
  lastUsedText: {
    fontSize: 13,
    color: D.textMuted,
  },
  cardFooter: {},
  futureValueCard: {
    borderRadius: 14,
    padding: 16,
    alignItems: 'center',
  },
  futureValueLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: D.textSecondary,
    letterSpacing: 1,
    marginBottom: 6,
  },
  futureValueAmount: {
    fontSize: 32,
    fontWeight: '800',
    color: D.green,
    letterSpacing: -1,
  },
  futureValueSubtext: {
    fontSize: 12,
    color: D.textSecondary,
    marginTop: 4,
    textAlign: 'center',
  },
  swipeHint: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 16,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: D.border,
  },
  swipeHintButton: {
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  swipeHintText: {
    fontSize: 12,
    fontWeight: '600',
    color: D.textMuted,
  },
  swipeHintDivider: {
    fontSize: 12,
    color: D.textMuted,
  },
  
  // Overlays
  overlayRight: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(16,185,129,0.1)',
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 10,
  },
  overlayLeft: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(148,163,184,0.1)',
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 10,
  },
  overlayContent: {
    alignItems: 'center',
  },
  overlayText: {
    fontSize: 24,
    fontWeight: '800',
    marginTop: 8,
  },
  overlaySubtext: {
    fontSize: 14,
    fontWeight: '600',
  },
  
  // Bottom
  bottomHint: {
    paddingHorizontal: 20,
    paddingBottom: 8,
  },
  actionHints: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: D.card,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: D.border,
  },
  actionButtonRight: {
    backgroundColor: D.greenFaint,
    borderColor: D.green + '30',
  },
  actionHintText: {
    fontSize: 14,
    fontWeight: '600',
    color: D.textMuted,
  },
  
  // Summary
  summaryContainer: {
    flex: 1,
  },
  summarySafe: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
  summaryContent: {
    alignItems: 'center',
  },
  summaryIconWrap: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: 'rgba(16,185,129,0.15)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  summaryTitle: {
    fontSize: 28,
    fontWeight: '800',
    color: D.white,
    textAlign: 'center',
    marginBottom: 8,
  },
  summarySubtitle: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.7)',
    textAlign: 'center',
    marginBottom: 32,
  },
  summaryCard: {
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 16,
    padding: 20,
    width: '100%',
    marginBottom: 24,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
  },
  summaryLabel: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.6)',
  },
  summaryValue: {
    fontSize: 16,
    fontWeight: '700',
    color: D.white,
  },
  summaryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: D.green,
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 14,
    gap: 8,
    width: '100%',
  },
  summaryButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: D.white,
  },
  summaryBackButton: {
    marginTop: 16,
    paddingVertical: 12,
  },
  summaryBackText: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.5)',
  },
});
