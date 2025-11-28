/**
 * Paper Trading Screen - Simulated trading without real money
 * 
 * Features:
 * - $100k starting balance (paper money)
 * - Buy/sell orders (market and limit)
 * - Position tracking with real-time P&L
 * - Trade history
 * - Win rate statistics
 */
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { useQuery, useMutation, gql } from '@apollo/client';
import { useColorScheme } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '../../../contexts/AuthContext';
import Icon from 'react-native-vector-icons/Feather';

// GraphQL Queries
const GET_PAPER_ACCOUNT_SUMMARY = gql`
  query GetPaperAccountSummary {
    paperAccountSummary {
      account {
        id
        initialBalance
        currentBalance
        totalValue
        realizedPnl
        unrealizedPnl
        totalPnl
        totalPnlPercent
        totalTrades
        winningTrades
        losingTrades
        winRate
      }
      positions {
        id
        stockSymbol
        stockName
        shares
        averagePrice
        currentPrice
        costBasis
        marketValue
        unrealizedPnl
        unrealizedPnlPercent
      }
      openOrders {
        id
        stockSymbol
        stockName
        side
        orderType
        quantity
        limitPrice
        filledPrice
        status
        createdAt
      }
      recentTrades {
        id
        stockSymbol
        stockName
        side
        quantity
        price
        totalValue
        realizedPnl
        realizedPnlPercent
        createdAt
      }
      statistics {
        totalTrades
        winningTrades
        losingTrades
        winRate
        totalPnl
        totalPnlPercent
        realizedPnl
        unrealizedPnl
      }
    }
  }
`;

const PLACE_PAPER_ORDER = gql`
  mutation PlacePaperOrder(
    $symbol: String!
    $side: String!
    $quantity: Int!
    $orderType: String
    $limitPrice: Float
  ) {
    placePaperOrder(
      symbol: $symbol
      side: $side
      quantity: $quantity
      orderType: $orderType
      limitPrice: $limitPrice
    ) {
      success
      message
      order {
        id
        stockSymbol
        side
        quantity
        filledPrice
        status
      }
    }
  }
`;

const CANCEL_PAPER_ORDER = gql`
  mutation CancelPaperOrder($orderId: Int!) {
    cancelPaperOrder(orderId: $orderId) {
      success
      message
    }
  }
`;

interface PaperTradingScreenProps {
  navigation?: any;
}

