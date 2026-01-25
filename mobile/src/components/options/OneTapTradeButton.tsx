import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { useQuery, useMutation } from '@apollo/client';
import { GET_ONE_TAP_TRADES } from '../../graphql/optionsQueries';
import { PLACE_MULTI_LEG_OPTIONS_ORDER } from '../../graphql/optionsMutations';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import logger from '../../utils/logger';

interface OneTapLeg {
  action: string;
  optionType: string;
  strike: number;
  expiration: string;
  quantity: number;
  premium: number;
}

interface OneTapTrade {
  strategy: string;
  entryPrice: number;
  expectedEdge: number;
  confidence: number;
  takeProfit: number;
  stopLoss: number;
  reasoning: string;
  maxLoss: number;
  maxProfit: number;
  probabilityOfProfit: number;
  symbol: string;
  legs: OneTapLeg[];
  strategyType: string;
  daysToExpiration: number;
  totalCost: number;
  totalCredit: number;
}

interface OneTapTradeButtonProps {
  symbol: string;
  accountSize?: number;
  riskTolerance?: number;
  onTradeExecuted?: (tradeId: string) => void;
}

export const OneTapTradeButton: React.FC<OneTapTradeButtonProps> = ({
  symbol,
  accountSize = 10000,
  riskTolerance = 0.1,
  onTradeExecuted,
}) => {
  const { data, loading, error, refetch } = useQuery(GET_ONE_TAP_TRADES, {
    variables: {
      symbol,
      accountSize,
      riskTolerance,
    },
    skip: !symbol || symbol.length === 0, // Skip if no symbol
    pollInterval: 60000, // Update every 60 seconds (reduced frequency to avoid rate limits)
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all', // Return partial data even on error
    notifyOnNetworkStatusChange: true,
  });

  const [placeOrder, { loading: placingOrder }] = useMutation(
    PLACE_MULTI_LEG_OPTIONS_ORDER,
    {
      onCompleted: (data) => {
        if (data?.placeMultiLegOptionsOrder?.success) {
          onTradeExecuted?.(data.placeMultiLegOptionsOrder.orderIds?.[0] || '');
        }
      },
      onError: (error) => {
        logger.error('Error placing one-tap trade:', error);
      },
    }
  );

  if (loading && !data) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="small" color="#007AFF" />
        <Text style={styles.loadingText}>Finding best trade...</Text>
      </View>
    );
  }

  // Check if error is rate limit (429)
  const isRateLimitError = error?.message?.includes('429') ||
                           error?.message?.includes('rate') ||
                           error?.message?.includes('Too many requests') ||
                           (error?.networkError as any)?.statusCode === 429;

  if (error || !data?.oneTapTrades || data.oneTapTrades.length === 0) {
    const handleRetry = async () => {
      try {
        // Wait a bit before retrying if rate limited
        if (isRateLimitError) {
          await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds
        }
        await refetch();
      } catch (err) {
        logger.error('Error retrying one-tap trades:', err);
      }
    };

    return (
      <View style={styles.container}>
        <Text style={styles.emptyText}>
          {error ? 'Failed to load trades' : 'No one-tap trades available'}
        </Text>
        {error && (
          <Text style={styles.errorText}>
            {isRateLimitError 
              ? 'Rate limit reached. Please wait a moment and try again.'
              : error.message || 'Please try again'}
          </Text>
        )}
        <TouchableOpacity
          style={[styles.retryButton, (loading || isRateLimitError) && styles.retryButtonDisabled]}
          onPress={handleRetry}
          disabled={loading || isRateLimitError}
        >
          {loading ? (
            <>
              <ActivityIndicator size="small" color="#FFFFFF" />
              <Text style={styles.retryButtonText}>Retrying...</Text>
            </>
          ) : (
            <Text style={styles.retryButtonText}>
              {isRateLimitError ? 'Wait & Retry' : 'Retry'}
            </Text>
          )}
        </TouchableOpacity>
      </View>
    );
  }

  const topTrade: OneTapTrade = data.oneTapTrades[0];

  const handleExecute = async () => {
    try {
      // Convert legs to GraphQL format
      const legs = topTrade.legs.map(leg => JSON.stringify({
        action: leg.action,
        optionType: leg.optionType,
        strike: leg.strike,
        expiration: leg.expiration,
        quantity: leg.quantity,
        premium: leg.premium,
      }));

      await placeOrder({
        variables: {
          symbol: topTrade.symbol,
          legs,
          strategyName: topTrade.strategy,
        },
      });
    } catch (error) {
      logger.error('Error executing one-tap trade:', error);
    }
  };

  const isCredit = topTrade.totalCredit > 0;
  const costDisplay = isCredit
    ? `$${topTrade.totalCredit.toFixed(2)} credit`
    : `$${topTrade.totalCost.toFixed(2)} debit`;

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Icon name="lightning-bolt" size={24} color="#007AFF" />
          <Text style={styles.title}>Do This Exact Trade</Text>
        </View>
        <View style={styles.confidenceBadge}>
          <Text style={styles.confidenceText}>
            {topTrade.confidence.toFixed(0)}%
          </Text>
        </View>
      </View>

      <View style={styles.tradeCard}>
        <Text style={styles.strategyText}>{topTrade.strategy}</Text>
        <Text style={styles.priceText}>@ {costDisplay}</Text>

        <View style={styles.metricsRow}>
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>Expected Edge</Text>
            <Text style={styles.metricValue}>
              +{topTrade.expectedEdge.toFixed(0)}% in 4hrs
            </Text>
          </View>
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>Win Chance</Text>
            <Text style={styles.metricValue}>
              {(topTrade.probabilityOfProfit * 100).toFixed(0)}%
            </Text>
          </View>
        </View>

        <View style={styles.riskRow}>
          <View style={styles.riskItem}>
            <Text style={styles.riskLabel}>Max Profit</Text>
            <Text style={[styles.riskValue, styles.positiveValue]}>
              ${topTrade.maxProfit.toFixed(2)}
            </Text>
          </View>
          <View style={styles.riskItem}>
            <Text style={styles.riskLabel}>Max Loss</Text>
            <Text style={[styles.riskValue, styles.negativeValue]}>
              ${topTrade.maxLoss.toFixed(2)}
            </Text>
          </View>
        </View>

        {topTrade.reasoning && (
          <View style={styles.reasoningContainer}>
            <Icon name="information" size={16} color="#6B7280" />
            <Text style={styles.reasoningText}>{topTrade.reasoning}</Text>
          </View>
        )}

        <TouchableOpacity
          style={[
            styles.executeButton,
            placingOrder && styles.executeButtonDisabled,
          ]}
          onPress={handleExecute}
          disabled={placingOrder}
        >
          {placingOrder ? (
            <>
              <ActivityIndicator size="small" color="#FFFFFF" />
              <Text style={styles.executeButtonText}>Placing Order...</Text>
            </>
          ) : (
            <>
              <Icon name="check-circle" size={20} color="#FFFFFF" />
              <Text style={styles.executeButtonText}>
                Execute Trade • {costDisplay}
              </Text>
            </>
          )}
        </TouchableOpacity>

        <View style={styles.bracketsInfo}>
          <View style={styles.bracketItem}>
            <Icon name="trending-up" size={14} color="#10B981" />
            <Text style={styles.bracketText}>
              Take Profit: ${topTrade.takeProfit.toFixed(2)}
            </Text>
          </View>
          <View style={styles.bracketItem}>
            <Icon name="trending-down" size={14} color="#EF4444" />
            <Text style={styles.bracketText}>
              Stop Loss: ${topTrade.stopLoss.toFixed(2)}
            </Text>
          </View>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    marginVertical: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  title: {
    fontSize: 20,
    fontWeight: '800',
    color: '#111827',
    marginLeft: 8,
  },
  confidenceBadge: {
    backgroundColor: '#10B981',
    paddingVertical: 4,
    paddingHorizontal: 12,
    borderRadius: 12,
  },
  confidenceText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  loadingText: {
    marginTop: 8,
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
  },
  emptyText: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    marginBottom: 8,
  },
  errorText: {
    fontSize: 12,
    color: '#EF4444',
    textAlign: 'center',
    marginBottom: 12,
  },
  retryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    paddingHorizontal: 20,
    backgroundColor: '#007AFF',
    borderRadius: 8,
    alignSelf: 'center',
    minWidth: 100,
  },
  retryButtonDisabled: {
    opacity: 0.6,
  },
  retryButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 8,
  },
  tradeCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 16,
  },
  strategyText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 8,
  },
  priceText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
    marginBottom: 16,
  },
  metricsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  metric: {
    flex: 1,
  },
  metricLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
  },
  riskRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  riskItem: {
    flex: 1,
  },
  riskLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  riskValue: {
    fontSize: 16,
    fontWeight: '700',
  },
  positiveValue: {
    color: '#10B981',
  },
  negativeValue: {
    color: '#EF4444',
  },
  reasoningContainer: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 16,
    padding: 12,
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
  },
  reasoningText: {
    flex: 1,
    marginLeft: 8,
    fontSize: 13,
    color: '#6B7280',
    lineHeight: 18,
  },
  executeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    marginBottom: 12,
  },
  executeButtonDisabled: {
    opacity: 0.6,
  },
  executeButtonText: {
    marginLeft: 8,
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  bracketsInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  bracketItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  bracketText: {
    marginLeft: 6,
    fontSize: 12,
    color: '#6B7280',
  },
});

