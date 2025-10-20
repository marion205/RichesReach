import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, ActivityIndicator } from 'react-native';
import { tutorMarketCommentary, DynamicContentResponse } from '../../../services/aiClient';

const HORIZONS = ['daily','weekly','monthly'] as const;
const TONES = ['neutral','bullish','bearish','educational'] as const;

export default function MarketCommentaryScreen() {
  const [userId] = useState('demo-user');
  const [horizon, setHorizon] = useState<typeof HORIZONS[number]>('daily');
  const [tone, setTone] = useState<typeof TONES[number]>('neutral');
  const [data, setData] = useState<DynamicContentResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const load = async () => {
    setLoading(true); setErr(null);
    try {
      const res = await tutorMarketCommentary({ user_id: userId, horizon, tone });
      setData(res);
    } catch (e: any) {
      setErr(e?.message || 'Request failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>{data?.headline || 'Market Commentary'}</Text>
      <View style={styles.row}>
        {HORIZONS.map((h) => (
          <TouchableOpacity key={h} onPress={() => setHorizon(h)} style={[styles.chip, horizon===h && styles.chipActive]}>
            <Text style={styles.chipText}>{h}</Text>
          </TouchableOpacity>
        ))}
      </View>
      <View style={[styles.row,{marginTop:8}]}>
        {TONES.map((t) => (
          <TouchableOpacity key={t} onPress={() => setTone(t)} style={[styles.chip, tone===t && styles.chipActive]}>
            <Text style={styles.chipText}>{t}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <TouchableOpacity onPress={load} style={styles.button} disabled={loading}>
        {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Refresh</Text>}
      </TouchableOpacity>
      {err ? <Text style={styles.err}>{err}</Text> : null}

      {data?.summary ? <Text style={styles.summary}>{data.summary}</Text> : null}

      {!!(data?.drivers || []).length && (
        <View style={styles.card}><Text style={styles.cardTitle}>Drivers</Text>{data.drivers.map((d: string, i: number) => <Text key={i} style={styles.li}>• {d}</Text>)}</View>
      )}
      {!!(data?.sectors || []).length && (
        <View style={styles.card}><Text style={styles.cardTitle}>Sectors</Text>{data.sectors.map((d: string, i: number) => <Text key={i} style={styles.li}>• {d}</Text>)}</View>
      )}
      {!!(data?.risks || []).length && (
        <View style={styles.card}><Text style={styles.cardTitle}>Risks</Text>{data.risks.map((d: string, i: number) => <Text key={i} style={styles.li}>• {d}</Text>)}</View>
      )}
      {!!(data?.opportunities || []).length && (
        <View style={styles.card}><Text style={styles.cardTitle}>Opportunities</Text>{data.opportunities.map((d: string, i: number) => <Text key={i} style={styles.li}>• {d}</Text>)}</View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa', padding: 16 },
  title: { color: '#1f2937', fontSize: 18, marginBottom: 8, fontWeight: '700' },
  row: { flexDirection: 'row', gap: 8, marginTop: 8, marginBottom: 8 },
  chip: { paddingVertical: 6, paddingHorizontal: 10, backgroundColor: '#e5e7eb', borderRadius: 16 },
  chipActive: { backgroundColor: '#3b82f6' },
  chipText: { color: '#1f2937', fontSize: 12 },
  button: { backgroundColor: '#06b6d4', padding: 10, borderRadius: 10, alignItems: 'center', marginVertical: 12 },
  buttonText: { color: '#ffffff', fontWeight: '700' },
  err: { color: '#ef4444', marginBottom: 8 },
  summary: { color: '#374151', marginBottom: 12, lineHeight: 20 },
  card: { backgroundColor: '#ffffff', padding: 12, borderRadius: 10, marginBottom: 12, shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 2, elevation: 1 },
  cardTitle: { color: '#1f2937', fontWeight: '700', marginBottom: 6 },
  li: { color: '#374151' },
});