export default function PaperTradingScreen({ navigation: propNavigation }: PaperTradingScreenProps) {
  const navigation = useNavigation<any>();
  const { logout } = useAuth();
  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';
  
  const [refreshing, setRefreshing] = useState(false);
  const [orderSymbol, setOrderSymbol] = useState('');
  const [orderQuantity, setOrderQuantity] = useState('');
  const [orderSide, setOrderSide] = useState<'BUY' | 'SELL'>('BUY');
  const [orderType, setOrderType] = useState<'MARKET' | 'LIMIT'>('MARKET');
  const [limitPrice, setLimitPrice] = useState('');
  const [showOrderForm, setShowOrderForm] = useState(false);
  const [loadingTimeout, setLoadingTimeout] = useState(false);

  const { data, loading, error, refetch } = useQuery(GET_PAPER_ACCOUNT_SUMMARY, {
    fetchPolicy: 'network-only', // Always fetch from network, don't use cache
    errorPolicy: 'all', // Return both data and errors
    notifyOnNetworkStatusChange: true,
    // Skip polling to avoid multiple requests
    pollInterval: 0,
  });

  // Add manual timeout to prevent infinite loading
  useEffect(() => {
    if (loading && !data && !error) {
      const timeout = setTimeout(() => {
        console.warn('⚠️ Paper Trading query timeout - forcing loading state to false');
        setLoadingTimeout(true);
      }, 8000); // 8 second timeout
      
      return () => clearTimeout(timeout);
    } else {
      setLoadingTimeout(false);
    }
  }, [loading, data, error]);

  const [placeOrder, { loading: placingOrder }] = useMutation(PLACE_PAPER_ORDER, {
    refetchQueries: [{ query: GET_PAPER_ACCOUNT_SUMMARY }],
    onCompleted: (data) => {
      if (data.placePaperOrder.success) {
        Alert.alert('Success', 'Order placed successfully!');
        setOrderSymbol('');
        setOrderQuantity('');
        setLimitPrice('');
        setShowOrderForm(false);
      } else {
        Alert.alert('Error', data.placePaperOrder.message);
      }
    },
    onError: (error) => {
      Alert.alert('Error', error.message);
    },
  });

  const [cancelOrder] = useMutation(CANCEL_PAPER_ORDER, {
    refetchQueries: [{ query: GET_PAPER_ACCOUNT_SUMMARY }],
    onCompleted: (data) => {
      if (data.cancelPaperOrder.success) {
        Alert.alert('Success', 'Order cancelled');
      } else {
        Alert.alert('Error', data.cancelPaperOrder.message);
      }
    },
  });

  const onRefresh = React.useCallback(() => {
    setRefreshing(true);
    refetch().finally(() => setRefreshing(false));
  }, [refetch]);

  const handlePlaceOrder = () => {
    if (!orderSymbol || !orderQuantity) {
      Alert.alert('Error', 'Please enter symbol and quantity');
      return;
    }

    const quantity = parseInt(orderQuantity);
    if (isNaN(quantity) || quantity <= 0) {
      Alert.alert('Error', 'Quantity must be a positive number');
      return;
    }

    if (orderType === 'LIMIT' && !limitPrice) {
      Alert.alert('Error', 'Limit price required for limit orders');
      return;
    }

    placeOrder({
      variables: {
        symbol: orderSymbol.toUpperCase(),
        side: orderSide,
        quantity,
        orderType,
        limitPrice: limitPrice ? parseFloat(limitPrice) : null,
      },
    });
  };

  const handleCancelOrder = (orderId: number) => {
    Alert.alert(
      'Cancel Order',
      'Are you sure you want to cancel this order?',
      [
        { text: 'No', style: 'cancel' },
        {
          text: 'Yes',
          onPress: () => {
            cancelOrder({ variables: { orderId } });
          },
        },
      ]
    );
  };

  const account = data?.paperAccountSummary?.account;
  const positions = data?.paperAccountSummary?.positions || [];
  const openOrders = data?.paperAccountSummary?.openOrders || [];
  const recentTrades = data?.paperAccountSummary?.recentTrades || [];
  const statistics = data?.paperAccountSummary?.statistics;
  
  // If no account data, create a default account for display
  const defaultAccount = {
    id: '1',
    initialBalance: 100000,
    currentBalance: 100000,
    totalValue: 100000,
    realizedPnl: 0,
    unrealizedPnl: 0,
    totalPnl: 0,
    totalPnlPercent: 0,
    totalTrades: 0,
    winningTrades: 0,
    losingTrades: 0,
    winRate: 0,
  };
  
  const displayAccount = account || defaultAccount;

  const styles = createStyles(isDark);

  // Show loading only if actually loading and haven't timed out
  const isActuallyLoading = loading && !data && !error && !loadingTimeout;
  
  if (isActuallyLoading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#00cc99" />
        <Text style={styles.loadingText}>Loading paper trading account...</Text>
      </View>
    );
  }

  // If timed out, show error
  if (loadingTimeout && !data && !error) {
    return (
      <View style={styles.container}>
        <Icon name="alert-circle" size={48} color="#ff4444" />
        <Text style={styles.errorText}>Request Timeout</Text>
        <Text style={styles.errorDetail}>
          The request took too long to complete. This might be due to network issues or authentication problems.
        </Text>
        <TouchableOpacity style={styles.retryButton} onPress={() => {
          setLoadingTimeout(false);
          refetch();
        }}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.container}>
        <Icon name="alert-circle" size={48} color="#ff4444" />
        <Text style={styles.errorText}>Error loading account</Text>
        <Text style={styles.errorDetail}>{error.message}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={() => refetch()}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // Handle case where query succeeds but returns null (unauthenticated)
  // Also handle case where data exists but paperAccountSummary is null
  // OR if we've timed out
  if ((!loading || loadingTimeout) && (data?.paperAccountSummary === null || (!data && !error))) {
    return (
      <View style={styles.container}>
        <Icon name="lock" size={48} color="#ff9500" />
        <Text style={styles.errorText}>Authentication Required</Text>
        <Text style={styles.errorDetail}>
          Please log in to access Paper Trading. This feature requires an authenticated account.
        </Text>
        <TouchableOpacity 
          style={styles.retryButton} 
          onPress={async () => {
            try {
              // Clear invalid token and trigger login screen
              await logout();
              // App.tsx will automatically show login screen when isAuthenticated becomes false
            } catch (error) {
              console.error('Logout error:', error);
              Alert.alert(
                'Authentication Required',
                'Please log in to access Paper Trading. You may need to restart the app.',
                [{ text: 'OK' }]
              );
            }
          }}
        >
          <Text style={styles.retryButtonText}>Go to Login</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Paper Trading</Text>
        <Text style={styles.subtitle}>Practice trading with $100,000 virtual money</Text>
      </View>

      {/* Account Summary */}
      {displayAccount && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Account Balance</Text>
          <View style={styles.balanceRow}>
            <View>
              <Text style={styles.balanceLabel}>Cash</Text>
              <Text style={styles.balanceValue}>
                ${parseFloat(displayAccount.currentBalance || 100000).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </Text>
            </View>
            <View>
              <Text style={styles.balanceLabel}>Total Value</Text>
              <Text style={styles.balanceValue}>
                ${parseFloat(displayAccount.totalValue || 100000).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </Text>
            </View>
          </View>
          <View style={styles.pnlRow}>
            <View>
              <Text style={styles.pnlLabel}>Total P&L</Text>
              <Text style={[styles.pnlValue, parseFloat(displayAccount.totalPnl || 0) >= 0 ? styles.profit : styles.loss]}>
                {parseFloat(displayAccount.totalPnl || 0) >= 0 ? '+' : ''}
                ${parseFloat(displayAccount.totalPnl || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                {' '}
                ({parseFloat(displayAccount.totalPnlPercent || 0).toFixed(2)}%)
              </Text>
            </View>
          </View>
        </View>
      )}

      {/* Statistics */}
      {(statistics || displayAccount) && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Statistics</Text>
          <View style={styles.statsGrid}>
            <View style={styles.statItem}>
              <Text style={styles.statValue}>{statistics?.totalTrades || displayAccount.totalTrades || 0}</Text>
              <Text style={styles.statLabel}>Total Trades</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={[styles.statValue, styles.winRate]}>
                {parseFloat(statistics?.winRate || displayAccount.winRate || 0).toFixed(1)}%
              </Text>
              <Text style={styles.statLabel}>Win Rate</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statValue}>{statistics?.winningTrades || displayAccount.winningTrades || 0}</Text>
              <Text style={styles.statLabel}>Wins</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statValue}>{statistics?.losingTrades || displayAccount.losingTrades || 0}</Text>
              <Text style={styles.statLabel}>Losses</Text>
            </View>
          </View>
        </View>
      )}

      {/* Place Order Button */}
      <TouchableOpacity
        style={styles.placeOrderButton}
        onPress={() => setShowOrderForm(!showOrderForm)}
      >
        <Icon name={showOrderForm ? "chevron-up" : "chevron-down"} size={20} color="#fff" />
        <Text style={styles.placeOrderButtonText}>
          {showOrderForm ? 'Hide Order Form' : 'Place Order'}
        </Text>
      </TouchableOpacity>

      {/* Order Form */}
      {showOrderForm && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Place Order</Text>
          
          {/* Side Selection */}
          <View style={styles.sideSelector}>
            <TouchableOpacity
              style={[styles.sideButton, orderSide === 'BUY' && styles.sideButtonActive]}
              onPress={() => setOrderSide('BUY')}
            >
              <Text style={[styles.sideButtonText, orderSide === 'BUY' && styles.sideButtonTextActive]}>
                BUY
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.sideButton, orderSide === 'SELL' && styles.sideButtonActive]}
              onPress={() => setOrderSide('SELL')}
            >
              <Text style={[styles.sideButtonText, orderSide === 'SELL' && styles.sideButtonTextActive]}>
                SELL
              </Text>
            </TouchableOpacity>
          </View>

          {/* Order Type */}
          <View style={styles.orderTypeSelector}>
            <TouchableOpacity
              style={[styles.typeButton, orderType === 'MARKET' && styles.typeButtonActive]}
              onPress={() => setOrderType('MARKET')}
            >
              <Text style={[styles.typeButtonText, orderType === 'MARKET' && styles.typeButtonTextActive]}>
                Market
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.typeButton, orderType === 'LIMIT' && styles.typeButtonActive]}
              onPress={() => setOrderType('LIMIT')}
            >
              <Text style={[styles.typeButtonText, orderType === 'LIMIT' && styles.typeButtonTextActive]}>
                Limit
              </Text>
            </TouchableOpacity>
          </View>

          {/* Input Fields */}
          <TextInput
            style={styles.input}
            placeholder="Symbol (e.g., AAPL)"
            placeholderTextColor="#999"
            value={orderSymbol}
            onChangeText={setOrderSymbol}
            autoCapitalize="characters"
          />
          <TextInput
            style={styles.input}
            placeholder="Quantity"
            placeholderTextColor="#999"
            value={orderQuantity}
            onChangeText={setOrderQuantity}
            keyboardType="numeric"
          />
          {orderType === 'LIMIT' && (
            <TextInput
              style={styles.input}
              placeholder="Limit Price"
              placeholderTextColor="#999"
              value={limitPrice}
              onChangeText={setLimitPrice}
              keyboardType="decimal-pad"
            />
          )}

          <TouchableOpacity
            style={[styles.submitButton, placingOrder && styles.submitButtonDisabled]}
            onPress={handlePlaceOrder}
            disabled={placingOrder}
          >
            {placingOrder ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.submitButtonText}>
                {orderSide} {orderSymbol || 'STOCK'}
              </Text>
            )}
          </TouchableOpacity>
        </View>
      )}

      {/* Open Positions */}
      {positions.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Open Positions ({positions.length})</Text>
          {positions.map((position: any) => (
            <View key={position.id} style={styles.positionItem}>
              <View style={styles.positionHeader}>
                <View>
                  <Text style={styles.positionSymbol}>{position.stockSymbol}</Text>
                  <Text style={styles.positionName}>{position.stockName}</Text>
                </View>
                <View style={styles.positionPnl}>
                  <Text style={[
                    styles.positionPnlValue,
                    parseFloat(position.unrealizedPnl) >= 0 ? styles.profit : styles.loss
                  ]}>
                    {parseFloat(position.unrealizedPnl) >= 0 ? '+' : ''}
                    ${parseFloat(position.unrealizedPnl).toFixed(2)}
                  </Text>
                  <Text style={styles.positionPnlPercent}>
                    {parseFloat(position.unrealizedPnlPercent).toFixed(2)}%
                  </Text>
                </View>
              </View>
              <View style={styles.positionDetails}>
                <Text style={styles.positionDetail}>
                  {position.shares} shares @ ${parseFloat(position.averagePrice).toFixed(2)}
                </Text>
                <Text style={styles.positionDetail}>
                  Current: ${parseFloat(position.currentPrice).toFixed(2)}
                </Text>
                <Text style={styles.positionDetail}>
                  Value: ${parseFloat(position.marketValue).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </Text>
              </View>
            </View>
          ))}
        </View>
      )}

      {/* Open Orders */}
      {openOrders.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Open Orders ({openOrders.length})</Text>
          {openOrders.map((order: any) => (
            <View key={order.id} style={styles.orderItem}>
              <View style={styles.orderHeader}>
                <View>
                  <Text style={styles.orderSymbol}>{order.stockSymbol}</Text>
                  <Text style={styles.orderDetails}>
                    {order.side} {order.quantity} @ {order.orderType}
                    {order.limitPrice && ` $${parseFloat(order.limitPrice).toFixed(2)}`}
                  </Text>
                </View>
                <TouchableOpacity
                  style={styles.cancelButton}
                  onPress={() => handleCancelOrder(order.id)}
                >
                  <Text style={styles.cancelButtonText}>Cancel</Text>
                </TouchableOpacity>
              </View>
            </View>
          ))}
        </View>
      )}

      {/* Recent Trades */}
      {recentTrades.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Recent Trades</Text>
          {recentTrades.slice(0, 10).map((trade: any) => (
            <View key={trade.id} style={styles.tradeItem}>
              <View style={styles.tradeHeader}>
                <View>
                  <Text style={styles.tradeSymbol}>{trade.stockSymbol}</Text>
                  <Text style={styles.tradeDetails}>
                    {trade.side} {trade.quantity} @ ${parseFloat(trade.price).toFixed(2)}
                  </Text>
                </View>
                {trade.realizedPnl !== null && (
                  <Text style={[
                    styles.tradePnl,
                    parseFloat(trade.realizedPnl) >= 0 ? styles.profit : styles.loss
                  ]}>
                    {parseFloat(trade.realizedPnl) >= 0 ? '+' : ''}
                    ${parseFloat(trade.realizedPnl).toFixed(2)}
                  </Text>
                )}
              </View>
            </View>
          ))}
        </View>
      )}

      <View style={styles.footer}>
        <Text style={styles.footerText}>
          💡 Paper trading uses virtual money. No real funds are at risk.
        </Text>
      </View>
    </ScrollView>
  );
}

