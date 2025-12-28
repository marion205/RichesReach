/**
 * Crypto Trading Card (Pro++ with Stop / Take-Profit)
 */

import React, { useEffect, useMemo, useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, TextInput, TouchableOpacity, Alert,
  ActivityIndicator, ScrollView, Modal, FlatList, Platform, Image
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import CryptoIcon from './CryptoIcon';
import { useQuery, useMutation } from '@apollo/client';
import {
  GET_SUPPORTED_CURRENCIES,
  GET_CRYPTO_PRICE,
  EXECUTE_CRYPTO_TRADE,
} from '../../cryptoQueries';
import { FEATURES } from '../../config/featureFlags';
import LicensingDisclosureScreen from '../LicensingDisclosureScreen';

type TradeSide = 'BUY' | 'SELL';
type InputMode = 'QTY' | 'USD';
type OrderType = 'MARKET' | 'LIMIT' | 'STOP_MARKET' | 'STOP_LIMIT' | 'TAKE_PROFIT_LIMIT';
type TimeInForce = 'GTC' | 'IOC' | 'FOK' | 'DAY';

interface CryptoTradingCardProps {
  onTradeSuccess: () => void;
  balances?: Record<string, number>;
  usdAvailable?: number;
  defaultSymbol?: string;
  /** Optional local icon map: { BTC: require('.../btc.png'), ETH: require('.../eth.png'), ... } */
  assetIcons?: Record<string, any>;
}

const FEE_RATE = 0.001;          // 0.10%
const SLIPPAGE_BPS = 50;         // 0.50% estimate for preview

const CryptoTradingCardPro: React.FC<CryptoTradingCardProps> = ({
  onTradeSuccess, balances, usdAvailable, defaultSymbol = 'BTC', assetIcons = {},
}) => {
  const [showLicensingDisclosure, setShowLicensingDisclosure] = useState(false);
  const [selectedSymbol, setSelectedSymbol] = useState(defaultSymbol);
  const [tradeType, setTradeType] = useState<TradeSide>('BUY');

  const [orderType, setOrderType] = useState<OrderType>('MARKET');
  const [timeInForce, setTimeInForce] = useState<TimeInForce>('GTC');

  const [mode, setMode] = useState<InputMode>('QTY');
  const [qty, setQty] = useState('');
  const [usd, setUsd] = useState('');

  // Price fields
  const [limitPrice, setLimitPrice] = useState('');    // used by LIMIT / STOP_LIMIT / TP_LIMIT
  const [triggerPrice, setTriggerPrice] = useState(''); // used by STOP_MARKET / STOP_LIMIT

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [error, setError] = useState('');

  // Picker state
  const [pickerOpen, setPickerOpen] = useState(false);

  // Help tooltips
  const [showOrderTypeHelp, setShowOrderTypeHelp] = useState(false);
  const [showTifHelp, setShowTifHelp] = useState(false);
  const [showRiskWarning, setShowRiskWarning] = useState(true);

  const { data: currenciesData, loading: currenciesLoading } = useQuery(GET_SUPPORTED_CURRENCIES);
  const { data: priceData, loading: priceLoading, refetch: refetchPrice } = useQuery(
    GET_CRYPTO_PRICE, { 
      variables: { symbol: selectedSymbol }, 
      skip: !selectedSymbol,
      fetchPolicy: 'cache-and-network',
      nextFetchPolicy: 'cache-first',
      errorPolicy: 'all'
    }
  );

  // Force refresh price data when component mounts or symbol changes
  useEffect(() => {
    if (selectedSymbol) {
      console.log(`[Crypto Trading] Refreshing price for ${selectedSymbol}`);
      refetchPrice();
    }
  }, [selectedSymbol, refetchPrice]);
  const [executeTrade] = useMutation(EXECUTE_CRYPTO_TRADE, {
    optimisticResponse: (variables) => ({
      executeCryptoTrade: {
        __typename: 'ExecuteCryptoTradeResponse',
        ok: true,
        trade: {
          __typename: 'CryptoTrade',
          id: `temp-${Date.now()}`,
          orderId: `temp-order-${Date.now()}`,
          symbol: variables.symbol,
          tradeType: variables.tradeType,
          quantity: variables.quantity,
          pricePerUnit: orderType === 'LIMIT' ? variables.pricePerUnit : (priceData?.cryptoPrice?.price || 0),
          totalAmount: variables.quantity * (orderType === 'LIMIT' ? variables.pricePerUnit : (priceData?.cryptoPrice?.price || 0)),
          status: 'PENDING',
          createdAt: new Date().toISOString(),
        },
        error: null,
      },
    }),
    update: (cache, { data }) => {
      if (data?.executeCryptoTrade?.ok) {
        // Update portfolio cache optimistically
        cache.modify({
          fields: {
            cryptoPortfolio(existing) {
              // Add the new trade to the portfolio
              return existing;
            },
          },
        });
      }
    },
  });

  // Enhanced symbol handling with sorting and icons
  type CurrencyMeta = { symbol: string; name?: string; iconUrl?: string; qtyDecimals?: number; priceDecimals?: number };
  
  // Fallback list of common cryptocurrencies
  const FALLBACK_CRYPTOS: CurrencyMeta[] = [
    { symbol: 'BTC', name: 'Bitcoin', qtyDecimals: 8, priceDecimals: 2 },
    { symbol: 'ETH', name: 'Ethereum', qtyDecimals: 8, priceDecimals: 2 },
    { symbol: 'SOL', name: 'Solana', qtyDecimals: 8, priceDecimals: 2 },
    { symbol: 'USDT', name: 'Tether', qtyDecimals: 2, priceDecimals: 2 },
    { symbol: 'USDC', name: 'USD Coin', qtyDecimals: 2, priceDecimals: 2 },
    { symbol: 'XRP', name: 'Ripple', qtyDecimals: 6, priceDecimals: 4 },
    { symbol: 'ADA', name: 'Cardano', qtyDecimals: 6, priceDecimals: 4 },
    { symbol: 'DOGE', name: 'Dogecoin', qtyDecimals: 8, priceDecimals: 4 },
    { symbol: 'AVAX', name: 'Avalanche', qtyDecimals: 8, priceDecimals: 2 },
    { symbol: 'BNB', name: 'Binance Coin', qtyDecimals: 8, priceDecimals: 2 },
    { symbol: 'MATIC', name: 'Polygon', qtyDecimals: 8, priceDecimals: 4 },
    { symbol: 'LTC', name: 'Litecoin', qtyDecimals: 8, priceDecimals: 2 },
    { symbol: 'DOT', name: 'Polkadot', qtyDecimals: 8, priceDecimals: 4 },
    { symbol: 'LINK', name: 'Chainlink', qtyDecimals: 8, priceDecimals: 4 },
    { symbol: 'UNI', name: 'Uniswap', qtyDecimals: 8, priceDecimals: 4 },
    { symbol: 'ATOM', name: 'Cosmos', qtyDecimals: 8, priceDecimals: 4 },
    { symbol: 'ALGO', name: 'Algorand', qtyDecimals: 8, priceDecimals: 4 },
    { symbol: 'FIL', name: 'Filecoin', qtyDecimals: 8, priceDecimals: 4 },
    { symbol: 'ETC', name: 'Ethereum Classic', qtyDecimals: 8, priceDecimals: 2 },
    { symbol: 'XLM', name: 'Stellar', qtyDecimals: 6, priceDecimals: 4 },
  ];
  
  const allSymbolsRaw: CurrencyMeta[] = useMemo(() => {
    const list: any[] = currenciesData?.supportedCurrencies ?? [];
    if (list.length === 0) {
      // Use fallback if query returns empty
      console.log('[Crypto Trading] No currencies from query, using fallback list');
      return FALLBACK_CRYPTOS;
    }
    return list.map(s => ({
      symbol: s.symbol,
      name: s.name,
      iconUrl: s.iconUrl,
      qtyDecimals: s.qtyDecimals,
      priceDecimals: s.priceDecimals,
    }));
  }, [currenciesData]);

  // Sort common majors first, then alphabetical
  const allSymbols = useMemo(() => {
    const majors = new Set(['BTC','ETH','SOL','USDT','USDC','XRP','ADA','DOGE','AVAX','BNB','MATIC','LTC']);
    const sorted = [...allSymbolsRaw].sort((a, b) => {
      const aMajor = majors.has(a.symbol) ? 0 : 1;
      const bMajor = majors.has(b.symbol) ? 0 : 1;
      if (aMajor !== bMajor) return aMajor - bMajor;
      return a.symbol.localeCompare(b.symbol);
    });
    console.log('[Crypto Trading] All symbols:', sorted.length, sorted.map(s => s.symbol).join(', '));
    return sorted;
  }, [allSymbolsRaw]);

  const symbolMeta = useMemo(() => {
    const found = allSymbols.find(s => s.symbol === selectedSymbol);
    return {
      qtyDecimals: found?.qtyDecimals ?? 8,
      priceDecimals: found?.priceDecimals ?? 2,
      name: found?.name ?? selectedSymbol,
      iconUrl: found?.iconUrl,
    };
  }, [allSymbols, selectedSymbol]);

  const currentPrice = parseFloat(priceData?.cryptoPrice?.priceUsd || '0');
  const change24h = parseFloat(priceData?.cryptoPrice?.priceChangePercentage24h || '0');

  // Keep limitPrice seeded to live when symbol/price changes (handy as a starting value)
  useEffect(() => {
    if (priceData?.cryptoPrice?.priceUsd) {
      setLimitPrice(String(priceData.cryptoPrice.priceUsd));
    }
  }, [priceData, selectedSymbol]);

  // Effective price for preview:
  // - MARKET / STOP_MARKET: use live
  // - LIMIT / STOP_LIMIT / TAKE_PROFIT_LIMIT: use limitPrice
  const effectivePrice =
    orderType === 'MARKET' || orderType === 'STOP_MARKET'
      ? currentPrice
      : parseFloat(limitPrice || '0');

  // Cross-calc qty <-> usd
  const qtyNum = parseFloat(qty || '0');
  const usdNum = parseFloat(usd || '0');
  useEffect(() => {
    setError('');
    const p = Number(effectivePrice);
    if (!p) return;

    if (mode === 'QTY') {
      const q = parseFloat(qty || '0');
      if (q > 0) setUsd((q * p).toFixed(2));
      else setUsd('');
    } else {
      const u = parseFloat(usd || '0');
      if (u > 0) setQty((u / p).toFixed(8));
      else setQty('');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, qty, usd, effectivePrice]);

  // Costs
  const fee = useMemo(() => (usdNum > 0 ? usdNum * FEE_RATE : 0), [usdNum]);
  const estSlippage = useMemo(
    () => (usdNum > 0 && (orderType === 'MARKET' || orderType === 'STOP_MARKET'))
      ? (usdNum * SLIPPAGE_BPS) / 10000
      : 0,
    [usdNum, orderType]
  );
  const totalCost = tradeType === 'BUY'
    ? usdNum + fee + estSlippage
    : Math.max(usdNum - fee - estSlippage, 0);

  /* ---------- Validations (dynamic) ---------- */
  useEffect(() => {
    const err = validate();
    setError(err || '');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tradeType, orderType, qty, usd, limitPrice, triggerPrice, effectivePrice, currentPrice, timeInForce]);

  const validate = (): string | null => {
    // Basic inputs
    if (!qty && !usd) return null;
    if (qtyNum <= 0) return 'Enter a valid quantity.';
    if (effectivePrice <= 0) return 'Enter a valid price.';

    // Wallet / cash checks
    if (tradeType === 'SELL') {
      const bal = balances?.[selectedSymbol];
      if (typeof bal === 'number' && qtyNum > bal + 1e-10) {
        return `You only have ${bal.toFixed(8)} ${selectedSymbol} available.`;
      }
    } else if (tradeType === 'BUY' && typeof usdAvailable === 'number') {
      if (totalCost > usdAvailable + 1e-6) {
        return `Insufficient USD: need ${fmtUSD(totalCost)}, available ${fmtUSD(usdAvailable)}.`;
      }
    }

    // Order-type specific
    const trig = parseFloat(triggerPrice || '0');
    const lim = parseFloat(limitPrice || '0');

    if (orderType === 'LIMIT' || orderType === 'STOP_LIMIT' || orderType === 'TAKE_PROFIT_LIMIT') {
      if (!lim || lim <= 0) return 'Limit price is required.';
    }
    if (orderType === 'STOP_MARKET' || orderType === 'STOP_LIMIT') {
      if (!trig || trig <= 0) return 'Trigger price is required for stop orders.';
      if (tradeType === 'BUY' && trig < currentPrice) {
        return 'For BUY stop orders, trigger must be ≥ current price.';
      }
      if (tradeType === 'SELL' && trig > currentPrice) {
        return 'For SELL stop orders, trigger must be ≤ current price.';
      }
    }
    if (orderType === 'STOP_LIMIT') {
      if (tradeType === 'BUY' && lim < trig) {
        return 'For BUY stop-limit, limit price should be ≥ trigger.';
      }
      if (tradeType === 'SELL' && lim > trig) {
        return 'For SELL stop-limit, limit price should be ≤ trigger.';
      }
    }
    if (orderType === 'TAKE_PROFIT_LIMIT') {
      // Convention used here:
      //  - BUY TP-LIMIT (enter on dip): limit ≤ current
      //  - SELL TP-LIMIT (exit into strength): limit ≥ current
      if (tradeType === 'BUY' && lim > currentPrice) {
        return 'For BUY take-profit limit, price should be ≤ current price (buy the dip).';
      }
      if (tradeType === 'SELL' && lim < currentPrice) {
        return 'For SELL take-profit limit, price should be ≥ current price.';
      }
    }

    // IOC/FOK sanity: avoid MARKET+GTC (not valid on many venues)
    if ((timeInForce === 'IOC' || timeInForce === 'FOK') && orderType === 'LIMIT') {
      // ok, many exchanges support limit-IOC/FOK
    }
    if ((timeInForce === 'IOC' || timeInForce === 'FOK') && orderType === 'MARKET') {
      // Many venues treat MARKET as Immediate-or-Cancel implicitly; allow.
    }

    return null;
  };

  /* ---------- UI helpers ---------- */
  const setPreset = (pct: number) => {
    const p = Number(effectivePrice);
    if (!p) return;
    if (tradeType === 'SELL') {
      const bal = balances?.[selectedSymbol] ?? 0;
      const q = bal * pct;
      setMode('QTY');
      setQty(q > 0 ? q.toFixed(8) : '');
    } else {
      const avail = typeof usdAvailable === 'number' ? usdAvailable : 0;
      const u = avail * pct;
      setMode('USD');
      setUsd(u > 0 ? u.toFixed(2) : '');
    }
  };
  const setMax = () => {
    if (tradeType === 'SELL') {
      const bal = balances?.[selectedSymbol] ?? 0;
      setMode('QTY'); setQty(bal > 0 ? bal.toFixed(8) : '');
    } else if (typeof usdAvailable === 'number') {
      setMode('USD'); setUsd(usdAvailable > 0 ? usdAvailable.toFixed(2) : '');
    }
  };

  const canSubmit = !isSubmitting && !error && parseFloat(qty || '0') > 0 &&
    (orderType === 'MARKET' || orderType === 'STOP_MARKET' || !!limitPrice) &&
    (orderType !== 'STOP_MARKET' && orderType !== 'STOP_LIMIT' ? true : !!triggerPrice);

  const openConfirm = () => {
    if (!canSubmit) return;
    
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
    
    setConfirmOpen(true);
  };

  const submitTrade = async () => {
    // Double-check trading is enabled before executing
    if (!FEATURES.CRYPTO_TRADING_ENABLED) {
      Alert.alert('Trading Not Available', FEATURES.CRYPTO_TRADING_MESSAGE);
      return;
    }

    setConfirmOpen(false);
    setIsSubmitting(true);
    try {
      // Server-authoritative pricing: don't send price for MARKET orders
      // Server will fetch fresh quote and use that for execution
      const variables: any = {
        symbol: `${selectedSymbol}/USD`, // Convert BTC to BTC/USD format
        tradeType,
        quantity: parseFloat(qty),
        orderType,
        // Only send pricePerUnit for LIMIT orders
        pricePerUnit: orderType === 'LIMIT' ? Number(limitPrice) : undefined,
        // Optional slippage protection for MARKET orders (1% = 100 bps)
        maxSlippageBps: orderType === 'MARKET' ? 100 : undefined,
      };

      console.log('Submitting trade with variables:', variables);

      const { data } = await executeTrade({ variables });
      
      if (data?.executeCryptoTrade?.ok) {
        const trade = data.executeCryptoTrade.trade;
        Alert.alert(
          'Trade Executed!', 
          `Order ID: ${trade.orderId}\n` +
          `Type: ${trade.tradeType} ${trade.quantity} ${selectedSymbol}\n` +
          `Price: $${trade.pricePerUnit}\n` +
          `Total: $${trade.totalAmount}\n` +
          `Status: ${trade.status}`,
          [
            { text: 'OK', onPress: () => onTradeSuccess() },
          ]
        );
        
        // Clear form
        setQty(''); 
        setUsd(''); 
        if (orderType !== 'LIMIT') setLimitPrice('');
        setTriggerPrice('');
      } else {
        const error = data?.executeCryptoTrade?.error;
        Alert.alert('Trade Failed', error?.message || 'Unknown error occurred');
      }
    } catch (e) {
      console.error('Trade error:', e);
      Alert.alert('Error', 'Failed to execute trade. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Icon helper
  const renderIcon = (sym: string, size: number, iconUrl?: string) => {
    return (
      <CryptoIcon 
        symbol={sym} 
        size={size}
        style={{ borderRadius: size/2 }}
      />
    );
  };

  /* ---------- Render ---------- */
  return (
    <>
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Side */}
      <View style={styles.segment}>
        <SegBtn active={tradeType === 'BUY'} color="#0EA5E9" icon="trending-up" onPress={() => setTradeType('BUY')} label="Buy" />
        <SegBtn active={tradeType === 'SELL'} color="#7C3AED" icon="trending-down" onPress={() => setTradeType('SELL')} label="Sell" />
      </View>

      {/* Symbol Picker */}
      <View style={styles.section}>
        <Text style={styles.label}>Cryptocurrency</Text>
        <View style={{ position: 'relative', zIndex: 1000 }}>
          <TouchableOpacity
            style={styles.symbolBtn}
            onPress={() => setPickerOpen(!pickerOpen)}
            disabled={currenciesLoading}
            activeOpacity={0.9}
          >
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
              {renderIcon(selectedSymbol, 28, symbolMeta.iconUrl)}
              <View>
                <Text style={styles.symbolCode}>{selectedSymbol}</Text>
                <Text style={styles.symbolName} numberOfLines={1}>{symbolMeta.name}</Text>
              </View>
            </View>
            <Icon name={pickerOpen ? "chevron-up" : "chevron-down"} size={18} color="#111827" />
          </TouchableOpacity>
          
          {/* Dropdown List */}
          {pickerOpen && (
            <View style={styles.dropdownContainer}>
              {currenciesLoading ? (
                <View style={{ padding: 20, alignItems: 'center' }}>
                  <ActivityIndicator size="small" color="#3b82f6" />
                  <Text style={{ marginTop: 8, color: '#6B7280', fontSize: 12 }}>Loading cryptocurrencies...</Text>
                </View>
              ) : allSymbols.length === 0 ? (
                <View style={{ padding: 20, alignItems: 'center' }}>
                  <Text style={{ color: '#6B7280', fontSize: 14 }}>No cryptocurrencies available</Text>
                </View>
              ) : (
                <FlatList
                  data={allSymbols}
                  keyExtractor={(item) => item.symbol}
                  showsVerticalScrollIndicator={true}
                  style={styles.dropdownList}
                  nestedScrollEnabled={true}
                  renderItem={({ item }) => {
                    const isSelected = item.symbol === selectedSymbol;
                    return (
                      <TouchableOpacity
                        style={[styles.dropdownItem, isSelected && styles.dropdownItemSelected]}
                        onPress={() => {
                          setSelectedSymbol(item.symbol);
                          setPickerOpen(false);
                        }}
                      >
                        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, flex: 1 }}>
                          {renderIcon(item.symbol, 20, item.iconUrl)}
                          <View style={{ flex: 1 }}>
                            <Text style={[styles.dropdownSymbol, isSelected && styles.dropdownSymbolSelected]}>
                              {item.symbol}
                            </Text>
                            {item.name && (
                              <Text style={styles.dropdownName} numberOfLines={1}>
                                {item.name}
                              </Text>
                            )}
                          </View>
                        </View>
                        {isSelected && <Icon name="check" size={16} color="#3b82f6" />}
                      </TouchableOpacity>
                    );
                  }}
                />
              )}
            </View>
          )}
        </View>
      </View>

      {/* Order type + TIF */}
      <View style={styles.rowSplit}>
        <View style={{ flex: 1, marginRight: 8 }}>
          <View style={styles.labelRow}>
            <Text style={styles.label}>Order Type</Text>
            <TouchableOpacity onPress={() => setShowOrderTypeHelp(!showOrderTypeHelp)}>
              <Icon name="help-circle" size={16} color="#6B7280" />
            </TouchableOpacity>
          </View>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ paddingVertical: 4, paddingRight: 20 }}>
            {(['MARKET','LIMIT','STOP_MARKET','STOP_LIMIT','TAKE_PROFIT_LIMIT'] as OrderType[]).map(t => (
              <TouchableOpacity
                key={t}
                style={[styles.pill, orderType === t && styles.pillActive]}
                onPress={() => setOrderType(t)}
              >
                <Text style={[styles.pillText, orderType === t && styles.pillTextActive]}>{t.replace(/_/g,' ')}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
          {showOrderTypeHelp && (
            <View style={styles.helpBox}>
              <Text style={styles.helpText}>
                <Text style={styles.helpBold}>MARKET:</Text> Execute immediately at current price{'\n'}
                <Text style={styles.helpBold}>LIMIT:</Text> Execute only at your specified price{'\n'}
                <Text style={styles.helpBold}>STOP_MARKET:</Text> Trigger market order when price hits trigger{'\n'}
                <Text style={styles.helpBold}>STOP_LIMIT:</Text> Trigger limit order when price hits trigger{'\n'}
                <Text style={styles.helpBold}>TAKE_PROFIT_LIMIT:</Text> Lock in profits at target price
              </Text>
            </View>
          )}
        </View>
        <View style={{ flex: 1, marginLeft: 8 }}>
          <View style={styles.labelRow}>
            <Text style={styles.label}>Time in Force</Text>
            <TouchableOpacity onPress={() => setShowTifHelp(!showTifHelp)}>
              <Icon name="help-circle" size={16} color="#6B7280" />
            </TouchableOpacity>
          </View>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ paddingVertical: 4, paddingRight: 20 }}>
            {(['GTC','DAY','IOC','FOK'] as TimeInForce[]).map(t => (
              <TouchableOpacity
                key={t}
                style={[styles.pillSm, timeInForce === t && styles.pillActiveSm]}
                onPress={() => setTimeInForce(t)}
              >
                <Text style={[styles.pillSmText, timeInForce === t && styles.pillSmTextActive]}>{t}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
          {showTifHelp && (
            <View style={styles.helpBox}>
              <Text style={styles.helpText}>
                <Text style={styles.helpBold}>GTC:</Text> Good Till Cancelled (stays active){'\n'}
                <Text style={styles.helpBold}>DAY:</Text> Valid only for today{'\n'}
                <Text style={styles.helpBold}>IOC:</Text> Immediate or Cancel{'\n'}
                <Text style={styles.helpBold}>FOK:</Text> Fill or Kill (all or nothing)
              </Text>
            </View>
          )}
        </View>
      </View>

      {/* Live price block */}
      <View style={styles.priceCard}>
        <View style={styles.priceRow}>
          <Text style={styles.priceLabel}>Current Price</Text>
          <TouchableOpacity onPress={() => refetchPrice()}><Icon name="refresh-cw" size={16} color="#007AFF" /></TouchableOpacity>
        </View>
        <View style={styles.priceRow}>
          <Text style={styles.priceValue}>{fmtUSD(currentPrice)}</Text>
          {change24h !== 0 && (
            <View style={[
              styles.changePill,
              { backgroundColor: change24h >= 0 ? '#ECFDF5' : '#FEF2F2',
                borderColor:   change24h >= 0 ? '#A7F3D0' : '#FECACA' }
            ]}>
              <Icon name={change24h >= 0 ? 'trending-up' : 'trending-down'}
                    size={12} color={change24h >= 0 ? '#10B981' : '#EF4444'} />
              <Text style={[
                styles.changeText,
                { color: change24h >= 0 ? '#10B981' : '#EF4444' }
              ]}>
                {change24h >= 0 ? '+' : ''}{change24h.toFixed(2)}%
              </Text>
            </View>
          )}
        </View>
        <Text style={styles.priceSubtext}>24h change • Prices update in real-time</Text>
      </View>

      {/* Price inputs (conditionally enabled) */}
      {(orderType === 'LIMIT' || orderType === 'STOP_LIMIT' || orderType === 'TAKE_PROFIT_LIMIT') && (
        <View style={styles.section}>
          <Text style={styles.label}>Limit Price</Text>
          <View style={styles.inputRow}>
            <TextInput
              style={styles.input}
              value={limitPrice}
              onChangeText={setLimitPrice}
              placeholder="0.00"
              keyboardType="decimal-pad"
              autoCapitalize="none"
            />
            <Text style={styles.suffix}>USD</Text>
          </View>
        </View>
      )}

      {(orderType === 'STOP_MARKET' || orderType === 'STOP_LIMIT') && (
        <View style={styles.section}>
          <Text style={styles.label}>Trigger Price (Stop)</Text>
          <View style={styles.inputRow}>
            <TextInput
              style={styles.input}
              value={triggerPrice}
              onChangeText={setTriggerPrice}
              placeholder="0.00"
              keyboardType="decimal-pad"
              autoCapitalize="none"
            />
            <Text style={styles.suffix}>USD</Text>
          </View>
          <Text style={styles.hintSmall}>
            {tradeType === 'BUY'
              ? 'BUY stop triggers at or above current price.'
              : 'SELL stop triggers at or below current price.'}
          </Text>
        </View>
      )}

      {/* Mode toggle + qty/usd */}
      <View style={styles.modeRow}>
        <View>
          <ToggleTwo
            left={{ label: 'Quantity', active: mode === 'QTY', onPress: () => setMode('QTY') }}
            right={{ label: 'USD', active: mode === 'USD', onPress: () => setMode('USD') }}
          />
          <Text style={styles.inputHint}>
            {mode === 'QTY' ? 'Enter amount in crypto units' : 'Enter dollar amount to spend'}
          </Text>
        </View>
        <View style={{ flex: 1 }} />
        <TouchableOpacity onPress={setMax}><Text style={styles.maxLink}>{tradeType === 'SELL' ? 'Max' : 'Use All $'}</Text></TouchableOpacity>
      </View>

      {mode === 'QTY' ? (
        <View style={styles.inputRow}>
          <TextInput
            style={styles.input}
            value={qty}
            onChangeText={setQty}
            placeholder="0.00000000"
            keyboardType="decimal-pad"
            autoCapitalize="none"
          />
          <Text style={styles.suffix}>{selectedSymbol}</Text>
        </View>
      ) : (
        <View style={styles.inputRow}>
          <TextInput
            style={styles.input}
            value={usd}
            onChangeText={setUsd}
            placeholder="0.00"
            keyboardType="decimal-pad"
            autoCapitalize="none"
          />
          <Text style={styles.suffix}>USD</Text>
        </View>
      )}

      {/* Presets */}
      <View style={styles.presetRow}>
        {[0.25, 0.5, 0.75, 1].map(p => (
          <TouchableOpacity key={p} style={styles.presetBtn} onPress={() => setPreset(p)}>
            <Text style={styles.presetText}>{Math.round(p * 100)}%</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Summary */}
      {(qtyNum > 0 || usdNum > 0) && (
        <View style={styles.summaryCard}>
          <Row label="Notional" value={fmtUSD(usdNum)} />
          <Row label="Est. Fee (0.10%)" value={fmtUSD(fee)} />
          {(orderType === 'MARKET' || orderType === 'STOP_MARKET') && (
            <Row label="Est. Slippage (0.50%)" value={fmtUSD(estSlippage)} />
          )}
          <View style={styles.divider} />
          <Row label={tradeType === 'BUY' ? 'Total Cost' : 'Est. Proceeds'} value={fmtUSD(totalCost)} bold />
        </View>
      )}

      {/* Error */}
      {!!error && (
        <View style={styles.errorBox}>
          <Icon name="alert-triangle" size={16} color="#B45309" />
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      {/* Risk Warning */}
      {showRiskWarning && (
        <View style={styles.riskWarning}>
          <View style={styles.riskHeader}>
            <Icon name="alert-triangle" size={16} color="#DC2626" />
            <Text style={styles.riskTitle}>Trading Risk Warning</Text>
            <TouchableOpacity onPress={() => setShowRiskWarning(false)}>
              <Icon name="x" size={16} color="#6B7280" />
            </TouchableOpacity>
          </View>
          <Text style={styles.riskText}>
            • Cryptocurrency trading involves significant risk{'\n'}
            • You may lose all invested capital{'\n'}
            • Prices can be extremely volatile{'\n'}
            • Only trade with money you can afford to lose{'\n'}
            • Past performance doesn't guarantee future results
          </Text>
        </View>
      )}

      {/* Educational Tips */}
      <View style={styles.tipsCard}>
        <View style={styles.tipsHeader}>
          <Icon name="lightbulb" size={16} color="#F59E0B" />
          <Text style={styles.tipsTitle}>Trading Tips</Text>
        </View>
        <Text style={styles.tipsText}>
          • Start with small amounts to learn{'\n'}
          • Use limit orders for better price control{'\n'}
          • Set stop-losses to manage risk{'\n'}
          • Never invest more than you can afford to lose
        </Text>
      </View>

      {/* Submit */}
      <TouchableOpacity
        style={[
          styles.submitBtn,
          (!canSubmit || !!error) && styles.submitDisabled,
          tradeType === 'BUY' ? styles.buyBtn : styles.sellBtn,
        ]}
        disabled={!canSubmit || !!error}
        onPress={openConfirm}
      >
        {isSubmitting ? <ActivityIndicator color="#fff" /> : (
          <>
            <Icon name={tradeType === 'BUY' ? 'trending-up' : 'trending-down'} size={18} color="#fff" />
            <Text style={styles.submitText}>{tradeType} {selectedSymbol}</Text>
          </>
        )}
      </TouchableOpacity>

      {/* Risk */}
      <View style={styles.notice}>
        <Icon name="alert-triangle" size={16} color="#92400E" />
        <Text style={styles.noticeText}>Crypto orders may execute partially or not at all depending on liquidity and your time-in-force.</Text>
      </View>


    </ScrollView>

    {/* Modals moved outside ScrollView to avoid nested scrollable components */}
    {/* Trade Confirmation Modal */}
    <Modal transparent animationType="slide" visible={confirmOpen} onRequestClose={() => setConfirmOpen(false)}>
      <View style={styles.sheetOverlay}>
        <View style={styles.confirmSheet}>
          <View style={styles.sheetHeader}>
            <Text style={styles.sheetTitle}>Confirm Trade</Text>
            <TouchableOpacity onPress={() => setConfirmOpen(false)}>
              <Icon name="x" size={20} color="#111827" />
            </TouchableOpacity>
          </View>
          <View style={styles.confirmContent}>
            <Row label="Action" value={`${tradeType} ${selectedSymbol}`} />
            <Row label="Order Type" value={orderType.replace(/_/g, ' ')} />
            {orderType !== 'MARKET' && <Row label="Limit Price" value={fmtUSD(parseFloat(limitPrice))} />}
            {['STOP_MARKET', 'STOP_LIMIT'].includes(orderType) && <Row label="Trigger Price" value={fmtUSD(parseFloat(triggerPrice))} />}
            <Row label="Quantity" value={qty} />
            <Row label="Time in Force" value={timeInForce} />
            {orderType !== 'MARKET' && (
              <>
                <Row label="Est. Fill Price" value={fmtUSD(effectivePrice)} />
                <Row label="Est. Slippage" value={`${(SLIPPAGE_BPS / 100).toFixed(2)}%`} />
              </>
            )}
            <Row label="Commission" value={fmtUSD(fee)} />
            {orderType === 'MARKET' && (
              <>
                <Row label="Est. Fill Price" value={fmtUSD(effectivePrice)} />
                <Row label="Est. Slippage" value={`${(SLIPPAGE_BPS / 100).toFixed(2)}%`} />
              </>
            )}
            <View style={styles.divider} />
            <Row label={tradeType === 'BUY' ? 'Total Cost' : 'Est. Proceeds'} value={fmtUSD(totalCost)} bold />
            <View style={{ height: 16 }} />
            <View style={styles.sheetBtns}>
              <TouchableOpacity style={[styles.sheetBtn, styles.sheetCancel]} onPress={() => setConfirmOpen(false)}>
                <Text style={styles.sheetCancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.sheetBtn, styles.sheetConfirm]} onPress={submitTrade}>
                <Text style={styles.sheetConfirmText}>Confirm</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </View>
    </Modal>

    </>
  );
};

/* ---------- tiny comps & helpers ---------- */
const SegBtn = ({ active, color, icon, label, onPress }: any) => (
  <TouchableOpacity style={[styles.segBtn, active && { backgroundColor: color }]} onPress={onPress} activeOpacity={0.85}>
    <Icon name={icon} size={18} color={active ? '#fff' : color} />
    <Text style={[styles.segText, active && styles.segTextActive]}>{label}</Text>
  </TouchableOpacity>
);

const ToggleTwo = ({ left, right }: any) => (
  <View style={styles.toggleTwo}>
    <TouchableOpacity style={[styles.toggleItem, left.active && styles.toggleActive]} onPress={left.onPress}>
      <Text style={[styles.toggleText, left.active && styles.toggleTextActive]}>{left.label}</Text>
    </TouchableOpacity>
    <TouchableOpacity style={[styles.toggleItem, right.active && styles.toggleActive]} onPress={right.onPress}>
      <Text style={[styles.toggleText, right.active && styles.toggleTextActive]}>{right.label}</Text>
    </TouchableOpacity>
  </View>
);

const Row = ({ label, value, bold }: { label: string; value: string; bold?: boolean }) => (
  <View style={styles.row}>
    <Text style={[styles.rowLabel, bold && { fontWeight: '700', color: '#111827' }]}>{label}</Text>
    <Text style={[styles.rowValue, bold && { fontWeight: '700', color: '#111827' }]}>{value}</Text>
  </View>
);

const fmtUSD = (v: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(v);

/* ---------- styles ---------- */
const styles = StyleSheet.create({
  container: { flex: 1, paddingTop: 20 },

  segment: { flexDirection: 'row', backgroundColor: '#FFFFFF', borderRadius: 12, padding: 4, marginBottom: 16,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.08, shadowRadius: 6, elevation: 2 },
  segBtn: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 12, borderRadius: 8, gap: 8 },
  segText: { fontSize: 16, fontWeight: '600', color: '#111827' },
  segTextActive: { color: '#fff' },

  section: { marginBottom: 16 },
  label: { fontSize: 14, fontWeight: '600', color: '#111827', marginBottom: 8 },

  chip: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 18, backgroundColor: '#F3F4F6', marginRight: 8 },
  chipActive: { backgroundColor: '#111827' },
  chipText: { fontSize: 14, fontWeight: '600', color: '#6B7280' },
  chipTextActive: { color: '#fff' },

  rowSplit: { flexDirection: 'row', marginBottom: 8 },
  pill: { paddingHorizontal: 10, paddingVertical: 6, borderRadius: 8, backgroundColor: '#F3F4F6', marginRight: 6 },
  pillActive: { backgroundColor: '#111827' },
  pillText: { color: '#6B7280', fontWeight: '700', fontSize: 12 },
  pillTextActive: { color: '#fff' },
  pillSm: { paddingHorizontal: 8, paddingVertical: 6, borderRadius: 999, backgroundColor: '#F3F4F6', marginRight: 6 },
  pillActiveSm: { backgroundColor: '#111827' },
  pillSmText: { color: '#6B7280', fontWeight: '700', fontSize: 11 },
  pillSmTextActive: { color: '#fff' },

  priceCard: { backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 16,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.08, shadowRadius: 6, elevation: 2 },
  priceRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  priceLabel: { fontSize: 12, color: '#6B7280' },
  priceValue: { fontSize: 24, fontWeight: '700', color: '#111827', marginVertical: 4 },
  changePill: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 10, paddingVertical: 4, borderRadius: 999, borderWidth: 1 },
  changeText: { fontSize: 12, fontWeight: '700' },

  inputRow: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFFFFF', borderRadius: 12, paddingHorizontal: 16, paddingVertical: 12,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.08, shadowRadius: 6, elevation: 2 },
  input: { flex: 1, fontSize: 16, color: '#111827' },
  suffix: { fontSize: 16, fontWeight: '700', color: '#6B7280', marginLeft: 8 },
  hintSmall: { marginTop: 6, fontSize: 12, color: '#6B7280' },

  modeRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 8, gap: 8 },
  toggleTwo: { flexDirection: 'row', backgroundColor: '#F3F4F6', borderRadius: 10, padding: 2 },
  toggleItem: { paddingVertical: 8, paddingHorizontal: 12, borderRadius: 8 },
  toggleActive: { backgroundColor: '#111827' },
  toggleText: { color: '#6B7280', fontWeight: '700' },
  toggleTextActive: { color: '#fff' },
  maxLink: { color: '#007AFF', fontWeight: '700' },

  presetRow: { flexDirection: 'row', gap: 8, marginTop: 10, marginBottom: 6 },
  presetBtn: { flex: 1, alignItems: 'center', paddingVertical: 10, borderRadius: 10, backgroundColor: '#EFF6FF' },
  presetText: { color: '#1D4ED8', fontWeight: '700' },

  summaryCard: { backgroundColor: '#FFFFFF', borderRadius: 12, padding: 16, marginTop: 10, marginBottom: 16,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.08, shadowRadius: 6, elevation: 2 },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginVertical: 4 },
  rowLabel: { fontSize: 14, color: '#6B7280' },
  rowValue: { fontSize: 14, color: '#111827', fontWeight: '600' },
  divider: { height: 1, backgroundColor: '#F3F4F6', marginVertical: 6 },

  errorBox: { flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: '#FFFBEB', borderColor: '#FCD34D', borderWidth: 1, padding: 12, borderRadius: 10, marginBottom: 14 },
  errorText: { color: '#92400E', fontSize: 14, flex: 1 },

  submitBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 16, borderRadius: 12, gap: 8, marginBottom: 16 },
  submitDisabled: { opacity: 0.6 },
  buyBtn: { backgroundColor: '#0EA5E9' },
  sellBtn: { backgroundColor: '#7C3AED' },
  submitText: { color: '#fff', fontWeight: '700', fontSize: 16 },

  notice: { flexDirection: 'row', gap: 8, backgroundColor: '#FFFBEB', borderColor: '#FCD34D', borderWidth: 1, padding: 12, borderRadius: 10, marginBottom: 20 },
  noticeText: { color: '#92400E', fontSize: 14, flex: 1 },

  sheetOverlay: { flex: 1, backgroundColor: '#000000', justifyContent: 'flex-end', paddingBottom: 100 },
  sheet: { backgroundColor: '#fff', padding: 16, borderTopLeftRadius: 16, borderTopRightRadius: 16, maxHeight: '80%' },
  confirmSheet: { backgroundColor: '#fff', padding: 16, borderTopLeftRadius: 16, borderTopRightRadius: 16, maxHeight: '50%', marginBottom: 50 },
  sheetHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  confirmContent: { paddingBottom: 20 },
  sheetTitle: { fontSize: 18, fontWeight: '700', color: '#111827' },
  sheetBtns: { flexDirection: 'row', gap: 10 },
  sheetBtn: { flex: 1, paddingVertical: 12, borderRadius: 10, alignItems: 'center' },
  sheetCancel: { backgroundColor: '#F3F4F6' },
  sheetConfirm: { backgroundColor: '#111827' },
  sheetCancelText: { color: '#111827', fontWeight: '700' },
  sheetConfirmText: { color: '#fff', fontWeight: '700' },

  // Symbol picker styles
  symbolBtn: { paddingVertical: 10, paddingHorizontal: 12, backgroundColor: '#fff', borderRadius: 12,
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.08, shadowRadius: 6, elevation: 2 },
  fallbackCircle: { alignItems: 'center', justifyContent: 'center', backgroundColor: '#EEF2FF' },
  fallbackText: { fontWeight: '700', color: '#3730A3' },
  symbolCode: { fontWeight: '700', color: '#111827' },
  symbolName: { fontSize: 12, color: '#6B7280', maxWidth: 120 },

  // Dropdown styles
  dropdownContainer: {
    marginTop: 4,
    backgroundColor: '#fff',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
    maxHeight: 300,
  },
  dropdownList: {
    maxHeight: 300,
  },
  dropdownItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  dropdownItemSelected: {
    backgroundColor: '#EFF6FF',
  },
  dropdownSymbol: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  dropdownSymbolSelected: {
    color: '#3b82f6',
  },
  dropdownName: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },

  pickerSheet: { backgroundColor: '#fff', paddingHorizontal: 16, paddingTop: 12, paddingBottom: 16, borderTopLeftRadius: 16, borderTopRightRadius: 16, maxHeight: '85%' },
  pickerHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 },
  searchRow: { flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: '#F3F4F6', paddingHorizontal: 12, paddingVertical: 8, borderRadius: 10, marginTop: 8, marginBottom: 10 },
  searchInput: { flex: 1, fontSize: 14, color: '#111827' },
  favToggleRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 },
  groupLabel: { fontSize: 12, color: '#6B7280', marginTop: 4, marginBottom: 6 },
  assetRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 10 },
  sep: { height: 1, backgroundColor: '#F3F4F6' },
  assetLeft: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  assetRight: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  assetSymbol: { fontWeight: '700', color: '#111827' },
  assetName: { fontSize: 12, color: '#6B7280', maxWidth: 200 },
  assetBal: { fontSize: 12, color: '#6B7280' },

  // Educational components
  labelRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 },
  helpBox: { backgroundColor: '#F8FAFC', borderColor: '#E2E8F0', borderWidth: 1, borderRadius: 8, padding: 12, marginTop: 8 },
  helpText: { fontSize: 12, color: '#475569', lineHeight: 18 },
  helpBold: { fontWeight: '700', color: '#1E293B' },
  priceSubtext: { fontSize: 11, color: '#6B7280', marginTop: 4, textAlign: 'center' },
  
  riskWarning: { backgroundColor: '#FEF2F2', borderColor: '#FECACA', borderWidth: 1, borderRadius: 8, padding: 12, marginBottom: 12 },
  riskHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 },
  riskTitle: { fontSize: 14, fontWeight: '700', color: '#DC2626', marginLeft: 6 },
  riskText: { fontSize: 12, color: '#991B1B', lineHeight: 18 },
  
  tipsCard: { backgroundColor: '#FFFBEB', borderColor: '#FCD34D', borderWidth: 1, borderRadius: 8, padding: 12, marginBottom: 12 },
  tipsHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
  tipsTitle: { fontSize: 14, fontWeight: '700', color: '#92400E', marginLeft: 6 },
  tipsText: { fontSize: 12, color: '#92400E', lineHeight: 18 },
  inputHint: { fontSize: 11, color: '#6B7280', marginTop: 4 },
});

export default CryptoTradingCardPro;