/**
 * Advanced Order Management
 * Professional-grade order types and execution
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
  Modal,
  Switch,
} from 'react-native';
import { useQuery, useMutation, gql } from '@apollo/client';
import { Ionicons } from '@expo/vector-icons';

// GraphQL Queries and Mutations
const GET_ACCOUNT_INFO = gql`
  query GetAccountInfo {
    accountInfo {
      buyingPower
      cash
      equity
      margin
      dayTradingBuyingPower
      patternDayTrader
    }
  }
`;

const GET_POSITIONS = gql`
  query GetPositions {
    positions {
      symbol
      quantity
      averagePrice
      marketValue
      unrealizedPnL
      unrealizedPnLPercent
      side
    }
  }
`;

const GET_ORDERS = gql`
  query GetOrders($status: String) {
    orders(status: $status) {
      id
      symbol
      side
      type
      quantity
      price
      stopPrice
      timeInForce
      status
      createdAt
      filledAt
      filledQuantity
      averageFillPrice
      commission
    }
  }
`;

const PLACE_ORDER = gql`
  mutation PlaceOrder($order: OrderInput!) {
    placeOrder(order: $order) {
      success
      message
      orderId
      order {
        id
        symbol
        side
        type
        quantity
        price
        status
        createdAt
      }
    }
  }
`;

const CANCEL_ORDER = gql`
  mutation CancelOrder($orderId: ID!) {
    cancelOrder(orderId: $orderId) {
      success
      message
    }
  }
`;

const MODIFY_ORDER = gql`
  mutation ModifyOrder($orderId: ID!, $modifications: OrderModificationInput!) {
    modifyOrder(orderId: $orderId, modifications: $modifications) {
      success
      message
      order {
        id
        symbol
        side
        type
        quantity
        price
        status
      }
    }
  }
`;

interface AccountInfo {
  buyingPower: number;
  cash: number;
  equity: number;
  margin: number;
  dayTradingBuyingPower: number;
  patternDayTrader: boolean;
}

interface Position {
  symbol: string;
  quantity: number;
  averagePrice: number;
  marketValue: number;
  unrealizedPnL: number;
  unrealizedPnLPercent: number;
  side: 'long' | 'short';
}

interface Order {
  id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  type: 'MARKET' | 'LIMIT' | 'STOP' | 'STOP_LIMIT' | 'TRAILING_STOP' | 'BRACKET' | 'OCO' | 'ICEBERG';
  quantity: number;
  price?: number;
  stopPrice?: number;
  timeInForce: 'DAY' | 'GTC' | 'IOC' | 'FOK';
  status: 'PENDING' | 'FILLED' | 'CANCELLED' | 'REJECTED' | 'PARTIALLY_FILLED';
  createdAt: string;
  filledAt?: string;
  filledQuantity?: number;
  averageFillPrice?: number;
  commission?: number;
}

interface OrderManagementProps {
  userId: string;
  onOrderPlaced?: (order: Order) => void;
  onOrderCancelled?: (orderId: string) => void;
}

export const OrderManagement: React.FC<OrderManagementProps> = ({
  userId,
  onOrderPlaced,
  onOrderCancelled,
}) => {
  const [activeTab, setActiveTab] = useState<'orders' | 'positions' | 'account' | 'place'>('orders');
  const [selectedOrderType, setSelectedOrderType] = useState<string>('MARKET');
  const [showOrderModal, setShowOrderModal] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [orderForm, setOrderForm] = useState({
    symbol: '',
    side: 'BUY' as 'BUY' | 'SELL',
    type: 'MARKET' as string,
    quantity: '',
    price: '',
    stopPrice: '',
    timeInForce: 'DAY' as 'DAY' | 'GTC' | 'IOC' | 'FOK',
    bracket: {
      takeProfit: '',
      stopLoss: '',
    },
    trailingStop: {
      trailAmount: '',
      trailPercent: '',
    },
    iceberg: {
      displayQuantity: '',
    },
  });

  const { data: accountData, loading: accountLoading } = useQuery(GET_ACCOUNT_INFO);
  const { data: positionsData, loading: positionsLoading } = useQuery(GET_POSITIONS);
  const { data: ordersData, loading: ordersLoading, refetch: refetchOrders } = useQuery(
    GET_ORDERS,
    { variables: { status: null } }
  );

  const [placeOrder] = useMutation(PLACE_ORDER);
  const [cancelOrder] = useMutation(CANCEL_ORDER);
  const [modifyOrder] = useMutation(MODIFY_ORDER);

  const orderTypes = [
    { value: 'MARKET', label: 'Market', description: 'Execute immediately at market price' },
    { value: 'LIMIT', label: 'Limit', description: 'Execute at specified price or better' },
    { value: 'STOP', label: 'Stop', description: 'Triggered when price reaches stop level' },
    { value: 'STOP_LIMIT', label: 'Stop Limit', description: 'Stop order with limit price' },
    { value: 'TRAILING_STOP', label: 'Trailing Stop', description: 'Stop that follows price' },
    { value: 'BRACKET', label: 'Bracket', description: 'Entry with take profit and stop loss' },
    { value: 'OCO', label: 'OCO', description: 'One Cancels Other order' },
    { value: 'ICEBERG', label: 'Iceberg', description: 'Large order hidden in smaller pieces' },
  ];

  const timeInForceOptions = [
    { value: 'DAY', label: 'Day', description: 'Valid for current trading day' },
    { value: 'GTC', label: 'GTC', description: 'Good Till Cancelled' },
    { value: 'IOC', label: 'IOC', description: 'Immediate or Cancel' },
    { value: 'FOK', label: 'FOK', description: 'Fill or Kill' },
  ];

  const handlePlaceOrder = async () => {
    try {
      const orderInput = {
        symbol: orderForm.symbol.toUpperCase(),
        side: orderForm.side,
        type: orderForm.type,
        quantity: parseInt(orderForm.quantity),
        price: orderForm.price ? parseFloat(orderForm.price) : null,
        stopPrice: orderForm.stopPrice ? parseFloat(orderForm.stopPrice) : null,
        timeInForce: orderForm.timeInForce,
        bracket: orderForm.bracket.takeProfit || orderForm.bracket.stopLoss ? {
          takeProfit: orderForm.bracket.takeProfit ? parseFloat(orderForm.bracket.takeProfit) : null,
          stopLoss: orderForm.bracket.stopLoss ? parseFloat(orderForm.bracket.stopLoss) : null,
        } : null,
        trailingStop: orderForm.trailingStop.trailAmount || orderForm.trailingStop.trailPercent ? {
          trailAmount: orderForm.trailingStop.trailAmount ? parseFloat(orderForm.trailingStop.trailAmount) : null,
          trailPercent: orderForm.trailingStop.trailPercent ? parseFloat(orderForm.trailingStop.trailPercent) : null,
        } : null,
        iceberg: orderForm.iceberg.displayQuantity ? {
          displayQuantity: parseInt(orderForm.iceberg.displayQuantity),
        } : null,
      };

      const result = await placeOrder({ variables: { order: orderInput } });
      
      if (result.data?.placeOrder?.success) {
        Alert.alert('Success', 'Order placed successfully!');
        setShowOrderModal(false);
        refetchOrders();
        onOrderPlaced?.(result.data.placeOrder.order);
        
        // Reset form
        setOrderForm({
          symbol: '',
          side: 'BUY',
          type: 'MARKET',
          quantity: '',
          price: '',
          stopPrice: '',
          timeInForce: 'DAY',
          bracket: { takeProfit: '', stopLoss: '' },
          trailingStop: { trailAmount: '', trailPercent: '' },
          iceberg: { displayQuantity: '' },
        });
      } else {
        Alert.alert('Error', result.data?.placeOrder?.message || 'Failed to place order');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to place order');
    }
  };

  const handleCancelOrder = async (orderId: string) => {
    try {
      const result = await cancelOrder({ variables: { orderId } });
      
      if (result.data?.cancelOrder?.success) {
        Alert.alert('Success', 'Order cancelled successfully!');
        refetchOrders();
        onOrderCancelled?.(orderId);
      } else {
        Alert.alert('Error', result.data?.cancelOrder?.message || 'Failed to cancel order');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to cancel order');
    }
  };

  const handleModifyOrder = async (orderId: string, modifications: any) => {
    try {
      const result = await modifyOrder({ variables: { orderId, modifications } });
      
      if (result.data?.modifyOrder?.success) {
        Alert.alert('Success', 'Order modified successfully!');
        refetchOrders();
      } else {
        Alert.alert('Error', result.data?.modifyOrder?.message || 'Failed to modify order');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to modify order');
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'FILLED': return '#00ff88';
      case 'PENDING': return '#ffbb00';
      case 'CANCELLED': return '#888';
      case 'REJECTED': return '#ff4444';
      case 'PARTIALLY_FILLED': return '#ff8800';
      default: return '#888';
    }
  };

  const getSideColor = (side: string) => {
    return side === 'BUY' ? '#00ff88' : '#ff4444';
  };

  const renderOrderCard = (order: Order) => (
    <TouchableOpacity
      key={order.id}
      style={styles.orderCard}
      onPress={() => {
        setSelectedOrder(order);
        setShowOrderModal(true);
      }}
    >
      <View style={styles.orderHeader}>
        <View style={styles.orderSymbolRow}>
          <Text style={styles.orderSymbol}>{order.symbol}</Text>
          <View style={[
            styles.orderSide,
            { backgroundColor: getSideColor(order.side) }
          ]}>
            <Text style={styles.orderSideText}>{order.side}</Text>
          </View>
        </View>
        <Text style={styles.orderType}>{order.type}</Text>
      </View>

      <View style={styles.orderDetails}>
        <View style={styles.orderDetailRow}>
          <Text style={styles.orderDetailLabel}>Quantity</Text>
          <Text style={styles.orderDetailValue}>{order.quantity}</Text>
        </View>
        {order.price && (
          <View style={styles.orderDetailRow}>
            <Text style={styles.orderDetailLabel}>Price</Text>
            <Text style={styles.orderDetailValue}>{formatCurrency(order.price)}</Text>
          </View>
        )}
        {order.stopPrice && (
          <View style={styles.orderDetailRow}>
            <Text style={styles.orderDetailLabel}>Stop Price</Text>
            <Text style={styles.orderDetailValue}>{formatCurrency(order.stopPrice)}</Text>
          </View>
        )}
        <View style={styles.orderDetailRow}>
          <Text style={styles.orderDetailLabel}>Time in Force</Text>
          <Text style={styles.orderDetailValue}>{order.timeInForce}</Text>
        </View>
      </View>

      <View style={styles.orderFooter}>
        <View style={styles.orderStatusRow}>
          <Text style={styles.orderStatusLabel}>Status</Text>
          <Text style={[
            styles.orderStatus,
            { color: getStatusColor(order.status) }
          ]}>
            {order.status}
          </Text>
        </View>
        <Text style={styles.orderTimestamp}>{formatTimestamp(order.createdAt)}</Text>
      </View>

      {order.status === 'PENDING' && (
        <View style={styles.orderActions}>
          <TouchableOpacity
            style={styles.cancelButton}
            onPress={() => handleCancelOrder(order.id)}
          >
            <Text style={styles.cancelButtonText}>Cancel</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.modifyButton}
            onPress={() => {
              // In a real app, this would open a modify order modal
              Alert.alert('Modify Order', 'Modify order functionality would open here');
            }}
          >
            <Text style={styles.modifyButtonText}>Modify</Text>
          </TouchableOpacity>
        </View>
      )}
    </TouchableOpacity>
  );

  const renderPositionCard = (position: Position) => (
    <View key={position.symbol} style={styles.positionCard}>
      <View style={styles.positionHeader}>
        <Text style={styles.positionSymbol}>{position.symbol}</Text>
        <View style={[
          styles.positionSide,
          { backgroundColor: position.side === 'long' ? '#00ff88' : '#ff4444' }
        ]}>
          <Text style={styles.positionSideText}>{position.side.toUpperCase()}</Text>
        </View>
      </View>

      <View style={styles.positionDetails}>
        <View style={styles.positionDetailRow}>
          <Text style={styles.positionDetailLabel}>Quantity</Text>
          <Text style={styles.positionDetailValue}>{position.quantity}</Text>
        </View>
        <View style={styles.positionDetailRow}>
          <Text style={styles.positionDetailLabel}>Avg Price</Text>
          <Text style={styles.positionDetailValue}>{formatCurrency(position.averagePrice)}</Text>
        </View>
        <View style={styles.positionDetailRow}>
          <Text style={styles.positionDetailLabel}>Market Value</Text>
          <Text style={styles.positionDetailValue}>{formatCurrency(position.marketValue)}</Text>
        </View>
        <View style={styles.positionDetailRow}>
          <Text style={styles.positionDetailLabel}>Unrealized P&L</Text>
          <Text style={[
            styles.positionDetailValue,
            { color: position.unrealizedPnL >= 0 ? '#00ff88' : '#ff4444' }
          ]}>
            {formatCurrency(position.unrealizedPnL)} ({position.unrealizedPnLPercent.toFixed(2)}%)
          </Text>
        </View>
      </View>

      <View style={styles.positionActions}>
        <TouchableOpacity
          style={styles.closePositionButton}
          onPress={() => {
            // In a real app, this would open a close position modal
            Alert.alert('Close Position', 'Close position functionality would open here');
          }}
        >
          <Text style={styles.closePositionButtonText}>Close Position</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  const renderAccountTab = () => {
    if (!accountData?.accountInfo) return null;

    const account = accountData.accountInfo;

    return (
      <ScrollView style={styles.tabContent}>
        <View style={styles.accountCard}>
          <Text style={styles.accountTitle}>Account Information</Text>
          
          <View style={styles.accountRow}>
            <Text style={styles.accountLabel}>Buying Power</Text>
            <Text style={styles.accountValue}>{formatCurrency(account.buyingPower)}</Text>
          </View>
          
          <View style={styles.accountRow}>
            <Text style={styles.accountLabel}>Cash</Text>
            <Text style={styles.accountValue}>{formatCurrency(account.cash)}</Text>
          </View>
          
          <View style={styles.accountRow}>
            <Text style={styles.accountLabel}>Equity</Text>
            <Text style={styles.accountValue}>{formatCurrency(account.equity)}</Text>
          </View>
          
          <View style={styles.accountRow}>
            <Text style={styles.accountLabel}>Margin</Text>
            <Text style={styles.accountValue}>{formatCurrency(account.margin)}</Text>
          </View>
          
          <View style={styles.accountRow}>
            <Text style={styles.accountLabel}>Day Trading Buying Power</Text>
            <Text style={styles.accountValue}>{formatCurrency(account.dayTradingBuyingPower)}</Text>
          </View>
          
          <View style={styles.accountRow}>
            <Text style={styles.accountLabel}>Pattern Day Trader</Text>
            <Text style={[
              styles.accountValue,
              { color: account.patternDayTrader ? '#ff4444' : '#00ff88' }
            ]}>
              {account.patternDayTrader ? 'Yes' : 'No'}
            </Text>
          </View>
        </View>
      </ScrollView>
    );
  };

  const renderPlaceOrderTab = () => (
    <ScrollView style={styles.tabContent}>
      <View style={styles.orderFormCard}>
        <Text style={styles.orderFormTitle}>Place New Order</Text>
        
        {/* Symbol Input */}
        <View style={styles.inputGroup}>
          <Text style={styles.inputLabel}>Symbol</Text>
          <TextInput
            style={styles.textInput}
            value={orderForm.symbol}
            onChangeText={(text) => setOrderForm({ ...orderForm, symbol: text })}
            placeholder="Enter symbol (e.g., AAPL)"
            placeholderTextColor="#888"
          />
        </View>

        {/* Side Selection */}
        <View style={styles.inputGroup}>
          <Text style={styles.inputLabel}>Side</Text>
          <View style={styles.sideSelector}>
            <TouchableOpacity
              style={[
                styles.sideButton,
                orderForm.side === 'BUY' && styles.activeSideButton,
              ]}
              onPress={() => setOrderForm({ ...orderForm, side: 'BUY' })}
            >
              <Text style={[
                styles.sideButtonText,
                orderForm.side === 'BUY' && styles.activeSideButtonText,
              ]}>
                BUY
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[
                styles.sideButton,
                orderForm.side === 'SELL' && styles.activeSideButton,
              ]}
              onPress={() => setOrderForm({ ...orderForm, side: 'SELL' })}
            >
              <Text style={[
                styles.sideButtonText,
                orderForm.side === 'SELL' && styles.activeSideButtonText,
              ]}>
                SELL
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Order Type Selection */}
        <View style={styles.inputGroup}>
          <Text style={styles.inputLabel}>Order Type</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <View style={styles.orderTypeSelector}>
              {orderTypes.map((type) => (
                <TouchableOpacity
                  key={type.value}
                  style={[
                    styles.orderTypeButton,
                    selectedOrderType === type.value && styles.activeOrderTypeButton,
                  ]}
                  onPress={() => {
                    setSelectedOrderType(type.value);
                    setOrderForm({ ...orderForm, type: type.value });
                  }}
                >
                  <Text style={[
                    styles.orderTypeButtonText,
                    selectedOrderType === type.value && styles.activeOrderTypeButtonText,
                  ]}>
                    {type.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </ScrollView>
        </View>

        {/* Quantity Input */}
        <View style={styles.inputGroup}>
          <Text style={styles.inputLabel}>Quantity</Text>
          <TextInput
            style={styles.textInput}
            value={orderForm.quantity}
            onChangeText={(text) => setOrderForm({ ...orderForm, quantity: text })}
            placeholder="Enter quantity"
            placeholderTextColor="#888"
            keyboardType="numeric"
          />
        </View>

        {/* Price Input (for limit orders) */}
        {(selectedOrderType === 'LIMIT' || selectedOrderType === 'STOP_LIMIT') && (
          <View style={styles.inputGroup}>
            <Text style={styles.inputLabel}>Price</Text>
            <TextInput
              style={styles.textInput}
              value={orderForm.price}
              onChangeText={(text) => setOrderForm({ ...orderForm, price: text })}
              placeholder="Enter price"
              placeholderTextColor="#888"
              keyboardType="numeric"
            />
          </View>
        )}

        {/* Stop Price Input (for stop orders) */}
        {(selectedOrderType === 'STOP' || selectedOrderType === 'STOP_LIMIT') && (
          <View style={styles.inputGroup}>
            <Text style={styles.inputLabel}>Stop Price</Text>
            <TextInput
              style={styles.textInput}
              value={orderForm.stopPrice}
              onChangeText={(text) => setOrderForm({ ...orderForm, stopPrice: text })}
              placeholder="Enter stop price"
              placeholderTextColor="#888"
              keyboardType="numeric"
            />
          </View>
        )}

        {/* Time in Force Selection */}
        <View style={styles.inputGroup}>
          <Text style={styles.inputLabel}>Time in Force</Text>
          <View style={styles.timeInForceSelector}>
            {timeInForceOptions.map((option) => (
              <TouchableOpacity
                key={option.value}
                style={[
                  styles.timeInForceButton,
                  orderForm.timeInForce === option.value && styles.activeTimeInForceButton,
                ]}
                onPress={() => setOrderForm({ ...orderForm, timeInForce: option.value as 'DAY' | 'GTC' | 'IOC' | 'FOK' })}
              >
                <Text style={[
                  styles.timeInForceButtonText,
                  orderForm.timeInForce === option.value && styles.activeTimeInForceButtonText,
                ]}>
                  {option.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Place Order Button */}
        <TouchableOpacity
          style={styles.placeOrderButton}
          onPress={handlePlaceOrder}
        >
          <Text style={styles.placeOrderButtonText}>Place Order</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'orders':
        return (
          <ScrollView style={styles.tabContent}>
            {ordersData?.orders?.map(renderOrderCard)}
          </ScrollView>
        );
      case 'positions':
        return (
          <ScrollView style={styles.tabContent}>
            {positionsData?.positions?.map(renderPositionCard)}
          </ScrollView>
        );
      case 'account':
        return renderAccountTab();
      case 'place':
        return renderPlaceOrderTab();
      default:
        return null;
    }
  };

  if (accountLoading || positionsLoading || ordersLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#0F0" />
        <Text style={styles.loadingText}>Loading order management data...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Order Management</Text>
        <TouchableOpacity style={styles.headerButton}>
          <Ionicons name="settings-outline" size={24} color="#fff" />
        </TouchableOpacity>
      </View>

      {/* Tab Navigation */}
      <View style={styles.tabContainer}>
        {[
          { key: 'orders', label: 'Orders', icon: 'list-outline' },
          { key: 'positions', label: 'Positions', icon: 'trending-up-outline' },
          { key: 'account', label: 'Account', icon: 'person-outline' },
          { key: 'place', label: 'Place Order', icon: 'add-circle-outline' },
        ].map((tab) => (
          <TouchableOpacity
            key={tab.key}
            style={[
              styles.tabButton,
              activeTab === tab.key && styles.activeTabButton,
            ]}
            onPress={() => setActiveTab(tab.key as any)}
          >
            <Ionicons
              name={tab.icon as any}
              size={20}
              color={activeTab === tab.key ? '#0F0' : '#888'}
            />
            <Text style={[
              styles.tabText,
              activeTab === tab.key && styles.activeTabText,
            ]}>
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Tab Content */}
      <View style={styles.content}>
        {renderTabContent()}
      </View>

      {/* Order Details Modal */}
      <Modal
        visible={showOrderModal}
        animationType="slide"
        onRequestClose={() => setShowOrderModal(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Order Details</Text>
            <TouchableOpacity
              style={styles.modalCloseButton}
              onPress={() => setShowOrderModal(false)}
            >
              <Ionicons name="close" size={24} color="#fff" />
            </TouchableOpacity>
          </View>
          
          {selectedOrder && (
            <ScrollView style={styles.modalContent}>
              <View style={styles.modalOrderCard}>
                <Text style={styles.modalOrderSymbol}>{selectedOrder.symbol}</Text>
                <Text style={styles.modalOrderType}>{selectedOrder.type}</Text>
                <Text style={styles.modalOrderSide}>{selectedOrder.side}</Text>
                <Text style={styles.modalOrderQuantity}>Quantity: {selectedOrder.quantity}</Text>
                {selectedOrder.price && (
                  <Text style={styles.modalOrderPrice}>Price: {formatCurrency(selectedOrder.price)}</Text>
                )}
                <Text style={styles.modalOrderStatus}>Status: {selectedOrder.status}</Text>
                <Text style={styles.modalOrderTimestamp}>
                  Created: {formatTimestamp(selectedOrder.createdAt)}
                </Text>
              </View>
            </ScrollView>
          )}
        </View>
      </Modal>
    </View>
  );
};

// Styles
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000',
  },
  loadingText: {
    color: '#0F0',
    marginTop: 10,
    fontSize: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 15,
    backgroundColor: '#1a1a1a',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  headerButton: {
    padding: 5,
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#1a1a1a',
    paddingHorizontal: 20,
  },
  tabButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 15,
    marginHorizontal: 5,
  },
  activeTabButton: {
    borderBottomWidth: 2,
    borderBottomColor: '#0F0',
  },
  tabText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#888',
    fontWeight: '500',
  },
  activeTabText: {
    color: '#0F0',
    fontWeight: 'bold',
  },
  content: {
    flex: 1,
  },
  tabContent: {
    flex: 1,
  },
  orderCard: {
    backgroundColor: '#1a1a1a',
    marginHorizontal: 20,
    marginVertical: 10,
    borderRadius: 12,
    padding: 20,
  },
  orderHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  orderSymbolRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  orderSymbol: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginRight: 10,
  },
  orderSide: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  orderSideText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#000',
  },
  orderType: {
    fontSize: 14,
    color: '#888',
  },
  orderDetails: {
    marginBottom: 15,
  },
  orderDetailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  orderDetailLabel: {
    fontSize: 14,
    color: '#888',
  },
  orderDetailValue: {
    fontSize: 14,
    color: '#fff',
    fontWeight: '500',
  },
  orderFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  orderStatusRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  orderStatusLabel: {
    fontSize: 14,
    color: '#888',
    marginRight: 8,
  },
  orderStatus: {
    fontSize: 14,
    fontWeight: 'bold',
  },
  orderTimestamp: {
    fontSize: 12,
    color: '#888',
  },
  orderActions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  cancelButton: {
    backgroundColor: '#ff4444',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
  },
  cancelButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  modifyButton: {
    backgroundColor: '#007bff',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
  },
  modifyButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  positionCard: {
    backgroundColor: '#1a1a1a',
    marginHorizontal: 20,
    marginVertical: 10,
    borderRadius: 12,
    padding: 20,
  },
  positionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  positionSymbol: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
  },
  positionSide: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  positionSideText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#000',
  },
  positionDetails: {
    marginBottom: 15,
  },
  positionDetailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  positionDetailLabel: {
    fontSize: 14,
    color: '#888',
  },
  positionDetailValue: {
    fontSize: 14,
    color: '#fff',
    fontWeight: '500',
  },
  positionActions: {
    alignItems: 'center',
  },
  closePositionButton: {
    backgroundColor: '#ff4444',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
  },
  closePositionButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  accountCard: {
    backgroundColor: '#1a1a1a',
    margin: 20,
    borderRadius: 12,
    padding: 20,
  },
  accountTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 15,
  },
  accountRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  accountLabel: {
    fontSize: 16,
    color: '#ccc',
  },
  accountValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  orderFormCard: {
    backgroundColor: '#1a1a1a',
    margin: 20,
    borderRadius: 12,
    padding: 20,
  },
  orderFormTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 20,
  },
  inputGroup: {
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 16,
    color: '#ccc',
    marginBottom: 8,
  },
  textInput: {
    backgroundColor: '#333',
    borderRadius: 8,
    padding: 15,
    fontSize: 16,
    color: '#fff',
    borderWidth: 1,
    borderColor: '#555',
  },
  sideSelector: {
    flexDirection: 'row',
  },
  sideButton: {
    flex: 1,
    paddingVertical: 15,
    marginHorizontal: 5,
    borderRadius: 8,
    backgroundColor: '#333',
    alignItems: 'center',
  },
  activeSideButton: {
    backgroundColor: '#007bff',
  },
  sideButtonText: {
    fontSize: 16,
    color: '#fff',
    fontWeight: '500',
  },
  activeSideButtonText: {
    fontWeight: 'bold',
  },
  orderTypeSelector: {
    flexDirection: 'row',
  },
  orderTypeButton: {
    paddingHorizontal: 15,
    paddingVertical: 10,
    marginRight: 10,
    borderRadius: 20,
    backgroundColor: '#333',
  },
  activeOrderTypeButton: {
    backgroundColor: '#007bff',
  },
  orderTypeButtonText: {
    fontSize: 14,
    color: '#fff',
    fontWeight: '500',
  },
  activeOrderTypeButtonText: {
    fontWeight: 'bold',
  },
  timeInForceSelector: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  timeInForceButton: {
    paddingHorizontal: 15,
    paddingVertical: 10,
    marginRight: 10,
    marginBottom: 10,
    borderRadius: 20,
    backgroundColor: '#333',
  },
  activeTimeInForceButton: {
    backgroundColor: '#007bff',
  },
  timeInForceButtonText: {
    fontSize: 14,
    color: '#fff',
    fontWeight: '500',
  },
  activeTimeInForceButtonText: {
    fontWeight: 'bold',
  },
  placeOrderButton: {
    backgroundColor: '#0F0',
    paddingVertical: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 20,
  },
  placeOrderButtonText: {
    color: '#000',
    fontSize: 18,
    fontWeight: 'bold',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#000',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 15,
    backgroundColor: '#1a1a1a',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  modalCloseButton: {
    padding: 5,
  },
  modalContent: {
    flex: 1,
    padding: 20,
  },
  modalOrderCard: {
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 20,
  },
  modalOrderSymbol: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 10,
  },
  modalOrderType: {
    fontSize: 18,
    color: '#ccc',
    marginBottom: 5,
  },
  modalOrderSide: {
    fontSize: 18,
    color: '#ccc',
    marginBottom: 5,
  },
  modalOrderQuantity: {
    fontSize: 16,
    color: '#ccc',
    marginBottom: 5,
  },
  modalOrderPrice: {
    fontSize: 16,
    color: '#ccc',
    marginBottom: 5,
  },
  modalOrderStatus: {
    fontSize: 16,
    color: '#ccc',
    marginBottom: 5,
  },
  modalOrderTimestamp: {
    fontSize: 16,
    color: '#ccc',
  },
});

export default OrderManagement;
