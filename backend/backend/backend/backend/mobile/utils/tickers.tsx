import React from 'react';
import { Text, View, Pressable, StyleSheet } from 'react-native';

const COLORS = {
  chip: '#ECFDF5',
  chipSym: '#00cc99',
  chipPx: '#111827',
  chgUp: '#10B981',
  chgDown: '#EF4444',
};

export function renderWithTickers(
  text: string,
  onPressTicker: (sym: string) => void,
  quotes?: Record<string, { price: number; chg: number }>
) {
  const parts = text.split(/(\$[A-Z]{1,5}\b)/g); // keeps delimiters
  return parts.map((p, i) => {
    const m = /^\$([A-Z]{1,5})$/.exec(p);
    if (!m) return <Text key={i} style={styles.regularText}>{p}</Text>;
    const sym = m[1];
    const q = quotes?.[sym];
    return (
      <Pressable key={i} onPress={() => onPressTicker(sym)} style={styles.chip}>
        <Text style={styles.chipSym}>${sym}</Text>
        {q ? (
          <View style={styles.chipQuote}>
            <Text style={styles.chipPx}>{q.price.toFixed(2)}</Text>
            <Text style={[styles.chg, { color: q.chg >= 0 ? COLORS.chgUp : COLORS.chgDown }]}>
              {(q.chg >= 0 ? '+' : '') + q.chg.toFixed(2)}%
            </Text>
          </View>
        ) : null}
      </Pressable>
    );
  });
}

const styles = StyleSheet.create({
  chip: {
    backgroundColor: COLORS.chip,
    borderRadius: 999,
    paddingHorizontal: 8,
    paddingVertical: 3,
    marginHorizontal: 2,
    flexDirection: 'row',
    alignItems: 'center',
  },
  chipSym: { color: COLORS.chipSym, fontWeight: '700' },
  chipQuote: { flexDirection: 'row', gap: 6, marginLeft: 6 },
  chipPx: { color: COLORS.chipPx, fontWeight: '600' },
  chg: { fontWeight: '700' },
  regularText: {
    color: '#111827',
    lineHeight: 20,
    flexWrap: 'wrap',
  },
});
