import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput, Alert, Modal,
  ActivityIndicator, RefreshControl, SafeAreaView, Dimensions, FlatList,
} from 'react-native';
import { useQuery, useMutation, NetworkStatus } from '@apollo/client';
import { gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import SparkMini from '../../../components/charts/SparkMini';
import SBLOCCalculator from '../../../components/forms/SBLOCCalculator';
import { GET_DAY_TRADING_PICKS } from '../../../graphql/dayTrading';

const { width } = Dimensions.get('window');

/* ------------------------------- GraphQL ------------------------------- */

const GET_TRADING_ACCOUNT = gql`
  query GetTradingAccount {
    tradingAccount {
      id
      buyingPower
      cash
      portfolioValue
      equity
      dayTradeCount
      patternDayTrader
      tradingBlocked
      dayTradingBuyingPower
      isDayTradingEnabled
      accountStatus
      createdAt
    }
  }
`;

const GET_TRADING_POSITIONS = gql`
  query GetTradingPositions {
    tradingPositions {
      id
      symbol
      quantity
      marketValue
      costBasis
      unrealizedPl
      unrealizedpi
      unrealizedPI
      unrealizedPLPercent
      unrealizedPlpc
      currentPrice
      side
    }
  }
`;

const GET_TRADING_ORDERS = gql`
  query GetTradingOrders($status: String, $limit: Int) {
    tradingOrders(status: $status, limit: $limit) {
      id
      symbol
      side
      orderType
      quantity
      price
      stopPrice
      status
      createdAt
      filledAt
      filledQuantity
      averageFillPrice
      commission
      notes
    }
  }
`;

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
      data {
        timestamp
        open
        high
        low
        close
        volume
      }
      currentPrice
      change
      changePercent
    }
  }
`;

const PLACE_STOCK_ORDER = gql`
  mutation PlaceStockOrder($symbol: String!, $side: String!, $quantity: Int!, $orderType: String!, $limitPrice: Float, $timeInForce: String) {
    placeStockOrder(symbol: $symbol, side: $side, quantity: $quantity, orderType: $orderType, limitPrice: $limitPrice, timeInForce: $timeInForce) {
      success
      message
      orderId
    }
  }
`;

const CREATE_ALPACA_ACCOUNT = gql`
  mutation CreateAlpacaAccount(
    $firstName: String!
    $lastName: String!
    $email: String!
    $dateOfBirth: Date!
    $streetAddress: String!
    $city: String!
    $state: String!
    $postalCode: String!
    $phone: String
    $ssn: String
    $country: String
    $employmentStatus: String
    $annualIncome: Float
    $netWorth: Float
    $riskTolerance: String
    $investmentExperience: String
  ) {
    createAlpacaAccount(
      firstName: $firstName
      lastName: $lastName
      email: $email
      dateOfBirth: $dateOfBirth
      streetAddress: $streetAddress
      city: $city
      state: $state
      postalCode: $postalCode
      phone: $phone
      ssn: $ssn
      country: $country
      employmentStatus: $employmentStatus
      annualIncome: $annualIncome
      netWorth: $netWorth
      riskTolerance: $riskTolerance
      investmentExperience: $investmentExperience
    ) {
      success
      message
      alpacaAccountId
      account {
        id
        status
        createdAt
        approvedAt
      }
    }
  }
`;

const GET_ALPACA_ACCOUNT = gql`
  query GetAlpacaAccount($userId: Int!) {
    alpacaAccount(userId: $userId) {
      id
      status
      alpacaAccountId
      approvedAt
      buyingPower
      cash
      portfolioValue
      createdAt
    }
  }
`;

const GET_ALPACA_ORDERS = gql`
  query GetAlpacaOrders($accountId: Int!, $status: String) {
    alpacaOrders(accountId: $accountId, status: $status) {
      id
      symbol
      qty
      side
      type
      timeInForce
      limitPrice
      stopPrice
      status
      filledAvgPrice
      filledQty
      createdAt
      submittedAt
      filledAt
    }
  }
`;

const GET_ALPACA_POSITIONS = gql`
  query GetAlpacaPositions($accountId: Int!) {
    alpacaPositions(accountId: $accountId) {
      id
      symbol
      qty
      avgEntryPrice
      marketValue
      costBasis
      unrealizedPl
      unrealizedPlPc
      currentPrice
      lastDayPrice
      changeToday
      updatedAt
    }
  }
`;

const CANCEL_ORDER = gql`
  mutation CancelOrder($orderId: String!) {
    cancelOrder(orderId: $orderId) { success message }
  }
