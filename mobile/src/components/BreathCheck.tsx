import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

interface BreathCheckProps {
  onSuggest?: (suggestion: { type: 'roundup' | 'dca'; amount: number; instrument: string }) => void;
}

export default function BreathCheck({ onSuggest }: BreathCheckProps) {
  const handleCheck = () => {
    const suggestion = { type: 'dca' as const, amount: 25, instrument: 'VTI' };
    onSuggest?.(suggestion);
  };
  return (
    <View style={styles.card}>
      <View style={styles.row}>
        <View style={styles.iconWrap}><Icon name="wind" size={20} color="#10B981" /></View>
        <View style={{ flex: 1 }}>
          <Text style={styles.title}>Breath Check</Text>
          <Text style={styles.subtitle}>Take a 10s pause; align your next move</Text>
        </View>
        <TouchableOpacity onPress={handleCheck} style={styles.cta}>
          <Text style={styles.ctaText}>Begin</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: { backgroundColor: '#FFFFFF', borderRadius: 12, padding: 14, marginHorizontal: 16, marginBottom: 12, borderWidth: 1, borderColor: '#E5E5EA' },
  row: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  iconWrap: { width: 36, height: 36, borderRadius: 10, backgroundColor: '#ECFDF5', alignItems: 'center', justifyContent: 'center' },
  title: { fontSize: 16, fontWeight: '700', color: '#1C1C1E' },
  subtitle: { fontSize: 12, color: '#6B7280', marginTop: 2 },
  cta: { backgroundColor: '#10B981', paddingHorizontal: 12, paddingVertical: 8, borderRadius: 8 },
  ctaText: { color: '#fff', fontWeight: '700', fontSize: 12 },
});


