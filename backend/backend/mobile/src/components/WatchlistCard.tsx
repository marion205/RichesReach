import React, { memo } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { getScoreColor, getBuyRecommendation } from '../utils/score';

export type WatchlistItem = {
  id: string;
  stock: {
    id: string;
    symbol: string;
    companyName: string;
    sector: string;
    beginnerFriendlyScore: number;
    currentPrice?: number | null;
  };
  addedAt: string;
  notes?: string | null;
};

export type WatchlistCardProps = {
  item: WatchlistItem;
  onRemove: (symbol: string) => void;
};

function WatchlistCard({ item, onRemove }: WatchlistCardProps) {
  const rec = getBuyRecommendation(item.stock.beginnerFriendlyScore);

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View style={{ flexDirection: 'row', alignItems: 'center' }}>
          <Text style={styles.symbol}>{item.stock.symbol}</Text>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
            <View style={[styles.scoreBadge, { backgroundColor: getScoreColor(item.stock.beginnerFriendlyScore) }]}>
              <Text style={styles.scoreText}>{item.stock.beginnerFriendlyScore}</Text>
            </View>
            <View style={[styles.recBadge, { backgroundColor: rec.backgroundColor, borderColor: rec.color }]}>
              <Text style={[styles.recText, { color: rec.color }]}>{rec.text}</Text>
            </View>
          </View>
        </View>
        <TouchableOpacity style={{ padding: 8 }} onPress={() => onRemove(item.stock.symbol)} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
          <Icon name="x" size={20} color="#ff4444" />
        </TouchableOpacity>
      </View>

      <Text style={styles.company}>{item.stock.companyName}</Text>
      <Text style={styles.sector}>{item.stock.sector}</Text>

      {item.notes ? (
        <View style={styles.notesBox}>
          <Text style={styles.notesLabel}>Notes:</Text>
          <Text style={styles.notes}>{item.notes}</Text>
        </View>
      ) : null}

      <Text style={styles.added}>Added: {new Date(item.addedAt).toLocaleDateString()}</Text>
    </View>
  );
}

export default memo(WatchlistCard);

const styles = StyleSheet.create({
  card: { backgroundColor: '#fff', borderRadius: 16, padding: 20, marginBottom: 16, shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 8, elevation: 3 },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 },
  symbol: { fontSize: 24, fontWeight: 'bold', color: '#333', marginRight: 12 },
  scoreBadge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 12, minWidth: 32, alignItems: 'center' },
  scoreText: { fontSize: 12, fontWeight: 'bold', color: '#fff' },
  recBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12, borderWidth: 1, minWidth: 60, alignItems: 'center' },
  recText: { fontSize: 10, fontWeight: 'bold' },
  company: { fontSize: 16, fontWeight: '600', color: '#333', marginBottom: 4 },
  sector: { fontSize: 14, color: '#666' },
  notesBox: { marginTop: 12, padding: 12, backgroundColor: '#f8f9fa', borderRadius: 8 },
  notesLabel: { fontSize: 12, fontWeight: '600', color: '#666', marginBottom: 4 },
  notes: { fontSize: 14, color: '#333' },
  added: { fontSize: 12, color: '#999', marginTop: 12, textAlign: 'right' },
});
