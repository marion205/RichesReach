import React, { memo } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { getScoreColor, getBuyRecommendation } from '../../shared/utils/score';

export type WatchlistItem = {
  id: string;
  stock: {
    id: string;
    symbol: string;
    companyName: string;
    sector?: string;
    beginnerFriendlyScore?: number;
    currentPrice?: number | null;
    change?: number | null;
    changePercent?: number | null;
  };
  addedAt: string;
  notes?: string | null;
  targetPrice?: number | null;
};

export type WatchlistCardProps = {
  item: WatchlistItem;
  onRemove: (symbol: string) => void;
};

function WatchlistCard({ item, onRemove }: WatchlistCardProps) {
  const score = item.stock.beginnerFriendlyScore ?? 75; // Default score if missing
  const rec = getBuyRecommendation(score);

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View style={{ flexDirection: 'row', alignItems: 'center' }}>
          <Text style={styles.symbol}>{item.stock.symbol}</Text>
          {score != null && (
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
              <View style={[styles.scoreBadge, { backgroundColor: getScoreColor(score) }]}>
                <Text style={styles.scoreText}>{score}</Text>
              </View>
              <View style={[styles.recBadge, { backgroundColor: rec.backgroundColor, borderColor: rec.color }]}>
                <Text style={[styles.recText, { color: rec.color }]}>{rec.text}</Text>
              </View>
            </View>
          )}
        </View>
        <TouchableOpacity style={{ padding: 8 }} onPress={() => onRemove(item.stock.symbol)} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
          <Icon name="x" size={20} color="#ff4444" />
        </TouchableOpacity>
      </View>

      <Text style={styles.company}>{item.stock.companyName}</Text>
      {item.stock.sector && <Text style={styles.sector}>{item.stock.sector}</Text>}

      {/* Price Information */}
      {item.stock.currentPrice != null && (
        <View style={styles.priceContainer}>
          <Text style={styles.price}>${item.stock.currentPrice.toFixed(2)}</Text>
          {item.stock.change != null && item.stock.changePercent != null && (
            <View style={[
              styles.changeContainer,
              { backgroundColor: item.stock.change >= 0 ? '#e8f5e9' : '#ffebee' }
            ]}>
              <Icon 
                name={item.stock.change >= 0 ? "trending-up" : "trending-down"} 
                size={14} 
                color={item.stock.change >= 0 ? "#4caf50" : "#f44336"} 
              />
              <Text style={[
                styles.change,
                { color: item.stock.change >= 0 ? "#4caf50" : "#f44336" }
              ]}>
                {item.stock.change >= 0 ? '+' : ''}{item.stock.change.toFixed(2)} ({item.stock.changePercent >= 0 ? '+' : ''}{(item.stock.changePercent * 100).toFixed(2)}%)
              </Text>
            </View>
          )}
        </View>
      )}

      {item.notes ? (
        <View style={styles.notesBox}>
          <Text style={styles.notesLabel}>Notes:</Text>
          <Text style={styles.notes}>{item.notes}</Text>
        </View>
      ) : null}

      {item.targetPrice != null && (
        <View style={styles.targetPriceBox}>
          <Text style={styles.targetPriceLabel}>Target Price:</Text>
          <Text style={styles.targetPrice}>${item.targetPrice.toFixed(2)}</Text>
        </View>
      )}

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
  sector: { fontSize: 14, color: '#666', marginBottom: 8 },
  priceContainer: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: 4, marginBottom: 8 },
  price: { fontSize: 20, fontWeight: 'bold', color: '#333' },
  changeContainer: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8, gap: 4 },
  change: { fontSize: 13, fontWeight: '600' },
  notesBox: { marginTop: 12, padding: 12, backgroundColor: '#f8f9fa', borderRadius: 8 },
  notesLabel: { fontSize: 12, fontWeight: '600', color: '#666', marginBottom: 4 },
  notes: { fontSize: 14, color: '#333' },
  targetPriceBox: { marginTop: 8, padding: 10, backgroundColor: '#fff3cd', borderRadius: 8, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  targetPriceLabel: { fontSize: 12, fontWeight: '600', color: '#856404' },
  targetPrice: { fontSize: 14, fontWeight: 'bold', color: '#856404' },
  added: { fontSize: 12, color: '#999', marginTop: 12, textAlign: 'right' },
});
