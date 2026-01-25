import React from 'react';
import { View, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

interface AuraHaloProps {
  score: number; // -1 (alert) .. 0 (neutral) .. 1 (calm)
  children: React.ReactNode;
}

// Simple visual halo that changes color by score
export default function AuraHalo({ score, children }: AuraHaloProps) {
  const clamped = Math.max(-1, Math.min(1, score));

  // Interpolate colors: alert -> focused -> calm
  const colors = clamped < -0.33
    ? ['#FFEEEE', '#FFD6D6'] // alert
    : clamped < 0.33
      ? ['#FFF7E3', '#FFE9B3'] // focused
      : ['#E9FFF2', '#D6FFEA']; // calm

  const borderColor = clamped < -0.33 ? '#FF3B30' : clamped < 0.33 ? '#FF9500' : '#34C759';

  return (
    <LinearGradient 
      colors={colors as [string, string]} 
      style={[styles.halo, { borderColor }]}
      start={{ x: 0, y: 0 }} 
      end={{ x: 1, y: 1 }}
    >
      <View style={styles.inner}>{children}</View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  halo: {
    padding: 8,
    borderRadius: 18,
    borderWidth: 1,
  },
  inner: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
  },
});


