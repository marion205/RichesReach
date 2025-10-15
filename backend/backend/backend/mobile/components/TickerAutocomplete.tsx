import React, { useMemo, useRef, useState } from 'react';
import { View, TextInput, FlatList, TouchableOpacity, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { gql, useLazyQuery } from '@apollo/client';

const COLORS = {
  card: '#FFFFFF',
  border: '#E2E8F0',
  text: '#1F2937',
  subtext: '#6B7280',
  primary: '#00cc99',
  muted: '#F3F4F6',
};

export const SEARCH_TICKERS = gql`
  query SearchTickers($q: String!, $limit: Int = 10) {
    searchTickers(q: $q, limit: $limit) {
      symbol
      companyName
      lastPrice
      changePct
    }
  }
`;

type Row = {
  symbol: string;
  companyName?: string | null;
  lastPrice?: number | null;
  changePct?: number | null;
};

type Props = {
  value: string;
  onChangeText: (v: string) => void;
  onSelect: (row: Row) => void;
  placeholder?: string;
  autoFocus?: boolean;
};

export default function TickerAutocomplete({
  value,
  onChangeText,
  onSelect,
  placeholder,
  autoFocus,
}: Props) {
  const [run, { data, loading }] = useLazyQuery(SEARCH_TICKERS, { fetchPolicy: 'cache-first' });
  const [q, setQ] = useState(value);
  const t = useRef<ReturnType<typeof setTimeout> | null>(null);

  const results: Row[] = useMemo(() => data?.searchTickers ?? [], [data]);

  const handleChange = (txt: string) => {
    setQ(txt);
    onChangeText(txt);
    if (t.current) clearTimeout(t.current);
    if (txt.trim().length < 1) return;
    t.current = setTimeout(() => run({ variables: { q: txt.trim(), limit: 10 } }), 180);
  };

  return (
    <View style={s.wrap}>
      <TextInput
        style={s.input}
        value={q}
        onChangeText={handleChange}
        placeholder={placeholder || 'Type a ticker e.g. AAPL'}
        autoCapitalize="characters"
        autoFocus={autoFocus}
      />
      {loading && (
        <View style={s.loading}>
          <ActivityIndicator size="small" color={COLORS.primary} />
        </View>
      )}
      {results.length > 0 && (
        <FlatList
          keyboardShouldPersistTaps="handled"
          data={results}
          keyExtractor={(it) => it.symbol}
          style={s.list}
          renderItem={({ item }) => {
            const green = (item.changePct ?? 0) >= 0;
            return (
              <TouchableOpacity style={s.row} onPress={() => onSelect(item)}>
                <Text style={s.sym}>${item.symbol}</Text>
                <Text style={s.name} numberOfLines={1}>
                  {item.companyName || ''}
                </Text>
                <View style={{ flex: 1 }} />
                {item.lastPrice != null && (
                  <Text style={s.px}>{item.lastPrice.toFixed(2)}</Text>
                )}
                {item.changePct != null && (
                  <Text style={[s.chg, { color: green ? '#10B981' : '#EF4444' }]}>
                    {(green ? '+' : '') + item.changePct.toFixed(2)}%
                  </Text>
                )}
              </TouchableOpacity>
            );
          }}
        />
      )}
    </View>
  );
}

const s = StyleSheet.create({
  wrap: { position: 'relative' },
  input: {
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: COLORS.card,
    fontSize: 16,
  },
  loading: { position: 'absolute', right: 10, top: 10 },
  list: {
    marginTop: 8,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 10,
    backgroundColor: COLORS.card,
    maxHeight: 240,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.muted,
  },
  sym: { fontWeight: '700', color: COLORS.primary, marginRight: 8 },
  name: { color: COLORS.subtext, flexShrink: 1, maxWidth: '55%' },
  px: { color: COLORS.text, fontWeight: '600', marginLeft: 8 },
  chg: { marginLeft: 8, fontWeight: '700' },
});
