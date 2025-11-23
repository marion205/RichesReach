import React, { useEffect, useMemo, useRef, useState, useCallback } from "react";
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
  StatusBar, // For status bar styling
  ActivityIndicator,
} from "react-native";
import * as Speech from "expo-speech";
import * as Haptics from "expo-haptics";
import type { StockMoment, MomentCategory } from "./ChartWithMoments";
import { LinearGradient } from "expo-linear-gradient"; // For gradient backgrounds

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
  /**
   * Use a custom TTS service (e.g. Wealth Oracle microservice).
   * If provided, expo-speech is not used.
   */
  speakFn?: (text: string, moment: StockMoment, onComplete?: () => void) => Promise<void>;
  stopFn?: () => void;
  /**
   * Cinematic intro slide before first moment.
   */
  enableIntro?: boolean;
  introText?: string;
}

// Constants
const CARD_WIDTH = Math.min(340, Dimensions.get("window").width * 0.9); // Slightly wider for polish
const CARD_MARGIN = 20;
const ITEM_LAYOUT_LENGTH = CARD_WIDTH + CARD_MARGIN;
const SPEECH_TIMEOUT_BASE_MS = 200;
const SPEECH_MIN_DURATION_MS = 5000;
const SPEECH_MAX_DURATION_MS = 25000;
const WEALTH_ORACLE_VOICE_OPTIONS: Speech.SpeechOptions = {
  language: "en-US",
  rate: 0.9,
  pitch: 1.05,
};

