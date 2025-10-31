import React, { useState } from 'react';
import { View, Text, StyleSheet, Modal, TouchableOpacity, TextInput } from 'react-native';

type Cadence = 'weekly' | 'biweekly' | 'monthly';

export default function CalmGoalSheet({ visible, onClose, onConfirm }: {
  visible: boolean;
  onClose: () => void;
  onConfirm: (plan: { amountUsd: number; cadence: Cadence }) => void;
}) {
  const [amount, setAmount] = useState('25');
  const [cadence, setCadence] = useState<Cadence>('weekly');

  return (
    <Modal visible={visible} animationType="slide" transparent>
      <View style={styles.scrim}>
        <View style={styles.sheet}>
          <View style={styles.header}>
            <Text style={styles.title}>Set a calm investing goal</Text>
            <TouchableOpacity onPress={onClose}>
              <Text style={styles.close}>✕</Text>
            </TouchableOpacity>
          </View>

          <Text style={styles.label}>Amount (USD)</Text>
          <TextInput
            value={amount}
            onChangeText={setAmount}
            keyboardType="numeric"
            style={styles.input}
            placeholder="$25"
          />

          <Text style={styles.label}>Cadence</Text>
          <View style={styles.row}>
            {(['weekly','biweekly','monthly'] as Cadence[]).map(c => (
              <TouchableOpacity key={c}
                style={[styles.pill, cadence===c && styles.pillActive]}
                onPress={() => setCadence(c)}>
                <Text style={[styles.pillText, cadence===c && styles.pillTextActive]}>
                  {c === 'weekly' ? 'Weekly' : c === 'biweekly' ? 'Biweekly' : 'Monthly'}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <TouchableOpacity
            style={styles.primary}
            onPress={() => onConfirm({ amountUsd: Math.max(5, parseInt(amount || '0', 10) || 25), cadence })}
          >
            <Text style={styles.primaryText}>Start Plan</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  scrim: { flex: 1, backgroundColor: 'rgba(0,0,0,0.4)', justifyContent: 'flex-end' },
  sheet: { backgroundColor: '#fff', borderTopLeftRadius: 16, borderTopRightRadius: 16, padding: 16 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  title: { fontSize: 18, fontWeight: '700', color: '#1C1C1E' },
  close: { fontSize: 18, color: '#8E8E93' },
  label: { marginTop: 8, marginBottom: 6, fontWeight: '600', color: '#1C1C1E' },
  input: { borderWidth: 1, borderColor: '#E5E5EA', borderRadius: 8, paddingHorizontal: 12, paddingVertical: 10 },
  row: { flexDirection: 'row', gap: 8 },
  pill: { paddingVertical: 8, paddingHorizontal: 12, borderRadius: 16, borderWidth: 1, borderColor: '#E5E5EA' },
  pillActive: { backgroundColor: '#E9FFF2', borderColor: '#34C759' },
  pillText: { color: '#1C1C1E' },
  pillTextActive: { color: '#34C759', fontWeight: '700' },
  primary: { marginTop: 16, backgroundColor: '#34C759', borderRadius: 10, paddingVertical: 12, alignItems: 'center' },
  primaryText: { color: '#fff', fontWeight: '700' },
});