function createStyles(isDark: boolean) {
  const bgColor = isDark ? '#1a1a1a' : '#ffffff';
  const cardBg = isDark ? '#2a2a2a' : '#f5f5f5';
  const textColor = isDark ? '#ffffff' : '#000000';
  const subtextColor = isDark ? '#999999' : '#666666';

  return StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: bgColor,
    },
    header: {
      padding: 20,
      paddingTop: 40,
    },
    title: {
      fontSize: 28,
      fontWeight: 'bold',
      color: textColor,
      marginBottom: 8,
    },
    subtitle: {
      fontSize: 14,
      color: subtextColor,
    },
    card: {
      backgroundColor: cardBg,
      margin: 16,
      padding: 16,
      borderRadius: 12,
    },
    cardTitle: {
      fontSize: 18,
      fontWeight: '600',
      color: textColor,
      marginBottom: 12,
    },
    balanceRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      marginBottom: 16,
    },
    balanceLabel: {
      fontSize: 12,
      color: subtextColor,
      marginBottom: 4,
    },
    balanceValue: {
      fontSize: 24,
      fontWeight: 'bold',
      color: textColor,
    },
    pnlRow: {
      marginTop: 8,
    },
    pnlLabel: {
      fontSize: 12,
      color: subtextColor,
      marginBottom: 4,
    },
    pnlValue: {
      fontSize: 20,
      fontWeight: 'bold',
    },
    profit: {
      color: '#00cc99',
    },
    loss: {
      color: '#ff4444',
    },
    statsGrid: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      justifyContent: 'space-between',
    },
    statItem: {
      width: '48%',
      marginBottom: 16,
    },
    statValue: {
      fontSize: 24,
      fontWeight: 'bold',
      color: textColor,
      marginBottom: 4,
    },
    statLabel: {
      fontSize: 12,
      color: subtextColor,
    },
    winRate: {
      color: '#00cc99',
    },
    placeOrderButton: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: '#00cc99',
      margin: 16,
      padding: 16,
      borderRadius: 12,
    },
    placeOrderButtonText: {
      color: '#fff',
      fontSize: 16,
      fontWeight: '600',
      marginLeft: 8,
    },
    sideSelector: {
      flexDirection: 'row',
      marginBottom: 16,
      borderRadius: 8,
      overflow: 'hidden',
      backgroundColor: isDark ? '#1a1a1a' : '#e0e0e0',
    },
    sideButton: {
      flex: 1,
      padding: 12,
      alignItems: 'center',
    },
    sideButtonActive: {
      backgroundColor: '#00cc99',
    },
    sideButtonText: {
      fontSize: 16,
      fontWeight: '600',
      color: subtextColor,
    },
    sideButtonTextActive: {
      color: '#fff',
    },
    orderTypeSelector: {
      flexDirection: 'row',
      marginBottom: 16,
      gap: 8,
    },
    typeButton: {
      flex: 1,
      padding: 12,
      borderRadius: 8,
      backgroundColor: isDark ? '#1a1a1a' : '#e0e0e0',
      alignItems: 'center',
    },
    typeButtonActive: {
      backgroundColor: '#00cc99',
    },
    typeButtonText: {
      fontSize: 14,
      fontWeight: '600',
      color: subtextColor,
    },
    typeButtonTextActive: {
      color: '#fff',
    },
    input: {
      backgroundColor: isDark ? '#1a1a1a' : '#ffffff',
      borderWidth: 1,
      borderColor: isDark ? '#333' : '#ddd',
      borderRadius: 8,
      padding: 12,
      marginBottom: 12,
      color: textColor,
      fontSize: 16,
    },
    submitButton: {
      backgroundColor: '#00cc99',
      padding: 16,
      borderRadius: 8,
      alignItems: 'center',
      marginTop: 8,
    },
    submitButtonDisabled: {
      opacity: 0.6,
    },
    submitButtonText: {
      color: '#fff',
      fontSize: 16,
      fontWeight: '600',
    },
    positionItem: {
      padding: 12,
      borderBottomWidth: 1,
      borderBottomColor: isDark ? '#333' : '#e0e0e0',
      marginBottom: 8,
    },
    positionHeader: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      marginBottom: 8,
    },
    positionSymbol: {
      fontSize: 18,
      fontWeight: '600',
      color: textColor,
    },
    positionName: {
      fontSize: 12,
      color: subtextColor,
    },
    positionPnl: {
      alignItems: 'flex-end',
    },
    positionPnlValue: {
      fontSize: 16,
      fontWeight: '600',
    },
    positionPnlPercent: {
      fontSize: 12,
      color: subtextColor,
    },
    positionDetails: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: 12,
    },
    positionDetail: {
      fontSize: 12,
      color: subtextColor,
    },
    orderItem: {
      padding: 12,
      borderBottomWidth: 1,
      borderBottomColor: isDark ? '#333' : '#e0e0e0',
      marginBottom: 8,
    },
    orderHeader: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
    },
    orderSymbol: {
      fontSize: 16,
      fontWeight: '600',
      color: textColor,
    },
    orderDetails: {
      fontSize: 12,
      color: subtextColor,
      marginTop: 4,
    },
    cancelButton: {
      backgroundColor: '#ff4444',
      paddingHorizontal: 12,
      paddingVertical: 6,
      borderRadius: 6,
    },
    cancelButtonText: {
      color: '#fff',
      fontSize: 12,
      fontWeight: '600',
    },
    tradeItem: {
      padding: 12,
      borderBottomWidth: 1,
      borderBottomColor: isDark ? '#333' : '#e0e0e0',
      marginBottom: 8,
    },
    tradeHeader: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
    },
    tradeSymbol: {
      fontSize: 16,
      fontWeight: '600',
      color: textColor,
    },
    tradeDetails: {
      fontSize: 12,
      color: subtextColor,
      marginTop: 4,
    },
    tradePnl: {
      fontSize: 16,
      fontWeight: '600',
    },
    footer: {
      padding: 20,
      alignItems: 'center',
    },
    footerText: {
      fontSize: 12,
      color: subtextColor,
      textAlign: 'center',
    },
    loadingText: {
      marginTop: 16,
      fontSize: 16,
      color: subtextColor,
      textAlign: 'center',
    },
    errorText: {
      marginTop: 16,
      fontSize: 18,
      fontWeight: '600',
      color: textColor,
      textAlign: 'center',
    },
    errorDetail: {
      marginTop: 8,
      fontSize: 14,
      color: subtextColor,
      textAlign: 'center',
    },
    retryButton: {
      marginTop: 16,
      backgroundColor: '#00cc99',
      paddingHorizontal: 24,
      paddingVertical: 12,
      borderRadius: 8,
    },
    retryButtonText: {
      color: '#fff',
      fontSize: 16,
      fontWeight: '600',
    },
  });
}

