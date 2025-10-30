import React from 'react';
import { View, Text, Pressable, StyleSheet, Modal } from 'react-native';
import { useNavigation } from '@react-navigation/native';

export default function InvestAdvancedSheet() {
  const navigation = useNavigation<any>();

  return (
    <View style={styles.overlay}>
      <View style={styles.sheet}>
        <Text style={styles.title}>Advanced</Text>
        <Text style={styles.subtitle}>Options, Greeks, Screeners</Text>

        <Pressable style={styles.row} onPress={() => navigation.navigate('AIOptions')}>
          <Text style={styles.rowText}>Options (AI)</Text>
        </Pressable>
        <Pressable style={styles.row} onPress={() => navigation.navigate('OptionsCopilot')}>
          <Text style={styles.rowText}>Options Copilot</Text>
        </Pressable>
        <Pressable style={styles.row} onPress={() => navigation.navigate('Screeners')}>
          <Text style={styles.rowText}>Screeners</Text>
        </Pressable>

        <Pressable style={[styles.row, styles.close]} onPress={() => navigation.goBack()}>
          <Text style={styles.rowText}>Close</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.35)',
    justifyContent: 'flex-end',
  },
  sheet: {
    backgroundColor: 'white',
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    padding: 16,
  },
  title: { fontSize: 20, fontWeight: '700' },
  subtitle: { opacity: 0.6, marginBottom: 12 },
  row: {
    paddingVertical: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: '#E5E5EA',
  },
  rowText: { fontSize: 16 },
  close: { borderBottomWidth: 0, marginTop: 4 },
});


