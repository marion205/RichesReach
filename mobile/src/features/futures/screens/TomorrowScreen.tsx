/**
 * Tomorrow Screen - Trade Tomorrow's Markets Today
 * Simple, Jobs-style: One sentence, one visual, one action
 */

import React, { useState, useCallback, useEffect, useMemo, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Alert,
  useColorScheme,
  Modal,
  Share,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import * as Haptics from 'expo-haptics';

import FuturesService from '../services/FuturesService';
import { FuturesRecommendation, FuturesPosition } from '../types/FuturesTypes';
import SparkMini from '../../../components/charts/SparkMini';
import { API_HTTP } from '../../../config/api';
import logger from '../../../utils/logger';
import { useWatchlist } from '../../../shared/hooks/useWatchlist';

// Mock data for demo when API is unavailable
const getMockRecommendations = (): FuturesRecommendation[] => [
  {
    symbol: 'MESZ5',
    name: 'Micro E-mini S&P 500',
    why_now: 'Strong earnings season momentum and positive macro indicators suggest continued upward trend.',
    max_loss: 250,
    max_gain: 750,
    probability: 72,
    action: 'Buy',
    current_price: 22.95,
    price_change: 0.45,
    price_change_percent: 2.0, // Top mover candidate
    volume_ratio: 1.8, // Unusual volume
    price_history: [22.50, 22.55, 22.60, 22.65, 22.70, 22.75, 22.80, 22.85, 22.90, 22.92, 22.94, 22.95], // For sparkline
  },
  {
    symbol: 'MNQZ5',
    name: 'Micro E-mini NASDAQ-100',
    why_now: 'Tech sector showing resilience with AI-driven growth. Support level holding strong.',
    max_loss: 300,
    max_gain: 900,
    probability: 68,
    action: 'Buy',
    current_price: 15.25,
    price_change: 0.30,
    price_change_percent: 2.0, // Top mover candidate
    volume_ratio: 1.2,
    price_history: [15.00, 15.05, 15.10, 15.12, 15.15, 15.18, 15.20, 15.22, 15.24, 15.25], // For sparkline
  },
  {
    symbol: 'M6EZ5',
    name: 'Micro Euro FX',
    why_now: 'ECB policy pivot expected. Dollar strength may be reaching peak.',
    max_loss: 200,
    max_gain: 600,
    probability: 65,
    action: 'Sell',
    current_price: 1.0850,
    price_change: -0.0020,
    price_change_percent: -0.18,
    volume_ratio: 0.9,
    price_history: [1.0870, 1.0865, 1.0860, 1.0858, 1.0855, 1.0852, 1.0850], // For sparkline
  },
  {
    symbol: 'MGCZ5',
    name: 'Micro Gold',
    why_now: 'Inflation concerns and geopolitical tensions supporting safe-haven demand.',
    max_loss: 350,
    max_gain: 850,
    probability: 70,
    action: 'Buy',
    current_price: 2050.50,
    price_change: 12.30,
    price_change_percent: 0.6, // Top mover candidate
    volume_ratio: 1.6, // Unusual volume
    price_history: [2038.20, 2040.00, 2042.50, 2045.00, 2047.50, 2049.00, 2050.00, 2050.50], // For sparkline
  },
];

export default function TomorrowScreen({ navigation }: any) {
  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';
  
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [usingCachedData, setUsingCachedData] = useState(true); // Start with true to show mock data immediately
  const [recommendations, setRecommendations] = useState<FuturesRecommendation[]>(getMockRecommendations()); // Initialize with mock data
  const [positions, setPositions] = useState<FuturesPosition[]>([]);
  const [showPositions, setShowPositions] = useState(false);
  const [viewMode, setViewMode] = useState<'list' | 'heatmap'>('list');
  const [selectedContract, setSelectedContract] = useState<FuturesRecommendation | null>(null);
  const [showContractInfo, setShowContractInfo] = useState(false);
  // Phase 3: Chart modal and filters
  const [showChartModal, setShowChartModal] = useState(false);
  const [chartContract, setChartContract] = useState<FuturesRecommendation | null>(null);
  const [sortBy, setSortBy] = useState<'default' | 'price_change' | 'probability' | 'category'>('default');
  const [filterCategory, setFilterCategory] = useState<string | null>(null);
  // Phase 3: Comparison view
  const [comparisonContracts, setComparisonContracts] = useState<FuturesRecommendation[]>([]);
  const [showComparisonModal, setShowComparisonModal] = useState(false);
  
  // Watchlist hook
  const { addToWatchlist } = useWatchlist();
  
  // Real-time price updates via polling (Phase 1 - upgrade to WebSocket in Phase 2)
  const [priceUpdates, setPriceUpdates] = useState<Record<string, { price: number; change: number; changePercent: number; priceHistory: number[] }>>({});
  const pricePollingRef = useRef<NodeJS.Timeout | null>(null);
  
  // Determine if we're in Regular Trading Hours (RTH) or Extended Trading Hours (ETH)
  // RTH: 9:30 AM - 4:00 PM ET (Monday-Friday)
  // ETH: 4:00 PM - 9:30 AM ET (overnight/pre-market)
  const getTradingSession = useCallback(() => {
    const now = new Date();
    const day = now.getDay(); // 0 = Sunday, 6 = Saturday
    const hour = now.getHours();
    const minute = now.getMinutes();
    const timeInMinutes = hour * 60 + minute;
    
    // Weekend = closed
    if (day === 0 || day === 6) {
      return { type: 'closed', label: 'Closed', isRTH: false };
    }
    
    // RTH: 9:30 AM (570 min) to 4:00 PM (960 min) ET
    const rthStart = 9 * 60 + 30; // 9:30 AM
    const rthEnd = 16 * 60; // 4:00 PM
    
    if (timeInMinutes >= rthStart && timeInMinutes < rthEnd) {
      return { type: 'rth', label: 'RTH', isRTH: true };
    } else {
      return { type: 'eth', label: 'ETH', isRTH: false };
    }
  }, []);
  
  const tradingSession = useMemo(() => getTradingSession(), [getTradingSession]);

  // Load recommendations with proper error handling (no silent mock fallback)
  const loadRecommendations = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      setUsingCachedData(false);
      
      // Add timeout wrapper (reduced to 5s for faster fallback to mock data)
      const timeoutPromise = new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Request timeout')), 5000)
      );
      
      const fetchPromise = FuturesService.getRecommendations();
      const resp = await Promise.race([fetchPromise, timeoutPromise]) as { recommendations: FuturesRecommendation[] };
      
      if (resp.recommendations && resp.recommendations.length > 0) {
        setRecommendations(resp.recommendations);
        setUsingCachedData(false); // Clear cached flag when real data loads
        setError(null); // Clear any previous errors
        // Initialize prices from recommendations (if included)
        const initialPrices: Record<string, { price: number; change: number; changePercent: number; priceHistory: number[] }> = {};
        resp.recommendations.forEach(rec => {
          if (rec.current_price !== undefined) {
            initialPrices[rec.symbol] = {
              price: rec.current_price,
              change: rec.price_change || 0,
              changePercent: rec.price_change_percent || 0,
              priceHistory: rec.price_history || [],
            };
          }
        });
        if (Object.keys(initialPrices).length > 0) {
          setPriceUpdates(initialPrices);
        }
        // Start polling for real-time price updates
        startPricePolling(resp.recommendations.map(r => r.symbol));
      } else {
        // Backend returned empty array - use mock data as fallback
        logger.warn('⚠️ [Tomorrow] Backend returned empty recommendations, using mock data');
        const mockData = getMockRecommendations();
        setRecommendations(mockData);
        setUsingCachedData(true);
        setError('No live recommendations available. Showing demo data. Pull to refresh.');
        // Start polling for mock symbols (won't work but won't crash)
        startPricePolling(mockData.map(r => r.symbol));
      }
    } catch (e: any) {
      logger.error('❌ [Tomorrow] Failed to load recommendations:', e);
      
      // Show user-friendly error message in banner (non-intrusive)
      // Only show modal if this is the FIRST load and we have NO cached data
      const hasCachedData = recommendations.length > 0;
      
      if (e?.message?.includes('timeout')) {
        // If no cached data, use mock data as fallback so screen still loads
        if (!hasCachedData) {
          logger.warn('⚠️ [Tomorrow] Using mock data due to timeout');
          setRecommendations(getMockRecommendations());
          setUsingCachedData(true);
          setError('Connection timeout. Showing demo data. Pull to refresh for live data.');
        } else {
          setError('Connection timeout. Showing cached data.');
          setUsingCachedData(true);
        }
        // Only show modal on first load with no cached data (and no mock fallback)
        // Removed modal to avoid blocking - banner is sufficient
      } else if (e?.message?.includes('Network request failed') || e?.message?.includes('Failed to fetch')) {
        // If no cached data, use mock data as fallback so screen still loads
        if (!hasCachedData) {
          logger.warn('⚠️ [Tomorrow] Using mock data due to network error');
          setRecommendations(getMockRecommendations());
          setUsingCachedData(true);
          setError('Network error. Showing demo data. Pull to refresh for live data.');
        } else {
          setError('Network error. Showing cached data.');
          setUsingCachedData(true);
        }
        // Removed modal to avoid blocking - banner is sufficient
      } else {
        // If no cached data, use mock data as fallback so screen still loads
        if (!hasCachedData) {
          logger.warn('⚠️ [Tomorrow] Using mock data due to error');
          setRecommendations(getMockRecommendations());
          setUsingCachedData(true);
          setError('Unable to load. Showing demo data. Pull to refresh for live data.');
        } else {
          setError('Update failed. Showing cached data.');
          setUsingCachedData(true);
        }
        // Removed modal to avoid blocking - banner is sufficient
      }
    } finally {
      setLoading(false);
    }
  }, [recommendations.length]);

  // Load recommendations on mount
  React.useEffect(() => {
    loadRecommendations();
  }, [loadRecommendations]);

  const loadPositions = useCallback(async () => {
    try {
      const resp = await FuturesService.getPositions();
      setPositions(resp.positions || []);
    } catch (e) {
      // Silent fail for positions
    }
  }, []);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadRecommendations();
    await loadPositions();
    setRefreshing(false);
  }, [loadRecommendations, loadPositions]);

  const handleTrade = useCallback(async (rec: FuturesRecommendation) => {
    // Haptic feedback
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    
    Alert.alert(
      'Confirm Trade',
      `${rec.action} ${rec.symbol}?\n\nWhy: ${rec.why_now}\nMax Loss: $${rec.max_loss}`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Trade',
          onPress: async () => {
            try {
              const result = await FuturesService.placeOrder({
                symbol: rec.symbol,
                side: rec.action === 'Buy' ? 'BUY' : 'SELL',
                quantity: 1, // Start with 1 micro contract
              });
              
              // Check if blocked with "Why not"
              if (result.status === 'blocked' && result.why_not) {
                const whyNot = result.why_not;
                Alert.alert(
                  'Order Blocked',
                  `${whyNot.reason}\n\n${whyNot.fix || ''}`,
                  [{ text: 'OK' }]
                );
              } else if (result.status === 'duplicate') {
                Alert.alert('Info', 'Order already submitted');
              } else {
                Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
                Alert.alert('Success', result.message || 'Order placed');
                handleRefresh();
              }
            } catch (e: any) {
              Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
              Alert.alert('Error', e.message || 'Failed to place order');
            }
          },
        },
      ]
    );
  }, [handleRefresh]);

  // Phase 3: Share recommendation
  const handleShare = useCallback(async (rec: FuturesRecommendation) => {
    try {
      const shareText = `Check out ${rec.symbol} (${rec.name})\n\n` +
        `Why Now: ${rec.why_now}\n\n` +
        `Max Loss: $${rec.max_loss} | Max Gain: $${rec.max_gain} | Probability: ${rec.probability}%\n\n` +
        `Action: ${rec.action}\n\n` +
        `Current Price: ${rec.current_price ? `$${rec.current_price.toFixed(2)}` : 'N/A'}\n` +
        `Price Change: ${rec.price_change_percent ? `${rec.price_change_percent >= 0 ? '+' : ''}${rec.price_change_percent.toFixed(2)}%` : 'N/A'}\n\n` +
        `Shared from RichesReach`;
      
      const result = await Share.share({
        message: shareText,
        title: `${rec.symbol} Trading Recommendation`,
      });
      
      if (result.action === Share.sharedAction) {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      }
    } catch (error: any) {
      logger.error('Error sharing recommendation:', error);
      Alert.alert('Error', 'Failed to share recommendation');
    }
  }, []);

  // Phase 3: Add to watchlist
  const handleAddToWatchlist = useCallback(async (rec: FuturesRecommendation) => {
    try {
      const result = await addToWatchlist({
        symbol: rec.symbol,
        company_name: rec.name,
        notes: `Futures recommendation - ${rec.action} | Probability: ${rec.probability}% | Max Gain: $${rec.max_gain}`,
      });

      if (result?.data?.addToWatchlist?.success) {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        Alert.alert('Success', `${rec.symbol} added to watchlist!`);
      } else {
        const message = result?.data?.addToWatchlist?.message || 'Failed to add to watchlist';
        Alert.alert('Info', message);
      }
    } catch (error: any) {
      logger.error('Error adding to watchlist:', error);
      Alert.alert('Error', 'Failed to add to watchlist. Please try again.');
    }
  }, [addToWatchlist]);

  // Phase 3: Toggle contract for comparison
  const handleToggleComparison = useCallback((rec: FuturesRecommendation) => {
    setComparisonContracts(prev => {
      const exists = prev.find(r => r.symbol === rec.symbol);
      if (exists) {
        const filtered = prev.filter(r => r.symbol !== rec.symbol);
        if (filtered.length === 0) {
          setShowComparisonModal(false);
        }
        return filtered;
      } else {
        const updated = [...prev, rec].slice(0, 3); // Max 3 contracts
        if (updated.length === 1) {
          setShowComparisonModal(true);
        }
        return updated;
      }
    });
  }, []);
  
  // Render recommendation card with real-time data
  const renderRecommendationCard = useCallback(({ item: rec }: { item: FuturesRecommendation }) => {
    const hasPrice = rec.current_price !== undefined;
    const change = rec.price_change || 0;
    const changePercent = rec.price_change_percent || 0;
    const isPositive = change >= 0;
    const priceColor = isPositive ? '#34C759' : '#FF3B30';
    
    // Generate sparkline data (24h or since midnight)
    const sparklineData = rec.price_history || [];
    
    // Format "Why Now" as bullet points
    const whyNowBullets = rec.why_now
      .split(/[.;]/)
      .map(s => s.trim())
      .filter(s => s.length > 0)
      .slice(0, 3); // Limit to 3 bullets for clean UI
    
    // Session indicator background color
    const sessionBgColor = tradingSession.isRTH 
      ? (isDark ? 'rgba(52, 199, 89, 0.1)' : 'rgba(52, 199, 89, 0.05)')
      : (isDark ? 'rgba(255, 159, 10, 0.1)' : 'rgba(255, 159, 10, 0.05)');
    
    return (
      <TouchableOpacity
        style={[
          styles.card,
          isDark && styles.cardDark,
          { backgroundColor: isDark ? '#1C1C1E' : '#FFFFFF' },
          { borderLeftWidth: 3, borderLeftColor: tradingSession.isRTH ? '#34C759' : '#FF9F0A' }
        ]}
        onPress={() => {
          // Phase 3: Tap card to open chart modal
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          setChartContract(rec);
          setShowChartModal(true);
        }}
        activeOpacity={0.7}
      >
        {/* Session Indicator with Badges */}
        <View style={[styles.sessionIndicator, { backgroundColor: sessionBgColor }]}>
          <View style={styles.sessionIndicatorLeft}>
            <View style={[
              styles.sessionBadge,
              { backgroundColor: tradingSession.isRTH ? '#34C759' : '#FF9F0A' }
            ]}>
              <Text style={styles.sessionBadgeText}>{tradingSession.label}</Text>
            </View>
            <Text 
              style={[styles.sessionLabel, isDark && styles.sessionLabelDark]}
              numberOfLines={1}
              ellipsizeMode="tail"
            >
              {tradingSession.isRTH ? 'Regular Trading Hours' : 'Extended Hours'}
            </Text>
          </View>
          <View style={styles.badgesContainer}>
            {isTopMover(rec.symbol) && (
              <View style={[styles.badge, styles.topMoverBadge]}>
                <Icon name="trending-up" size={9} color="#FFFFFF" />
                <Text style={styles.badgeText} numberOfLines={1}>Top</Text>
              </View>
            )}
            {hasUnusualVolume(rec) && (
              <View style={[styles.badge, styles.unusualVolumeBadge]}>
                <Icon name="activity" size={9} color="#FFFFFF" />
                <Text style={styles.badgeText} numberOfLines={1}>Vol</Text>
              </View>
            )}
            <TouchableOpacity
              onPress={(e) => {
                e.stopPropagation();
                setSelectedContract(rec);
                setShowContractInfo(true);
              }}
              style={styles.infoButton}
            >
              <Icon name="info" size={14} color={isDark ? '#8E8E93' : '#6B7280'} />
            </TouchableOpacity>
            {/* Phase 3: Comparison toggle button */}
            <TouchableOpacity
              onPress={(e) => {
                e.stopPropagation();
                handleToggleComparison(rec);
              }}
              style={[
                styles.comparisonToggleButton,
                comparisonContracts.find(c => c.symbol === rec.symbol) && styles.comparisonToggleButtonActive
              ]}
            >
              <Icon 
                name="layers" 
                size={12} 
                color={comparisonContracts.find(c => c.symbol === rec.symbol) 
                  ? '#FFFFFF' 
                  : (isDark ? '#8E8E93' : '#6B7280')} 
              />
            </TouchableOpacity>
          </View>
        </View>
        
        <View style={styles.cardHeader}>
          <View style={styles.cardHeaderLeft}>
            <Text style={[styles.cardSymbol, isDark && styles.cardSymbolDark]}>{rec.symbol}</Text>
            <Text style={[styles.cardName, isDark && styles.cardNameDark]}>{rec.name}</Text>
          </View>
          {hasPrice && (
            <View style={styles.cardPriceContainer}>
              <Text style={[styles.cardPrice, isDark && styles.cardPriceDark]}>${rec.current_price.toFixed(2)}</Text>
              <View style={[styles.priceChangeRow, { backgroundColor: priceColor + '15' }]}>
                <Icon 
                  name={isPositive ? 'arrow-up' : 'arrow-down'} 
                  size={12} 
                  color={priceColor} 
                />
                <Text style={[styles.priceChange, { color: priceColor }]}>
                  {isPositive ? '+' : ''}{change.toFixed(2)} ({isPositive ? '+' : ''}{changePercent.toFixed(2)}%)
                </Text>
              </View>
            </View>
          )}
        </View>
        
        {/* Sparkline - Always show (SparkMini has fallback for empty data) */}
        <View style={styles.sparklineContainer}>
          <SparkMini
            data={sparklineData.length > 0 ? sparklineData : undefined}
            width={120}
            height={24}
            upColor="#34C759"
            downColor="#FF3B30"
          />
        </View>
        
        {/* Why Now as Bullet Points */}
        <View style={styles.whyNowContainer}>
          <Text style={[styles.whyNowTitle, isDark && styles.whyNowTitleDark]}>Why Now:</Text>
          {whyNowBullets.map((bullet, idx) => (
            <View key={idx} style={styles.whyNowBullet}>
              <Text style={[styles.whyNowBulletText, isDark && styles.whyNowBulletTextDark]}>
                • {bullet}
              </Text>
            </View>
          ))}
        </View>
        
        <View style={styles.cardMetrics}>
          <View style={styles.cardMetric}>
            <Text style={[styles.cardMetricLabel, isDark && styles.cardMetricLabelDark]}>Max Loss</Text>
            <Text style={[styles.cardMetricValue, isDark && styles.cardMetricValueDark]}>${rec.max_loss}</Text>
          </View>
          <View style={styles.cardMetric}>
            <Text style={[styles.cardMetricLabel, isDark && styles.cardMetricLabelDark]}>Max Gain</Text>
            <Text style={[styles.cardMetricValue, styles.positive, isDark && styles.cardMetricValueDark]}>${rec.max_gain}</Text>
          </View>
          <View style={styles.cardMetric}>
            <Text style={[styles.cardMetricLabel, isDark && styles.cardMetricLabelDark]}>Probability</Text>
            <Text style={[styles.cardMetricValue, isDark && styles.cardMetricValueDark]}>{rec.probability}%</Text>
          </View>
        </View>

        <TouchableOpacity
          style={styles.cardAction}
          onPress={(e) => {
            e.stopPropagation();
            handleTrade(rec);
          }}
          activeOpacity={0.7}
        >
          <Text style={[styles.cardActionText, isDark && styles.cardActionTextDark]}>{rec.action}</Text>
          <Icon name="chevron-right" size={20} color={isDark ? '#0A84FF' : '#007AFF'} />
        </TouchableOpacity>
      </TouchableOpacity>
    );
  }, [handleTrade, isDark, tradingSession, isTopMover, hasUnusualVolume]);
  
  // Render heatmap cell
  const renderHeatmapCell = useCallback((rec: FuturesRecommendation) => {
    const hasPrice = rec.current_price !== undefined;
    const change = rec.price_change || 0;
    const changePercent = rec.price_change_percent || 0;
    const isPositive = change >= 0;
    const priceColor = isPositive ? '#34C759' : '#FF3B30';
    
    // Color intensity based on price change
    const intensity = Math.min(Math.abs(changePercent) / 5, 1); // Max at 5% change
    const bgColor = isPositive 
      ? `rgba(52, 199, 89, ${0.1 + intensity * 0.3})`
      : `rgba(255, 59, 48, ${0.1 + intensity * 0.3})`;
    
    return (
      <TouchableOpacity
        key={rec.symbol}
        style={[
          styles.heatmapCell,
          { backgroundColor: bgColor },
          isDark && styles.heatmapCellDark
        ]}
        onPress={() => handleTrade(rec)}
        activeOpacity={0.7}
      >
        <View style={styles.heatmapCellHeader}>
          <Text style={[styles.heatmapSymbol, isDark && styles.heatmapSymbolDark]}>{rec.symbol}</Text>
          <View style={styles.heatmapBadges}>
            {isTopMover(rec.symbol) && (
              <View style={[styles.badge, styles.topMoverBadge, styles.heatmapBadge]}>
                <Icon name="trending-up" size={8} color="#FFFFFF" />
              </View>
            )}
            {hasUnusualVolume(rec) && (
              <View style={[styles.badge, styles.unusualVolumeBadge, styles.heatmapBadge]}>
                <Icon name="activity" size={8} color="#FFFFFF" />
              </View>
            )}
            <TouchableOpacity
              onPress={(e) => {
                e.stopPropagation();
                setSelectedContract(rec);
                setShowContractInfo(true);
              }}
              style={styles.heatmapInfoButton}
            >
              <Icon name="info" size={12} color={isDark ? '#8E8E93' : '#6B7280'} />
            </TouchableOpacity>
          </View>
        </View>
        <Text style={[styles.heatmapName, isDark && styles.heatmapNameDark]} numberOfLines={1}>
          {rec.name}
        </Text>
        {hasPrice && (
          <View style={styles.heatmapPrice}>
            <Text style={[styles.heatmapPriceValue, isDark && styles.heatmapPriceValueDark]}>
              ${rec.current_price.toFixed(2)}
            </Text>
            <Text style={[styles.heatmapPriceChange, { color: priceColor }]}>
              {isPositive ? '+' : ''}{changePercent.toFixed(2)}%
            </Text>
          </View>
        )}
        <View style={styles.heatmapMetrics}>
          <Text style={[styles.heatmapMetric, isDark && styles.heatmapMetricDark]}>
            {rec.probability}% prob
          </Text>
          <Text style={[styles.heatmapAction, { color: rec.action === 'Buy' ? '#34C759' : '#FF3B30' }]}>
            {rec.action}
          </Text>
        </View>
      </TouchableOpacity>
    );
  }, [handleTrade, isDark, isTopMover, hasUnusualVolume]);
  
  // Render heatmap view
  const renderHeatmap = useCallback(() => {
    const categories = Object.keys(recommendationsByCategory).sort();
    
    if (categories.length === 0) {
      return (
        <View style={styles.center}>
          <Icon name="grid" size={48} color="#8E8E93" />
          <Text style={[styles.emptyText, isDark && styles.emptyTextDark]}>No recommendations to display</Text>
        </View>
      );
    }
    
    return (
      <ScrollView 
        style={styles.heatmapContainer}
        contentContainerStyle={styles.heatmapContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />}
      >
        {categories.map(category => {
          const categoryRecs = recommendationsByCategory[category];
          if (!categoryRecs || categoryRecs.length === 0) return null;
          
          return (
            <View key={category} style={styles.heatmapCategory}>
              <Text style={[styles.heatmapCategoryTitle, isDark && styles.heatmapCategoryTitleDark]}>
                {category}
              </Text>
              <View style={styles.heatmapGrid}>
                {categoryRecs.map(rec => renderHeatmapCell(rec))}
              </View>
            </View>
          );
        })}
      </ScrollView>
    );
  }, [recommendationsByCategory, renderHeatmapCell, refreshing, handleRefresh, isDark]);
  
  // Skeleton loader for loading state
  const renderSkeletonLoader = useCallback(() => (
    <View style={styles.skeletonCard}>
      <View style={styles.skeletonHeader}>
        <View style={[styles.skeletonBox, { width: 80, height: 24 }]} />
        <View style={[styles.skeletonBox, { width: 100, height: 16, marginTop: 4 }]} />
      </View>
      <View style={[styles.skeletonBox, { width: '100%', height: 16, marginTop: 12 }]} />
      <View style={[styles.skeletonBox, { width: '80%', height: 16, marginTop: 8 }]} />
      <View style={styles.skeletonMetrics}>
        <View style={[styles.skeletonBox, { width: 60, height: 40 }]} />
        <View style={[styles.skeletonBox, { width: 60, height: 40 }]} />
        <View style={[styles.skeletonBox, { width: 60, height: 40 }]} />
      </View>
    </View>
  ), []);

  // Poll for real-time prices (Phase 1 - upgrade to WebSocket in Phase 2)
  const fetchPrices = useCallback(async (symbols: string[]) => {
    if (!symbols.length) return;
    
    try {
      // Try to fetch real prices from API
      const pricePromises = symbols.map(async (symbol) => {
        try {
          const response = await fetch(`${API_HTTP}/api/futures/price/${symbol}`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
          });
          
          if (response.ok) {
            const data = await response.json();
            return {
              symbol,
              price: data.price || 0,
              change: data.change || 0,
              changePercent: data.changePercent || 0,
              priceHistory: data.priceHistory || [],
            };
          }
          return null;
        } catch (e) {
          logger.warn(`⚠️ [Tomorrow] Failed to fetch price for ${symbol}:`, e);
          return null;
        }
      });
      
      const results = await Promise.all(pricePromises);
      const updates: Record<string, { price: number; change: number; changePercent: number; priceHistory: number[] }> = {};
      
      results.forEach((result) => {
        if (result && result.price > 0) {
          updates[result.symbol] = {
            price: result.price,
            change: result.change,
            changePercent: result.changePercent,
            priceHistory: result.priceHistory,
          };
        }
      });
      
      // If we got some updates, use them
      if (Object.keys(updates).length > 0) {
        setPriceUpdates(prev => ({ ...prev, ...updates }));
      } else {
        // Fallback: Use price data from recommendations if available
        const recUpdates: Record<string, { price: number; change: number; changePercent: number; priceHistory: number[] }> = {};
        symbols.forEach((symbol) => {
          const rec = recommendations.find(r => r.symbol === symbol);
          if (rec && rec.current_price !== undefined) {
            recUpdates[symbol] = {
              price: rec.current_price,
              change: rec.price_change || 0,
              changePercent: rec.price_change_percent || 0,
              priceHistory: rec.price_history || [],
            };
          }
        });
        if (Object.keys(recUpdates).length > 0) {
          setPriceUpdates(prev => ({ ...prev, ...recUpdates }));
        }
      }
    } catch (e) {
      logger.error('❌ [Tomorrow] Error fetching prices:', e);
    }
  }, [recommendations]);
  
  // Start polling for prices
  const startPricePolling = useCallback((symbols: string[]) => {
    if (!symbols.length) return;
    
    // Fetch immediately
    fetchPrices(symbols);
    
    // Then poll every 5 seconds
    pricePollingRef.current = setInterval(() => {
      fetchPrices(symbols);
    }, 5000);
  }, [fetchPrices]);
  
  // Stop polling
  const stopPricePolling = useCallback(() => {
    if (pricePollingRef.current) {
      clearInterval(pricePollingRef.current);
      pricePollingRef.current = null;
    }
  }, []);
  
  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      stopPricePolling();
    };
  }, [stopPricePolling]);

  // Load positions on mount
  React.useEffect(() => {
    loadPositions();
  }, [loadPositions]);
  
  // Merge real-time price updates with recommendations
  const recommendationsWithPrices = useMemo(() => {
    return recommendations.map(rec => {
      const priceUpdate = priceUpdates[rec.symbol];
      if (priceUpdate) {
        return {
          ...rec,
          current_price: priceUpdate.price,
          price_change: priceUpdate.change,
          price_change_percent: priceUpdate.changePercent,
          price_history: priceUpdate.priceHistory,
          last_updated: new Date().toISOString(),
        };
      }
      return rec;
    });
  }, [recommendations, priceUpdates]);

  // Helper to categorize contracts
  const getContractCategory = useCallback((symbol: string): string => {
    if (symbol.startsWith('MES') || symbol.startsWith('MNQ') || symbol.startsWith('MYM') || symbol.startsWith('M2K')) {
      return 'Equity Index';
    } else if (symbol.startsWith('M6E') || symbol.startsWith('M6B') || symbol.startsWith('M6A')) {
      return 'Currency';
    } else if (symbol.startsWith('MGC') || symbol.startsWith('MCL') || symbol.startsWith('MNG')) {
      return 'Commodities';
    }
    return 'Other';
  }, []);

  // Phase 3: Filter and sort recommendations
  const filteredAndSortedRecommendations = useMemo(() => {
    let filtered = [...recommendationsWithPrices];
    
    // Apply category filter
    if (filterCategory) {
      filtered = filtered.filter(rec => getContractCategory(rec.symbol) === filterCategory);
    }
    
    // Apply sorting
    if (sortBy === 'price_change') {
      filtered.sort((a, b) => Math.abs(b.price_change_percent || 0) - Math.abs(a.price_change_percent || 0));
    } else if (sortBy === 'probability') {
      filtered.sort((a, b) => b.probability - a.probability);
    } else if (sortBy === 'category') {
      filtered.sort((a, b) => {
        const catA = getContractCategory(a.symbol);
        const catB = getContractCategory(b.symbol);
        return catA.localeCompare(catB);
      });
    }
    // 'default' keeps original order
    
    return filtered;
  }, [recommendationsWithPrices, filterCategory, sortBy, getContractCategory]);

  // Group recommendations by category for heatmap
  const recommendationsByCategory = useMemo(() => {
    const grouped: Record<string, typeof recommendationsWithPrices> = {};
    recommendationsWithPrices.forEach(rec => {
      const category = getContractCategory(rec.symbol);
      if (!grouped[category]) {
        grouped[category] = [];
      }
      grouped[category].push(rec);
    });
    return grouped;
  }, [recommendationsWithPrices, getContractCategory]);

  // Identify Top Movers (highest absolute price change %)
  const topMovers = useMemo(() => {
    const withPriceChange = recommendationsWithPrices.filter(r => 
      r.price_change_percent !== undefined && r.price_change_percent !== null
    );
    
    if (withPriceChange.length === 0) {
      // If no price data, show first 3 as top movers for demo
      return recommendationsWithPrices.slice(0, 3).map(r => r.symbol);
    }
    
    return [...withPriceChange]
      .sort((a, b) => Math.abs(b.price_change_percent || 0) - Math.abs(a.price_change_percent || 0))
      .slice(0, 3)
      .map(r => r.symbol);
  }, [recommendationsWithPrices]);

  // Check if a recommendation is a top mover
  const isTopMover = useCallback((symbol: string) => {
    return topMovers.includes(symbol);
  }, [topMovers]);

  // Check if a recommendation has unusual volume (volume_ratio > 1.5)
  const hasUnusualVolume = useCallback((rec: FuturesRecommendation) => {
    return rec.volume_ratio !== undefined && rec.volume_ratio > 1.5;
  }, []);

  // Get contract specifications for info modal
  const getContractSpecs = useCallback((symbol: string) => {
    const root = symbol.substring(0, 3);
    const specs: Record<string, { tickSize: number; tickValue: number; contractSize: number; margin: number }> = {
      'MES': { tickSize: 0.25, tickValue: 1.25, contractSize: 5, margin: 1200 },
      'MNQ': { tickSize: 0.25, tickValue: 0.50, contractSize: 2, margin: 1200 },
      'M6E': { tickSize: 0.0001, tickValue: 1.25, contractSize: 12500, margin: 500 },
      'MGC': { tickSize: 0.10, tickValue: 1.0, contractSize: 10, margin: 1000 },
      'MYM': { tickSize: 1.0, tickValue: 0.50, contractSize: 0.50, margin: 1200 },
      'M2K': { tickSize: 0.10, tickValue: 0.50, contractSize: 5, margin: 1200 },
    };
    return specs[root] || { tickSize: 0.01, tickValue: 1.0, contractSize: 1, margin: 1000 };
  }, []);

  return (
    <View style={[styles.container, isDark && styles.containerDark]}>
      <View style={[styles.header, isDark && styles.headerDark]}>
        <View style={styles.headerTop}>
          <View style={styles.headerLeft}>
            <Text style={[styles.headerTitle, isDark && styles.headerTitleDark]}>Tomorrow</Text>
            <Text style={[styles.headerSubtitle, isDark && styles.headerSubtitleDark]}>Trade tomorrow's markets today</Text>
          </View>
          {/* View Toggle */}
          <View style={styles.viewToggle}>
            <TouchableOpacity
              style={[styles.toggleButton, viewMode === 'list' && styles.toggleButtonActive]}
              onPress={() => setViewMode('list')}
            >
              <Icon name="list" size={18} color={viewMode === 'list' ? '#FFFFFF' : (isDark ? '#8E8E93' : '#6B7280')} />
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.toggleButton, viewMode === 'heatmap' && styles.toggleButtonActive]}
              onPress={() => setViewMode('heatmap')}
            >
              <Icon name="grid" size={18} color={viewMode === 'heatmap' ? '#FFFFFF' : (isDark ? '#8E8E93' : '#6B7280')} />
            </TouchableOpacity>
          </View>
        </View>
        {positions.length > 0 && (
          <TouchableOpacity
            style={[styles.positionsButton, isDark && styles.positionsButtonDark]}
            onPress={() => setShowPositions(!showPositions)}
          >
            <Text style={[styles.positionsButtonText, isDark && styles.positionsButtonTextDark]}>
              {showPositions ? 'Hide' : 'Show'} Positions ({positions.length})
            </Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Error/Status Banner */}
      {(error || usingCachedData) && (
        <View style={[
          styles.statusBanner, 
          usingCachedData && styles.cachedBanner,
          isDark && styles.statusBannerDark,
          isDark && usingCachedData && styles.cachedBannerDark
        ]}>
          <Icon 
            name={usingCachedData ? 'wifi-off' : 'alert-circle'} 
            size={16} 
            color={usingCachedData ? '#F59E0B' : '#FF3B30'} 
          />
          <Text style={[styles.statusBannerText, isDark && styles.statusBannerTextDark]}>
            {usingCachedData 
              ? (recommendations.length > 0 
                  ? 'Using cached data. Pull to refresh for latest.' 
                  : 'No connection. Pull to refresh when online.')
              : error}
          </Text>
          {error && !usingCachedData && (
            <TouchableOpacity 
              onPress={handleRefresh}
              style={styles.retryButton}
            >
              <Icon name="refresh-cw" size={14} color={isDark ? '#0A84FF' : '#007AFF'} />
            </TouchableOpacity>
          )}
        </View>
      )}

      {/* Phase 3: Filter and Sort Controls */}
      {viewMode === 'list' && recommendationsWithPrices.length > 0 && (
        <View style={[styles.filterBar, isDark && styles.filterBarDark]}>
          <View style={styles.filterRow}>
            <Text style={[styles.filterLabel, isDark && styles.filterLabelDark]}>Filter:</Text>
            <TouchableOpacity
              style={[styles.filterChip, !filterCategory && styles.filterChipActive]}
              onPress={() => setFilterCategory(null)}
            >
              <Text style={[styles.filterChipText, !filterCategory && styles.filterChipTextActive]}>All</Text>
            </TouchableOpacity>
            {['Equity Index', 'Currency', 'Commodities'].map(cat => (
              <TouchableOpacity
                key={cat}
                style={[styles.filterChip, filterCategory === cat && styles.filterChipActive]}
                onPress={() => setFilterCategory(filterCategory === cat ? null : cat)}
              >
                <Text style={[styles.filterChipText, filterCategory === cat && styles.filterChipTextActive]}>
                  {cat}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
          <View style={styles.filterRow}>
            <Text style={[styles.filterLabel, isDark && styles.filterLabelDark]}>Sort:</Text>
            <TouchableOpacity
              style={[styles.filterChip, sortBy === 'default' && styles.filterChipActive]}
              onPress={() => setSortBy('default')}
            >
              <Text style={[styles.filterChipText, sortBy === 'default' && styles.filterChipTextActive]}>Default</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.filterChip, sortBy === 'price_change' && styles.filterChipActive]}
              onPress={() => setSortBy('price_change')}
            >
              <Text style={[styles.filterChipText, sortBy === 'price_change' && styles.filterChipTextActive]}>Price</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.filterChip, sortBy === 'probability' && styles.filterChipActive]}
              onPress={() => setSortBy('probability')}
            >
              <Text style={[styles.filterChipText, sortBy === 'probability' && styles.filterChipTextActive]}>Prob</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {viewMode === 'heatmap' ? (
        renderHeatmap()
      ) : (
        <FlatList
          data={loading && filteredAndSortedRecommendations.length === 0 ? [] : filteredAndSortedRecommendations}
          renderItem={renderRecommendationCard}
          keyExtractor={(item, index) => item.symbol || index.toString()}
        ListHeaderComponent={
          showPositions && positions.length > 0 ? (
            <View style={styles.positionsSection}>
              <Text style={styles.sectionTitle}>Open Positions</Text>
              {positions.map((pos, idx) => (
                <View key={idx} style={styles.positionCard}>
                  <View style={styles.positionHeader}>
                    <Text style={styles.positionSymbol}>{pos.symbol}</Text>
                    <Text style={[styles.positionPnl, pos.pnl >= 0 ? styles.positive : styles.negative]}>
                      {pos.pnl >= 0 ? '+' : ''}${pos.pnl.toFixed(2)}
                    </Text>
                  </View>
                  <Text style={styles.positionDetails}>
                    {pos.side} {pos.quantity} @ ${pos.entry_price.toFixed(2)} • Now: ${pos.current_price.toFixed(2)}
                  </Text>
                  <Text style={styles.positionPercent}>
                    {pos.pnl_percent >= 0 ? '+' : ''}{pos.pnl_percent.toFixed(2)}%
                  </Text>
                </View>
              ))}
            </View>
          ) : null
        }
        ListEmptyComponent={
          loading ? (
            <View style={styles.center}>
              {Array.from({ length: 3 }).map((_, i) => (
                <React.Fragment key={i}>{renderSkeletonLoader()}</React.Fragment>
              ))}
            </View>
          ) : (
            <View style={styles.center}>
              <Icon name="calendar" size={48} color="#8E8E93" />
              <Text style={styles.emptyText}>No recommendations yet</Text>
              <TouchableOpacity style={styles.refreshButton} onPress={loadRecommendations}>
                <Text style={styles.refreshButtonText}>Refresh</Text>
              </TouchableOpacity>
            </View>
          )
        }
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        removeClippedSubviews
        maxToRenderPerBatch={5}
        windowSize={10}
        initialNumToRender={5}
        getItemLayout={(data, index) => ({
          length: 220, // Approximate card height
          offset: 220 * index,
          index,
        })}
        />
      )}

      {/* Contract Info Modal */}
      <Modal
        visible={showContractInfo}
        transparent
        animationType="slide"
        onRequestClose={() => setShowContractInfo(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, isDark && styles.modalContentDark]}>
            {selectedContract && (() => {
              const specs = getContractSpecs(selectedContract.symbol);
              return (
                <>
                  <View style={styles.modalHeader}>
                    <Text style={[styles.modalTitle, isDark && styles.modalTitleDark]}>
                      {selectedContract.symbol}
                    </Text>
                    <TouchableOpacity
                      onPress={() => setShowContractInfo(false)}
                      style={styles.modalCloseButton}
                    >
                      <Icon name="x" size={24} color={isDark ? '#FFFFFF' : '#000000'} />
                    </TouchableOpacity>
                  </View>
                  
                  <Text style={[styles.modalSubtitle, isDark && styles.modalSubtitleDark]}>
                    {selectedContract.name}
                  </Text>

                  <View style={styles.modalSpecs}>
                    <View style={styles.modalSpecRow}>
                      <Text style={[styles.modalSpecLabel, isDark && styles.modalSpecLabelDark]}>Tick Size</Text>
                      <Text style={[styles.modalSpecValue, isDark && styles.modalSpecValueDark]}>
                        {specs.tickSize}
                      </Text>
                    </View>
                    <View style={styles.modalSpecRow}>
                      <Text style={[styles.modalSpecLabel, isDark && styles.modalSpecLabelDark]}>Tick Value</Text>
                      <Text style={[styles.modalSpecValue, isDark && styles.modalSpecValueDark]}>
                        ${specs.tickValue}
                      </Text>
                    </View>
                    <View style={styles.modalSpecRow}>
                      <Text style={[styles.modalSpecLabel, isDark && styles.modalSpecLabelDark]}>Contract Size</Text>
                      <Text style={[styles.modalSpecValue, isDark && styles.modalSpecValueDark]}>
                        {specs.contractSize.toLocaleString()}
                      </Text>
                    </View>
                    <View style={styles.modalSpecRow}>
                      <Text style={[styles.modalSpecLabel, isDark && styles.modalSpecLabelDark]}>Margin Requirement</Text>
                      <Text style={[styles.modalSpecValue, isDark && styles.modalSpecValueDark]}>
                        ${specs.margin.toLocaleString()}
                      </Text>
                    </View>
                  </View>

                  <View style={styles.modalInfo}>
                    <Text style={[styles.modalInfoTitle, isDark && styles.modalInfoTitleDark]}>
                      What This Means
                    </Text>
                    <Text style={[styles.modalInfoText, isDark && styles.modalInfoTextDark]}>
                      • Tick Size: Minimum price movement{'\n'}
                      • Tick Value: Dollar value per tick{'\n'}
                      • Contract Size: Notional value per contract{'\n'}
                      • Margin: Required capital to trade
                    </Text>
                  </View>

                  <TouchableOpacity
                    style={[styles.modalButton, isDark && styles.modalButtonDark]}
                    onPress={() => {
                      setShowContractInfo(false);
                      handleTrade(selectedContract);
                    }}
                  >
                    <Text style={styles.modalButtonText}>Place Trade</Text>
                  </TouchableOpacity>
                </>
              );
            })()}
          </View>
        </View>
      </Modal>

      {/* Phase 3: Chart Modal */}
      <Modal
        visible={showChartModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowChartModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, styles.chartModalContent, isDark && styles.modalContentDark]}>
            {chartContract && (
              <>
                <View style={styles.modalHeader}>
                  <View style={styles.modalHeaderLeft}>
                    <Text style={[styles.modalTitle, isDark && styles.modalTitleDark]}>
                      {chartContract.symbol}
                    </Text>
                    <Text style={[styles.modalSubtitle, isDark && styles.modalSubtitleDark]}>
                      {chartContract.name}
                    </Text>
                  </View>
                  <TouchableOpacity
                    onPress={() => setShowChartModal(false)}
                    style={styles.modalCloseButton}
                  >
                    <Icon name="x" size={24} color={isDark ? '#FFFFFF' : '#000000'} />
                  </TouchableOpacity>
                </View>

                {/* Price Display */}
                {chartContract.current_price !== undefined && (
                  <View style={styles.chartPriceHeader}>
                    <Text style={[styles.chartPrice, isDark && styles.chartPriceDark]}>
                      ${chartContract.current_price.toFixed(2)}
                    </Text>
                    {chartContract.price_change_percent !== undefined && (
                      <View style={[
                        styles.chartPriceChange,
                        { backgroundColor: (chartContract.price_change_percent >= 0 ? '#34C759' : '#FF3B30') + '15' }
                      ]}>
                        <Icon 
                          name={chartContract.price_change_percent >= 0 ? 'arrow-up' : 'arrow-down'} 
                          size={14} 
                          color={chartContract.price_change_percent >= 0 ? '#34C759' : '#FF3B30'} 
                        />
                        <Text style={[
                          styles.chartPriceChangeText,
                          { color: chartContract.price_change_percent >= 0 ? '#34C759' : '#FF3B30' }
                        ]}>
                          {chartContract.price_change_percent >= 0 ? '+' : ''}
                          {chartContract.price_change_percent.toFixed(2)}%
                        </Text>
                      </View>
                    )}
                  </View>
                )}

                {/* Chart */}
                <View style={styles.chartContainer}>
                  {chartContract.price_history && chartContract.price_history.length > 0 ? (
                    <View style={styles.chartWrapper}>
                      <SparkMini
                        data={chartContract.price_history}
                        width={320}
                        height={180}
                        upColor="#34C759"
                        downColor="#FF3B30"
                      />
                    </View>
                  ) : (
                    <View style={styles.chartPlaceholder}>
                      <Icon name="trending-up" size={48} color="#8E8E93" />
                      <Text style={[styles.chartPlaceholderText, isDark && styles.chartPlaceholderTextDark]}>
                        Chart data loading...
                      </Text>
                    </View>
                  )}
                </View>

                {/* Quick Actions */}
                <View style={styles.chartActions}>
                  <TouchableOpacity
                    style={[styles.chartActionButton, isDark && styles.chartActionButtonDark]}
                    onPress={() => {
                      setShowChartModal(false);
                      handleTrade(chartContract);
                    }}
                  >
                    <Icon name="arrow-right-circle" size={20} color={isDark ? '#0A84FF' : '#007AFF'} />
                    <Text style={[styles.chartActionText, isDark && styles.chartActionTextDark]}>Trade</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.chartActionButton, isDark && styles.chartActionButtonDark]}
                    onPress={() => {
                      setShowChartModal(false);
                      setSelectedContract(chartContract);
                      setShowContractInfo(true);
                    }}
                  >
                    <Icon name="info" size={20} color={isDark ? '#0A84FF' : '#007AFF'} />
                    <Text style={[styles.chartActionText, isDark && styles.chartActionTextDark]}>Details</Text>
                  </TouchableOpacity>
                </View>
                {/* Phase 3: Additional Quick Actions */}
                <View style={styles.chartActionsSecondary}>
                  <TouchableOpacity
                    style={[styles.chartActionButtonSecondary, isDark && styles.chartActionButtonSecondaryDark]}
                    onPress={() => {
                      if (chartContract) {
                        handleAddToWatchlist(chartContract);
                      }
                    }}
                  >
                    <Icon name="bookmark" size={18} color={isDark ? '#8E8E93' : '#6B7280'} />
                    <Text style={[styles.chartActionTextSecondary, isDark && styles.chartActionTextSecondaryDark]}>Watchlist</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.chartActionButtonSecondary, isDark && styles.chartActionButtonSecondaryDark]}
                    onPress={() => {
                      if (chartContract) {
                        handleShare(chartContract);
                      }
                    }}
                  >
                    <Icon name="share-2" size={18} color={isDark ? '#8E8E93' : '#6B7280'} />
                    <Text style={[styles.chartActionTextSecondary, isDark && styles.chartActionTextSecondaryDark]}>Share</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.chartActionButtonSecondary, isDark && styles.chartActionButtonSecondaryDark]}
                    onPress={() => {
                      if (chartContract) {
                        handleToggleComparison(chartContract);
                        setShowChartModal(false);
                      }
                    }}
                  >
                    <Icon name="layers" size={18} color={isDark ? '#8E8E93' : '#6B7280'} />
                    <Text style={[styles.chartActionTextSecondary, isDark && styles.chartActionTextSecondaryDark]}>Compare</Text>
                  </TouchableOpacity>
                </View>
              </>
            )}
          </View>
        </View>
      </Modal>

      {/* Phase 3: Comparison Modal */}
      <Modal
        visible={showComparisonModal}
        transparent
        animationType="slide"
        onRequestClose={() => {
          setShowComparisonModal(false);
          setComparisonContracts([]);
        }}
      >
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, styles.comparisonModalContent, isDark && styles.modalContentDark]}>
            <View style={styles.modalHeader}>
              <View style={styles.modalHeaderLeft}>
                <Text style={[styles.modalTitle, isDark && styles.modalTitleDark]}>
                  Compare Contracts
                </Text>
                <Text style={[styles.modalSubtitle, isDark && styles.modalSubtitleDark]}>
                  {comparisonContracts.length} of 3 selected
                </Text>
              </View>
              <TouchableOpacity
                onPress={() => {
                  setShowComparisonModal(false);
                  setComparisonContracts([]);
                }}
                style={styles.modalCloseButton}
              >
                <Icon name="x" size={24} color={isDark ? '#FFFFFF' : '#000000'} />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.comparisonScrollView} showsVerticalScrollIndicator={false}>
              {comparisonContracts.map((rec, index) => {
                const hasPrice = rec.current_price !== undefined;
                const change = rec.price_change || 0;
                const changePercent = rec.price_change_percent || 0;
                const isPositive = change >= 0;
                const priceColor = isPositive ? '#34C759' : '#FF3B30';

                return (
                  <View key={rec.symbol} style={[styles.comparisonCard, isDark && styles.comparisonCardDark]}>
                    <View style={styles.comparisonCardHeader}>
                      <View style={styles.comparisonCardHeaderLeft}>
                        <Text style={[styles.comparisonSymbol, isDark && styles.comparisonSymbolDark]}>
                          {rec.symbol}
                        </Text>
                        <Text style={[styles.comparisonName, isDark && styles.comparisonNameDark]}>
                          {rec.name}
                        </Text>
                      </View>
                      <TouchableOpacity
                        onPress={() => handleToggleComparison(rec)}
                        style={styles.comparisonRemoveButton}
                      >
                        <Icon name="x" size={16} color={isDark ? '#8E8E93' : '#6B7280'} />
                      </TouchableOpacity>
                    </View>

                    {hasPrice && (
                      <View style={styles.comparisonPriceRow}>
                        <Text style={[styles.comparisonPrice, isDark && styles.comparisonPriceDark]}>
                          ${rec.current_price.toFixed(2)}
                        </Text>
                        <View style={[styles.comparisonPriceChange, { backgroundColor: priceColor + '15' }]}>
                          <Icon 
                            name={isPositive ? 'arrow-up' : 'arrow-down'} 
                            size={12} 
                            color={priceColor} 
                          />
                          <Text style={[styles.comparisonPriceChangeText, { color: priceColor }]}>
                            {isPositive ? '+' : ''}{changePercent.toFixed(2)}%
                          </Text>
                        </View>
                      </View>
                    )}

                    <View style={styles.comparisonMetrics}>
                      <View style={styles.comparisonMetric}>
                        <Text style={[styles.comparisonMetricLabel, isDark && styles.comparisonMetricLabelDark]}>
                          Max Loss
                        </Text>
                        <Text style={[styles.comparisonMetricValue, isDark && styles.comparisonMetricValueDark]}>
                          ${rec.max_loss}
                        </Text>
                      </View>
                      <View style={styles.comparisonMetric}>
                        <Text style={[styles.comparisonMetricLabel, isDark && styles.comparisonMetricLabelDark]}>
                          Max Gain
                        </Text>
                        <Text style={[styles.comparisonMetricValue, styles.comparisonMetricValuePositive, isDark && styles.comparisonMetricValueDark]}>
                          ${rec.max_gain}
                        </Text>
                      </View>
                      <View style={styles.comparisonMetric}>
                        <Text style={[styles.comparisonMetricLabel, isDark && styles.comparisonMetricLabelDark]}>
                          Probability
                        </Text>
                        <Text style={[styles.comparisonMetricValue, isDark && styles.comparisonMetricValueDark]}>
                          {rec.probability}%
                        </Text>
                      </View>
                    </View>

                    <View style={styles.comparisonActionRow}>
                      <Text style={[styles.comparisonAction, isDark && styles.comparisonActionDark]}>
                        {rec.action}
                      </Text>
                      <TouchableOpacity
                        style={[styles.comparisonTradeButton, isDark && styles.comparisonTradeButtonDark]}
                        onPress={() => {
                          setShowComparisonModal(false);
                          handleTrade(rec);
                        }}
                      >
                        <Text style={styles.comparisonTradeButtonText}>Trade</Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                );
              })}
            </ScrollView>

            {comparisonContracts.length < 3 && (
              <View style={styles.comparisonHint}>
                <Text style={[styles.comparisonHintText, isDark && styles.comparisonHintTextDark]}>
                  Tap "Compare" on other contracts to add them here
                </Text>
              </View>
            )}
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  header: {
    padding: 20,
    backgroundColor: 'white',
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#E5E5EA',
  },
  headerTitle: {
    fontSize: 34,
    fontWeight: '700',
    color: '#000',
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 17,
    color: '#8E8E93',
  },
  content: {
    flex: 1,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 17,
    color: '#8E8E93',
  },
  emptyText: {
    marginTop: 16,
    fontSize: 17,
    color: '#8E8E93',
    textAlign: 'center',
  },
  refreshButton: {
    marginTop: 20,
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: '#007AFF',
    borderRadius: 8,
  },
  refreshButtonText: {
    color: 'white',
    fontSize: 17,
    fontWeight: '600',
  },
  card: {
    backgroundColor: 'white',
    margin: 16,
    marginBottom: 0,
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  cardSymbol: {
    fontSize: 24,
    fontWeight: '700',
    color: '#000',
  },
  cardName: {
    fontSize: 15,
    color: '#8E8E93',
    marginTop: 2,
  },
  cardWhy: {
    fontSize: 17,
    color: '#000',
    marginVertical: 12,
    lineHeight: 24,
  },
  // Session Indicator Styles
  sessionIndicator: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    padding: 8,
    borderRadius: 6,
    marginBottom: 12,
    gap: 8,
    flexWrap: 'wrap',
  },
  sessionBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    flexShrink: 0,
  },
  sessionBadgeText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  sessionLabel: {
    fontSize: 12,
    color: '#6B7280',
    fontWeight: '500',
    flexShrink: 1,
    flex: 1,
    minWidth: 0,
  },
  // Why Now Bullet Points Styles
  whyNowContainer: {
    marginVertical: 12,
  },
  whyNowTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#000',
    marginBottom: 8,
  },
  whyNowBullet: {
    marginBottom: 6,
  },
  whyNowBulletText: {
    fontSize: 15,
    color: '#374151',
    lineHeight: 22,
  },
  cardMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginVertical: 16,
    paddingTop: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: '#E5E5EA',
  },
  cardMetric: {
    alignItems: 'center',
  },
  cardMetricLabel: {
    fontSize: 13,
    color: '#8E8E93',
    marginBottom: 4,
  },
  cardMetricValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#000',
  },
  positive: {
    color: '#34C759',
  },
  cardAction: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 8,
    paddingTop: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: '#E5E5EA',
  },
  cardActionText: {
    fontSize: 17,
    fontWeight: '600',
    color: '#007AFF',
  },
  positionsButton: {
    marginTop: 12,
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: '#007AFF',
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  positionsButtonText: {
    color: 'white',
    fontSize: 15,
    fontWeight: '600',
  },
  positionsSection: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#000',
    marginBottom: 12,
  },
  positionCard: {
    backgroundColor: 'white',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  positionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  positionSymbol: {
    fontSize: 20,
    fontWeight: '700',
    color: '#000',
  },
  positionPnl: {
    fontSize: 20,
    fontWeight: '700',
  },
  positionDetails: {
    fontSize: 15,
    color: '#8E8E93',
    marginBottom: 4,
  },
  positionPercent: {
    fontSize: 16,
    fontWeight: '600',
    color: '#8E8E93',
  },
  negative: {
    color: '#FF3B30',
  },
  // New styles for Phase 1 improvements
  statusBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#FEF2F2',
    borderBottomWidth: 1,
    borderBottomColor: '#FEE2E2',
    gap: 8,
  },
  cachedBanner: {
    backgroundColor: '#FFFBEB',
    borderBottomColor: '#FEF3C7',
  },
  statusBannerText: {
    fontSize: 14,
    color: '#991B1B',
    flex: 1,
  },
  retryButton: {
    padding: 4,
    marginLeft: 8,
  },
  listContent: {
    paddingBottom: 20,
  },
  cardHeaderLeft: {
    flex: 1,
  },
  cardPriceContainer: {
    alignItems: 'flex-end',
  },
  cardPrice: {
    fontSize: 20,
    fontWeight: '700',
    color: '#000',
    marginBottom: 4,
  },
  priceChangeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    gap: 4,
  },
  priceChange: {
    fontSize: 12,
    fontWeight: '600',
  },
  sparklineContainer: {
    marginVertical: 12,
    alignItems: 'flex-start',
  },
  skeletonCard: {
    backgroundColor: 'white',
    margin: 16,
    marginBottom: 0,
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  skeletonHeader: {
    marginBottom: 8,
  },
  skeletonBox: {
    backgroundColor: '#E5E7EB',
    borderRadius: 4,
  },
  skeletonMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: '#E5E5EA',
  },
  // Dark Mode Styles
  containerDark: {
    backgroundColor: '#000000',
  },
  headerDark: {
    backgroundColor: '#1C1C1E',
    borderBottomColor: '#38383A',
  },
  headerTitleDark: {
    color: '#FFFFFF',
  },
  headerSubtitleDark: {
    color: '#8E8E93',
  },
  statusBannerDark: {
    backgroundColor: '#2C1F1F',
    borderBottomColor: '#3C2F2F',
  },
  cachedBannerDark: {
    backgroundColor: '#2C241F',
    borderBottomColor: '#3C342F',
  },
  statusBannerTextDark: {
    color: '#FF6B6B',
  },
  positionsButtonDark: {
    backgroundColor: '#0A84FF',
  },
  positionsButtonTextDark: {
    color: '#FFFFFF',
  },
  cardDark: {
    backgroundColor: '#1C1C1E',
    shadowColor: '#000000',
  },
  cardSymbolDark: {
    color: '#FFFFFF',
  },
  cardNameDark: {
    color: '#8E8E93',
  },
  cardPriceDark: {
    color: '#FFFFFF',
  },
  sessionLabelDark: {
    color: '#A1A1AA',
  },
  whyNowTitleDark: {
    color: '#FFFFFF',
  },
  whyNowBulletTextDark: {
    color: '#E5E5EA',
  },
  cardMetricLabelDark: {
    color: '#8E8E93',
  },
  cardMetricValueDark: {
    color: '#FFFFFF',
  },
  cardActionTextDark: {
    color: '#0A84FF',
  },
  // Header Layout Styles
  headerTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  headerLeft: {
    flex: 1,
  },
  viewToggle: {
    flexDirection: 'row',
    backgroundColor: '#F2F2F7',
    borderRadius: 8,
    padding: 2,
    gap: 2,
  },
  toggleButton: {
    padding: 8,
    borderRadius: 6,
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: 36,
  },
  toggleButtonActive: {
    backgroundColor: '#007AFF',
  },
  // Session Indicator Updates
  sessionIndicatorLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    flex: 1,
    minWidth: 0,
    flexShrink: 1,
  },
  badgesContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    flexWrap: 'wrap',
    justifyContent: 'flex-end',
    flexShrink: 0,
    marginLeft: 8,
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 5,
    paddingVertical: 2,
    borderRadius: 4,
    gap: 3,
    minHeight: 18,
  },
  topMoverBadge: {
    backgroundColor: '#FF6B35',
  },
  badgeText: {
    color: '#FFFFFF',
    fontSize: 9,
    fontWeight: '700',
    lineHeight: 11,
  },
  heatmapBadge: {
    paddingHorizontal: 4,
    paddingVertical: 2,
  },
  // Heatmap Styles
  heatmapContainer: {
    flex: 1,
  },
  heatmapContent: {
    padding: 16,
    paddingBottom: 40,
  },
  heatmapCategory: {
    marginBottom: 24,
  },
  heatmapCategoryTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#000',
    marginBottom: 12,
  },
  heatmapGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  heatmapCell: {
    width: '47%', // 2 columns with gap
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  heatmapCellHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  heatmapBadges: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  heatmapInfoButton: {
    padding: 2,
    marginLeft: 2,
  },
  heatmapSymbol: {
    fontSize: 16,
    fontWeight: '700',
    color: '#000',
  },
  heatmapName: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 8,
  },
  heatmapPrice: {
    marginBottom: 8,
  },
  heatmapPriceValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#000',
    marginBottom: 2,
  },
  heatmapPriceChange: {
    fontSize: 12,
    fontWeight: '600',
  },
  heatmapMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 4,
  },
  heatmapMetric: {
    fontSize: 11,
    color: '#6B7280',
  },
  heatmapAction: {
    fontSize: 12,
    fontWeight: '700',
  },
  // Dark Mode Heatmap Styles
  heatmapCellDark: {
    backgroundColor: '#1C1C1E',
    borderColor: '#38383A',
  },
  heatmapSymbolDark: {
    color: '#FFFFFF',
  },
  heatmapNameDark: {
    color: '#8E8E93',
  },
  heatmapPriceValueDark: {
    color: '#FFFFFF',
  },
  heatmapMetricDark: {
    color: '#8E8E93',
  },
  heatmapCategoryTitleDark: {
    color: '#FFFFFF',
  },
  emptyTextDark: {
    color: '#8E8E93',
  },
  // Badge Styles
  unusualVolumeBadge: {
    backgroundColor: '#8B5CF6',
  },
  infoButton: {
    padding: 4,
    marginLeft: 4,
  },
  // Modal Styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 24,
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  modalTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#000000',
  },
  modalCloseButton: {
    padding: 4,
  },
  modalSubtitle: {
    fontSize: 17,
    color: '#6B7280',
    marginBottom: 24,
  },
  modalSpecs: {
    marginBottom: 24,
  },
  modalSpecRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#E5E7EB',
  },
  modalSpecLabel: {
    fontSize: 16,
    color: '#6B7280',
  },
  modalSpecValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#000000',
  },
  modalInfo: {
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
  },
  modalInfoTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#000000',
    marginBottom: 8,
  },
  modalInfoText: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
  },
  modalButton: {
    backgroundColor: '#007AFF',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  modalButtonText: {
    color: '#FFFFFF',
    fontSize: 17,
    fontWeight: '700',
  },
  // Dark Mode Modal Styles
  modalContentDark: {
    backgroundColor: '#1C1C1E',
  },
  modalTitleDark: {
    color: '#FFFFFF',
  },
  modalSubtitleDark: {
    color: '#8E8E93',
  },
  modalSpecLabelDark: {
    color: '#8E8E93',
  },
  modalSpecValueDark: {
    color: '#FFFFFF',
  },
  modalInfoTitleDark: {
    color: '#FFFFFF',
  },
  modalInfoTextDark: {
    color: '#8E8E93',
  },
  modalButtonDark: {
    backgroundColor: '#0A84FF',
  },
  // Phase 3: Filter Bar Styles
  filterBar: {
    backgroundColor: '#FFFFFF',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#E5E5EA',
  },
  filterRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    flexWrap: 'wrap',
    gap: 8,
  },
  filterLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#6B7280',
    marginRight: 4,
  },
  filterChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#F2F2F7',
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  filterChipActive: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  filterChipText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6B7280',
  },
  filterChipTextActive: {
    color: '#FFFFFF',
  },
  // Phase 3: Chart Modal Styles
  chartModalContent: {
    maxHeight: '85%',
  },
  modalHeaderLeft: {
    flex: 1,
  },
  chartPriceHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 20,
    paddingBottom: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#E5E5EA',
  },
  chartPrice: {
    fontSize: 32,
    fontWeight: '700',
    color: '#000000',
  },
  chartPriceChange: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    gap: 6,
  },
  chartPriceChangeText: {
    fontSize: 16,
    fontWeight: '700',
  },
  chartContainer: {
    height: 220,
    marginBottom: 24,
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    overflow: 'hidden',
  },
  chartWrapper: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
  },
  chartPlaceholder: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  chartPlaceholderText: {
    marginTop: 12,
    fontSize: 14,
    color: '#6B7280',
  },
  chartActions: {
    flexDirection: 'row',
    gap: 12,
  },
  chartActionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 12,
    backgroundColor: '#F2F2F7',
    gap: 8,
  },
  chartActionText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
  },
  // Dark Mode Filter & Chart Styles
  filterBarDark: {
    backgroundColor: '#1C1C1E',
    borderBottomColor: '#38383A',
  },
  filterLabelDark: {
    color: '#8E8E93',
  },
  filterChipDark: {
    backgroundColor: '#2C2C2E',
    borderColor: '#38383A',
  },
  chartPriceDark: {
    color: '#FFFFFF',
  },
  chartPlaceholderTextDark: {
    color: '#8E8E93',
  },
  chartActionButtonDark: {
    backgroundColor: '#2C2C2E',
  },
  chartActionTextDark: {
    color: '#0A84FF',
  },
  // Phase 3: Secondary Chart Actions
  chartActionsSecondary: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 8,
  },
  chartActionButtonSecondary: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 12,
    borderRadius: 10,
    backgroundColor: '#F2F2F7',
    gap: 6,
  },
  chartActionButtonSecondaryDark: {
    backgroundColor: '#2C2C2E',
  },
  chartActionTextSecondary: {
    fontSize: 13,
    fontWeight: '600',
    color: '#6B7280',
  },
  chartActionTextSecondaryDark: {
    color: '#8E8E93',
  },
  // Phase 3: Comparison Toggle Button
  comparisonToggleButton: {
    padding: 4,
    marginLeft: 4,
    borderRadius: 4,
    backgroundColor: 'transparent',
  },
  comparisonToggleButtonActive: {
    backgroundColor: '#007AFF',
  },
  // Phase 3: Comparison Modal Styles
  comparisonModalContent: {
    maxHeight: '90%',
  },
  comparisonScrollView: {
    maxHeight: 500,
  },
  comparisonCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  comparisonCardDark: {
    backgroundColor: '#2C2C2E',
    borderColor: '#38383A',
  },
  comparisonCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  comparisonCardHeaderLeft: {
    flex: 1,
  },
  comparisonSymbol: {
    fontSize: 20,
    fontWeight: '700',
    color: '#000000',
    marginBottom: 4,
  },
  comparisonSymbolDark: {
    color: '#FFFFFF',
  },
  comparisonName: {
    fontSize: 14,
    color: '#6B7280',
  },
  comparisonNameDark: {
    color: '#8E8E93',
  },
  comparisonRemoveButton: {
    padding: 4,
  },
  comparisonPriceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  comparisonPrice: {
    fontSize: 24,
    fontWeight: '700',
    color: '#000000',
  },
  comparisonPriceDark: {
    color: '#FFFFFF',
  },
  comparisonPriceChange: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    gap: 4,
  },
  comparisonPriceChangeText: {
    fontSize: 14,
    fontWeight: '700',
  },
  comparisonMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 16,
    paddingTop: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: '#E5E5EA',
  },
  comparisonMetric: {
    alignItems: 'center',
  },
  comparisonMetricLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  comparisonMetricLabelDark: {
    color: '#8E8E93',
  },
  comparisonMetricValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#000000',
  },
  comparisonMetricValuePositive: {
    color: '#34C759',
  },
  comparisonMetricValueDark: {
    color: '#FFFFFF',
  },
  comparisonActionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: '#E5E5EA',
  },
  comparisonAction: {
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
  },
  comparisonActionDark: {
    color: '#0A84FF',
  },
  comparisonTradeButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: '#007AFF',
  },
  comparisonTradeButtonDark: {
    backgroundColor: '#0A84FF',
  },
  comparisonTradeButtonText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  comparisonHint: {
    padding: 16,
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
    marginTop: 12,
  },
  comparisonHintDark: {
    backgroundColor: '#2C2C2E',
  },
  comparisonHintText: {
    fontSize: 13,
    color: '#6B7280',
    textAlign: 'center',
  },
  comparisonHintTextDark: {
    color: '#8E8E93',
  },
});

