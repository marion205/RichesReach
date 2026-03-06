/**
 * DemoBanner — thin persistent banner shown at the very top of the app
 * whenever EXPO_PUBLIC_DEMO_MODE=true.
 *
 * Reminds the presenter (and any investor watching) that they're looking
 * at demo data, not a live account.
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useDemo } from '../contexts/DemoContext';

export default function DemoBanner() {
  const { isDemoMode } = useDemo();
  if (!isDemoMode) return null;

  return (
    <View style={styles.banner}>
      <Text style={styles.text}>🎭  DEMO MODE — sample data only</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  banner: {
    backgroundColor: '#6366F1',
    paddingVertical: 4,
    alignItems: 'center',
    justifyContent: 'center',
    width: '100%',
  },
  text: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.4,
  },
});
