import React, { useState, useEffect } from 'react';
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
import { useQuery, useMutation, useApolloClient } from '@apollo/client';
import { gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';

const { width } = Dimensions.get('window');

// GraphQL Queries
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
      symbol
      quantity
      marketValue
      costBasis
      unrealizedPl
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

// GraphQL Mutations
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

const PLACE_LIMIT_ORDER = gql`
  mutation PlaceLimitOrder($symbol: String!, $quantity: Int!, $side: String!, $limitPrice: Float!, $notes: String) {
    placeLimitOrder(symbol: $symbol, quantity: $quantity, side: $side, limitPrice: $limitPrice, notes: $notes) {
      success
      order {
        id
        symbol
        side
        orderType
        quantity
        price
        status
        createdAt
        notes
      }
    }
  }
`;

const PLACE_STOP_LOSS_ORDER = gql`
  mutation PlaceStopLossOrder($symbol: String!, $quantity: Int!, $side: String!, $stopPrice: Float!, $notes: String) {
    placeStopLossOrder(symbol: $symbol, quantity: $quantity, side: $side, stopPrice: $stopPrice, notes: $notes) {
      success
      order {
        id
        symbol
        side
        orderType
        quantity
        stopPrice
        status
        createdAt
        notes
      }
    }
  }
`;

const CANCEL_ORDER = gql`
  mutation CancelOrder($orderId: String!) {
    cancelOrder(orderId: $orderId) {
      success
      message
    }
  }
`;

const TradingScreen = ({ navigateTo }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [refreshing, setRefreshing] = useState(false);
  const [showOrderModal, setShowOrderModal] = useState(false);
  const [orderType, setOrderType] = useState('market');
  const [orderSide, setOrderSide] = useState('buy');
  const [symbol, setSymbol] = useState('');
  const [quantity, setQuantity] = useState('');
  const [price, setPrice] = useState('');
  const [stopPrice, setStopPrice] = useState('');
  const [notes, setNotes] = useState('');
  const [isPlacingOrder, setIsPlacingOrder] = useState(false);

  // Queries
  const { data: accountData, loading: accountLoading, refetch: refetchAccount } = useQuery(
    GET_TRADING_ACCOUNT,
    { errorPolicy: 'all' }
  );

  const { data: positionsData, loading: positionsLoading, refetch: refetchPositions } = useQuery(
    GET_TRADING_POSITIONS,
    { errorPolicy: 'all' }
  );

  const { data: ordersData, loading: ordersLoading, refetch: refetchOrders } = useQuery(
    GET_TRADING_ORDERS,
    { 
      variables: { limit: 20 },
      errorPolicy: 'all' 
    }
  );

  const { data: quoteData, loading: quoteLoading, refetch: refetchQuote } = useQuery(
    GET_TRADING_QUOTE,
    { 
      variables: { symbol: symbol || 'AAPL' },
      skip: !symbol,
      errorPolicy: 'all' 
    }
  );

  // Mutations
  const [placeMarketOrder] = useMutation(PLACE_MARKET_ORDER);
  const [placeLimitOrder] = useMutation(PLACE_LIMIT_ORDER);
  const [placeStopLossOrder] = useMutation(PLACE_STOP_LOSS_ORDER);
  const [cancelOrder] = useMutation(CANCEL_ORDER);

  const onRefresh = async () => {
    setRefreshing(true);
    try {
      await Promise.all([
        refetchAccount(),
        refetchPositions(),
        refetchOrders(),
        refetchQuote()
      ]);
    } catch (error) {
      console.error('Error refreshing data:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const handlePlaceOrder = async () => {
    if (!symbol || !quantity) {
      Alert.alert('Error', 'Please enter symbol and quantity');
      return;
    }

    setIsPlacingOrder(true);
    try {
      let result;
      const orderNotes = notes || `Placed via RichesReach app`;

      switch (orderType) {
        case 'market':
          result = await placeMarketOrder({
            variables: {
              symbol: symbol.toUpperCase(),
              quantity: parseInt(quantity),
              side: orderSide,
              notes: orderNotes
            }
          });
          break;
        case 'limit':
          if (!price) {
            Alert.alert('Error', 'Please enter limit price');
            return;
          }
          result = await placeLimitOrder({
            variables: {
              symbol: symbol.toUpperCase(),
              quantity: parseInt(quantity),
              side: orderSide,
              limitPrice: parseFloat(price),
              notes: orderNotes
            }
          });
          break;
        case 'stop_loss':
          if (!stopPrice) {
            Alert.alert('Error', 'Please enter stop price');
            return;
          }
          result = await placeStopLossOrder({
            variables: {
              symbol: symbol.toUpperCase(),
              quantity: parseInt(quantity),
              side: orderSide,
              stopPrice: parseFloat(stopPrice),
              notes: orderNotes
            }
          });
          break;
      }

      if (result.data) {
        const orderData = result.data[`place${orderType.charAt(0).toUpperCase() + orderType.slice(1)}Order`];
        if (orderData.success) {
          Alert.alert(
            'Order Placed',
            `Your ${orderType} order for ${quantity} shares of ${symbol.toUpperCase()} has been placed successfully.`,
            [{ text: 'OK', onPress: () => {
              setShowOrderModal(false);
              resetOrderForm();
              refetchOrders();
            }}]
          );
        } else {
          Alert.alert('Error', 'Failed to place order');
        }
      }
    } catch (error) {
      console.error('Error placing order:', error);
      Alert.alert('Error', 'Failed to place order. Please try again.');
    } finally {
      setIsPlacingOrder(false);
    }
  };

  const handleCancelOrder = async (orderId: string) => {
    Alert.alert(
      'Cancel Order',
      'Are you sure you want to cancel this order?',
      [
        { text: 'No', style: 'cancel' },
        { 
          text: 'Yes', 
          onPress: async () => {
            try {
              const result = await cancelOrder({
                variables: { orderId }
              });
              
              if (result.data.cancelOrder.success) {
                Alert.alert('Success', 'Order cancelled successfully');
                refetchOrders();
              } else {
                Alert.alert('Error', 'Failed to cancel order');
              }
            } catch (error) {
              console.error('Error cancelling order:', error);
              Alert.alert('Error', 'Failed to cancel order');
            }
          }
        }
      ]
    );
  };

  const resetOrderForm = () => {
    setSymbol('');
    setQuantity('');
    setPrice('');
    setStopPrice('');
    setNotes('');
    setOrderType('market');
    setOrderSide('buy');
  };

  const renderOverviewTab = () => {
    const account = accountData?.tradingAccount;
    const positions = positionsData?.tradingPositions || [];

    return (
      <ScrollView style={styles.tabContent} showsVerticalScrollIndicator={false}>
        {/* Account Summary */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Account Summary</Text>
          {accountLoading ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="small" color="#007AFF" />
              <Text style={styles.loadingText}>Loading account...</Text>
            </View>
          ) : account ? (
            <View style={styles.accountCard}>
              <View style={styles.accountRow}>
                <Text style={styles.accountLabel}>Buying Power</Text>
                <Text style={styles.accountValue}>${account.buyingPower?.toLocaleString() || '0.00'}</Text>
              </View>
              <View style={styles.accountRow}>
                <Text style={styles.accountLabel}>Cash</Text>
                <Text style={styles.accountValue}>${account.cash?.toLocaleString() || '0.00'}</Text>
              </View>
              <View style={styles.accountRow}>
                <Text style={styles.accountLabel}>Portfolio Value</Text>
                <Text style={styles.accountValue}>${account.portfolioValue?.toLocaleString() || '0.00'}</Text>
              </View>
              <View style={styles.accountRow}>
                <Text style={styles.accountLabel}>Equity</Text>
                <Text style={styles.accountValue}>${account.equity?.toLocaleString() || '0.00'}</Text>
              </View>
              <View style={styles.accountRow}>
                <Text style={styles.accountLabel}>Day Trading Buying Power</Text>
                <Text style={styles.accountValue}>${account.dayTradingBuyingPower?.toLocaleString() || '0.00'}</Text>
              </View>
              <View style={styles.accountRow}>
                <Text style={styles.accountLabel}>Is Day Trading Enabled</Text>
                <Text style={[styles.accountValue, { color: account.isDayTradingEnabled ? '#34C759' : '#FF3B30' }]}>
                  {account.isDayTradingEnabled ? 'Yes' : 'No'}
                </Text>
              </View>
              <View style={styles.accountRow}>
                <Text style={styles.accountLabel}>Account Status</Text>
                <Text style={[styles.accountValue, { color: account.accountStatus === 'active' ? '#34C759' : '#FF3B30' }]}>
                  {account.accountStatus?.toUpperCase() || 'UNKNOWN'}
                </Text>
              </View>
              {account.tradingBlocked && (
                <View style={styles.warningBox}>
                  <Icon name="alert-triangle" size={16} color="#FF9500" />
                  <Text style={styles.warningText}>Trading is currently blocked</Text>
                </View>
              )}
            </View>
          ) : (
            <Text style={styles.errorText}>Unable to load account data</Text>
          )}
        </View>

        {/* Positions */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Positions</Text>
          {positionsLoading ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="small" color="#007AFF" />
              <Text style={styles.loadingText}>Loading positions...</Text>
            </View>
          ) : positions.length > 0 ? (
            positions.map((position, index) => (
              <View key={index} style={styles.positionCard}>
                <View style={styles.positionHeader}>
                  <Text style={styles.positionSymbol}>{position.symbol}</Text>
                  <Text style={[
                    styles.positionPl,
                    { color: position.unrealizedPl >= 0 ? '#34C759' : '#FF3B30' }
                  ]}>
                    {position.unrealizedPl >= 0 ? '+' : ''}${position.unrealizedPl?.toFixed(2)}
                  </Text>
                </View>
                <View style={styles.positionDetails}>
                  <Text style={styles.positionQuantity}>{position.quantity} shares</Text>
                  <Text style={styles.positionPrice}>@ ${position.currentPrice?.toFixed(2)}</Text>
                  <Text style={styles.positionValue}>Value: ${position.marketValue?.toLocaleString()}</Text>
                </View>
                <Text style={[
                  styles.positionPlpc,
                  { color: position.unrealizedPlpc >= 0 ? '#34C759' : '#FF3B30' }
                ]}>
                  {position.unrealizedPlpc >= 0 ? '+' : ''}{position.unrealizedPlpc?.toFixed(2)}%
                </Text>
              </View>
            ))
          ) : (
            <View style={styles.emptyState}>
              <Icon name="briefcase" size={48} color="#8E8E93" />
              <Text style={styles.emptyText}>No positions yet</Text>
              <Text style={styles.emptySubtext}>Start trading to see your positions here</Text>
            </View>
          )}
        </View>
      </ScrollView>
    );
  };

  const renderOrdersTab = () => {
    const orders = ordersData?.tradingOrders || [];

    return (
      <ScrollView style={styles.tabContent} showsVerticalScrollIndicator={false}>
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Recent Orders</Text>
          {ordersLoading ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="small" color="#007AFF" />
              <Text style={styles.loadingText}>Loading orders...</Text>
            </View>
          ) : orders.length > 0 ? (
            orders.map((order, index) => (
              <View key={index} style={styles.orderCard}>
                <View style={styles.orderHeader}>
                  <View style={styles.orderInfo}>
                    <Text style={styles.orderSymbol}>{order.symbol}</Text>
                    <Text style={styles.orderType}>{order.orderType.toUpperCase()}</Text>
                  </View>
                  <View style={styles.orderStatus}>
                    <Text style={[
                      styles.statusText,
                      { color: getStatusColor(order.status) }
                    ]}>
                      {order.status.toUpperCase()}
                    </Text>
                    {order.status === 'pending' && (
                      <TouchableOpacity
                        style={styles.cancelButton}
                        onPress={() => handleCancelOrder(order.id)}
                      >
                        <Text style={styles.cancelButtonText}>Cancel</Text>
                      </TouchableOpacity>
                    )}
                  </View>
                </View>
                <View style={styles.orderDetails}>
                  <Text style={styles.orderSide}>{order.side.toUpperCase()} {order.quantity} shares</Text>
                  {order.price && <Text style={styles.orderPrice}>@ ${order.price.toFixed(2)}</Text>}
                  {order.stopPrice && <Text style={styles.orderStopPrice}>Stop: ${order.stopPrice.toFixed(2)}</Text>}
                </View>
                <Text style={styles.orderTime}>
                  {new Date(order.createdAt).toLocaleString()}
                </Text>
                {order.notes && (
                  <Text style={styles.orderNotes}>Note: {order.notes}</Text>
                )}
              </View>
            ))
          ) : (
            <View style={styles.emptyState}>
              <Icon name="clock" size={48} color="#8E8E93" />
              <Text style={styles.emptyText}>No orders yet</Text>
              <Text style={styles.emptySubtext}>Place your first order to get started</Text>
            </View>
          )}
        </View>
      </ScrollView>
    );
  };

  const renderOrderModal = () => (
    <Modal
      visible={showOrderModal}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={() => setShowOrderModal(false)}
    >
      <SafeAreaView style={styles.modalContainer}>
        <View style={styles.modalHeader}>
          <Text style={styles.modalTitle}>Place Order</Text>
          <TouchableOpacity onPress={() => setShowOrderModal(false)}>
            <Icon name="x" size={24} color="#000" />
          </TouchableOpacity>
        </View>
        
        <ScrollView style={styles.modalContent}>
          {/* Order Type */}
          <View style={styles.inputGroup}>
            <Text style={styles.inputLabel}>Order Type</Text>
            <View style={styles.orderTypeButtons}>
              {['market', 'limit', 'stop_loss'].map((type) => (
                <TouchableOpacity
                  key={type}
                  style={[
                    styles.orderTypeButton,
                    orderType === type && styles.orderTypeButtonActive
                  ]}
                  onPress={() => setOrderType(type)}
                >
                  <Text style={[
                    styles.orderTypeButtonText,
                    orderType === type && styles.orderTypeButtonTextActive
                  ]}>
                    {type.replace('_', ' ').toUpperCase()}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Order Side */}
          <View style={styles.inputGroup}>
            <Text style={styles.inputLabel}>Side</Text>
            <View style={styles.sideButtons}>
              <TouchableOpacity
                style={[
                  styles.sideButton,
                  orderSide === 'buy' && styles.sideButtonActive
                ]}
                onPress={() => setOrderSide('buy')}
              >
                <Text style={[
                  styles.sideButtonText,
                  orderSide === 'buy' && styles.sideButtonTextActive
                ]}>
                  BUY
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.sideButton,
                  orderSide === 'sell' && styles.sideButtonActiveSell
                ]}
                onPress={() => setOrderSide('sell')}
              >
                <Text style={[
                  styles.sideButtonText,
                  orderSide === 'sell' && styles.sideButtonTextActive
                ]}>
                  SELL
                </Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Symbol */}
          <View style={styles.inputGroup}>
            <Text style={styles.inputLabel}>Symbol</Text>
            <TextInput
              style={styles.textInput}
              value={symbol}
              onChangeText={setSymbol}
              placeholder="e.g., AAPL"
              autoCapitalize="characters"
              autoCorrect={false}
            />
          </View>

          {/* Quantity */}
          <View style={styles.inputGroup}>
            <Text style={styles.inputLabel}>Quantity</Text>
            <TextInput
              style={styles.textInput}
              value={quantity}
              onChangeText={setQuantity}
              placeholder="Number of shares"
              keyboardType="numeric"
            />
          </View>

          {/* Price (for limit orders) */}
          {orderType === 'limit' && (
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Limit Price</Text>
              <TextInput
                style={styles.textInput}
                value={price}
                onChangeText={setPrice}
                placeholder="Price per share"
                keyboardType="numeric"
              />
            </View>
          )}

          {/* Stop Price (for stop loss orders) */}
          {orderType === 'stop_loss' && (
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Stop Price</Text>
              <TextInput
                style={styles.textInput}
                value={stopPrice}
                onChangeText={setStopPrice}
                placeholder="Stop price"
                keyboardType="numeric"
              />
            </View>
          )}

          {/* Notes */}
          <View style={styles.inputGroup}>
            <Text style={styles.inputLabel}>Notes (Optional)</Text>
            <TextInput
              style={[styles.textInput, styles.textArea]}
              value={notes}
              onChangeText={setNotes}
              placeholder="Add a note about this order"
              multiline
              numberOfLines={3}
            />
          </View>

          {/* Current Quote */}
          {symbol && quoteData?.tradingQuote && (
            <View style={styles.quoteCard}>
              <Text style={styles.quoteTitle}>Current Quote for {symbol.toUpperCase()}</Text>
              <View style={styles.quoteRow}>
                <Text style={styles.quoteLabel}>Bid:</Text>
                <Text style={styles.quoteValue}>${quoteData.tradingQuote.bid?.toFixed(2)}</Text>
              </View>
              <View style={styles.quoteRow}>
                <Text style={styles.quoteLabel}>Ask:</Text>
                <Text style={styles.quoteValue}>${quoteData.tradingQuote.ask?.toFixed(2)}</Text>
              </View>
            </View>
          )}

          {/* Place Order Button */}
          <TouchableOpacity
            style={[styles.placeOrderButton, isPlacingOrder && styles.placeOrderButtonDisabled]}
            onPress={handlePlaceOrder}
            disabled={isPlacingOrder}
          >
            {isPlacingOrder ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Text style={styles.placeOrderButtonText}>Place Order</Text>
            )}
          </TouchableOpacity>
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'filled': return '#34C759';
      case 'pending': return '#FF9500';
      case 'cancelled': return '#8E8E93';
      case 'rejected': return '#FF3B30';
      default: return '#8E8E93';
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigateTo('home')}>
          <Icon name="arrow-left" size={24} color="#000" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Trading</Text>
        <TouchableOpacity onPress={() => setShowOrderModal(true)}>
          <Icon name="plus" size={24} color="#007AFF" />
        </TouchableOpacity>
      </View>

      {/* Tab Navigation */}
      <View style={styles.tabNavigation}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'overview' && styles.activeTab]}
          onPress={() => setActiveTab('overview')}
        >
          <Text style={[styles.tabText, activeTab === 'overview' && styles.activeTabText]}>
            Overview
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'orders' && styles.activeTab]}
          onPress={() => setActiveTab('orders')}
        >
          <Text style={[styles.tabText, activeTab === 'orders' && styles.activeTabText]}>
            Orders
          </Text>
        </TouchableOpacity>
      </View>

      {/* Tab Content */}
      <View style={styles.tabContentContainer}>
        {activeTab === 'overview' && renderOverviewTab()}
        {activeTab === 'orders' && renderOrdersTab()}
      </View>

      {/* Order Modal */}
      {renderOrderModal()}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
  },
  tabNavigation: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  tab: {
    flex: 1,
    paddingVertical: 16,
    alignItems: 'center',
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  activeTab: {
    borderBottomColor: '#007AFF',
  },
  tabText: {
    fontSize: 16,
    color: '#8E8E93',
    fontWeight: '500',
  },
  activeTabText: {
    color: '#007AFF',
    fontWeight: '600',
  },
  tabContentContainer: {
    flex: 1,
  },
  tabContent: {
    flex: 1,
    padding: 20,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#000',
    marginBottom: 16,
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 20,
  },
  loadingText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#8E8E93',
  },
  errorText: {
    fontSize: 14,
    color: '#FF3B30',
    textAlign: 'center',
    paddingVertical: 20,
  },
  accountCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  accountRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#F2F2F7',
  },
  accountLabel: {
    fontSize: 16,
    color: '#8E8E93',
  },
  accountValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
  },
  warningBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF3CD',
    padding: 12,
    borderRadius: 8,
    marginTop: 12,
  },
  warningText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#856404',
    fontWeight: '500',
  },
  positionCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  positionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  positionSymbol: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
  },
  positionPl: {
    fontSize: 16,
    fontWeight: '600',
  },
  positionDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  positionQuantity: {
    fontSize: 14,
    color: '#8E8E93',
  },
  positionPrice: {
    fontSize: 14,
    color: '#8E8E93',
  },
  positionValue: {
    fontSize: 14,
    color: '#8E8E93',
  },
  positionPlpc: {
    fontSize: 14,
    fontWeight: '600',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyText: {
    fontSize: 16,
    color: '#8E8E93',
    marginTop: 16,
    fontWeight: '500',
  },
  emptySubtext: {
    fontSize: 14,
    color: '#8E8E93',
    marginTop: 8,
    textAlign: 'center',
  },
  orderCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  orderHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  orderInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  orderSymbol: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
    marginRight: 8,
  },
  orderType: {
    fontSize: 12,
    color: '#007AFF',
    backgroundColor: '#E3F2FD',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  orderStatus: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
    marginRight: 8,
  },
  cancelButton: {
    backgroundColor: '#FF3B30',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  cancelButtonText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  orderDetails: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  orderSide: {
    fontSize: 14,
    color: '#8E8E93',
    marginRight: 8,
  },
  orderPrice: {
    fontSize: 14,
    color: '#8E8E93',
    marginRight: 8,
  },
  orderStopPrice: {
    fontSize: 14,
    color: '#8E8E93',
  },
  orderTime: {
    fontSize: 12,
    color: '#8E8E93',
  },
  orderNotes: {
    fontSize: 12,
    color: '#8E8E93',
    fontStyle: 'italic',
    marginTop: 4,
  },
  // Modal Styles
  modalContainer: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
  },
  modalContent: {
    flex: 1,
    padding: 20,
  },
  inputGroup: {
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    marginBottom: 8,
  },
  textInput: {
    backgroundColor: '#fff',
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  textArea: {
    height: 80,
    textAlignVertical: 'top',
  },
  orderTypeButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  orderTypeButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: '#F2F2F7',
    alignItems: 'center',
  },
  orderTypeButtonActive: {
    backgroundColor: '#007AFF',
  },
  orderTypeButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#8E8E93',
  },
  orderTypeButtonTextActive: {
    color: '#fff',
  },
  sideButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  sideButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: '#F2F2F7',
    alignItems: 'center',
  },
  sideButtonActive: {
    backgroundColor: '#34C759',
  },
  sideButtonActiveSell: {
    backgroundColor: '#FF3B30',
  },
  sideButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#8E8E93',
  },
  sideButtonTextActive: {
    color: '#fff',
  },
  quoteCard: {
    backgroundColor: '#E3F2FD',
    borderRadius: 8,
    padding: 16,
    marginBottom: 20,
  },
  quoteTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    marginBottom: 8,
  },
  quoteRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  quoteLabel: {
    fontSize: 14,
    color: '#8E8E93',
  },
  quoteValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#000',
  },
  placeOrderButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 20,
  },
  placeOrderButtonDisabled: {
    backgroundColor: '#8E8E93',
  },
  placeOrderButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default TradingScreen;
