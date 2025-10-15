import React, { useMemo } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useQuery } from '@apollo/client';
import { MINI_QUOTES } from '../../../tickerFollows';
import TickerFollowButton from './TickerFollowButton';

const C = { primary: '#00cc99', red: '#EF4444', green: '#10B981', text: '#111827', chip: '#F3F4F6', border: '#E5E7EB' };

export default function TickerChips({ symbols, onPressSymbol }: { symbols: string[]; onPressSymbol?: (s: string) => void }) {
  const uniq = useMemo(() => Array.from(new Set((symbols || []).filter(Boolean).map((s) => s.toUpperCase()))), [symbols]);
  const { data } = useQuery(MINI_QUOTES, { variables: { symbols: uniq }, skip: !uniq.length, fetchPolicy: 'cache-first' });

  const quoteMap = useMemo(() => {
    const m: Record<string, { last?: number; changePct?: number }> = {};
    (data?.quotes || []).forEach((q: any) => (m[q.symbol] = q));
    return m;
  }, [data]);

  return (
    <View style={s.row}>
      {uniq.map((sym) => {
        const q = quoteMap[sym];
        const chg = q?.changePct ?? 0;
        const pos = chg >= 0;
        return (
          <View key={sym} style={s.chip}>
            <TouchableOpacity onPress={() => onPressSymbol?.(sym)} style={{ flexDirection: 'row', alignItems: 'center' }}>
              <Text style={s.sym}>${sym}</Text>
              {q?.last != null && <Text style={s.px}>{q.last.toFixed(2)}</Text>}
              <Text style={[s.chg, { color: pos ? C.green : C.red }]}>{(pos ? '+' : '') + chg.toFixed(2)}%</Text>
            </TouchableOpacity>
            <TickerFollowButton symbol={sym} />
          </View>
        );
      })}
    </View>
  );
}

const s = StyleSheet.create({
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingHorizontal: 10,
    paddingVertical: 8,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 12,
  },
  sym: { fontWeight: '800', color: C.primary, marginRight: 6 },
  px: { color: C.text, fontWeight: '600', marginRight: 6 },
  chg: { fontWeight: '700' },
});
