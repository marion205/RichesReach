/**
 * Tomorrow Screen - Trade Tomorrow's Markets Today
 * Simple, Jobs-style: One sentence, one visual, one action
 */

import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

import FuturesService from '../services/FuturesService';
import { FuturesRecommendation, FuturesPosition } from '../types/FuturesTypes';

export default function TomorrowScreen({ navigation }: any) {
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [recommendations, setRecommendations] = useState<FuturesRecommendation[]>([]);
  const [positions, setPositions] = useState<FuturesPosition[]>([]);
  const [showPositions, setShowPositions] = useState(false);

  // Use REST API (more reliable than GraphQL for now)
  const loadRecommendations = useCallback(async () => {
    try {
      setLoading(true);
      const resp = await FuturesService.getRecommendations();
      setRecommendations(resp.recommendations || []);
    } catch (e) {
      Alert.alert('Error', 'Failed to load recommendations');
    } finally {
      setLoading(false);
    }
  }, []);

  // Load recommendations on mount
  React.useEffect(() => {
    loadRecommendations();
  }, [loadRecommendations]);

  const loadPositions = useCallback(async () => {
    try {
      const resp = await FuturesService.getPositions();
      setPositions(resp.positions || []);
    } catch (e) {
      // Silent fail for positions
    }
  }, []);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadRecommendations();
    await loadPositions();
    setRefreshing(false);
  }, [loadRecommendations, loadPositions]);

  const handleTrade = useCallback(async (rec: FuturesRecommendation) => {
    Alert.alert(
      'Confirm Trade',
      `${rec.action} ${rec.symbol}?\n\nWhy: ${rec.why_now}\nMax Loss: $${rec.max_loss}`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Trade',
          onPress: async () => {
            try {
              const result = await FuturesService.placeOrder({
                symbol: rec.symbol,
                side: rec.action === 'Buy' ? 'BUY' : 'SELL',
                quantity: 1, // Start with 1 micro contract
              });
              
              // Check if blocked with "Why not"
              if (result.status === 'blocked' && result.why_not) {
                const whyNot = result.why_not;
                Alert.alert(
                  'Order Blocked',
                  `${whyNot.reason}\n\n${whyNot.fix || ''}`,
                  [{ text: 'OK' }]
                );
              } else if (result.status === 'duplicate') {
                Alert.alert('Info', 'Order already submitted');
              } else {
                Alert.alert('Success', result.message || 'Order placed');
                handleRefresh();
              }
            } catch (e: any) {
              Alert.alert('Error', e.message || 'Failed to place order');
            }
          },
        },
      ]
    );
  }, [handleRefresh]);

  // Load positions on mount
  React.useEffect(() => {
    loadPositions();
  }, [loadPositions]);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Tomorrow</Text>
        <Text style={styles.headerSubtitle}>Trade tomorrow's markets today</Text>
        {positions.length > 0 && (
          <TouchableOpacity
            style={styles.positionsButton}
            onPress={() => setShowPositions(!showPositions)}
          >
            <Text style={styles.positionsButtonText}>
              {showPositions ? 'Hide' : 'Show'} Positions ({positions.length})
            </Text>
          </TouchableOpacity>
        )}
      </View>

      <ScrollView
        style={styles.content}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />}
      >
        {showPositions && positions.length > 0 && (
          <View style={styles.positionsSection}>
            <Text style={styles.sectionTitle}>Open Positions</Text>
            {positions.map((pos, idx) => (
              <View key={idx} style={styles.positionCard}>
                <View style={styles.positionHeader}>
                  <Text style={styles.positionSymbol}>{pos.symbol}</Text>
                  <Text style={[styles.positionPnl, pos.pnl >= 0 ? styles.positive : styles.negative]}>
                    {pos.pnl >= 0 ? '+' : ''}${pos.pnl.toFixed(2)}
                  </Text>
                </View>
                <Text style={styles.positionDetails}>
                  {pos.side} {pos.quantity} @ ${pos.entry_price.toFixed(2)} • Now: ${pos.current_price.toFixed(2)}
                </Text>
                <Text style={styles.positionPercent}>
                  {pos.pnl_percent >= 0 ? '+' : ''}{pos.pnl_percent.toFixed(2)}%
                </Text>
              </View>
            ))}
          </View>
        )}
        
        {loading && !recommendations.length ? (
          <View style={styles.center}>
            <ActivityIndicator size="large" color="#007AFF" />
            <Text style={styles.loadingText}>Loading recommendations...</Text>
          </View>
        ) : recommendations.length === 0 ? (
          <View style={styles.center}>
            <Icon name="calendar" size={48} color="#8E8E93" />
            <Text style={styles.emptyText}>No recommendations yet</Text>
            <TouchableOpacity style={styles.refreshButton} onPress={loadRecommendations}>
              <Text style={styles.refreshButtonText}>Refresh</Text>
            </TouchableOpacity>
          </View>
        ) : (
          recommendations.map((rec, idx) => (
            <TouchableOpacity
              key={idx}
              style={styles.card}
              onPress={() => handleTrade(rec)}
            >
              <View style={styles.cardHeader}>
                <Text style={styles.cardSymbol}>{rec.symbol}</Text>
                <Text style={styles.cardName}>{rec.name}</Text>
              </View>
              
              <Text style={styles.cardWhy}>{rec.why_now}</Text>
              
              <View style={styles.cardMetrics}>
                <View style={styles.cardMetric}>
                  <Text style={styles.cardMetricLabel}>Max Loss</Text>
                  <Text style={styles.cardMetricValue}>${rec.max_loss}</Text>
                </View>
                <View style={styles.cardMetric}>
                  <Text style={styles.cardMetricLabel}>Max Gain</Text>
                  <Text style={[styles.cardMetricValue, styles.positive]}>${rec.max_gain}</Text>
                </View>
                <View style={styles.cardMetric}>
                  <Text style={styles.cardMetricLabel}>Probability</Text>
                  <Text style={styles.cardMetricValue}>{rec.probability}%</Text>
                </View>
              </View>

              <View style={styles.cardAction}>
                <Text style={styles.cardActionText}>{rec.action}</Text>
                <Icon name="chevron-right" size={20} color="#007AFF" />
              </View>
            </TouchableOpacity>
          ))
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  header: {
    padding: 20,
    backgroundColor: 'white',
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#E5E5EA',
  },
  headerTitle: {
    fontSize: 34,
    fontWeight: '700',
    color: '#000',
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 17,
    color: '#8E8E93',
  },
  content: {
    flex: 1,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 17,
    color: '#8E8E93',
  },
  emptyText: {
    marginTop: 16,
    fontSize: 17,
    color: '#8E8E93',
    textAlign: 'center',
  },
  refreshButton: {
    marginTop: 20,
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: '#007AFF',
    borderRadius: 8,
  },
  refreshButtonText: {
    color: 'white',
    fontSize: 17,
    fontWeight: '600',
  },
  card: {
    backgroundColor: 'white',
    margin: 16,
    marginBottom: 0,
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  cardHeader: {
    marginBottom: 8,
  },
  cardSymbol: {
    fontSize: 24,
    fontWeight: '700',
    color: '#000',
  },
  cardName: {
    fontSize: 15,
    color: '#8E8E93',
    marginTop: 2,
  },
  cardWhy: {
    fontSize: 17,
    color: '#000',
    marginVertical: 12,
    lineHeight: 24,
  },
  cardMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginVertical: 16,
    paddingTop: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: '#E5E5EA',
  },
  cardMetric: {
    alignItems: 'center',
  },
  cardMetricLabel: {
    fontSize: 13,
    color: '#8E8E93',
    marginBottom: 4,
  },
  cardMetricValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#000',
  },
  positive: {
    color: '#34C759',
  },
  cardAction: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 8,
    paddingTop: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: '#E5E5EA',
  },
  cardActionText: {
    fontSize: 17,
    fontWeight: '600',
    color: '#007AFF',
  },
  positionsButton: {
    marginTop: 12,
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: '#007AFF',
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  positionsButtonText: {
    color: 'white',
    fontSize: 15,
    fontWeight: '600',
  },
  positionsSection: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#000',
    marginBottom: 12,
  },
  positionCard: {
    backgroundColor: 'white',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  positionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  positionSymbol: {
    fontSize: 20,
    fontWeight: '700',
    color: '#000',
  },
  positionPnl: {
    fontSize: 20,
    fontWeight: '700',
  },
  positionDetails: {
    fontSize: 15,
    color: '#8E8E93',
    marginBottom: 4,
  },
  positionPercent: {
    fontSize: 16,
    fontWeight: '600',
    color: '#8E8E93',
  },
  negative: {
    color: '#FF3B30',
  },
});

