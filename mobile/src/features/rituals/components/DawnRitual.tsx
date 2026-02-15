/**
 * Ritual Dawn Component
 * Tactical, execution-driven morning check-in.
 *
 * 5 phases (user-paced):
 *  1. Sunrise   — 4s animation, greeting + tagline, fires API
 *  2. Portfolio  — total value, change, top holdings
 *  3. Market     — S&P direction, sentiment, headline
 *  4. Action     — one focused suggestion
 *  5. Commitment — commit or skip, streak display
 */

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  Dimensions,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { PanGestureHandler, State } from 'react-native-gesture-handler';
import * as Speech from 'expo-speech';
import { LinearGradient } from 'expo-linear-gradient';
import * as Haptics from 'expo-haptics';
import Icon from 'react-native-vector-icons/Feather';
import { dawnRitualService } from '../services/DawnRitualService';
import logger from '../../../utils/logger';
import type {
  RitualPhase,
  RitualDawnResult,
  PortfolioSnapshot,
  MarketContext,
  ActionSuggestion,
} from '../types/RitualDawnTypes';

// ---------------------------------------------------------------------------
// Haptics helper
// ---------------------------------------------------------------------------
const triggerHaptic = (type: 'light' | 'medium' | 'success') => {
  try {
    if (type === 'light') {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    } else if (type === 'medium') {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    } else if (type === 'success') {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    }
  } catch {
    // Haptics not available
  }
};

const { width, height } = Dimensions.get('window');

const PHASES: RitualPhase[] = ['sunrise', 'portfolio', 'market', 'action', 'commitment'];
const INTERACTIVE_PHASES: RitualPhase[] = ['portfolio', 'market', 'action', 'commitment'];
const SWIPE_THRESHOLD = 50;

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------
interface DawnRitualProps {
  visible: boolean;
  onComplete?: (result: { syncedTransactions: number; actionTaken: string }) => void;
  onSkip?: () => void;
  onNavigate?: (screen: string, params?: Record<string, unknown>) => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
export const DawnRitual: React.FC<DawnRitualProps> = ({
  visible,
  onComplete,
  onSkip,
  onNavigate,
}) => {
  const [phase, setPhase] = useState<RitualPhase>('sunrise');
  const [ritualData, setRitualData] = useState<RitualDawnResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [sunriseAnimationDone, setSunriseAnimationDone] = useState(false);
  const [readAloud, setReadAloud] = useState(false);

  // Dynamic phases: skip portfolio when user has no positions
  const effectivePhases = useMemo((): RitualPhase[] => {
    if (!ritualData?.portfolio) return PHASES;
    if (ritualData.portfolio.has_portfolio === false) {
      return ['sunrise', 'market', 'action', 'commitment'];
    }
    return PHASES;
  }, [ritualData?.portfolio?.has_portfolio]);
  const effectiveInteractivePhases = useMemo(
    () => effectivePhases.filter((p) => p !== 'sunrise'),
    [effectivePhases]
  );

  // Animation values
  const sunY = useRef(new Animated.Value(height + 100)).current;
  const sunOpacity = useRef(new Animated.Value(0)).current;
  const skyGradient = useRef(new Animated.Value(0)).current;
  const contentOpacity = useRef(new Animated.Value(1)).current;

  // Track whether sunrise animation has completed
  const sunriseComplete = useRef(false);
  const dataLoaded = useRef(false);

  // -----------------------------------------------------------------------
  // Reset when visibility changes
  // -----------------------------------------------------------------------
  useEffect(() => {
    if (!visible) {
      sunY.setValue(height + 100);
      sunOpacity.setValue(0);
      skyGradient.setValue(0);
      contentOpacity.setValue(1);
      setPhase('sunrise');
      setRitualData(null);
      setLoading(false);
      setSunriseAnimationDone(false);
      sunriseComplete.current = false;
      dataLoaded.current = false;
      return;
    }

    const timer = setTimeout(() => startRitual(), 100);
    return () => clearTimeout(timer);
  }, [visible]);

  // -----------------------------------------------------------------------
  // Auto-advance from sunrise once both animation + data are ready
  // -----------------------------------------------------------------------
  const tryAdvanceFromSunrise = useCallback(() => {
    if (sunriseComplete.current && dataLoaded.current) {
      advancePhase();
    }
  }, []);

  // -----------------------------------------------------------------------
  // Start the ritual: fire animation + API concurrently
  // -----------------------------------------------------------------------
  const startRitual = async () => {
    setPhase('sunrise');
    triggerHaptic('light');
    setLoading(true);

    // Reset animation values
    sunY.setValue(height + 100);
    sunOpacity.setValue(0);
    skyGradient.setValue(0);
    contentOpacity.setValue(1);
    sunriseComplete.current = false;
    dataLoaded.current = false;

    // 1. Sunrise animation (4 seconds)
    Animated.parallel([
      Animated.timing(sunY, {
        toValue: height * 0.3,
        duration: 4000,
        useNativeDriver: true,
      }),
      Animated.timing(sunOpacity, {
        toValue: 1,
        duration: 2000,
        useNativeDriver: true,
      }),
      Animated.timing(skyGradient, {
        toValue: 1,
        duration: 4000,
        useNativeDriver: false,
      }),
    ]).start(() => {
      sunriseComplete.current = true;
      setSunriseAnimationDone(true);
      tryAdvanceFromSunrise();
    });

    // 2. Fetch ritual data concurrently
    try {
      const data = await dawnRitualService.performRitualDawn();
      setRitualData(data);
      dataLoaded.current = true;
      setLoading(false);
      tryAdvanceFromSunrise();
    } catch (error) {
      logger.error('[RitualDawn] Error fetching data:', error);
      setLoading(false);
      dataLoaded.current = true;
      tryAdvanceFromSunrise();
    }
  };

  // -----------------------------------------------------------------------
  // Phase transitions (user-paced): tap or swipe left = next, swipe right = back
  // -----------------------------------------------------------------------
  const runPhaseTransition = (nextPhase: RitualPhase) => {
    Animated.timing(contentOpacity, {
      toValue: 0,
      duration: 200,
      useNativeDriver: true,
    }).start(() => {
      setPhase(nextPhase);
      Animated.timing(contentOpacity, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }).start();
    });
  };

