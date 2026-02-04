import React, { useEffect, useMemo, useRef, useState, useCallback, memo } from "react";
import {
  View,
  Text,
  StyleSheet,
  Modal,
  Pressable,
  FlatList,
  ListRenderItemInfo,
  Dimensions,
  Animated,
  StatusBar,
  ActivityIndicator,
  PanResponder,
} from "react-native";
import { Audio } from "expo-av";
import * as Speech from "expo-speech";
import * as Haptics from "expo-haptics";
import type { StockMoment, MomentCategory } from "./ChartWithMoments";
import { LinearGradient } from "expo-linear-gradient";
import logger from "../../utils/logger";

// Optional: Share moment as image (requires react-native-view-shot + expo-sharing)
let captureRef: ((view: React.Component | null, options?: { format?: string; quality?: number; result?: string }) => Promise<string>) | null = null;
let Sharing: typeof import("expo-sharing") | null = null;
try {
  const v = require("react-native-view-shot");
  captureRef = v.captureRef ?? v.default?.captureRef ?? null;
} catch {
  captureRef = null;
}
try {
  const Sh = require("expo-sharing");
  Sharing = Sh.default ?? Sh;
} catch {
  Sharing = null;
}

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

export type MomentAnalyticsEvent = {
  type:
    | "story_open"
    | "story_close"
    | "moment_change"
    | "moment_play_toggle"
    | "moment_skip_next"
    | "moment_skip_prev";
  symbol: string;
  momentId?: string;
  index?: number;
  fromIndex?: number;
  toIndex?: number;
  totalMoments: number;
  listenedCount?: number;
};

interface ExtendedMoment extends StockMoment {
  isIntro?: boolean;
}

interface MomentStoryPlayerProps {
  visible: boolean;
  symbol: string;
  moments: StockMoment[];
  initialIndex?: number;
  onClose?: () => void;
  onMomentChange?: (moment: StockMoment | null) => void;
  onAnalyticsEvent?: (event: MomentAnalyticsEvent) => void;
  /** Custom TTS service. If provided, expo-speech is not used. */
  speakFn?: (text: string, moment: StockMoment, onComplete?: () => void) => Promise<void>;
  stopFn?: () => void;
  /** Cinematic intro slide before first moment. */
  enableIntro?: boolean;
  introText?: string;
  /** When true, show a "Sample" badge so users know moments are placeholder, not symbol-specific. */
  isSampleData?: boolean;
}

