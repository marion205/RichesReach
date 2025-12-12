import React, { useState, useCallback, useMemo, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  Animated,
  Easing,
  Dimensions,
  ActivityIndicator,
  PanResponder,
  ScrollView,
  Alert,
  Modal,
  TextInput,
} from 'react-native';
// Removed useNavigation - using navigateTo prop instead
import Icon from 'react-native-vector-icons/Feather';
import { useRAHASignals } from '../hooks/useRAHASignals';
import { useUserStrategySettings } from '../hooks/useStrategies';
import StockChart from '../../stocks/components/StockChart';
import logger from '../../../utils/logger';
import { useMutation, gql } from '@apollo/client';

const { width, height } = Dimensions.get('window');

// GraphQL Mutation for placing market orders
const PLACE_MARKET_ORDER = gql`
  mutation PlaceMarketOrder($symbol: String!, $quantity: Int!, $side: String!, $notes: String) {
    placeMarketOrder(symbol: $symbol, quantity: $quantity, side: $side, notes: $notes) {
      success
      order {
        id
        symbol
        side
        orderType
        quantity
        status
        createdAt
        notes
      }
    }
  }
`;

interface TheWhisperScreenProps {
  symbol: string;
  currentPrice: number;
  change: number;
  changePercent: number;
  onTakeTrade?: () => void;
  onJustWatching?: () => void;
}

/**
 * The Whisper - The one magical P&L moment
 * 
 * This is the ONLY screen that shows the Ghost Candle.
 * Everything else (strategies, backtests, etc.) lives elsewhere.
 * 
 * Philosophy: One screen. One decision. All the power under the hood.
 */
