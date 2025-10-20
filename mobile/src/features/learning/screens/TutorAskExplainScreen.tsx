import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, StyleSheet, ActivityIndicator } from 'react-native';
import { tutorAsk, tutorExplain, AskResponse, ExplainResponse } from '../../../services/aiClient';

export default function TutorAskExplainScreen() {
  const [userId] = useState('demo-user');
  const [mode, setMode] = useState<'ask'|'explain'>('ask');
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [output, setOutput] = useState<AskResponse | ExplainResponse | null>(null);

  const onSubmit = async () => {
    const q = input.trim();
    if (!q || loading) return;
    setError(null);
    setOutput(null);
    setLoading(true);
    try {
      if (mode === 'ask') {
        const res = await tutorAsk({ user_id: userId, question: q });
        setOutput(res);
      } else {
        const res = await tutorExplain({ user_id: userId, concept: q });
        setOutput(res);
      }
    } catch (e: any) {
      setError(e?.message || 'Request failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.screen}>
      <View style={styles.headerRow}>
        <TouchableOpacity onPress={() => setMode('ask')} style={[styles.chip, mode==='ask' && styles.chipActive]}><Text style={styles.chipText}>Ask</Text></TouchableOpacity>
        <TouchableOpacity onPress={() => setMode('explain')} style={[styles.chip, mode==='explain' && styles.chipActive]}><Text style={styles.chipText}>Explain</Text></TouchableOpacity>
      </View>

      <TextInput
        style={styles.input}
        placeholder={mode==='ask' ? 'Ask a question…' : 'Enter a concept…'}
        placeholderTextColor="#8b8b94"
        value={input}
        onChangeText={setInput}
        multiline
      />

      <TouchableOpacity onPress={onSubmit} style={[styles.button, !input.trim() || loading ? styles.buttonDisabled : null]} disabled={!input.trim() || loading}>
        {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Submit</Text>}
      </TouchableOpacity>

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <ScrollView style={styles.card}>
        {output ? (
          <>
            {'response' in output ? (
              <>
                <Text style={styles.label}>Answer</Text>
                <Text style={styles.mono}>{output.response}</Text>
                <View style={styles.metaRow}>
                  {output.model ? <Text style={styles.meta}>Model: {output.model}</Text> : null}
                  {typeof output.confidence_score === 'number' ? <Text style={styles.meta}>Confidence: {(output.confidence_score * 100).toFixed(0)}%</Text> : null}
                  {!output.model && <Text style={styles.meta}>AI Generated</Text>}
                </View>
              </>
            ) : (
              <>
                <Text style={styles.title}>{(output as ExplainResponse).concept}</Text>
                <Text style={styles.body}>{(output as ExplainResponse).explanation}</Text>
                {((output as ExplainResponse).examples || []).length ? (
                  <>
                    <Text style={styles.label}>Examples</Text>
                    {(output as ExplainResponse).examples!.map((ex, i) => <Text key={i} style={styles.body}>• {ex}</Text>)}
                  </>
                ) : null}
              </>
            )}
          </>
        ) : (
          <Text style={styles.placeholder}>Your result will appear here.</Text>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, padding: 16, backgroundColor: '#f8f9fa' },
  headerRow: { flexDirection: 'row', gap: 8, marginBottom: 12 },
  chip: { paddingVertical: 8, paddingHorizontal: 12, backgroundColor: '#e5e7eb', borderRadius: 20 },
  chipActive: { backgroundColor: '#3b82f6' },
  chipText: { color: '#1f2937' },
  input: { minHeight: 90, backgroundColor: '#ffffff', color: '#1f2937', padding: 12, borderRadius: 10, marginBottom: 12, borderWidth: 1, borderColor: '#d1d5db' },
  button: { backgroundColor: '#3b82f6', padding: 12, borderRadius: 10, alignItems: 'center' },
  buttonDisabled: { opacity: 0.5 },
  buttonText: { color: '#ffffff', fontWeight: '600' },
  card: { marginTop: 12, backgroundColor: '#ffffff', borderRadius: 12, padding: 12, shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 2, elevation: 1 },
  label: { color: '#6b7280', fontSize: 12, marginBottom: 4 },
  title: { color: '#1f2937', fontSize: 18, marginBottom: 6, fontWeight: '600' },
  body: { color: '#374151', marginBottom: 6 },
  mono: { color: '#374151', fontFamily: 'Menlo', fontSize: 13 },
  metaRow: { flexDirection: 'row', gap: 12, marginTop: 8 },
  meta: { color: '#6b7280', fontSize: 12 },
  placeholder: { color: '#9ca3af' },
  error: { color: '#ef4444', marginTop: 8 },
});
