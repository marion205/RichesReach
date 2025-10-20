import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, FlatList, ActivityIndicator } from 'react-native';
import { assistantQuery } from '../../../services/aiClient';

interface Message { id: string; role: 'user'|'assistant'; text: string }

export default function AssistantChatScreen() {
  const [userId] = useState('demo-user');
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);

  const onSend = async () => {
    const text = input.trim();
    if (!text || sending) return;
    const id = String(Date.now());
    setMessages(prev => [...prev, { id, role: 'user', text }]);
    setInput('');
    setSending(true);
    try {
      const res = await assistantQuery({ user_id: userId, prompt: text });
      const answer = typeof res?.answer === 'string'
        ? res.answer
        : typeof res?.response === 'string'
          ? res.response
          : JSON.stringify(res);
      setMessages(prev => [...prev, { id: id + '-a', role: 'assistant', text: answer }]);
    } catch (e: any) {
      setMessages(prev => [...prev, { id: id + '-e', role: 'assistant', text: e.message || 'Request failed' }]);
    } finally {
      setSending(false);
    }
  };

  return (
    <View style={styles.container}>
      <FlatList
        data={messages}
        keyExtractor={(m) => m.id}
        renderItem={({ item }) => (
          <View style={[styles.bubble, item.role==='user'? styles.userBubble : styles.assistantBubble]}>
            <Text style={styles.text}>{item.text}</Text>
          </View>
        )}
        contentContainerStyle={{ padding: 16 }}
      />
      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={setInput}
          placeholder="Ask anything…"
          placeholderTextColor="#8b8b94"
          multiline
        />
        <TouchableOpacity onPress={onSend} style={[styles.sendBtn, (!input.trim() || sending) && { opacity: 0.5 }]} disabled={!input.trim() || sending}>
          {sending ? <ActivityIndicator color="#fff" /> : <Text style={styles.sendText}>Send</Text>}
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa' },
  bubble: { marginVertical: 6, padding: 10, borderRadius: 12, maxWidth: '85%' },
  userBubble: { alignSelf: 'flex-end', backgroundColor: '#3b82f6' },
  assistantBubble: { alignSelf: 'flex-start', backgroundColor: '#ffffff', shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 2, elevation: 1 },
  text: { color: '#1f2937' },
  inputRow: { flexDirection: 'row', padding: 12, borderTopWidth: 1, borderTopColor: '#e5e7eb', backgroundColor: '#ffffff' },
  input: { flex: 1, backgroundColor: '#f3f4f6', color: '#1f2937', padding: 10, borderRadius: 10, marginRight: 8, maxHeight: 120, borderWidth: 1, borderColor: '#d1d5db' },
  sendBtn: { backgroundColor: '#22c55e', paddingHorizontal: 14, justifyContent: 'center', borderRadius: 10, minWidth: 72, alignItems: 'center' },
  sendText: { color: '#ffffff', fontWeight: '700' },
});