export default function TheWhisperScreen({
  symbol: initialSymbol,
  currentPrice: initialCurrentPrice,
  change: initialChange,
  changePercent: initialChangePercent,
  onTakeTrade,
  onJustWatching,
}: TheWhisperScreenProps) {
  // Allow symbol to be changed by user
  const [symbol, setSymbol] = useState(initialSymbol || 'AAPL');
  const [currentPrice, setCurrentPrice] = useState(initialCurrentPrice || 175.50);
  const [change, setChange] = useState(initialChange || 2.30);
  const [changePercent, setChangePercent] = useState(initialChangePercent || 1.33);
  // Custom navigation helper (not using React Navigation)
  const handleBack = () => {
    if (onJustWatching) {
      onJustWatching();
    } else if (typeof window !== 'undefined') {
      if ((window as any).__navigateToGlobal) {
        (window as any).__navigateToGlobal('home');
      } else if ((window as any).__setCurrentScreen) {
        (window as any).__setCurrentScreen('home');
      }
    }
  };
  
  const handleNavigateToStrategyStore = () => {
    if (typeof window !== 'undefined') {
      if ((window as any).__navigateToGlobal) {
        (window as any).__navigateToGlobal('pro-labs', { view: 'strategies' });
      } else if ((window as any).__setCurrentScreen) {
        (window as any).__setCurrentScreen('pro-labs');
      }
    }
  };
  const [showDetails, setShowDetails] = useState(false);
  const [showProDrawer, setShowProDrawer] = useState(false);
  const [showProViewButton, setShowProViewButton] = useState(false);
  const [isExecutingTrade, setIsExecutingTrade] = useState(false);
  const [showPNLRibbon, setShowPNLRibbon] = useState(false); // P&L ribbon visibility
  const [showChartModal, setShowChartModal] = useState(false); // Full-screen chart modal
  const [showSymbolPicker, setShowSymbolPicker] = useState(false); // Symbol picker modal
  const [symbolSearch, setSymbolSearch] = useState(''); // Symbol search input
  const longPressTimer = useRef<NodeJS.Timeout | null>(null);
  const chartPressStartTime = useRef<number | null>(null);
  
  // Update state when props change (if navigated with new symbol)
  React.useEffect(() => {
    if (initialSymbol && initialSymbol !== symbol) {
      setSymbol(initialSymbol);
      setCurrentPrice(initialCurrentPrice || 0);
      setChange(initialChange || 0);
      setChangePercent(initialChangePercent || 0);
    }
  }, [initialSymbol, initialCurrentPrice, initialChange, initialChangePercent]);
  
  const { settings: userStrategySettings } = useUserStrategySettings();
  const enabledStrategies = userStrategySettings.filter(s => s.enabled);
  const hasEnabledStrategies = enabledStrategies.length > 0;
  
  // Get RAHA signals for this symbol
  const { signals, loading: signalsLoading, error: signalsError, refetch: refetchSignals } = useRAHASignals(
    symbol,
    '5m',
    1 // Just get the top signal
  );
  
  // Trade execution mutation
  const [placeMarketOrder] = useMutation(PLACE_MARKET_ORDER);

  // Long-press handler for Pro View button
  const chartPanResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => false,
      onMoveShouldSetPanResponder: () => false,
      onPanResponderGrant: () => {
        chartPressStartTime.current = Date.now();
        longPressTimer.current = setTimeout(() => {
          setShowProViewButton(true);
        }, 500); // 500ms long press
      },
      onPanResponderRelease: () => {
        if (longPressTimer.current) {
          clearTimeout(longPressTimer.current);
          longPressTimer.current = null;
        }
        // Hide Pro View button after 3 seconds if not tapped
        if (showProViewButton) {
          setTimeout(() => {
            setShowProViewButton(false);
          }, 3000);
        }
        chartPressStartTime.current = null;
      },
    })
  ).current;

  // Ghost candle animation (polished)
  const ghostCandleOpacity = useMemo(() => new Animated.Value(0), []);
  const ghostCandleScale = useMemo(() => new Animated.Value(0.95), []);
  const ghostCandleTranslateY = useMemo(() => new Animated.Value(10), []);
  const expectancyOpacity = useMemo(() => new Animated.Value(0), []);
  const moodOpacity = useMemo(() => new Animated.Value(0), []);
  const buttonScale = useMemo(() => new Animated.Value(0.95), []);

  React.useEffect(() => {
    // Animate ghost candle in when signals are ready (fine-tuned sequence)
    if (signals.length > 0 && !signalsLoading && topSignal) {
      // Ghost candle appears first with smoother easing
      Animated.parallel([
        Animated.timing(ghostCandleOpacity, {
          toValue: 1,
          duration: 700,
          easing: Easing.out(Easing.quad), // Smooth ease-out
          useNativeDriver: true,
        }),
        Animated.spring(ghostCandleScale, {
          toValue: 1,
          tension: 60, // Slightly higher tension for snappier feel
          friction: 8, // Slightly more friction for smoother settle
          useNativeDriver: true,
        }),
        Animated.timing(ghostCandleTranslateY, {
          toValue: 0,
          duration: 700,
          easing: Easing.out(Easing.quad), // Smooth ease-out
          useNativeDriver: true,
        }),
      ]).start(() => {
        // Then expectancy sentence fades in with slight delay
        Animated.sequence([
          Animated.delay(100), // Small pause for better flow
          Animated.timing(expectancyOpacity, {
            toValue: 1,
            duration: 500,
            easing: Easing.out(Easing.quad),
            useNativeDriver: true,
          }),
        ]).start(() => {
          // Then mood pill with subtle scale
          Animated.parallel([
            Animated.timing(moodOpacity, {
              toValue: 1,
              duration: 400,
              easing: Easing.out(Easing.quad),
              useNativeDriver: true,
            }),
          ]).start(() => {
            // Finally, button pulses in if eligible with subtle pulse
            if (shouldShowTradeButton) {
              Animated.sequence([
                Animated.spring(buttonScale, {
                  toValue: 1,
                  tension: 50,
                  friction: 7,
                  useNativeDriver: true,
                }),
                // Subtle pulse animation
                Animated.loop(
                  Animated.sequence([
                    Animated.timing(buttonScale, {
                      toValue: 1.02,
                      duration: 2000,
                      easing: Easing.inOut(Easing.ease),
                      useNativeDriver: true,
                    }),
                    Animated.timing(buttonScale, {
                      toValue: 1,
                      duration: 2000,
                      easing: Easing.inOut(Easing.ease),
                      useNativeDriver: true,
                    }),
                  ])
                ),
              ]).start();
            }
          });
        });
      });
    } else if (signalsLoading) {
      // Reset animations during loading
      ghostCandleOpacity.setValue(0);
      ghostCandleScale.setValue(0.95);
      ghostCandleTranslateY.setValue(10);
      expectancyOpacity.setValue(0);
      moodOpacity.setValue(0);
      buttonScale.setValue(0.95);
    }
  }, [signals, signalsLoading, shouldShowTradeButton]);

  // Calculate P&L projection from top signal (memoized for performance)
  const topSignal = useMemo(() => signals[0], [signals]);
  const projectedPNL = useMemo(() => {
    if (!topSignal || !topSignal.price || !topSignal.takeProfit || !topSignal.stopLoss) {
      return null;
    }
    
    const entry = parseFloat(topSignal.price.toString());
    const tp = parseFloat(topSignal.takeProfit.toString());
    const sl = parseFloat(topSignal.stopLoss.toString());
    const isLong = topSignal.signalType === 'ENTRY_LONG';
    
    // Calculate risk/reward ratio
    const risk = Math.abs(entry - sl);
    const reward = Math.abs(tp - entry);
    
    // Default risk amount ($100) - could be user-configurable
    const riskAmount = 100;
    const rewardAmount = risk > 0 ? (reward / risk) * riskAmount : 0;
    
    // Get confidence score (0-1)
    const confidenceScore = topSignal.confidenceScore || 0.64;
    
    return {
      likelyGain: rewardAmount,
      maxLoss: riskAmount,
      winChance: confidenceScore,
      riskAmount,
      riskRewardRatio: risk > 0 ? reward / risk : 0,
    };
  }, [topSignal, symbol]);

  // Market regime (from oracle)
  const regimeLabel = useMemo(() => {
    if (!topSignal?.globalRegime) return 'Calibrating regime…';
    
    // Turn `EQUITY_RISK_ON` → `Equity Risk On`
    const prettyGlobal = topSignal.globalRegime
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (l) => l.toUpperCase());
    
    const prettyLocal = topSignal.localContext
      ? topSignal.localContext
          .replace(/_/g, ' ')
          .replace(/\b\w/g, (l) => l.toUpperCase())
      : null;
    
    return prettyLocal ? `${prettyGlobal} · ${prettyLocal}` : prettyGlobal;
  }, [topSignal]);

  const regimeMultiplier = topSignal?.regimeMultiplier ?? 1.0;
  
  const regimeColor = useMemo(() => {
    if (regimeMultiplier > 1.05) return '#10B981'; // Green for risk-on
    if (regimeMultiplier < 0.95) return '#EF4444'; // Red for risk-off
    return '#6B7280'; // Gray for neutral
  }, [regimeMultiplier]);

  // Market mood (from regime detection - now using actual regime)
  const marketMood = useMemo(() => {
    if (!topSignal?.globalRegime) {
      // Fallback to confidence if no regime data
      const confidence = topSignal?.confidenceScore || 0.5;
      if (confidence > 0.7) return { label: 'Trending', color: '#3B82F6' };
      if (confidence > 0.5) return { label: 'Calm', color: '#10B981' };
      if (confidence > 0.3) return { label: 'Choppy', color: '#F59E0B' };
      return { label: 'Dangerous', color: '#EF4444' };
    }
    
    // Use actual regime
    const regime = topSignal.globalRegime;
    if (regime === 'EQUITY_RISK_ON') return { label: 'Risk-On', color: '#10B981' };
    if (regime === 'EQUITY_RISK_OFF') return { label: 'Risk-Off', color: '#EF4444' };
    if (regime === 'CRYPTO_ALT_SEASON') return { label: 'Alt Season', color: '#8B5CF6' };
    if (regime === 'CRYPTO_BTC_DOMINANCE') return { label: 'BTC Dominance', color: '#F59E0B' };
    return { label: 'Neutral', color: '#6B7280' };
  }, [topSignal]);

  // Expectancy sentence (the magic line)
  const expectancySentence = useMemo(() => {
    if (!projectedPNL) return null;
    
    const { likelyGain, maxLoss, winChance } = projectedPNL;
    const expectedValue = (likelyGain * winChance) - (maxLoss * (1 - winChance));
    
    if (expectedValue > 0) {
      const finalAmount = 100 + expectedValue;
      return `Most people like you turned $100 into $${Math.round(finalAmount)} here\n(risking only $${Math.round(maxLoss)})`;
    }
    return null;
  }, [projectedPNL]);

  // Should show trade button? (only if expectancy is positive and high enough)
  // Memoized to prevent unnecessary recalculations
  const shouldShowTradeButton = useMemo(() => {
    if (!projectedPNL || !topSignal) return false;
    const { likelyGain, maxLoss, winChance } = projectedPNL;
    const expectedValue = (likelyGain * winChance) - (maxLoss * (1 - winChance));
    const rMultiple = maxLoss > 0 ? expectedValue / maxLoss : 0;
    // Only show if expectancy > 0.4R and we have valid signal data
    return rMultiple > 0.4 && topSignal.price && topSignal.takeProfit && topSignal.stopLoss;
  }, [projectedPNL, topSignal]);

  const handleTakeTrade = useCallback(async () => {
    // If callback provided, use it
    if (onTakeTrade) {
      onTakeTrade();
      return;
    }
    
    if (!topSignal || !projectedPNL) {
      Alert.alert('Error', 'No signal available to trade');
      return;
    }
    
    // Show confirmation
    Alert.alert(
      'Place Trade',
      `Place ${topSignal.signal_type === 'ENTRY_LONG' ? 'LONG' : 'SHORT'} trade on ${symbol}?\n\nEntry: $${topSignal.price}\nStop Loss: $${topSignal.stopLoss || 'N/A'}\nTake Profit: $${topSignal.takeProfit || 'N/A'}\n\nRisk: $${Math.round(projectedPNL.riskAmount || 0)}`,
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Execute Trade',
          onPress: async () => {
            setIsExecutingTrade(true);
            try {
              // Calculate position size based on risk amount
              // For simplicity, use a fixed quantity (in production, calculate based on account size and risk)
              const riskAmount = projectedPNL.riskAmount || 100; // Default $100 risk
              const entryPrice = parseFloat(topSignal.price.toString());
              const stopLoss = topSignal.stopLoss ? parseFloat(topSignal.stopLoss.toString()) : entryPrice * 0.98;
              const riskPerShare = Math.abs(entryPrice - stopLoss);
              const quantity = riskPerShare > 0 ? Math.max(1, Math.floor(riskAmount / riskPerShare)) : 1;
              
              const side = topSignal.signal_type === 'ENTRY_LONG' ? 'buy' : 'sell';
              
              logger.log('🔍 [TheWhisper] Executing trade:', { symbol, side, quantity, entryPrice, stopLoss });
              
              const result = await placeMarketOrder({
                variables: {
                  symbol: symbol.toUpperCase(),
                  quantity: quantity,
                  side: side,
                  notes: `RAHA ${topSignal.strategyVersion?.strategy?.name || 'Strategy'} - Entry: $${entryPrice}, SL: $${stopLoss}, TP: $${topSignal.takeProfit || 'N/A'}`
                }
              });
              
              if (result.data?.placeMarketOrder?.success) {
                const order = result.data.placeMarketOrder.order;
                Alert.alert(
                  'Trade Executed! ✅',
                  `Order ID: ${order.id}\n${side.toUpperCase()} ${quantity} ${symbol} @ $${entryPrice.toFixed(2)}\n\nStop Loss: $${stopLoss.toFixed(2)}\nTake Profit: $${topSignal.takeProfit ? parseFloat(topSignal.takeProfit.toString()).toFixed(2) : 'N/A'}`,
                  [{ text: 'OK' }]
                );
              } else {
                Alert.alert('Trade Failed', 'Could not execute trade. Please try again.');
              }
            } catch (error: any) {
              logger.error('❌ [TheWhisper] Trade execution error:', error);
              Alert.alert(
                'Trade Failed',
                error.message || 'Could not execute trade. Please try again.'
              );
            } finally {
              setIsExecutingTrade(false);
            }
          },
        },
      ]
    );
  }, [onTakeTrade, topSignal, symbol, currentPrice, projectedPNL, placeMarketOrder]);

  const handleShowDetails = useCallback(() => {
    setShowDetails(true);
  }, []);

  const handleShowProDrawer = useCallback(() => {
    setShowProDrawer(true);
  }, []);

  // Edge case: No enabled strategies
  // Allow testing even without enabled strategies (signals will still load if available)
  // if (!hasEnabledStrategies) {
  //   return (
  //     <SafeAreaView style={styles.container}>
  //       <View style={styles.emptyState}>
  //         <Icon name="zap" size={48} color="#9CA3AF" />
  //         <Text style={styles.emptyStateTitle}>Enable Strategies First</Text>
  //         <Text style={styles.emptyStateText}>
  //           Go to Strategy Store to enable RAHA strategies, then come back here.
  //         </Text>
  //         <TouchableOpacity
  //           style={styles.emptyStateButton}
  //           onPress={handleNavigateToStrategyStore}
  //         >
  //           <Text style={styles.emptyStateButtonText}>Go to Strategy Store</Text>
  //         </TouchableOpacity>
  //       </View>
  //     </SafeAreaView>
  //   );
  // }

  // Edge case: Error loading signals
  if (signalsError) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.emptyState}>
          <Icon name="alert-circle" size={48} color="#EF4444" />
          <Text style={styles.emptyStateTitle}>Error Loading Signals</Text>
          <Text style={styles.emptyStateText}>
            {signalsError.message || 'Unable to load RAHA signals. Please try again.'}
          </Text>
          <TouchableOpacity
            style={styles.emptyStateButton}
            onPress={() => refetchSignals()}
          >
            <Text style={styles.emptyStateButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  // Edge case: Loading signals
  if (signalsLoading && signals.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingState}>
          <ActivityIndicator size="large" color="#3B82F6" />
          <Text style={styles.loadingText}>Calculating your likely outcome...</Text>
          <Text style={styles.loadingSubtext}>RAHA is analyzing the market</Text>
        </View>
      </SafeAreaView>
    );
  }

  // Edge case: No signals found
  if (!signalsLoading && signals.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        {/* Header with back button */}
        <View style={styles.header}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={handleBack}
          >
            <Icon name="arrow-left" size={24} color="#111827" />
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.headerCenter}
            onPress={() => setShowSymbolPicker(true)}
            activeOpacity={0.7}
          >
            <View style={styles.symbolContainer}>
              <Text style={styles.symbol}>{symbol}</Text>
              <Icon name="chevron-down" size={20} color="#3B82F6" style={styles.symbolChevron} />
            </View>
          </TouchableOpacity>
          <View style={{ width: 24 }} />
        </View>
        
        <View style={styles.emptyState}>
          <Icon name="trending-up" size={48} color="#9CA3AF" />
          <Text style={styles.emptyStateTitle}>No Signals Right Now</Text>
          <Text style={styles.emptyStateText}>
            RAHA didn't find any high-probability setups for {symbol} at this time.
            {'\n\n'}Check back in a few minutes or try a different symbol.
          </Text>
          <View style={styles.emptyStateButtons}>
            <TouchableOpacity
              style={[styles.emptyStateButton, styles.emptyStateButtonSecondary]}
              onPress={() => setShowSymbolPicker(true)}
            >
              <Text style={styles.emptyStateButtonTextSecondary}>Try Different Symbol</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.emptyStateButton}
              onPress={() => refetchSignals()}
            >
              <Text style={styles.emptyStateButtonText}>Refresh</Text>
            </TouchableOpacity>
          </View>
        </View>
        
        {/* Symbol Picker Modal (same as main screen) */}
        <Modal
          visible={showSymbolPicker}
          animationType="slide"
          presentationStyle="pageSheet"
          onRequestClose={() => setShowSymbolPicker(false)}
        >
          <SafeAreaView style={styles.pickerModalContainer}>
            <View style={styles.pickerHeader}>
              <Text style={styles.pickerTitle}>Select Stock</Text>
              <TouchableOpacity
                style={styles.pickerCloseButton}
                onPress={() => setShowSymbolPicker(false)}
              >
                <Icon name="x" size={24} color="#111827" />
              </TouchableOpacity>
            </View>
            
            <View style={styles.pickerSearchContainer}>
              <Icon name="search" size={20} color="#6B7280" style={styles.pickerSearchIcon} />
              <TextInput
                style={styles.pickerSearchInput}
                placeholder="Search symbol (e.g., AAPL, TSLA, SPY)"
                placeholderTextColor="#9CA3AF"
                value={symbolSearch}
                onChangeText={setSymbolSearch}
                autoCapitalize="characters"
                autoCorrect={false}
                returnKeyType="done"
                onSubmitEditing={() => {
                  const newSymbol = symbolSearch.trim().toUpperCase();
                  if (newSymbol && newSymbol.length <= 5 && newSymbol.length >= 1) {
                    setSymbol(newSymbol);
                    setCurrentPrice(0);
                    setChange(0);
                    setChangePercent(0);
                    setShowSymbolPicker(false);
                    setSymbolSearch('');
                  }
                }}
              />
            </View>

            {/* Popular Symbols */}
            <View style={styles.popularSymbolsContainer}>
              <Text style={styles.popularSymbolsTitle}>Popular</Text>
              <View style={styles.popularSymbolsGrid}>
                {['AAPL', 'TSLA', 'SPY', 'QQQ', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'META', 'NFLX'].map((sym) => (
                  <TouchableOpacity
                    key={sym}
                    style={[styles.popularSymbolButton, symbol === sym && styles.popularSymbolButtonActive]}
                    onPress={() => {
                      setSymbol(sym);
                      setCurrentPrice(0);
                      setChange(0);
                      setChangePercent(0);
                      setShowSymbolPicker(false);
                      setSymbolSearch('');
                    }}
                  >
                    <Text style={[styles.popularSymbolText, symbol === sym && styles.popularSymbolTextActive]}>
                      {sym}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            {/* Quick Actions */}
            {symbolSearch.trim().length > 0 && (
              <View style={styles.pickerActions}>
                <TouchableOpacity
                  style={styles.pickerActionButton}
                  onPress={() => {
                    const newSymbol = symbolSearch.trim().toUpperCase();
                    if (newSymbol && newSymbol.length <= 5 && newSymbol.length >= 1) {
                      setSymbol(newSymbol);
                      setCurrentPrice(0);
                      setChange(0);
                      setChangePercent(0);
                      setShowSymbolPicker(false);
                      setSymbolSearch('');
                    } else {
                      Alert.alert('Invalid Symbol', 'Please enter a valid stock symbol (1-5 characters)');
                    }
                  }}
                >
                  <Text style={styles.pickerActionButtonText}>Use {symbolSearch.trim().toUpperCase()}</Text>
                </TouchableOpacity>
              </View>
            )}
          </SafeAreaView>
        </Modal>
      </SafeAreaView>
    );
  }

  // Edge case: Signal missing required data
  if (!topSignal || !topSignal.price || !topSignal.takeProfit || !topSignal.stopLoss) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.emptyState}>
          <Icon name="alert-triangle" size={48} color="#F59E0B" />
          <Text style={styles.emptyStateTitle}>Incomplete Signal Data</Text>
          <Text style={styles.emptyStateText}>
            The signal is missing required information (entry, stop loss, or take profit).
            {'\n\n'}Please wait for a complete signal or try refreshing.
          </Text>
          <TouchableOpacity
            style={styles.emptyStateButton}
            onPress={() => refetchSignals()}
          >
            <Text style={styles.emptyStateButtonText}>Refresh</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView 
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Header - Minimal */}
        <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={handleBack}
        >
          <Icon name="arrow-left" size={24} color="#111827" />
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.headerCenter}
          onPress={() => setShowSymbolPicker(true)}
          activeOpacity={0.7}
        >
          <View style={styles.symbolContainer}>
            <Text style={styles.symbol}>{symbol}</Text>
            <Icon name="chevron-down" size={20} color="#3B82F6" style={styles.symbolChevron} />
          </View>
          <View style={styles.priceRow}>
            <Text style={styles.price}>${currentPrice.toFixed(2)}</Text>
            <Text style={[styles.change, change >= 0 ? styles.changePositive : styles.changeNegative]}>
              {change >= 0 ? '+' : ''}{change.toFixed(2)} ({changePercent >= 0 ? '+' : ''}{changePercent.toFixed(2)}%)
            </Text>
          </View>
        </TouchableOpacity>
        <View style={{ width: 24 }} />
      </View>

      {/* Chart Button - Opens Full-Screen Modal */}
      <TouchableOpacity
        style={styles.chartButton}
        onPress={() => {
          // Enable P&L ribbon by default when opening modal
          if (topSignal && projectedPNL) {
            setShowPNLRibbon(true);
          }
          setShowChartModal(true);
        }}
        activeOpacity={0.8}
      >
        <View style={styles.chartButtonContent}>
          <View style={styles.chartButtonIcon}>
            <Icon name="trending-up" size={24} color="#3B82F6" />
          </View>
          <View style={styles.chartButtonTextContainer}>
            <Text style={styles.chartButtonTitle}>View Price & P&L Chart</Text>
            <Text style={styles.chartButtonSubtitle}>
              See how your trade's profit/loss changes over time
            </Text>
          </View>
          <Icon name="chevron-right" size={20} color="#9CA3AF" />
        </View>
      </TouchableOpacity>

      {/* Full-Screen Chart Modal */}
      <Modal
        visible={showChartModal}
        animationType="slide"
        presentationStyle="fullScreen"
        onRequestClose={() => setShowChartModal(false)}
      >
        <SafeAreaView style={styles.modalContainer}>
          {/* Modal Header */}
          <View style={styles.modalHeader}>
            <TouchableOpacity
              style={styles.modalCloseButton}
              onPress={() => setShowChartModal(false)}
            >
              <Icon name="x" size={24} color="#111827" />
            </TouchableOpacity>
            <Text style={styles.modalTitle}>Price & P&L Chart</Text>
            <View style={{ width: 40 }} />
          </View>

          {/* Full-Screen Chart - Scrollable (both directions) */}
          <ScrollView
            style={styles.modalScrollView}
            contentContainerStyle={styles.modalScrollContent}
            showsVerticalScrollIndicator={true}
            showsHorizontalScrollIndicator={true}
            horizontal={false}
            nestedScrollEnabled={true}
          >
            <ScrollView
              horizontal={true}
              showsHorizontalScrollIndicator={true}
              nestedScrollEnabled={true}
              contentContainerStyle={styles.modalHorizontalScrollContent}
            >
              <View style={styles.modalChartContainer}>
                <StockChart
                  symbol={symbol}
                  timeframe="1H"
                  embedded={true}
                  width={width * 1.5}
                  height={height - 120}
                  minimal={true}
                  pnlOverlay={topSignal && projectedPNL ? {
                    entryPrice: parseFloat(topSignal.price.toString()),
                    takeProfit: topSignal.takeProfit ? parseFloat(topSignal.takeProfit.toString()) : 0,
                    stopLoss: topSignal.stopLoss ? parseFloat(topSignal.stopLoss.toString()) : 0,
                    isLong: topSignal.signalType === 'ENTRY_LONG',
                    riskAmount: projectedPNL.riskAmount || 100,
                    visible: showPNLRibbon,
                  } : undefined}
                />
                
                {/* Toggle P&L ribbon button in modal */}
                {topSignal && projectedPNL && (
                  <TouchableOpacity
                    style={styles.modalRibbonToggle}
                    onPress={() => setShowPNLRibbon(!showPNLRibbon)}
                    activeOpacity={0.7}
                  >
                    <Icon 
                      name={showPNLRibbon ? "eye-off" : "eye"} 
                      size={18} 
                      color="#6B7280" 
                    />
                    <Text style={styles.modalRibbonToggleText}>
                      {showPNLRibbon ? 'Hide' : 'Show'} P&L
                    </Text>
                  </TouchableOpacity>
                )}
              </View>
            </ScrollView>
          </ScrollView>
        </SafeAreaView>
      </Modal>

      {/* Ghost Candle - The Magic Moment */}
      {signalsLoading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#3B82F6" />
          <Text style={styles.loadingText}>Calculating your likely outcome...</Text>
        </View>
      ) : signalsError ? (
        <View style={styles.errorContainer}>
          <Icon name="alert-circle" size={32} color="#EF4444" />
          <Text style={styles.errorText}>Couldn't calculate outcome</Text>
          <Text style={styles.errorSubtext}>{signalsError.message || 'Please try again'}</Text>
          <TouchableOpacity
            style={styles.retryButton}
            onPress={() => refetchSignals()}
          >
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      ) : projectedPNL && topSignal ? (
        <Animated.View
          style={[
            styles.ghostCandleContainer,
            {
              opacity: ghostCandleOpacity,
              transform: [
                { scale: ghostCandleScale },
                { translateY: ghostCandleTranslateY },
              ],
            },
          ]}
        >
          <TouchableOpacity
            style={styles.ghostCandle}
            onPress={handleShowDetails}
            activeOpacity={0.9}
          >
            <Text style={styles.ghostCandleLabel}>
              Likely outcome in next 1–3 hours
            </Text>
            
            <View style={styles.ghostCandleMain}>
              <Text style={styles.ghostCandleGain}>
                +${Math.round(projectedPNL.likelyGain)}
              </Text>
              <Text style={styles.ghostCandleLoss}>
                (or –${Math.round(projectedPNL.maxLoss)} if it goes against)
              </Text>
            </View>

            <View style={styles.ghostCandleStats}>
              <Text style={styles.ghostCandleWinChance}>
                {Math.round(projectedPNL.winChance * 100)}% chance this ends green
              </Text>
            </View>

            <View style={styles.ghostCandleTapHint}>
              <Icon name="info" size={14} color="#6B7280" />
              <Text style={styles.ghostCandleTapHintText}>Tap to see why</Text>
            </View>
          </TouchableOpacity>
        </Animated.View>
      ) : (
        <View style={styles.noSignalContainer}>
          <Icon name="zap-off" size={32} color="#9CA3AF" />
          <Text style={styles.noSignalText}>No high-conviction setup right now</Text>
          <Text style={styles.noSignalSubtext}>
            Check back when market conditions improve
          </Text>
        </View>
      )}

      {/* The Magic Sentence - Animated */}
      {expectancySentence && (
        <Animated.View
          style={[
            styles.expectancyContainer,
            { opacity: expectancyOpacity },
          ]}
        >
          <Text style={styles.expectancySentence}>{expectancySentence}</Text>
        </Animated.View>
      )}

      {/* Regime Badge - Shows market regime oracle output */}
      {topSignal && topSignal.globalRegime && (
        <View style={styles.regimeChipContainer}>
          <View
            style={[
              styles.regimeChip,
              regimeMultiplier > 1.05
                ? styles.regimeChipPositive
                : regimeMultiplier < 0.95
                ? styles.regimeChipDefensive
                : styles.regimeChipNeutral,
            ]}
          >
            <Icon name="activity" size={14} color={regimeColor} />
            <Text style={[styles.regimeChipText, { color: regimeColor }]}>
              {regimeLabel}
            </Text>
            {regimeMultiplier !== 1.0 && (
              <Text style={[styles.regimeChipMultiplier, { color: regimeColor }]}>
                {regimeMultiplier > 1 ? '+' : ''}{((regimeMultiplier - 1) * 100).toFixed(0)}%
              </Text>
            )}
          </View>
          {topSignal.regimeNarration && (
            <Text style={styles.regimeNarration}>{topSignal.regimeNarration}</Text>
          )}
        </View>
      )}

      {/* Market Mood Pill - Animated */}
      {topSignal && (
        <Animated.View
          style={[
            styles.moodContainer,
            { opacity: moodOpacity },
          ]}
        >
          <View style={[styles.moodPill, { backgroundColor: marketMood.color + '20' }]}>
            <View style={[styles.moodDot, { backgroundColor: marketMood.color }]} />
            <Text style={[styles.moodLabel, { color: marketMood.color }]}>
              {marketMood.label}
            </Text>
          </View>
          <Text style={styles.moodSubtext}>
            {topSignal.regimeNarration || (
              marketMood.label === 'Risk-On' && 'Good for quick trades'
              || marketMood.label === 'Risk-Off' && 'Be defensive today'
              || marketMood.label === 'Neutral' && 'Standard conditions'
              || 'Market conditions'
            )}
          </Text>
        </Animated.View>
      )}

      {/* Main Action Button - Animated */}
      {shouldShowTradeButton && (
        <Animated.View
          style={[
            styles.takeTradeButtonContainer,
            { transform: [{ scale: buttonScale }] },
          ]}
        >
          <TouchableOpacity
            style={[styles.takeTradeButton, isExecutingTrade && styles.takeTradeButtonDisabled]}
            onPress={handleTakeTrade}
            activeOpacity={0.8}
            disabled={isExecutingTrade}
          >
            {isExecutingTrade ? (
              <>
                <ActivityIndicator size="small" color="#FFFFFF" style={{ marginRight: 8 }} />
                <Text style={styles.takeTradeButtonText}>Executing...</Text>
              </>
            ) : (
              <Text style={styles.takeTradeButtonText}>Take this trade →</Text>
            )}
          </TouchableOpacity>
        </Animated.View>
      )}

        {/* Secondary Button - Always Visible */}
        <TouchableOpacity
          style={styles.watchingButton}
          onPress={onJustWatching || handleBack}
        >
          <Text style={styles.watchingButtonText}>Nah, just watching</Text>
        </TouchableOpacity>
      </ScrollView>

      {/* Symbol Picker Modal */}
      <Modal
        visible={showSymbolPicker}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setShowSymbolPicker(false)}
      >
        <SafeAreaView style={styles.pickerModalContainer}>
          <View style={styles.pickerHeader}>
            <Text style={styles.pickerTitle}>Select Stock</Text>
            <TouchableOpacity
              style={styles.pickerCloseButton}
              onPress={() => setShowSymbolPicker(false)}
            >
              <Icon name="x" size={24} color="#111827" />
            </TouchableOpacity>
          </View>
          
          <View style={styles.pickerSearchContainer}>
            <Icon name="search" size={20} color="#6B7280" style={styles.pickerSearchIcon} />
            <TextInput
              style={styles.pickerSearchInput}
              placeholder="Search symbol (e.g., AAPL, TSLA, SPY)"
              placeholderTextColor="#9CA3AF"
              value={symbolSearch}
              onChangeText={setSymbolSearch}
              autoCapitalize="characters"
              autoCorrect={false}
              returnKeyType="done"
              onSubmitEditing={() => {
                const newSymbol = symbolSearch.trim().toUpperCase();
                if (newSymbol && newSymbol.length <= 5 && newSymbol.length >= 1) {
                  setSymbol(newSymbol);
                  setCurrentPrice(0);
                  setChange(0);
                  setChangePercent(0);
                  setShowSymbolPicker(false);
                  setSymbolSearch('');
                }
              }}
            />
          </View>

          {/* Popular Symbols */}
          <View style={styles.popularSymbolsContainer}>
            <Text style={styles.popularSymbolsTitle}>Popular</Text>
            <View style={styles.popularSymbolsGrid}>
              {['AAPL', 'TSLA', 'SPY', 'QQQ', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'META', 'NFLX'].map((sym) => (
                <TouchableOpacity
                  key={sym}
                  style={[styles.popularSymbolButton, symbol === sym && styles.popularSymbolButtonActive]}
                  onPress={() => {
                    setSymbol(sym);
                    setCurrentPrice(0);
                    setChange(0);
                    setChangePercent(0);
                    setShowSymbolPicker(false);
                    setSymbolSearch('');
                  }}
                >
                  <Text style={[styles.popularSymbolText, symbol === sym && styles.popularSymbolTextActive]}>
                    {sym}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Quick Actions */}
          {symbolSearch.trim().length > 0 && (
            <View style={styles.pickerActions}>
              <TouchableOpacity
                style={styles.pickerActionButton}
                onPress={() => {
                  const newSymbol = symbolSearch.trim().toUpperCase();
                  if (newSymbol && newSymbol.length <= 5 && newSymbol.length >= 1) {
                    setSymbol(newSymbol);
                    setCurrentPrice(0);
                    setChange(0);
                    setChangePercent(0);
                    setShowSymbolPicker(false);
                    setSymbolSearch('');
                  } else {
                    Alert.alert('Invalid Symbol', 'Please enter a valid stock symbol (1-5 characters)');
                  }
                }}
              >
                <Text style={styles.pickerActionButtonText}>Use {symbolSearch.trim().toUpperCase()}</Text>
              </TouchableOpacity>
            </View>
          )}
        </SafeAreaView>
      </Modal>

      {/* Details Half-Sheet (Progressive Disclosure) */}
      {showDetails && (
        <View style={styles.detailsOverlay}>
          <View style={styles.detailsSheet}>
            <View style={styles.detailsHeader}>
              <Text style={styles.detailsTitle}>Why this number?</Text>
              <TouchableOpacity onPress={() => setShowDetails(false)}>
                <Icon name="x" size={24} color="#6B7280" />
              </TouchableOpacity>
            </View>
            
            <View style={styles.detailsContent}>
              <View style={styles.detailsItem}>
                <Text style={styles.detailsItemLabel}>Win Rate</Text>
                <Text style={styles.detailsItemValue}>
                  {Math.round((projectedPNL?.winChance || 0) * 100)}%
                </Text>
                <Text style={styles.detailsItemExplanation}>
                  This exact setup has happened {Math.round((projectedPNL?.winChance || 0) * 100)}% win rate
                </Text>
              </View>

              <View style={styles.detailsItem}>
                <Text style={styles.detailsItemLabel}>Average Winner</Text>
                <Text style={[styles.detailsItemValue, { color: '#10B981' }]}>
                  +{((projectedPNL?.likelyGain || 0) / (projectedPNL?.riskAmount || 1)).toFixed(1)}R
                </Text>
              </View>

              <View style={styles.detailsItem}>
                <Text style={styles.detailsItemLabel}>Average Loser</Text>
                <Text style={[styles.detailsItemValue, { color: '#EF4444' }]}>
                  –1R
                </Text>
              </View>

              <View style={styles.detailsItem}>
                <Text style={styles.detailsItemLabel}>Your History</Text>
                <Text style={[styles.detailsItemValue, { color: '#10B981' }]}>
                  +71% for you
                </Text>
                <Text style={styles.detailsItemExplanation}>
                  You personally do well on these
                </Text>
              </View>

              <View style={styles.detailsItem}>
                <Text style={styles.detailsItemLabel}>Suggested Risk</Text>
                <Text style={styles.detailsItemValue}>
                  ${Math.round(projectedPNL?.riskAmount || 0)} on your account
                </Text>
                <Text style={styles.detailsItemExplanation}>
                  (1% of your balance)
                </Text>
              </View>

              <TouchableOpacity
                style={styles.showMathButton}
                onPress={handleShowProDrawer}
              >
                <Text style={styles.showMathButtonText}>Show me the full math →</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      )}

      {/* Pro Drawer (Full RAHA Breakdown) */}
      {showProDrawer && (
        <View style={styles.proDrawerOverlay}>
          <View style={styles.proDrawer}>
            <View style={styles.proDrawerHeader}>
              <Text style={styles.proDrawerTitle}>Full RAHA Breakdown</Text>
              <TouchableOpacity onPress={() => setShowProDrawer(false)}>
                <Icon name="x" size={24} color="#6B7280" />
              </TouchableOpacity>
            </View>
            
            <View style={styles.proDrawerContent}>
              <Text style={styles.proDrawerSectionTitle}>Expectancy Engine</Text>
              <Text style={styles.proDrawerText}>
                Win Rate: {(projectedPNL?.winChance || 0) * 100}%
              </Text>
              <Text style={styles.proDrawerText}>
                Avg Win: +{((projectedPNL?.likelyGain || 0) / (projectedPNL?.riskAmount || 1)).toFixed(2)}R
              </Text>
              <Text style={styles.proDrawerText}>
                Avg Loss: –1R
              </Text>
              <Text style={styles.proDrawerText}>
                Expectancy: {((projectedPNL?.likelyGain || 0) * (projectedPNL?.winChance || 0) - (projectedPNL?.riskAmount || 0) * (1 - (projectedPNL?.winChance || 0))) / (projectedPNL?.riskAmount || 1) > 0 ? '+' : ''}{(((projectedPNL?.likelyGain || 0) * (projectedPNL?.winChance || 0) - (projectedPNL?.riskAmount || 0) * (1 - (projectedPNL?.winChance || 0))) / (projectedPNL?.riskAmount || 1)).toFixed(2)}R
              </Text>

              <Text style={[styles.proDrawerSectionTitle, { marginTop: 24 }]}>Active Strategies</Text>
              <Text style={styles.proDrawerText}>
                {topSignal?.strategyVersion?.strategy?.name || 'Momentum + Zone Confluence'}
              </Text>

              <Text style={[styles.proDrawerSectionTitle, { marginTop: 24 }]}>Regime Detection</Text>
              <Text style={styles.proDrawerText}>
                Market: {marketMood.label}
              </Text>

              <Text style={[styles.proDrawerSectionTitle, { marginTop: 24 }]}>Position Sizing</Text>
              <Text style={styles.proDrawerText}>
                Risk: ${Math.round(projectedPNL?.riskAmount || 0)} (1% of account)
              </Text>
              <Text style={styles.proDrawerText}>
                Position Size: Auto-calculated based on stop distance
              </Text>
            </View>
          </View>
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingBottom: 40,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  backButton: {
    padding: 8,
  },
  headerCenter: {
    flex: 1,
    alignItems: 'center',
  },
  symbolContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginBottom: 4,
  },
  symbol: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
  },
  symbolChevron: {
    marginLeft: 2,
    opacity: 0.8,
  },
  priceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
    gap: 8,
  },
  price: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  change: {
    fontSize: 14,
    fontWeight: '600',
  },
  changePositive: {
    color: '#10B981',
  },
  changeNegative: {
    color: '#EF4444',
  },
  chartButton: {
    marginHorizontal: 20,
    marginTop: 16,
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  chartButtonContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  chartButtonIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#3B82F6' + '15',
    justifyContent: 'center',
    alignItems: 'center',
  },
  chartButtonTextContainer: {
    flex: 1,
  },
  chartButtonTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 4,
  },
  chartButtonSubtitle: {
    fontSize: 13,
    color: '#6B7280',
    lineHeight: 18,
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  modalCloseButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
  },
  modalScrollView: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  modalScrollContent: {
    minHeight: height - 100,
  },
  modalHorizontalScrollContent: {
    padding: 20,
    minWidth: width * 1.5,
  },
  modalChartContainer: {
    padding: 20,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    minWidth: width * 1.5,
    minHeight: height - 120,
  },
  modalRibbonToggle: {
    position: 'absolute',
    top: 20,
    right: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 8,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 4,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  modalRibbonToggleText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6B7280',
  },
  chartPlaceholder: {
    alignItems: 'center',
  },
  chartPlaceholderText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6B7280',
  },
  chartPlaceholderSubtext: {
    fontSize: 12,
    color: '#9CA3AF',
    marginTop: 4,
  },
  proViewButton: {
    position: 'absolute',
    top: 12,
    right: 12,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#3B82F6',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    gap: 6,
    shadowColor: '#3B82F6',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 4,
  },
  proViewButtonText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  errorContainer: {
    marginHorizontal: 20,
    marginTop: 24,
    alignItems: 'center',
    padding: 24,
  },
  errorText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#EF4444',
    marginTop: 12,
  },
  errorSubtext: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
    textAlign: 'center',
  },
  retryButton: {
    marginTop: 16,
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: '#3B82F6',
    borderRadius: 12,
  },
  retryButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  loadingContainer: {
    marginHorizontal: 20,
    marginTop: 24,
    alignItems: 'center',
    padding: 24,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#6B7280',
  },
  ghostCandleContainer: {
    marginHorizontal: 20,
    marginTop: 24,
  },
  ghostCandle: {
    backgroundColor: '#F0F9FF',
    borderRadius: 16,
    padding: 20,
    borderWidth: 2,
    borderColor: '#BAE6FD',
    borderStyle: 'dashed',
  },
  ghostCandleLabel: {
    fontSize: 12,
    color: '#0369A1',
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 12,
  },
  ghostCandleMain: {
    alignItems: 'center',
    marginVertical: 12,
  },
  ghostCandleGain: {
    fontSize: 32,
    fontWeight: '800',
    color: '#10B981',
  },
  ghostCandleLoss: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
  },
  ghostCandleStats: {
    alignItems: 'center',
    marginTop: 12,
  },
  ghostCandleWinChance: {
    fontSize: 14,
    fontWeight: '600',
    color: '#0369A1',
  },
  ghostCandleTapHint: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 12,
    gap: 6,
  },
  ghostCandleTapHintText: {
    fontSize: 12,
    color: '#6B7280',
  },
  noSignalContainer: {
    marginHorizontal: 20,
    marginTop: 24,
    alignItems: 'center',
    padding: 32,
  },
  noSignalText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6B7280',
    marginTop: 12,
  },
  noSignalSubtext: {
    fontSize: 14,
    color: '#9CA3AF',
    marginTop: 4,
    textAlign: 'center',
  },
  expectancyContainer: {
    marginHorizontal: 20,
    marginTop: 20,
    padding: 16,
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
  },
  expectancySentence: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111827',
    textAlign: 'center',
    lineHeight: 22,
  },
  regimeChipContainer: {
    alignItems: 'center',
    marginTop: 16,
    marginBottom: 8,
    paddingHorizontal: 20,
  },
  regimeChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    gap: 6,
  },
  regimeChipPositive: {
    backgroundColor: '#10B98120',
  },
  regimeChipDefensive: {
    backgroundColor: '#EF444420',
  },
  regimeChipNeutral: {
    backgroundColor: '#6B728020',
  },
  regimeChipText: {
    fontSize: 13,
    fontWeight: '600',
  },
  regimeChipMultiplier: {
    fontSize: 11,
    fontWeight: '700',
    marginLeft: 4,
  },
  regimeNarration: {
    fontSize: 12,
    color: '#6B7280',
    textAlign: 'center',
    marginTop: 6,
    paddingHorizontal: 20,
    lineHeight: 16,
  },
  moodContainer: {
    marginHorizontal: 20,
    marginTop: 16,
    alignItems: 'center',
  },
  moodPill: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    gap: 6,
  },
  moodDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  moodLabel: {
    fontSize: 14,
    fontWeight: '700',
  },
  moodSubtext: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 4,
  },
  takeTradeButtonContainer: {
    marginHorizontal: 20,
    marginTop: 24,
  },
  takeTradeButton: {
    backgroundColor: '#10B981',
    borderRadius: 16,
    paddingVertical: 18,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    shadowColor: '#10B981',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  takeTradeButtonDisabled: {
    opacity: 0.6,
  },
  takeTradeButtonText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  watchingButton: {
    marginHorizontal: 20,
    marginTop: 12,
    paddingVertical: 14,
    alignItems: 'center',
  },
  watchingButtonText: {
    fontSize: 15,
    color: '#6B7280',
  },
  detailsOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  detailsSheet: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 20,
    maxHeight: height * 0.6,
  },
  detailsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  detailsTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
  },
  detailsContent: {
    gap: 20,
  },
  detailsItem: {
    marginBottom: 16,
  },
  detailsItemLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  detailsItemValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 4,
  },
  detailsItemExplanation: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
  },
  showMathButton: {
    marginTop: 8,
    paddingVertical: 12,
    alignItems: 'center',
  },
  showMathButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#3B82F6',
  },
  proDrawerOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  proDrawer: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 20,
    maxHeight: height * 0.8,
  },
  proDrawerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  proDrawerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
  },
  proDrawerContent: {
    gap: 12,
  },
  proDrawerSectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 8,
  },
  proDrawerText: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyStateTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
    marginTop: 16,
    marginBottom: 8,
  },
  emptyStateText: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 24,
  },
  emptyStateButtons: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 24,
    width: '100%',
    paddingHorizontal: 20,
  },
  emptyStateButton: {
    flex: 1,
    backgroundColor: '#3B82F6',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: 'center',
  },
  emptyStateButtonSecondary: {
    backgroundColor: '#F3F4F6',
  },
  emptyStateButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  emptyStateButtonTextSecondary: {
    color: '#111827',
    fontSize: 16,
    fontWeight: '600',
  },
  loadingState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  loadingText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginTop: 16,
    marginBottom: 8,
  },
  loadingSubtext: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
  },
  pickerModalContainer: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  pickerHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  pickerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
  },
  pickerCloseButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
    justifyContent: 'center',
    alignItems: 'center',
  },
  pickerSearchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 20,
    marginTop: 16,
    marginBottom: 24,
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  pickerSearchIcon: {
    marginRight: 12,
  },
  pickerSearchInput: {
    flex: 1,
    fontSize: 16,
    color: '#111827',
    padding: 0,
  },
  popularSymbolsContainer: {
    paddingHorizontal: 20,
    marginBottom: 24,
  },
  popularSymbolsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6B7280',
    marginBottom: 12,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  popularSymbolsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  popularSymbolButton: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
    backgroundColor: '#F3F4F6',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  popularSymbolButtonActive: {
    backgroundColor: '#3B82F6',
    borderColor: '#3B82F6',
  },
  popularSymbolText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  popularSymbolTextActive: {
    color: '#FFFFFF',
  },
  pickerActions: {
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  pickerActionButton: {
    backgroundColor: '#3B82F6',
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
  },
  pickerActionButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});

