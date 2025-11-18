import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  ScrollView,
  RefreshControl,
} from 'react-native';
import { useQuery, useMutation, useApolloClient } from '@apollo/client';
import { useNavigation } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/Feather';
import { Alert } from 'react-native';
import OnboardingGuard from '../../../components/OnboardingGuard';
import AlpacaConnectModal from '../../../components/AlpacaConnectModal';
import SBLOCCalculator from '../../../components/forms/SBLOCCalculator';
import { alpacaAnalytics } from '../../../services/alpacaAnalyticsService';
import { AccountSummaryCard } from '../components/AccountSummaryCard';
import { PositionsList } from '../components/PositionsList';
import { PositionRow } from '../components/PositionRow';
import { OrdersList } from '../components/OrdersList';
import { OrderModal } from '../components/OrderModal';
import { useAlpacaAccount } from '../hooks/useAlpacaAccount';
import { useAlpacaPositions } from '../hooks/useAlpacaPositions';
import { useAlpacaOrders } from '../hooks/useAlpacaOrders';
import { usePlaceOrder } from '../hooks/usePlaceOrder';
import { useOrderForm } from '../hooks/useOrderForm';
import {
  GET_TRADING_ACCOUNT,
  GET_TRADING_POSITIONS,
  GET_TRADING_ORDERS,
  GET_TRADING_QUOTE,
  CANCEL_ORDER,
} from '../../../graphql/tradingQueries';
import { AlpacaPosition, NavigationType } from '../types';
import logger from '../../../utils/logger';

const C = {
  bg: '#F5F6FA',
  card: '#FFFFFF',
  line: '#E9EAF0',
  text: '#111827',
  sub: '#6B7280',
  primary: '#007AFF',
};

/* -------------------------------- Screen -------------------------------- */