`;

/* ----------------------------- UI Helpers ------------------------------ */

const C = {
  bg: '#F5F6FA',
  card: '#FFFFFF',
  line: '#E9EAF0',
  text: '#111827',
  sub: '#6B7280',
  primary: '#007AFF',
  green: '#22C55E',
  red: '#EF4444',
  amber: '#F59E0B',
  blueSoft: '#E8F1FF',
  successSoft: '#EAFBF1',
  dangerSoft: '#FEECEC',
  shadow: 'rgba(16,24,40,0.08)',
};

const formatMoney = (v?: number, digits = 2) =>
  `$${(Number(v) || 0).toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits })}`;

const Money = ({ children }: { children?: number }) => (
  <Text style={styles.value}>{formatMoney(children)}</Text>
);

const Chip = ({ label, tone = 'neutral' }: { label: string; tone?: 'neutral'|'success'|'danger'|'warning'|'info' }) => {
  const toneMap: any = {
    neutral: { bg: '#F3F4F6', color: C.sub },
    success: { bg: C.successSoft, color: C.green },
    danger:  { bg: C.dangerSoft,  color: C.red },
    warning: { bg: '#FFF7ED',     color: C.amber },
    info:    { bg: C.blueSoft,    color: C.primary },
  };
  const t = toneMap[tone];
  return (
    <View style={[styles.chip, { backgroundColor: t.bg }]}>
      <Text style={[styles.chipText, { color: t.color }]}>{label}</Text>
    </View>
  );
};

const getStatusMeta = (status: string) => {
  const s = status?.toLowerCase();
  if (s === 'filled')   return { color: C.green, icon: 'check-circle' };
  if (s === 'pending' || s === 'new' || s === 'accepted' || s === 'open')  return { color: C.amber, icon: 'clock' };
  if (s === 'rejected') return { color: C.red, icon: 'x-circle' };
  if (s === 'cancelled' || s === 'canceled')return { color: '#9CA3AF', icon: 'slash' };
  return { color: '#9CA3AF', icon: 'more-horizontal' };
};

const isOpen = (s: string) => ['pending','accepted','new','open'].includes(String(s).toLowerCase());

const groupOrders = (orders: any[]) => {
  const today = new Date();
  const startOfDay = new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime();
  const startOfWeek = (() => {
    const day = today.getDay(); // 0..6
    const diffDate = today.getDate() - day;
    return new Date(today.getFullYear(), today.getMonth(), diffDate).getTime();
  })();

  const buckets: Record<string, any[]> = { 'Today': [], 'This Week': [], 'Earlier': [] };
  for (const o of orders) {
    const t = new Date(o.createdAt).getTime();
    if (t >= startOfDay) buckets['Today'].push(o);
    else if (t >= startOfWeek) buckets['This Week'].push(o);
    else buckets['Earlier'].push(o);
  }
  return buckets;
};

const fmtTime = (iso: string) => {
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, { month:'short', day:'2-digit', hour:'2-digit', minute:'2-digit' }).replace(',', '');
  } catch { return iso; }
};

const sanitizeInt = (s: string) => {
  const n = parseInt(String(s).replace(/[^\d]/g, ''), 10);
  return Number.isFinite(n) ? n : NaN;
};
const sanitizeFloat = (s: string) => {
  const n = parseFloat(String(s).replace(/[^0-9.]/g, ''));
  return Number.isFinite(n) ? n : NaN;
};
const upper = (s: string) => String(s).trim().toUpperCase();



/* -------------------------------- Screen -------------------------------- */

const TradingScreen = ({ navigateTo }: { navigateTo: (screen: string) => void }) => {
  const [activeTab, setActiveTab] = useState<'overview'|'orders'>('overview');
  const [refreshing, setRefreshing] = useState(false);
  const [showOrderModal, setShowOrderModal] = useState(false);
  const [showSBLOCModal, setShowSBLOCModal] = useState(false);
  const [orderType, setOrderType] = useState<'market'|'limit'|'stop_loss'>('market');
  const [orderSide, setOrderSide] = useState<'buy'|'sell'>('buy');
  const [symbol, setSymbol] = useState('');
  const [quantity, setQuantity] = useState('');
  const [price, setPrice] = useState('');
  const [stopPrice, setStopPrice] = useState('');
  const [notes, setNotes] = useState('');
  const [isPlacingOrder, setIsPlacingOrder] = useState(false);
  const [orderFilter, setOrderFilter] = useState<'all'|'open'|'filled'|'cancelled'>('all');
  const [dayTradingMode, setDayTradingMode] = useState<'SAFE'|'AGGRESSIVE'>('SAFE');

  const { data: accountData, loading: accountLoading, refetch: refetchAccount } =
    useQuery(GET_TRADING_ACCOUNT, { errorPolicy: 'all' });

  const { data: positionsData, loading: positionsLoading, refetch: refetchPositions } =
    useQuery(GET_TRADING_POSITIONS, { errorPolicy: 'all' });

  const {
    data: ordersData,
    loading: ordersLoading,
    networkStatus: ordersStatus,
    refetch: refetchOrders,
    startPolling: startOrdersPolling,
    stopPolling: stopOrdersPolling,
  } = useQuery(GET_TRADING_ORDERS, { variables: { limit: 20 }, errorPolicy: 'all', notifyOnNetworkStatusChange: true });

  const { data: dayTradingData, loading: dayTradingLoading, refetch: refetchDayTrading } =
    useQuery(GET_DAY_TRADING_PICKS, { variables: { mode: dayTradingMode }, errorPolicy: 'all' });

  // Debounced quote fetch when typing a symbol
  const {
    data: quoteData,
    refetch: refetchQuote,
  } = useQuery(GET_TRADING_QUOTE, { variables: { symbol: upper(symbol) || 'AAPL' }, skip: !symbol, errorPolicy: 'all' });
  const quoteTimerRef = useRef<NodeJS.Timeout | null>(null);
  useEffect(() => {
    if (!symbol) return;
    if (quoteTimerRef.current) clearTimeout(quoteTimerRef.current);
    quoteTimerRef.current = setTimeout(() => {
      refetchQuote?.({ symbol: upper(symbol) });
    }, 400);
    return () => { if (quoteTimerRef.current) clearTimeout(quoteTimerRef.current); };
  }, [symbol, refetchQuote]);

  const [placeStockOrder] = useMutation(PLACE_STOCK_ORDER, { errorPolicy: 'all' });
  const [createAlpacaAccount] = useMutation(CREATE_ALPACA_ACCOUNT, { errorPolicy: 'all' });
  const [cancelOrder] = useMutation(CANCEL_ORDER, { errorPolicy: 'all' });

  // Alpaca account queries
  const { data: alpacaAccountData, loading: alpacaAccountLoading, refetch: refetchAlpacaAccount } =
    useQuery(GET_ALPACA_ACCOUNT, { 
      variables: { userId: 1 }, // This should come from auth context
      errorPolicy: 'all',
      skip: false
    });

  const { data: alpacaOrdersData, loading: alpacaOrdersLoading, refetch: refetchAlpacaOrders } =
    useQuery(GET_ALPACA_ORDERS, { 
      variables: { accountId: alpacaAccountData?.alpacaAccount?.id || 0 }, 
      errorPolicy: 'all',
      skip: !alpacaAccountData?.alpacaAccount?.id
    });

  const { data: alpacaPositionsData, loading: alpacaPositionsLoading, refetch: refetchAlpacaPositions } =
    useQuery(GET_ALPACA_POSITIONS, { 
      variables: { accountId: alpacaAccountData?.alpacaAccount?.id || 0 }, 
      errorPolicy: 'all',
      skip: !alpacaAccountData?.alpacaAccount?.id
    });

  // Use Alpaca data when available, fallback to mock data
  const alpacaAccount = alpacaAccountData?.alpacaAccount;
  const alpacaPositions = useMemo(() => alpacaPositionsData?.alpacaPositions ?? [], [alpacaPositionsData]);
  const alpacaOrders = useMemo(() => alpacaOrdersData?.alpacaOrders ?? [], [alpacaOrdersData]);
  
  const account = alpacaAccount || accountData?.tradingAccount;
  const positions = alpacaPositions.length > 0 ? alpacaPositions : (positionsData?.tradingPositions ?? []);
  const orders = alpacaOrders.length > 0 ? alpacaOrders : (ordersData?.tradingOrders ?? []);

  // Optional: light polling on orders while Orders tab is visible
  useEffect(() => {
    if (activeTab === 'orders') startOrdersPolling?.(30_000);
    else stopOrdersPolling?.();
    return () => stopOrdersPolling?.();
  }, [activeTab, startOrdersPolling, stopOrdersPolling]);

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
        symbol ? refetchQuote?.({ symbol: upper(symbol) }) : Promise.resolve(null),
      ]);
    } finally { setRefreshing(false); }
  }, [refetchAccount, refetchPositions, refetchOrders, refetchAlpacaAccount, refetchAlpacaPositions, refetchAlpacaOrders, refetchQuote, symbol]);

  /* ----------------------------- Place Order ---------------------------- */

  const validateOrder = () => {
    const sym = upper(symbol);
    const qty = sanitizeInt(quantity);
    if (!sym) return 'Please enter a symbol';
    if (!qty || qty <= 0) return 'Quantity must be a positive integer';
    if (orderType === 'limit') {
      const p = sanitizeFloat(price);
      if (!Number.isFinite(p) || p <= 0) return 'Enter a valid limit price';
    }
    if (orderType === 'stop_loss') {
      const sp = sanitizeFloat(stopPrice);
      if (!Number.isFinite(sp) || sp <= 0) return 'Enter a valid stop price';
    }
    return null;
  };

  const handlePlaceOrder = async () => {
    const err = validateOrder();
    if (err) return Alert.alert('Invalid Order', err);

    // Inline SBLOC nudge for tax-aware flow (only for sells with gains)
    if (orderSide === 'sell') {
      const pos = positions.find((p: any) => p.symbol === upper(symbol));
      const unrealized = Number(pos?.unrealizedPl ?? pos?.unrealizedpl ?? pos?.unrealizedPL ?? 0);
      if (unrealized > 0) {
        Alert.alert(
          'Need cash without selling?',
          'You may be eligible to borrow against your portfolio via an SBLOC and avoid a taxable sale.',
          [
            { text: 'Keep Selling', style: 'destructive', onPress: proceedWithOrder },
            { text: 'Learn / Borrow', onPress: () => setShowSBLOCModal(true) },
          ],
        );
        return;
      }
    }
    proceedWithOrder();
  };

  const proceedWithOrder = async () => {
    setIsPlacingOrder(true);
    try {
      const sym = upper(symbol);
      const qty = sanitizeInt(quantity);
      
      // Check if user has Alpaca account, if not create one
      if (!alpacaAccount) {
        Alert.alert(
          'Alpaca Account Required',
          'You need an Alpaca trading account to place real orders. Would you like to create one?',
          [
            { text: 'Cancel', style: 'cancel' },
            { 
              text: 'Create Account', 
              onPress: async () => {
                try {
                  const accountRes = await createAlpacaAccount({ 
                    variables: { 
                      firstName: "Test",
                      lastName: "User",
                      email: "test@example.com",
                      dateOfBirth: "1990-01-01",
                      streetAddress: "123 Main St",
                      city: "New York",
                      state: "NY",
                      postalCode: "10001",
                      country: "US",
                      riskTolerance: "medium",
                      investmentExperience: "beginner"
                    }
                  });
                  
                  if (accountRes?.data?.createAlpacaAccount?.success) {
                    Alert.alert(
                      'Account Created',
                      accountRes.data.createAlpacaAccount.message || 'Your Alpaca account has been created. Please complete the KYC process to start trading.',
                      [{ text: 'OK', onPress: () => refetchAlpacaAccount() }]
                    );
                  } else {
                    Alert.alert('Account Creation Failed', accountRes?.data?.createAlpacaAccount?.message || 'Could not create Alpaca account. Please try again.');
                  }
                } catch (e: any) {
                  Alert.alert('Account Creation Failed', e?.message || 'Could not create Alpaca account.');
                }
              }
            }
          ]
        );
        setIsPlacingOrder(false);
        return;
      }

      // Check if account is approved for trading
      if (!alpacaAccount.approvedAt) {
        Alert.alert(
          'Account Not Approved',
          'Your Alpaca account is not yet approved for trading. Please complete the KYC process first.',
          [{ text: 'OK' }]
        );
        setIsPlacingOrder(false);
        return;
      }

      // Prepare order variables
      const orderVariables: any = {
        symbol: sym,
        side: orderSide.toUpperCase(),
        quantity: qty,
        orderType: orderType === 'market' ? 'MARKET' : orderType === 'limit' ? 'LIMIT' : 'STOP',
        timeInForce: 'DAY'
      };

      if (orderType === 'limit' && price) {
        orderVariables.limitPrice = sanitizeFloat(price);
      }

      // Place order through Alpaca
      const res = await placeStockOrder({ variables: orderVariables });
      const success = res?.data?.placeStockOrder?.success;
      const message = res?.data?.placeStockOrder?.message;
      const orderId = res?.data?.placeStockOrder?.orderId;

      if (success) {
        Alert.alert(
          'Order Placed Successfully', 
          `${message}\n\nOrder ID: ${orderId}`,
          [{ text: 'OK' }]
        );
        setShowOrderModal(false);
        resetOrderForm();
        
        // Refresh data
        refetchAlpacaOrders?.();
        refetchAlpacaPositions?.();
        refetchAlpacaAccount?.();
      } else {
        Alert.alert('Order Failed', message || 'Could not place order. Please try again.');
      }
    } catch (e: any) {
      Alert.alert('Order Failed', e?.message || 'Could not place order. Please try again.');
    } finally {
      setIsPlacingOrder(false);
    }
  };

  const resetOrderForm = () => {
    setSymbol(''); setQuantity(''); setPrice(''); setStopPrice(''); setNotes('');
    setOrderType('market'); setOrderSide('buy');
  };

  const handleCancelOrder = async (orderId: string) => {
    try {
      const res = await cancelOrder({ variables: { orderId } });
      if (res?.data?.cancelOrder?.success) {
        Alert.alert('Order Cancelled', 'Your order has been cancelled.');
        refetchOrders?.();
      } else {
        Alert.alert('Cancel Failed', res?.data?.cancelOrder?.message || 'Please try again.');
      }
    } catch (e: any) {
      Alert.alert('Cancel Failed', e?.message || 'Please try again.');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'filled':    return C.green;
      case 'pending':   return C.amber;
      case 'cancelled': return C.sub;
      case 'rejected':  return C.red;
      default:          return C.sub;
    }
  };

  /* ------------------------------- TABS -------------------------------- */

  const renderOverview = () => {
    // Create header component with account summary
    const ListHeaderComponent = () => (
      <>
        {/* Account Summary */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>Account Summary</Text>
            {account?.accountStatus ? (
              <Chip
                label={account.accountStatus.toUpperCase()}
                tone={account.accountStatus?.toLowerCase() === 'active' ? 'success' : 'warning'}
              />
            ) : null}
          </View>

          {accountLoading && (
            <View style={styles.centerRow}>
              <ActivityIndicator color={C.primary} />
              <Text style={styles.sub}>  Loading account…</Text>
            </View>
          )}

          {!accountLoading && account && (
            <>
              <View style={styles.grid}>
                <View style={[styles.gridCell, styles.gridCellTopLeft]}>
                  <Text style={styles.label}>Portfolio Value</Text>
                  <Money>{account.portfolioValue}</Money>
                </View>
                <View style={[styles.gridCell, styles.gridCellTopRight]}>
                  <Text style={styles.label}>Equity</Text>
                  <Money>{account.equity}</Money>
                </View>
                <View style={[styles.gridCell, styles.gridCellMiddleLeft]}>
                  <Text style={styles.label}>Buying Power</Text>
                  <Money>{account.buyingPower}</Money>
                </View>
                <View style={[styles.gridCell, styles.gridCellMiddleRight]}>
                  <Text style={styles.label}>Cash</Text>
                  <Money>{account.cash}</Money>
                </View>
                <View style={[styles.gridCell, styles.gridCellBottomLeft]}>
                  <Text style={styles.label}>DT Buying Power</Text>
                  <Money>{account.dayTradingBuyingPower}</Money>
                </View>
                <View style={[styles.gridCell, styles.gridCellBottomRight]}>
                  <Text style={styles.label}>Day Trading</Text>
                  <Text style={[styles.value, { color: account.isDayTradingEnabled ? C.green : C.red }]}>
                    {account.isDayTradingEnabled ? 'Enabled' : 'Disabled'}
                  </Text>
                </View>
              </View>

              {account.tradingBlocked && (
                <View style={styles.alertSoft}>
                  <Icon name="alert-triangle" size={16} color={C.amber} />
                  <Text style={[styles.sub, { marginLeft: 8 }]}>Trading is currently blocked</Text>
                </View>
              )}

              {/* Alpaca Account Status */}
              {alpacaAccount && (
                <View style={styles.alpacaStatusCard}>
                  <View style={styles.alpacaStatusHeader}>
                    <Icon name="shield" size={16} color={alpacaAccount.approvedAt ? C.green : C.amber} />
                    <Text style={styles.alpacaStatusTitle}>Alpaca Account</Text>
                    <Chip
                      label={alpacaAccount.status?.toUpperCase() || 'UNKNOWN'}
                      tone={alpacaAccount.approvedAt ? 'success' : 'warning'}
                    />
                  </View>
                  
                  {!alpacaAccount.approvedAt && (
                    <View style={styles.kycPrompt}>
                      <Text style={styles.kycPromptText}>
                        Complete KYC verification to start trading with real money
                      </Text>
                      <TouchableOpacity 
                        style={styles.kycButton}
                        onPress={() => {
                          Alert.alert(
                            'KYC Verification',
                            'This will open the KYC verification process. You\'ll need to provide identity documents and personal information.',
                            [
                              { text: 'Cancel', style: 'cancel' },
                              { text: 'Start KYC', onPress: () => {
                                // This would navigate to KYC screen
                                Alert.alert('KYC Process', 'KYC verification process would start here.');
                              }}
                            ]
                          );
                        }}
                      >
                        <Text style={styles.kycButtonText}>Start KYC</Text>
                      </TouchableOpacity>
                    </View>
                  )}
                </View>
              )}

              {/* Day Trading Button - Always Visible */}
              <TouchableOpacity 
                style={styles.dayTradingButton}
                onPress={() => navigateTo('day-trading')}
              >
                <View style={styles.dayTradingButtonContent}>
                  <Icon name="trending-up" size={20} color="#fff" />
                  <View style={styles.dayTradingButtonText}>
                    <Text style={styles.dayTradingButtonTitle}>Daily Top-3 Picks</Text>
                    <Text style={styles.dayTradingButtonSubtitle}>AI-powered intraday opportunities</Text>
                  </View>
                  <Icon name="chevron-right" size={20} color="#fff" />
                </View>
              </TouchableOpacity>
            </>
          )}
          {!accountLoading && !account && <Text style={[styles.sub,{textAlign:'center'}]}>Unable to load account data.</Text>}
        </View>

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

        {/* Daily Top-3 Picks - Always Visible */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>Daily Top-3 Picks</Text>
            <View style={styles.modeToggle}>
              {(['SAFE', 'AGGRESSIVE'] as const).map(mode => (
                <TouchableOpacity
                  key={mode}
                  onPress={() => setDayTradingMode(mode)}
                  style={[
                    styles.modeButton,
                    dayTradingMode === mode && styles.modeButtonActive
                  ]}
                >
                  <Text style={[
                    styles.modeButtonText,
                    dayTradingMode === mode && styles.modeButtonTextActive
                  ]}>
                    {mode}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {dayTradingLoading && (
            <View style={styles.centerRow}>
              <ActivityIndicator color={C.primary} />
              <Text style={styles.sub}>  Loading picks…</Text>
            </View>
          )}

          {!dayTradingLoading && dayTradingData?.dayTradingPicks?.picks && (
            <>
              {dayTradingData.dayTradingPicks.picks.slice(0, 3).map((pick, index) => (
                <View key={`${pick.symbol}-${pick.side}`} style={styles.pickCard}>
                  <View style={styles.pickHeader}>
                    <View style={styles.pickSymbolRow}>
                      <Text style={styles.pickSymbol}>{pick.symbol}</Text>
                      <View style={[
                        styles.pickSideChip,
                        { backgroundColor: pick.side === 'LONG' ? C.green : C.red }
                      ]}>
                        <Text style={styles.pickSideText}>{pick.side}</Text>
                      </View>
                    </View>
                    <View style={styles.pickScore}>
                      <Text style={[
                        styles.pickScoreValue,
                        { color: pick.score >= 2 ? C.green : pick.score >= 1 ? C.amber : C.red }
                      ]}>
                        {pick.score.toFixed(2)}
                      </Text>
                      <Text style={styles.pickScoreLabel}>Score</Text>
                    </View>
                  </View>

                  <View style={styles.pickDetails}>
                    <View style={styles.pickDetailRow}>
                      <Text style={styles.pickDetailLabel}>Entry</Text>
                      <Text style={styles.pickDetailValue}>
                        ${(pick.risk.stop + pick.risk.atr5m).toFixed(2)}
                      </Text>
                    </View>
                    <View style={styles.pickDetailRow}>
                      <Text style={styles.pickDetailLabel}>Stop</Text>
                      <Text style={styles.pickDetailValue}>
                        ${pick.risk.stop.toFixed(2)}
                      </Text>
                    </View>
                    <View style={styles.pickDetailRow}>
                      <Text style={styles.pickDetailLabel}>Target</Text>
                      <Text style={styles.pickDetailValue}>
                        {pick.risk.targets?.[0] ? `$${pick.risk.targets[0].toFixed(2)}` : '—'}
                      </Text>
                    </View>
                    <View style={styles.pickDetailRow}>
                      <Text style={styles.pickDetailLabel}>Size</Text>
                      <Text style={styles.pickDetailValue}>
                        {pick.risk.sizeShares} sh
                      </Text>
                    </View>
                  </View>

                  {pick.notes && (
                    <Text style={styles.pickNotes}>{pick.notes}</Text>
                  )}

                  <TouchableOpacity
                    style={[
                      styles.pickExecuteButton,
                      { backgroundColor: pick.side === 'LONG' ? C.green : C.red }
                    ]}
                    onPress={() => {
                      Alert.alert(
                        'Execute Trade',
                        `Execute ${pick.side} ${pick.symbol}?\nEntry≈ $${(pick.risk.stop + pick.risk.atr5m).toFixed(2)}\nStop: $${pick.risk.stop.toFixed(2)}\nTarget: ${pick.risk.targets?.[0] ? `$${pick.risk.targets[0].toFixed(2)}` : '—'}`,
                        [
                          { text: 'Cancel', style: 'cancel' },
                          { text: 'Execute', onPress: () => Alert.alert('Order accepted', 'Simulated execution complete.') },
                        ]
                      );
                    }}
                  >
                    <Text style={styles.pickExecuteText}>Execute {pick.side}</Text>
                  </TouchableOpacity>
                </View>
              ))}

              <TouchableOpacity
                style={styles.viewAllPicksButton}
                onPress={() => navigateTo('day-trading')}
              >
                <Text style={styles.viewAllPicksText}>View All Picks</Text>
                <Icon name="chevron-right" size={16} color={C.primary} />
              </TouchableOpacity>
            </>
          )}

          {!dayTradingLoading && (!dayTradingData?.dayTradingPicks?.picks || dayTradingData.dayTradingPicks.picks.length === 0) && (
            <View style={styles.emptyBlock}>
              <Icon name="trending-up" size={40} color={C.sub} />
              <Text style={styles.emptyTitle}>No picks available</Text>
              <Text style={styles.emptySub}>Check back later for new opportunities.</Text>
            </View>
          )}
        </View>

        {/* Positions Header */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>Positions</Text>
            <TouchableOpacity onPress={onRefresh}>
              <Icon name="refresh-ccw" size={18} color={C.sub} />
            </TouchableOpacity>
          </View>

          {positionsLoading && (
            <View style={styles.centerRow}>
              <ActivityIndicator color={C.primary} />
              <Text style={styles.sub}>  Loading positions…</Text>
            </View>
          )}

          {!positionsLoading && positions.length === 0 && (
            <View style={styles.emptyBlock}>
              <Icon name="briefcase" size={40} color={C.sub} />
              <Text style={styles.emptyTitle}>No positions yet</Text>
              <Text style={styles.emptySub}>Start trading to see positions here.</Text>
            </View>
          )}
        </View>
      </>
    );

    // Create footer component
    const ListFooterComponent = () => (
      <View style={{ height: 16 }} />
    );

    return (
      <FlatList
        style={styles.scroller}
        data={!positionsLoading && positions.length > 0 ? positions : []}
        keyExtractor={(p) => p.id || p.symbol}
        renderItem={({ item }) => <MemoPositionRow position={item} />}
        ItemSeparatorComponent={() => <View style={{ height: 1, backgroundColor: C.line }} />}
        ListHeaderComponent={ListHeaderComponent}
        ListFooterComponent={ListFooterComponent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        showsVerticalScrollIndicator={false}
        initialNumToRender={6}
        windowSize={7}
        removeClippedSubviews
      />
    );
  };

  const renderOrders = () => {
    const all = ordersData?.tradingOrders || [];
    const filtered = all.filter((o: any) => {
      if (orderFilter === 'all') return true;
      if (orderFilter === 'open') return isOpen(o.status);
      return String(o.status).toLowerCase() === orderFilter;
    });

    const sections = groupOrders(filtered);

    return (
      <ScrollView style={styles.scroller} showsVerticalScrollIndicator={false}>
        <View style={styles.card}>
          {/* Header + refresh */}
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>Recent Orders</Text>
            <TouchableOpacity onPress={onRefresh} style={styles.iconBtn}>
              <Icon name="refresh-ccw" size={18} color={C.sub} />
            </TouchableOpacity>
          </View>

          {/* Filter bar */}
          <View style={styles.filterBar}>
            {(['all','open','filled','cancelled'] as const).map(k => (
              <TouchableOpacity
                key={k}
                onPress={() => setOrderFilter(k)}
                style={[styles.filterPill, orderFilter===k && styles.filterPillActive]}
              >
                <Text style={[styles.filterPillText, orderFilter===k && styles.filterPillTextActive]}>
                  {k === 'all' ? 'All' : k === 'open' ? 'Open' : k.charAt(0).toUpperCase()+k.slice(1)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* Loading */}
          {ordersLoading && (
            <View style={styles.skeletonBlock}>
              {[...Array(3)].map((_,i)=>(
                <View key={i} style={styles.skeletonRow}>
                  <View style={styles.skeletonAccent}/>
                  <View style={{ flex:1 }}>
                    <View style={styles.skeletonLineWide}/>
                    <View style={styles.skeletonLine}/>
                    <View style={styles.skeletonLineShort}/>
                  </View>
                </View>
              ))}
            </View>
          )}

          {/* Empty */}
          {!ordersLoading && filtered.length === 0 && (
            <View style={styles.emptyBlock}>
              <Icon name="clipboard" size={44} color={C.sub} />
              <Text style={styles.emptyTitle}>No matching orders</Text>
              <Text style={styles.emptySub}>
                {orderFilter==='all' ? 'Place your first order to get started.' : 'Try a different filter.'}
              </Text>
            </View>
          )}

          {/* Sections */}
          {!ordersLoading && filtered.length > 0 && (
            <>
              {(['Today','This Week','Earlier'] as const).map(label => (
                sections[label].length ? (
                  <View key={label} style={{ marginTop: 8 }}>
                    <Text style={styles.sectionDivider}>{label}</Text>

                    {sections[label].map((o:any, i:number) => {
                      const sideBuy = String(o.side).toLowerCase() === 'buy';
                      const { color: statusColor, icon } = getStatusMeta(o.status);
                      const showCancel = String(o.status).toLowerCase() === 'pending';

                      return (
                        <View key={`${label}-${i}`} style={styles.orderCardRow}>
                          {/* Left accent by side */}
                          <View style={[styles.sideAccent, { backgroundColor: sideBuy ? '#16A34A' : '#DC2626' }]} />

                          <View style={{ flex:1 }}>
                            {/* Top line: Ticker + chips + status */}
                            <View style={styles.rowBetween}>
                              <View style={{ flexDirection:'row', alignItems:'center', gap:8, flexShrink:1 }}>
                                <Text style={styles.ticker}>{o.symbol}</Text>
                                <View style={[styles.badge, styles.badgeInfo]}>
                                  <Text style={styles.badgeText}>{String(o.orderType).toUpperCase()}</Text>
                                </View>
                                <View style={[styles.badge, sideBuy ? styles.badgeSuccess : styles.badgeDanger]}>
                                  <Text style={styles.badgeText}>{String(o.side).toUpperCase()}</Text>
                                </View>
                              </View>

                              <View style={[styles.badge, { backgroundColor: `${statusColor}1A` }]}>
                                <View style={{ flexDirection:'row', alignItems:'center', gap:6 }}>
                                  <Icon name={icon as any} size={14} color={statusColor} />
                                  <Text style={[styles.badgeText, { color: statusColor }]}>{String(o.status).toUpperCase()}</Text>
                                </View>
                              </View>
                            </View>

                            {/* Middle: size / price */}
                            <View style={styles.rowWrap}>
                              <Text style={styles.sub}>{o.quantity} shares</Text>
                              {o.price     ? <Text style={styles.sub}>@ ${o.price.toFixed(2)}</Text> : null}
                              {o.stopPrice ? <Text style={styles.sub}>Stop ${o.stopPrice.toFixed(2)}</Text> : null}
                            </View>

                            {/* Bottom: time + Cancel */}
                            <View style={styles.rowBetween}>
                              <View style={{ flexDirection:'row', alignItems:'center', gap:6 }}>
                                <Icon name="calendar" size={14} color={C.sub} />
                                <Text style={styles.meta}>{fmtTime(o.createdAt)}</Text>
                              </View>
                              {showCancel && (
                                <TouchableOpacity style={styles.ghostDangerBtn} onPress={() => handleCancelOrder(o.id)}>
                                  <Icon name="x-circle" size={14} color="#EF4444" />
                                  <Text style={styles.ghostDangerText}>Cancel</Text>
                                </TouchableOpacity>
                              )}
                            </View>

                            {o.notes ? <Text style={styles.note}>"{o.notes}"</Text> : null}
                          </View>
                        </View>
                      );
                    })}
                  </View>
                ) : null
              ))}
            </>
          )}
        </View>

        <View style={{ height: 16 }} />
      </ScrollView>
    );
  };

  /* ------------------------------- Modal -------------------------------- */

  const renderOrderModal = () => {
    const validationError = validateOrder();
    const disabled = Boolean(validationError) || isPlacingOrder;

    return (
    <Modal visible={showOrderModal} animationType="slide" presentationStyle="pageSheet" onRequestClose={() => setShowOrderModal(false)}>
      <SafeAreaView style={styles.modal}>
        <View style={styles.modalBar} />
        <View style={styles.modalHeader}>
          <Text style={styles.modalTitle}>Place Order</Text>
          <TouchableOpacity onPress={() => setShowOrderModal(false)}><Icon name="x" size={24} color={C.text} /></TouchableOpacity>
        </View>

        <ScrollView style={{ paddingHorizontal:20 }} showsVerticalScrollIndicator={false}>
          {/* Type */}
          <Text style={styles.inputLabel}>Order Type</Text>
          <View style={styles.pillRow}>
            {(['market','limit','stop_loss'] as const).map(t => (
              <TouchableOpacity key={t} onPress={() => setOrderType(t)}
                style={[styles.pill, orderType===t && styles.pillActive]}>
                <Text style={[styles.pillText, orderType===t && styles.pillTextActive]}>{t.replace('_',' ').toUpperCase()}</Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* Side */}
          <Text style={[styles.inputLabel, { marginTop:16 }]}>Side</Text>
          <View style={styles.pillRow}>
            {(['buy','sell'] as const).map(s => (
              <TouchableOpacity key={s} onPress={() => setOrderSide(s)}
                style={[styles.pill, orderSide===s && (s==='buy'?styles.pillBuy:styles.pillSell)]}>
                <Text style={[styles.pillText, orderSide===s && styles.pillTextActive]}>{s.toUpperCase()}</Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* SBLOC Alternative for Sell Orders */}
          {orderSide === 'sell' && (
            <View style={styles.sblocAlternative}>
              <View style={styles.sblocAlternativeHeader}>
                <Icon name="lightbulb" size={16} color="#F59E0B" />
                <Text style={styles.sblocAlternativeTitle}>Consider SBLOC Instead?</Text>
              </View>
              <Text style={styles.sblocAlternativeText}>
                Instead of selling your shares, you could borrow against your portfolio to access liquidity while keeping your investments growing.
              </Text>
              <TouchableOpacity 
                style={styles.sblocAlternativeBtn}
                onPress={() => setShowSBLOCModal(true)}
              >
                <Icon name="trending-up" size={16} color="#F59E0B" />
                <Text style={styles.sblocAlternativeBtnText}>Learn About SBLOC</Text>
              </TouchableOpacity>
            </View>
          )}

          {/* Inputs */}
          <View style={{ marginTop:16 }}>
            <Text style={styles.inputLabel}>Symbol</Text>
            <TextInput
              style={styles.input}
              value={symbol}
              onChangeText={(t) => setSymbol(upper(t))}
              placeholder="e.g., AAPL"
              autoCapitalize="characters"
              autoCorrect={false}
            />
          </View>

          <View style={{ marginTop:12 }}>
            <Text style={styles.inputLabel}>Quantity</Text>
            <TextInput 
              style={styles.input} 
              value={quantity} 
              onChangeText={setQuantity} 
              placeholder="Number of shares" 
              keyboardType="numeric" 
            />
          </View>

          {orderType==='limit' && (
            <View style={{ marginTop:12 }}>
              <Text style={styles.inputLabel}>Limit Price</Text>
              <TextInput style={styles.input} value={price} onChangeText={setPrice} placeholder="Price per share" keyboardType="numeric" />
            </View>
          )}

          {orderType==='stop_loss' && (
            <View style={{ marginTop:12 }}>
              <Text style={styles.inputLabel}>Stop Price</Text>
              <TextInput style={styles.input} value={stopPrice} onChangeText={setStopPrice} placeholder="Stop price" keyboardType="numeric" />
            </View>
          )}

          <View style={{ marginTop:12, marginBottom:16 }}>
            <Text style={styles.inputLabel}>Notes (Optional)</Text>
            <TextInput style={[styles.input, { height:84, textAlignVertical:'top' }]} value={notes} onChangeText={setNotes} multiline placeholder="Add a note about this order" />
          </View>

          {/* Quote */}
          {symbol && quoteData?.tradingQuote && (
            <View style={styles.quoteBox}>
              <Text style={styles.quoteTitle}>Quote • {symbol.toUpperCase()}</Text>
              <View style={styles.rowBetween}><Text style={styles.sub}>Bid</Text><Text style={styles.value}>${quoteData.tradingQuote.bid?.toFixed(2)}</Text></View>
              <View style={styles.rowBetween}><Text style={styles.sub}>Ask</Text><Text style={styles.value}>${quoteData.tradingQuote.ask?.toFixed(2)}</Text></View>
            </View>
          )}

          <TouchableOpacity
            style={[styles.primaryBtn, disabled && { opacity:0.6 }]}
            onPress={handlePlaceOrder}
            disabled={disabled}
          >
            {isPlacingOrder ? <ActivityIndicator color="#fff" /> : <Text style={styles.primaryBtnText}>Place Order</Text>}
          </TouchableOpacity>

          <View style={{ height:24 }} />
        </ScrollView>
      </SafeAreaView>
    </Modal>
    );
  };

  /* ------------------------------ RENDER -------------------------------- */

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigateTo('home')} hitSlop={{ top:8,left:8,bottom:8,right:8 }}>
          <Icon name="arrow-left" size={22} color={C.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Trading</Text>
        <TouchableOpacity onPress={() => setShowOrderModal(true)} style={styles.headerAction}>
          <Icon name="plus" size={20} color={C.primary} />
          <Text style={styles.headerActionText}>Order</Text>
        </TouchableOpacity>
      </View>

      {/* Tabs */}
      <View style={styles.tabs}>
        {(['overview','orders'] as const).map(t => (
          <TouchableOpacity key={t} onPress={() => setActiveTab(t)} style={[styles.tabPill, activeTab===t && styles.tabPillActive]}>
            <Text style={[styles.tabPillText, activeTab===t && styles.tabPillTextActive]}>
              {t[0].toUpperCase()+t.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Content */}
      <View style={{ flex:1 }}>
        {activeTab === 'overview' ? renderOverview() : renderOrders()}
      </View>

      {renderOrderModal()}

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
  );
};

/* ----------------------------- Position Row Component ----------------------------- */

const PositionRow = ({ position }: { position: any }) => {
  const isUp = (Number(position?.unrealizedPl) ?? 0) >= 0;
  const { data: chartData } = useQuery(GET_STOCK_CHART_DATA, {
    variables: { symbol: position.symbol, timeframe: '1D' },
    errorPolicy: 'all',
    fetchPolicy: 'cache-first',
  });

  const chartPrices = chartData?.stockChartData?.data?.map((d: any) => d.close) || [];
  
  // Normalize inconsistent server fields
  const plPct = Number(position.unrealizedPlpc ?? position.unrealizedPLPercent ?? 0);

  return (
    <View style={styles.positionRow}>
      <View style={styles.tickerAvatar}>
        <Text style={styles.tickerAvatarText}>{position.symbol?.[0]}</Text>
      </View>

      <View style={{ flex: 1, paddingRight: 8 }}>
        <View style={styles.rowBetween}>
          <Text style={styles.ticker}>{position.symbol}</Text>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
            <SparkMini 
              data={chartPrices} 
              width={70} 
              height={18} 
              upColor={C.green}
              downColor={C.red}
              neutralColor={C.sub}
            />
            <Chip 
              label={`${isUp?'+':''}${plPct.toFixed(2)}%`} 
              tone={isUp ? 'success' : 'danger'} 
            />
          </View>
        </View>

        <View style={styles.rowBetween}>
          <Text style={styles.sub}>{position.quantity} shares  •  @ ${position.currentPrice?.toFixed(2)}</Text>
          <Text style={[styles.value, { color: isUp ? C.green : C.red }]}>
            {isUp?'+':''}${position.unrealizedPl?.toFixed(2)}
          </Text>
        </View>

        <View style={styles.rowBetween}>
          <Text style={styles.sub}>Value</Text>
          <Text style={styles.value}>${position.marketValue?.toLocaleString()}</Text>
        </View>
      </View>
    </View>
  );
};

/* -------------------------------- Styles -------------------------------- */

const styles = StyleSheet.create({
  container: { flex:1, backgroundColor: C.bg },

  header: {
    flexDirection:'row', alignItems:'center', justifyContent:'space-between',
    paddingHorizontal:16, paddingVertical:12, backgroundColor: C.card,
    borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: C.line,
    shadowColor: C.shadow, shadowOpacity: 1, shadowRadius: 8, shadowOffset: { width:0, height:2 }, elevation:2,
  },
  headerTitle: { fontSize:18, fontWeight:'700', color: C.text },
  headerAction: { flexDirection:'row', alignItems:'center', gap:6, paddingHorizontal:10, paddingVertical:6, borderRadius:8, backgroundColor:'#F4F7FF' },
  headerActionText: { color: C.primary, fontWeight:'700' },

  tabs: {
    flexDirection:'row', backgroundColor: C.bg, padding:12, gap:8,
  },
  tabPill: {
    flex:1, paddingVertical:10, borderRadius:999, alignItems:'center',
    backgroundColor:'#E9EDF7',
  },
  tabPillActive: { backgroundColor: C.card, borderWidth:1, borderColor: C.line },
  tabPillText: { color:'#5B6473', fontWeight:'600' },
  tabPillTextActive: { color: C.text },

  scroller: { paddingHorizontal:16 },

  card: {
    backgroundColor: C.card, borderRadius:16, padding:16, marginTop:12,
    shadowColor: C.shadow, shadowOpacity:1, shadowRadius:10, shadowOffset:{width:0,height:2}, elevation:2,
  },
  cardHeader: { flexDirection:'row', alignItems:'center', justifyContent:'space-between', marginBottom:8 },
  cardTitle: { fontSize:16, fontWeight:'700', color: C.text },

  grid: {
    flexDirection:'row', flexWrap:'wrap', borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: C.line, marginTop:8,
  },
  gridCell: {
    width: (width - 16*2 - 1) / 2, paddingVertical:12, paddingHorizontal:12,
  },
  gridCellTopLeft: {
    borderRightWidth: StyleSheet.hairlineWidth, borderRightColor: C.line,
    borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: C.line,
  },
  gridCellTopRight: {
    borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: C.line,
  },
  gridCellMiddleLeft: {
    borderRightWidth: StyleSheet.hairlineWidth, borderRightColor: C.line,
    borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: C.line,
  },
  gridCellMiddleRight: {
    borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: C.line,
  },
  gridCellBottomLeft: {
    borderRightWidth: StyleSheet.hairlineWidth, borderRightColor: C.line,
  },
  gridCellBottomRight: {
    // No borders for bottom right
  },

  row: { flexDirection:'row', alignItems:'center', justifyContent:'space-between', paddingVertical:8 },
  rowBetween: { flexDirection:'row', alignItems:'center', justifyContent:'space-between', marginTop:6 },
  rowWrap: { flexDirection:'row', alignItems:'center', flexWrap:'wrap', gap:8, marginTop:6 },

  label: { fontSize:12, color: C.sub },
  value: { fontSize:16, fontWeight:'700', color: C.text },
  sub: { fontSize:13, color: C.sub },

  chip: { paddingHorizontal:10, paddingVertical:4, borderRadius:999, alignSelf:'flex-start' },
  chipText: { fontSize:11, fontWeight:'700' },

  centerRow: { flexDirection:'row', alignItems:'center', justifyContent:'center', paddingVertical:12 },

  alertSoft: {
    marginTop:12, padding:12, borderRadius:12, backgroundColor:'#FFF7E6', flexDirection:'row', alignItems:'center'
  },

  /* Positions */
  positionRow: {
    flexDirection:'row', gap:12, paddingVertical:12, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: C.line,
  },
  tickerAvatar: {
    width:40, height:40, borderRadius:8, backgroundColor:'#EEF2FF', alignItems:'center', justifyContent:'center',
  },
  tickerAvatarText: { fontWeight:'800', color: C.primary },
  ticker: { fontSize:16, fontWeight:'800', color: C.text },

  /* Orders */
  orderRow: {
    paddingVertical:12, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: C.line,
  },
  smallDangerBtn: {
    backgroundColor: C.red, paddingHorizontal:10, paddingVertical:6, borderRadius:8,
  },
  smallDangerText: { color:'#fff', fontSize:12, fontWeight:'700' },
  note: { marginTop:6, fontStyle:'italic', color: C.sub, fontSize:12 },

  /* Empty */
  emptyBlock: { alignItems:'center', paddingVertical:24, gap:6 },
  emptyTitle: { fontWeight:'700', color: C.text, fontSize:16 },
  emptySub: { color: C.sub },

  /* Modal */
  modal: { flex:1, backgroundColor: C.bg },
  modalBar: { alignSelf:'center', width:40, height:4, backgroundColor:'#D1D5DB', borderRadius:999, marginTop:8, marginBottom:4 },
  modalHeader: {
    flexDirection:'row', alignItems:'center', justifyContent:'space-between',
    paddingHorizontal:20, paddingVertical:12, backgroundColor: C.card, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: C.line,
  },
  modalTitle: { fontSize:18, fontWeight:'800', color: C.text },

  inputLabel: { fontWeight:'700', color: C.text, marginBottom:6 },
  input: { backgroundColor: C.card, borderWidth:1, borderColor: C.line, borderRadius:10, paddingHorizontal:14, paddingVertical:12, fontSize:16 },

  pillRow: { flexDirection:'row', gap:8 },
  pill: { flex:1, paddingVertical:10, borderRadius:999, alignItems:'center', backgroundColor:'#EEF2F7' },
  pillActive: { backgroundColor: C.primary },
  pillBuy: { backgroundColor: C.green },
  pillSell: { backgroundColor: C.red },
  pillText: { fontWeight:'700', color:'#5B6473' },
  pillTextActive: { color:'#fff' },

  quoteBox: { backgroundColor: C.blueSoft, borderRadius:12, padding:12, marginTop:8, gap:6 },
  quoteTitle: { fontWeight:'800', color: C.text, marginBottom:4 },

  primaryBtn: { backgroundColor: C.primary, paddingVertical:16, borderRadius:12, alignItems:'center', marginTop:16 },
  primaryBtnText: { color:'#fff', fontSize:16, fontWeight:'800' },

  // Filter
  filterBar: {
    flexDirection: 'row',
    gap: 8,
    paddingHorizontal: 4,
    paddingBottom: 8,
  },
  filterPill: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 14,
    backgroundColor: '#F3F4F6',
  },
  filterPillActive: {
    backgroundColor: '#E0ECFF',
  },
  filterPillText: {
    fontSize: 13,
    color: '#6B7280',
    fontWeight: '600',
  },
  filterPillTextActive: {
    color: '#1D4ED8',
  },

  // Order row
  orderCardRow: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 14,
    marginTop: 10,
    shadowColor: '#000',
    shadowOpacity: 0.06,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 6,
    elevation: 2,
  },
  sideAccent: {
    width: 4,
    borderRadius: 6,
    marginRight: 12,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 999,
    backgroundColor: '#EEF2FF',
  },
  badgeText: { fontSize: 11, fontWeight: '700', color: '#1F2937' },
  badgeInfo: { backgroundColor: '#E3F2FD' },
  badgeSuccess: { backgroundColor: '#E7F7EE' },
  badgeDanger: { backgroundColor: '#FDECEC' },

  meta: { fontSize: 12, color: C.sub },

  // Section label
  sectionDivider: {
    fontSize: 12,
    fontWeight: '700',
    color: '#6B7280',
    marginTop: 12,
    marginBottom: 2,
    paddingHorizontal: 2,
    letterSpacing: 0.3,
    textTransform: 'uppercase',
  },

  // Buttons
  ghostDangerBtn: {
    flexDirection:'row',
    alignItems:'center',
    gap:6,
    paddingHorizontal:10,
    paddingVertical:6,
    borderRadius: 8,
    backgroundColor: '#FEE2E2',
  },
  ghostDangerText: { color:'#EF4444', fontWeight:'700', fontSize:12 },

  iconBtn: { padding: 6, borderRadius: 8, backgroundColor: '#F3F4F6' },

  // Skeleton
  skeletonBlock: { paddingTop: 8 },
  skeletonRow: {
    flexDirection:'row',
    gap:12,
    backgroundColor:'#fff',
    padding:14,
    borderRadius:12,
    marginTop:10,
  },
  skeletonAccent:{ width:4, borderRadius:6, backgroundColor:'#E5E7EB' },
  skeletonLineWide:{ height:12, backgroundColor:'#E5E7EB', borderRadius:6, marginBottom:8, width:'60%' },
  skeletonLine:{ height:10, backgroundColor:'#E5E7EB', borderRadius:6, marginBottom:8, width:'40%' },
  skeletonLineShort:{ height:10, backgroundColor:'#E5E7EB', borderRadius:6, width:'28%' },

  // SBLOC Alternative styles
  sblocAlternative: {
    backgroundColor: '#FEF3C7',
    borderRadius: 12,
    padding: 16,
    marginTop: 16,
    borderWidth: 1,
    borderColor: '#FDE68A',
  },
  sblocAlternativeHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  sblocAlternativeTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#92400E',
    marginLeft: 8,
  },
  sblocAlternativeText: {
    fontSize: 14,
    color: '#92400E',
    lineHeight: 20,
    marginBottom: 12,
  },
  sblocAlternativeBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F59E0B',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  sblocAlternativeBtnText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
    marginLeft: 6,
  },

  // Day Trading Button
  dayTradingButton: {
    marginTop: 16,
    backgroundColor: '#2196F3',
    borderRadius: 12,
    padding: 16,
  },
  dayTradingButtonContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  dayTradingButtonText: {
    flex: 1,
    marginLeft: 12,
  },
  dayTradingButtonTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 2,
  },
  dayTradingButtonSubtitle: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.8)',
  },

  // Daily Picks Styles
  modeToggle: {
    flexDirection: 'row',
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
    padding: 2,
  },
  modeButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  modeButtonActive: {
    backgroundColor: '#FFFFFF',
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowOffset: { width: 0, height: 1 },
    shadowRadius: 2,
    elevation: 1,
  },
  modeButtonText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6B7280',
  },
  modeButtonTextActive: {
    color: '#1F2937',
  },
  pickCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 14,
    marginTop: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    shadowColor: '#000',
    shadowOpacity: 0.04,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 4,
    elevation: 1,
  },
  pickHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  pickSymbolRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  pickSymbol: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1F2937',
  },
  pickSideChip: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  pickSideText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '700',
  },
  pickScore: {
    alignItems: 'center',
  },
  pickScoreValue: {
    fontSize: 18,
    fontWeight: '700',
  },
  pickScoreLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
  pickDetails: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  pickDetailRow: {
    width: '48%',
    marginBottom: 8,
  },
  pickDetailLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 2,
  },
  pickDetailValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1F2937',
  },
  pickNotes: {
    fontSize: 12,
    color: '#6B7280',
    fontStyle: 'italic',
    marginBottom: 12,
    lineHeight: 16,
  },
  pickExecuteButton: {
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  pickExecuteText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
  viewAllPicksButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    marginTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  viewAllPicksText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#0E7AFE',
    marginRight: 4,
  },

  // Alpaca Account Status Styles
  alpacaStatusCard: {
    backgroundColor: '#F8FAFC',
    borderRadius: 12,
    padding: 16,
    marginTop: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  alpacaStatusHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  alpacaStatusTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: C.text,
    marginLeft: 8,
    flex: 1,
  },
  kycPrompt: {
    marginTop: 8,
    padding: 12,
    backgroundColor: '#FEF3C7',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#FDE68A',
  },
  kycPromptText: {
    fontSize: 13,
    color: '#92400E',
    marginBottom: 8,
    lineHeight: 18,
  },
  kycButton: {
    backgroundColor: '#F59E0B',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 6,
    alignSelf: 'flex-start',
  },
  kycButtonText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '600',
  },

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

// Memoized version for performance
const MemoPositionRow = React.memo(PositionRow);

export default TradingScreen;