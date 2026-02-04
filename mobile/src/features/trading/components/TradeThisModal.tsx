/**
 * One-tap "Trade this" modal: shows Kelly-based position size and confirm for paper trading.
 * Shortens alert → decision → execution workflow.
 */
import React, { useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useQuery, useLazyQuery, useMutation } from '@apollo/client';
import { gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';

const GET_PAPER_ACCOUNT_SUMMARY = gql`
  query GetPaperAccountSummaryForTrade {
    paperAccountSummary {
      account {
        id
        currentBalance
        totalValue
      }
    }
  }
`;

const CALCULATE_POSITION_SIZE = gql`
  query CalculatePositionSizeForTrade(
    $accountEquity: Float!
    $entryPrice: Float!
    $stopPrice: Float!
    $confidence: Float
    $method: String
    $symbol: String
  ) {
    calculatePositionSize(
      accountEquity: $accountEquity
      entryPrice: $entryPrice
      stopPrice: $stopPrice
      confidence: $confidence
      method: $method
      symbol: $symbol
    ) {
      positionSize
      positionValue
      positionPct
      method
      kellyFraction
      recommendedFraction
    }
  }
`;

const PLACE_PAPER_ORDER = gql`
  mutation PlacePaperOrderFromSignal(
    $symbol: String!
    $side: String!
    $quantity: Int!
    $orderType: String
  ) {
    placePaperOrder(
      symbol: $symbol
      side: $side
      quantity: $quantity
      orderType: $orderType
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

export interface TradeThisSignal {
  symbol: string;
  signalType: string; // LONG | SHORT
  entryPrice: number;
  stopPrice?: number;
  mlScore?: number;
}

interface TradeThisModalProps {
  visible: boolean;
  onClose: () => void;
  signal: TradeThisSignal | null;
  onSuccess?: () => void;
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

export default function TradeThisModal({
  visible,
  onClose,
  signal,
  onSuccess,
}: TradeThisModalProps) {
  const { data: accountData } = useQuery(GET_PAPER_ACCOUNT_SUMMARY, {
    skip: !visible,
  });
  const [calculateSize, { data: sizeData, loading: sizeLoading }] = useLazyQuery(
    CALCULATE_POSITION_SIZE,
    { fetchPolicy: 'network-only' }
  );
  const [placeOrder, { loading: placing }] = useMutation(PLACE_PAPER_ORDER, {
    refetchQueries: [{ query: GET_PAPER_ACCOUNT_SUMMARY }],
  });

  const accountEquity =
    accountData?.paperAccountSummary?.account?.currentBalance ??
    accountData?.paperAccountSummary?.account?.totalValue ??
    0;
  const positionResult = sizeData?.calculatePositionSize;
  const suggestedShares = positionResult?.positionSize ?? 0;
  const positionValue = positionResult?.positionValue ?? 0;
  const backendMethod = (positionResult?.method ?? '').toLowerCase();
  const usedKelly = backendMethod === 'kelly';
  const methodSubtext = usedKelly
    ? (positionResult?.recommendedFraction != null
        ? ` (${(positionResult.recommendedFraction * 100).toFixed(0)}% of equity)`
        : '')
    : ' (fallback: position cap when Kelly isn’t available for this symbol)';

  useEffect(() => {
    if (!visible || !signal || accountEquity <= 0) return;
    const entryPrice = signal.entryPrice;
    const stopPrice =
      signal.stopPrice ??
      (signal.signalType === 'LONG'
        ? entryPrice * 0.98
        : entryPrice * 1.02);
    const confidence = typeof signal.mlScore === 'number' ? signal.mlScore : 0.7;
    calculateSize({
      variables: {
        accountEquity: Number(accountEquity),
        entryPrice,
        stopPrice,
        confidence,
        method: 'KELLY',
        symbol: signal.symbol,
      },
    });
  }, [visible, signal, accountEquity, calculateSize]);

  const handleConfirm = useCallback(() => {
    if (!signal || suggestedShares < 1) {
      Alert.alert('Invalid size', 'Suggested shares must be at least 1.');
      return;
    }
    const side = signal.signalType === 'LONG' ? 'BUY' : 'SELL';
    placeOrder({
      variables: {
        symbol: signal.symbol,
        side,
        quantity: Math.round(suggestedShares),
        orderType: 'MARKET',
      },
    })
      .then((res) => {
        const result = res.data?.placePaperOrder;
        if (result?.success) {
          onSuccess?.();
          onClose();
          Alert.alert('Order placed', 'Paper order placed successfully.');
        } else {
          Alert.alert('Order failed', result?.message ?? 'Unknown error');
        }
      })
      .catch((err) => {
        Alert.alert('Error', err.message ?? 'Failed to place order');
      });
  }, [signal, suggestedShares, placeOrder, onSuccess, onClose]);

  if (!signal) return null;

  const side = signal.signalType === 'LONG' ? 'BUY' : 'SELL';
  const estCost = suggestedShares * signal.entryPrice;

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent
      onRequestClose={onClose}
    >
      <View style={styles.overlay}>
        <View style={styles.content}>
          <View style={styles.header}>
            <Text style={styles.title}>Trade this signal</Text>
            <TouchableOpacity onPress={onClose} style={styles.closeBtn} hitSlop={12}>
              <Icon name="x" size={24} color="#6B7280" />
            </TouchableOpacity>
          </View>

          <View style={styles.row}>
            <Text style={styles.label}>Symbol</Text>
            <Text style={styles.value}>{signal.symbol}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>Side</Text>
            <Text style={[styles.value, styles[side === 'BUY' ? 'buy' : 'sell']]}>
              {side}
            </Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>Entry (est.)</Text>
            <Text style={styles.value}>{formatCurrency(signal.entryPrice)}</Text>
          </View>

          {sizeLoading ? (
            <View style={styles.loadingRow}>
              <ActivityIndicator size="small" color="#3B82F6" />
              <Text style={styles.loadingText}>Calculating size…</Text>
            </View>
          ) : (
            <>
              <View style={styles.row}>
                <Text style={styles.label}>Suggested shares</Text>
                <Text style={styles.value}>
                  {Math.round(suggestedShares) || '—'}
                </Text>
              </View>
              <View style={styles.row}>
                <Text style={styles.label}>Est. cost</Text>
                <Text style={styles.value}>
                  {suggestedShares >= 1
                    ? formatCurrency(estCost)
                    : '—'}
                </Text>
              </View>
              <View style={styles.kellyNote}>
                <Icon name="info" size={14} color="#6B7280" />
                <Text style={styles.kellyNoteText}>
                  Based on Kelly sizing{methodSubtext}
                </Text>
              </View>
            </>
          )}

          <View style={styles.actions}>
            <TouchableOpacity
              style={styles.cancelButton}
              onPress={onClose}
              disabled={placing}
            >
              <Text style={styles.cancelButtonText}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[
                styles.confirmButton,
                (suggestedShares < 1 || sizeLoading || placing) && styles.confirmDisabled,
              ]}
              onPress={handleConfirm}
              disabled={suggestedShares < 1 || sizeLoading || placing}
            >
              {placing ? (
                <ActivityIndicator size="small" color="#FFF" />
              ) : (
                <Text style={styles.confirmButtonText}>Confirm paper trade</Text>
              )}
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  content: {
    backgroundColor: '#FFF',
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    padding: 20,
    paddingBottom: 32,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  closeBtn: {
    padding: 4,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  label: {
    fontSize: 14,
    color: '#6B7280',
  },
  value: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  buy: {
    color: '#059669',
  },
  sell: {
    color: '#DC2626',
  },
  loadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 16,
    gap: 8,
  },
  loadingText: {
    fontSize: 14,
    color: '#6B7280',
  },
  kellyNote: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 8,
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
  },
  kellyNoteText: {
    fontSize: 12,
    color: '#6B7280',
  },
  actions: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 24,
  },
  cancelButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 10,
    backgroundColor: '#F3F4F6',
    alignItems: 'center',
  },
  cancelButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
  },
  confirmButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 10,
    backgroundColor: '#3B82F6',
    alignItems: 'center',
  },
  confirmDisabled: {
    opacity: 0.6,
  },
  confirmButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFF',
  },
});
