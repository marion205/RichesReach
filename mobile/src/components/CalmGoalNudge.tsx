import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

interface CalmGoalNudgeProps {
  onStart: () => void;
  onDismiss?: () => void;
  title?: string;
  subtitle?: string;
}

export default function CalmGoalNudge({ onStart, onDismiss, title, subtitle }: CalmGoalNudgeProps) {
  return (
    <View style={styles.container}>
      <View style={styles.left}>
        <Icon name="heart" size={18} color="#34C759" />
        <Text style={styles.title}>{title || 'You seem anxious about spending.'}</Text>
        <Text style={styles.subtitle}>{subtitle || 'Want to set a calm investing goal?'}</Text>
      </View>
      <View style={styles.actions}>
        <TouchableOpacity style={styles.primary} onPress={onStart}>
          <Text style={styles.primaryText}>Set Goal</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.secondary} onPress={onDismiss}>
          <Icon name="x" size={16} color="#8E8E93" />
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginHorizontal: 16,
    marginTop: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E5EA',
    backgroundColor: '#F5FFF8',
    padding: 12,
    flexDirection: 'row',
    alignItems: 'center',
  },
  left: { flex: 1 },
  title: { fontSize: 14, fontWeight: '700', color: '#1C1C1E' },
  subtitle: { fontSize: 12, color: '#666', marginTop: 2 },
  actions: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  primary: {
    backgroundColor: '#34C759',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
  },
  primaryText: { color: '#fff', fontWeight: '700' },
  secondary: { padding: 8 },
});


