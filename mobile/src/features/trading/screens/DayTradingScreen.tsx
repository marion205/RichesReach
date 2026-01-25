import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
  Alert,
  FlatList,
  ActivityIndicator,
  Dimensions,
} from 'react-native';
import { PanGestureHandler, State } from 'react-native-gesture-handler';
import { useQuery, useMutation, useApolloClient } from '@apollo/client';
import { gql } from '@apollo/client';
import { GET_DAY_TRADING_PICKS, LOG_DAY_TRADING_OUTCOME } from '../../../graphql/dayTrading';
import { GET_EXECUTION_SUGGESTION } from '../../../graphql/execution';
import Icon from 'react-native-vector-icons/Feather';
import { HeaderButtons } from '../components/HeaderButtons';
import SparkMini from '../../../components/charts/SparkMini';
import * as Haptics from 'expo-haptics';
import * as Speech from 'expo-speech';
import { API_HTTP } from '../../../config/api';
import { useVoice } from '../../../contexts/VoiceContext';
import { useNavigation } from '@react-navigation/native';
import OnboardingGuard from '../../../components/OnboardingGuard';
import logger from '../../../utils/logger';
import EducationalTooltip from '../../../components/common/EducationalTooltip';
import { RiskRewardDiagram } from '../../../components/common/RiskRewardDiagram';
import { WhyThisTradeModal } from '../../../components/common/WhyThisTradeModal';
import { LearnWhileTradingModal } from '../../../components/common/LearnWhileTradingModal';
import ExecutionQualityDashboard from '../components/ExecutionQualityDashboard';
// RAHA Integration - The Whisper (Jobs Approach)
import TheWhisperScreen from '../../raha/screens/TheWhisperScreen';

type TradingMode = 'SAFE' | 'AGGRESSIVE';
type Side = 'LONG' | 'SHORT';

interface DayTradingPick {
  symbol: string;
  side: Side;
  score: number;
  features: {
    momentum15m: number;
    rvol10m: number;
    vwapDist: number;
    breakoutPct: number;
    spreadBps: number;
    catalystScore: number;
    orderImbalance?: number;
    bidDepth?: number;
    askDepth?: number;
    depthImbalance?: number;
    executionQualityScore?: number;
    microstructureRisky?: boolean;
  };
  risk: {
    atr5m: number;
    sizeShares: number;
    stop: number;
    targets: number[];
    timeStopMin: number;
  };
  notes: string;
}

interface DayTradingData {
  asOf: string;
  mode: TradingMode;
  picks: DayTradingPick[];
  universeSize: number;
  qualityThreshold: number;
  universeSource?: string; // "CORE" or "DYNAMIC_MOVERS"
  // Diagnostic fields
  scannedCount?: number;
  passedLiquidity?: number;
  passedQuality?: number;
  failedDataFetch?: number;
  filteredByMicrostructure?: number;
  filteredByVolatility?: number;
  filteredByMomentum?: number;
}

const GET_TRADING_QUOTE = gql`
  query GetTradingQuote($symbol: String!) {
    tradingQuote(symbol: $symbol) {
      symbol
      bid
      ask
      bidSize
      askSize
      timestamp
    }
  }
`;

const GET_STOCK_CHART_DATA = gql`
  query GetStockChartData($symbol: String!, $timeframe: String!) {
    stockChartData(symbol: $symbol, timeframe: $timeframe) {
      symbol
      interval
      data {
        timestamp
        open
        high
        low
        close
        volume
      }
    }
  }
`;

interface TradingQuote {
  symbol: string;
  bid?: number;
  ask?: number;
  bidSize?: number;
  askSize?: number;
  timestamp?: string;
  // Computed fields for display
  currentPrice?: number; // Computed from (bid + ask) / 2
  change?: number; // Not available from quote, will be undefined
  changePercent?: number; // Not available from quote, will be undefined
  [key: string]: unknown;
}

interface GestureEvent {
  nativeEvent: {
    translationX: number;
    translationY: number;
    state: number;
    [key: string]: unknown;
  };
}

