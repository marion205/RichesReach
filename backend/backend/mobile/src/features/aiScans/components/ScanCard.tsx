/**
 * Scan Card Component — Hedge-Fund Edition
 * Optimized for high-frequency AI scan dashboards
 */

import React, { useState, useCallback, memo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { AIScan } from '../types/AIScansTypes';
import { LineChart } from 'react-native-chart-kit';
import { Dimensions } from 'react-native';

const { width } = Dimensions.get('window');

interface ScanCardProps {
  scan: AIScan;
  onPress: () => void;
  onRun: () => Promise<void> | void;
}

const fmtMoney = (n?: number) => Number.isFinite(n as number) ? `$${Number(n).toFixed(2)}` : '—';
const fmtPct = (n?: number) => Number.isFinite(n as number) ? `${Number(n).toFixed(2)}%` : '—';

const ScanCard: React.FC<ScanCardProps> = React.memo(({ scan, onPress, onRun }) => {
  const [running, setRunning] = useState(false);

  const handleRunPress = useCallback(async () => {
    try {
      setRunning(true);
      await onRun();
    } finally {
      setRunning(false);
    }
  }, [onRun]);

  const getCategoryColor = (category: string) => {
    const map: Record<string, string> = {
      momentum: '#00cc99',
      value: '#007AFF',
      growth: '#FF9500',
      dividend: '#8B5CF6',
      volatility: '#FF3B30',
    };
    return map[category] || '#8E8E93';
  };

  const getRiskColor = (risk: string) => {
    const map: Record<string, string> = {
      low: '#00cc99',
      medium: '#FF9500',
      high: '#FF3B30',
    };
    return map[risk] || '#8E8E93';
  };

  const formatLastRun = (lastRun?: string | Date) => {
    if (!lastRun) return 'Never run';
    const diff = Date.now() - new Date(lastRun).getTime();
    const hours = Math.floor(diff / 36e5);
    const days = Math.floor(hours / 24);
    return days > 0 ? `${days}d ago` : hours > 0 ? `${hours}h ago` : 'Just now';
  };

  const sparkData = scan.results?.slice(0, 5).map((r) => r.score) || [];

  return (
    <TouchableOpacity style={styles.container} activeOpacity={0.9} onPress={onPress}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.name} numberOfLines={1} allowFontScaling={false}>
          {scan.name}
        </Text>
        <View style={[styles.badge, { backgroundColor: getCategoryColor(scan.category) }]}>
          <Text style={styles.badgeText}>{scan.category}</Text>
        </View>
      </View>

      {/* Description */}
      <Text style={styles.description} numberOfLines={2}>
        {scan.description}
      </Text>

      {/* Sparkline (if available) */}
      {sparkData.length >= 3 && (
        <LineChart
          data={{
            labels: Array(sparkData.length).fill(''),
            datasets: [{ data: sparkData }],
          }}
          width={width * 0.75}
          height={60}
          withDots={false}
          withInnerLines={false}
          withVerticalLabels={false}
          chartConfig={{
            backgroundColor: '#fff',
            color: () => '#00cc99',
          }}
          style={styles.sparkline}
        />
      )}

      {/* Metrics */}
      <View style={styles.metrics}>
        <View>
          <Text style={styles.label}>Risk</Text>
          <View style={[styles.riskBadge, { backgroundColor: getRiskColor(scan.riskLevel) }]}>
            <Text style={styles.riskText}>{scan.riskLevel}</Text>
          </View>
        </View>
        <View>
          <Text style={styles.label}>Time Horizon</Text>
          <Text style={styles.value}>{scan.timeHorizon}</Text>
        </View>
        <View>
          <Text style={styles.label}>Last Run</Text>
          <Text style={styles.value}>{formatLastRun(scan.lastRun)}</Text>
        </View>
      </View>

      {/* Actions */}
      <View style={styles.actions}>
        <TouchableOpacity
          style={[styles.runButton, running && styles.runButtonDisabled]}
          disabled={running}
          onPress={handleRunPress}
        >
          {running ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <>
              <Icon name="play" size={16} color="#fff" />
              <Text style={styles.runButtonText}>Run</Text>
            </>
          )}
        </TouchableOpacity>

        <TouchableOpacity style={styles.viewButton} onPress={onPress}>
          <Icon name="eye" size={16} color="#00cc99" />
          <Text style={styles.viewButtonText}>Details</Text>
        </TouchableOpacity>
      </View>
    </TouchableOpacity>
  );
});

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderColor: '#E5E5EA',
    borderWidth: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  name: { fontSize: 18, fontWeight: '600', color: '#000', flexShrink: 1 },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
  },
  badgeText: { color: '#fff', fontSize: 11, fontWeight: '600' },
  description: { color: '#666', marginBottom: 8, fontSize: 13 },
  metrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 6,
    marginBottom: 10,
  },
  label: { fontSize: 12, color: '#8E8E93' },
  value: { fontSize: 14, color: '#000', fontWeight: '500' },
  riskBadge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 8, marginTop: 2 },
  riskText: { color: '#fff', fontSize: 11, fontWeight: '600' },
  sparkline: { marginTop: 4, marginBottom: 6 },
  actions: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 8 },
  runButton: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#00cc99',
    paddingVertical: 10,
    borderRadius: 8,
    marginRight: 6,
  },
  runButtonDisabled: { backgroundColor: '#8E8E93' },
  runButtonText: { color: '#fff', marginLeft: 6, fontWeight: '600' },
  viewButton: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F2F2F7',
    paddingVertical: 10,
    borderRadius: 8,
    marginLeft: 6,
  },
  viewButtonText: { color: '#00cc99', marginLeft: 6, fontWeight: '600' },
});

export default memo(ScanCard);