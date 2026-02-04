import React, { useState, useCallback, useMemo, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  SafeAreaView,
  Dimensions,
  Alert,
  Modal,
  TextInput,
  ActivityIndicator,
} from 'react-native';
import { useQuery, useMutation } from '@apollo/client';
import { gql } from '@apollo/client';
import { useNavigation } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/Feather';
import logger from '../../../utils/logger';
import {
  GET_SWING_SIGNALS,
  LIKE_SIGNAL,
  COMMENT_SIGNAL,
  SwingSignal,
  formatCurrency,
  formatPercentage,
  getTimeAgo,
  getSignalColor,
  getMLScoreColor,
  getMLScoreLabel,
} from '../../../graphql/swingTradingQueries';
import TradeThisModal, { TradeThisSignal } from '../../trading/components/TradeThisModal';

const { width } = Dimensions.get('window');

// Use the imported GraphQL queries from swingTradingQueries.ts

interface Signal {
  id: string;
  symbol: string;
  timeframe: string;
  triggeredAt: string;
  signalType: string;
  entryPrice: number;
  stopPrice?: number;
  targetPrice?: number;
  mlScore: number;
  thesis: string;
  riskRewardRatio?: number;
  daysSinceTriggered: number;
  isLikedByUser: boolean;
  userLikeCount: number;
  features: any;
  isActive: boolean;
  isValidated: boolean;
  validationPrice?: number;
  validationTimestamp?: string;
  createdBy: {
    id: string;
    username: string;
    name: string;
  };
}

interface SignalsScreenProps {
  navigateTo?: (screen: string) => void;
}

// Mock data for demo when API is unavailable
const getMockSignals = (): Signal[] => [
  {
    id: '1',
    symbol: 'AAPL',
    timeframe: '1D',
    triggeredAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    signalType: 'LONG',
    entryPrice: 175.50,
    stopPrice: 170.00,
    targetPrice: 185.00,
    mlScore: 0.85,
    thesis: 'Strong earnings beat and positive guidance. Technical breakout above resistance.',
    riskRewardRatio: 2.5,
    daysSinceTriggered: 2,
    isLikedByUser: false,
    userLikeCount: 42,
    features: {},
    isActive: true,
    isValidated: true,
    validationPrice: 176.20,
    validationTimestamp: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    createdBy: { id: '1', username: 'system', name: 'AI Trading System' },
  },
  {
    id: '2',
    symbol: 'TSLA',
    timeframe: '1D',
    triggeredAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    signalType: 'SHORT',
    entryPrice: 245.00,
    stopPrice: 250.00,
    targetPrice: 230.00,
    mlScore: 0.72,
    thesis: 'Overbought conditions and negative sentiment. Expecting pullback to support.',
    riskRewardRatio: 3.0,
    daysSinceTriggered: 1,
    isLikedByUser: true,
    userLikeCount: 28,
    features: {},
    isActive: true,
    isValidated: false,
    createdBy: { id: '1', username: 'system', name: 'AI Trading System' },
  },
  {
    id: '3',
    symbol: 'NVDA',
    timeframe: '1D',
    triggeredAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    signalType: 'LONG',
    entryPrice: 485.00,
    stopPrice: 475.00,
    targetPrice: 510.00,
    mlScore: 0.91,
    thesis: 'AI sector momentum continues. Strong institutional buying detected.',
    riskRewardRatio: 2.5,
    daysSinceTriggered: 3,
    isLikedByUser: false,
    userLikeCount: 67,
    features: {},
    isActive: true,
    isValidated: true,
    validationPrice: 492.50,
    validationTimestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    createdBy: { id: '1', username: 'system', name: 'AI Trading System' },
  },
];

