/**
 * Playbook Card Component — Hedge-Fund Edition
 * Optimized for institutional-grade playbook browsing
 */

import React, { useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { Playbook } from '../types/AIScansTypes';

interface PlaybookCardProps {
  playbook: Playbook;
  onPress: () => void;
}

const PlaybookCard: React.FC<PlaybookCardProps> = React.memo(({ playbook, onPress }) => {
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

  const formatPerformance = (performance: any) => {
    if (!performance) return 'N/A';
    return `${(performance.successRate * 100).toFixed(0)}% success`;
  };

  return (
    <TouchableOpacity style={styles.container} activeOpacity={0.9} onPress={onPress}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.name} numberOfLines={1} allowFontScaling={false}>
          {playbook.name}
        </Text>
        <View style={[styles.badge, { backgroundColor: getCategoryColor(playbook.category) }]}>
          <Text style={styles.badgeText}>{playbook.category}</Text>
        </View>
      </View>

      {/* Description */}
      <Text style={styles.description} numberOfLines={2}>
        {playbook.description}
      </Text>

      {/* Author */}
      <View style={styles.authorRow}>
        <Icon name="user" size={14} color="#8E8E93" />
        <Text style={styles.authorText}>{playbook.author}</Text>
      </View>

      {/* Metrics */}
      <View style={styles.metrics}>
        <View>
          <Text style={styles.label}>Risk</Text>
          <View style={[styles.riskBadge, { backgroundColor: getRiskColor(playbook.riskLevel) }]}>
            <Text style={styles.riskText}>{playbook.riskLevel}</Text>
          </View>
        </View>
        <View>
          <Text style={styles.label}>Performance</Text>
          <Text style={styles.value}>{formatPerformance(playbook.performance)}</Text>
        </View>
        <View>
          <Text style={styles.label}>Runs</Text>
          <Text style={styles.value}>{playbook.performance?.totalRuns || 0}</Text>
        </View>
      </View>

      {/* Tags */}
      {playbook.tags && playbook.tags.length > 0 && (
        <View style={styles.tagsContainer}>
          {playbook.tags.slice(0, 3).map((tag, index) => (
            <View key={index} style={styles.tag}>
              <Text style={styles.tagText}>{tag}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Action */}
      <View style={styles.actionContainer}>
        <TouchableOpacity style={styles.cloneButton} onPress={onPress}>
          <Icon name="copy" size={16} color="#00cc99" />
          <Text style={styles.cloneButtonText}>Clone Playbook</Text>
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
  authorRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  authorText: { 
    fontSize: 12, 
    color: '#8E8E93', 
    marginLeft: 4 
  },
  metrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  label: { fontSize: 12, color: '#8E8E93' },
  value: { fontSize: 14, color: '#000', fontWeight: '500' },
  riskBadge: { 
    paddingHorizontal: 8, 
    paddingVertical: 2, 
    borderRadius: 8, 
    marginTop: 2 
  },
  riskText: { color: '#fff', fontSize: 11, fontWeight: '600' },
  tagsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 12,
  },
  tag: {
    backgroundColor: '#F2F2F7',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    marginRight: 6,
    marginBottom: 4,
  },
  tagText: {
    fontSize: 11,
    color: '#8E8E93',
    fontWeight: '500',
  },
  actionContainer: {
    alignItems: 'center',
  },
  cloneButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F2F2F7',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
  },
  cloneButtonText: { 
    color: '#00cc99', 
    marginLeft: 6, 
    fontWeight: '600',
    fontSize: 14,
  },
});

export default PlaybookCard;