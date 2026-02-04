import React, { useState } from 'react';
import { View, Text, StyleSheet, Modal, TouchableOpacity } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

interface Props {
  visible: boolean;
  onClose: () => void;
  onResult?: (text: string) => void;
}

export default function VoiceCaptureSheet({ visible, onClose, onResult }: Props) {
  const [transcript, setTranscript] = useState('');
  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View style={styles.card}>
          <View style={styles.header}>
            <Text style={styles.title}>Voice Capture</Text>
            <TouchableOpacity onPress={onClose}><Icon name="x" size={20} color="#8E8E93" /></TouchableOpacity>
          </View>
          <Text style={styles.subtitle}>Type or paste your request. ASR coming soon.</Text>
          <View style={styles.box}>
            <Text style={styles.text}>{transcript || '“set calm investing goal”'}</Text>
          </View>
          <View style={styles.row}>
            <TouchableOpacity style={styles.btn} onPress={() => setTranscript('set calm investing goal')}>
              <Text style={styles.btnText}>Sample</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.btn, styles.primary]} onPress={() => { onResult?.(transcript || 'set calm investing goal'); onClose(); }}>
              <Text style={[styles.btnText, { color: '#fff' }]}>Use</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.35)', justifyContent: 'flex-end' },
  card: { backgroundColor: '#fff', borderTopLeftRadius: 16, borderTopRightRadius: 16, padding: 16 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  title: { fontSize: 16, fontWeight: '700', color: '#1C1C1E' },
  subtitle: { fontSize: 12, color: '#6B7280', marginTop: 6, marginBottom: 10 },
  box: { backgroundColor: '#F8F9FA', borderRadius: 12, padding: 14, borderWidth: 1, borderColor: '#E5E5EA' },
  text: { color: '#1C1C1E' },
  row: { flexDirection: 'row', gap: 10, marginTop: 12 },
  btn: { flex: 1, backgroundColor: '#F2F2F7', borderRadius: 10, paddingVertical: 12, alignItems: 'center' },
  primary: { backgroundColor: '#0EA5E9' },
  btnText: { color: '#1C1C1E', fontWeight: '700' },
});


