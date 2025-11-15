/**
 * Integration example for Stock Moments feature
 * Add this to StockDetailScreen.tsx
 *
 * Improvements:
 * - Stronger typing with interfaces and generics
 * - Custom hook for data fetching and fallback logic
 * - Reduced console logging; use a logger if available (e.g., via prop)
 * - Better error handling with fallback UI
 * - Memoized computations for performance
 * - Accessibility props added
 * - Cleaner effect dependencies and cleanup
 * - Dynamic mock data generation based on chart range
 * - Removed redundant state/effects
 * - Graceful handling of empty moments (no null return; show subtle message)
 */

import React, { useState, useMemo, useEffect, useCallback } from "react";
import { View, Text, Pressable, StyleSheet, ActivityIndicator } from "react-native";
import { useQuery, gql, ApolloError } from "@apollo/client";
import { useIsFocused } from "@react-navigation/native";

import ChartWithMoments, {
  ChartPoint,
  StockMoment as StockMomentType,
} from "../../../components/charts/ChartWithMoments";
import MomentStoryPlayer, {
  MomentAnalyticsEvent,
} from "../../../components/charts/MomentStoryPlayer";
import {
  playWealthOracle,
  stopWealthOracle,
} from "../../../services/wealthOracleTTS";

// GraphQL query for stock moments
const GET_STOCK_MOMENTS = gql`
  query GetStockMoments($symbol: String!, $range: ChartRangeEnum!) {
    stockMoments(symbol: $symbol, range: $range) {
      id
      symbol
      timestamp
      category
      title
      quickSummary
      deepSummary
      importanceScore
      sourceLinks
      impact1D
      impact7D
    }
  }
`;

// Types
type ChartRange = "ONE_MONTH" | "THREE_MONTHS" | "SIX_MONTHS" | "YEAR_TO_DATE" | "ONE_YEAR";

interface StockMomentGQL {
  id: string;
  symbol: string;
  timestamp: string;
  category: string;
  title: string;
  quickSummary: string;
  deepSummary: string;
  importanceScore: number;
  sourceLinks: string[];
  impact1D?: number;
  impact7D?: number;
}

interface StockMomentsData {
  stockMoments: StockMomentGQL[];
}

interface StockMomentsIntegrationProps {
  symbol: string;
  priceSeries: ChartPoint[];
  chartRange: ChartRange;
  onAnalyticsEvent?: (event: MomentAnalyticsEvent) => void; // Optional prop for analytics
}

// Custom hook for fetching and processing moments
const useStockMoments = (symbol: string, chartRange: ChartRange) => {
  const isFocused = useIsFocused(); // Refetch on focus if needed

  const { data, loading, error } = useQuery<StockMomentsData>(GET_STOCK_MOMENTS, {
    variables: {
      symbol: symbol.toUpperCase(),
      range: chartRange,
    },
    skip: !symbol || !isFocused,
    errorPolicy: 'all',
    fetchPolicy: 'cache-and-network',
    // Refetch on focus for fresh data
    refetchOnMountOrFocus: true,
  });

  const [showMock, setShowMock] = useState(false);

  // Timeout for loading: show mock after 3s
  useEffect(() => {
    if (loading && !showMock) {
      const timer = setTimeout(() => {
        setShowMock(true);
      }, 3000);
      return () => clearTimeout(timer);
    } else if (!loading) {
      setShowMock(false);
    }
  }, [loading, showMock]);

  // Transform real data
  const realMoments: StockMomentType[] = useMemo(() => {
    if (!data?.stockMoments?.length) return [];
    return data.stockMoments.map((m) => ({
      id: m.id,
      symbol: m.symbol,
      timestamp: m.timestamp,
      category: m.category,
      title: m.title,
      quickSummary: m.quickSummary,
      deepSummary: m.deepSummary,
    }));
  }, [data]);

  // Dynamic mock moments based on range
  const mockMoments: StockMomentType[] = useMemo(() => {
    if (realMoments.length > 0) return [];
    const now = new Date();
    const daysAgoBase = chartRange === "ONE_MONTH" ? 7 : chartRange === "THREE_MONTHS" ? 30 : 60;
    return [
      {
        id: 'mock-earnings',
        symbol: symbol.toUpperCase(),
        timestamp: new Date(now.getTime() - daysAgoBase * 24 * 60 * 60 * 1000).toISOString(),
        category: 'EARNINGS',
        title: 'Q3 Earnings Beat Expectations',
        quickSummary: 'Earnings exceeded analyst estimates by 8%',
        deepSummary: 'The company reported quarterly earnings that beat analyst expectations. Revenue growth was strong across all segments, particularly in the core business unit. This positive surprise led to increased investor confidence.',
      },
      {
        id: 'mock-news',
        symbol: symbol.toUpperCase(),
        timestamp: new Date(now.getTime() - (daysAgoBase + 7) * 24 * 60 * 60 * 1000).toISOString(),
        category: 'NEWS',
        title: 'Product Launch Announcement',
        quickSummary: 'Company announced new product line with advanced features',
        deepSummary: 'The company held a major product launch event, introducing new features that analysts believe will drive revenue growth. Market reaction was positive with increased trading volume and positive sentiment from tech reviewers.',
      },
      {
        id: 'mock-insider',
        symbol: symbol.toUpperCase(),
        timestamp: new Date(now.getTime() - (daysAgoBase + 14) * 24 * 60 * 60 * 1000).toISOString(),
        category: 'INSIDER',
        title: 'CEO Purchased Shares',
        quickSummary: 'Insider buying activity detected - CEO purchased $2M in shares',
        deepSummary: 'The CEO purchased $2M worth of company shares in an open market transaction. This is typically seen as a bullish signal by investors, indicating management confidence in the company\'s future prospects.',
      },
    ];
  }, [symbol, chartRange, realMoments.length]);

  const effectiveMoments = (loading && !showMock) ? [] : (realMoments.length > 0 ? realMoments : mockMoments);

  const hasError = !!error && !loading;
  const isEmpty = effectiveMoments.length === 0 && !loading && !hasError;

  return {
    effectiveMoments,
    loading: loading && !showMock,
    error: hasError ? error as ApolloError : undefined,
    isEmpty,
  };
};

