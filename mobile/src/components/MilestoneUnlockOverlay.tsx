import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Modal, Animated, Easing, TouchableOpacity, Share } from 'react-native';
import * as Haptics from 'expo-haptics';

interface Props {
  visible: boolean;
  title: string;
  onClose: () => void;
}

export default function MilestoneUnlockOverlay({ visible, title, onClose }: Props) {
  const opacity = useRef(new Animated.Value(0)).current;
  const scale = useRef(new Animated.Value(0.9)).current;

  useEffect(() => {
    if (visible) {
      Animated.parallel([
        Animated.timing(opacity, { toValue: 1, duration: 260, easing: Easing.out(Easing.quad), useNativeDriver: true }),
        Animated.spring(scale, { toValue: 1, useNativeDriver: true }),
      ]).start();
      try { Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success); } catch {}
    } else {
      opacity.setValue(0);
      scale.setValue(0.9);
    }
  }, [visible]);

  return (
    <Modal visible={visible} transparent onRequestClose={onClose} animationType="fade">
      <Animated.View style={[styles.overlay, { opacity }] }>
        <Animated.View style={[styles.card, { transform: [{ scale }] }]}>
          <Text style={styles.header}>Milestone Unlocked</Text>
          <Text style={styles.title}>{title}</Text>
          <View style={styles.row}>
            <TouchableOpacity style={styles.primary} onPress={async () => {
              try { await Share.share({ message: `I just unlocked: ${title} 🎉` }); } catch {}
              onClose();
            }}>
              <Text style={styles.primaryText}>Share</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.secondary} onPress={onClose}>
              <Text style={styles.secondaryText}>Close</Text>
            </TouchableOpacity>
          </View>
        </Animated.View>
      </Animated.View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.4)', alignItems: 'center', justifyContent: 'center' },
  card: { width: '84%', backgroundColor: '#fff', borderRadius: 16, padding: 18, borderWidth: 1, borderColor: '#E5E5EA' },
  header: { fontSize: 14, fontWeight: '700', color: '#34C759' },
  title: { fontSize: 18, fontWeight: '700', color: '#1C1C1E', marginTop: 6, marginBottom: 14 },
  row: { flexDirection: 'row', gap: 10 },
  primary: { flex: 1, backgroundColor: '#34C759', borderRadius: 10, paddingVertical: 12, alignItems: 'center' },
  primaryText: { color: '#fff', fontWeight: '700' },
  secondary: { flex: 1, backgroundColor: '#F2F2F7', borderRadius: 10, paddingVertical: 12, alignItems: 'center' },
  secondaryText: { color: '#1C1C1E', fontWeight: '700' },
});


