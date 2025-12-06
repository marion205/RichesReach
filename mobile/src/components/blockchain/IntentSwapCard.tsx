/**
 * Intent Swap Card Component
 * MEV-protected swaps via CoW Swap, 1inch Fusion, UniswapX
 */

import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, TextInput, Alert, ActivityIndicator } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import IntentService, { SwapIntent } from '../../services/IntentService';
import * as Haptics from 'expo-haptics';

export default function IntentSwapCard() {
  const [sellToken, setSellToken] = useState('USDC');
  const [buyToken, setBuyToken] = useState('ETH');
  const [sellAmount, setSellAmount] = useState('');
  const [loading, setLoading] = useState(false);
  const [quotes, setQuotes] = useState<any[]>([]);
  const [selectedSource, setSelectedSource] = useState<'auto' | 'cowswap' | '1inch' | 'uniswapx'>('auto');

  const handleGetQuotes = async () => {
    if (!sellAmount || parseFloat(sellAmount) <= 0) {
      Alert.alert('Error', 'Please enter a valid amount');
      return;
    }

    try {
      setLoading(true);
      const intent: SwapIntent = {
        sellToken,
        buyToken,
        sellAmount,
        receiver: '0x...', // Would get from wallet
        validFor: 300, // 5 minutes
        source: selectedSource,
      };

      const quoteResults = await IntentService.getQuotes(intent);
      setQuotes(quoteResults);
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to get quotes');
    } finally {
      setLoading(false);
    }
  };

  const handleSwap = async () => {
    if (!sellAmount || parseFloat(sellAmount) <= 0) {
      Alert.alert('Error', 'Please enter a valid amount');
      return;
    }

    if (quotes.length === 0) {
      Alert.alert('Error', 'Please get quotes first');
      return;
    }

    try {
      setLoading(true);
      const intent: SwapIntent = {
        sellToken,
        buyToken,
        sellAmount,
        receiver: '0x...', // Would get from wallet
        validFor: 300,
        source: selectedSource,
      };

      const order = await IntentService.createSwapIntent(intent);
      
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      Alert.alert(
        'Intent Created',
        `Your swap intent has been submitted. Order ID: ${order.intentId}\n\nYou'll receive ${quotes[0].buyAmount} ${buyToken} when filled.`,
        [{ text: 'OK' }]
      );
    } catch (error: any) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      Alert.alert('Error', error.message || 'Failed to create swap intent');
    } finally {
      setLoading(false);
    }
  };

  const getSourceIcon = (source: string) => {
    switch (source) {
      case 'cowswap':
        return '🐮';
      case '1inch':
        return '1️⃣';
      case 'uniswapx':
        return '🦄';
      default:
        return '⚡';
    }
  };

  const getSourceName = (source: string) => {
    switch (source) {
      case 'cowswap':
        return 'CoW Swap';
      case '1inch':
        return '1inch Fusion';
      case 'uniswapx':
        return 'UniswapX';
      default:
        return 'Auto';
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Icon name="zap" size={20} color="#667eea" />
        <Text style={styles.title}>Intent Swap</Text>
        <View style={styles.badge}>
          <Text style={styles.badgeText}>MEV Protected</Text>
        </View>
      </View>

      <Text style={styles.description}>
        Get the best price with MEV protection. No gas fees, no front-running.
      </Text>

      {/* Token Selection */}
      <View style={styles.tokenRow}>
        <View style={styles.tokenInput}>
          <Text style={styles.label}>Sell</Text>
          <TextInput
            style={styles.amountInput}
            placeholder="0.00"
            value={sellAmount}
            onChangeText={setSellAmount}
            keyboardType="decimal-pad"
          />
          <Text style={styles.tokenSymbol}>{sellToken}</Text>
        </View>

        <TouchableOpacity
          style={styles.swapButton}
          onPress={() => {
            const temp = sellToken;
            setSellToken(buyToken);
            setBuyToken(temp);
          }}
        >
          <Icon name="arrow-down-up" size={20} color="#667eea" />
        </TouchableOpacity>

        <View style={styles.tokenInput}>
          <Text style={styles.label}>Buy</Text>
          <Text style={styles.amountDisplay}>
            {quotes.length > 0 ? parseFloat(quotes[0].buyAmount).toFixed(4) : '0.00'}
          </Text>
          <Text style={styles.tokenSymbol}>{buyToken}</Text>
        </View>
      </View>

      {/* Source Selection */}
      <View style={styles.sourceSelector}>
        <Text style={styles.sourceLabel}>Protocol:</Text>
        {['auto', 'cowswap', '1inch', 'uniswapx'].map((source) => (
          <TouchableOpacity
            key={source}
            style={[
              styles.sourceChip,
              selectedSource === source && styles.sourceChipActive,
            ]}
            onPress={() => setSelectedSource(source as any)}
          >
            <Text style={styles.sourceChipIcon}>{getSourceIcon(source)}</Text>
            <Text
              style={[
                styles.sourceChipText,
                selectedSource === source && styles.sourceChipTextActive,
              ]}
            >
              {getSourceName(source)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Quotes */}
      {quotes.length > 0 && (
        <View style={styles.quotesContainer}>
          <Text style={styles.quotesTitle}>Best Quotes:</Text>
          {quotes.map((quote, index) => (
            <View key={index} style={styles.quoteCard}>
              <View style={styles.quoteHeader}>
                <Text style={styles.quoteSource}>
                  {getSourceIcon(quote.source)} {getSourceName(quote.source)}
                </Text>
                {index === 0 && (
                  <View style={styles.bestBadge}>
                    <Text style={styles.bestBadgeText}>Best</Text>
                  </View>
                )}
              </View>
              <View style={styles.quoteDetails}>
                <View style={styles.quoteDetail}>
                  <Text style={styles.quoteLabel}>You Receive</Text>
                  <Text style={styles.quoteValue}>
                    {parseFloat(quote.buyAmount).toFixed(4)} {buyToken}
                  </Text>
                </View>
                <View style={styles.quoteDetail}>
                  <Text style={styles.quoteLabel}>Price Impact</Text>
                  <Text style={[styles.quoteValue, { color: quote.priceImpact > 1 ? '#FF3B30' : '#34C759' }]}>
                    {quote.priceImpact.toFixed(2)}%
                  </Text>
                </View>
                <View style={styles.quoteDetail}>
                  <Text style={styles.quoteLabel}>Fee</Text>
                  <Text style={styles.quoteValue}>{parseFloat(quote.fee).toFixed(4)}</Text>
                </View>
                <View style={styles.quoteDetail}>
                  <Text style={styles.quoteLabel}>Gas</Text>
                  <Text style={styles.quoteValue}>
                    {parseFloat(quote.estimatedGas) === 0 ? 'Free' : `${quote.estimatedGas} gwei`}
                  </Text>
                </View>
              </View>
            </View>
          ))}
        </View>
      )}

      {/* Actions */}
      <View style={styles.actions}>
        <TouchableOpacity
          style={[styles.button, styles.quoteButton]}
          onPress={handleGetQuotes}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator size="small" color="#FFFFFF" />
          ) : (
            <>
              <Icon name="search" size={16} color="#FFFFFF" />
              <Text style={styles.buttonText}>Get Quotes</Text>
            </>
          )}
        </TouchableOpacity>

        {quotes.length > 0 && (
          <TouchableOpacity
            style={[styles.button, styles.swapButtonPrimary]}
            onPress={handleSwap}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator size="small" color="#FFFFFF" />
            ) : (
              <>
                <Icon name="zap" size={16} color="#FFFFFF" />
                <Text style={styles.buttonText}>Create Intent</Text>
              </>
            )}
          </TouchableOpacity>
        )}
      </View>

      {/* Info */}
      <View style={styles.infoBox}>
        <Icon name="info" size={14} color="#666" />
        <Text style={styles.infoText}>
          Intent-based swaps are filled automatically when the best price is available. No gas fees, MEV-protected.
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1a1a1a',
    marginLeft: 8,
    flex: 1,
  },
  badge: {
    backgroundColor: '#34C75915',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  badgeText: {
    color: '#34C759',
    fontSize: 11,
    fontWeight: '600',
  },
  description: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    marginBottom: 16,
  },
  tokenRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 12,
  },
  tokenInput: {
    flex: 1,
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
    padding: 12,
  },
  label: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  amountInput: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  amountDisplay: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  tokenSymbol: {
    fontSize: 12,
    color: '#666',
  },
  swapButton: {
    padding: 8,
    backgroundColor: '#F2F2F7',
    borderRadius: 8,
  },
  sourceSelector: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    marginBottom: 16,
    gap: 8,
  },
  sourceLabel: {
    fontSize: 12,
    color: '#666',
    marginRight: 8,
  },
  sourceChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#F2F2F7',
    borderWidth: 1,
    borderColor: '#E5E5EA',
    gap: 4,
  },
  sourceChipActive: {
    backgroundColor: '#667eea',
    borderColor: '#667eea',
  },
  sourceChipIcon: {
    fontSize: 12,
  },
  sourceChipText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#666',
  },
  sourceChipTextActive: {
    color: '#FFFFFF',
  },
  quotesContainer: {
    marginBottom: 16,
  },
  quotesTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 8,
  },
  quoteCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
  },
  quoteHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  quoteSource: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  bestBadge: {
    backgroundColor: '#34C759',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  bestBadgeText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '600',
  },
  quoteDetails: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  quoteDetail: {
    flex: 1,
    minWidth: '45%',
  },
  quoteLabel: {
    fontSize: 11,
    color: '#666',
    marginBottom: 2,
  },
  quoteValue: {
    fontSize: 13,
    fontWeight: '700',
    color: '#1a1a1a',
  },
  actions: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 12,
  },
  button: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 14,
    borderRadius: 8,
    gap: 8,
  },
  quoteButton: {
    backgroundColor: '#F2F2F7',
  },
  swapButtonPrimary: {
    backgroundColor: '#667eea',
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  infoBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#F9FAFB',
    padding: 12,
    borderRadius: 8,
    gap: 8,
  },
  infoText: {
    fontSize: 12,
    color: '#666',
    lineHeight: 18,
    flex: 1,
  },
});