interface CategoryStyle {
  color: string;
  gradient: readonly [string, string];
  icon: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────────────────────────────────────

const { width: SCREEN_WIDTH } = Dimensions.get("window");
const CARD_WIDTH = Math.min(340, SCREEN_WIDTH * 0.9);
const CARD_MARGIN = 20;
const ITEM_LAYOUT_LENGTH = CARD_WIDTH + CARD_MARGIN;

// TTS timing
const SPEECH_TIMEOUT_BASE_MS = 200;
const SPEECH_MIN_DURATION_MS = 5000;
const SPEECH_MAX_DURATION_MS = 25000;
const TTS_LOADING_TIMEOUT_MS = 1500;
const TTS_ERROR_FALLBACK_MS = 2000;

const WEALTH_ORACLE_VOICE_OPTIONS: Speech.SpeechOptions = {
  language: "en-US",
  rate: 0.9,
  pitch: 1.05,
};

const CATEGORY_STYLES: Record<string, CategoryStyle> = {
  EARNINGS: { color: "#10B981", gradient: ["#10B981", "#059669"] as const, icon: "💰" },
  NEWS: { color: "#3B82F6", gradient: ["#3B82F6", "#2563EB"] as const, icon: "📰" },
  INSIDER: { color: "#F59E0B", gradient: ["#F59E0B", "#D97706"] as const, icon: "👤" },
  MACRO: { color: "#8B5CF6", gradient: ["#8B5CF6", "#7C3AED"] as const, icon: "🌍" },
  SENTIMENT: { color: "#EF4444", gradient: ["#EF4444", "#DC2626"] as const, icon: "😊" },
  OTHER: { color: "#6B7280", gradient: ["#6B7280", "#4B5563"] as const, icon: "•" },
} as const;

// ─────────────────────────────────────────────────────────────────────────────
// Utility functions
// ─────────────────────────────────────────────────────────────────────────────

const getCategoryStyle = (category: string, isIntro: boolean): CategoryStyle => {
  if (isIntro) return CATEGORY_STYLES.OTHER;
  return CATEGORY_STYLES[category] ?? CATEGORY_STYLES.OTHER;
};

const calculateSpeechDuration = (text: string): number => {
  const wordCount = text.split(/\s+/).length;
  return Math.min(
    SPEECH_MAX_DURATION_MS,
    Math.max(SPEECH_MIN_DURATION_MS, wordCount * SPEECH_TIMEOUT_BASE_MS)
  );
};

const clampIndex = (index: number, length: number): number => {
  if (length === 0) return 0;
  return Math.max(0, Math.min(index, length - 1));
};

const triggerHaptic = (style: Haptics.ImpactFeedbackStyle = Haptics.ImpactFeedbackStyle.Light) => {
  Haptics.impactAsync(style).catch(() => {});
};

const triggerSuccessHaptic = () => {
  Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
};

// ─────────────────────────────────────────────────────────────────────────────
// Memoized Card Component
// ─────────────────────────────────────────────────────────────────────────────

interface MomentCardProps {
  item: ExtendedMoment;
  isActive: boolean;
  listened: boolean;
  isSampleData?: boolean;
}

const MomentCard = memo(React.forwardRef<View, MomentCardProps>(function MomentCardInner({ item, isActive, listened, isSampleData }, ref) {
  const catStyle = getCategoryStyle(item.category, !!item.isIntro);

  return (
    <View ref={ref} collapsable={false} style={styles.cardWrapper}>
      <Animated.View
        style={[
          styles.card,
          isActive && styles.cardActive,
          item.isIntro && styles.cardIntro,
        ]}
        accessible
        accessibilityRole="text"
        accessibilityLabel={`${item.category} moment: ${item.title}. ${item.deepSummary.substring(0, 100)}...`}
      >
        <View style={styles.cardHeaderRow}>
          <LinearGradient
            colors={catStyle.gradient as [string, string]}
            style={styles.categoryIconContainer}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
          >
            <Text style={styles.categoryIcon}>{catStyle.icon}</Text>
          </LinearGradient>
          <View style={styles.cardCategoryContainer}>
            <Text
              style={[styles.cardCategory, { color: catStyle.color }]}
              aria-label={`${item.category} category`}
            >
              {item.isIntro ? "INTRO" : item.category}
            </Text>
          </View>
          {listened && (
            <View style={styles.listenedIndicator}>
              <Text style={styles.cardListenedDot} aria-hidden>✓</Text>
            </View>
          )}
        </View>
        <Text style={styles.cardTitle} numberOfLines={2}>{item.title}</Text>
        <Text style={styles.cardSummary} numberOfLines={6}>{item.deepSummary}</Text>
        <View style={styles.shareFooter}>
          <Text style={styles.brandText}>Wealth Oracle</Text>
          {isSampleData && <Text style={styles.sampleStamp}>SAMPLE DATA</Text>}
          <Text style={styles.symbolStamp}>{item.symbol?.toUpperCase() ?? ""}</Text>
        </View>
      </Animated.View>
    </View>
  );
}));

MomentCard.displayName = "MomentCard";

// ─────────────────────────────────────────────────────────────────────────────
// Custom Hooks
// ─────────────────────────────────────────────────────────────────────────────

/** Stable key for mock→real rehydration (title + timestamp) */
const getStableKey = (m: StockMoment | ExtendedMoment): string =>
  `${m.title}_${m.timestamp}`;

/**
 * Hook to manage story moments with optional intro.
 * Returns getStableKey so caller can rehydrate listenedIds when data swaps (mock→real).
 */
const useStoryMoments = (
  moments: StockMoment[],
  symbol: string,
  enableIntro: boolean,
  introText?: string
) => {
  const sortedMoments = useMemo(
    () => [...moments].sort((a, b) =>
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    ),
    [moments]
  );

  const introMoment = useMemo<ExtendedMoment | null>(() => {
    if (!enableIntro || !sortedMoments.length) return null;

    const text = introText ||
      `Here's the story behind ${symbol.toUpperCase()}'s recent moves. I'll walk you through each key moment on the chart.`;

    return {
      id: `INTRO_${symbol}`,
      symbol,
      timestamp: sortedMoments[0]?.timestamp ?? new Date().toISOString(),
      category: "OTHER" as MomentCategory,
      title: `The story behind ${symbol.toUpperCase()}`,
      quickSummary: text,
      deepSummary: text,
      isIntro: true,
    };
  }, [enableIntro, sortedMoments, symbol, introText]);

  const storyMoments = useMemo<ExtendedMoment[]>(() => {
    if (introMoment) return [introMoment, ...sortedMoments];
    return sortedMoments;
  }, [introMoment, sortedMoments]);

  return { sortedMoments, introMoment, storyMoments, getStableKey };
};

/**
 * Hook to manage TTS speech
 */
const useSpeech = (
  speakFn?: MomentStoryPlayerProps["speakFn"],
  stopFn?: MomentStoryPlayerProps["stopFn"]
) => {
  const speechTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const loadingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const clearTimeouts = useCallback(() => {
    if (speechTimeoutRef.current) {
      clearTimeout(speechTimeoutRef.current);
      speechTimeoutRef.current = null;
    }
    if (loadingTimeoutRef.current) {
      clearTimeout(loadingTimeoutRef.current);
      loadingTimeoutRef.current = null;
    }
  }, []);

  const stopSpeech = useCallback(() => {
    clearTimeouts();
    if (stopFn) {
      stopFn();
    } else {
      Speech.stop();
    }
  }, [stopFn, clearTimeouts]);

  const speak = useCallback(async (
    text: string,
    moment: StockMoment,
    onComplete: () => void,
    setLoading: (loading: boolean) => void
  ) => {
    if (!isMountedRef.current) return;
    setLoading(true);

    const safeComplete = () => {
      if (isMountedRef.current) onComplete();
    };
    const safeSetLoading = (v: boolean) => {
      if (isMountedRef.current) setLoading(v);
    };

    loadingTimeoutRef.current = setTimeout(() => {
      safeSetLoading(false);
    }, TTS_LOADING_TIMEOUT_MS);

    try {
      if (speakFn) {
        speakFn(text, moment, safeComplete)
          .catch((error) => {
            logger.warn('[MomentStoryPlayer] TTS error:', error);
            setTimeout(safeComplete, TTS_ERROR_FALLBACK_MS);
          })
          .finally(() => {
            clearTimeouts();
            safeSetLoading(false);
          });
        return;
      }

      clearTimeouts();
      safeSetLoading(false);
      Speech.speak(text, {
        ...WEALTH_ORACLE_VOICE_OPTIONS,
        onDone: () => isMountedRef.current && onComplete(),
        onError: () => isMountedRef.current && onComplete(),
      });
    } catch (error) {
      logger.warn('[MomentStoryPlayer] Speech error:', error);
      clearTimeouts();
      safeSetLoading(false);
      if (isMountedRef.current) onComplete();
    }
  }, [speakFn, clearTimeouts]);

  return { speak, stopSpeech, speechTimeoutRef, clearTimeouts };
};

// ─────────────────────────────────────────────────────────────────────────────
// Main Component
// ─────────────────────────────────────────────────────────────────────────────

const MomentStoryPlayer: React.FC<MomentStoryPlayerProps> = ({
  visible,
  symbol,
  moments,
  initialIndex = 0,
  onClose,
  onMomentChange,
  onAnalyticsEvent,
  speakFn,
  stopFn,
  enableIntro = true,
  introText,
  isSampleData = false,
}) => {
  // State
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isTTSLoading, setIsTTSLoading] = useState(false);
  const [listenedIds, setListenedIds] = useState<Set<string>>(new Set());

