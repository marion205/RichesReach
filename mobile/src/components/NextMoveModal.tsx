import React from 'react';
import { View, Text, StyleSheet, Modal, TouchableOpacity, FlatList } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

interface NextMoveModalProps {
  visible: boolean;
  onClose: () => void;
  portfolioValue?: number;
}

interface Idea { symbol: string; action: 'BUY' | 'HOLD' | 'TRIM'; conviction: 'calm' | 'balanced' | 'bold'; sizePct: number; thesis: string; }

export default function NextMoveModal({ visible, onClose, portfolioValue = 10000 }: NextMoveModalProps) {
  const ideas: Idea[] = React.useMemo(() => {
    // simple simulated suggestions
    const base: Idea[] = [
      { symbol: 'VTI', action: 'BUY', conviction: 'calm', sizePct: 2, thesis: 'Broad market exposure to steady volatility.' },
      { symbol: 'AAPL', action: 'HOLD', conviction: 'balanced', sizePct: 0, thesis: 'Quality compounder; maintain position.' },
      { symbol: 'TSLA', action: 'TRIM', conviction: 'bold', sizePct: -1, thesis: 'Reduce single-name risk after recent spike.' },
    ];
    return base;
  }, []);

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View style={styles.card}>
          <View style={styles.header}>
            <Text style={styles.title}>Next Move (Simulated)</Text>
            <TouchableOpacity onPress={onClose}><Icon name="x" size={20} color="#8E8E93" /></TouchableOpacity>
          </View>
          <Text style={styles.subtitle}>Portfolio: ${portfolioValue.toLocaleString()}</Text>
          <FlatList
            data={ideas}
            keyExtractor={(i) => i.symbol}
            renderItem={({ item }) => (
              <View style={styles.row}>
                <View style={styles.left}>
                  <Text style={styles.symbol}>{item.symbol}</Text>
                  <Text style={styles.thesis}>{item.thesis}</Text>
                </View>
                <View style={styles.right}>
                  <Text style={[styles.action, item.action === 'BUY' ? styles.buy : item.action === 'TRIM' ? styles.trim : styles.hold]}>{item.action}</Text>
                  {item.sizePct !== 0 && <Text style={styles.size}>{item.sizePct > 0 ? '+' : ''}{item.sizePct}%</Text>}
                </View>
              </View>
            )}
          />
          <View style={styles.footer}>
            <Icon name="alert-triangle" size={14} color="#8E8E93" />
            <Text style={styles.disclaimer}>Educational simulation. Not investment advice.</Text>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.35)', justifyContent: 'flex-end' },
  card: { backgroundColor: '#fff', borderTopLeftRadius: 16, borderTopRightRadius: 16, padding: 16, maxHeight: '70%' },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  title: { fontSize: 16, fontWeight: '700', color: '#1C1C1E' },
  subtitle: { color: '#666', marginTop: 4, marginBottom: 8 },
  row: { flexDirection: 'row', paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: '#F0F0F0' },
  left: { flex: 1 },
  right: { alignItems: 'flex-end' },
  symbol: { fontSize: 14, fontWeight: '700', color: '#1C1C1E' },
  thesis: { fontSize: 12, color: '#666', marginTop: 2 },
  action: { fontSize: 12, fontWeight: '700' },
  buy: { color: '#22C55E' },
  hold: { color: '#8E8E93' },
  trim: { color: '#EF4444' },
  size: { fontSize: 12, color: '#1C1C1E' },
  footer: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 8 },
  disclaimer: { fontSize: 11, color: '#8E8E93' },
});