  const advancePhase = () => {
    triggerHaptic('light');
    const currentIdx = effectivePhases.indexOf(phase);
    if (currentIdx >= effectivePhases.length - 1) return;
    runPhaseTransition(effectivePhases[currentIdx + 1]);
  };

  const goBackPhase = () => {
    triggerHaptic('light');
    const currentIdx = effectivePhases.indexOf(phase);
    if (currentIdx <= 0) return;
    runPhaseTransition(effectivePhases[currentIdx - 1]);
  };

  const onSwipeGesture = useCallback(
    (event: { nativeEvent: { state: number; translationX: number } }) => {
      const { state: gestureState, translationX } = event.nativeEvent;
      if (gestureState !== State.END) return;
      if (translationX < -SWIPE_THRESHOLD) advancePhase();
      else if (translationX > SWIPE_THRESHOLD) goBackPhase();
    },
    [phase, effectivePhases]
  );

  // -----------------------------------------------------------------------
  // Commitment handlers
  // -----------------------------------------------------------------------
  const handleCommit = (actionTaken: string) => {
    triggerHaptic('success');
    dawnRitualService.completeRitualDawn(actionTaken, ritualData?.greeting_key ?? undefined);
    onComplete?.({
      syncedTransactions: ritualData?.transactionsSynced ?? 0,
      actionTaken,
    });
  };

  const handleActionCTA = () => {
    const target = ritualData?.action?.target_screen;
    if (target && onNavigate) {
      onNavigate(target);
    } else {
      advancePhase();
    }
  };

  // -----------------------------------------------------------------------
  // Format helpers
  // -----------------------------------------------------------------------
  const formatDollars = (n: number) => {
    const abs = Math.abs(n);
    const sign = n >= 0 ? '+' : '-';
    if (abs >= 1000) {
      return `${sign}$${(abs / 1000).toFixed(1)}k`;
    }
    return `${sign}$${abs.toFixed(2)}`;
  };

  const formatPercent = (n: number) => {
    const sign = n >= 0 ? '+' : '';
    return `${sign}${n.toFixed(2)}%`;
  };