export default function DayTradingScreen({ navigateTo }: { navigateTo?: (screen: string) => void }) {
  const [showWhyThisTrade, setShowWhyThisTrade] = useState<DayTradingPick | null>(null);
  const [showLearnModal, setShowLearnModal] = useState(false);
  const navigation = useNavigation();
  const [mode, setMode] = useState<TradingMode>('SAFE');
  const [refreshing, setRefreshing] = useState(false);
  const [quotes, setQuotes] = useState<{ [key: string]: TradingQuote }>({});
  const [charts, setCharts] = useState<{ [key: string]: number[] }>({});
  const [visibleSymbols, setVisibleSymbols] = useState<Set<string>>(new Set());
  const [isGestureActive, setIsGestureActive] = useState(false);
  const [gestureDirection, setGestureDirection] = useState<string>('');
  const [selectedPick, setSelectedPick] = useState<DayTradingPick | null>(null);
  const [showExecutionQuality, setShowExecutionQuality] = useState(false);
  const [showWhisper, setShowWhisper] = useState(false);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const chartPollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const client = useApolloClient();
  const { selectedVoice, getVoiceParameters } = useVoice();
  const [logOutcome] = useMutation(LOG_DAY_TRADING_OUTCOME, {
    errorPolicy: 'all',
  });

  const handleNavigateToOnboarding = () => {
    // Navigate to login if not authenticated, or onboarding if authenticated but not completed
    try {
      // Check if user is authenticated via navigation state or context
      // For now, try to navigate to onboarding first
      navigation.navigate('onboarding' as never);
    } catch (error) {
      logger.error('Navigation error:', error);
      // Fallback: try alternative navigation
      try {
        // Try nested navigation for onboarding
        (navigation as any).navigate('Home', {
          screen: 'onboarding',
        });
      } catch (nestedError) {
        logger.error('Nested navigation error:', nestedError);
        // Final fallback
        if (navigateTo) {
          navigateTo('onboarding');
        }
      }
    }
  };

  // AR Gesture Handlers
  const speakText = useCallback((text: string) => {
    const params = getVoiceParameters(selectedVoice.id);
    // Use Speech.speak with voice parameters
    Speech.speak(text, {
      voice: selectedVoice.id,
      pitch: params.pitch,
      rate: params.rate,
    });
  }, [selectedVoice, getVoiceParameters]);

  const executeGestureTrade = useCallback(async (pick: DayTradingPick, side: 'LONG' | 'SHORT') => {
    try {
      // Haptic feedback
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      
      // Voice confirmation
      speakText(`${selectedVoice.name}: Executing ${side} trade for ${pick.symbol}`);
      
      // Mock trade execution (replace with real API call)
      const response = await fetch(`${API_HTTP}/api/mobile/gesture-trade/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol: pick.symbol,
          gesture_type: side === 'LONG' ? 'swipe_right' : 'swipe_left'
        })
      });
      
      const result = await response.json();
      
      if (result.success) {
        // Success haptic
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        
        // Voice confirmation
        speakText(`Trade executed successfully! Order ID: ${result.order_result.order_id}`);
        
        // Log the outcome
        await logOutcome({
          variables: {
            input: {
              symbol: pick.symbol,
              side: side,
              entryPrice: result.order_result.filled_price,
              quantity: result.order_result.quantity,
              timestamp: new Date().toISOString(),
              outcome: 'EXECUTED'
            }
          }
        });
      }
    } catch (error) {
      logger.error('Gesture trade failed:', error);
      
      // Error haptic
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      
      // Voice error message
      speakText('Trade execution failed. Please try again.');
    }
  }, [selectedVoice, speakText, logOutcome]);

  const switchTradingMode = useCallback(async (newMode: TradingMode) => {
    try {
      // Haptic feedback
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      
      // Voice confirmation
      speakText(`Switching to ${newMode} mode`);
      
      // Switch mode
      setMode(newMode);
      
      // Success haptic
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      
      // Voice confirmation
      speakText(`${newMode} mode activated`);
    } catch (error) {
      logger.error('Mode switch failed:', error);
      
      // Error haptic
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      
      // Voice error message
      speakText('Mode switch failed. Please try again.');
    }
  }, [speakText]);

  const handleGesture = useCallback((event: GestureEvent) => {
    const { translationX, translationY, state } = event.nativeEvent;
    
    if (state === State.BEGAN) {
      setIsGestureActive(true);
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    } else if (state === State.ACTIVE) {
      // Determine gesture direction
      if (Math.abs(translationX) > Math.abs(translationY)) {
        if (translationX > 50) {
          setGestureDirection('RIGHT');
        } else if (translationX < -50) {
          setGestureDirection('LEFT');
        }
      } else {
        if (translationY > 50) {
          setGestureDirection('DOWN');
        } else if (translationY < -50) {
          setGestureDirection('UP');
        }
      }
    } else if (state === State.END) {
      setIsGestureActive(false);
      
      // Execute action based on gesture
      if (gestureDirection === 'RIGHT' && selectedPick) {
        // Swipe right = Long trade
        executeGestureTrade(selectedPick, 'LONG');
      } else if (gestureDirection === 'LEFT' && selectedPick) {
        // Swipe left = Short trade
        executeGestureTrade(selectedPick, 'SHORT');
      } else if (gestureDirection === 'UP') {
        // Swipe up = Switch to Aggressive mode
        switchTradingMode('AGGRESSIVE');
      } else if (gestureDirection === 'DOWN') {
        // Swipe down = Switch to Safe mode
        switchTradingMode('SAFE');
      }
      
      setGestureDirection('');
    }
  }, [gestureDirection, selectedPick, executeGestureTrade, switchTradingMode]);

  const selectPick = useCallback((pick: DayTradingPick) => {
    setSelectedPick(pick);
    speakText(`Selected ${pick.symbol} for gesture trading`);
  }, [speakText]);

  const { data, loading, error, refetch, networkStatus, startPolling, stopPolling } = useQuery(
    GET_DAY_TRADING_PICKS,
    {
      variables: { mode },
      fetchPolicy: 'network-only', // Force network fetch to avoid stale cache showing empty picks
      notifyOnNetworkStatusChange: true,
      errorPolicy: 'all',
      // Force schema refresh by bypassing cache completely
      context: {
        fetchOptions: {
          cache: 'no-store',
        },
      },
      onError: (err) => {
        // Log error but don't block UI - we'll use mock data fallback
        if (__DEV__) {
          logger.log('⚠️ Day Trading query error (will use mock data):', err.message);
        }
      },
    },
  );

  // Force schema refresh on mount if we get schema errors
  useEffect(() => {
    if (error?.graphQLErrors?.some((e: any) => e.message?.includes('Cannot query field'))) {
      if (__DEV__) {
        logger.log('🔄 Schema mismatch detected - clearing Apollo cache and retrying');
      }
      // Clear cache and reset store to force schema re-introspection
      client.resetStore()
        .then(() => {
          if (__DEV__) {
            logger.log('✅ Apollo cache cleared - retrying query');
          }
          // Retry the query after cache is cleared
          refetch({ mode });
        })
        .catch((e) => {
          if (__DEV__) {
            logger.log('⚠️ Cache reset error (non-fatal):', e);
          }
        });
    }
  }, [error, client, refetch, mode]);

  // GraphQL returns camelCase - Apollo Client handles the transformation
  // Debug: log the raw data to see what we're getting
  if (__DEV__) {
    if (error) {
      logger.log('❌ GraphQL Error:', JSON.stringify(error, null, 2));
      if (error.networkError) {
        logger.log('❌ Network Error Details:', {
          message: error.networkError.message,
          name: error.networkError.name,
          statusCode: (error.networkError as any).statusCode,
          bodyText: (error.networkError as any).bodyText,
        });
      }
      // Log the GraphQL URL being used
      const graphqlUrl = require('../../../config/api').API_GRAPHQL;
      logger.log('🔗 GraphQL URL:', graphqlUrl);
    }
    if (data?.dayTradingPicks) {
      logger.log('📊 Day Trading Data:', JSON.stringify(data.dayTradingPicks, null, 2));
      logger.log('📊 Picks Array:', data.dayTradingPicks.picks);
      logger.log('📊 Picks Length:', data.dayTradingPicks.picks?.length ?? 0);
    } else if (data) {
      logger.log('📊 Data (no dayTradingPicks):', JSON.stringify(data, null, 2));
    }
    if (loading) {
      logger.log('⏳ Loading state:', loading);
    }
  }
  
  const dayTradingData: DayTradingData | null = data?.dayTradingPicks ?? null;

  // Generate mode-specific mock data (should rarely be used - backend provides mock data)
  // This is only a last-resort fallback if backend data is completely unavailable
  const getMockPicks = useCallback((): DayTradingPick[] => {
    if (mode === 'SAFE') {
      // SAFE mode: Large-cap, stable stocks
      return [
        {
          symbol: 'MSFT',
          side: 'LONG',
          score: 2.3,
          features: {
            momentum15m: 0.015,
            rvol10m: 1.8,
            vwapDist: 0.01,
            breakoutPct: 0.02,
            spreadBps: 3.0,
            catalystScore: 0.7,
            executionQualityScore: 0.85,
          },
          risk: {
            atr5m: 2.5,
            sizeShares: 100,
            stop: 375.0,
            targets: [388.0, 395.0],
            timeStopMin: 45,
          },
          notes: 'Large-cap momentum breakout with low volatility setup',
        },
        {
          symbol: 'GOOGL',
          side: 'LONG',
          score: 2.1,
          features: {
            momentum15m: 0.012,
            rvol10m: 1.6,
            vwapDist: 0.008,
            breakoutPct: 0.018,
            spreadBps: 2.5,
            catalystScore: 0.65,
            executionQualityScore: 0.82,
          },
          risk: {
            atr5m: 2.2,
            sizeShares: 100,
            stop: 137.0,
            targets: [141.0, 144.0],
            timeStopMin: 45,
          },
          notes: 'Stable large-cap with conservative risk parameters',
        },
        {
          symbol: 'JPM',
          side: 'LONG',
          score: 1.9,
          features: {
            momentum15m: 0.01,
            rvol10m: 1.5,
            vwapDist: 0.006,
            breakoutPct: 0.015,
            spreadBps: 3.5,
            catalystScore: 0.6,
            executionQualityScore: 0.8,
          },
          risk: {
            atr5m: 2.0,
            sizeShares: 100,
            stop: 157.0,
            targets: [161.0, 164.0],
            timeStopMin: 45,
          },
          notes: 'Financial sector momentum with high liquidity',
        },
      ];
    } else {
      // AGGRESSIVE mode: Growth/mid-cap stocks
      return [
        {
          symbol: 'TSLA',
          side: 'LONG',
          score: 2.8,
          features: {
            momentum15m: 0.045,
            rvol10m: 2.5,
            vwapDist: 0.025,
            breakoutPct: 0.055,
            spreadBps: 8.0,
            catalystScore: 0.9,
            executionQualityScore: 0.88,
          },
          risk: {
            atr5m: 4.5,
            sizeShares: 75,
            stop: 240.0,
            targets: [255.0, 265.0],
            timeStopMin: 25,
          },
          notes: 'High volatility growth stock with strong momentum',
        },
        {
          symbol: 'NVDA',
          side: 'LONG',
          score: 2.6,
          features: {
            momentum15m: 0.038,
            rvol10m: 2.3,
            vwapDist: 0.022,
            breakoutPct: 0.048,
            spreadBps: 6.5,
            catalystScore: 0.85,
            executionQualityScore: 0.9,
          },
          risk: {
            atr5m: 5.0,
            sizeShares: 50,
            stop: 480.0,
            targets: [505.0, 520.0],
            timeStopMin: 25,
          },
          notes: 'Tech momentum play with higher risk/reward',
        },
        {
          symbol: 'PLTR',
          side: 'SHORT',
          score: 2.2,
          features: {
            momentum15m: -0.032,
            rvol10m: 2.0,
            vwapDist: -0.018,
            breakoutPct: 0.035,
            spreadBps: 10.0,
            catalystScore: 0.75,
            executionQualityScore: 0.75,
          },
          risk: {
            atr5m: 3.5,
            sizeShares: 100,
            stop: 18.5,
            targets: [17.0, 16.0],
            timeStopMin: 25,
          },
          notes: 'Reversal setup in volatile growth stock',
        },
      ];
    }
  }, [mode]);

  // Use real data from API, fallback to mock data for testing
  const effectiveData = dayTradingData;

  // Use real data from API, with mock data fallback for testing educational features
  // Also use mock data if there's a network error (similar to Budget/Spending screens)
  const picks = useMemo(() => {
    if (__DEV__) {
      logger.log('🔍 useMemo picks - effectiveData:', effectiveData);
      logger.log('🔍 useMemo picks - effectiveData?.picks:', effectiveData?.picks);
      logger.log('🔍 useMemo picks - effectiveData?.picks?.length:', effectiveData?.picks?.length ?? 0);
      if (error) {
        logger.log('⚠️ Network error detected, will use mock data:', error.message);
      }
      if (effectiveData) {
        logger.log('📊 Diagnostics:', {
          scanned: effectiveData.scannedCount,
          passedLiquidity: effectiveData.passedLiquidity,
          passedQuality: effectiveData.passedQuality,
          failedFetch: effectiveData.failedDataFetch,
          filteredMicrostructure: effectiveData.filteredByMicrostructure,
          filteredVolatility: effectiveData.filteredByVolatility,
          filteredMomentum: effectiveData.filteredByMomentum,
        });
      }
    }
    
    // If there's a network error, use mock data immediately
    if (error && !effectiveData?.picks) {
      if (__DEV__) {
        logger.log('⚠️ Network error - using mock data for development');
      }
      return getMockPicks();
    }
    
    if (effectiveData?.picks && effectiveData.picks.length > 0) {
      // Backend now returns up to 10 picks - use all of them
      const result = effectiveData.picks;
      if (__DEV__) {
        logger.log('✅ Returning picks:', result.length, result.map(p => p.symbol));
      }
      return result;
    }
    // Return mock data if no real data available (for testing educational features)
    if (__DEV__) {
      logger.log('⚠️ No picks available - returning mock data for testing');
    }
    return getMockPicks();
  }, [dayTradingData?.picks, getMockPicks, error]);

  // Use real data for metadata display
  const effectiveDayTradingData: DayTradingData | null = dayTradingData;

  // --- helpers ---
  const isMarketHours = useCallback(() => {
    // simple NYSE approximation; adjust if you already store tz server-side
    const now = new Date();
    const day = now.getDay(); // 0 Sun ... 6 Sat
    if (day === 0 || day === 6) return false;
    const h = now.getHours();
    const m = now.getMinutes();
    const mins = h * 60 + m;
    // 9:30–16:00 local time
    return mins >= 9 * 60 + 30 && mins <= 16 * 60;
  }, []);

  const getMarketStatus = useCallback(() => {
    const now = new Date();
    const day = now.getDay(); // 0 Sun ... 6 Sat
    const dayName = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][day];
    
    if (day === 0 || day === 6) {
      return {
        isOpen: false,
        message: `Markets are closed (${dayName}). Trading resumes Monday–Friday, 9:30 AM–4:00 PM ET.`,
        isWeekend: true,
      };
    }
    
    const h = now.getHours();
    const m = now.getMinutes();
    const mins = h * 60 + m;
    const marketOpen = 9 * 60 + 30; // 9:30 AM
    const marketClose = 16 * 60; // 4:00 PM
    
    if (mins < marketOpen) {
      return {
        isOpen: false,
        message: `Markets open at 9:30 AM ET. Pre-market activity may be limited.`,
        isPreMarket: true,
      };
    }
    
    if (mins > marketClose) {
      return {
        isOpen: false,
        message: `Markets closed at 4:00 PM ET. After-hours activity may be limited.`,
        isAfterHours: true,
      };
    }
    
    return {
      isOpen: true,
      message: 'Markets are open',
    };
  }, []);

  const fetchQuotes = useCallback(async (symbols: string[]) => {
    if (!symbols.length) return;

    // Generate mock quotes for mock picks (when backend returns empty)
    const mockQuotes: Record<string, TradingQuote> = {
      'AAPL': {
        symbol: 'AAPL',
        currentPrice: 150.0,
        change: 1.5,
        changePercent: 1.01,
        volume: 50000000,
        bid: 149.95,
        ask: 150.05,
      },
      'TSLA': {
        symbol: 'TSLA',
        currentPrice: 172.5,
        change: -2.3,
        changePercent: -1.32,
        volume: 80000000,
        bid: 172.40,
        ask: 172.60,
      },
      'NVDA': {
        symbol: 'NVDA',
        currentPrice: 180.0,
        change: 3.2,
        changePercent: 1.81,
        volume: 60000000,
        bid: 179.90,
        ask: 180.10,
      },
    };

    const quotePromises = symbols.map((s) =>
      client.query({
        query: GET_TRADING_QUOTE,
        variables: { symbol: s },
      }).catch(() => {
        // If query fails, return mock quote if available
        if (mockQuotes[s]) {
          return { data: { tradingQuote: mockQuotes[s] } };
        }
        return { data: null };
      }),
    );

    try {
      const results = await Promise.all(quotePromises);
      const newQuotes = results.reduce((acc: Record<string, TradingQuote>, res, i) => {
        if (res.data?.tradingQuote) {
          const quote = res.data.tradingQuote as TradingQuote;
          // Compute currentPrice from bid/ask if not provided
          if (!quote.currentPrice && quote.bid && quote.ask) {
            quote.currentPrice = (quote.bid + quote.ask) / 2;
          }
          acc[symbols[i]] = quote;
        } else if (mockQuotes[symbols[i]]) {
          // Use mock quote if real quote failed
          acc[symbols[i]] = mockQuotes[symbols[i]];
        }
        return acc;
      }, {});

      setQuotes((prev) => ({ ...prev, ...newQuotes }));
    } catch (e) {
      logger.error('Failed to fetch quotes', e);
      // Fallback to mock quotes on error
      const mockOnlyQuotes = symbols.reduce((acc, s) => {
        if (mockQuotes[s]) {
          acc[s] = mockQuotes[s];
        }
        return acc;
      }, {} as Record<string, TradingQuote>);
      if (Object.keys(mockOnlyQuotes).length > 0) {
        setQuotes((prev) => ({ ...prev, ...mockOnlyQuotes }));
      }
    }
  }, [client]);

  const fetchCharts = useCallback(async (symbols: string[]) => {
    if (!symbols.length) return;

    const missingCharts = symbols.filter((s) => !charts[s]);
    if (!missingCharts.length) return;

    // Temporarily use mock chart data to avoid 400 errors
    try {
      const newCharts = missingCharts.reduce((acc, symbol) => {
        // Generate mock chart data (30 data points with some variation)
        // Compute currentPrice from bid/ask if not available
        const quote = quotes[symbol];
        const basePrice = quote?.currentPrice || 
                         (quote?.bid && quote?.ask ? (quote.bid + quote.ask) / 2 : 100);
        const mockData = Array.from({ length: 30 }, (_, i) => {
          const variation = (Math.random() - 0.5) * 0.1; // ±5% variation
          return basePrice * (1 + variation);
        });
        acc[symbol] = mockData;
        return acc;
      }, {} as Record<string, number[]>);

      setCharts((prev) => ({ ...prev, ...newCharts }));
      logger.log('📊 Using mock chart data for symbols:', missingCharts);
    } catch (e) {
      logger.error('Failed to generate mock charts', e);
    }

    // Future enhancement: Re-enable real chart fetching once backend 400 errors are resolved
    // Tracked in: Backend API error handling improvements
    // const chartPromises = missingCharts.map((s) =>
    //   client.query({
    //     query: GET_STOCK_CHART_DATA,
    //     variables: { symbol: s, timeframe: '1D' },
    //   }),
    // );

    // try {
    //   const results = await Promise.all(chartPromises);
    //   const newCharts = results.reduce((acc, res, i) => {
    //     if (res.data?.stockChartData?.data) {
    //       interface ChartDataPoint {
    //         close: number;
    //         [key: string]: unknown;
    //       }
    //       const closes = res.data.stockChartData.data.map((d: ChartDataPoint) => d.close);
    //       acc[missingCharts[i]] = closes;
    //     }
    //     return acc;
    //   }, {} as Record<string, number[]>);

    //   setCharts((prev) => ({ ...prev, ...newCharts }));
    // } catch (e) {
    //   logger.error('Failed to fetch charts', e);
    // }
  }, [charts, quotes]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      // Force network fetch (bypass cache) - fetchPolicy is set to 'network-only' in useQuery
      if (__DEV__) {
        logger.log('🔄 Refreshing picks for mode:', mode);
        // Clear Apollo cache for this query to ensure fresh data and schema
        try {
          await client.cache.evict({ fieldName: 'dayTradingPicks' });
          await client.cache.gc();
          // Also reset the cache to force schema refresh
          await client.resetStore();
        } catch (e) {
          logger.log('⚠️ Cache clear error (non-fatal):', e);
        }
      }
      const result = await refetch({ mode });
      if (__DEV__) {
        logger.log('🔄 Refetch result:', JSON.stringify(result.data?.dayTradingPicks, null, 2));
        logger.log('🔄 Refetch picks count:', result.data?.dayTradingPicks?.picks?.length ?? 0);
        if (result.data?.dayTradingPicks?.picks) {
          logger.log('🔄 Refetch picks symbols:', result.data.dayTradingPicks.picks.map((p: DayTradingPick) => p.symbol));
        }
      }
      const symbols = [...new Set(picks.map((p) => p.symbol))];
      await fetchQuotes(symbols);
      await fetchCharts(symbols);
    } catch (err) {
      if (__DEV__) {
        logger.error('❌ Refresh error:', err);
      }
    } finally {
      setRefreshing(false);
    }
  }, [mode, refetch, picks, fetchQuotes, fetchCharts, client]);

  const handleModeChange = useCallback(
    async (newMode: TradingMode) => {
      if (newMode === mode) return;
      setMode(newMode);
      // refetch immediately on toggle for snappy UX
      await refetch({ mode: newMode });
      const symbols = [...new Set(picks.map((p) => p.symbol))];
      await fetchQuotes(symbols);
      await fetchCharts(symbols);
    },
    [mode, refetch, picks, fetchQuotes, fetchCharts],
  );

  // Handle visible items change
  const onViewableItemsChanged = useCallback(({ viewableItems }: { viewableItems: any[] }) => {
    const newVisible = new Set(viewableItems.map((item: any) => item.item?.symbol || item.symbol).filter(Boolean));
    setVisibleSymbols(newVisible);
    fetchCharts(Array.from(newVisible));
  }, [fetchCharts]);

  const viewabilityConfig = useMemo(
    () => ({
      itemVisiblePercentThreshold: 50,
      minimumViewTime: 1000,
    }),
    [],
  );

  // Fetch data when picks change
  useEffect(() => {
    const symbols = [...new Set(picks.map((p) => p.symbol))];
    fetchQuotes(symbols);
    fetchCharts(symbols);
  }, [picks, fetchQuotes, fetchCharts]);

  // polling during market hours
  useEffect(() => {
    // if you're already using Apollo polling, this is enough:
    if (isMarketHours()) startPolling?.(60_000);
    else stopPolling?.();

    // extra safety: manual interval (kept off by default)
    if (pollingRef.current) clearInterval(pollingRef.current);
    if (isMarketHours()) {
      pollingRef.current = setInterval(() => {
        refetch({ mode }).catch(() => {});
        const symbols = [...new Set(picks.map((p) => p.symbol))];
        fetchQuotes(symbols);
      }, 30000); // Poll quotes every 30 seconds
    }
    return () => {
      stopPolling?.();
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [mode, isMarketHours, refetch, startPolling, stopPolling, picks, fetchQuotes]);

  // Separate polling for charts (less frequent)
  useEffect(() => {
    if (chartPollingRef.current) clearInterval(chartPollingRef.current);
    if (isMarketHours()) {
      chartPollingRef.current = setInterval(() => {
        fetchCharts(Array.from(visibleSymbols));
      }, 60000); // Poll charts every 60 seconds for visible items only
    }
    return () => {
      if (chartPollingRef.current) clearInterval(chartPollingRef.current);
    };
  }, [isMarketHours, visibleSymbols, fetchCharts]);

  // ---- UI color system ----
  const C = useMemo(
    () => ({
      bg: '#FAFBFC',
      card: '#FFFFFF',
      text: '#1A202C',
      sub: '#718096',
      border: '#E9ECEF',
      primary: '#3182CE',
      safe: '#38A169',
      aggressive: '#D69E2E',
      long: '#38A169',
      short: '#E53E3E',
      warnBg: '#FEFCBF',
      warnBorder: '#FAD999',
      warnText: '#B7791F',
      warning: '#F59E0B', // Amber/warning color
      amber: '#F59E0B', // Amber color
      red: '#E53E3E', // Red color
      shadow: 'rgba(0, 0, 0, 0.06)',
      shadowLight: 'rgba(0, 0, 0, 0.04)',
    }),
    [],
  );

  const getModeColor = (m: TradingMode) => (m === 'SAFE' ? C.safe : C.aggressive);
  const getSideColor = (side: Side) => (side === 'LONG' ? C.long : C.short);
  const getScoreColor = (score: number) => (score >= 2 ? C.long : score >= 1 ? C.aggressive : C.short);
  const getChangeColor = (changePercent: number) => (changePercent >= 0 ? C.long : C.short);

  // robust entry computation (use atr around stop; invert for SHORT)
  const computeEntry = (pick: DayTradingPick) => {
    const stop = pick.risk?.stop ?? 0;
    const atr = pick.risk?.atr5m ?? 0;
    return pick.side === 'LONG' ? stop + atr : Math.max(0, stop - atr);
  };

  const handleTradeExecution = useCallback(
    (pick: DayTradingPick) => {
      const entry = computeEntry(pick);
      const primaryTarget = pick.risk.targets?.[0] ?? entry;
      Alert.alert(
        'Execute Trade',
        `Execute ${pick.side} ${pick.symbol}?\n\nEntry: $${(entry ?? 0).toFixed(2)}\nStop: $${(pick.risk?.stop ?? 0).toFixed(
          2,
        )}\nTarget: $${Number(primaryTarget ?? 0).toFixed(2)}\nSize: ${pick.risk?.sizeShares ?? 0} shares`,
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Execute',
            onPress: async () => {
              // Place your real order here (brokerage/OMS). After submission, log a provisional outcome.
              try {
                await logOutcome({
                  variables: {
                    input: {
                      symbol: pick.symbol,
                      side: pick.side,
                      mode,
                      entryPrice: entry,
                      stopPrice: pick.risk.stop,
                      targetPrice: primaryTarget,
                      sizeShares: pick.risk.sizeShares,
                      features: pick.features,
                      score: pick.score,
                      executedAt: new Date().toISOString(),
                      // you can add clientOrderId here for reconciliation
                    },
                  },
                });
              } catch (e) {
                // Non-blocking: trade might still be placed; this is just telemetry
                logger.warn('Outcome log failed', e);
              }
              Alert.alert('Trade Submitted', `${pick.side} ${pick.symbol} sent`);
            },
          },
        ],
      );
    },
    [logOutcome, mode],
  );

  // MemoizedPick is now defined outside this component (see below)
  // This prevents it from being recreated on every render

  // Use refs to keep handlers stable - they never change identity
  const navigateToRef = useRef(navigateTo);
  useEffect(() => {
    navigateToRef.current = navigateTo;
  }, [navigateTo]);

  // Stable wrapper callbacks that never change - they use refs internally
  const handleRiskPress = useCallback(() => {
    navigateToRef.current?.('risk-management');
  }, []); // Empty deps - this callback never changes

  const handleMLPress = useCallback(() => {
    navigateToRef.current?.('ml-system');
  }, []); // Empty deps - this callback never changes

  const handleBackPress = useCallback(() => {
    navigateToRef.current?.('trading');
  }, []); // Empty deps - this callback never changes

  // Memoize header buttons - only recreate if navigateTo existence changes
  const headerButtonsElement = useMemo(() => {
    if (!navigateTo) return null;
    
    if (__DEV__) {
      logger.log('🔧 Creating HeaderButtons element');
    }
    
    return (
      <HeaderButtons
        onRiskPress={handleRiskPress}
        onMLPress={handleMLPress}
      />
    );
  }, [!!navigateTo, handleRiskPress, handleMLPress]); // Only recreate if navigateTo existence changes

  // ---- header / top ----
  // Memoize just the top header bar separately to keep buttons stable
  const HeaderTopBar = useMemo(() => {
    if (__DEV__) {
      logger.log('🔧 Creating HeaderTopBar');
    }
    
    return (
      <View style={[styles.header, { backgroundColor: C.card, borderBottomColor: C.border }]}>
        <View style={styles.headerRow}>
          <View style={styles.headerLeft}>
            {navigateTo && (
              <TouchableOpacity 
                style={styles.backBtn} 
                onPress={handleBackPress} 
                accessibilityRole="button" 
                accessibilityLabel="Back"
              >
                <Icon name="arrow-left" size={20} color={C.primary} />
              </TouchableOpacity>
            )}
            <View style={styles.headerText}>
              <Text style={[styles.title, { color: C.text }]}>Trading</Text>
              <Text style={[styles.subtitle, { color: C.sub }]}>Execute trades and manage signals</Text>
            </View>
          </View>
          {headerButtonsElement}
        </View>
      </View>
    );
  }, [!!navigateTo, handleBackPress, headerButtonsElement]); // Only recreate if navigateTo existence changes

  const Header = useMemo(() => (
    <View>
      {HeaderTopBar}

      {/* Mode Toggle */}
      <View style={[styles.modeWrap, { backgroundColor: C.card, shadowColor: '#000' }]}>
        <View style={styles.modeHeader}>
          <View style={styles.modeHeaderLeft}>
            <Icon name="toggle-left" size={16} color={C.sub} />
            <Text style={[styles.modeTitle, { color: C.text }]}>Trading Mode</Text>
          </View>
          <View style={{ flexDirection: 'row', gap: 8, alignItems: 'center' }}>
            {selectedPick && (
              <TouchableOpacity
                style={[styles.executionQualityButton, { backgroundColor: '#3B82F6' + '20' }]}
                onPress={() => setShowWhisper(true)}
              >
                <Icon name="eye" size={14} color="#3B82F6" />
                <Text style={[styles.executionQualityButtonText, { color: '#3B82F6' }]}>
                  See Your Likely Outcome
                </Text>
              </TouchableOpacity>
            )}
            <TouchableOpacity
              style={[styles.executionQualityButton, { backgroundColor: C.primary + '20' }]}
              onPress={() => setShowExecutionQuality(!showExecutionQuality)}
            >
              <Icon name="activity" size={14} color={C.primary} />
              <Text style={[styles.executionQualityButtonText, { color: C.primary }]}>
                Execution Quality
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.infoDot}
              onPress={() =>
                Alert.alert(
                  'Trading Modes',
                  'SAFE: Conservative picks with tighter thresholds and liquidity filters.\n\nAGGRESSIVE: Higher-variance picks with looser filters and broader universe.\n\nPosition sizing/time-stop differ by mode.',
                )
              }
            >
              <Text style={{ fontWeight: '700', color: C.sub }}>i</Text>
            </TouchableOpacity>
          </View>
        </View>
        <View style={styles.modeGroup}>
          <TouchableOpacity
            style={[styles.modeBtn, mode === 'SAFE' && { backgroundColor: getModeColor('SAFE') }]}
            onPress={() => handleModeChange('SAFE')}
          >
            <Text style={[styles.modeBtnText, mode === 'SAFE' ? styles.modeBtnTextActive : { color: C.sub }]}>SAFE</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.modeBtn, mode === 'AGGRESSIVE' && { backgroundColor: getModeColor('AGGRESSIVE') }]}
            onPress={() => handleModeChange('AGGRESSIVE')}
          >
            <Text
              style={[styles.modeBtnText, mode === 'AGGRESSIVE' ? styles.modeBtnTextActive : { color: C.sub }]}
            >
              AGGRESSIVE
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Mode Info */}
      <View style={[styles.infoStrip, { backgroundColor: '#EBF4FF' }]}>
        <Text style={[styles.infoText, { color: C.primary }]}>
          {mode === 'SAFE'
            ? '0.5% risk per trade • 45 min time-stop • Large-cap/liquid universe'
            : '1.2% risk per trade • 25 min time-stop • Extended universe'}
        </Text>
        {effectiveDayTradingData?.universeSource === 'DYNAMIC_MOVERS' && (
          <Text style={[styles.infoText, { color: C.primary, fontSize: 11, marginTop: 4, fontStyle: 'italic' }]}>
            Scanning today's biggest movers, then filtering through RichesReach risk rules
          </Text>
        )}
      </View>

      {/* Execution Quality Dashboard */}
      {showExecutionQuality && (
        <View style={[styles.executionQualitySection, { backgroundColor: C.card }]}>
          <View style={styles.executionQualityHeader}>
            <Text style={[styles.executionQualityTitle, { color: C.text }]}>Execution Quality Metrics</Text>
            <TouchableOpacity onPress={() => setShowExecutionQuality(false)}>
              <Icon name="x" size={20} color={C.sub} />
            </TouchableOpacity>
          </View>
          <ExecutionQualityDashboard signalType="day_trading" days={30} />
        </View>
      )}

      {/* The Whisper - The One Magical P&L Moment */}
      {showWhisper && selectedPick && (
        <TheWhisperScreen
          symbol={selectedPick.symbol}
          currentPrice={quotes[selectedPick.symbol]?.currentPrice || 0}
          change={quotes[selectedPick.symbol]?.change || 0}
          changePercent={quotes[selectedPick.symbol]?.changePercent || 0}
          onTakeTrade={() => {
            setShowWhisper(false);
            handleTradeExecution(selectedPick);
          }}
          onJustWatching={() => setShowWhisper(false)}
        />
      )}

      {/* Market Status */}
      {effectiveDayTradingData && (
        <View style={[styles.marketBox, { backgroundColor: C.card }]}>
          <View style={styles.marketRow}>
            <Icon name="clock" size={14} color={C.sub} />
            <Text style={[styles.marketText, { color: C.sub, marginLeft: 8 }]}>
              Last Updated: {(() => {
                if (!effectiveDayTradingData.asOf) return 'Just now';
                try {
                  const date = new Date(effectiveDayTradingData.asOf);
                  if (isNaN(date.getTime())) return 'Just now';
                  return date.toLocaleTimeString();
                } catch {
                  return 'Just now';
                }
              })()}
            </Text>
          </View>
          <View style={styles.marketRow}>
            <Icon name="globe" size={14} color={C.sub} />
            <Text style={[styles.marketText, { color: C.sub, marginLeft: 8 }]}>
              Universe: {effectiveDayTradingData.universeSize ?? 0} • Threshold: {effectiveDayTradingData.qualityThreshold ?? 'N/A'}
            </Text>
          </View>
          {effectiveDayTradingData.universeSource && (
            <View style={styles.marketRow}>
              <Icon 
                name={effectiveDayTradingData.universeSource === 'DYNAMIC_MOVERS' ? 'trending-up' : 'layers'} 
                size={14} 
                color={effectiveDayTradingData.universeSource === 'DYNAMIC_MOVERS' ? C.primary : C.sub} 
              />
              <Text style={[styles.marketText, { 
                color: effectiveDayTradingData.universeSource === 'DYNAMIC_MOVERS' ? C.primary : C.sub, 
                marginLeft: 8,
                fontWeight: effectiveDayTradingData.universeSource === 'DYNAMIC_MOVERS' ? '600' : '400'
              }]}>
                Source: {effectiveDayTradingData.universeSource === 'DYNAMIC_MOVERS' 
                  ? 'Dynamic Discovery (Polygon movers)' 
                  : 'Core Universe'}
              </Text>
            </View>
          )}
        </View>
      )}
    </View>
  ), [navigateTo, mode, handleModeChange, effectiveDayTradingData, handleBackPress, HeaderTopBar, C, getModeColor]);

  // Only show real data - empty state is handled by ListEmptyComponent

  return (
    <OnboardingGuard 
      requireKYC={true}
      onNavigateToOnboarding={handleNavigateToOnboarding}
    >
      <PanGestureHandler
        onGestureEvent={handleGesture}
        onHandlerStateChange={handleGesture}
      >
        <View style={[styles.container, { backgroundColor: C.bg }]}>
          {/* Selected Pick Indicator */}
          {selectedPick && (
            <View style={styles.selectedPickIndicator}>
              <Text style={styles.selectedPickText}>
                Selected: {selectedPick.symbol} - Swipe to trade
              </Text>
            </View>
          )}

          {/* Gesture Feedback */}
          {isGestureActive && gestureDirection && (
            <View style={styles.gestureFeedback}>
              <Text style={styles.gestureFeedbackText}>
                {gestureDirection === 'RIGHT' && '→ LONG'}
                {gestureDirection === 'LEFT' && '← SHORT'}
                {gestureDirection === 'UP' && '↑ AGGRESSIVE'}
                {gestureDirection === 'DOWN' && '↓ SAFE'}
              </Text>
            </View>
          )}

          {/* Error Banner (if using mock data due to network error) */}
          {error && picks.length > 0 && (
            <View style={[styles.errorBanner, { backgroundColor: C.warning + '20', borderLeftColor: C.warning }]}>
              <Icon name="alert-triangle" size={16} color={C.warning} />
              <Text style={[styles.errorBannerText, { color: C.warning }]}>
                Using mock data - Backend connection failed. {error.networkError?.message || error.message}
              </Text>
              <TouchableOpacity 
                onPress={() => refetch({ mode })}
                style={styles.retryButtonSmall}
              >
                <Text style={[styles.retryButtonText, { color: C.warning, fontSize: 12 }]}>Retry</Text>
              </TouchableOpacity>
            </View>
          )}

          {/* Loading, Error, or Picks List */}
          {loading && picks.length === 0 ? (
            <View style={styles.emptyWrap}>
              <ActivityIndicator size="large" color={C.primary} />
              <Text style={[styles.emptyTitle, { color: C.sub, marginTop: 16 }]}>Loading picks...</Text>
            </View>
          ) : error && picks.length === 0 ? (
            <View style={[styles.emptyWrap, { padding: 20 }]}>
              <Icon name="alert-circle" size={48} color={C.short} />
              <Text style={[styles.emptyTitle, { color: C.short, marginTop: 16 }]}>Error loading picks</Text>
              <Text style={[styles.emptySub, { color: C.sub, marginTop: 8 }]}>
                {(() => {
                  // Show more detailed error information
                  if (error.networkError) {
                    return `Network error: ${error.networkError.message || 'Unable to connect to server'}`;
                  }
                  if (error.graphQLErrors && error.graphQLErrors.length > 0) {
                    return `GraphQL error: ${error.graphQLErrors[0].message}`;
                  }
                  return error.message || 'Unknown error occurred';
                })()}
              </Text>
              {__DEV__ && error && (
                <Text style={[styles.emptySub, { color: C.sub, marginTop: 8, fontSize: 10 }]}>
                  Debug: {JSON.stringify({
                    message: error.message,
                    networkError: error.networkError?.message,
                    graphQLErrors: error.graphQLErrors?.map(e => e.message),
                  }, null, 2)}
                </Text>
              )}
              <TouchableOpacity 
                style={[styles.retryButton, { backgroundColor: C.primary, marginTop: 16 }]}
                onPress={() => refetch({ mode })}
              >
                <Text style={[styles.retryButtonText, { color: '#fff' }]}>Retry</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <FlatList
              data={picks}
              keyExtractor={(item) => `${item.symbol}-${item.side}`}
              ListHeaderComponent={Header}
              renderItem={({ item }) => (
                <MemoizedPick
                  item={item}
                  quotes={quotes}
                  charts={charts}
                  C={C}
                  selectedPick={selectedPick}
                  selectPick={selectPick}
                  computeEntry={computeEntry}
                  handleTradeExecution={handleTradeExecution}
                  setShowWhyThisTrade={setShowWhyThisTrade}
                />
              )}
              contentContainerStyle={{ paddingBottom: 24 }}
              refreshControl={<RefreshControl refreshing={refreshing || networkStatus === 4} onRefresh={onRefresh} tintColor={C.primary} />}
              initialNumToRender={5}
              maxToRenderPerBatch={5}
              windowSize={10}
              removeClippedSubviews={true}
              onViewableItemsChanged={onViewableItemsChanged}
              viewabilityConfig={viewabilityConfig}
              ListEmptyComponent={
                <View style={styles.emptyWrap}>
                  <Icon name="inbox" size={64} color={C.sub} />
                  <Text style={[styles.emptyTitle, { color: C.sub }]}>No qualifying picks for {mode} mode</Text>
                  
                  {/* Market status message */}
                  {(() => {
                    const marketStatus = getMarketStatus();
                    if (!marketStatus.isOpen) {
                      return (
                        <View style={{ marginTop: 16, padding: 16, backgroundColor: C.bg, borderRadius: 12, width: '100%', marginBottom: 8 }}>
                          <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 8 }}>
                            <Icon name="clock" size={20} color={C.amber} style={{ marginRight: 8 }} />
                            <Text style={[styles.emptySub, { color: C.amber, fontWeight: '700', fontSize: 14 }]}>
                              Markets Closed
                            </Text>
                          </View>
                          <Text style={[styles.emptySub, { color: C.sub, fontSize: 12, lineHeight: 18 }]}>
                            {marketStatus.message}
                          </Text>
                          {marketStatus.isWeekend && (
                            <Text style={[styles.emptySub, { color: C.sub, fontSize: 11, marginTop: 8, fontStyle: 'italic' }]}>
                              This is normal behavior. Picks will populate when markets reopen.
                            </Text>
                          )}
                        </View>
                      );
                    }
                    return (
                      <Text style={[styles.emptySub, { color: C.sub }]}>
                        Quality threshold not met or market conditions unsuitable
                      </Text>
                    );
                  })()}
                  {dayTradingData && (
                    <View style={{ marginTop: 16, padding: 16, backgroundColor: C.bg, borderRadius: 12, width: '100%' }}>
                      <Text style={[styles.emptySub, { color: C.sub, fontSize: 12, marginBottom: 8 }]}>
                        Diagnostic Info:
                      </Text>
                      <Text style={[styles.emptySub, { color: C.sub, fontSize: 11 }]}>
                        Scanned: {dayTradingData.scannedCount ?? dayTradingData.universeSize} symbols
                      </Text>
                      {dayTradingData.failedDataFetch !== undefined && dayTradingData.failedDataFetch > 0 && (
                        <Text style={[styles.emptySub, { color: C.red, fontSize: 11 }]}>
                          Failed data fetch: {dayTradingData.failedDataFetch} (market closed or API issues)
                        </Text>
                      )}
                      {dayTradingData.passedLiquidity !== undefined && (
                        <Text style={[styles.emptySub, { color: C.sub, fontSize: 11 }]}>
                          Passed liquidity: {dayTradingData.passedLiquidity}
                        </Text>
                      )}
                      {dayTradingData.passedQuality !== undefined && (
                        <Text style={[styles.emptySub, { color: C.sub, fontSize: 11 }]}>
                          Passed quality threshold: {dayTradingData.passedQuality}
                        </Text>
                      )}
                      {(dayTradingData.filteredByVolatility !== undefined || 
                        dayTradingData.filteredByMomentum !== undefined || 
                        dayTradingData.filteredByMicrostructure !== undefined) && (
                        <Text style={[styles.emptySub, { color: C.sub, fontSize: 11, marginTop: 8 }]}>
                          Filtered by: Volatility ({dayTradingData.filteredByVolatility ?? 0}), 
                          Momentum ({dayTradingData.filteredByMomentum ?? 0}), 
                          Microstructure ({dayTradingData.filteredByMicrostructure ?? 0})
                        </Text>
                      )}
                    </View>
                  )}
                  <TouchableOpacity 
                    style={[styles.retryButton, { backgroundColor: C.primary, marginTop: 16 }]}
                    onPress={() => {
                      if (__DEV__) {
                        logger.log('🔄 Manual retry triggered');
                      }
                      refetch({ mode });
                    }}
                  >
                    <Text style={[styles.retryButtonText, { color: '#fff' }]}>Force Refresh</Text>
                  </TouchableOpacity>
                </View>
              }
              ListFooterComponent={
                <View style={[styles.disclaimer, { borderLeftColor: C.warnBorder, backgroundColor: C.warnBg, marginTop: 20 }]}>
                  <Icon name="alert-circle" size={16} color={C.warnText} style={{ marginRight: 8 }} />
                  <Text style={[styles.disclaimerText, { color: C.warnText }]}>
                    Day trading involves significant risk. Only trade with capital you can afford to lose. Past performance does
                    not guarantee future results.
                  </Text>
                </View>
              }
            />
          )}
        </View>
      </PanGestureHandler>
      
      {/* Why This Trade Modal - Outside PanGestureHandler */}
      {showWhyThisTrade && (() => {
        const pick = showWhyThisTrade;
        const entry = computeEntry(pick);
        const target = pick.risk?.targets?.[0] ?? entry;
        const risk = Math.abs(entry - (pick.risk?.stop ?? 0));
        const reward = Math.abs(target - entry);
        const rrRatio = risk > 0 ? reward / risk : 0;
        
        // Generate trade signals from pick features
        const signals: Array<{
          name: string;
          value: number | string;
          strength: 'strong' | 'moderate' | 'weak';
          explanation: string;
          color: string;
        }> = [
          {
            name: 'Momentum (15m)',
            value: pick.features?.momentum15m ?? 0,
            strength: (pick.features?.momentum15m ?? 0) > 0.5 ? 'strong' : (pick.features?.momentum15m ?? 0) > 0.2 ? 'moderate' : 'weak',
            explanation: `15-minute momentum of ${(pick.features?.momentum15m ?? 0).toFixed(3)} indicates ${pick.side === 'LONG' ? 'upward' : 'downward'} price movement. Higher values suggest stronger momentum.`,
            color: pick.side === 'LONG' ? '#22C55E' : '#EF4444',
          },
          {
            name: 'Relative Volume',
            value: `${(pick.features?.rvol10m ?? 0).toFixed(2)}x`,
            strength: (pick.features?.rvol10m ?? 0) > 2 ? 'strong' : (pick.features?.rvol10m ?? 0) > 1.5 ? 'moderate' : 'weak',
            explanation: `Volume is ${(pick.features?.rvol10m ?? 0).toFixed(2)}x the average, indicating ${(pick.features?.rvol10m ?? 0) > 1.5 ? 'strong' : 'moderate'} interest. Higher volume confirms price moves.`,
            color: '#007AFF',
          },
          {
            name: 'VWAP Distance',
            value: (pick.features?.vwapDist ?? 0).toFixed(3),
            strength: Math.abs(pick.features?.vwapDist ?? 0) > 0.02 ? 'strong' : Math.abs(pick.features?.vwapDist ?? 0) > 0.01 ? 'moderate' : 'weak',
            explanation: `Price is ${Math.abs(pick.features?.vwapDist ?? 0).toFixed(3)} away from VWAP. ${pick.side === 'LONG' ? 'Above' : 'Below'} VWAP suggests ${pick.side === 'LONG' ? 'bullish' : 'bearish'} momentum.`,
            color: '#F59E0B',
          },
          {
            name: 'Breakout Potential',
            value: `${((pick.features?.breakoutPct ?? 0) * 100).toFixed(1)}%`,
            strength: (pick.features?.breakoutPct ?? 0) > 0.03 ? 'strong' : (pick.features?.breakoutPct ?? 0) > 0.01 ? 'moderate' : 'weak',
            explanation: `Breakout potential of ${((pick.features?.breakoutPct ?? 0) * 100).toFixed(1)}% suggests the stock may break through key resistance/support levels.`,
            color: '#8B5CF6',
          },
        ];
        
        return (
          <WhyThisTradeModal
            visible={true}
            onClose={() => setShowWhyThisTrade(null)}
            symbol={pick.symbol}
            side={pick.side}
            signals={signals}
            confidenceScore={pick.score}
            riskRewardRatio={rrRatio}
            entryPrice={entry}
            stopPrice={pick.risk?.stop}
            targetPrice={target}
          />
        );
      })()}
      
      {/* Learn While Trading Modal - Outside PanGestureHandler */}
      <LearnWhileTradingModal
        visible={showLearnModal}
        onClose={() => setShowLearnModal(false)}
        onNavigateToRiskCoach={() => {
          setShowLearnModal(false);
          if (navigateTo) {
            navigateTo('RiskCoach');
          }
        }}
      />
    </OnboardingGuard>
  );
}

/* ============ Small subcomponent ============ */
function KV({ label, value, color, tooltip }: { label: string; value: string; color?: string; tooltip?: { term: string; explanation: string } }) {
  const content = (
    <View style={styles.kvContainer}>
      <View style={styles.kvLabelRow}>
        <Text style={styles.kvLabel} numberOfLines={1} ellipsizeMode="tail">{label}</Text>
        {tooltip && (
          <View style={styles.kvTooltipIcon}>
            <Icon name="info" size={11} color="#94A3B8" />
          </View>
        )}
      </View>
      <Text style={[styles.kvValue, { color: color || '#111827' }]} numberOfLines={1}>{value}</Text>
    </View>
  );

  const wrapper = (
    <View style={styles.kvWrapper}>
      {content}
    </View>
  );

  if (tooltip) {
    return (
      <EducationalTooltip 
        term={tooltip.term} 
        explanation={tooltip.explanation} 
        position="top"
        style={styles.kvWrapper}
        hideExternalIcon={true}
      >
        {content}
      </EducationalTooltip>
    );
  }

  return wrapper;
}

/* ============ MemoizedPick - Top-level component to prevent recreation ============ */
interface MemoizedPickProps {
  item: DayTradingPick;
  quotes: { [key: string]: TradingQuote };
  charts: { [key: string]: number[] };
  C: any;
  selectedPick: DayTradingPick | null;
  selectPick: (pick: DayTradingPick) => void;
  computeEntry: (pick: DayTradingPick) => number;
  handleTradeExecution: (pick: DayTradingPick) => void;
  setShowWhyThisTrade: (pick: DayTradingPick | null) => void;
}

const MemoizedPick = React.memo(function MemoizedPick({
  item,
  quotes,
  charts,
  C,
  selectedPick,
  selectPick,
  computeEntry,
  handleTradeExecution,
  setShowWhyThisTrade,
}: MemoizedPickProps) {
  const entry = computeEntry(item);
  const target = item.risk?.targets?.[0] ?? entry;
  const quote = quotes[item.symbol];
  const chartData = charts[item.symbol] || [];
  // changePercent not available from trading quote (only bid/ask), default to 0
  const changePercent = quote?.changePercent ?? 0;
  const isSelected = selectedPick?.symbol === item.symbol;

  // Helper functions defined inside component
  const getSideColor = (side: Side) => (side === 'LONG' ? C.long : C.short);
  const getScoreColor = (score: number) => (score >= 2 ? C.long : score >= 1 ? C.aggressive : C.short);
  const getChangeColor = (changePercent: number) => (changePercent >= 0 ? C.long : C.short);

  const queryVariables = useMemo(() => {
    const entryPrice = entry || (item.risk?.stop ? item.risk.stop + (item.risk?.atr5m || 1) : undefined);

    const signalObj = {
      symbol: item.symbol,
      side: item.side,
      entry_price: entryPrice,
      risk: {
        stop: item.risk?.stop,
        targets: item.risk?.targets || [],
        sizeShares: item.risk?.sizeShares || 100,
        atr5m: item.risk?.atr5m,
        // atr1d not available in day trading risk type
      },
      features: {
        spreadBps: item.features?.spreadBps || 5.0,
        executionQualityScore: item.features?.executionQualityScore,
      },
    };

    const signalStr = JSON.stringify(signalObj);
    
    // Debug log the signal being sent
    if (__DEV__) {
      logger.log(`📤 [${item.symbol}] Building execution suggestion query:`, {
        signalObj,
        signalStr,
        signalLength: signalStr.length,
      });
    }

    return {
      signal: signalStr,
      signalType: 'day_trading',
    };
  }, [
    item.symbol,
    item.side,
    entry,
    item.risk?.stop,
    item.risk?.targets,
    item.risk?.sizeShares,
    item.risk?.atr5m,
    // item.risk?.atr1d, // atr1d not available in day trading risk type
    item.features?.spreadBps,
    item.features?.executionQualityScore,
  ]);

  const [stableSuggestion, setStableSuggestion] = useState<any>(null);
  const [queryError, setQueryError] = useState<any>(null);
  const [hasTimedOut, setHasTimedOut] = useState(false);

  // Debug: Log query variables to see if they're valid
  if (__DEV__) {
    logger.log(`🔍 [${item.symbol}] Execution suggestion query variables:`, {
      hasSignal: !!queryVariables.signal,
      signalLength: queryVariables.signal?.length,
      signalType: queryVariables.signalType,
      willSkip: !queryVariables.signal,
    });
  }

  const { data, loading, error } = useQuery(GET_EXECUTION_SUGGESTION, {
    variables: queryVariables,
    errorPolicy: 'all',
    fetchPolicy: 'cache-and-network',
    nextFetchPolicy: 'cache-first',
    notifyOnNetworkStatusChange: false,
    returnPartialData: true,
    skip: !queryVariables.signal || !queryVariables.signal.trim(), // Skip if signal is invalid or empty
    onError: (err) => {
      setQueryError(err);
      setHasTimedOut(true);
      if (__DEV__) {
        logger.log(`❌ [${item.symbol}] Execution suggestion query error:`, err);
        logger.log(`❌ [${item.symbol}] Error details:`, {
          message: err.message,
          graphQLErrors: err.graphQLErrors,
          networkError: err.networkError,
        });
      }
    },
    onCompleted: (data) => {
      setQueryError(null);
      setHasTimedOut(false);
      if (__DEV__) {
        logger.log(`✅ [${item.symbol}] Execution suggestion query completed:`, {
          hasData: !!data,
          hasExecutionSuggestion: !!data?.executionSuggestion,
          executionSuggestion: data?.executionSuggestion,
        });
      }
    },
  });

  // Manual timeout: if loading for more than 15 seconds, consider it timed out
  useEffect(() => {
    if (loading && !stableSuggestion) {
      const timeoutId = setTimeout(() => {
        if (loading && !stableSuggestion) {
          setHasTimedOut(true);
          if (__DEV__) {
            logger.log(`⏱️ Execution suggestion query timed out for ${item.symbol} after 15s`);
          }
        }
      }, 15000); // 15 second timeout

      return () => clearTimeout(timeoutId);
    } else {
      setHasTimedOut(false);
    }
  }, [loading, stableSuggestion, item.symbol]);

  // Keep the last GOOD suggestion so the card doesn't blink during refetches
  useEffect(() => {
    const rawSuggestion = data?.executionSuggestion;

    if (__DEV__) {
      logger.log(`🔍 [${item.symbol}] Execution suggestion effect:`, {
        hasData: !!data,
        hasExecutionSuggestion: !!rawSuggestion,
        rawSuggestionKeys: rawSuggestion ? Object.keys(rawSuggestion) : [],
        currentStableSuggestion: !!stableSuggestion,
      });
    }

    if (rawSuggestion) {
      // Accept even partial data - don't require all fields
      setStableSuggestion(rawSuggestion);

      if (__DEV__) {
        logger.log(`✅ Execution suggestion received for ${item.symbol}:`, {
          hasOrderType: 'orderType' in rawSuggestion,
          hasPriceBand: !!rawSuggestion.priceBand,
          hasRationale: !!rawSuggestion.rationale,
          fullData: rawSuggestion,
        });
      }
    } else if (data && !rawSuggestion) {
      // Data exists but no executionSuggestion field - log this
      if (__DEV__) {
        logger.log(`⚠️ [${item.symbol}] Query returned data but no executionSuggestion field:`, data);
      }
    }

    // IMPORTANT: do NOT set stableSuggestion back to null on refetch.
    // If rawSuggestion is null during a refetch, we keep the old suggestion
  }, [data?.executionSuggestion, item.symbol, stableSuggestion]);

  // Debug logging (hook always runs, but only logs in dev)
  useEffect(() => {
    if (!__DEV__) return;

    logger.log(`🔍 ExecutionSuggestion query for ${item.symbol}:`, {
      loading,
      hasData: !!data?.executionSuggestion,
      hasStableData: !!stableSuggestion,
      error: error?.message,
    });
  }, [loading, data, stableSuggestion, error, item.symbol]);

  const effectiveSuggestion = stableSuggestion;
  const isRefreshing = loading && !!effectiveSuggestion;
  
  // Show loading only if actively loading and haven't timed out
  const shouldShowLoading = loading && !effectiveSuggestion && !hasTimedOut && !error;

  // Debug logging for render decision
  if (__DEV__) {
    logger.log(`🎨 [${item.symbol}] Render decision:`, {
      loading,
      hasEffectiveSuggestion: !!effectiveSuggestion,
      hasTimedOut,
      hasError: !!error,
      shouldShowLoading,
      willShowCard: !!effectiveSuggestion && !shouldShowLoading && !hasTimedOut && !(error && !effectiveSuggestion),
    });
    
    if (!effectiveSuggestion && !loading) {
      logger.log(`⚠️ No execution suggestion for ${item.symbol} - error:`, error?.message || queryError?.message);
    }
    if (effectiveSuggestion) {
      logger.log(`✅ Execution suggestion available for ${item.symbol}:`, {
        hasOrderType: !!effectiveSuggestion.orderType,
        hasPriceBand: !!effectiveSuggestion.priceBand,
        hasRationale: !!effectiveSuggestion.rationale,
        suggestion: effectiveSuggestion,
      });
    }
  }

  return (
    <TouchableOpacity
      style={[
        styles.card,
        {
          backgroundColor: C.card,
          borderColor: isSelected ? '#4CAF50' : C.border,
          borderWidth: isSelected ? 2 : 1,
        },
      ]}
      onPress={() => selectPick(item)}
      activeOpacity={0.7}
    >
      <View>
        {/* Header */}
        <View style={styles.pickHeader}>
          <View style={styles.pickSymbolWrap}>
            <View style={styles.symbolIcon}>
              <Icon name="trending-up" size={20} color={getSideColor(item.side)} />
            </View>
            <View style={{ flex: 1 }}>
              <Text
                style={[styles.pickSymbol, { color: C.text }]}
                accessibilityRole="text"
                accessibilityLabel={`Symbol ${item.symbol}`}
              >
                {item.symbol}
              </Text>
              {quote && (
                <View style={styles.changeWrap}>
                  <Text
                    style={[styles.changeValue, { color: getChangeColor(changePercent) }]}
                  >
                    {changePercent >= 0
                      ? `+${changePercent.toFixed(2)}%`
                      : `${changePercent.toFixed(2)}%`}
                  </Text>
                  <Text style={[styles.changeLabel, { color: C.sub }]}>Live</Text>
                </View>
              )}
            </View>
            <View style={[styles.badge, { backgroundColor: getSideColor(item.side) }]}>
              <Text style={styles.badgeText}>{item.side}</Text>
            </View>
          </View>
          <View style={styles.pickScoreWrap}>
            <Text
              style={[styles.scoreValue, { color: getScoreColor(item.score) }]}
            >
              {(item.score ?? 0).toFixed(2)}
            </Text>
            <Text style={[styles.scoreLabel, { color: C.sub }]}>Score</Text>
          </View>
        </View>

        {/* Live Chart */}
        <View style={styles.chartContainer}>
          {chartData && chartData.length > 0 ? (
            <>
              <SparkMini
                data={chartData}
                width={chartData.length * 2}
                height={60}
                upColor={C.long}
                downColor={C.short}
                neutralColor={C.sub}
              />
              <View style={styles.chartFooter}>
                <Text
                  style={[styles.chartPrice, { color: getChangeColor(changePercent) }]}
                >
                  {quote ? `$${quote.currentPrice?.toFixed(2)}` : 'N/A'}
                </Text>
                <Text style={styles.chartTime}>1D Intraday</Text>
              </View>
            </>
          ) : (
            <View style={[styles.chartPlaceholder, { backgroundColor: C.border }]}>
              <Text
                style={[styles.chartPlaceholderText, { color: C.sub }]}
              >
                Chart Loading...
              </Text>
            </View>
          )}
        </View>

        {/* Features */}
        <View style={styles.block}>
          <View style={styles.blockHeader}>
            <Icon name="bar-chart-2" size={16} color={C.sub} />
            <Text style={[styles.blockTitle, { color: C.text }]}>Key Features</Text>
          </View>
          <View style={styles.grid}>
            <KV label="Momentum" value={(item.features?.momentum15m ?? 0).toFixed(3)} />
            <KV label="RVOL" value={`${(item.features?.rvol10m ?? 0).toFixed(2)}x`} />
            <KV label="VWAP" value={(item.features?.vwapDist ?? 0).toFixed(3)} />
            <KV label="Breakout" value={(item.features?.breakoutPct ?? 0).toFixed(3)} />
          </View>
        </View>

        {/* Risk */}
        <View style={styles.block}>
          <View style={styles.blockHeader}>
            <Icon name="shield" size={16} color={C.sub} />
            <Text style={[styles.blockTitle, { color: C.text }]}>Risk Management</Text>
          </View>
          <View style={styles.grid}>
            <KV label="Size" value={`${item.risk?.sizeShares ?? 0} shares`} />
            <KV label="Entry" value={`$${(entry ?? 0).toFixed(2)}`} />
            <KV 
              label="Stop" 
              value={`$${(item.risk?.stop ?? 0).toFixed(2)}`}
              tooltip={{
                term: "Stop Loss",
                explanation: "The price where your trade automatically exits to limit loss. This stop is calculated based on 1.5x ATR (Average True Range) for SAFE mode or 2x ATR for AGGRESSIVE mode. ATR measures volatility - higher ATR means the stock moves more, so wider stops are needed to avoid getting stopped out by normal price fluctuations."
              }}
            />
            <KV 
              label="Target" 
              value={`$${Number(target ?? 0).toFixed(2)}`}
              tooltip={{
                term: "Take Profit Target",
                explanation: "The price where you should take profit. The risk:reward ratio compares potential profit to potential loss. Aim for at least 2:1 (risk $1 to make $2). This target is calculated based on the stop distance to maintain a good risk:reward ratio."
              }}
            />
            <KV 
              label="Time Stop" 
              value={`${item.risk?.timeStopMin ?? 0} min`}
              tooltip={{
                term: "Time Stop",
                explanation: "Exit the trade after this many minutes regardless of price. This prevents holding losing positions too long. For SAFE mode: 45 minutes, for AGGRESSIVE mode: 25 minutes. Time stops help enforce discipline and prevent emotional trading."
              }}
            />
            <KV 
              label="ATR(5m)" 
              value={`${(item.risk?.atr5m ?? 0).toFixed(2)}`}
              tooltip={{
                term: "ATR (Average True Range)",
                explanation: "ATR measures volatility over a 5-minute period. Higher ATR means the stock moves more (more volatile). Use ATR to set stop loss distance: 1.5-2x ATR for day trading, 2-3x ATR for swing trading. This ensures stops are wide enough to avoid normal price noise but tight enough to limit losses."
              }}
            />
          </View>
        </View>

        {/* Risk/Reward Diagram */}
        {item.risk?.stop && target && (() => {
          const entryPrice = entry || item.risk.stop + (item.risk.atr5m || 1);
          const stopPrice = item.risk.stop;
          const targetPrice = target;
          const riskAmount = Math.abs(entryPrice - stopPrice);
          const rewardAmount = Math.abs(targetPrice - entryPrice);
          const riskRewardRatio = riskAmount > 0 ? (rewardAmount / riskAmount).toFixed(2) : '0.00';
          
          return (
            <View style={[styles.riskRewardCard, { backgroundColor: C.card }]}>
              <View style={styles.riskRewardHeader}>
                <Text style={[styles.riskRewardTitle, { color: C.text }]}>Risk/Reward Analysis</Text>
                <View style={styles.ratioBadge}>
                  <Icon name="trending-up" size={14} color="#22C55E" />
                  <Text style={styles.ratioText}>R:R {riskRewardRatio}:1</Text>
                </View>
              </View>
              <RiskRewardDiagram
                entryPrice={entryPrice}
                stopPrice={stopPrice}
                targetPrice={targetPrice}
                riskAmount={riskAmount}
                rewardAmount={rewardAmount}
              />
            </View>
          );
        })()}

        {/* Why This Trade Button */}
        <TouchableOpacity
          style={[styles.whyTradeButton, { borderColor: getSideColor(item.side) }]}
          onPress={() => setShowWhyThisTrade(item)}
        >
          <Text style={[styles.whyTradeText, { color: getSideColor(item.side) }]}>
            Why This Trade?
          </Text>
        </TouchableOpacity>

        {item.notes ? (
          <Text style={[styles.notes, { color: C.sub }]}>{item.notes}</Text>
        ) : null}

        {/* Execution Suggestion - BEAUTIFUL LIGHT MODE VERSION */}
        {shouldShowLoading ? (
          <View style={styles.suggestionLoading}>
            <ActivityIndicator size="small" color="#3182CE" />
            <Text style={styles.suggestionLoadingText}>
              Analyzing market depth & liquidity...
            </Text>
          </View>
        ) : hasTimedOut || (error && !effectiveSuggestion) ? (
          <View style={styles.suggestionUnavailable}>
            <Icon name="alert-triangle" size={20} color="#DC2626" />
            <View style={{ flex: 1, marginLeft: 10 }}>
              <Text style={styles.suggestionUnavailableTitle}>
                Smart Order Unavailable
              </Text>
              <Text style={styles.suggestionUnavailableText}>
                Real-time execution engine timed out. Use manual entry.
              </Text>
            </View>
          </View>
        ) : effectiveSuggestion ? (
          <View style={styles.suggestionContainer}>
            {/* Header */}
            <View style={styles.suggestionHeader}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                <View style={styles.suggestionIcon}>
                  <Icon name="zap" size={18} color="#FFF" />
                </View>
                <Text style={styles.suggestionTitle}>Smart Order Suggestion</Text>
                {isRefreshing && <ActivityIndicator size={14} color="#3182CE" />}
              </View>
              {(() => {
                const confidence = effectiveSuggestion.confidence;
                const confidenceNum = confidence != null ? Number(confidence) : null;
                const isValidConfidence = confidenceNum != null && !isNaN(confidenceNum) && confidenceNum >= 0 && confidenceNum <= 1;
                
                if (isValidConfidence) {
                  return (
                    <View style={[
                      styles.confidenceBadge,
                      { backgroundColor: confidenceNum >= 0.8 ? '#DCFCE7' : '#FEF3C7' }
                    ]}>
                      <Text style={[
                        styles.confidenceText,
                        { color: confidenceNum >= 0.8 ? '#166534' : '#92400E' }
                      ]}>
                        {(confidenceNum * 100).toFixed(0)}% Confidence
                      </Text>
                    </View>
                  );
                }
                return null;
              })()}
            </View>

            {/* Order Type + Price Band */}
            <View style={styles.suggestionBody}>
              <View style={styles.suggestionRow}>
                <Text style={styles.suggestionLabel}>Recommended Order</Text>
                <View style={[
                  styles.orderTypePill,
                  { backgroundColor: getSideColor(item.side) + '20' }
                ]}>
                  <Text style={[styles.orderTypeText, { color: getSideColor(item.side) }]}>
                    {effectiveSuggestion.orderType || 'Limit'}
                  </Text>
                </View>
              </View>

              {(() => {
                const priceLow = effectiveSuggestion.priceBand?.low;
                const priceHigh = effectiveSuggestion.priceBand?.high;
                const lowNum = priceLow != null ? Number(priceLow) : null;
                const highNum = priceHigh != null ? Number(priceHigh) : null;
                const hasValidPrices = lowNum != null && !isNaN(lowNum) && highNum != null && !isNaN(highNum);
                
                // Fallback to entry price if price band is invalid
                const fallbackPrice = entry || quote?.currentPrice || (quote?.bid && quote?.ask ? (quote.bid + quote.ask) / 2 : null);
                
                if (hasValidPrices || fallbackPrice) {
                  const displayLow = hasValidPrices ? lowNum : (fallbackPrice ? fallbackPrice * 0.9995 : null);
                  const displayHigh = hasValidPrices ? highNum : (fallbackPrice ? fallbackPrice * 1.0005 : null);
                  const midpoint = displayLow != null && displayHigh != null ? (displayLow + displayHigh) / 2 : null;
                  
                  if (displayLow != null && displayHigh != null && midpoint != null) {
                    return (
                      <View style={styles.priceBand}>
                        <Text style={styles.priceBandLabel}>Optimal Fill Range</Text>
                        <View style={styles.priceRange}>
                          <Text style={styles.priceLow}>${displayLow.toFixed(2)}</Text>
                          <View style={styles.priceArrow}>
                            <Icon name="arrow-right" size={14} color="#3182CE" />
                          </View>
                          <Text style={styles.priceHigh}>${displayHigh.toFixed(2)}</Text>
                        </View>
                        <Text style={styles.priceMidpoint}>
                          Mid: ${midpoint.toFixed(2)}
                        </Text>
                      </View>
                    );
                  }
                }
                return null;
              })()}

              {/* Rationale */}
              {effectiveSuggestion.rationale && (
                <View style={styles.rationaleBox}>
                  <Text style={styles.rationaleTitle}>Why this order?</Text>
                  <Text style={styles.rationaleText}>
                    {effectiveSuggestion.rationale}
                  </Text>
                </View>
              )}
            </View>

            {/* Footer */}
            <View style={styles.suggestionFooter}>
              <Text style={styles.suggestionFooterText}>
                Suggested by RichesReach Execution Engine • {new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
              </Text>
            </View>
          </View>
        ) : null}

        <TouchableOpacity
          style={[styles.executeBtn, { backgroundColor: getSideColor(item.side) }]}
          onPress={() => handleTradeExecution(item)}
          accessibilityRole="button"
          accessibilityLabel={`Execute ${item.side} ${item.symbol}`}
        >
          <Icon name="zap" size={18} color="#fff" style={{ marginRight: 8 }} />
          <Text style={styles.executeBtnText}>Execute {item.side} Trade</Text>
        </TouchableOpacity>
      </View>
    </TouchableOpacity>
  );
});

MemoizedPick.displayName = 'MemoizedPick';

/* ============ Styles ============ */
const styles = StyleSheet.create({
  container: { flex: 1 },
  header: { 
    paddingHorizontal: 20, 
    paddingVertical: 16, 
    borderBottomWidth: 1,
    shadowColor: '#000', 
    shadowOpacity: 0.1,
  },
  paperTradingBanner: {
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderBottomWidth: 1,
    marginTop: 0,
  },
  paperTradingContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  paperTradingLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  paperTradingText: {
    fontSize: 13,
    fontWeight: '500',
    marginLeft: 8,
  },
  paperTradingButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    gap: 6,
  },
  paperTradingButtonText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '600',
  },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  headerLeft: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  backBtn: { 
    marginRight: 12, 
    padding: 8, 
    borderRadius: 12, 
    backgroundColor: '#EBF4FF',
  },
  backText: { fontSize: 16, fontWeight: '700' },
  headerText: { flex: 1, marginLeft: 8 },
  title: { fontSize: 24, fontWeight: '800' },
  subtitle: { fontSize: 15, marginTop: 4 },
  headerRight: { flexDirection: 'row', gap: 8 },
  pillBtn: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    paddingHorizontal: 16, 
    paddingVertical: 10, 
    borderRadius: 20,
    shadowColor: '#000', 
    shadowOpacity: 0.1, 
    shadowRadius: 8, 
    shadowOffset: { width: 0, height: 2 }, 
    elevation: 2,
  },
  pillBtnText: { color: '#fff', fontSize: 14, fontWeight: '700' },

  modeWrap: {
    marginHorizontal: 20,
    marginTop: 16,
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOpacity: 0.08,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 4 },
    elevation: 3,
  },
  modeHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  modeHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  modeTitle: { fontSize: 18, fontWeight: '800' },
  executionQualityButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  executionQualityButtonText: {
    fontSize: 12,
    fontWeight: '700',
  },
  executionQualitySection: {
    marginHorizontal: 20,
    marginTop: 12,
    borderRadius: 12,
    padding: 16,
    maxHeight: 600,
  },
  executionQualityHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  executionQualityTitle: {
    fontSize: 16,
    fontWeight: '700',
  },
  rahaSection: {
    marginHorizontal: 20,
    marginTop: 12,
    borderRadius: 12,
    padding: 16,
    maxHeight: 400,
  },
  rahaHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  rahaHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  rahaTitle: {
    fontSize: 16,
    fontWeight: '700',
  },
  rahaContent: {
    marginTop: 8,
  },
  rahaEmpty: {
    alignItems: 'center',
    padding: 24,
  },
  rahaEmptyText: {
    fontSize: 14,
    fontWeight: '600',
    marginTop: 12,
    textAlign: 'center',
  },
  rahaEmptySubtext: {
    fontSize: 12,
    marginTop: 4,
    textAlign: 'center',
  },
  rahaPnlSection: {
    marginHorizontal: 20,
    marginTop: 12,
    borderRadius: 12,
    padding: 16,
  },
  infoDot: {
    width: 24, height: 24, borderRadius: 12, alignItems: 'center', justifyContent: 'center', backgroundColor: '#F7FAFC',
    borderWidth: 1, borderColor: '#E2E8F0',
  },
  modeGroup: { flexDirection: 'row', backgroundColor: '#F7FAFC', borderRadius: 12, padding: 4 },
  modeBtn: { flex: 1, paddingVertical: 12, borderRadius: 8, alignItems: 'center' },
  modeBtnText: { fontSize: 16, fontWeight: '800' },
  modeBtnTextActive: { color: '#fff' },

  infoStrip: { marginHorizontal: 20, marginTop: 12, padding: 14, borderRadius: 12 },
  infoText: { fontSize: 14, textAlign: 'center', fontWeight: '700' },

  marketBox: { 
    marginHorizontal: 20, 
    marginTop: 12, 
    padding: 16, 
    borderRadius: 12,
    shadowColor: '#000', 
    shadowOpacity: 0.05, 
    shadowRadius: 8, 
    shadowOffset: { width: 0, height: 2 }, 
    elevation: 1,
  },
  marketRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  marketText: { fontSize: 13, textAlign: 'center', flex: 1 },

  card: {
    borderWidth: 1,
    marginHorizontal: 20,
    borderRadius: 18,
    padding: 20,
    marginTop: 16,
    shadowColor: '#000',
    shadowOpacity: 0.06,
    shadowRadius: 16,
    shadowOffset: { width: 0, height: 4 },
    elevation: 4,
  },
  pickHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 },
  pickSymbolWrap: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  symbolIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#EBF4FF',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  pickSymbol: { fontSize: 22, fontWeight: '800' },
  changeWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  changeValue: { fontSize: 14, fontWeight: '700' },
  changeLabel: { fontSize: 12, marginLeft: 4 },
  badge: { paddingHorizontal: 10, paddingVertical: 6, borderRadius: 12 },
  badgeText: { color: '#fff', fontSize: 12, fontWeight: '800' },
  pickScoreWrap: { alignItems: 'center' },
  scoreValue: { fontSize: 20, fontWeight: '800' },
  scoreLabel: { fontSize: 12 },

  chartContainer: {
    marginBottom: 20,
    padding: 16,
    backgroundColor: '#F7FAFC',
    borderRadius: 12,
  },
  chartPlaceholder: {
    height: 60,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  chartPlaceholderText: {
    fontSize: 12,
    fontWeight: '500',
  },
  chartFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 8,
  },
  chartPrice: { fontSize: 16, fontWeight: '800' },
  chartTime: { fontSize: 12, color: '#718096' },

  block: { marginBottom: 24 },
  blockHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  blockTitle: { fontSize: 15, fontWeight: '700', color: '#475569' },
  grid: { 
    flexDirection: 'row', 
    flexWrap: 'wrap', 
    justifyContent: 'flex-start',
    gap: 8,
    paddingVertical: 4,
    paddingHorizontal: 0,
  },
  kvWrapper: {
    flex: 1,
    minWidth: '48%',
    maxWidth: '48%',
  },
  kvContainer: {
    width: '100%',
    paddingVertical: 12,
    paddingHorizontal: 10,
    backgroundColor: '#F8F9FA',
    borderRadius: 10,
    marginBottom: 0,
    alignItems: 'flex-start',
    minHeight: 70,
    justifyContent: 'center',
  },
  kvLabelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
    gap: 3,
    width: '100%',
  },
  kvLabel: { 
    fontSize: 10, 
    color: '#8B8B99',
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    flexShrink: 0,
  },
  kvTooltipIcon: {
    marginLeft: 0,
    flexShrink: 0,
    marginTop: 0,
  },
  kvValue: { 
    fontSize: 16, 
    fontWeight: '600',
    lineHeight: 20,
    color: '#111827',
  },

  notes: { fontSize: 14, fontStyle: 'italic', marginBottom: 20, padding: 12, backgroundColor: '#F7FAFC', borderRadius: 12 },

  executeBtn: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    justifyContent: 'center', 
    paddingVertical: 14, 
    borderRadius: 16,
    shadowColor: '#000', 
    shadowOpacity: 0.2, 
    shadowRadius: 8, 
    shadowOffset: { width: 0, height: 4 }, 
    elevation: 3,
  },
  executeBtnText: { color: '#fff', fontSize: 16, fontWeight: '800' },
  riskRewardCard: {
    borderRadius: 18,
    paddingHorizontal: 16,
    paddingVertical: 16,
    marginTop: 20,
    marginBottom: 8,
    shadowColor: '#000',
    shadowOpacity: 0.06,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 4 },
    elevation: 2,
  },
  riskRewardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  riskRewardTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
  },
  ratioBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 12,
    gap: 5,
  },
  ratioText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#16A34A',
  },
  whyTradeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 18,
    borderRadius: 10,
    borderWidth: 1.5,
    marginTop: 24,     // ⬅️ was 16 – gives the diagram breathing room
    marginBottom: 12,
    gap: 8,
    backgroundColor: 'transparent',
  },
  whyTradeText: {
    fontSize: 14,
    fontWeight: '700',
  },

  emptyWrap: { padding: 60, alignItems: 'center', justifyContent: 'center' },
  emptyTitle: { fontSize: 18, fontWeight: '800', textAlign: 'center', marginBottom: 8 },
  emptySub: { fontSize: 14, textAlign: 'center' },
  retryButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  retryButtonText: {
    fontSize: 16,
    fontWeight: '700',
  },
  errorBanner: {
    marginHorizontal: 20,
    marginTop: 12,
    padding: 12,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    borderLeftWidth: 4,
    gap: 8,
  },
  errorBannerText: {
    fontSize: 12,
    flex: 1,
    fontWeight: '600',
  },
  retryButtonSmall: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    borderWidth: 1,
  },

  disclaimer: {
    marginHorizontal: 20,
    marginBottom: 20,
    padding: 12,
    borderLeftWidth: 3,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  disclaimerText: { fontSize: 12, lineHeight: 18, flex: 1 },

  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: { fontSize: 16, textAlign: 'center', marginTop: 16 },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  errorText: { fontSize: 16, textAlign: 'center', marginTop: 16, marginBottom: 24 },
  retryBtn: { 
    paddingVertical: 12, 
    paddingHorizontal: 24, 
    borderRadius: 12,
    shadowColor: '#000', 
    shadowOpacity: 0.1, 
    shadowRadius: 8, 
    shadowOffset: { width: 0, height: 2 }, 
    elevation: 2,
  },
  retryBtnText: { color: '#fff', fontSize: 16, fontWeight: '800' },

  // AR Gesture Styles
  gestureHints: {
    position: 'absolute',
    top: 20,
    left: 20,
    right: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
    zIndex: 1000,
  },
  gestureHint: {
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  gestureText: {
    fontSize: 10,
    color: '#fff',
    marginTop: 2,
    fontWeight: '600',
  },
  gestureFeedback: {
    position: 'absolute',
    bottom: 100,
    left: 20,
    right: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    zIndex: 1000,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  gestureFeedbackText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#000',
  },
  selectedPickIndicator: {
    position: 'absolute',
    top: 60,
    left: 20,
    right: 20,
    backgroundColor: 'rgba(76, 175, 80, 0.9)',
    padding: 10,
    borderRadius: 8,
    alignItems: 'center',
    zIndex: 1000,
  },
  selectedPickText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
  },

  // Smart Order Suggestion Styles
  suggestionContainer: {
    marginTop: 20,
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 18,
    borderWidth: 1.5,
    borderColor: '#E0E7FF',
    shadowColor: '#000',
    shadowOpacity: 0.08,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 4 },
    elevation: 5,
  },
  suggestionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 14,
  },
  suggestionIcon: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#3182CE',
    alignItems: 'center',
    justifyContent: 'center',
  },
  suggestionTitle: {
    fontSize: 17,
    fontWeight: '800',
    color: '#1E293B',
  },
  confidenceBadge: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 20,
  },
  confidenceText: {
    fontSize: 12,
    fontWeight: '700',
  },
  suggestionBody: {
    gap: 12,
  },
  suggestionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  suggestionLabel: {
    fontSize: 14,
    color: '#475569',
    fontWeight: '600',
  },
  orderTypePill: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  orderTypeText: {
    fontSize: 13,
    fontWeight: '700',
  },
  priceBand: {
    backgroundColor: '#F8FAFC',
    padding: 14,
    borderRadius: 14,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  priceBandLabel: {
    fontSize: 13,
    color: '#64748B',
    marginBottom: 8,
    fontWeight: '600',
  },
  priceRange: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  priceLow: {
    fontSize: 18,
    fontWeight: '700',
    color: '#DC2626',
  },
  priceArrow: {
    backgroundColor: '#E0E7FF',
    padding: 6,
    borderRadius: 12,
  },
  priceHigh: {
    fontSize: 18,
    fontWeight: '700',
    color: '#16A34A',
  },
  priceMidpoint: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 6,
  },
  rationaleBox: {
    backgroundColor: '#F0F9FF',
    padding: 12,
    borderRadius: 12,
    borderLeftWidth: 3,
    borderLeftColor: '#0EA5E9',
  },
  rationaleTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#0369A1',
    marginBottom: 4,
  },
  rationaleText: {
    fontSize: 13.5,
    color: '#1E40AF',
    lineHeight: 19,
  },
  suggestionFooter: {
    marginTop: 14,
    alignItems: 'center',
  },
  suggestionFooterText: {
    fontSize: 11,
    color: '#94A3B8',
    fontStyle: 'italic',
  },
  suggestionLoading: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    backgroundColor: '#F0F9FF',
    borderRadius: 14,
    marginTop: 20,
    borderWidth: 1,
    borderColor: '#BAE6FD',
    gap: 10,
  },
  suggestionLoadingText: {
    fontSize: 14,
    color: '#0369A1',
    fontWeight: '600',
  },
  suggestionUnavailable: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#FEF2F2',
    borderRadius: 14,
    marginTop: 20,
    borderWidth: 1,
    borderColor: '#FCA5A5',
    gap: 10,
  },
  suggestionUnavailableTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#991B1B',
  },
  suggestionUnavailableText: {
    fontSize: 13,
    color: '#991B1B',
    textAlign: 'left',
  },
});