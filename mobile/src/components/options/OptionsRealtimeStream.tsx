import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

interface OptionsRealtimeStreamProps {
  symbol: string;
  contractSymbol?: string;
}

interface StreamData {
  bid: number;
  ask: number;
  last: number;
  volume: number;
  delta: number;
  gamma: number;
  theta: number;
  vega: number;
  impliedVolatility: number;
  timestamp: string;
}

export default function OptionsRealtimeStream({ symbol, contractSymbol }: OptionsRealtimeStreamProps) {
  const [streamData, setStreamData] = useState<StreamData | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!symbol) return;

    // In production, this would connect to a WebSocket server
    // For now, simulate real-time updates with polling
    const connectWebSocket = () => {
      // Simulate WebSocket connection
      setIsConnected(true);
      
      // Simulate real-time updates every 2 seconds
      const updateInterval = setInterval(() => {
        // Generate mock real-time data
        const mockData: StreamData = {
          bid: 2.40 + Math.random() * 0.1,
          ask: 2.50 + Math.random() * 0.1,
          last: 2.45 + Math.random() * 0.1,
          volume: Math.floor(1000 + Math.random() * 500),
          delta: 0.5 + (Math.random() - 0.5) * 0.1,
          gamma: 0.02 + (Math.random() - 0.5) * 0.01,
          theta: -0.05 + (Math.random() - 0.5) * 0.02,
          vega: 0.1 + (Math.random() - 0.5) * 0.05,
          impliedVolatility: 0.25 + (Math.random() - 0.5) * 0.05,
          timestamp: new Date().toISOString(),
        };
        
        setStreamData(mockData);
        setLastUpdate(new Date());
      }, 2000);

      return () => {
        clearInterval(updateInterval);
        setIsConnected(false);
      };
    };

    const cleanup = connectWebSocket();
    
    return () => {
      if (cleanup) cleanup();
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [symbol, contractSymbol]);

  if (!streamData) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Icon name="radio" size={18} color="#007AFF" />
          <Text style={styles.title}>Real-Time Options Data</Text>
          <View style={[styles.statusIndicator, !isConnected && styles.statusIndicatorOffline]}>
            <View style={[styles.statusDot, !isConnected && styles.statusDotOffline]} />
            <Text style={styles.statusText}>{isConnected ? 'Live' : 'Connecting...'}</Text>
          </View>
        </View>
        <View style={styles.loadingState}>
          <Text style={styles.loadingText}>Connecting to real-time feed...</Text>
        </View>
      </View>
    );
  }

  const spread = streamData.ask - streamData.bid;
  const midPrice = (streamData.bid + streamData.ask) / 2;
  const spreadPercent = (spread / midPrice) * 100;

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Icon name="radio" size={18} color="#007AFF" />
        <Text style={styles.title}>Real-Time Options Data</Text>
        <View style={[styles.statusIndicator, isConnected && styles.statusIndicatorLive]}>
          <View style={[styles.statusDot, isConnected && styles.statusDotLive]} />
          <Text style={styles.statusText}>{isConnected ? 'LIVE' : 'OFFLINE'}</Text>
        </View>
      </View>

      {lastUpdate && (
        <Text style={styles.lastUpdate}>
          Last update: {lastUpdate.toLocaleTimeString()}
        </Text>
      )}

      {/* Price Data */}
      <View style={styles.priceSection}>
        <View style={styles.priceRow}>
          <View style={styles.priceItem}>
            <Text style={styles.priceLabel}>Bid</Text>
            <Text style={[styles.priceValue, styles.bidPrice]}>
              ${streamData.bid.toFixed(2)}
            </Text>
          </View>
          <View style={styles.priceItem}>
            <Text style={styles.priceLabel}>Ask</Text>
            <Text style={[styles.priceValue, styles.askPrice]}>
              ${streamData.ask.toFixed(2)}
            </Text>
          </View>
          <View style={styles.priceItem}>
            <Text style={styles.priceLabel}>Last</Text>
            <Text style={styles.priceValue}>
              ${streamData.last.toFixed(2)}
            </Text>
          </View>
        </View>
        <View style={styles.spreadRow}>
          <Text style={styles.spreadLabel}>Spread:</Text>
          <Text style={styles.spreadValue}>
            ${spread.toFixed(2)} ({spreadPercent.toFixed(2)}%)
          </Text>
        </View>
      </View>

      {/* Greeks - Real-Time */}
      <View style={styles.greeksSection}>
        <Text style={styles.sectionTitle}>Live Greeks</Text>
        <View style={styles.greeksGrid}>
          <View style={styles.greekCard}>
            <Text style={styles.greekLabel}>Delta</Text>
            <Text style={[styles.greekValue, streamData.delta > 0 ? styles.positive : styles.negative]}>
              {streamData.delta > 0 ? '+' : ''}{streamData.delta.toFixed(3)}
            </Text>
          </View>
          <View style={styles.greekCard}>
            <Text style={styles.greekLabel}>Gamma</Text>
            <Text style={styles.greekValue}>{streamData.gamma.toFixed(3)}</Text>
          </View>
          <View style={styles.greekCard}>
            <Text style={styles.greekLabel}>Theta</Text>
            <Text style={[styles.greekValue, styles.negative]}>
              {streamData.theta.toFixed(3)}
            </Text>
          </View>
          <View style={styles.greekCard}>
            <Text style={styles.greekLabel}>Vega</Text>
            <Text style={styles.greekValue}>{streamData.vega.toFixed(3)}</Text>
          </View>
        </View>
      </View>

      {/* Volume & IV */}
      <View style={styles.metricsRow}>
        <View style={styles.metric}>
          <Text style={styles.metricLabel}>Volume</Text>
          <Text style={styles.metricValue}>{streamData.volume.toLocaleString()}</Text>
        </View>
        <View style={styles.metric}>
          <Text style={styles.metricLabel}>Implied Volatility</Text>
          <Text style={styles.metricValue}>
            {(streamData.impliedVolatility * 100).toFixed(1)}%
          </Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  title: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
    marginLeft: 8,
    flex: 1,
  },
  statusIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    backgroundColor: '#D1FAE5',
  },
  statusIndicatorLive: {
    backgroundColor: '#D1FAE5',
  },
  statusIndicatorOffline: {
    backgroundColor: '#FEE2E2',
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#059669',
  },
  statusDotLive: {
    backgroundColor: '#059669',
  },
  statusDotOffline: {
    backgroundColor: '#DC2626',
  },
  statusText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#059669',
  },
  lastUpdate: {
    fontSize: 11,
    color: '#9CA3AF',
    marginBottom: 12,
    textAlign: 'right',
  },
  loadingState: {
    paddingVertical: 40,
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 14,
    color: '#6B7280',
  },
  priceSection: {
    marginBottom: 16,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  priceRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 12,
  },
  priceItem: {
    alignItems: 'center',
  },
  priceLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  priceValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
  },
  bidPrice: {
    color: '#059669',
  },
  askPrice: {
    color: '#DC2626',
  },
  spreadRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  spreadLabel: {
    fontSize: 12,
    color: '#6B7280',
  },
  spreadValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
  },
  greeksSection: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 12,
  },
  greeksGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  greekCard: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    alignItems: 'center',
  },
  greekLabel: {
    fontSize: 11,
    color: '#6B7280',
    marginBottom: 6,
    fontWeight: '600',
  },
  greekValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
  },
  positive: {
    color: '#059669',
  },
  negative: {
    color: '#DC2626',
  },
  metricsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
  },
  metric: {
    alignItems: 'center',
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
});

