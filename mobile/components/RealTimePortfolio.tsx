import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Alert,
  ActivityIndicator,
  Animated,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import RealTimePortfolioService, { PortfolioMetrics, PortfolioHolding, PortfolioUpdate } from '../services/RealTimePortfolioService';

interface RealTimePortfolioProps {
  onHoldingPress?: (holding: PortfolioHolding) => void;
}

const RealTimePortfolio: React.FC<RealTimePortfolioProps> = ({ onHoldingPress }) => {
  const [portfolio, setPortfolio] = useState<PortfolioMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string>('');
  const [isTracking, setIsTracking] = useState(false);
  const pulseAnim = useState(new Animated.Value(1))[0];

  useEffect(() => {
    // Start real-time tracking
    RealTimePortfolioService.startTracking();
    setIsTracking(true);

    // Subscribe to portfolio updates
    const handlePortfolioUpdate = (update: PortfolioUpdate) => {
      if (update.type === 'portfolio_refresh') {
        setPortfolio(update.data as PortfolioMetrics);
        setLastUpdate(new Date(update.timestamp).toLocaleTimeString());
        setError(null);
        
        // Pulse animation for updates
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.05,
            duration: 200,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 200,
            useNativeDriver: true,
          }),
        ]).start();
      } else if (update.type === 'error') {
        setError(update.data as string);
      }
    };

    RealTimePortfolioService.onPortfolioUpdate(handlePortfolioUpdate);

    // Load initial data
    loadPortfolio();

    return () => {
      RealTimePortfolioService.offPortfolioUpdate(handlePortfolioUpdate);
    };
  }, []);

  const loadPortfolio = async () => {
    try {
      setLoading(true);
      const data = await RealTimePortfolioService.getCurrentMetrics();
      if (data) {
        setPortfolio(data);
        setLastUpdate(new Date(data.lastUpdated).toLocaleTimeString());
      }
    } catch (err) {
      setError('Failed to load portfolio');
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadPortfolio();
    setRefreshing(false);
  };

  const toggleTracking = () => {
    if (isTracking) {
      RealTimePortfolioService.stopTracking();
      setIsTracking(false);
    } else {
      RealTimePortfolioService.startTracking();
      setIsTracking(true);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatPercent = (percent: number) => {
    const sign = percent >= 0 ? '+' : '';
    return `${sign}${percent.toFixed(2)}%`;
  };

  const getReturnColor = (amount: number) => {
    if (amount > 0) return '#34C759';
    if (amount < 0) return '#FF3B30';
    return '#8E8E93';
  };

  const getReturnIcon = (amount: number) => {
    if (amount > 0) return 'trending-up';
    if (amount < 0) return 'trending-down';
    return 'minus';
  };

  const renderHolding = (holding: PortfolioHolding) => (
    <TouchableOpacity
      key={holding.symbol}
      style={styles.holdingCard}
      onPress={() => onHoldingPress?.(holding)}
      activeOpacity={0.7}
    >
      <View style={styles.holdingHeader}>
        <View style={styles.holdingInfo}>
          <Text style={styles.symbol}>{holding.symbol}</Text>
          <Text style={styles.companyName} numberOfLines={1}>
            {holding.companyName}
          </Text>
        </View>
        <View style={styles.holdingPrice}>
          <Text style={styles.currentPrice}>
            {formatCurrency(holding.currentPrice)}
          </Text>
          <View style={[styles.returnBadge, { backgroundColor: getReturnColor(holding.returnAmount) }]}>
            <Icon 
              name={getReturnIcon(holding.returnAmount)} 
              size={12} 
              color="#fff" 
            />
            <Text style={styles.returnText}>
              {formatPercent(holding.returnPercent)}
            </Text>
          </View>
        </View>
      </View>
      
      <View style={styles.holdingDetails}>
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>Shares:</Text>
          <Text style={styles.detailValue}>{holding.shares}</Text>
        </View>
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>Total Value:</Text>
          <Text style={styles.detailValue}>{formatCurrency(holding.totalValue)}</Text>
        </View>
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>Return:</Text>
          <Text style={[styles.detailValue, { color: getReturnColor(holding.returnAmount) }]}>
            {formatCurrency(holding.returnAmount)}
          </Text>
        </View>
      </View>
    </TouchableOpacity>
  );

  if (loading && !portfolio) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading portfolio...</Text>
      </View>
    );
  }

  if (error && !portfolio) {
    return (
      <View style={styles.errorContainer}>
        <Icon name="alert-circle" size={48} color="#FF3B30" />
        <Text style={styles.errorTitle}>Failed to Load Portfolio</Text>
        <Text style={styles.errorMessage}>{error}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={loadPortfolio}>
          <Text style={styles.retryButtonText}>Try Again</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (!portfolio) {
    return (
      <View style={styles.emptyContainer}>
        <Icon name="pie-chart" size={48} color="#8E8E93" />
        <Text style={styles.emptyTitle}>No Portfolio Data</Text>
        <Text style={styles.emptyMessage}>
          Your portfolio will appear here once you add holdings
        </Text>
      </View>
    );
  }

  return (
    <ScrollView 
      style={styles.container}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={onRefresh}
          colors={['#007AFF']}
          tintColor="#007AFF"
        />
      }
    >
      {/* Portfolio Header */}
      <Animated.View style={[styles.portfolioHeader, { transform: [{ scale: pulseAnim }] }]}>
        <View style={styles.headerTop}>
          <Text style={styles.headerTitle}>Portfolio</Text>
          <TouchableOpacity onPress={toggleTracking} style={styles.trackingButton}>
            <Icon 
              name={isTracking ? "pause-circle" : "play-circle"} 
              size={24} 
              color={isTracking ? "#34C759" : "#8E8E93"} 
            />
          </TouchableOpacity>
        </View>
        
        <View style={styles.portfolioMetrics}>
          <Text style={styles.totalValue}>
            {formatCurrency(portfolio.totalValue)}
          </Text>
          <View style={styles.returnContainer}>
            <View style={[styles.totalReturnBadge, { backgroundColor: getReturnColor(portfolio.totalReturn) }]}>
              <Icon 
                name={getReturnIcon(portfolio.totalReturn)} 
                size={16} 
                color="#fff" 
              />
              <Text style={styles.totalReturnText}>
                {formatCurrency(portfolio.totalReturn)} ({formatPercent(portfolio.totalReturnPercent)})
              </Text>
            </View>
          </View>
        </View>

        {portfolio.dayChange !== 0 && (
          <View style={styles.dayChangeContainer}>
            <Text style={styles.dayChangeLabel}>Today:</Text>
            <Text style={[styles.dayChangeValue, { color: getReturnColor(portfolio.dayChange) }]}>
              {formatCurrency(portfolio.dayChange)} ({formatPercent(portfolio.dayChangePercent)})
            </Text>
          </View>
        )}

        <View style={styles.lastUpdateContainer}>
          <Icon name="clock" size={12} color="#8E8E93" />
          <Text style={styles.lastUpdateText}>
            {isTracking ? 'Live' : 'Paused'} • Updated {lastUpdate}
          </Text>
        </View>
      </Animated.View>

      {/* Holdings List */}
      <View style={styles.holdingsSection}>
        <Text style={styles.sectionTitle}>
          Holdings ({portfolio.holdings.length})
        </Text>
        {portfolio.holdings.map(renderHolding)}
      </View>

      {/* Portfolio Summary */}
      <View style={styles.summarySection}>
        <Text style={styles.sectionTitle}>Summary</Text>
        <View style={styles.summaryCard}>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Total Invested:</Text>
            <Text style={styles.summaryValue}>{formatCurrency(portfolio.totalCost)}</Text>
          </View>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Current Value:</Text>
            <Text style={styles.summaryValue}>{formatCurrency(portfolio.totalValue)}</Text>
          </View>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Total Return:</Text>
            <Text style={[styles.summaryValue, { color: getReturnColor(portfolio.totalReturn) }]}>
              {formatCurrency(portfolio.totalReturn)}
            </Text>
          </View>
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
    padding: 32,
  },
  errorTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 16,
    marginBottom: 8,
  },
  errorMessage: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginBottom: 24,
  },
  retryButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
    padding: 32,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 16,
    marginBottom: 8,
  },
  emptyMessage: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
  },
  portfolioHeader: {
    backgroundColor: '#fff',
    padding: 20,
    margin: 16,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  headerTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  trackingButton: {
    padding: 4,
  },
  portfolioMetrics: {
    alignItems: 'center',
    marginBottom: 16,
  },
  totalValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  returnContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
  },
  totalReturnBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  totalReturnText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 4,
  },
  dayChangeContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  dayChangeLabel: {
    fontSize: 14,
    color: '#666',
    marginRight: 8,
  },
  dayChangeValue: {
    fontSize: 14,
    fontWeight: '600',
  },
  lastUpdateContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  lastUpdateText: {
    fontSize: 12,
    color: '#8E8E93',
    marginLeft: 4,
  },
  holdingsSection: {
    paddingHorizontal: 16,
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  holdingCard: {
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
  holdingHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  holdingInfo: {
    flex: 1,
  },
  symbol: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  companyName: {
    fontSize: 14,
    color: '#666',
    marginTop: 2,
  },
  holdingPrice: {
    alignItems: 'flex-end',
  },
  currentPrice: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  returnBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  returnText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
    marginLeft: 2,
  },
  holdingDetails: {
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
    paddingTop: 12,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  detailLabel: {
    fontSize: 14,
    color: '#666',
  },
  detailValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  summarySection: {
    paddingHorizontal: 16,
    marginBottom: 20,
  },
  summaryCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  summaryLabel: {
    fontSize: 14,
    color: '#666',
  },
  summaryValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
});

export default RealTimePortfolio;