const SignalsScreen: React.FC<SignalsScreenProps> = ({ navigateTo: navigateToProp }) => {
  const navigation = useNavigation<any>();
  const [refreshing, setRefreshing] = useState(false);
  const [selectedSignal, setSelectedSignal] = useState<Signal | null>(null);
  const [commentModalVisible, setCommentModalVisible] = useState(false);
  const [commentText, setCommentText] = useState('');
  const [tradeModalVisible, setTradeModalVisible] = useState(false);
  const [signalForTrade, setSignalForTrade] = useState<Signal | null>(null);
  const [loadingTimeout, setLoadingTimeout] = useState(false);
  const [filters, setFilters] = useState({
    symbol: '',
    signalType: '',
    minMlScore: 0.5,
    isActive: true,
  });

  // Use React Navigation if navigateTo prop not provided
  const navigateTo = navigateToProp || ((screen: string) => {
    try {
      navigation.navigate(screen as never);
    } catch (error) {
      logger.warn('Navigation error:', error);
      // Fallback to globalNavigate if available
      try {
        if (typeof window !== 'undefined' && (window as any).__navigateToGlobal) {
          (window as any).__navigateToGlobal(screen);
        }
      } catch (fallbackError) {
        logger.error('All navigation methods failed:', fallbackError);
      }
    }
  });
  
  // Ensure navigateTo is always a function
  if (typeof navigateTo !== 'function') {
    logger.error('navigateTo is not a function:', typeof navigateTo, navigateTo);
  }

  const { data, loading, error, refetch } = useQuery(GET_SWING_SIGNALS, {
    variables: {
      symbol: filters.symbol || undefined,
      signalType: filters.signalType || undefined,
      minMlScore: filters.minMlScore,
      isActive: filters.isActive,
      limit: 50,
    },
    pollInterval: 30000, // Poll every 30 seconds
    errorPolicy: 'all',
    fetchPolicy: 'cache-and-network',
    context: { fetchOptions: { timeout: 8000 } }, // 8 second timeout
  });

  // Timeout loading state after 10 seconds
  useEffect(() => {
    if (loading && !data) {
      const timeout = setTimeout(() => {
        setLoadingTimeout(true);
      }, 10000);
      return () => clearTimeout(timeout);
    } else {
      setLoadingTimeout(false);
    }
  }, [loading, data]);

  const [likeSignal] = useMutation(LIKE_SIGNAL);
  const [commentSignal] = useMutation(COMMENT_SIGNAL);

  // Use real data from GraphQL or fallback to mock data for demo
  const signals: SwingSignal[] = useMemo(() => {
    if (data?.swingSignals && data.swingSignals.length > 0) {
      return data.swingSignals;
    }
    // If loading timed out or no data, use mock data for demo
    if (loadingTimeout || (error && !data?.swingSignals)) {
      return getMockSignals();
    }
    return [];
  }, [data?.swingSignals, loadingTimeout, error]);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await refetch();
    } catch (error) {
      logger.error('Error refreshing signals:', error);
    } finally {
      setRefreshing(false);
    }
  }, [refetch]);

  const handleLikeSignal = useCallback(async (signalId: string) => {
    try {
      await likeSignal({
        variables: { signalId },
        optimisticResponse: {
          likeSignal: {
            success: true,
            isLiked: !signals.find(s => s.id === signalId)?.isLikedByUser,
            likeCount: (signals.find(s => s.id === signalId)?.userLikeCount || 0) + 1,
            errors: [],
          },
        },
      });
    } catch (error) {
      logger.error('Error liking signal:', error);
      Alert.alert('Error', 'Failed to like signal');
    }
  }, [likeSignal, signals]);

  const handleCommentSignal = useCallback(async () => {
    if (!selectedSignal || !commentText.trim()) return;

    try {
      await commentSignal({
        variables: {
          signalId: selectedSignal.id,
          content: commentText.trim(),
        },
      });
      setCommentModalVisible(false);
      setCommentText('');
      setSelectedSignal(null);
      Alert.alert('Success', 'Comment added successfully');
    } catch (error) {
      logger.error('Error commenting on signal:', error);
      Alert.alert('Error', 'Failed to add comment');
    }
  }, [commentSignal, selectedSignal, commentText]);

  const getSignalTypeDisplay = (signalType: string) => {
    return signalType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const getSignalTypeColor = (signalType: string) => {
    if (signalType.includes('long')) return '#10B981';
    if (signalType.includes('short')) return '#EF4444';
    return '#6B7280';
  };

  const getMlScoreColor = (score: number) => {
    if (score >= 0.8) return '#10B981';
    if (score >= 0.6) return '#F59E0B';
    return '#EF4444';
  };

  const formatPrice = (price: number) => {
    return `$${price.toFixed(2)}`;
  };

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  const renderSignalCard = useCallback(({ item }: { item: Signal }) => (
    <TouchableOpacity
      style={styles.signalCard}
      onPress={() => setSelectedSignal(item)}
      activeOpacity={0.7}
    >
      <View style={styles.signalHeader}>
        <View style={styles.symbolContainer}>
          <Text style={styles.symbolText}>{item.symbol}</Text>
          <Text style={styles.timeframeText}>{item.timeframe}</Text>
        </View>
        <View style={styles.signalTypeContainer}>
          <View
            style={[
              styles.signalTypeBadge,
              { backgroundColor: getSignalTypeColor(item.signalType) },
            ]}
          >
            <Text style={styles.signalTypeText}>
              {getSignalTypeDisplay(item.signalType)}
            </Text>
          </View>
        </View>
      </View>

      <View style={styles.signalMetrics}>
        <View style={styles.metricItem}>
          <Text style={styles.metricLabel}>ML Score</Text>
          <Text
            style={[
              styles.metricValue,
              { color: getMlScoreColor(item.mlScore) },
            ]}
          >
            {formatPercentage(item.mlScore)}
          </Text>
        </View>
        <View style={styles.metricItem}>
          <Text style={styles.metricLabel}>Entry</Text>
          <Text style={styles.metricValue}>{formatPrice(item.entryPrice)}</Text>
        </View>
        <View style={styles.metricItem}>
          <Text style={styles.metricLabel}>Stop</Text>
          <Text style={styles.metricValue}>
            {item.stopPrice ? formatPrice(item.stopPrice) : 'N/A'}
          </Text>
        </View>
        <View style={styles.metricItem}>
          <Text style={styles.metricLabel}>Target</Text>
          <Text style={styles.metricValue}>
            {item.targetPrice ? formatPrice(item.targetPrice) : 'N/A'}
          </Text>
        </View>
      </View>

      {item.riskRewardRatio && (
        <View style={styles.riskRewardContainer}>
          <Text style={styles.riskRewardText}>
            R/R: {item.riskRewardRatio.toFixed(2)}
          </Text>
        </View>
      )}

      <Text style={styles.thesisText} numberOfLines={2}>
        {item.thesis}
      </Text>

      <View style={styles.signalFooter}>
        <View style={styles.timeContainer}>
          <Icon name="clock" size={14} color="#6B7280" />
          <Text style={styles.timeText}>
            {item.daysSinceTriggered}d ago
          </Text>
        </View>
        <View style={styles.actionsContainer}>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => handleLikeSignal(item.id)}
          >
            <Icon
              name={item.isLikedByUser ? 'heart' : 'heart'}
              size={16}
              color={item.isLikedByUser ? '#EF4444' : '#6B7280'}
            />
            <Text style={styles.actionText}>{item.userLikeCount}</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => {
              setSelectedSignal(item);
              setCommentModalVisible(true);
            }}
          >
            <Icon name="message-circle" size={16} color="#6B7280" />
            <Text style={styles.actionText}>Comment</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.actionButton, styles.tradeThisButton]}
            onPress={() => {
              setSignalForTrade(item);
              setTradeModalVisible(true);
            }}
          >
            <Icon name="zap" size={16} color="#3B82F6" />
            <Text style={[styles.actionText, styles.tradeThisText]}>Trade this</Text>
          </TouchableOpacity>
        </View>
      </View>
    </TouchableOpacity>
  ), [handleLikeSignal]);

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <Icon name="trending-up" size={64} color="#D1D5DB" />
      <Text style={styles.emptyStateTitle}>No Signals Found</Text>
      <Text style={styles.emptyStateText}>
        Try adjusting your filters or check back later for new signals.
      </Text>
    </View>
  );

  const renderLoadingState = () => (
    <View style={styles.loadingState}>
      <ActivityIndicator size="large" color="#3B82F6" />
      <Text style={styles.loadingText}>Loading signals...</Text>
    </View>
  );

  // Show loading only if actively loading and haven't timed out
  if (loading && !data && !loadingTimeout) {
    return renderLoadingState();
  }

  if (error) {
    return (
      <View style={styles.errorState}>
        <Icon name="alert-circle" size={64} color="#EF4444" />
        <Text style={styles.errorTitle}>Error Loading Signals</Text>
        <Text style={styles.errorText}>{error.message}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={handleRefresh}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigateTo('swing-trading-test')}
        >
          <Icon name="arrow-left" size={24} color="#6B7280" />
        </TouchableOpacity>
        <View style={styles.headerTitleContainer}>
          <Text style={styles.headerTitle}>Swing Trading Signals</Text>
        </View>
        <TouchableOpacity
          style={styles.filterButton}
          onPress={() => {
            // Future enhancement: Implement filter modal for signal filtering (timeframe, sector, etc.)
            Alert.alert('Filters', 'Filter functionality coming soon');
          }}
        >
          <Icon name="filter" size={20} color="#6B7280" />
        </TouchableOpacity>
      </View>

      <FlatList
        data={signals}
        keyExtractor={(item) => item.id}
        renderItem={renderSignalCard}
        contentContainerStyle={styles.listContainer}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
        }
        ListEmptyComponent={renderEmptyState}
        showsVerticalScrollIndicator={false}
      />

      {/* Comment Modal */}
      <Modal
        visible={commentModalVisible}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setCommentModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Add Comment</Text>
              <TouchableOpacity
                onPress={() => setCommentModalVisible(false)}
                style={styles.closeButton}
              >
                <Icon name="x" size={24} color="#6B7280" />
              </TouchableOpacity>
            </View>
            <TextInput
              style={styles.commentInput}
              placeholder="Write your comment..."
              value={commentText}
              onChangeText={setCommentText}
              multiline
              numberOfLines={4}
              textAlignVertical="top"
            />
            <View style={styles.modalActions}>
              <TouchableOpacity
                style={styles.cancelButton}
                onPress={() => setCommentModalVisible(false)}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.submitButton}
                onPress={handleCommentSignal}
                disabled={!commentText.trim()}
              >
                <Text style={styles.submitButtonText}>Submit</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      <TradeThisModal
        visible={tradeModalVisible}
        onClose={() => {
          setTradeModalVisible(false);
          setSignalForTrade(null);
        }}
        signal={signalForTrade ? {
          symbol: signalForTrade.symbol,
          signalType: signalForTrade.signalType,
          entryPrice: signalForTrade.entryPrice,
          stopPrice: signalForTrade.stopPrice,
          mlScore: signalForTrade.mlScore,
        } as TradeThisSignal : null}
        onSuccess={() => handleRefresh()}
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  backButton: {
    padding: 8,
    marginRight: 8,
  },
  headerTitleContainer: {
    flex: 1,
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#111827',
  },
  filterButton: {
    padding: 8,
  },
  listContainer: {
    padding: 16,
  },
  signalCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  signalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  symbolContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  symbolText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginRight: 8,
  },
  timeframeText: {
    fontSize: 12,
    color: '#6B7280',
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  signalTypeContainer: {
    flex: 1,
    alignItems: 'flex-end',
  },
  signalTypeBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  signalTypeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  signalMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  metricItem: {
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  riskRewardContainer: {
    alignSelf: 'flex-start',
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    marginBottom: 12,
  },
  riskRewardText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#92400E',
  },
  thesisText: {
    fontSize: 14,
    color: '#374151',
    lineHeight: 20,
    marginBottom: 12,
  },
  signalFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  timeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  timeText: {
    fontSize: 12,
    color: '#6B7280',
    marginLeft: 4,
  },
  actionsContainer: {
    flexDirection: 'row',
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    marginLeft: 16,
  },
  actionText: {
    fontSize: 12,
    color: '#6B7280',
    marginLeft: 4,
  },
  tradeThisButton: {
    marginLeft: 12,
  },
  tradeThisText: {
    color: '#3B82F6',
    fontWeight: '600',
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  emptyStateTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#374151',
    marginTop: 16,
    marginBottom: 8,
  },
  emptyStateText: {
    fontSize: 16,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 24,
  },
  loadingState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#6B7280',
  },
  errorState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  errorTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#EF4444',
    marginTop: 16,
    marginBottom: 8,
  },
  errorText: {
    fontSize: 16,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 24,
  },
  retryButton: {
    backgroundColor: '#3B82F6',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 20,
    width: width * 0.9,
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  closeButton: {
    padding: 4,
  },
  commentInput: {
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: '#111827',
    marginBottom: 16,
    minHeight: 100,
  },
  modalActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
  },
  cancelButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginRight: 12,
  },
  cancelButtonText: {
    fontSize: 16,
    color: '#6B7280',
  },
  submitButton: {
    backgroundColor: '#3B82F6',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 6,
  },
  submitButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});

export default SignalsScreen;
