import React, { useState, useEffect, useMemo, useRef } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput, Alert,
  ActivityIndicator, SafeAreaView, Modal, FlatList, RefreshControl
} from 'react-native';
import { useQuery, useMutation } from '@apollo/client';
import { gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import { FEATURES } from '../../../config/featureFlags';
import LicensingDisclosureScreen from '../../../components/LicensingDisclosureScreen';

// GraphQL Queries and Mutations
const GET_CRYPTO_ASSETS = gql`
  query GetCryptoAssets($status: String) {
    cryptoAssets(status: $status)
  }
`;

const GET_ALPACA_CRYPTO_ACCOUNT = gql`
  query GetAlpacaCryptoAccount($userId: Int!) {
    alpacaCryptoAccount(userId: $userId) {
      id
      status
      alpacaCryptoAccountId
      isApproved
      usdBalance
      totalCryptoValue
      createdAt
    }
  }
`;

const GET_ALPACA_CRYPTO_BALANCES = gql`
  query GetAlpacaCryptoBalances($accountId: Int!) {
    alpacaCryptoBalances(accountId: $accountId) {
      id
      symbol
      totalAmount
      availableAmount
      usdValue
      updatedAt
    }
  }
`;

const GET_ALPACA_CRYPTO_ORDERS = gql`
  query GetAlpacaCryptoOrders($accountId: Int!, $status: String) {
    alpacaCryptoOrders(accountId: $accountId, status: $status) {
      id
      symbol
      qty
      notional
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

const CREATE_ALPACA_CRYPTO_ORDER = gql`
  mutation CreateAlpacaCryptoOrder(
    $accountId: Int!
    $symbol: String!
    $qty: Decimal
    $notional: Decimal
    $side: String!
    $type: String!
    $timeInForce: String!
    $limitPrice: Decimal
    $stopPrice: Decimal
  ) {
    createAlpacaCryptoOrder(
      accountId: $accountId
      symbol: $symbol
      qty: $qty
      notional: $notional
      side: $side
      type: $type
      timeInForce: $timeInForce
      limitPrice: $limitPrice
      stopPrice: $stopPrice
    ) {
      id
      symbol
      side
      type
      status
      createdAt
    }
  }
`;

const CREATE_ALPACA_CRYPTO_ACCOUNT = gql`
  mutation CreateAlpacaCryptoAccount($userId: Int!, $alpacaAccountId: Int) {
    createAlpacaCryptoAccount(userId: $userId, alpacaAccountId: $alpacaAccountId) {
      id
      status
      alpacaCryptoAccountId
      isApproved
      createdAt
    }
  }
`;

// Constants
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
  warningSoft: '#FEF3C7',
  shadow: 'rgba(16,24,40,0.08)',
};

interface CryptoTradingScreenProps {
  navigation: any;
}

const CryptoTradingScreen: React.FC<CryptoTradingScreenProps> = ({ navigation }) => {
  const [showLicensingDisclosure, setShowLicensingDisclosure] = useState(false);

  const [activeTab, setActiveTab] = useState<'overview' | 'orders' | 'assets'>('overview');
  const [refreshing, setRefreshing] = useState(false);
  const [showOrderModal, setShowOrderModal] = useState(false);
  const [orderType, setOrderType] = useState<'market' | 'limit'>('market');
  const [orderSide, setOrderSide] = useState<'buy' | 'sell'>('buy');
  const [selectedAsset, setSelectedAsset] = useState('');
  const [quantity, setQuantity] = useState('');
  const [notional, setNotional] = useState('');
  const [price, setPrice] = useState('');
  const [isPlacingOrder, setIsPlacingOrder] = useState(false);

  // Mutations
  const [createCryptoOrder] = useMutation(CREATE_ALPACA_CRYPTO_ORDER);
  const [createCryptoAccount] = useMutation(CREATE_ALPACA_CRYPTO_ACCOUNT);

  // Queries
  const { data: cryptoAssetsData, loading: cryptoAssetsLoading, refetch: refetchCryptoAssets } =
    useQuery(GET_CRYPTO_ASSETS, { 
      variables: { status: 'active' },
      errorPolicy: 'all'
    });

  const { data: cryptoAccountData, loading: cryptoAccountLoading, refetch: refetchCryptoAccount } =
    useQuery(GET_ALPACA_CRYPTO_ACCOUNT, { 
      variables: { userId: 1 }, // This should come from auth context
      errorPolicy: 'all'
    });

  const { data: cryptoBalancesData, loading: cryptoBalancesLoading, refetch: refetchCryptoBalances } =
    useQuery(GET_ALPACA_CRYPTO_BALANCES, { 
      variables: { accountId: cryptoAccountData?.alpacaCryptoAccount?.id || 0 },
      errorPolicy: 'all',
      skip: !cryptoAccountData?.alpacaCryptoAccount?.id
    });

  const { data: cryptoOrdersData, loading: cryptoOrdersLoading, refetch: refetchCryptoOrders } =
    useQuery(GET_ALPACA_CRYPTO_ORDERS, { 
      variables: { accountId: cryptoAccountData?.alpacaCryptoAccount?.id || 0 },
      errorPolicy: 'all',
      skip: !cryptoAccountData?.alpacaCryptoAccount?.id
    });

  // Data
  const cryptoAccount = cryptoAccountData?.alpacaCryptoAccount;
  const cryptoBalances = useMemo(() => cryptoBalancesData?.alpacaCryptoBalances ?? [], [cryptoBalancesData]);
  const cryptoOrders = useMemo(() => cryptoOrdersData?.alpacaCryptoOrders ?? [], [cryptoOrdersData]);
  const cryptoAssets = useMemo(() => cryptoAssetsData?.cryptoAssets ?? [], [cryptoAssetsData]);

  // Popular crypto pairs
  const popularPairs = ['BTC/USD', 'ETH/USD', 'ADA/USD', 'SOL/USD', 'DOT/USD', 'MATIC/USD'];

  const onRefresh = async () => {
    setRefreshing(true);
    try {
      await Promise.all([
        refetchCryptoAccount(),
        refetchCryptoBalances(),
        refetchCryptoOrders(),
        refetchCryptoAssets(),
      ]);
    } finally {
      setRefreshing(false);
    }
  };

  const handlePlaceOrder = async () => {
    // Block trading if feature is disabled
    if (!FEATURES.CRYPTO_TRADING_ENABLED) {
      Alert.alert(
        'Trading Not Available',
        FEATURES.CRYPTO_TRADING_MESSAGE,
        [
          { text: 'Cancel', style: 'cancel' },
          { 
            text: 'View Licensing Info', 
            onPress: () => setShowLicensingDisclosure(true)
          }
        ]
      );
      return;
    }

    if (!cryptoAccount) {
      Alert.alert(
        'Crypto Account Required',
        'You need a crypto trading account to place orders. Would you like to create one?',
        [
          { text: 'Cancel', style: 'cancel' },
          { 
            text: 'Create Account', 
            onPress: async () => {
              try {
                const accountRes = await createCryptoAccount({ 
                  variables: { userId: 1 } // This should come from auth context
                });
                
                if (accountRes?.data?.createAlpacaCryptoAccount) {
                  Alert.alert(
                    'Account Created',
                    'Your crypto account has been created. Please complete the KYC process to start trading.',
                    [{ text: 'OK', onPress: () => refetchCryptoAccount() }]
                  );
                } else {
                  Alert.alert('Account Creation Failed', 'Could not create crypto account. Please try again.');
                }
              } catch (e: any) {
                Alert.alert('Account Creation Failed', e?.message || 'Could not create crypto account.');
              }
            }
          }
        ]
      );
      return;
    }

    if (!cryptoAccount.isApproved) {
      Alert.alert(
        'Account Not Approved',
        'Your crypto account is not yet approved for trading. Please complete the KYC process first.',
        [{ text: 'OK' }]
      );
      return;
    }

    if (!selectedAsset || (!quantity && !notional)) {
      Alert.alert('Error', 'Please select an asset and enter quantity or notional amount');
      return;
    }

    setIsPlacingOrder(true);
    try {
      const orderVariables: any = {
        accountId: cryptoAccount.id,
        symbol: `${selectedAsset}/USD`, // Convert BTC to BTC/USD format
        side: orderSide.toUpperCase(),
        type: orderType.toUpperCase(),
        timeInForce: 'DAY'
      };

      if (orderType === 'market') {
        if (notional) {
          orderVariables.notional = parseFloat(notional);
        } else if (quantity) {
          orderVariables.qty = parseFloat(quantity);
        }
      } else {
        if (quantity) {
          orderVariables.qty = parseFloat(quantity);
        }
        if (price) {
          orderVariables.limitPrice = parseFloat(price);
        }
      }

      const result = await createCryptoOrder({ variables: orderVariables });
      
      if (result.data?.createAlpacaCryptoOrder) {
        Alert.alert(
          'Order Placed Successfully',
          `Your ${orderType} ${orderSide} order for ${selectedAsset} has been placed.`,
          [{ text: 'OK' }]
        );
        setShowOrderModal(false);
        resetOrderForm();
        refetchCryptoOrders();
        refetchCryptoBalances();
      } else {
        Alert.alert('Order Failed', 'Could not place order. Please try again.');
      }
    } catch (error: any) {
      Alert.alert('Order Failed', error.message || 'Could not place order. Please try again.');
    } finally {
      setIsPlacingOrder(false);
    }
  };

  const resetOrderForm = () => {
    setSelectedAsset('');
    setQuantity('');
    setNotional('');
    setPrice('');
    setOrderType('market');
    setOrderSide('buy');
  };

  const formatMoney = (value: number) => `$${(value || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

  const renderOverview = () => {
    return (
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Account Summary */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>Crypto Account</Text>
            {cryptoAccount?.status && (
              <View style={[
                styles.statusBadge,
                { backgroundColor: cryptoAccount.isApproved ? C.successSoft : C.warningSoft }
              ]}>
                <Text style={[
                  styles.statusText,
                  { color: cryptoAccount.isApproved ? C.green : C.amber }
                ]}>
                  {cryptoAccount.status.toUpperCase()}
                </Text>
              </View>
            )}
          </View>

          {cryptoAccountLoading && (
            <View style={styles.loadingContainer}>
              <ActivityIndicator color={C.primary} />
              <Text style={styles.loadingText}>Loading account...</Text>
            </View>
          )}

          {!cryptoAccountLoading && cryptoAccount && (
            <View style={styles.accountGrid}>
              <View style={styles.accountItem}>
                <Text style={styles.accountLabel}>USD Balance</Text>
                <Text style={styles.accountValue}>{formatMoney(cryptoAccount.usdBalance)}</Text>
              </View>
              <View style={styles.accountItem}>
                <Text style={styles.accountLabel}>Total Crypto Value</Text>
                <Text style={styles.accountValue}>{formatMoney(cryptoAccount.totalCryptoValue)}</Text>
              </View>
            </View>
          )}

          {!cryptoAccountLoading && !cryptoAccount && (
            <View style={styles.emptyState}>
              <Icon name="wallet" size={40} color={C.sub} />
              <Text style={styles.emptyTitle}>No Crypto Account</Text>
              <Text style={styles.emptySubtitle}>Create a crypto account to start trading</Text>
              <TouchableOpacity 
                style={styles.createAccountButton}
                onPress={async () => {
                  try {
                    const accountRes = await createCryptoAccount({ 
                      variables: { userId: 1 }
                    });
                    
                    if (accountRes?.data?.createAlpacaCryptoAccount) {
                      Alert.alert(
                        'Account Created',
                        'Your crypto account has been created. Please complete the KYC process to start trading.',
                        [{ text: 'OK', onPress: () => refetchCryptoAccount() }]
                      );
                    }
                  } catch (e: any) {
                    Alert.alert('Account Creation Failed', e?.message || 'Could not create crypto account.');
                  }
                }}
              >
                <Text style={styles.createAccountButtonText}>Create Crypto Account</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>

        {/* Balances */}
        {cryptoBalances.length > 0 && (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Text style={styles.cardTitle}>Crypto Balances</Text>
              <TouchableOpacity onPress={onRefresh}>
                <Icon name="refresh-ccw" size={18} color={C.sub} />
              </TouchableOpacity>
            </View>

            {cryptoBalancesLoading && (
              <View style={styles.loadingContainer}>
                <ActivityIndicator color={C.primary} />
                <Text style={styles.loadingText}>Loading balances...</Text>
              </View>
            )}

            {!cryptoBalancesLoading && cryptoBalances.map((balance: any) => (
              <View key={balance.id} style={styles.balanceRow}>
                <View style={styles.balanceInfo}>
                  <Text style={styles.balanceSymbol}>{balance.symbol}</Text>
                  <Text style={styles.balanceAmount}>
                    {parseFloat(balance.totalAmount).toFixed(6)} {balance.symbol.split('/')[0]}
                  </Text>
                </View>
                <View style={styles.balanceValue}>
                  <Text style={styles.balanceUsdValue}>{formatMoney(balance.usdValue)}</Text>
                  <Text style={styles.balanceAvailable}>
                    Available: {parseFloat(balance.availableAmount).toFixed(6)}
                  </Text>
                </View>
              </View>
            ))}
          </View>
        )}

        {/* Popular Pairs */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>Popular Pairs</Text>
          </View>
          <View style={styles.pairsGrid}>
            {popularPairs.map((pair) => (
              <TouchableOpacity
                key={pair}
                style={styles.pairButton}
                onPress={() => {
                  setSelectedAsset(pair);
                  setShowOrderModal(true);
                }}
              >
                <Text style={styles.pairText}>{pair}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      </ScrollView>
    );
  };

  const renderOrders = () => {
    return (
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>Recent Orders</Text>
            <TouchableOpacity onPress={onRefresh}>
              <Icon name="refresh-ccw" size={18} color={C.sub} />
            </TouchableOpacity>
          </View>

          {cryptoOrdersLoading && (
            <View style={styles.loadingContainer}>
              <ActivityIndicator color={C.primary} />
              <Text style={styles.loadingText}>Loading orders...</Text>
            </View>
          )}

          {!cryptoOrdersLoading && cryptoOrders.length === 0 && (
            <View style={styles.emptyState}>
              <Icon name="clipboard" size={40} color={C.sub} />
              <Text style={styles.emptyTitle}>No Orders Yet</Text>
              <Text style={styles.emptySubtitle}>Place your first crypto order to get started</Text>
            </View>
          )}

          {!cryptoOrdersLoading && cryptoOrders.map((order: any) => (
            <View key={order.id} style={styles.orderRow}>
              <View style={styles.orderInfo}>
                <View style={styles.orderHeader}>
                  <Text style={styles.orderSymbol}>{order.symbol}</Text>
                  <View style={[
                    styles.orderSideBadge,
                    { backgroundColor: order.side === 'BUY' ? C.successSoft : C.dangerSoft }
                  ]}>
                    <Text style={[
                      styles.orderSideText,
                      { color: order.side === 'BUY' ? C.green : C.red }
                    ]}>
                      {order.side}
                    </Text>
                  </View>
                </View>
                <Text style={styles.orderDetails}>
                  {order.qty ? `${order.qty} ${order.symbol.split('/')[0]}` : `$${order.notional}`} • {order.type}
                </Text>
                <Text style={styles.orderTime}>
                  {new Date(order.createdAt).toLocaleString()}
                </Text>
              </View>
              <View style={[
                styles.orderStatusBadge,
                { backgroundColor: order.status === 'FILLED' ? C.successSoft : C.warningSoft }
              ]}>
                <Text style={[
                  styles.orderStatusText,
                  { color: order.status === 'FILLED' ? C.green : C.amber }
                ]}>
                  {order.status}
                </Text>
              </View>
            </View>
          ))}
        </View>
      </ScrollView>
    );
  };

  const renderAssets = () => {
    return (
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>Available Assets</Text>
            <TouchableOpacity onPress={onRefresh}>
              <Icon name="refresh-ccw" size={18} color={C.sub} />
            </TouchableOpacity>
          </View>

          {cryptoAssetsLoading && (
            <View style={styles.loadingContainer}>
              <ActivityIndicator color={C.primary} />
              <Text style={styles.loadingText}>Loading assets...</Text>
            </View>
          )}

          {!cryptoAssetsLoading && cryptoAssets.length === 0 && (
            <View style={styles.emptyState}>
              <Icon name="trending-up" size={40} color={C.sub} />
              <Text style={styles.emptyTitle}>No Assets Available</Text>
              <Text style={styles.emptySubtitle}>Check back later for available crypto assets</Text>
            </View>
          )}

          {!cryptoAssetsLoading && cryptoAssets.map((asset: string) => (
            <TouchableOpacity
              key={asset}
              style={styles.assetRow}
              onPress={() => {
                setSelectedAsset(asset);
                setShowOrderModal(true);
              }}
            >
              <View style={styles.assetInfo}>
                <Text style={styles.assetSymbol}>{asset}</Text>
                <Text style={styles.assetName}>
                  {asset.split('/')[0]} / {asset.split('/')[1]}
                </Text>
              </View>
              <Icon name="chevron-right" size={20} color={C.sub} />
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>
    );
  };

  const renderOrderModal = () => {
    return (
      <Modal visible={showOrderModal} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={styles.modal}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Place Crypto Order</Text>
            <TouchableOpacity onPress={() => setShowOrderModal(false)}>
              <Icon name="x" size={24} color={C.text} />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalContent} showsVerticalScrollIndicator={false}>
            {/* Order Type */}
            <Text style={styles.inputLabel}>Order Type</Text>
            <View style={styles.pillRow}>
              {(['market', 'limit'] as const).map(type => (
                <TouchableOpacity
                  key={type}
                  onPress={() => setOrderType(type)}
                  style={[styles.pill, orderType === type && styles.pillActive]}
                >
                  <Text style={[styles.pillText, orderType === type && styles.pillTextActive]}>
                    {type.toUpperCase()}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            {/* Side */}
            <Text style={[styles.inputLabel, { marginTop: 16 }]}>Side</Text>
            <View style={styles.pillRow}>
              {(['buy', 'sell'] as const).map(side => (
                <TouchableOpacity
                  key={side}
                  onPress={() => setOrderSide(side)}
                  style={[
                    styles.pill,
                    orderSide === side && (side === 'buy' ? styles.pillBuy : styles.pillSell)
                  ]}
                >
                  <Text style={[styles.pillText, orderSide === side && styles.pillTextActive]}>
                    {side.toUpperCase()}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            {/* Asset */}
            <View style={{ marginTop: 16 }}>
              <Text style={styles.inputLabel}>Asset</Text>
              <TextInput
                style={styles.input}
                value={selectedAsset}
                onChangeText={setSelectedAsset}
                placeholder="e.g., BTC/USD"
                autoCapitalize="characters"
              />
            </View>

            {/* Quantity or Notional */}
            {orderType === 'market' ? (
              <View style={{ marginTop: 12 }}>
                <Text style={styles.inputLabel}>Notional Amount (USD)</Text>
                <TextInput
                  style={styles.input}
                  value={notional}
                  onChangeText={setNotional}
                  placeholder="Amount in USD"
                  keyboardType="numeric"
                />
              </View>
            ) : (
              <View style={{ marginTop: 12 }}>
                <Text style={styles.inputLabel}>Quantity</Text>
                <TextInput
                  style={styles.input}
                  value={quantity}
                  onChangeText={setQuantity}
                  placeholder="Amount of crypto"
                  keyboardType="numeric"
                />
              </View>
            )}

            {/* Limit Price */}
            {orderType === 'limit' && (
              <View style={{ marginTop: 12 }}>
                <Text style={styles.inputLabel}>Limit Price</Text>
                <TextInput
                  style={styles.input}
                  value={price}
                  onChangeText={setPrice}
                  placeholder="Price per unit"
                  keyboardType="numeric"
                />
              </View>
            )}

            <TouchableOpacity
              style={[styles.placeOrderButton, isPlacingOrder && { opacity: 0.6 }]}
              onPress={handlePlaceOrder}
              disabled={isPlacingOrder}
            >
              {isPlacingOrder ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.placeOrderButtonText}>Place Order</Text>
              )}
            </TouchableOpacity>
          </ScrollView>
        </SafeAreaView>
      </Modal>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Icon name="arrow-left" size={24} color={C.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Crypto Trading</Text>
        <TouchableOpacity onPress={() => setShowOrderModal(true)} style={styles.headerAction}>
          <Icon name="plus" size={20} color={C.primary} />
          <Text style={styles.headerActionText}>Trade</Text>
        </TouchableOpacity>
      </View>

      {/* Tabs */}
      <View style={styles.tabs}>
        {(['overview', 'orders', 'assets'] as const).map(tab => (
          <TouchableOpacity
            key={tab}
            onPress={() => setActiveTab(tab)}
            style={[styles.tab, activeTab === tab && styles.tabActive]}
          >
            <Text style={[styles.tabText, activeTab === tab && styles.tabTextActive]}>
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Content */}
      <View style={{ flex: 1 }}>
        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'orders' && renderOrders()}
        {activeTab === 'assets' && renderAssets()}
      </View>

      {renderOrderModal()}

      {/* Licensing Disclosure Modal */}
      <Modal
        visible={showLicensingDisclosure}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setShowLicensingDisclosure(false)}
      >
        <LicensingDisclosureScreen onClose={() => setShowLicensingDisclosure(false)} />
      </Modal>
    </SafeAreaView>
    </>
  );
};

// Styles
const styles = StyleSheet.create({
  disabledContainer: {
    flex: 1,
    backgroundColor: '#F5F6FA',
  },
  disabledContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  disabledTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1C1C1E',
    marginTop: 24,
    marginBottom: 12,
    textAlign: 'center',
  },
  disabledMessage: {
    fontSize: 16,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 32,
  },
  linkButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 20,
    backgroundColor: '#F5F6FA',
    borderRadius: 12,
    marginBottom: 16,
    gap: 8,
  },
  linkText: {
    fontSize: 16,
    color: '#007AFF',
    fontWeight: '600',
  },
  backButton: {
    paddingVertical: 12,
    paddingHorizontal: 24,
    backgroundColor: '#007AFF',
    borderRadius: 12,
    marginTop: 8,
  },
  backButtonText: {
    fontSize: 16,
    color: '#FFFFFF',
    fontWeight: '600',
  },
  container: {
    flex: 1,
    backgroundColor: C.bg,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: C.card,
    borderBottomWidth: 1,
    borderBottomColor: C.line,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: C.text,
  },
  headerAction: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: '#F4F7FF',
  },
  headerActionText: {
    color: C.primary,
    fontWeight: '700',
  },
  tabs: {
    flexDirection: 'row',
    backgroundColor: C.bg,
    padding: 12,
    gap: 8,
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 999,
    alignItems: 'center',
    backgroundColor: '#E9EDF7',
  },
  tabActive: {
    backgroundColor: C.card,
    borderWidth: 1,
    borderColor: C.line,
  },
  tabText: {
    color: '#5B6473',
    fontWeight: '600',
  },
  tabTextActive: {
    color: C.text,
  },
  content: {
    flex: 1,
    paddingHorizontal: 16,
  },
  card: {
    backgroundColor: C.card,
    borderRadius: 16,
    padding: 16,
    marginTop: 12,
    shadowColor: C.shadow,
    shadowOpacity: 1,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: C.text,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 20,
  },
  loadingText: {
    marginLeft: 8,
    color: C.sub,
  },
  accountGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  accountItem: {
    width: '50%',
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderRightWidth: 1,
    borderRightColor: C.line,
    borderBottomWidth: 1,
    borderBottomColor: C.line,
  },
  accountLabel: {
    fontSize: 12,
    color: C.sub,
    marginBottom: 4,
  },
  accountValue: {
    fontSize: 16,
    fontWeight: '700',
    color: C.text,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: C.text,
    marginTop: 12,
    marginBottom: 4,
  },
  emptySubtitle: {
    fontSize: 14,
    color: C.sub,
    textAlign: 'center',
    marginBottom: 20,
  },
  createAccountButton: {
    backgroundColor: C.primary,
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
  },
  createAccountButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  balanceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: C.line,
  },
  balanceInfo: {
    flex: 1,
  },
  balanceSymbol: {
    fontSize: 16,
    fontWeight: '700',
    color: C.text,
  },
  balanceAmount: {
    fontSize: 14,
    color: C.sub,
    marginTop: 2,
  },
  balanceValue: {
    alignItems: 'flex-end',
  },
  balanceUsdValue: {
    fontSize: 16,
    fontWeight: '700',
    color: C.text,
  },
  balanceAvailable: {
    fontSize: 12,
    color: C.sub,
    marginTop: 2,
  },
  pairsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  pairButton: {
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: C.line,
  },
  pairText: {
    fontSize: 14,
    fontWeight: '600',
    color: C.text,
  },
  orderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: C.line,
  },
  orderInfo: {
    flex: 1,
  },
  orderHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 4,
  },
  orderSymbol: {
    fontSize: 16,
    fontWeight: '700',
    color: C.text,
  },
  orderSideBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  orderSideText: {
    fontSize: 12,
    fontWeight: '600',
  },
  orderDetails: {
    fontSize: 14,
    color: C.sub,
    marginBottom: 2,
  },
  orderTime: {
    fontSize: 12,
    color: C.sub,
  },
  orderStatusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  orderStatusText: {
    fontSize: 12,
    fontWeight: '600',
  },
  assetRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: C.line,
  },
  assetInfo: {
    flex: 1,
  },
  assetSymbol: {
    fontSize: 16,
    fontWeight: '700',
    color: C.text,
  },
  assetName: {
    fontSize: 14,
    color: C.sub,
    marginTop: 2,
  },
  modal: {
    flex: 1,
    backgroundColor: C.bg,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 12,
    backgroundColor: C.card,
    borderBottomWidth: 1,
    borderBottomColor: C.line,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: C.text,
  },
  modalContent: {
    paddingHorizontal: 20,
  },
  inputLabel: {
    fontWeight: '700',
    color: C.text,
    marginBottom: 6,
  },
  input: {
    backgroundColor: C.card,
    borderWidth: 1,
    borderColor: C.line,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 16,
  },
  pillRow: {
    flexDirection: 'row',
    gap: 8,
  },
  pill: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 999,
    alignItems: 'center',
    backgroundColor: '#EEF2F7',
  },
  pillActive: {
    backgroundColor: C.primary,
  },
  pillBuy: {
    backgroundColor: C.green,
  },
  pillSell: {
    backgroundColor: C.red,
  },
  pillText: {
    fontWeight: '700',
    color: '#5B6473',
  },
  pillTextActive: {
    color: '#fff',
  },
  placeOrderButton: {
    backgroundColor: C.primary,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 20,
    marginBottom: 20,
  },
  placeOrderButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '800',
  },
});

export default CryptoTradingScreen;
