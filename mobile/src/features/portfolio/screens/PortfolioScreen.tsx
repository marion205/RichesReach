import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import {
View,
Text,
StyleSheet,
ScrollView,
RefreshControl,
Alert,
TouchableOpacity,
DeviceEventEmitter,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useQuery } from '@apollo/client';
import { gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import { SecureMarketDataService } from '../../stocks/services/SecureMarketDataService';
import { GET_MY_PORTFOLIOS } from '../../../portfolioQueries';
import MilestonesTimeline, { Milestone } from '../../../components/MilestonesTimeline';
import MilestoneUnlockOverlay from '../../../components/MilestoneUnlockOverlay';
import { useNavigation } from '@react-navigation/native';
import PortfolioHoldings, { Holding } from '../components/PortfolioHoldings';
import { getMockMyPortfolios } from '../../../services/mockPortfolioData';
import ConstellationOrb from '../components/ConstellationOrb';
import { useMoneySnapshot } from '../hooks/useMoneySnapshot';
import LifeEventPetalsModal from '../components/LifeEventPetalsModal';
import MarketCrashShieldView from '../components/MarketCrashShieldView';
import GrowthProjectionView from '../components/GrowthProjectionView';
import WhatIfSimulator from '../components/WhatIfSimulator';
import QuickActionsModal from '../components/QuickActionsModal';
import DetailedBreakdownModal from '../components/DetailedBreakdownModal';
import logger from '../../../utils/logger';
import { SharedOrb } from '../../family/components/SharedOrb';
import { FamilyManagementModal } from '../../family/components/FamilyManagementModal';
import { familySharingService, FamilyGroup, FamilyMember } from '../../family/services/FamilySharingService';
import { DawnRitualScreen } from '../../rituals/screens/DawnRitualScreen';
import { CreditQuestScreen } from '../../credit/screens/CreditQuestScreen';
interface PortfolioScreenProps {
navigateTo?: (screen: string) => void;
}
interface NavigationParams {
  screen?: string;
  params?: Record<string, unknown>;
  [key: string]: unknown;
}

interface PortfolioHolding {
  symbol?: string;
  stock?: {
    symbol?: string;
    companyName?: string;
    name?: string;
    currentPrice?: number;
    averagePrice?: number;
  };
  shares?: number;
  quantity?: number;
  currentPrice?: number;
  totalValue?: number;
  averagePrice?: number;
  name?: string;
  [key: string]: unknown;
}

interface Portfolio {
  name: string;
  totalValue?: number;
  holdingsCount?: number;
  holdings?: PortfolioHolding[];
  [key: string]: unknown;
}

interface StablePortfolioData {
  name: string;
  holdings: Array<{
    symbol?: string;
    shares?: number;
  }>;
}

const PortfolioScreen: React.FC<PortfolioScreenProps> = ({ navigateTo }) => {
const insets = useSafeAreaInsets();
  const navigation = useNavigation();
  
  // ALL HOOKS MUST BE AT THE TOP - before any conditional returns
  const [refreshing, setRefreshing] = useState(false);
  const [realTimePrices, setRealTimePrices] = useState<{ [key: string]: number }>({});
  const [loadingPrices, setLoadingPrices] = useState(false);
  const [celebrateTitle, setCelebrateTitle] = useState<string | null>(null);
  
  // Modal visibility states for gesture actions
  const [showLifeEvents, setShowLifeEvents] = useState(false);
  const [showShield, setShowShield] = useState(false);
  const [showGrowth, setShowGrowth] = useState(false);
  const [showWhatIf, setShowWhatIf] = useState(false);
  const [showQuickActions, setShowQuickActions] = useState(false);
  const [showBreakdown, setShowBreakdown] = useState(false);
  
  // Family sharing state
  const [familyGroup, setFamilyGroup] = useState<FamilyGroup | null>(null);
  const [showFamilyManagement, setShowFamilyManagement] = useState(false);
  const [currentUser, setCurrentUser] = useState<FamilyMember | null>(null);
  const [loadingFamily, setLoadingFamily] = useState(false);
  
  // Dawn Ritual state
  const [showDawnRitual, setShowDawnRitual] = useState(false);
  
  // Credit Quest state
  const [showCreditQuest, setShowCreditQuest] = useState(false);
  
  const { data: portfolioData, loading: portfolioLoading, error: portfolioError, refetch } = useQuery(GET_MY_PORTFOLIOS, {
    errorPolicy: 'all', // Continue even if there are errors
    fetchPolicy: 'cache-and-network', // Use cache but also fetch fresh data
    notifyOnNetworkStatusChange: true,
  });

  // Money snapshot hook (for Constellation Orb)
  const { snapshot, loading: snapshotLoading, hasBankLinked, refetch: refetchSnapshot, error: snapshotError } = useMoneySnapshot();
  
  // Ensure all modals are closed when screen mounts (prevent blocking overlays)
  useEffect(() => {
    logger.log('[PortfolioScreen] Screen mounted, ensuring all modals are closed');
    setShowLifeEvents(false);
    setShowShield(false);
    setShowGrowth(false);
    setShowWhatIf(false);
    setShowQuickActions(false);
    setShowBreakdown(false);
    setShowFamilyManagement(false);
    setShowDawnRitual(false);
    setShowCreditQuest(false);
    setCelebrateTitle(null);
  }, []); // Only run on mount
  
  // Load family group on mount - memoized to prevent recreation
  const loadFamilyGroup = useCallback(async () => {
    try {
      setLoadingFamily(true);
      const group = await familySharingService.getFamilyGroup();
      setFamilyGroup(group);
      
      // Find current user in family group
      if (group) {
        // In a real app, get current user ID from auth context
        // For now, assume first member or owner is current user
        const user = group.members.find(m => m.role === 'owner') || group.members[0];
        setCurrentUser(user || null);
      }
    } catch (error) {
      logger.error('[PortfolioScreen] Failed to load family group:', error);
      setFamilyGroup(null);
    } finally {
      setLoadingFamily(false);
    }
  }, []);

  useEffect(() => {
    loadFamilyGroup();
  }, [loadFamilyGroup]);

  // Listen for Dawn Ritual notification
  useEffect(() => {
    const subscription = DeviceEventEmitter.addListener('openDawnRitual', () => {
      setShowDawnRitual(true);
    });
    return () => subscription.remove();
  }, []);
  
  // Debug logging - debounced to prevent excessive logging
  useEffect(() => {
    if (__DEV__) {
      // Use timeout to debounce logging and prevent blocking
      const timeoutId = setTimeout(() => {
        logger.log('[PortfolioScreen] Constellation Orb Debug:', {
          hasBankLinked,
          hasSnapshot: !!snapshot,
          snapshotLoading,
          snapshotError: snapshotError?.message,
          bankAccountsCount: snapshot?.breakdown?.bankAccountsCount,
          willShowOrb: hasBankLinked && !!snapshot,
          hasFamilyGroup: !!familyGroup,
          familyMembers: familyGroup?.members.length || 0,
        });
      }, 500); // Debounce by 500ms
      
      return () => clearTimeout(timeoutId);
    }
  }, [hasBankLinked, snapshot, snapshotLoading, snapshotError, familyGroup]);
  
  // Timeout handling: Stop loading after 3 seconds and use mock data
  const [portfolioLoadingTimeout, setPortfolioLoadingTimeout] = useState(false);
  
  useEffect(() => {
    if (portfolioLoading) {
      const timer = setTimeout(() => {
        logger.log('[PortfolioScreen] Portfolio loading timeout - using fallback');
        setPortfolioLoadingTimeout(true);
      }, 3000); // 3 second timeout
      return () => clearTimeout(timer);
    } else {
      setPortfolioLoadingTimeout(false);
    }
  }, [portfolioLoading]);
  
  const go = useCallback((name: string, params?: NavigationParams) => {
    logger.log('PortfolioScreen: Navigating to', name, params);
    
    // Map screen names to their correct navigation names
    const screenNameMap: Record<string, string> = {
      'ai-portfolio': 'AIPortfolio', // Map to the correct React Navigation screen name
      'ai-recommendations': 'AIPortfolio', // Also support this alias
      'portfolio-management': 'PortfolioManagement',
      'premium-analytics': 'premium-analytics',
      'trading': 'trading',
      'stock': 'Stocks', // Map to Stocks screen name
      'StockDetail': 'StockDetail',
    };
    
    const mappedName = screenNameMap[name] || name;
    
    try {
      if (navigation && 'navigate' in navigation && typeof navigation.navigate === 'function') {
        logger.log('PortfolioScreen: Using navigation.navigate with mapped name:', mappedName);
        // For screens in the same stack (InvestStack), navigate directly
        navigation.navigate(mappedName as never, params as never);
        return;
      }
    } catch (error) {
      logger.error('PortfolioScreen: Navigation error', error);
      // Try alternative navigation approach
      try {
        // If direct navigation fails, try nested navigation for InvestStack screens
        const investStackScreens = ['premium-analytics', 'PortfolioManagement', 'trading', 'Stocks', 'StockDetail', 'AIPortfolio'];
        if (investStackScreens.includes(mappedName) && 'navigate' in navigation && typeof navigation.navigate === 'function') {
          logger.log('PortfolioScreen: Trying nested navigation to Invest stack');
          navigation.navigate('Invest' as never, {
            screen: mappedName,
            params: params
          } as never);
          return;
        }
      } catch (nestedError) {
        logger.error('PortfolioScreen: Nested navigation error', nestedError);
      }
    }
    logger.log('PortfolioScreen: Using navigateTo fallback');
    if (navigateTo) {
      navigateTo(name, params);
    } else {
      logger.warn('PortfolioScreen: No navigation method available');
    }
  }, [navigation, navigateTo]);
// Ref to track if we're currently fetching prices to prevent concurrent calls
const fetchingPricesRef = useRef(false);

// Fetch real-time prices for portfolio holdings - memoized to prevent recreation
interface HoldingForPrice {
  symbol?: string;
  stock?: { symbol?: string };
  [key: string]: unknown;
}
const fetchRealTimePrices = useCallback(async (holdings: HoldingForPrice[]) => {
  if (holdings.length === 0) {
    setLoadingPrices(false);
    fetchingPricesRef.current = false;
    return;
  }
  // Prevent concurrent calls
  if (fetchingPricesRef.current) {
    return;
  }
  fetchingPricesRef.current = true;
  setLoadingPrices(true);
  try {
    const symbols = holdings.map(holding => holding.stock?.symbol || holding.symbol).filter(Boolean);
    if (symbols.length === 0) {
      setLoadingPrices(false);
      fetchingPricesRef.current = false;
      return;
    }
    const service = SecureMarketDataService.getInstance();
    const quotes = await service.fetchQuotes(symbols);
    const prices: { [key: string]: number } = {};
    quotes.forEach((quote) => {
      if (quote.price > 0) {
        prices[quote.symbol] = quote.price;
      }
    });
    setRealTimePrices(prices);
  } catch (error) {
    logger.error('Failed to fetch real-time prices for portfolio:', error);
    // Use prices from mock portfolio data as fallback
    const mockPrices: { [key: string]: number } = {};
    interface HoldingWithPrice {
      symbol?: string;
      stock?: { symbol?: string };
      [key: string]: unknown;
    }
    holdings.forEach((holding: HoldingWithPrice) => {
      const symbol = holding.stock?.symbol || holding.symbol;
      const price = holding.currentPrice || holding.stock?.currentPrice || 0;
      if (symbol && price > 0) {
        mockPrices[symbol] = price;
      }
    });
    setRealTimePrices(mockPrices);
  } finally {
    setLoadingPrices(false);
    fetchingPricesRef.current = false;
  }
}, []);

// Extract stable reference to portfolios to prevent infinite loops
const portfoliosRef = useRef<string>('');
// Create a stable string representation that only changes when actual data changes
// The ref comparison in useEffect will prevent unnecessary fetches even if this recalculates
const portfoliosDataString = useMemo(() => {
  if (!portfolioData?.myPortfolios?.portfolios) {
    return '';
  }
  try {
    // Create a stable string representation of the portfolios data
    // Only include fields that matter for price fetching to minimize recalculation overhead
    const stableData = portfolioData.myPortfolios.portfolios.map((p: Portfolio): StablePortfolioData => ({
      name: p.name,
      holdings: (p.holdings || []).map((h: PortfolioHolding) => ({
        symbol: h.stock?.symbol || h.symbol,
        shares: h.shares || h.quantity,
      })),
    }));
    return JSON.stringify(stableData);
  } catch (error) {
    logger.error('[PortfolioScreen] Error creating stable portfolio string:', error);
    return '';
  }
  // Note: We depend on the array reference, but the ref comparison in useEffect
  // will prevent infinite loops by only fetching when the actual data changes
}, [portfolioData?.myPortfolios?.portfolios]);

// Fetch real-time prices when portfolio data changes - using stable reference
useEffect(() => {
  // Only fetch if the data actually changed
  if (portfoliosDataString !== portfoliosRef.current) {
    portfoliosRef.current = portfoliosDataString;
    
    // Use a timeout to debounce and prevent blocking the main thread
    const timeoutId = setTimeout(() => {
      if (portfolioData?.myPortfolios?.portfolios) {
        const allHoldings = portfolioData.myPortfolios.portfolios.flatMap((p: Portfolio) => p.holdings || []);
        if (allHoldings.length > 0) {
          // Fetch prices asynchronously to avoid blocking
          fetchRealTimePrices(allHoldings).catch((error) => {
            logger.error('[PortfolioScreen] Error fetching prices:', error);
            setLoadingPrices(false);
          });
        } else {
          // No holdings, ensure loading is false
          setLoadingPrices(false);
        }
      } else {
        // No portfolio data yet, but don't block rendering
        setLoadingPrices(false);
      }
    }, 100); // Small delay to prevent blocking initial render
    
    return () => clearTimeout(timeoutId);
  }
  // Only depend on portfoliosDataString - fetchRealTimePrices is stable (empty deps)
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, [portfoliosDataString]);
  const onRefresh = async () => {
setRefreshing(true);
try {
await Promise.all([
  refetch(),
  refetchSnapshot(), // Also refresh money snapshot
]);
} catch (error) {
// Error refreshing portfolio data
} finally {
setRefreshing(false);
}
};

  // Log error for debugging but don't block rendering
  if (portfolioError) {
    logger.warn('Portfolio query error:', portfolioError);
    // Continue to render with demo data instead of showing error screen
  }
  
  // Fallback demo data when backend has no portfolios yet or on error
  // Use comprehensive mock data that matches chart values
  const mockPortfoliosData = getMockMyPortfolios();
  const demoPortfolios = mockPortfoliosData.portfolios.map(p => ({
    name: p.name,
    totalValue: p.totalValue,
    holdingsCount: p.holdingsCount,
    holdings: p.holdings.map(h => ({
      id: h.id,
      stock: {
        symbol: h.stock.symbol,
        companyName: h.stock.companyName,
        currentPrice: h.stock.currentPrice,
      },
      shares: h.shares,
      averagePrice: h.averagePrice,
      currentPrice: h.currentPrice,
      totalValue: h.totalValue,
    })),
  }));
  
  // Use data if available, otherwise fall back to demo data
  const rawPortfolios = portfolioData?.myPortfolios?.portfolios || [];
  const portfolios = (rawPortfolios.length > 0 && !portfolioError) ? rawPortfolios : demoPortfolios;
  const totalValue = (portfolioData?.myPortfolios?.totalValue != null)
    ? portfolioData.myPortfolios.totalValue
    : portfolios.reduce((sum: number, p: Portfolio) => sum + (p.totalValue || 0), 0);
  const totalPortfolios = (portfolioData?.myPortfolios?.totalPortfolios != null)
    ? portfolioData.myPortfolios.totalPortfolios
    : portfolios.length;

  // Transform portfolio holdings into format expected by PortfolioHoldings component
  // MUST BE BEFORE ANY EARLY RETURNS
  const allHoldings: Holding[] = useMemo(() => {
  const holdings = portfolios.flatMap((portfolio: Portfolio) => {
    if (!portfolio.holdings || portfolio.holdings.length === 0) return [];
    return portfolio.holdings.map((holding: PortfolioHolding) => {
      const symbol = holding.stock?.symbol || holding.symbol || '';
      const quantity = holding.shares || holding.quantity || 0;
      const currentPrice = realTimePrices[symbol] || holding.currentPrice || holding.stock?.currentPrice || 0;
      const totalValue = quantity * currentPrice || holding.totalValue || 0;
      const averagePrice = holding.averagePrice || holding.stock?.averagePrice || currentPrice;
      const change = currentPrice - averagePrice;
      const changePercent = averagePrice > 0 ? (change / averagePrice) * 100 : 0;
      
      return {
        symbol,
        quantity,
        currentPrice,
        totalValue,
        change: change * quantity, // Total change in value
        changePercent,
        name: holding.stock?.companyName || holding.stock?.name || holding.name,
      };
    });
  });
  
  // Only log in development and limit log size to prevent performance issues
  if (__DEV__ && holdings.length > 0) {
    logger.log('PortfolioScreen: Transformed holdings:', holdings.length);
    // Only log first few holdings to avoid huge logs
    if (holdings.length <= 5) {
      logger.log('PortfolioScreen: Holdings:', holdings);
    }
  }
  return holdings;
  }, [portfolios, realTimePrices]);

  // Basic milestones (v1)
  const milestones: Milestone[] = [
    { id: 'm1', title: 'First $1,000 invested', subtitle: 'A solid foundation' },
    { id: 'm2', title: 'First dividend received', subtitle: 'Income begins to compound' },
    { id: 'm3', title: 'Best month performance', subtitle: '+5% return month' },
  ];

  // NOW SAFE TO DO EARLY RETURNS - ALL HOOKS HAVE BEEN CALLED
  // Only show loading if actively loading and not timed out
  if (portfolioLoading && !portfolioLoadingTimeout) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Icon name="bar-chart-2" size={24} color="#34C759" />
          <Text style={styles.headerTitle}>Portfolio</Text>
          <View style={styles.headerButtons}>
            <TouchableOpacity
              onPress={() => {
                try {
                  logger.log('[PortfolioScreen] Credit Quest button pressed');
                  setShowCreditQuest(true);
                } catch (error) {
                  logger.error('[PortfolioScreen] Error opening Credit Quest:', error);
                }
              }}
              style={styles.creditButton}
            >
              <Icon name="activity" size={18} color="#007AFF" />
              <Text style={styles.creditButtonLabel}>Credit</Text>
            </TouchableOpacity>
            <TouchableOpacity
              onPress={() => {
                try {
                  logger.log('[PortfolioScreen] Family Management button pressed');
                  setShowFamilyManagement(true);
                } catch (error) {
                  logger.error('[PortfolioScreen] Error opening Family Management:', error);
                }
              }}
              style={styles.familyButton}
            >
              <Icon 
                name={familyGroup ? "users" : "user-plus"} 
                size={20} 
                color={familyGroup ? "#34C759" : "#8E8E93"} 
              />
              {familyGroup && (
                <View style={styles.familyBadge}>
                  <Text style={styles.familyBadgeText}>{familyGroup.members.length}</Text>
                </View>
              )}
            </TouchableOpacity>
          </View>
        </View>
        <View style={styles.loadingContainer}>
          <Icon name="refresh-cw" size={32} color="#34C759" />
          <Text style={styles.loadingText}>Loading your portfolio...</Text>
        </View>
      </View>
    );
  }

  if (portfolios.length === 0) {
return (
<View style={styles.container}>
<View style={styles.header}>
<Icon name="bar-chart-2" size={24} color="#34C759" />
<Text style={styles.headerTitle}>Portfolio</Text>
<View style={styles.headerButtons}>
  <TouchableOpacity
    onPress={() => setShowCreditQuest(true)}
    style={styles.creditButton}
  >
    <Icon name="credit-card" size={18} color="#007AFF" />
    <Text style={styles.creditButtonLabel}>Credit</Text>
  </TouchableOpacity>
  <TouchableOpacity
    onPress={() => setShowFamilyManagement(true)}
    style={styles.familyButton}
  >
    <Icon 
      name={familyGroup ? "users" : "user-plus"} 
      size={20} 
      color={familyGroup ? "#34C759" : "#8E8E93"} 
    />
    {familyGroup && (
      <View style={styles.familyBadge}>
        <Text style={styles.familyBadgeText}>{familyGroup.members.length}</Text>
      </View>
    )}
  </TouchableOpacity>
</View>
</View>
<View style={styles.emptyContainer}>
<Icon name="bar-chart-2" size={64} color="#9CA3AF" />
<Text style={styles.emptyTitle}>No Portfolios Yet</Text>
<Text style={styles.emptySubtitle}>
Start building your investment portfolio by adding stocks.
</Text>
<View style={styles.emptyActions}>
<Text 
style={styles.emptyActionText}
onPress={() => navigateTo?.('home')}
>
Go to Home to add stocks
</Text>
</View>
</View>
{/* Family Management Modal - also available in empty state */}
<FamilyManagementModal
  visible={showFamilyManagement}
  onClose={() => {
    setShowFamilyManagement(false);
    loadFamilyGroup();
  }}
  onFamilyCreated={(group) => {
    setFamilyGroup(group);
    const user = group.members.find(m => m.role === 'owner') || group.members[0];
    setCurrentUser(user || null);
  }}
/>
</View>
);
  }
return (
<View style={styles.container}>
<View style={styles.header}>
<Icon name="bar-chart-2" size={24} color="#34C759" />
<Text style={styles.headerTitle}>Portfolio</Text>
<View style={styles.headerButtons}>
  <TouchableOpacity
    onPress={() => setShowCreditQuest(true)}
    style={styles.creditButton}
  >
    <Icon name="credit-card" size={18} color="#007AFF" />
    <Text style={styles.creditButtonLabel}>Credit</Text>
  </TouchableOpacity>
  <TouchableOpacity
    onPress={() => setShowFamilyManagement(true)}
    style={styles.familyButton}
  >
    <Icon 
      name={familyGroup ? "users" : "user-plus"} 
      size={20} 
      color={familyGroup ? "#34C759" : "#8E8E93"} 
    />
    {familyGroup && (
      <View style={styles.familyBadge}>
        <Text style={styles.familyBadgeText}>{familyGroup.members.length}</Text>
      </View>
    )}
  </TouchableOpacity>
</View>
</View>
    <ScrollView
      style={styles.content}
      contentContainerStyle={{ paddingBottom: insets.bottom + 80 }}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
      showsVerticalScrollIndicator={false}
    >
    {/* Portfolio Overview - Constellation Orb or Shared Orb */}
    {/* Show SharedOrb if user has family group, otherwise ConstellationOrb */}
{snapshot ? (
  <View style={styles.constellationContainer}>
    {familyGroup && currentUser ? (
      <SharedOrb
        snapshot={snapshot}
        familyGroupId={familyGroup.id}
        currentUser={currentUser}
        onGesture={(gesture) => {
          // Map gestures to modals
          switch (gesture) {
            case 'tap':
              setShowLifeEvents(true);
              break;
            case 'double_tap':
              setShowQuickActions(true);
              break;
            case 'long_press':
              setShowBreakdown(true);
              break;
            case 'swipe_left':
              setShowShield(true);
              break;
            case 'swipe_right':
              setShowGrowth(true);
              break;
            case 'pinch':
              setShowWhatIf(true);
              break;
          }
        }}
      />
    ) : (
      <ConstellationOrb
        snapshot={snapshot}
        onTap={() => setShowLifeEvents(true)}
        onDoubleTap={() => setShowQuickActions(true)}
        onLongPress={() => setShowBreakdown(true)}
        onSwipeLeft={() => setShowShield(true)}
        onSwipeRight={() => setShowGrowth(true)}
        onPinch={() => setShowWhatIf(true)}
      />
    )}
    
    {/* Gesture Action Modals */}
    {snapshot && (
      <>
        <LifeEventPetalsModal
          visible={showLifeEvents}
          onClose={() => setShowLifeEvents(false)}
          snapshot={snapshot}
        />
        <MarketCrashShieldView
          visible={showShield}
          onClose={() => setShowShield(false)}
          snapshot={snapshot}
        />
        <GrowthProjectionView
          visible={showGrowth}
          onClose={() => setShowGrowth(false)}
          snapshot={snapshot}
        />
        <WhatIfSimulator
          visible={showWhatIf}
          onClose={() => setShowWhatIf(false)}
          snapshot={snapshot}
        />
        <QuickActionsModal
          visible={showQuickActions}
          onClose={() => setShowQuickActions(false)}
          snapshot={snapshot}
          onNavigate={go}
        />
        <DetailedBreakdownModal
          visible={showBreakdown}
          onClose={() => setShowBreakdown(false)}
          snapshot={snapshot}
        />
      </>
    )}
    {/* Always render DetailedBreakdownModal even if snapshot is null (will use fallback) */}
    {!snapshot && (
      <DetailedBreakdownModal
        visible={showBreakdown}
        onClose={() => setShowBreakdown(false)}
        snapshot={{
          netWorth: 0,
          cashflow: { period: '30d', in: 0, out: 0, delta: 0 },
          positions: [],
          shield: [],
          breakdown: { bankBalance: 0, portfolioValue: 0, bankAccountsCount: 0 },
        }}
      />
    )}
    {/* Family Management Modal */}
    <FamilyManagementModal
      visible={showFamilyManagement}
      onClose={() => {
        setShowFamilyManagement(false);
        loadFamilyGroup(); // Reload family group after closing
      }}
      onFamilyCreated={(group) => {
        setFamilyGroup(group);
        const user = group.members.find(m => m.role === 'owner') || group.members[0];
        setCurrentUser(user || null);
      }}
    />
    {/* Dawn Ritual Modal */}
    <DawnRitualScreen
      visible={showDawnRitual}
      onComplete={async (transactionsSynced) => {
        const { dawnRitualScheduler } = await import('../../rituals/services/DawnRitualScheduler');
        await dawnRitualScheduler.markPerformed();
        setShowDawnRitual(false);
      }}
      onClose={() => setShowDawnRitual(false)}
    />
    {/* Credit Quest Modal */}
    <CreditQuestScreen
      visible={showCreditQuest}
      onClose={() => setShowCreditQuest(false)}
    />
    {/* Milestones Timeline below orb */}
    <MilestonesTimeline milestones={milestones} onCelebrate={(t) => setCelebrateTitle(t)} />
  </View>
) : (
  <View style={styles.portfolioOverview}>
    {/* Debug info for Constellation Orb */}
    {__DEV__ && snapshotLoading && (
      <View style={{ padding: 16, backgroundColor: '#FFF3CD', borderRadius: 8, marginBottom: 16 }}>
        <Text style={{ color: '#856404', fontSize: 12 }}>
          Loading Constellation Orb... (snapshotLoading: {String(snapshotLoading)})
        </Text>
        {snapshotError && (
          <Text style={{ color: '#721C24', fontSize: 12, marginTop: 4 }}>
            Error: {snapshotError.message}
          </Text>
        )}
      </View>
    )}
    <Text style={styles.overviewTitle}>Your Portfolios</Text>
    <Text style={styles.overviewSubtitle}>
      {totalPortfolios} portfolios • ${totalValue.toLocaleString()} total value
      {loadingPrices && ' • Loading prices...'}
    </Text>
    <View style={styles.watchlistGrid}>
      {portfolios.slice(0, 3).map((portfolio: Portfolio) => (
        <View key={portfolio.name} style={styles.watchlistItem}>
          <Text style={styles.stockSymbol}>{portfolio.name}</Text>
          <Text style={styles.stockName} numberOfLines={1}>
            {portfolio.holdingsCount} holdings
          </Text>
          <View style={styles.priceContainer}>
            <Text style={styles.stockPrice}>
              ${portfolio.totalValue ? portfolio.totalValue.toLocaleString() : '0'}
            </Text>
          </View>
        </View>
      ))}
    </View>
    {portfolios.length > 3 && (
      <Text style={styles.moreStocks}>
        +{portfolios.length - 3} more portfolios
      </Text>
    )}

    {/* Milestones Timeline (placed outside grid for full width) */}
    <MilestonesTimeline milestones={milestones} onCelebrate={(t) => setCelebrateTitle(t)} />
  </View>
)}

{/* Portfolio Holdings - Mid Section */}
<View style={{ marginTop: 24, marginBottom: 16, paddingHorizontal: 16 }}>
    <PortfolioHoldings
      holdings={allHoldings}
      onStockPress={(symbol) => {
        try {
          logger.log('[PortfolioScreen] Stock pressed:', symbol);
          go('StockDetail', { symbol });
        } catch (error) {
          logger.error('[PortfolioScreen] Error navigating to StockDetail:', error);
          Alert.alert('Navigation Error', `Could not open ${symbol} details. Please try again.`);
        }
      }}
      onBuy={(holding) => {
        try {
          logger.log('[PortfolioScreen] Buy button pressed for:', holding.symbol);
          go('trading', { symbol: holding.symbol, action: 'buy' });
        } catch (error) {
          logger.error('[PortfolioScreen] Error navigating to trading:', error);
          Alert.alert('Navigation Error', 'Could not open trading screen. Please try again.');
        }
      }}
      onSell={(holding) => {
        try {
          logger.log('[PortfolioScreen] Sell button pressed for:', holding.symbol);
          go('trading', { symbol: holding.symbol, action: 'sell' });
        } catch (error) {
          logger.error('[PortfolioScreen] Error navigating to trading (sell):', error);
          Alert.alert('Navigation Error', 'Could not open trading screen. Please try again.');
        }
      }}
      loading={loadingPrices && !portfolioLoadingTimeout && portfolioLoading}
      onAddHoldings={() => {
        try {
          logger.log('[PortfolioScreen] Add Holdings button pressed');
          go('portfolio-management');
        } catch (error) {
          logger.error('[PortfolioScreen] Error navigating to portfolio-management:', error);
          Alert.alert('Navigation Error', 'Could not open portfolio management. Please try again.');
        }
      }}
  />
</View>

             {/* Portfolio Actions */}
             <View style={styles.actionsSection}>
               <Text style={styles.actionsTitle}>Portfolio Management</Text>
<TouchableOpacity 
 style={styles.actionButton}
 onPress={() => {
   try {
     logger.log('[PortfolioScreen] Portfolio Management button pressed');
     go('portfolio-management');
   } catch (error) {
     logger.error('[PortfolioScreen] Error navigating to portfolio-management:', error);
     Alert.alert('Navigation Error', 'Could not open portfolio management. Please try again.');
   }
 }}
>
<View style={styles.actionContent}>
<Icon name="edit" size={24} color="#34C759" />
<View style={styles.actionText}>
<Text style={styles.actionTitle}>Manage Holdings</Text>
<Text style={styles.actionDescription}>
Add, edit, or remove stocks from your portfolio
</Text>
</View>
<Icon name="chevron-right" size={20} color="#8E8E93" />
</View>
</TouchableOpacity>
<TouchableOpacity 
 style={styles.actionButton}
 onPress={() => {
   try {
     logger.log('[PortfolioScreen] Stock Discovery button pressed');
     go('stock');
   } catch (error) {
     logger.error('[PortfolioScreen] Error navigating to stock:', error);
     Alert.alert('Navigation Error', 'Could not open stock discovery. Please try again.');
   }
 }}
>
<View style={styles.actionContent}>
<Icon name="search" size={24} color="#34C759" />
<View style={styles.actionText}>
<Text style={styles.actionTitle}>Discover Stocks</Text>
<Text style={styles.actionDescription}>
Find new stocks to add to your watchlist
</Text>
</View>
<Icon name="chevron-right" size={20} color="#8E8E93" />
</View>
</TouchableOpacity>
<TouchableOpacity 
 style={styles.actionButton}
 onPress={() => {
   try {
     logger.log('[PortfolioScreen] AI Portfolio button pressed');
     go('ai-portfolio');
   } catch (error) {
     logger.error('[PortfolioScreen] Error navigating to ai-portfolio:', error);
     Alert.alert('Navigation Error', 'Could not open AI recommendations. Please try again.');
   }
 }}
>
<View style={styles.actionContent}>
<Icon name="cpu" size={24} color="#34C759" />
<View style={styles.actionText}>
<Text style={styles.actionTitle}>AI Recommendations</Text>
<Text style={styles.actionDescription}>
Get personalized stock recommendations
</Text>
</View>
<Icon name="chevron-right" size={20} color="#8E8E93" />
</View>
</TouchableOpacity>
<TouchableOpacity 
 style={styles.actionButton}
 onPress={() => {
   try {
     logger.log('[PortfolioScreen] Trading button pressed');
     go('trading');
   } catch (error) {
     logger.error('[PortfolioScreen] Error navigating to trading:', error);
     Alert.alert('Navigation Error', 'Could not open trading. Please try again.');
   }
 }}
>
<View style={styles.actionContent}>
<Icon name="dollar-sign" size={24} color="#34C759" />
<View style={styles.actionText}>
<Text style={styles.actionTitle}>Trading</Text>
<Text style={styles.actionDescription}>
Place buy/sell orders and manage your trades
</Text>
</View>
<Icon name="chevron-right" size={20} color="#8E8E93" />
</View>
</TouchableOpacity>
<TouchableOpacity 
  style={[styles.actionButton, { backgroundColor: '#FFF8E1' }]}
  onPress={() => {
    try {
      logger.log('[PortfolioScreen] Premium Analytics button pressed');
      go('premium-analytics');
    } catch (error) {
      logger.error('[PortfolioScreen] Error navigating to premium-analytics:', error);
      Alert.alert('Navigation Error', 'Could not open premium analytics. Please try again.');
    }
  }}
>
<View style={styles.actionContent}>
<Icon name="star" size={24} color="#FFD700" />
<View style={styles.actionText}>
<Text style={[styles.actionTitle, { color: '#B8860B' }]}>Options Analysis</Text>
<Text style={styles.actionDescription}>
Advanced options strategies and market sentiment
</Text>
</View>
<Icon name="chevron-right" size={20} color="#8E8E93" />
</View>
        </TouchableOpacity>
        {/* Dawn Ritual - Manual Trigger */}
        <TouchableOpacity 
          style={[styles.actionButton, { backgroundColor: '#FFF4E6', borderWidth: 1, borderColor: '#FF9500' }]}
          onPress={() => {
            try {
              logger.log('[PortfolioScreen] Dawn Ritual button pressed');
              setShowDawnRitual(true);
            } catch (error) {
              logger.error('[PortfolioScreen] Error opening Dawn Ritual:', error);
            }
          }}
        >
          <View style={styles.actionContent}>
            <Icon name="sunrise" size={24} color="#FF9500" />
            <View style={styles.actionText}>
              <Text style={[styles.actionTitle, { color: '#FF9500' }]}>🌅 Dawn Ritual</Text>
              <Text style={styles.actionDescription}>
                Start your daily wealth awakening ritual (30s)
              </Text>
            </View>
            <Icon name="chevron-right" size={20} color="#8E8E93" />
          </View>
        </TouchableOpacity>
      </View>

      {/* Portfolio Health & Visualization Section */}
      <View style={styles.wellnessSection}>
        <Text style={styles.wellnessTitle}>Portfolio Health & Visualization</Text>
        
        <TouchableOpacity 
          style={styles.wellnessButton}
          onPress={() => go('wellness-dashboard')}
        >
          <View style={styles.wellnessButtonContent}>
            <Icon name="heart" size={24} color="#EF4444" />
            <View style={styles.wellnessText}>
              <Text style={styles.wellnessButtonTitle}>Wellness Score Dashboard</Text>
              <Text style={styles.wellnessButtonDescription}>
                Dynamic portfolio health metrics and insights
              </Text>
            </View>
            <Icon name="chevron-right" size={20} color="#8E8E93" />
          </View>
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.wellnessButton}
          onPress={() => go('ar-preview')}
        >
          <View style={styles.wellnessButtonContent}>
            <Icon name="camera" size={24} color="#10B981" />
            <View style={styles.wellnessText}>
              <Text style={styles.wellnessButtonTitle}>AR Portfolio Preview</Text>
              <Text style={styles.wellnessButtonDescription}>
                Augmented reality portfolio visualization
              </Text>
            </View>
            <Icon name="chevron-right" size={20} color="#8E8E93" />
          </View>
        </TouchableOpacity>
      </View>

      {/* Advanced Portfolio Features Section */}
      <View style={styles.wellnessSection}>
        <Text style={styles.wellnessTitle}>Advanced Portfolio Features</Text>
        
        <TouchableOpacity 
          style={styles.wellnessButton}
          onPress={() => go('blockchain-integration')}
        >
          <View style={styles.wellnessButtonContent}>
            <Icon name="link" size={24} color="#8B5CF6" />
            <View style={styles.wellnessText}>
              <Text style={styles.wellnessButtonTitle}>Blockchain Integration</Text>
              <Text style={styles.wellnessButtonDescription}>
                DeFi meets traditional finance - tokenize your portfolio
              </Text>
            </View>
            <Icon name="chevron-right" size={20} color="#8E8E93" />
          </View>
        </TouchableOpacity>
      </View>

      {/* Analytics Section */}
<View style={styles.analyticsSection}>
<Text style={styles.analyticsTitle}>Portfolio Analytics</Text>
<View style={styles.analyticsGrid}>
<View style={styles.analyticsCard}>
<Text style={styles.analyticsLabel}>Total Return</Text>
<Text style={styles.analyticsValue}>+12.5%</Text>
<Text style={styles.analyticsSubtext}>This month</Text>
</View>
<View style={styles.analyticsCard}>
<Text style={styles.analyticsLabel}>Sharpe Ratio</Text>
<Text style={styles.analyticsValue}>1.4</Text>
<Text style={styles.analyticsSubtext}>Risk-adjusted</Text>
</View>
<View style={styles.analyticsCard}>
<Text style={styles.analyticsLabel}>Volatility</Text>
<Text style={styles.analyticsValue}>15.8%</Text>
<Text style={styles.analyticsSubtext}>Annualized</Text>
</View>
<View style={styles.analyticsCard}>
<Text style={styles.analyticsLabel}>Max Drawdown</Text>
<Text style={styles.analyticsValue}>-5.2%</Text>
<Text style={styles.analyticsSubtext}>Worst decline</Text>
</View>
</View>
      <TouchableOpacity 
        style={styles.analyticsButton}
        onPress={() => go('premium-analytics')}
      >
        <View style={styles.analyticsButtonContent}>
          <Icon name="pie-chart" size={20} color="#007AFF" />
          <Text style={styles.analyticsButtonText}>View Detailed Analytics</Text>
          <Icon name="chevron-right" size={16} color="#8E8E93" />
        </View>
      </TouchableOpacity>
      
      {/* Signal Updates Button */}
      <TouchableOpacity 
        style={[styles.analyticsButton, { marginTop: 12 }]}
        onPress={() => go('signal-updates', { mode: 'portfolio' })}
      >
        <View style={styles.analyticsButtonContent}>
          <Icon name="activity" size={20} color="#10B981" />
          <Text style={styles.analyticsButtonText}>Portfolio Signal Updates</Text>
          <Icon name="chevron-right" size={16} color="#8E8E93" />
        </View>
      </TouchableOpacity>
</View>
</ScrollView>
  {/* Celebration Overlay */}
  <MilestoneUnlockOverlay visible={!!celebrateTitle} title={celebrateTitle ?? ''} onClose={() => setCelebrateTitle(null)} />
</View>
);
};
const styles = StyleSheet.create({
container: {
flex: 1,
backgroundColor: '#f8f9fa',
paddingTop: 0,
},
header: {
flexDirection: 'row',
alignItems: 'center',
justifyContent: 'space-between',
gap: 12,
paddingHorizontal: 20,
paddingVertical: 16,
backgroundColor: '#FFFFFF',
borderBottomWidth: 1,
borderBottomColor: '#E5E5EA',
},
headerTitle: {
fontSize: 20,
fontWeight: '600',
color: '#1C1C1E',
flex: 1,
},
headerButtons: {
    flexDirection: 'row',
    gap: 8,
    alignItems: 'center',
  },
  creditButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#F0F8FF',
    minHeight: 40,
  },
  creditButtonLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#007AFF',
  },
  familyButton: {
    position: 'relative',
    padding: 10,
    borderRadius: 20,
    backgroundColor: '#F8F9FA',
    minWidth: 40,
    minHeight: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
familyBadge: {
position: 'absolute',
top: -4,
right: -4,
backgroundColor: '#34C759',
borderRadius: 10,
minWidth: 20,
height: 20,
justifyContent: 'center',
alignItems: 'center',
paddingHorizontal: 4,
borderWidth: 2,
borderColor: '#FFFFFF',
},
familyBadgeText: {
color: '#FFFFFF',
fontSize: 10,
fontWeight: 'bold',
},
content: {
flex: 1,
},
loadingContainer: {
flex: 1,
justifyContent: 'center',
alignItems: 'center',
padding: 40,
},
loadingText: {
fontSize: 16,
color: '#8E8E93',
marginTop: 16,
},
errorContainer: {
flex: 1,
justifyContent: 'center',
alignItems: 'center',
padding: 40,
},
errorTitle: {
fontSize: 18,
fontWeight: '600',
color: '#1C1C1E',
marginTop: 16,
marginBottom: 8,
},
errorText: {
fontSize: 14,
color: '#8E8E93',
textAlign: 'center',
lineHeight: 20,
},
errorActions: {
marginTop: 20,
},
errorActionText: {
fontSize: 16,
color: '#34C759',
fontWeight: '600',
},
emptyContainer: {
flex: 1,
justifyContent: 'center',
alignItems: 'center',
padding: 40,
},
emptyTitle: {
fontSize: 20,
fontWeight: '600',
color: '#1C1C1E',
marginTop: 16,
marginBottom: 8,
},
emptySubtitle: {
fontSize: 14,
color: '#8E8E93',
textAlign: 'center',
lineHeight: 20,
marginBottom: 20,
},
emptyActions: {
marginTop: 20,
},
emptyActionText: {
fontSize: 16,
color: '#34C759',
fontWeight: '600',
},
constellationContainer: {
marginTop: 16,
paddingHorizontal: 16,
paddingBottom: 16,
},
portfolioOverview: {
backgroundColor: '#FFFFFF',
borderRadius: 12,
padding: 20,
marginHorizontal: 16,
marginBottom: 16,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 4,
elevation: 3,
},
overviewTitle: {
fontSize: 20,
fontWeight: 'bold',
color: '#1C1C1E',
marginBottom: 4,
},
overviewSubtitle: {
fontSize: 14,
color: '#8E8E93',
marginBottom: 16,
},
  watchlistGrid: {
  flexDirection: 'row',
  flexWrap: 'wrap',
  justifyContent: 'space-between',
  rowGap: 12,
  },
  watchlistItem: {
  width: '48%',
  backgroundColor: '#F8F9FA',
  borderRadius: 12,
  padding: 14,
  marginBottom: 12,
  alignItems: 'flex-start',
  },
  stockSymbol: {
  fontSize: 16,
  fontWeight: '700',
  color: '#1C1C1E',
  marginBottom: 2,
  },
  stockName: {
  fontSize: 12,
  color: '#8E8E93',
  textAlign: 'left',
  marginBottom: 6,
  },
priceContainer: {
  alignItems: 'flex-start',
},
stockPrice: {
  fontSize: 16,
  fontWeight: '700',
  color: '#34C759',
  lineHeight: 18,
},
livePriceIndicator: {
fontSize: 10,
fontWeight: '600',
color: '#34C759',
backgroundColor: '#E8F5E8',
paddingHorizontal: 4,
paddingVertical: 2,
borderRadius: 4,
textAlign: 'center',
marginTop: 2,
},
moreStocks: {
fontSize: 14,
color: '#8E8E93',
textAlign: 'center',
fontStyle: 'italic',
marginTop: 8,
},
actionsSection: {
marginTop: 8,
paddingHorizontal: 16,
},
actionsTitle: {
fontSize: 18,
fontWeight: 'bold',
color: '#1C1C1E',
marginBottom: 16,
},
actionButton: {
backgroundColor: '#FFFFFF',
borderRadius: 12,
padding: 16,
marginBottom: 12,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 4,
elevation: 3,
},
actionContent: {
flexDirection: 'row',
alignItems: 'center',
},
actionText: {
flex: 1,
marginLeft: 16,
},
actionTitle: {
fontSize: 16,
fontWeight: '600',
color: '#1C1C1E',
marginBottom: 4,
},
actionDescription: {
fontSize: 14,
color: '#8E8E93',
lineHeight: 20,
},
analyticsSection: {
marginTop: 8,
paddingHorizontal: 16,
},
analyticsTitle: {
fontSize: 18,
fontWeight: 'bold',
color: '#1C1C1E',
marginBottom: 16,
},
analyticsGrid: {
flexDirection: 'row',
flexWrap: 'wrap',
justifyContent: 'space-between',
marginBottom: 16,
},
analyticsCard: {
backgroundColor: '#FFFFFF',
borderRadius: 12,
padding: 16,
width: '48%',
marginBottom: 12,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 4,
elevation: 3,
},
analyticsLabel: {
fontSize: 12,
color: '#8E8E93',
fontWeight: '500',
marginBottom: 4,
},
analyticsValue: {
fontSize: 20,
fontWeight: 'bold',
color: '#1C1C1E',
marginBottom: 2,
},
analyticsSubtext: {
fontSize: 11,
color: '#8E8E93',
},
analyticsButton: {
backgroundColor: '#F0F8FF',
borderRadius: 12,
padding: 16,
borderWidth: 1,
borderColor: '#E3F2FD',
},
analyticsButtonContent: {
flexDirection: 'row',
alignItems: 'center',
justifyContent: 'center',
},
analyticsButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
    marginLeft: 8,
    marginRight: 8,
  },
  wellnessSection: {
    marginTop: 8,
    paddingHorizontal: 16,
  },
  wellnessTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1C1C1E',
    marginBottom: 16,
  },
  wellnessButton: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  wellnessButtonContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  wellnessText: {
    flex: 1,
    marginLeft: 16,
  },
  wellnessButtonTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  wellnessButtonDescription: {
    fontSize: 14,
    color: '#8E8E93',
    lineHeight: 20,
  },
});
export default PortfolioScreen;