  const formatValue = (n: number) => {
    if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`;
    if (n >= 1_000) return `$${(n / 1_000).toFixed(1)}k`;
    return `$${n.toFixed(2)}`;
  };

  // -----------------------------------------------------------------------
  // Read aloud: text for current phase
  // -----------------------------------------------------------------------
  const getSpeechText = useCallback((p: RitualPhase): string => {
    if (!ritualData) return '';
    switch (p) {
      case 'sunrise':
        return [ritualData.greeting || '', ritualData.tagline || ''].filter(Boolean).join('. ');
      case 'portfolio': {
        const port = ritualData.portfolio;
        if (!port?.has_portfolio) return 'No positions yet. Your first investment is the hardest — and the most important.';
        const change = `${port.change_dollars >= 0 ? 'Up' : 'Down'} ${formatDollars(port.change_dollars)}, ${formatPercent(port.change_percent)}.`;
        return `Your portfolio: ${formatValue(port.total_value)}. ${change}`;
      }
      case 'market': {
        const m = ritualData.market;
        if (!m) return '';
        const dir = m.sp500_direction === 'up' ? 'up' : m.sp500_direction === 'down' ? 'down' : 'flat';
        return `${m.headline || ''} S&P 500 is ${dir} ${m.sp500_change_percent?.toFixed(2) ?? 0} percent.`;
      }
      case 'action': {
        const a = ritualData.action;
        if (!a) return '';
        return `${a.headline || a.title || ''}. ${a.cta_text || ''}`;
      }
      case 'commitment':
        return ritualData.streak
          ? `You're on a ${ritualData.streak} day streak. Choose your commitment.`
          : 'Choose your commitment.';
      default:
        return '';
    }
  }, [ritualData]);

  // Speak current phase when readAloud is on and phase/ritualData change
  useEffect(() => {
    if (!readAloud) return;
    const text = getSpeechText(phase);
    if (!text.trim()) return;
    Speech.speak(text, { rate: 0.92, language: 'en-US' });
    return () => {
      Speech.stop();
    };
  }, [readAloud, phase, getSpeechText]);

  // Stop speech when readAloud turns off or component unmounts
  useEffect(() => {
    if (!readAloud) Speech.stop();
  }, [readAloud]);

  // -----------------------------------------------------------------------
  // Render helpers for each phase
  // -----------------------------------------------------------------------
  const renderSunrise = () => (
    <View style={styles.phaseContainer}>
      <Text style={styles.greetingText}>
        {ritualData?.greeting || 'Ritual Dawn'}
      </Text>
      <Text style={styles.taglineText}>
        {ritualData?.tagline || 'Your tactical morning check-in.'}
      </Text>
      {sunriseAnimationDone && loading && (
        <View style={styles.loadingAfterSunrise}>
          <ActivityIndicator size="small" color="#FFFFFF" />
          <Text style={styles.loadingAfterSunriseText}>Loading your briefing…</Text>
        </View>
      )}
    </View>
  );

  const renderPortfolio = () => {
    const p: PortfolioSnapshot = ritualData?.portfolio ?? {
      total_value: 0, previous_total_value: 0,
      change_dollars: 0, change_percent: 0,
      top_holdings: [], holdings_count: 0, has_portfolio: false,
    };

    if (!p.has_portfolio) {
      return (
        <View style={styles.phaseCard}>
          <Icon name="briefcase" size={40} color="#FFFFFF" />
          <Text style={styles.cardTitle}>No Positions Yet</Text>
          <Text style={styles.cardDetail}>
            Your first investment is the hardest — and the most important.
          </Text>
        </View>
      );
    }

    const changeColor = p.change_dollars >= 0 ? '#34C759' : '#FF3B30';

    return (
      <View style={styles.phaseCard}>
        <Text style={styles.cardLabel}>YOUR PORTFOLIO</Text>
        <Text style={styles.portfolioValue}>{formatValue(p.total_value)}</Text>
        <Text style={[styles.portfolioChange, { color: changeColor }]}>
          {formatDollars(p.change_dollars)}  ({formatPercent(p.change_percent)})
        </Text>

        {p.top_holdings.length > 0 && (
          <View style={styles.holdingsContainer}>
            {p.top_holdings.map((h) => {
              const hColor = h.change_percent >= 0 ? '#34C759' : '#FF3B30';
              return (
                <View key={h.symbol} style={styles.holdingRow}>
                  <Text style={styles.holdingSymbol}>{h.symbol}</Text>
                  <Text style={styles.holdingName} numberOfLines={1}>{h.name}</Text>
                  <Text style={[styles.holdingChange, { color: hColor }]}>
                    {formatPercent(h.change_percent)}
                  </Text>
                </View>
              );
            })}
          </View>
        )}

        <Text style={styles.holdingsCount}>
          {p.holdings_count} position{p.holdings_count !== 1 ? 's' : ''} total
        </Text>
      </View>
    );
  };

  const renderMarket = () => {
    const m: MarketContext = ritualData?.market ?? {
      sp500_change_percent: 0, sp500_direction: 'flat',
      market_sentiment: 'neutral', notable_indices: [],
      headline: 'Market data is currently unavailable.',
      volatility_level: 'moderate',
    };

    const dirIcon = m.sp500_direction === 'up'
      ? 'trending-up'
      : m.sp500_direction === 'down'
        ? 'trending-down'
        : 'minus';
    const dirColor = m.sp500_direction === 'up'
      ? '#34C759'
      : m.sp500_direction === 'down'
        ? '#FF3B30'
        : '#8E8E93';

    const sentimentColors: Record<string, string> = {
      bullish: '#34C759',
      bearish: '#FF3B30',
      neutral: '#8E8E93',
    };

    return (
      <View style={styles.phaseCard}>
        <Text style={styles.cardLabel}>MARKET OVERVIEW</Text>

        <View style={styles.marketRow}>
          <Icon name={dirIcon} size={32} color={dirColor} />
          <View style={{ marginLeft: 12 }}>
            <Text style={styles.marketIndex}>S&P 500</Text>
            <Text style={[styles.marketChange, { color: dirColor }]}>
              {formatPercent(m.sp500_change_percent)}
            </Text>
          </View>

          <View style={[
            styles.sentimentBadge,
            { backgroundColor: sentimentColors[m.market_sentiment] || '#8E8E93' },
          ]}>
            <Text style={styles.sentimentText}>
              {m.market_sentiment.charAt(0).toUpperCase() + m.market_sentiment.slice(1)}
            </Text>
          </View>
        </View>

        <Text style={styles.marketHeadline}>{m.headline}</Text>

        {m.volatility_level === 'elevated' && (
          <View style={styles.volatilityBadge}>
            <Icon name="alert-triangle" size={14} color="#FF9500" />
            <Text style={styles.volatilityText}>Elevated volatility</Text>
          </View>
        )}
      </View>
    );
  };

  const renderAction = () => {
    const a: ActionSuggestion = ritualData?.action ?? {
      action_type: 'no_action',
      headline: 'Start your day with awareness.',
      detail: 'Review your portfolio when you\'re ready.',
      action_label: 'Open portfolio',
      target_screen: null,
      urgency: 'low',
    };

    const urgencyColors: Record<string, string> = {
      high: '#FF3B30',
      medium: '#FF9500',
      low: '#34C759',
    };

    const iconMap: Record<string, string> = {
      risk_flag: 'alert-triangle',
      opportunity: 'zap',
      rebalance: 'sliders',
      review: 'eye',
      no_action: 'check-circle',
    };

    return (
      <View style={styles.phaseCard}>
        <Text style={styles.cardLabel}>TODAY'S ACTION</Text>

        <View style={styles.actionIconRow}>
          <View style={[
            styles.actionIconCircle,
            { backgroundColor: urgencyColors[a.urgency] || '#34C759' },
          ]}>
            <Icon
              name={iconMap[a.action_type] || 'check-circle'}
              size={24}
              color="#FFFFFF"
            />
          </View>
        </View>

        <Text style={styles.actionHeadline}>{a.headline}</Text>
        <Text style={styles.actionDetail}>{a.detail}</Text>

        {a.action_type !== 'no_action' && a.target_screen && (
          <TouchableOpacity style={styles.ctaButton} onPress={handleActionCTA}>
            <Text style={styles.ctaButtonText}>{a.action_label}</Text>
            <Icon name="arrow-right" size={16} color="#FFFFFF" />
          </TouchableOpacity>
        )}
      </View>
    );
  };

  const renderCommitment = () => {
    const actionLabel = ritualData?.action?.action_label || 'Review portfolio';
    const streak = ritualData?.streak ?? 0;

    return (
      <View style={styles.phaseCard}>
        <Text style={styles.cardLabel}>YOUR COMMITMENT</Text>

        {streak > 0 && (
          <View style={styles.streakBadge}>
            <Icon name="zap" size={16} color="#FF9500" />
            <Text style={styles.streakText}>Day {streak}</Text>
          </View>
        )}

        <Text style={styles.commitQuestion}>
          What will you do today?
        </Text>

        <TouchableOpacity
          style={styles.commitButton}
          onPress={() => handleCommit(actionLabel)}
        >
          <Text style={styles.commitButtonText}>
            I'll {actionLabel.toLowerCase()} today
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.noActionButton}
          onPress={() => handleCommit('no_action')}
        >
          <Text style={styles.noActionButtonText}>No action today</Text>
        </TouchableOpacity>
      </View>
    );
  };

  // -----------------------------------------------------------------------
  // Main render
  // -----------------------------------------------------------------------
  if (!visible) return null;

  const showAdvanceHint = ['portfolio', 'market', 'action'].includes(phase);

  return (
    <View style={styles.container}>
      {/* Sky Gradient Background */}
      <View style={styles.skyContainer}>
        <LinearGradient
          colors={['#0a0a1a', '#1a1a3a', '#2a2a5a']}
          style={StyleSheet.absoluteFill}
          start={{ x: 0, y: 0 }}
          end={{ x: 0, y: 1 }}
        />
      </View>

      {/* Sunrise Overlay */}
      <Animated.View style={[styles.sunriseOverlay, { opacity: skyGradient }]}>
        <LinearGradient
          colors={['#ff6b6b', '#ffa500', '#ffd700', '#87ceeb']}
          style={StyleSheet.absoluteFill}
          start={{ x: 0, y: 1 }}
          end={{ x: 0, y: 0 }}
        />
      </Animated.View>

      {/* Sun */}
      <Animated.View
        style={[
          styles.sun,
          { transform: [{ translateY: sunY }], opacity: sunOpacity },
        ]}
      >
        <View style={styles.sunCore} />
        <View style={styles.sunGlow} />
      </Animated.View>

      {/* Content + swipe area: swipe left = next, swipe right = back */}
      <PanGestureHandler
        onHandlerStateChange={onSwipeGesture}
        activeOffsetX={[-20, 20]}
        failOffsetY={[-15, 15]}
      >
        <View style={styles.swipeableArea}>
          <Animated.View style={[styles.contentContainer, { opacity: contentOpacity }]}>
            {phase === 'sunrise' && renderSunrise()}
            {phase === 'portfolio' && renderPortfolio()}
            {phase === 'market' && renderMarket()}
            {phase === 'action' && renderAction()}
            {phase === 'commitment' && renderCommitment()}
          </Animated.View>
          {/* Tap to advance overlay */}
          {showAdvanceHint && (
            <TouchableOpacity
              style={styles.advanceOverlay}
              activeOpacity={0.8}
              onPress={advancePhase}
            >
              <Text style={styles.advanceHint}>Tap or swipe to continue</Text>
            </TouchableOpacity>
          )}
        </View>
      </PanGestureHandler>

      {/* Phase dots */}
      {phase !== 'sunrise' && (
        <View style={styles.phaseDots}>
          {effectiveInteractivePhases.map((p) => (
            <View
              key={p}
              style={[styles.dot, phase === p && styles.dotActive]}
            />
          ))}
        </View>
      )}

      {/* Read aloud toggle: show when we have data */}
      {ritualData && (
        <TouchableOpacity
          style={[styles.readAloudButton, readAloud && styles.readAloudButtonActive]}
          onPress={() => setReadAloud((v) => !v)}
        >
          <Icon name="volume-2" size={20} color={readAloud ? '#0a0a1a' : '#FFFFFF'} />
          <Text style={[styles.readAloudText, readAloud && styles.readAloudTextActive]}>
            Read aloud
          </Text>
        </TouchableOpacity>
      )}

      {/* Skip button */}
      {phase !== 'commitment' && (
        <TouchableOpacity style={styles.skipButton} onPress={onSkip}>
          <Text style={styles.skipText}>Skip</Text>
        </TouchableOpacity>
      )}
    </View>
  );
};

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------
const styles = StyleSheet.create({
  container: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: '#0a0a1a',
  },
  skyContainer: {
    ...StyleSheet.absoluteFillObject,
  },
  sunriseOverlay: {
    ...StyleSheet.absoluteFillObject,
  },
  sun: {
    position: 'absolute',
    left: width / 2 - 50,
    width: 100,
    height: 100,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sunCore: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#ffd700',
    shadowColor: '#ffd700',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 1,
    shadowRadius: 30,
    elevation: 10,
  },
  sunGlow: {
    position: 'absolute',
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: '#ffa500',
    opacity: 0.5,
  },

  // Content
  swipeableArea: {
    flex: 1,
  },
  contentContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
    paddingTop: 80,
  },
  phaseContainer: {
    alignItems: 'center',
    gap: 12,
  },

  // Sunrise phase
  greetingText: {
    fontSize: 28,
    fontWeight: '700',
    color: '#FFFFFF',
    textAlign: 'center',
    textShadowColor: 'rgba(0, 0, 0, 0.5)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  taglineText: {
    fontSize: 18,
    color: '#FFFFFF',
    opacity: 0.85,
    textAlign: 'center',
    fontStyle: 'italic',
    marginTop: 8,
  },
  loadingAfterSunrise: {
    marginTop: 24,
    alignItems: 'center',
    gap: 12,
  },
  loadingAfterSunriseText: {
    fontSize: 14,
    color: '#FFFFFF',
    opacity: 0.8,
  },

  // Shared card
  phaseCard: {
    width: width - 48,
    backgroundColor: 'rgba(0, 0, 0, 0.55)',
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
  },
  cardLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF',
    opacity: 0.5,
    letterSpacing: 1.5,
    marginBottom: 16,
  },
  cardTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#FFFFFF',
    marginTop: 12,
    textAlign: 'center',
  },
  cardDetail: {
    fontSize: 15,
    color: '#FFFFFF',
    opacity: 0.8,
    textAlign: 'center',
    marginTop: 8,
    lineHeight: 22,
  },

  // Portfolio phase
  portfolioValue: {
    fontSize: 36,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  portfolioChange: {
    fontSize: 18,
    fontWeight: '600',
    marginTop: 4,
  },
  holdingsContainer: {
    width: '100%',
    marginTop: 20,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(255, 255, 255, 0.15)',
    paddingTop: 16,
  },
  holdingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 6,
  },
  holdingSymbol: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
    width: 60,
  },
  holdingName: {
    fontSize: 13,
    color: '#FFFFFF',
    opacity: 0.6,
    flex: 1,
    marginRight: 8,
  },
  holdingChange: {
    fontSize: 14,
    fontWeight: '600',
    width: 70,
    textAlign: 'right',
  },
  holdingsCount: {
    fontSize: 12,
    color: '#FFFFFF',
    opacity: 0.4,
    marginTop: 12,
  },

  // Market phase
  marketRow: {
    flexDirection: 'row',
    alignItems: 'center',
    width: '100%',
    marginBottom: 16,
  },
  marketIndex: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  marketChange: {
    fontSize: 20,
    fontWeight: '700',
  },
  sentimentBadge: {
    marginLeft: 'auto',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  sentimentText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  marketHeadline: {
    fontSize: 15,
    color: '#FFFFFF',
    opacity: 0.85,
    textAlign: 'center',
    lineHeight: 22,
  },
  volatilityBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 12,
    paddingHorizontal: 10,
    paddingVertical: 4,
    backgroundColor: 'rgba(255, 149, 0, 0.2)',
    borderRadius: 8,
    gap: 6,
  },
  volatilityText: {
    fontSize: 12,
    color: '#FF9500',
    fontWeight: '600',
  },

  // Action phase
  actionIconRow: {
    marginBottom: 16,
  },
  actionIconCircle: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  actionHeadline: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
    textAlign: 'center',
    marginBottom: 8,
  },
  actionDetail: {
    fontSize: 15,
    color: '#FFFFFF',
    opacity: 0.8,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 16,
  },
  ctaButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#007AFF',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 12,
    gap: 8,
  },
  ctaButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },

  // Commitment phase
  streakBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 149, 0, 0.2)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    gap: 6,
    marginBottom: 20,
  },
  streakText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FF9500',
  },
  commitQuestion: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
    textAlign: 'center',
    marginBottom: 24,
  },
  commitButton: {
    width: '100%',
    backgroundColor: '#34C759',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 12,
  },
  commitButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  noActionButton: {
    width: '100%',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.3)',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  noActionButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    opacity: 0.7,
  },

  // Navigation
  advanceOverlay: {
    position: 'absolute',
    bottom: 100,
    left: 0,
    right: 0,
    alignItems: 'center',
  },
  advanceHint: {
    fontSize: 13,
    color: '#FFFFFF',
    opacity: 0.4,
  },
  phaseDots: {
    position: 'absolute',
    bottom: 60,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 8,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.25)',
  },
  dotActive: {
    backgroundColor: '#FFFFFF',
    width: 20,
  },
  skipButton: {
    position: 'absolute',
    top: 60,
    right: 20,
    padding: 12,
  },
  skipText: {
    color: '#FFFFFF',
    opacity: 0.7,
    fontSize: 16,
  },
  readAloudButton: {
    position: 'absolute',
    bottom: 100,
    left: 20,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.15)',
  },
  readAloudButtonActive: {
    backgroundColor: '#FFFFFF',
  },
  readAloudText: {
    color: '#FFFFFF',
    fontSize: 14,
    opacity: 0.9,
  },
  readAloudTextActive: {
    color: '#0a0a1a',
    opacity: 1,
  },
});
