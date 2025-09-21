import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  Modal,
  ActivityIndicator,
  RefreshControl,
  SafeAreaView,
  Dimensions,
} from 'react-native';
import { useQuery, useMutation } from '@apollo/client';
import { gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import SparkMini from '../../../components/charts/SparkMini';
import SBLOCCalculator from '../../../components/forms/SBLOCCalculator';

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
      timeframe
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

const PLACE_MARKET_ORDER = gql`
  mutation PlaceMarketOrder($symbol: String!, $quantity: Int!, $side: String!, $notes: String) {
    placeMarketOrder(symbol: $symbol, quantity: $quantity, side: $side, notes: $notes) {
      success
      order { id symbol side orderType quantity status createdAt notes }
    }
  }
`;

const PLACE_LIMIT_ORDER = gql`
  mutation PlaceLimitOrder($symbol: String!, $quantity: Int!, $side: String!, $limitPrice: Float!, $notes: String) {
    placeLimitOrder(symbol: $symbol, quantity: $quantity, side: $side, limitPrice: $limitPrice, notes: $notes) {
      success
      order { id symbol side orderType quantity price status createdAt notes }
    }
  }
`;

const PLACE_STOP_LOSS_ORDER = gql`
  mutation PlaceStopLossOrder($symbol: String!, $quantity: Int!, $side: String!, $stopPrice: Float!, $notes: String) {
    placeStopLossOrder(symbol: $symbol, quantity: $quantity, side: $side, stopPrice: $stopPrice, notes: $notes) {
      success
      order { id symbol side orderType quantity stopPrice status createdAt notes }
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

const Money = ({ children }: { children: number | undefined }) => (
  <Text style={styles.value}>
    {typeof children === 'number' ? `$${children.toLocaleString()}` : '$0.00'}
  </Text>
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

const FieldRow = ({ label, value, hint, tone }:{
  label: string; value: React.ReactNode; hint?: string; tone?: 'neutral'|'success'|'danger'
}) => (
  <View style={styles.row}>
    <Text style={styles.label}>{label}</Text>
    <View style={{ flexDirection:'row', alignItems:'center', gap:8 }}>
      {hint ? <Chip label={hint} tone={tone || 'neutral'} /> : null}
      <Text style={styles.value}>{value}</Text>
    </View>
  </View>
);

/* ------------------------------ Component ------------------------------ */

/* ----------------------------- Helpers ------------------------------ */

// Status meta (color + icon)
const getStatusMeta = (status: string) => {
  const s = status?.toLowerCase();
  if (s === 'filled')   return { color: '#22C55E', icon: 'check-circle' };
  if (s === 'pending')  return { color: '#F59E0B', icon: 'clock' };
  if (s === 'rejected') return { color: '#EF4444', icon: 'x-circle' };
  if (s === 'cancelled')return { color: '#9CA3AF', icon: 'slash' };
  return { color: '#9CA3AF', icon: 'more-horizontal' };
};

// "open" = actionable
const isOpen = (s: string) => ['pending','accepted','new','open'].includes(String(s).toLowerCase());

// Groups: Today / This Week / Earlier
const groupOrders = (orders: any[]) => {
  const today = new Date();
  const startOfDay = new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime();
  const startOfWeek = (d => {
    const day = d.getDay(); // 0..6
    const diff = d.getDate() - day; // Sunday week
    return new Date(d.getFullYear(), d.getMonth(), diff).getTime();
  })(today);

  const buckets: Record<string, any[]> = { 'Today': [], 'This Week': [], 'Earlier': [] };
  for (const o of orders) {
    const t = new Date(o.createdAt).getTime();
    if (t >= startOfDay) buckets['Today'].push(o);
    else if (t >= startOfWeek) buckets['This Week'].push(o);
    else buckets['Earlier'].push(o);
  }
  return buckets;
};

// Nicely formatted timestamp (short)
const fmtTime = (iso: string) => {
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, { month:'short', day:'2-digit', hour:'2-digit', minute:'2-digit' }).replace(',', '');
  } catch { return iso; }
};

const TradingScreen = ({ navigateTo }: any) => {
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

  const { data: accountData, loading: accountLoading, refetch: refetchAccount } = useQuery(GET_TRADING_ACCOUNT, { errorPolicy: 'all' });
  const { data: positionsData, loading: positionsLoading, refetch: refetchPositions } = useQuery(GET_TRADING_POSITIONS, { errorPolicy: 'all' });
  const { data: ordersData, loading: ordersLoading, refetch: refetchOrders } = useQuery(GET_TRADING_ORDERS, { variables: { limit: 20 }, errorPolicy: 'all' });
  const { data: quoteData, refetch: refetchQuote } = useQuery(GET_TRADING_QUOTE, { variables: { symbol: symbol || 'AAPL' }, skip: !symbol, errorPolicy: 'all' });

  const [placeMarketOrder]   = useMutation(PLACE_MARKET_ORDER);
  const [placeLimitOrder]    = useMutation(PLACE_LIMIT_ORDER);
  const [placeStopLossOrder] = useMutation(PLACE_STOP_LOSS_ORDER);
  const [cancelOrder]        = useMutation(CANCEL_ORDER);

  const onRefresh = async () => {
    setRefreshing(true);
    try {
      await Promise.all([refetchAccount(), refetchPositions(), refetchOrders(), refetchQuote()]);
    } finally { setRefreshing(false); }
  };

  const handlePlaceOrder = async () => {
    if (!symbol || !quantity) return Alert.alert('Error', 'Please enter symbol and quantity');
    
    // SBLOC nudge for sell orders with unrealized gains
    if (orderSide === 'sell') {
      const position = positionsData?.tradingPositions?.find((p: any) => p.symbol === symbol.toUpperCase());
      if (position && position.unrealizedPl > 0) {
        Alert.alert(
          'Need cash without selling?',
          'You may be eligible to borrow against your portfolio via an SBLOC, avoiding a taxable sale.',
          [
            { text: 'Keep Selling', style: 'destructive', onPress: proceedWithSell },
            { text: 'Learn / Borrow', onPress: () => setShowSBLOCModal(true) }
          ]
        );
        return;
      }
    }
    
    proceedWithSell();
  };

  const proceedWithSell = async () => {
    setIsPlacingOrder(true);
    try {
      const orderNotes = notes || 'Placed via RichesReach app';
      let result: any;

      if (orderType === 'market') {
        result = await placeMarketOrder({ variables:{ symbol: symbol.toUpperCase(), quantity: parseInt(quantity), side: orderSide, notes: orderNotes } });
      } else if (orderType === 'limit') {
        if (!price) return Alert.alert('Error','Please enter limit price');
        result = await placeLimitOrder({ variables:{ symbol: symbol.toUpperCase(), quantity: parseInt(quantity), side: orderSide, limitPrice: parseFloat(price), notes: orderNotes } });
      } else {
        if (!stopPrice) return Alert.alert('Error','Please enter stop price');
        result = await placeStopLossOrder({ variables:{ symbol: symbol.toUpperCase(), quantity: parseInt(quantity), side: orderSide, stopPrice: parseFloat(stopPrice), notes: orderNotes } });
      }

      const key = `place${orderType.replace('_','').replace(/^./, c=>c.toUpperCase())}Order`;
      if (result?.data?.[key]?.success) {
        Alert.alert('Order Placed', `Your ${orderType.replace('_',' ')} order for ${quantity} ${symbol.toUpperCase()} is in.`);
        setShowOrderModal(false); resetOrderForm(); refetchOrders();
      } else {
        Alert.alert('Error','Failed to place order');
      }
    } catch (e) {
      Alert.alert('Error','Failed to place order. Please try again.');
    } finally { setIsPlacingOrder(false); }
  };

  const resetOrderForm = () => {
    setSymbol(''); setQuantity(''); setPrice(''); setStopPrice(''); setNotes(''); setOrderType('market'); setOrderSide('buy');
  };

  const handleCancelOrder = async (orderId: string) => {
    try {
      const result = await cancelOrder({ variables: { orderId } });
      if (result?.data?.cancelOrder?.success) {
        Alert.alert('Order Cancelled', 'Your order has been cancelled successfully.');
        refetchOrders();
      } else {
        Alert.alert('Error', 'Failed to cancel order. Please try again.');
      }
    } catch (e) {
      Alert.alert('Error', 'Failed to cancel order. Please try again.');
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

  const account = accountData?.tradingAccount;
  const positions = positionsData?.tradingPositions || [];
  const orders = ordersData?.tradingOrders || [];

  const renderOverview = () => (
    <ScrollView
      style={styles.scroller}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      showsVerticalScrollIndicator={false}
    >
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
          </>
        )}
        {!accountLoading && !account && <Text style={[styles.sub,{textAlign:'center'}]}>Unable to load account data.</Text>}
      </View>

      {/* Positions */}
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

        {!positionsLoading && positions.map((p: any, idx: number) => {
          const up = p.unrealizedPl >= 0;
          return (
            <PositionRow key={p.id || p.symbol || `position-${idx}`} position={p} isUp={up} />
          );
        })}
      </View>

      <View style={{ height: 16 }} />
    </ScrollView>
  );

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

  const renderOrderModal = () => (
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
            <TextInput style={styles.input} value={symbol} onChangeText={setSymbol} placeholder="e.g., AAPL" autoCapitalize="characters" />
          </View>

          <View style={{ marginTop:12 }}>
            <Text style={styles.inputLabel}>Quantity</Text>
            <TextInput style={styles.input} value={quantity} onChangeText={setQuantity} placeholder="Number of shares" keyboardType="numeric" />
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

          <TouchableOpacity style={[styles.primaryBtn, isPlacingOrder && { opacity:0.7 }]} onPress={handlePlaceOrder} disabled={isPlacingOrder}>
            {isPlacingOrder ? <ActivityIndicator color="#fff" /> : <Text style={styles.primaryBtnText}>Place Order</Text>}
          </TouchableOpacity>

          <View style={{ height:24 }} />
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );

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

const PositionRow = ({ position, isUp }: { position: any; isUp: boolean }) => {
  const { data: chartData } = useQuery(GET_STOCK_CHART_DATA, {
    variables: { symbol: position.symbol, timeframe: '1D' },
    errorPolicy: 'all',
    fetchPolicy: 'cache-first',
  });

  const chartPrices = chartData?.stockChartData?.data?.map((d: any) => d.close) || [];

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
              label={`${isUp?'+':''}${position.unrealizedPlpc?.toFixed(2)}%`} 
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
});

export default TradingScreen;