  // Refs
  const listRef = useRef<FlatList<ExtendedMoment>>(null);
  const slideAnim = useRef(new Animated.Value(0)).current;
  const panY = useRef(new Animated.Value(0)).current;
  const previousIndexRef = useRef(0);
  const cardRefs = useRef<Record<number, View | null>>({});
  const listenedStableKeysRef = useRef<Set<string>>(new Set());

  // Custom hooks
  const { sortedMoments, introMoment, storyMoments, getStableKey } = useStoryMoments(
    moments, symbol, enableIntro, introText
  );
  const { speak, stopSpeech, speechTimeoutRef, clearTimeouts } = useSpeech(speakFn, stopFn);

  // Derived values
  const totalRealMoments = sortedMoments.length;
  const safeCurrentIndex = clampIndex(currentIndex, storyMoments.length);
  const currentExtended = storyMoments[safeCurrentIndex] ?? null;
  const currentMomentForChart = currentExtended?.isIntro ? null : currentExtended;
  const listenedCount = listenedIds.size;

  // Correct initial scroll when modal opens so list doesn't flash then jump
  const initialScrollIndexWhenVisible = useMemo(() => {
    if (!visible || !storyMoments.length) return 0;
    return enableIntro ? 0 : clampIndex(initialIndex, storyMoments.length);
  }, [visible, storyMoments.length, enableIntro, initialIndex]);

  // ─────────────────────────────────────────────────────────────────────────
  // Analytics helper
  // ─────────────────────────────────────────────────────────────────────────

  const fireAnalytics = useCallback((event: MomentAnalyticsEvent) => {
    onAnalyticsEvent?.(event);
  }, [onAnalyticsEvent]);

  const getAnalyticsIndex = useCallback((index: number): number => {
    return introMoment && index > 0 ? index - 1 : index;
  }, [introMoment]);