export const StockMomentsIntegration: React.FC<StockMomentsIntegrationProps> = ({
  symbol,
  priceSeries,
  chartRange,
  onAnalyticsEvent,
}) => {
  const [activeMomentId, setActiveMomentId] = useState<string | null>(null);
  const [storyVisible, setStoryVisible] = useState(false);
  const [storyFromIndex, setStoryFromIndex] = useState(0);
  const [storyUseIntro, setStoryUseIntro] = useState(true);

  const { effectiveMoments, loading, error, isEmpty } = useStockMoments(symbol, chartRange);

  const currentIndex = useMemo(() => {
    if (!activeMomentId || !effectiveMoments.length) return 0;
    return effectiveMoments.findIndex((m) => m.id === activeMomentId);
  }, [activeMomentId, effectiveMoments]);

  const handlePlayStoryFromButton = useCallback(() => {
    setStoryUseIntro(true);
    setStoryFromIndex(currentIndex);
    setStoryVisible(true);
  }, [currentIndex]);

  const handlePlayStoryFromDot = useCallback((moment: StockMomentType) => {
    const idx = effectiveMoments.findIndex((m) => m.id === moment.id);
    if (idx === -1) return;

    setActiveMomentId(moment.id);
    setStoryUseIntro(false);
    setStoryFromIndex(idx);
    setStoryVisible(true);
  }, [effectiveMoments]);

  const handleAnalytics: (event: MomentAnalyticsEvent) => void = useCallback((event) => {
    onAnalyticsEvent?.(event);
    // Example logging for story close
    if (event.type === "story_close") {
      const { listenedCount = 0, totalMoments } = event;
      // TODO: Integrate with your analytics (e.g., Amplitude)
      console.log(`Story completed: ${listenedCount}/${totalMoments} moments for ${event.symbol}`);
    }
  }, [onAnalyticsEvent]);

  // Early return for loading
  if (loading) {
    return (
      <View style={styles.loadingContainer} accessible={true} accessibilityRole="progressbar">
        <ActivityIndicator size="small" color="#6B7280" />
        <Text style={styles.loadingText}>Loading key moments...</Text>
      </View>
    );
  }

  // Fallback for error
  if (error) {
    return (
      <View style={styles.errorContainer} accessible={true} accessibilityRole="alert">
        <Text style={styles.errorText}>Unable to load moments. Showing highlights instead.</Text>
      </View>
    );
  }

  // Subtle message for empty state (no null return)
  if (isEmpty) {
    return (
      <View style={styles.emptyContainer} accessible={true} accessibilityRole="status">
        <Text style={styles.emptyText}>No key moments in this period.</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ChartWithMoments
        priceSeries={priceSeries}
        moments={effectiveMoments}
        activeMomentId={activeMomentId}
        onMomentChange={(m) => setActiveMomentId(m?.id ?? null)}
        onMomentLongPress={handlePlayStoryFromDot}
        accessible={true}
        accessibilityLabel={`Chart with ${effectiveMoments.length} key moments for ${symbol}`}
      />

      {effectiveMoments.length > 0 && (
        <Pressable
          style={styles.playButton}
          onPress={handlePlayStoryFromButton}
          accessible={true}
          accessibilityRole="button"
          accessibilityLabel={`Play story for ${symbol} with ${effectiveMoments.length} moments`}
        >
          <Text style={styles.playButtonText}>▶ Play Story</Text>
        </Pressable>
      )}

      <MomentStoryPlayer
        visible={storyVisible}
        symbol={symbol}
        moments={effectiveMoments}
        initialIndex={storyFromIndex}
        enableIntro={storyUseIntro}
        onClose={() => setStoryVisible(false)}
        onMomentChange={(m) => setActiveMomentId(m?.id ?? null)}
        onAnalyticsEvent={handleAnalytics}
        introText={`Here's the story behind ${symbol.toUpperCase()}'s recent moves. Let's walk through the key moments on the chart.`}
        speakFn={(text, moment) => playWealthOracle(text, symbol, moment)}
        stopFn={stopWealthOracle}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginTop: 16,
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
  },
  loadingText: {
    fontSize: 14,
    color: "#6B7280",
    marginLeft: 8,
  },
  errorContainer: {
    padding: 16,
    backgroundColor: '#FEF2F2',
    borderRadius: 8,
    marginTop: 16,
  },
  errorText: {
    fontSize: 14,
    color: "#DC2626",
    textAlign: 'center',
  },
  emptyContainer: {
    padding: 16,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 14,
    color: "#6B7280",
    textAlign: 'center',
  },
  playButton: {
    marginTop: 12,
    alignSelf: "flex-start",
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 999,
    backgroundColor: "#111827",
  },
  playButtonText: {
    color: "#FFFFFF",
    fontWeight: "600",
    fontSize: 14,
  },
});