const TradingScreen = ({ navigateTo }: { navigateTo: (screen: string) => void }) => {
  const navigation = useNavigation<NavigationType>();
  const apolloClient = useApolloClient();
  const [activeTab, setActiveTab] = useState<'overview' | 'orders'>('overview');
  const [refreshing, setRefreshing] = useState(false);
  const [showOrderModal, setShowOrderModal] = useState(false);
  const [showSBLOCModal, setShowSBLOCModal] = useState(false);
  const [showConnectModal, setShowConnectModal] = useState(false);
  const [orderFilter, setOrderFilter] = useState<'all' | 'open' | 'filled' | 'cancelled'>('all');

  // Alpaca account hooks
  const { alpacaAccount, loading: alpacaAccountLoading, refetch: refetchAlpacaAccount } =
    useAlpacaAccount(1);

  const { positions: alpacaPositions, loading: alpacaPositionsLoading, refetch: refetchAlpacaPositions } =
    useAlpacaPositions(alpacaAccount?.id || null);

  const { orders: alpacaOrders, loading: alpacaOrdersLoading, refetch: refetchAlpacaOrders } =
    useAlpacaOrders(alpacaAccount?.id || null);

  // Legacy trading account queries (fallback)
  const { data: accountData, loading: accountLoading, refetch: refetchAccount } = useQuery(
    GET_TRADING_ACCOUNT,
    {
      errorPolicy: 'all',
      fetchPolicy: 'cache-and-network',
      notifyOnNetworkStatusChange: true,
    }
  );

  const { data: positionsData, loading: positionsLoading, refetch: refetchPositions } = useQuery(
    GET_TRADING_POSITIONS,
    {
      errorPolicy: 'all',
      fetchPolicy: 'cache-and-network',
      notifyOnNetworkStatusChange: true,
    }
  );

  const {
    data: ordersData,
    loading: ordersLoading,
    refetch: refetchOrders,
    startPolling: startOrdersPolling,
    stopPolling: stopOrdersPolling,
  } = useQuery(GET_TRADING_ORDERS, {
    variables: { limit: 20 },
    errorPolicy: 'all',
    notifyOnNetworkStatusChange: true,
  });

  // Quote query for order modal
  const orderForm = useOrderForm();
  const [quoteSymbol, setQuoteSymbol] = useState<string>('');
  
  const {
    data: quoteData,
    loading: quoteLoading,
    refetch: refetchQuote,
    error: quoteError,
  } = useQuery(GET_TRADING_QUOTE, {
    variables: { symbol: quoteSymbol || 'AAPL' },
    skip: !quoteSymbol, // Only run when we have a symbol
    errorPolicy: 'all',
    fetchPolicy: 'cache-first', // Use cache first for faster response
    notifyOnNetworkStatusChange: true,
    // Add timeout handling - if query takes too long, show mock data
    context: {
      timeout: 5000, // 5 second timeout
    },
    onCompleted: async (data) => {
      // Cache quote for offline access
      if (data?.tradingQuote && quoteSymbol) {
        const { tradingOfflineCache } = await import('../services/TradingOfflineCache');
        await tradingOfflineCache.cacheQuote(quoteSymbol, data.tradingQuote);
      }
      logger.log('✅ TradingQuote query completed:', JSON.stringify(data, null, 2));
      logger.log('📊 TradingQuote data structure:', {
        hasTradingQuote: !!data?.tradingQuote,
        tradingQuote: data?.tradingQuote,
        keys: data ? Object.keys(data) : [],
      });
    },
    onError: (error) => {
      if (__DEV__) {
        console.warn('⚠️ TradingQuote query error:', error);
        console.warn('⚠️ Error details:', {
          message: error?.message,
          graphQLErrors: error?.graphQLErrors,
          networkError: error?.networkError,
        });
      }
    },
  });

  const quoteTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Update quote symbol when form symbol changes (debounced)
  useEffect(() => {
    if (!showOrderModal) return; // Only fetch when modal is open
    
    const symbol = orderForm.symbol.trim().toUpperCase();
    
    if (!symbol) {
      setQuoteSymbol('');
      return;
    }

    // Clear any existing timer
    if (quoteTimerRef.current) clearTimeout(quoteTimerRef.current);
    
    // Immediate fetch if symbol just appeared, otherwise debounce
    const shouldFetchImmediately = quoteSymbol === '' && symbol.length >= 1;
    
    if (shouldFetchImmediately) {
      setQuoteSymbol(symbol);
      // Small delay to ensure state update
      setTimeout(() => {
        refetchQuote?.({ symbol });
      }, 50);
    } else {
      // Debounce for typing
      quoteTimerRef.current = setTimeout(() => {
        setQuoteSymbol(symbol);
        refetchQuote?.({ symbol });
      }, 300);
    }

    return () => {
      if (quoteTimerRef.current) clearTimeout(quoteTimerRef.current);
    };
  }, [orderForm.symbol, showOrderModal, refetchQuote, quoteSymbol]);

  // Reset when modal closes
  useEffect(() => {
    if (!showOrderModal) {
      setQuoteSymbol('');
      if (quoteTimerRef.current) clearTimeout(quoteTimerRef.current);
    }
  }, [showOrderModal]);

  // Initialize Polygon WebSocket for real-time prices when modal opens
  useEffect(() => {
    if (showOrderModal && orderForm.symbol) {
      // Import dynamically to avoid loading if not needed
      import('../../../services/polygonRealtimeService').then(({ initPolygonStream }) => {
        const symbol = orderForm.symbol.trim().toUpperCase();
        if (symbol) {
          initPolygonStream(apolloClient, [symbol]);
        }
        }).catch((error) => {
        // Silently fail if Polygon service not available (e.g., missing API key)
        logger.warn('⚠️ Polygon WebSocket not available:', error);
      });
    }
  }, [showOrderModal, orderForm.symbol, apolloClient]);

  // Timeout handling for loading states
  const [accountLoadingTimeout, setAccountLoadingTimeout] = useState(false);
  const [positionsLoadingTimeout, setPositionsLoadingTimeout] = useState(false);

  useEffect(() => {
    if (accountLoading) {
      const timer = setTimeout(() => setAccountLoadingTimeout(true), 5000);
      return () => clearTimeout(timer);
    } else {
      setAccountLoadingTimeout(false);
    }
  }, [accountLoading]);

  useEffect(() => {
    if (positionsLoading) {
      const timer = setTimeout(() => setPositionsLoadingTimeout(true), 5000);
      return () => clearTimeout(timer);
    } else {
      setPositionsLoadingTimeout(false);
    }
  }, [positionsLoading]);

  // Optimized polling: only poll orders when Orders tab is visible, with longer interval
  useEffect(() => {
    if (activeTab === 'orders') {
      // Poll every 30 seconds when orders tab is active (reduced from default)
      startOrdersPolling?.(30_000);
    } else {
      stopOrdersPolling?.();
    }
    return () => stopOrdersPolling?.();
  }, [activeTab, startOrdersPolling, stopOrdersPolling]);

  // Mock data for demo when API is unavailable
  const getMockAccount = () => ({
    id: 'demo-account-1',
    buyingPower: 25000,
    cash: 15000,
    portfolioValue: 125000,
    equity: 125000,
    dayTradeCount: 0,
    patternDayTrader: false,
    tradingBlocked: false,
    dayTradingBuyingPower: 50000,
    isDayTradingEnabled: true,
    accountStatus: 'active',
    createdAt: new Date().toISOString(),
  });

  const getMockPositions = () => [
    {
      id: 'pos-1',
      symbol: 'AAPL',
      quantity: 50,
      marketValue: 8750,
      costBasis: 7500,
      unrealizedPl: 1250,
      unrealizedPLPercent: 16.67,
      currentPrice: 175,
      side: 'long',
    },
    {
      id: 'pos-2',
      symbol: 'MSFT',
      quantity: 30,
      marketValue: 12000,
      costBasis: 10200,
      unrealizedPl: 1800,
      unrealizedPLPercent: 17.65,
      currentPrice: 400,
      side: 'long',
    },
  ];

  // Use Alpaca data when available, fallback to legacy or mock data
  const account = useMemo(() => {
    if (alpacaAccount) return alpacaAccount;
    if (accountData?.tradingAccount) return accountData.tradingAccount;
    if (accountLoadingTimeout || (!accountLoading && !accountData)) {
      return getMockAccount();
    }
    return null;
  }, [alpacaAccount, accountData?.tradingAccount, accountLoadingTimeout, accountLoading]);

  const positions = useMemo(() => {
    if (alpacaPositions.length > 0) return alpacaPositions;
    if (positionsData?.tradingPositions && positionsData.tradingPositions.length > 0) {
      return positionsData.tradingPositions;
    }
    if (positionsLoadingTimeout || (!positionsLoading && !positionsData?.tradingPositions)) {
      return getMockPositions();
    }
    return [];
  }, [
    alpacaPositions,
    positionsData?.tradingPositions,
    positionsLoadingTimeout,
    positionsLoading,
  ]);

  const orders = alpacaOrders.length > 0 ? alpacaOrders : ordersData?.tradingOrders ?? [];

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await Promise.all([
        refetchAccount?.(),
        refetchPositions?.(),
        refetchOrders?.(),
        refetchAlpacaAccount?.(),
        refetchAlpacaPositions?.(),
        refetchAlpacaOrders?.(),
        orderForm.symbol ? refetchQuote?.({ symbol: orderForm.symbol.toUpperCase() }) : Promise.resolve(null),
      ]);
    } finally {
      setRefreshing(false);
    }
  }, [
    refetchAccount,
    refetchPositions,
    refetchOrders,
    refetchAlpacaAccount,
    refetchAlpacaPositions,
    refetchAlpacaOrders,
    refetchQuote,
    orderForm.symbol,
  ]);

  // Place order hook
  const { placeOrder, isPlacing: isPlacingOrder } = usePlaceOrder();
  const [cancelOrder] = useMutation(CANCEL_ORDER, { errorPolicy: 'all' });

  // Memoize current position lookup to avoid recalculating on every render
  const currentPosition = useMemo<AlpacaPosition | undefined>(() => {
    if (!orderForm.symbol) return undefined;
    return positions.find((p: AlpacaPosition) => p.symbol === orderForm.symbol.toUpperCase());
  }, [positions, orderForm.symbol]);

  const handlePlaceOrder = async () => {
    const err = orderForm.validate();
    if (err) {
      return Alert.alert('Invalid Order', err);
    }

    // Inline SBLOC nudge for tax-aware flow (only for sells with gains)
    if (orderForm.orderSide === 'sell') {
      const pos = currentPosition;
      const unrealized = Number(
        pos?.unrealizedPl ?? pos?.unrealizedpl ?? pos?.unrealizedPL ?? 0
      );
      if (unrealized > 0) {
        Alert.alert(
          'Need cash without selling?',
          'You may be eligible to borrow against your portfolio via an SBLOC and avoid a taxable sale.',
          [
            { text: 'Keep Selling', style: 'destructive', onPress: proceedWithOrder },
            { text: 'Learn / Borrow', onPress: () => setShowSBLOCModal(true) },
          ]
        );
        return;
      }
    }
    proceedWithOrder();
  };

  const proceedWithOrder = async () => {
    await placeOrder({
      symbol: orderForm.symbol,
      quantity: orderForm.quantity,
      orderType: orderForm.orderType,
      orderSide: orderForm.orderSide,
      price: orderForm.price,
      stopPrice: orderForm.stopPrice,
      alpacaAccount,
      onConnectRequired: () => {
        setShowOrderModal(false);
        setTimeout(() => {
          setShowConnectModal(true);
        }, 300);
      },
      onSuccess: () => {
        setShowOrderModal(false);
        orderForm.reset();
      },
      refetchQueries: [refetchAlpacaOrders, refetchAlpacaPositions, refetchAlpacaAccount],
    });
  };

  const handleCancelOrder = useCallback(async (orderId: string) => {
    try {
      const res = await cancelOrder({ variables: { orderId } });
      if (res?.data?.cancelOrder?.success) {
        Alert.alert('Order Cancelled', 'Your order has been cancelled.');
        refetchOrders?.();
        refetchAlpacaOrders?.();
      } else {
        Alert.alert('Cancel Failed', res?.data?.cancelOrder?.message || 'Please try again.');
      }
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Please try again.';
      Alert.alert('Cancel Failed', errorMessage);
    }
  }, [cancelOrder, refetchOrders, refetchAlpacaOrders]);

  /* ------------------------------- TABS -------------------------------- */

  const ListHeaderComponent = useMemo(
    () => (
      <>
        <AccountSummaryCard
          account={account}
          alpacaAccount={alpacaAccount}
          loading={accountLoading && !accountLoadingTimeout}
        />

        {/* Trading Coach - Quick Assistance */}
        <TouchableOpacity
          style={styles.card}
          onPress={() => navigateTo('trading-coach')}
        >
          <View style={styles.cardHeader}>
            <View style={styles.coachHeader}>
              <Icon name="target" size={20} color="#F59E0B" />
              <Text style={styles.cardTitle}>Trading Coach</Text>
            </View>
            <Icon name="chevron-right" size={16} color="#8E8E93" />
          </View>
          <Text style={styles.coachDescription}>Get quick trading advice & strategies</Text>
          <Text style={styles.coachMeta}>Real-time • Assistance</Text>
        </TouchableOpacity>

        {/* Day Trading - Always Visible Link */}
        <TouchableOpacity style={styles.card} onPress={() => navigateTo('day-trading')}>
          <View style={styles.cardHeader}>
            <View style={styles.coachHeader}>
              <Icon name="trending-up" size={20} color="#2196F3" />
              <Text style={styles.cardTitle}>Daily Top-3 Picks</Text>
            </View>
            <Icon name="chevron-right" size={16} color="#8E8E93" />
          </View>
          <Text style={styles.coachDescription}>AI-powered intraday opportunities</Text>
          <Text style={styles.coachMeta}>Intraday • Signals</Text>
        </TouchableOpacity>
      </>
    ),
    [account, alpacaAccount, accountLoading, accountLoadingTimeout, navigateTo]
  );

  const renderOverview = () => {
    const ListFooterComponent = () => <View style={{ height: 16 }} />;

    return (
      <ScrollView
        style={styles.scroller}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        showsVerticalScrollIndicator={false}
      >
        {ListHeaderComponent}
        <PositionsList
          positions={positions}
          loading={positionsLoading && !positionsLoadingTimeout}
          onRefresh={onRefresh}
          refreshing={refreshing}
        />
        <ListFooterComponent />
      </ScrollView>
    );
  };

  const renderOrders = useCallback(() => {
    return (
      <OrdersList
        orders={orders}
        loading={ordersLoading || alpacaOrdersLoading}
        filter={orderFilter}
        onFilterChange={setOrderFilter}
        onRefresh={onRefresh}
        onCancelOrder={handleCancelOrder}
      />
    );
  }, [orders, ordersLoading, alpacaOrdersLoading, orderFilter, onRefresh, handleCancelOrder]);

  const handleNavigateToOnboarding = () => {
    try {
      navigation.navigate('onboarding' as never);
    } catch (error) {
      try {
        navigation.navigate('Home' as never, {
          screen: 'onboarding',
        } as never);
      } catch (nestedError) {
        if (navigateTo) {
          navigateTo('onboarding');
        }
      }
    }
  };

  return (
    <>
      {/* Alpaca Connect Modal - Render outside OnboardingGuard to ensure it's always on top */}
      <AlpacaConnectModal
        visible={showConnectModal}
        onClose={() => {
          setShowConnectModal(false);
          alpacaAnalytics.track('connect_modal_shown', { action: 'closed' });
        }}
        onConnect={async () => {
          try {
            alpacaAnalytics.track('connect_has_account_yes');
            // Initiate OAuth flow - opens browser to Alpaca
            const { initiateAlpacaOAuth } = await import('../../../services/alpacaOAuthService');
            await initiateAlpacaOAuth();
            setShowConnectModal(false);
          } catch (error) {
            logger.error('Failed to initiate OAuth:', error);
            // Error already handled in service
          }
        }}
      />
      <OnboardingGuard
        requireKYC={!alpacaAccount?.approvedAt}
        forceShowForDemo={false}
        onNavigateToOnboarding={handleNavigateToOnboarding}
      >
        <SafeAreaView style={styles.container}>
          {/* Header */}
          <View style={styles.header}>
            <TouchableOpacity
              onPress={() => navigateTo('home')}
              hitSlop={{ top: 8, left: 8, bottom: 8, right: 8 }}
            >
              <Icon name="arrow-left" size={22} color={C.text} />
            </TouchableOpacity>
            <Text style={styles.headerTitle}>Trading</Text>
            <View style={styles.headerActions}>
              <TouchableOpacity
                onPress={() => navigateTo('risk-management')}
                style={[styles.headerPill, { backgroundColor: '#FEE2E2' }]}
                accessibilityLabel="Risk"
              >
                <Icon name="shield" size={16} color="#EF4444" />
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => navigateTo('ml-system')}
                style={[styles.headerPill, { backgroundColor: '#EDE9FE' }]}
                accessibilityLabel="ML"
              >
                <Icon name="cpu" size={16} color="#7C3AED" />
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => setShowOrderModal(true)}
                style={styles.headerAction}
                accessibilityLabel="New order"
              >
                <Icon name="plus" size={20} color={C.primary} />
                <Text style={styles.headerActionText}>Order</Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Tabs */}
          <View style={styles.tabs}>
            {(['overview', 'orders'] as const).map((t) => (
              <TouchableOpacity
                key={t}
                onPress={() => setActiveTab(t)}
                style={[styles.tabPill, activeTab === t && styles.tabPillActive]}
              >
                <Text style={[styles.tabPillText, activeTab === t && styles.tabPillTextActive]}>
                  {t[0].toUpperCase() + t.slice(1)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* Content */}
          <View style={{ flex: 1 }}>
            {activeTab === 'overview' ? renderOverview() : renderOrders()}
          </View>

          {/* Order Modal */}
          <OrderModal
            visible={showOrderModal}
            onClose={() => {
              setShowOrderModal(false);
              orderForm.reset();
            }}
            onSubmit={handlePlaceOrder}
            isSubmitting={isPlacingOrder}
            quoteData={quoteData}
            quoteLoading={quoteLoading}
            onSBLOCPress={() => setShowSBLOCModal(true)}
            form={orderForm}
          />

          {/* SBLOC Calculator */}
          <SBLOCCalculator
            visible={showSBLOCModal}
            onClose={() => setShowSBLOCModal(false)}
            portfolioValue={account?.portfolioValue || 0}
            onApply={() => {
              setShowSBLOCModal(false);
              Alert.alert(
                'SBLOC Application',
                'This would open the SBLOC application flow with our partner banks.',
                [{ text: 'OK' }]
              );
            }}
          />
        </SafeAreaView>
      </OnboardingGuard>
    </>
  );
};

/* -------------------------------- Styles -------------------------------- */

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.bg },

  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: C.card,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: C.line,
    shadowColor: 'rgba(16,24,40,0.08)',
    shadowOpacity: 1,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  headerTitle: { fontSize: 18, fontWeight: '700', color: C.text },
  headerActions: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  headerAction: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: '#F4F7FF',
  },
  headerActionText: { color: C.primary, fontWeight: '700' },
  headerPill: { paddingHorizontal: 10, paddingVertical: 6, borderRadius: 8 },

  tabs: {
    flexDirection: 'row',
    backgroundColor: C.bg,
    padding: 12,
    gap: 8,
  },
  tabPill: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 999,
    alignItems: 'center',
    backgroundColor: '#E9EDF7',
  },
  tabPillActive: { backgroundColor: C.card, borderWidth: 1, borderColor: C.line },
  tabPillText: { color: '#5B6473', fontWeight: '600' },
  tabPillTextActive: { color: C.text },

  scroller: { paddingHorizontal: 16 },

  card: {
    backgroundColor: C.card,
    borderRadius: 16,
    padding: 16,
    marginTop: 12,
    shadowColor: 'rgba(16,24,40,0.08)',
    shadowOpacity: 1,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  cardTitle: { fontSize: 16, fontWeight: '700', color: C.text },

  // Trading Coach styles
  coachHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  coachDescription: {
    fontSize: 14,
    color: C.sub,
    marginTop: 4,
    marginBottom: 2,
  },
  coachMeta: {
    fontSize: 12,
    color: '#9CA3AF',
    fontWeight: '500',
  },
});

export default TradingScreen;