  // Audio ducking: lower background music/podcasts while Oracle speaks
  const configureAudioSession = useCallback(async (active: boolean) => {
    try {
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: false,
        playsInSilentModeIOS: active,
        staysActiveInBackground: false,
        shouldDuckAndroid: active,
        playThroughEarpieceAndroid: false,
      });
    } catch (error) {
      logger.warn('[MomentStoryPlayer] Audio session error:', error);
    }
  }, []);

  // ─────────────────────────────────────────────────────────────────────────
  // Effects
  // ─────────────────────────────────────────────────────────────────────────

  // Clamp currentIndex when storyMoments changes
  useEffect(() => {
    if (!storyMoments.length) {
      setCurrentIndex(0);
      return;
    }
    const clamped = clampIndex(currentIndex, storyMoments.length);
    if (clamped !== currentIndex) {
      setCurrentIndex(clamped);
    }
  }, [storyMoments.length, currentIndex]);

  // Modal animation (reset pan when opening so swipe-to-dismiss starts clean)
  useEffect(() => {
    if (visible) {
      slideAnim.setValue(0);
      panY.setValue(0);
    } else {
      Animated.timing(slideAnim, {
        toValue: 400,
        duration: 150,
        useNativeDriver: true,
      }).start();
    }
  }, [visible, slideAnim, panY]);

  // Status bar
  useEffect(() => {
    if (visible) {
      StatusBar.setBarStyle("dark-content");
      StatusBar.setBackgroundColor?.("transparent", false);
    }
    return () => {
      StatusBar.setBarStyle("default");
    };
  }, [visible]);

  // Audio ducking when story mode opens/closes
  useEffect(() => {
    if (visible) {
      configureAudioSession(true);
    } else {
      configureAudioSession(false);
    }
  }, [visible, configureAudioSession]);

  // Scroll and notify on index change (with previousIndex for accurate analytics)
  useEffect(() => {
    if (!visible || !storyMoments.length) return;

    const safeIndex = clampIndex(currentIndex, storyMoments.length);
    const fromIndex = previousIndexRef.current;

    // Scroll to current card
    requestAnimationFrame(() => {
      try {
        listRef.current?.scrollToIndex({
          index: safeIndex,
          animated: true,
          viewPosition: 0.5,
        });
      } catch {
        listRef.current?.scrollToOffset({
          offset: safeIndex * ITEM_LAYOUT_LENGTH,
          animated: true,
        });
      }
    });

    onMomentChange?.(currentMomentForChart);

    if (currentMomentForChart && fromIndex !== safeIndex) {
      fireAnalytics({
        type: "moment_change",
        symbol,
        momentId: currentMomentForChart.id,
        index: getAnalyticsIndex(currentIndex),
        fromIndex: getAnalyticsIndex(fromIndex),
        toIndex: getAnalyticsIndex(safeIndex),
        totalMoments: totalRealMoments,
      });
    }

    previousIndexRef.current = safeIndex;
    triggerHaptic();
  }, [visible, currentIndex, storyMoments.length, currentMomentForChart, onMomentChange, symbol, totalRealMoments, fireAnalytics, getAnalyticsIndex]);

  // Rehydrate listenedIds when moments change (mock→real) so checkmarks persist
  useEffect(() => {
    if (listenedStableKeysRef.current.size === 0) return;
    setListenedIds((prev) => {
      const next = new Set(prev);
      storyMoments.forEach((m) => {
        if (!m.isIntro && listenedStableKeysRef.current.has(getStableKey(m)))
          next.add(m.id);
      });
      return next;
    });
  }, [moments, storyMoments, getStableKey]);

  // Reset state on visibility change
  useEffect(() => {
    if (!visible) {
      stopSpeech();
      setIsPlaying(false);
      setListenedIds(new Set());
      listenedStableKeysRef.current = new Set();
      setCurrentIndex(0);
      setIsTTSLoading(false);
      return;
    }

    // Initialize on open
    const maxIndex = storyMoments.length - 1;
    const startIndex = introMoment ? 0 : clampIndex(initialIndex, maxIndex + 1);

    setCurrentIndex(startIndex);
    setListenedIds(new Set());
    setIsPlaying(true);
    setIsTTSLoading(false);
    previousIndexRef.current = startIndex;

    // Fire analytics asynchronously
    queueMicrotask(() => {
      fireAnalytics({
        type: "story_open",
        symbol,
        totalMoments: totalRealMoments,
      });
    });

    return () => stopSpeech();
  }, [visible, initialIndex, symbol, totalRealMoments, introMoment, storyMoments.length, stopSpeech, fireAnalytics]);

  // ─────────────────────────────────────────────────────────────────────────
  // Speech handlers
  // ─────────────────────────────────────────────────────────────────────────

  const handleSpeechComplete = useCallback(() => {
    if (!visible || !currentExtended) return;

    // Mark as listened (if not intro); store stable key for mock→real rehydration
    if (!currentExtended.isIntro) {
      listenedStableKeysRef.current.add(getStableKey(currentExtended));
      setListenedIds(prev => new Set(prev).add(currentExtended.id));
    }

    if (!isPlaying) return;

    // Advance to next or stop
    setCurrentIndex(prev => {
      const next = prev + 1;
      if (next >= storyMoments.length) {
        setIsPlaying(false);
        triggerSuccessHaptic();
        return prev;
      }
      return next;
    });
  }, [visible, currentExtended, isPlaying, storyMoments.length, getStableKey]);

  // TTS for current slide
  useEffect(() => {
    if (!visible || !currentExtended || !isPlaying) {
      stopSpeech();
      return;
    }

    stopSpeech();

    const text = currentExtended.deepSummary;
    const forMoment: StockMoment = currentMomentForChart ?? {
      ...currentExtended,
      category: "OTHER" as MomentCategory,
    };

    // Start TTS asynchronously
    queueMicrotask(() => {
      speak(text, forMoment, handleSpeechComplete, setIsTTSLoading).catch(() => {
        logger.warn('[MomentStoryPlayer] TTS failed, continuing');
      });
    });

    // Fallback timeout for expo-speech only
    if (!speakFn) {
      const duration = calculateSpeechDuration(text);
      speechTimeoutRef.current = setTimeout(() => {
        stopSpeech();
        handleSpeechComplete();
      }, duration);
    }

    return () => {
      stopSpeech();
      clearTimeouts();
    };
  }, [visible, isPlaying, currentExtended, currentMomentForChart, speak, stopSpeech, handleSpeechComplete, speakFn, speechTimeoutRef, clearTimeouts]);

  // ─────────────────────────────────────────────────────────────────────────
  // User interaction handlers
  // ─────────────────────────────────────────────────────────────────────────

  const handleClose = useCallback(() => {
    stopSpeech();
    setIsPlaying(false);

    fireAnalytics({
      type: "story_close",
      symbol,
      totalMoments: totalRealMoments,
      listenedCount,
    });

    onMomentChange?.(null);
    onClose?.();
  }, [stopSpeech, fireAnalytics, symbol, totalRealMoments, listenedCount, onMomentChange, onClose]);

  // When user starts swiping cards manually, stop TTS so voice doesn't overlap
  const handleScrollBeginDrag = useCallback(() => {
    if (isPlaying) {
      setIsPlaying(false);
      stopSpeech();
      triggerHaptic(Haptics.ImpactFeedbackStyle.Light);
    }
  }, [isPlaying, stopSpeech]);

  // Ref for swipe-to-dismiss so PanResponder always calls latest handleClose
  const closeHandlerRef = useRef(handleClose);
  useEffect(() => {
    closeHandlerRef.current = handleClose;
  }, [handleClose]);

  const panResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => false,
      onMoveShouldSetPanResponder: (_, gestureState) => Math.abs(gestureState.dy) > 5,
      onPanResponderMove: (_, gestureState) => {
        if (gestureState.dy > 0) panY.setValue(gestureState.dy);
      },
      onPanResponderRelease: (_, gestureState) => {
        if (gestureState.dy > 120 || gestureState.vy > 0.5) {
          closeHandlerRef.current?.();
        } else {
          Animated.spring(panY, {
            toValue: 0,
            useNativeDriver: true,
            tension: 40,
            friction: 8,
          }).start();
        }
      },
    })
  ).current;

  const combinedTranslateY = useMemo(
    () => Animated.add(slideAnim, panY),
    [slideAnim, panY]
  );

  const handleTogglePlay = useCallback(() => {
    if (!currentExtended) return;

    const nextPlaying = !isPlaying;
    setIsPlaying(nextPlaying);

    if (currentMomentForChart) {
      fireAnalytics({
        type: "moment_play_toggle",
        symbol,
        momentId: currentMomentForChart.id,
        index: getAnalyticsIndex(currentIndex),
        totalMoments: totalRealMoments,
      });
    }

    triggerHaptic(nextPlaying ? Haptics.ImpactFeedbackStyle.Medium : Haptics.ImpactFeedbackStyle.Light);
  }, [currentExtended, isPlaying, currentMomentForChart, fireAnalytics, symbol, totalRealMoments, currentIndex, getAnalyticsIndex]);

  const handleNext = useCallback(() => {
    if (!storyMoments.length || currentIndex >= storyMoments.length - 1) return;

    const fromIndex = currentIndex;
    const toIndex = currentIndex + 1;

    stopSpeech();
    setCurrentIndex(toIndex);
    setIsPlaying(true);

    fireAnalytics({
      type: "moment_skip_next",
      symbol,
      fromIndex: getAnalyticsIndex(fromIndex),
      toIndex: getAnalyticsIndex(toIndex),
      totalMoments: totalRealMoments,
    });

    triggerHaptic();
  }, [storyMoments.length, currentIndex, stopSpeech, fireAnalytics, symbol, totalRealMoments, getAnalyticsIndex]);

  const handlePrevious = useCallback(() => {
    if (!storyMoments.length || currentIndex <= 0) return;

    const fromIndex = currentIndex;
    const toIndex = currentIndex - 1;

    stopSpeech();
    setCurrentIndex(toIndex);
    setIsPlaying(true);

    fireAnalytics({
      type: "moment_skip_prev",
      symbol,
      fromIndex: getAnalyticsIndex(fromIndex),
      toIndex: getAnalyticsIndex(toIndex),
      totalMoments: totalRealMoments,
    });

    triggerHaptic();
  }, [storyMoments.length, currentIndex, stopSpeech, fireAnalytics, symbol, totalRealMoments, getAnalyticsIndex]);

  const handleShare = useCallback(async () => {
    if (!captureRef || !Sharing) {
      logger.warn("[MomentStoryPlayer] Share requires react-native-view-shot and expo-sharing");
      return;
    }
    const currentRef = cardRefs.current[safeCurrentIndex];
    if (!currentRef) return;
    try {
      const uri = await captureRef(currentRef as any, {
        format: "png",
        quality: 1,
        result: "tmpfile",
      });
      if (await Sharing!.isAvailableAsync()) {
        await Sharing!.shareAsync(uri, {
          mimeType: "image/png",
          dialogTitle: `Share this ${symbol} moment`,
        });
      }
    } catch (error) {
      logger.error("[MomentStoryPlayer] Share failed", error);
    }
  }, [safeCurrentIndex, symbol]);

  // ─────────────────────────────────────────────────────────────────────────
  // FlatList helpers
  // ─────────────────────────────────────────────────────────────────────────

  const renderItem = useCallback(
    ({ item, index }: ListRenderItemInfo<ExtendedMoment>) => (
      <MomentCard
        ref={(el) => {
          cardRefs.current[index] = el;
        }}
        item={item}
        isActive={index === currentIndex}
        listened={!item.isIntro && listenedIds.has(item.id)}
        isSampleData={isSampleData}
      />
    ),
    [currentIndex, listenedIds, isSampleData]
  );

  const getItemLayout = useCallback(
    (_data: ExtendedMoment[] | null, index: number) => ({
      length: ITEM_LAYOUT_LENGTH,
      offset: ITEM_LAYOUT_LENGTH * index,
      index,
    }),
    []
  );

  const handleScrollToIndexFailed = useCallback((info: { index: number }) => {
    const safeIndex = clampIndex(info.index, storyMoments.length);
    logger.warn('[MomentStoryPlayer] scrollToIndexFailed, retrying:', safeIndex);
    setTimeout(() => {
      listRef.current?.scrollToOffset({
        offset: safeIndex * ITEM_LAYOUT_LENGTH,
        animated: true,
      });
    }, 100);
  }, [storyMoments.length]);

  const keyExtractor = useCallback((m: ExtendedMoment) => m.id, []);

  // ─────────────────────────────────────────────────────────────────────────
  // Render
  // ─────────────────────────────────────────────────────────────────────────

  if (!visible) return null;

  const isAtStart = currentIndex === 0;
  const isAtEnd = currentIndex === storyMoments.length - 1;
  const progressPercent = totalRealMoments > 0
    ? (listenedCount / totalRealMoments) * 100
    : 0;

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={handleClose}
      statusBarTranslucent
      presentationStyle="overFullScreen"
    >
      <View style={styles.backdrop}>
        <Animated.View
          {...panResponder.panHandlers}
          style={[
            styles.sheet,
            { transform: [{ translateY: combinedTranslateY }] },
          ]}
        >
          <View style={styles.dragHandle} />
          {/* Header */}
          <LinearGradient
            colors={["#FFFFFF", "#F0F9FF", "#F8FAFC"]}
            style={styles.gradientHeader}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
          >
            <View style={styles.headerRow}>
              <View style={styles.headerLeft}>
                <Text style={styles.headerSymbol}>{symbol.toUpperCase()}</Text>
                <View style={styles.headerTitleRow}>
                  <Text style={styles.headerTitle}>Story Mode</Text>
                  {isSampleData && (
                    <View style={styles.sampleBadge}>
                      <Text style={styles.sampleBadgeText}>Sample</Text>
                    </View>
                  )}
                  {isTTSLoading && (
                    <View style={styles.loadingIndicator}>
                      <ActivityIndicator size="small" color="#3B82F6" />
                      <Text style={styles.loadingText}>Preparing voice...</Text>
                    </View>
                  )}
                </View>
              </View>
              <View style={styles.headerActions}>
                <Pressable
                  onPress={handleShare}
                  accessible
                  accessibilityRole="button"
                  accessibilityLabel="Share this moment"
                  style={styles.shareIconButton}
                  hitSlop={10}
                >
                  <Text style={styles.shareIconText}>📤</Text>
                </Pressable>
                <Pressable
                  onPress={handleClose}
                  accessible
                  accessibilityRole="button"
                  accessibilityLabel="Close story mode"
                  style={styles.closeButton}
                  hitSlop={12}
                >
                  <Text style={styles.closeText}>✕</Text>
                </Pressable>
              </View>
            </View>
          </LinearGradient>

          {/* Story Cards */}
          <FlatList
            ref={listRef}
            data={storyMoments}
            keyExtractor={keyExtractor}
            renderItem={renderItem}
            horizontal
            pagingEnabled
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.listContent}
            getItemLayout={getItemLayout}
            initialScrollIndex={initialScrollIndexWhenVisible}
            onScrollToIndexFailed={handleScrollToIndexFailed}
            onScrollBeginDrag={handleScrollBeginDrag}
            scrollEventThrottle={16}
            removeClippedSubviews
            maxToRenderPerBatch={3}
            windowSize={5}
            bounces={false}
            decelerationRate="fast"
          />

          {/* Controls */}
          <View style={styles.controlsRow}>
            <Pressable
              style={[styles.controlButton, isAtStart && styles.controlButtonDisabled]}
              onPress={handlePrevious}
              disabled={isAtStart}
              accessible
              accessibilityRole="button"
              accessibilityLabel="Previous moment"
              accessibilityState={{ disabled: isAtStart }}
              hitSlop={8}
            >
              <Text style={[styles.controlButtonText, isAtStart && styles.controlButtonTextDisabled]}>
                Previous
              </Text>
            </Pressable>

            <Pressable
              style={[styles.controlButton, styles.playButton, !currentExtended && styles.controlButtonDisabled]}
              onPress={handleTogglePlay}
              disabled={!currentExtended}
              accessible
              accessibilityRole="button"
              accessibilityLabel={isPlaying ? "Pause story" : "Play story"}
              accessibilityState={{ disabled: !currentExtended }}
              hitSlop={8}
            >
              <Text style={styles.playButtonText}>
                {isPlaying ? "⏸️ Pause" : "▶️ Play"}
              </Text>
            </Pressable>

            <Pressable
              style={[styles.controlButton, isAtEnd && styles.controlButtonDisabled]}
              onPress={handleNext}
              disabled={isAtEnd}
              accessible
              accessibilityRole="button"
              accessibilityLabel="Next moment"
              accessibilityState={{ disabled: isAtEnd }}
              hitSlop={8}
            >
              <Text style={[styles.controlButtonText, isAtEnd && styles.controlButtonTextDisabled]}>
                Next
              </Text>
            </Pressable>
          </View>

          {/* Progress */}
          <View style={styles.progressRow}>
            <View style={styles.progressBarContainer}>
              <View style={[styles.progressBar, { width: `${progressPercent}%` }]} />
            </View>
            <Text style={styles.progressText}>
              {totalRealMoments === 0
                ? "No moments available"
                : `${listenedCount}/${totalRealMoments} moments listened • ${symbol.toUpperCase()}`}
            </Text>
          </View>
        </Animated.View>
      </View>
    </Modal>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// Styles
