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
import { useQuery } from '@apollo/client';
import { gql } from '@apollo/client';

import FuturesService from '../services/FuturesService';
import { FuturesRecommendation } from '../types/FuturesTypes';

const GET_FUTURES_RECOMMENDATIONS = gql`
  query GetFuturesRecommendations($user_id: ID) {
    futuresRecommendations(user_id: $user_id) {
      symbol
      name
      why_now
      max_loss
      max_gain
      probability
      action
    }
  }
`;

export default function TomorrowScreen({ navigation }: any) {
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [recommendations, setRecommendations] = useState<FuturesRecommendation[]>([]);

  const { data, refetch } = useQuery(GET_FUTURES_RECOMMENDATIONS, {
    fetchPolicy: 'cache-and-network',
    onCompleted: (data) => {
      if (data?.futuresRecommendations) {
        setRecommendations(data.futuresRecommendations);
      }
    },
  });

  const loadRecommendations = useCallback(async () => {
    try {
      setLoading(true);
      const resp = await FuturesService.getRecommendations();
      setRecommendations(resp.recommendations);
    } catch (e) {
      Alert.alert('Error', 'Failed to load recommendations');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    await refetch();
    await loadRecommendations();
    setRefreshing(false);
  }, [refetch, loadRecommendations]);

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
              await FuturesService.placeOrder({
                symbol: rec.symbol,
                side: rec.action === 'Buy' ? 'BUY' : 'SELL',
                quantity: 1, // Start with 1 micro contract
              });
              Alert.alert('Success', 'Order placed');
              handleRefresh();
            } catch (e) {
              Alert.alert('Error', 'Failed to place order');
            }
          },
        },
      ]
    );
  }, [handleRefresh]);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Tomorrow</Text>
        <Text style={styles.headerSubtitle}>Trade tomorrow's markets today</Text>
      </View>

      <ScrollView
        style={styles.content}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />}
      >
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
});

