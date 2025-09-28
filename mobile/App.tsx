import React, { useEffect, useState } from 'react';
import { SafeAreaView, Text, TouchableOpacity, ActivityIndicator, Linking } from 'react-native';
import { API_HTTP, API_GRAPHQL, API_WS } from './src/config';

const API = process.env.EXPO_PUBLIC_API_URL || '';

// Debug logging (temporary)
console.log("🔧 App.tsx API Configuration:", { API_HTTP, API_GRAPHQL, API_WS, API });

type Check = { name: string; path: string; ok?: boolean; ms?: number; err?: string };

async function ping(url: string) {
  const t0 = Date.now();
  const res = await fetch(url, { method: 'GET' });
  const ms = Date.now() - t0;
  // consider 200-399 as OK for health
  if (res.status >= 200 && res.status < 400) return { ok: true, ms };
  return { ok: false, ms, err: `HTTP ${res.status}` };
}

export default function App() {
  const [checks, setChecks] = useState<Check[]>([
    { name: 'Root', path: '/' },
    { name: 'Signals', path: '/signals/' },
    { name: 'Prices (BTC,ETH)', path: '/prices/?symbols=BTC,ETH' },
  ]);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    if (!API) {
      setChecks(cs => cs.map(c => ({ ...c, ok: false, err: 'EXPO_PUBLIC_API_URL missing' })));
      return;
    }
    setLoading(true);
    try {
      const results = await Promise.all(
        checks.map(async (c) => {
          try {
            const r = await ping(API.replace(/\/$/, '') + c.path);
            return { ...c, ...r };
          } catch (e: any) {
            return { ...c, ok: false, err: e?.message || 'Network error' };
          }
        })
      );
      setChecks(results);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { run(); }, []);

  return (
    <SafeAreaView style={{ flex: 1, padding: 20, gap: 16 }}>
      <Text style={{ fontSize: 20, fontWeight: '700' }}>RichesReach • Backend Health</Text>
      <Text selectable>API: {API || 'not set'}</Text>

      {loading ? <ActivityIndicator /> : null}

      {checks.map((c) => (
        <TouchableOpacity
          key={c.name}
          onPress={() => Linking.openURL(API.replace(/\/$/, '') + c.path)}
          style={{
            borderWidth: 1,
            borderColor: c.ok ? '#22c55e' : '#ef4444',
            padding: 12, borderRadius: 10
          }}
        >
          <Text style={{ fontWeight: '600' }}>{c.name}</Text>
          <Text>{c.path}</Text>
          <Text>
            {c.ok ? `✅ OK in ${c.ms} ms` : `❌ ${c.err || 'Failed'}`}
          </Text>
        </TouchableOpacity>
      ))}

      <TouchableOpacity
        onPress={run}
        style={{ marginTop: 12, backgroundColor: '#111827', padding: 14, borderRadius: 10 }}
      >
        <Text style={{ color: 'white', textAlign: 'center', fontWeight: '700' }}>Re-run checks</Text>
      </TouchableOpacity>
    </SafeAreaView>
  );
}