// ─────────────────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "flex-end",
  },
  sheet: {
    backgroundColor: "#FFFFFF",
    borderTopLeftRadius: 36,
    borderTopRightRadius: 36,
    paddingBottom: 40,
    maxWidth: SCREEN_WIDTH,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: -8 },
    shadowOpacity: 0.12,
    shadowRadius: 24,
    elevation: 16,
  },
  dragHandle: {
    width: 40,
    height: 5,
    backgroundColor: "rgba(0,0,0,0.1)",
    borderRadius: 3,
    alignSelf: "center",
    marginTop: 10,
    marginBottom: -10,
    zIndex: 10,
  },
  gradientHeader: {
    borderTopLeftRadius: 36,
    borderTopRightRadius: 36,
    paddingTop: 20,
    paddingBottom: 20,
  },
  headerRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingHorizontal: 24,
    alignItems: "center",
  },
  headerLeft: {
    flex: 1,
  },
  headerSymbol: {
    fontSize: 14,
    fontWeight: "600",
    color: "#6B7280",
    marginBottom: 2,
  },
  headerTitleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: "900",
    color: "#111827",
    letterSpacing: -0.5,
  },
  sampleBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    backgroundColor: "rgba(107, 114, 128, 0.2)",
  },
  sampleBadgeText: {
    fontSize: 11,
    fontWeight: "600",
    color: "#6B7280",
    textTransform: "uppercase",
  },
  loadingIndicator: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 8,
    paddingVertical: 4,
    backgroundColor: "rgba(59, 130, 246, 0.1)",
    borderRadius: 12,
  },
  loadingText: {
    fontSize: 11,
    fontWeight: "500",
    color: "#3B82F6",
  },
  headerActions: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  shareIconButton: {
    padding: 8,
    borderRadius: 16,
    backgroundColor: "rgba(0,0,0,0.05)",
  },
  shareIconText: {
    fontSize: 20,
  },
  closeButton: {
    padding: 8,
    borderRadius: 16,
    backgroundColor: "rgba(0,0,0,0.05)",
  },
  closeText: {
    fontSize: 20,
    fontWeight: "600",
    color: "#6B7280",
  },
  listContent: {
    paddingHorizontal: 20,
    paddingVertical: 20,
  },
  cardWrapper: {},
  card: {
    width: CARD_WIDTH,
    marginRight: CARD_MARGIN,
    borderRadius: 28,
    padding: 24,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "rgba(0,0,0,0.05)",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.06,
    shadowRadius: 12,
    elevation: 4,
  },
  cardIntro: {
    backgroundColor: "#F0FDF4",
    borderColor: "#22C55E20",
    shadowColor: "#22C55E",
    shadowOpacity: 0.08,
  },
  cardActive: {
    backgroundColor: "#F3F4F6",
    borderColor: "#3B82F620",
    shadowColor: "#3B82F6",
    shadowOpacity: 0.12,
    transform: [{ scale: 1.02 }],
  },
  cardHeaderRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 16,
    gap: 12,
  },
  categoryIconContainer: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: "center",
    alignItems: "center",
  },
  categoryIcon: {
    fontSize: 14,
    fontWeight: "bold",
    color: "#FFFFFF",
  },
  cardCategoryContainer: {
    flex: 1,
  },
  cardCategory: {
    fontSize: 12,
    fontWeight: "700",
    textTransform: "uppercase",
    letterSpacing: 1,
  },
  listenedIndicator: {
    backgroundColor: "#22C55E20",
    borderRadius: 16,
    paddingHorizontal: 8,
    paddingVertical: 4,
    minWidth: 24,
    alignItems: "center",
  },
  cardListenedDot: {
    fontSize: 14,
    color: "#22C55E",
    fontWeight: "600",
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: "800",
    color: "#111827",
    marginBottom: 12,
    lineHeight: 22,
    letterSpacing: -0.3,
  },
  cardSummary: {
    fontSize: 15,
    color: "#374151",
    lineHeight: 22,
  },
  shareFooter: {
    marginTop: "auto",
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: "rgba(0,0,0,0.05)",
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  brandText: {
    fontSize: 10,
    fontWeight: "700",
    color: "#3B82F6",
    letterSpacing: 1,
    textTransform: "uppercase",
  },
  sampleStamp: {
    fontSize: 8,
    color: "#9CA3AF",
    fontWeight: "600",
    backgroundColor: "#F3F4F6",
    paddingHorizontal: 4,
    borderRadius: 2,
  },
  symbolStamp: {
    fontSize: 12,
    fontWeight: "800",
    color: "#111827",
  },
  controlsRow: {
    marginTop: 24,
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    gap: 20,
  },
  controlButton: {
    paddingHorizontal: 24,
    paddingVertical: 14,
    borderRadius: 28,
    borderWidth: 1,
    borderColor: "rgba(0,0,0,0.1)",
    backgroundColor: "#FFFFFF",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 2,
    minWidth: 80,
    alignItems: "center",
  },
  controlButtonDisabled: {
    opacity: 0.6,
    borderColor: "rgba(0,0,0,0.05)",
  },
  controlButtonText: {
    fontSize: 15,
    fontWeight: "700",
    color: "#374151",
    letterSpacing: 0.5,
  },
  controlButtonTextDisabled: {
    color: "#9CA3AF",
  },
  playButton: {
    backgroundColor: "#111827",
    borderColor: "#111827",
    paddingHorizontal: 32,
    shadowColor: "#111827",
    shadowOpacity: 0.15,
    minWidth: 100,
  },
  playButtonText: {
    fontSize: 15,
    fontWeight: "800",
    color: "#FFFFFF",
    letterSpacing: 0.5,
  },
  progressRow: {
    marginTop: 20,
    alignItems: "center",
    paddingHorizontal: 24,
  },
  progressBarContainer: {
    width: "100%",
    height: 6,
    backgroundColor: "rgba(0,0,0,0.05)",
    borderRadius: 3,
    overflow: "hidden",
    marginBottom: 12,
  },
  progressBar: {
    height: "100%",
    backgroundColor: "#22C55E",
    borderRadius: 3,
  },
  progressText: {
    fontSize: 14,
    color: "#6B7280",
    textAlign: "center",
    fontWeight: "500",
  },
});

export default memo(MomentStoryPlayer);