// Enhanced category styles with gradients/icons
const CATEGORY_STYLES = {
  EARNINGS: { color: "#10B981", gradient: ["#10B981", "#059669"], icon: "💰" },
  NEWS: { color: "#3B82F6", gradient: ["#3B82F6", "#2563EB"], icon: "📰" },
  INSIDER: { color: "#F59E0B", gradient: ["#F59E0B", "#D97706"], icon: "👤" },
  MACRO: { color: "#8B5CF6", gradient: ["#8B5CF6", "#7C3AED"], icon: "🌍" },
  SENTIMENT: { color: "#EF4444", gradient: ["#EF4444", "#DC2626"], icon: "😊" },
  OTHER: { color: "#6B7280", gradient: ["#6B7280", "#4B5563"], icon: "•" },
} as const;

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
}) => {
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isTTSLoading, setIsTTSLoading] = useState(false);
  const [listenedIds, setListenedIds] = useState<string[]>([]);
  const listRef = useRef<FlatList<ExtendedMoment>>(null);
  const speechTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const slideAnim = useRef(new Animated.Value(0)).current;

  const sortedMoments: StockMoment[] = useMemo(
    () =>
      [...moments].sort(
        (a, b) =>
          new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
      ),
    [moments],
  );

  const introMoment: ExtendedMoment | null = useMemo(() => {
    if (!enableIntro || !sortedMoments.length) return null;

    const text =
      introText ||
      `Here's the story behind ${symbol.toUpperCase()}'s recent moves. I'll walk you through each key moment on the chart.`;

    const nowIso =
      sortedMoments.length > 0 ? sortedMoments[0].timestamp : new Date().toISOString();

    return {
      id: "INTRO",
      symbol,
      timestamp: nowIso,
      category: "OTHER",
      title: `The story behind ${symbol.toUpperCase()}`,
      quickSummary: text,
      deepSummary: text,
      isIntro: true,
    } as ExtendedMoment;
  }, [enableIntro, sortedMoments, symbol, introText]);

  const storyMoments: ExtendedMoment[] = useMemo(() => {
    if (introMoment) return [introMoment, ...sortedMoments];
    return [...sortedMoments];
  }, [introMoment, sortedMoments]);

  // Clamp currentIndex to valid range when storyMoments change
  useEffect(() => {
    if (!storyMoments.length) {
      setCurrentIndex(0);
      return;
    }
    const clampedIndex = Math.max(0, Math.min(currentIndex, storyMoments.length - 1));
    if (clampedIndex !== currentIndex) {
      setCurrentIndex(clampedIndex);
    }
  }, [storyMoments.length, currentIndex]);

  const safeCurrentIndex = storyMoments.length > 0
    ? Math.max(0, Math.min(currentIndex, storyMoments.length - 1))
    : 0;
  const currentExtended: ExtendedMoment | null =
    storyMoments.length > 0 ? storyMoments[safeCurrentIndex] : null;

  // "Real" StockMoment for chart/analytics (ignore intro as a data point)
  const currentMomentForChart: StockMoment | null =
    currentExtended && !currentExtended.isIntro ? currentExtended : null;

  const total = sortedMoments.length; // only real moments for analytics

  const fireAnalytics = useCallback((event: MomentAnalyticsEvent) => {
    onAnalyticsEvent?.(event);
  }, [onAnalyticsEvent]);

  // Instant open - no animation delay for better UX
  useEffect(() => {
    if (visible) {
      // Set to final position immediately - no animation delay
      slideAnim.setValue(0);
    } else {
      // Quick close animation (optional)
      Animated.timing(slideAnim, {
        toValue: 400,
        duration: 150, // Faster close
        useNativeDriver: true,
      }).start();
    }
  }, [visible, slideAnim]);

  // Status bar adjustment
  useEffect(() => {
    if (visible) {
      StatusBar.setBarStyle("dark-content");
      StatusBar.setBackgroundColor("transparent", false);
    }
    return () => {
      StatusBar.setBarStyle("default");
    };
  }, [visible]);

  // Scroll + notify when current index changes (unchanged logic)
  useEffect(() => {
    if (!visible || !storyMoments.length) return;

    const safeIndex = Math.max(0, Math.min(currentIndex, storyMoments.length - 1));
    
    requestAnimationFrame(() => {
      try {
        listRef.current?.scrollToIndex({
          index: safeIndex,
          animated: true,
          viewPosition: 0.5,
        });
      } catch (error) {
        console.warn('[MomentStoryPlayer] scrollToIndex error:', error);
        listRef.current?.scrollToOffset({ 
          offset: safeIndex * ITEM_LAYOUT_LENGTH, 
          animated: true 
        });
      }
    });

    if (currentMomentForChart && onMomentChange) {
      onMomentChange(currentMomentForChart);
      fireAnalytics({
        type: "moment_change",
        symbol,
        momentId: currentMomentForChart.id,
        index: introMoment ? currentIndex - 1 : currentIndex,
        totalMoments: total,
      });
    } else if (!currentMomentForChart && onMomentChange) {
      onMomentChange(null);
    }

    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(console.warn);
  }, [
    visible,
    currentIndex,
    storyMoments,
    currentMomentForChart,
    onMomentChange,
    symbol,
    total,
    introMoment,
    fireAnalytics,
  ]);

  // Reset state when opening/closing - make this instant
  useEffect(() => {
    if (!visible) {
      stopSpeech();
      setIsPlaying(false);
      setListenedIds([]);
      setCurrentIndex(0);
      setIsTTSLoading(false);
      return () => stopSpeech();
    }

    // Set state immediately - don't wait for anything
    const maxIndex = storyMoments.length - 1;
    const clampedInitialIndex = Math.max(0, Math.min(initialIndex, maxIndex));
    const baseIndex = introMoment ? 0 : clampedInitialIndex;
    
    // Set all state synchronously for instant UI
    setCurrentIndex(baseIndex);
    setListenedIds([]);
    setIsPlaying(true);
    setIsTTSLoading(false); // Start with loading false, will set true when TTS starts

    // Fire analytics asynchronously (don't block)
    setTimeout(() => {
      fireAnalytics({
        type: "story_open",
        symbol,
        totalMoments: total,
      });
    }, 0);

    return () => stopSpeech();
  }, [visible, initialIndex, symbol, total, introMoment, storyMoments.length, fireAnalytics]);

  // TTS helpers (unchanged)
  const stopSpeech = useCallback(() => {
    if (speechTimeoutRef.current) {
      clearTimeout(speechTimeoutRef.current);
      speechTimeoutRef.current = null;
    }
    if (stopFn) {
      stopFn();
    } else {
      Speech.stop();
    }
  }, [stopFn]);

  const handleSpeechComplete = useCallback(() => {
    if (!visible || !currentExtended) return;

    if (!currentExtended.isIntro) {
      setListenedIds((prev) =>
        prev.includes(currentExtended.id) ? prev : [...prev, currentExtended.id],
      );
    }

    if (!isPlaying) return;

    setCurrentIndex((prev) => {
      const next = prev + 1;
      if (next >= storyMoments.length) {
        setIsPlaying(false);
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(console.warn);
        return prev;
      }
      return next;
    });
  }, [visible, currentExtended, isPlaying, storyMoments.length]);

  const speakText = useCallback(async (text: string, moment: StockMoment) => {
    // Start TTS immediately without blocking
    setIsTTSLoading(true);
    
    // Set loading to false quickly (max 1.5s) so UI doesn't feel stuck
    const loadingTimeout = setTimeout(() => {
      setIsTTSLoading(false);
    }, 1500);
    
    try {
      if (speakFn) {
        // Pass completion callback so story advances when audio finishes
        speakFn(text, moment, handleSpeechComplete)
          .catch((error) => {
            console.warn('[MomentStoryPlayer] TTS error (non-blocking):', error);
            // On error, still advance story after a delay
            setTimeout(handleSpeechComplete, 2000);
          })
          .finally(() => {
            clearTimeout(loadingTimeout);
            setIsTTSLoading(false);
          });
        // Return immediately - don't wait, but completion will be handled by callback
        return;
      }

      clearTimeout(loadingTimeout);
      setIsTTSLoading(false);
      Speech.speak(text, {
        ...WEALTH_ORACLE_VOICE_OPTIONS,
        onDone: handleSpeechComplete,
        onError: handleSpeechComplete,
      });
    } catch (error) {
      clearTimeout(loadingTimeout);
      console.warn('[MomentStoryPlayer] Speech error:', error);
      setIsTTSLoading(false);
      handleSpeechComplete();
    }
  }, [speakFn, handleSpeechComplete]);

  // TTS for current slide (unchanged)
  useEffect(() => {
    if (!visible || !currentExtended || !isPlaying) {
      stopSpeech();
      return;
    }

    stopSpeech();

    const text = currentExtended.deepSummary;
    const estimatedWords = text.split(/\s+/).length;
    const estimatedDurationMs = Math.min(
      SPEECH_MAX_DURATION_MS,
      Math.max(SPEECH_MIN_DURATION_MS, estimatedWords * SPEECH_TIMEOUT_BASE_MS),
    );

    const forMoment: StockMoment =
      currentMomentForChart ?? {
        ...currentExtended,
        category: "OTHER" as MomentCategory,
      };

    // Start TTS immediately without waiting - fire and forget
    // Use setTimeout(0) to ensure this doesn't block rendering
    setTimeout(() => {
      speakText(text, forMoment).catch(() => {
        // If TTS fails, just continue - don't block
        console.warn('[MomentStoryPlayer] TTS failed, continuing without voice');
      });
    }, 0);

    // Set timeout as fallback ONLY if using expo-speech (not TTS service)
    // TTS service will call handleSpeechComplete via callback
    if (!speakFn) {
      speechTimeoutRef.current = setTimeout(() => {
        stopSpeech();
        handleSpeechComplete();
      }, estimatedDurationMs);
    }

    return () => {
      stopSpeech();
      if (speechTimeoutRef.current) {
        clearTimeout(speechTimeoutRef.current);
        speechTimeoutRef.current = null;
      }
    };
  }, [visible, isPlaying, currentExtended, currentMomentForChart, speakText, stopSpeech, handleSpeechComplete]);

  const handleClose = useCallback(() => {
    stopSpeech();
    setIsPlaying(false);

    fireAnalytics({
      type: "story_close",
      symbol,
      totalMoments: total,
      listenedCount: listenedIds.length,
    });

    onMomentChange?.(null);
    onClose?.();
  }, [stopSpeech, fireAnalytics, symbol, total, listenedIds.length, onMomentChange, onClose]);

  const handleTogglePlay = useCallback(() => {
    if (!currentExtended) return;
    const nextPlaying = !isPlaying;
    setIsPlaying(nextPlaying);

    if (currentMomentForChart) {
      fireAnalytics({
        type: "moment_play_toggle",
        symbol,
        momentId: currentMomentForChart.id,
        index: introMoment ? currentIndex - 1 : currentIndex,
        totalMoments: total,
      });
    }

    Haptics.impactAsync(
      nextPlaying ? Haptics.ImpactFeedbackStyle.Medium : Haptics.ImpactFeedbackStyle.Light,
    ).catch(console.warn);
  }, [currentExtended, isPlaying, currentMomentForChart, fireAnalytics, symbol, total, introMoment, currentIndex]);

  const handleNext = useCallback(() => {
    if (!storyMoments.length || currentIndex === storyMoments.length - 1) return;
    const fromIndex = currentIndex;
    const toIndex = currentIndex + 1;

    stopSpeech();
    setCurrentIndex(toIndex);
    setIsPlaying(true);

    fireAnalytics({
      type: "moment_skip_next",
      symbol,
      fromIndex: introMoment && fromIndex > 0 ? fromIndex - 1 : fromIndex,
      toIndex: introMoment && toIndex > 0 ? toIndex - 1 : toIndex,
      totalMoments: total,
    });

    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(console.warn);
  }, [storyMoments.length, currentIndex, stopSpeech, fireAnalytics, symbol, total, introMoment]);

  const handlePrevious = useCallback(() => {
    if (!storyMoments.length || currentIndex === 0) return;
    const fromIndex = currentIndex;
    const toIndex = currentIndex - 1;

    stopSpeech();
    setCurrentIndex(toIndex);
    setIsPlaying(true);

    fireAnalytics({
      type: "moment_skip_prev",
      symbol,
      fromIndex: introMoment && fromIndex > 0 ? fromIndex - 1 : fromIndex,
      toIndex: introMoment && toIndex > 0 ? toIndex - 1 : toIndex,
      totalMoments: total,
    });

    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(console.warn);
  }, [storyMoments.length, currentIndex, stopSpeech, fireAnalytics, symbol, total, introMoment]);

  const renderItem = useCallback(
    ({ item, index }: ListRenderItemInfo<ExtendedMoment>) => {
      const isActive = index === currentIndex;
      const listened = !item.isIntro && listenedIds.includes(item.id);
      const catStyle = item.isIntro ? CATEGORY_STYLES.OTHER : CATEGORY_STYLES[item.category as keyof typeof CATEGORY_STYLES];

      return (
        <Animated.View
          style={[
            styles.card,
            isActive && styles.cardActive,
            item.isIntro && styles.cardIntro,
          ]}
          accessible={true}
          accessibilityRole="article"
          accessibilityLabel={`${item.category} moment: ${item.title}. ${item.deepSummary.substring(0, 100)}...`}
        >
          <View style={styles.cardHeaderRow}>
            <LinearGradient
              colors={catStyle.gradient}
              style={styles.categoryIconContainer}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
            >
              <Text style={[styles.categoryIcon, { color: "#FFFFFF" }]}>{catStyle.icon}</Text>
            </LinearGradient>
            <View style={styles.cardCategoryContainer}>
              <Text style={[styles.cardCategory, { color: catStyle.color }]} aria-label={`${item.category} category`}>
                {item.isIntro ? "INTRO" : item.category}
              </Text>
            </View>
            {listened && (
              <View style={styles.listenedIndicator}>
                <Text style={styles.cardListenedDot} aria-hidden={true}>✓</Text>
              </View>
            )}
          </View>
          <Text style={styles.cardTitle} numberOfLines={2}>{item.title}</Text>
          <Text style={styles.cardSummary} numberOfLines={6}>
            {item.deepSummary}
          </Text>
        </Animated.View>
      );
    },
    [currentIndex, listenedIds],
  );

  // All hooks must be called before any conditional returns
  const getItemLayout = useCallback(
    (data: ExtendedMoment[] | null, index: number) => ({
      length: ITEM_LAYOUT_LENGTH,
      offset: ITEM_LAYOUT_LENGTH * index,
      index,
    }),
    [],
  );

  // Early return after all hooks
  if (!visible) return null;

  const realTotal = total;
  const listenedCount = listenedIds.length;

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade" // Faster than slide
      onRequestClose={handleClose}
      statusBarTranslucent={true}
      presentationStyle="overFullScreen" // Faster rendering
    >
      <View style={styles.backdrop}>
        <Animated.View
          style={[
            styles.sheet,
            {
              transform: [
                {
                  translateY: slideAnim,
                },
              ],
            },
          ]}
        >
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
                  {isTTSLoading && (
                    <View style={styles.loadingIndicator}>
                      <ActivityIndicator size="small" color="#3B82F6" />
                      <Text style={styles.loadingText}>Preparing voice...</Text>
                    </View>
                  )}
                </View>
              </View>
              <Pressable 
                onPress={handleClose}
                accessible={true}
                accessibilityRole="button"
                accessibilityLabel="Close story mode"
                style={styles.closeButton}
              >
                <Text style={styles.closeText}>✕</Text>
              </Pressable>
            </View>
          </LinearGradient>

          <FlatList
            ref={listRef}
            data={storyMoments}
            keyExtractor={(m) => m.id}
            renderItem={renderItem}
            horizontal
            pagingEnabled
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.listContent}
            getItemLayout={getItemLayout}
            initialScrollIndex={safeCurrentIndex}
            onScrollToIndexFailed={(info) => {
              const safeIndex = Math.max(0, Math.min(info.index, storyMoments.length - 1));
              console.warn('[MomentStoryPlayer] scrollToIndexFailed, retrying with safe index:', safeIndex);
              setTimeout(() => {
                try {
                  listRef.current?.scrollToOffset({ 
                    offset: safeIndex * ITEM_LAYOUT_LENGTH, 
                    animated: true 
                  });
                } catch (error) {
                  console.warn('[MomentStoryPlayer] scrollToOffset failed:', error);
                }
              }, 100);
            }}
            removeClippedSubviews={true}
            maxToRenderPerBatch={3}
            windowSize={5}
            bounces={false}
            decelerationRate="fast"
          />

          <View style={styles.controlsRow}>
            <Pressable
              style={[styles.controlButton, currentIndex === 0 && styles.controlButtonDisabled]}
              onPress={handlePrevious}
              disabled={currentIndex === 0}
              accessible={true}
              accessibilityRole="button"
              accessibilityLabel="Previous moment"
              accessibilityState={{ disabled: currentIndex === 0 }}
            >
              <Text
                style={[
                  styles.controlButtonText,
                  currentIndex === 0 && styles.controlButtonTextDisabled,
                ]}
              >
                Previous
              </Text>
            </Pressable>

            <Pressable
              style={[styles.controlButton, styles.playButton, !currentExtended && styles.controlButtonDisabled]}
              onPress={handleTogglePlay}
              disabled={!currentExtended}
              accessible={true}
              accessibilityRole="button"
              accessibilityLabel={isPlaying ? "Pause story" : "Play story"}
              accessibilityState={{ disabled: !currentExtended }}
            >
              <Text style={styles.playButtonText}>
                {isPlaying ? "⏸️ Pause" : "▶️ Play"}
              </Text>
            </Pressable>

            <Pressable
              style={[styles.controlButton, currentIndex === storyMoments.length - 1 && styles.controlButtonDisabled]}
              onPress={handleNext}
              disabled={currentIndex === storyMoments.length - 1}
              accessible={true}
              accessibilityRole="button"
              accessibilityLabel="Next moment"
              accessibilityState={{ disabled: currentIndex === storyMoments.length - 1 }}
            >
              <Text
                style={[
                  styles.controlButtonText,
                  currentIndex === storyMoments.length - 1 &&
                    styles.controlButtonTextDisabled,
                ]}
              >
                Next
              </Text>
            </Pressable>
          </View>

          <View style={styles.progressRow}>
            <View style={styles.progressBarContainer}>
              <View 
                style={[
                  styles.progressBar,
                  { 
                    width: `${(listenedCount / Math.max(realTotal, 1)) * 100}%` 
                  }
                ]} 
              />
            </View>
            <Text style={styles.progressText}>
              {realTotal === 0
                ? "No moments available"
                : `${listenedCount}/${realTotal} moments listened • ${symbol.toUpperCase()}`}
            </Text>
          </View>
        </Animated.View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)", // Deeper blur for immersion
    justifyContent: "flex-end",
  },
  sheet: {
    backgroundColor: "#FFFFFF",
    borderTopLeftRadius: 36,
    borderTopRightRadius: 36,
    paddingBottom: 40,
    maxWidth: Dimensions.get("window").width,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: -8 },
    shadowOpacity: 0.12,
    shadowRadius: 24,
    elevation: 16,
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

export default MomentStoryPlayer;
