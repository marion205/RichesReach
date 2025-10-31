import React, { useEffect, useRef, useState } from 'react';
import { View, Text, StyleSheet, Animated, Easing, TouchableOpacity, Share } from 'react-native';
import * as Haptics from 'expo-haptics';
import MaterialCommunityIcons from 'react-native-vector-icons/MaterialCommunityIcons';

export interface Milestone {
  id: string;
  title: string;
  subtitle?: string;
  date?: string;
}

interface MilestonesTimelineProps {
  milestones: Milestone[];
  onCelebrate?: (title: string) => void;
}

export default function MilestonesTimeline({ milestones, onCelebrate }: MilestonesTimelineProps) {
  if (!milestones || milestones.length === 0) return null;

  // Pulse animation for the current milestone icon
  const pulse = useRef(new Animated.Value(0)).current;
  const [LottieView, setLottieView] = useState<any>(null);
  const [localAnim, setLocalAnim] = useState<any>(null);
  useEffect(() => {
    // Attempt to load lottie-react-native if available (Expo friendly)
    let mounted = true;
    (async () => {
      try {
        const mod = await import('lottie-react-native');
        if (mounted) setLottieView(() => mod.default || (mod as any));
      } catch (e) {
        // Lottie not installed; gracefully fall back to vector animation
      }
      try {
        const json = require('../../assets/lottie/seed_to_tree.json');
        if (mounted) setLocalAnim(json);
      } catch {}
    })();
    return () => { mounted = false; };
  }, []);
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 1, duration: 900, easing: Easing.out(Easing.quad), useNativeDriver: true }),
        Animated.timing(pulse, { toValue: 0, duration: 900, easing: Easing.in(Easing.quad), useNativeDriver: true }),
      ])
    ).start();
    // light haptic to reinforce milestone presence
    try { Haptics.selectionAsync(); } catch {}
  }, [pulse]);

  const scale = pulse.interpolate({ inputRange: [0, 1], outputRange: [0.92, 1.08] });
  const glowOpacity = pulse.interpolate({ inputRange: [0, 1], outputRange: [0.15, 0.35] });

  return (
    <View style={styles.container}>
      <Text style={styles.header}>Milestones</Text>
      {milestones.map((m, i) => {
        const isCurrent = i === milestones.length - 1;
        const rowOpacity = useRef(new Animated.Value(0)).current;
        const rowTranslate = useRef(new Animated.Value(8)).current;
        useEffect(() => {
          const delay = 120 * i;
          Animated.parallel([
            Animated.timing(rowOpacity, { toValue: 1, duration: 380, delay, useNativeDriver: true }),
            Animated.timing(rowTranslate, { toValue: 0, duration: 380, delay, easing: Easing.out(Easing.cubic), useNativeDriver: true }),
          ]).start();
        }, [rowOpacity, rowTranslate]);

        return (
          <Animated.View key={m.id} style={[styles.row, { opacity: rowOpacity, transform: [{ translateY: rowTranslate }] }] }>
            <View style={styles.iconCol}>
              <View style={styles.iconStack}>
                {isCurrent && (
                  <Animated.View style={[styles.glow, { opacity: glowOpacity, transform: [{ scale }] }]} />
                )}

                {isCurrent && LottieView && localAnim ? (
                  <View style={styles.lottieWrap}>
                    <LottieView
                      autoPlay
                      loop
                      style={{ width: 32, height: 32 }}
                      source={localAnim}
                    />
                  </View>
                ) : (
                  <Animated.View style={isCurrent ? { transform: [{ scale }] } : undefined}>
                    <MaterialCommunityIcons name={isCurrent ? 'tree' : 'sprout'} size={20} color={isCurrent ? '#34C759' : '#8E8E93'} />
                  </Animated.View>
                )}
              </View>
              {i < milestones.length - 1 && <View style={styles.connector} />}
            </View>
            <View style={styles.textCol}>
              <Text style={styles.title}>{m.title}</Text>
              {!!m.subtitle && <Text style={styles.subtitle}>{m.subtitle}</Text>}
              {!!m.date && <Text style={styles.meta}>{m.date}</Text>}
              {isCurrent && (
                <View style={styles.actions}>
                  <TouchableOpacity
                    onPress={async () => {
                      try {
                        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
                        await Share.share({ message: `Milestone achieved: ${m.title}${m.date ? ` on ${m.date}` : ''}` });
                      } catch {}
                    }}
                    style={styles.shareButton}
                  >
                    <Text style={styles.shareText}>Share</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    onPress={async () => {
                      try { await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy); } catch {}
                      onCelebrate?.(m.title);
                    }}
                    style={[styles.shareButton, { marginLeft: 8 }]}
                  >
                    <Text style={styles.shareText}>Celebrate</Text>
                  </TouchableOpacity>
                </View>
              )}
            </View>
          </Animated.View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { backgroundColor: '#FFFFFF', borderRadius: 12, padding: 16, marginHorizontal: 16, marginBottom: 16, borderWidth: 1, borderColor: '#E5E5EA' },
  header: { fontSize: 18, fontWeight: '700', color: '#1C1C1E', marginBottom: 8 },
  row: { flexDirection: 'row', marginBottom: 12 },
  iconCol: { width: 28, alignItems: 'center' },
  connector: { width: 2, backgroundColor: '#E5E5EA', flex: 1, marginTop: 4 },
  textCol: { flex: 1, paddingLeft: 8 },
  title: { fontSize: 14, fontWeight: '600', color: '#1C1C1E' },
  subtitle: { fontSize: 12, color: '#666', marginTop: 2 },
  meta: { fontSize: 11, color: '#8E8E93', marginTop: 2 },
  iconStack: { width: 24, height: 24, alignItems: 'center', justifyContent: 'center' },
  glow: { position: 'absolute', width: 26, height: 26, borderRadius: 13, backgroundColor: '#34C759' },
  lottieWrap: { width: 32, height: 32, alignItems: 'center', justifyContent: 'center' },
  actions: { marginTop: 6 },
  shareButton: { backgroundColor: '#F0F8FF', borderRadius: 8, paddingHorizontal: 10, paddingVertical: 6, alignSelf: 'flex-start', borderWidth: 1, borderColor: '#E3F2FD' },
  shareText: { color: '#007AFF', fontWeight: '700', fontSize: 12 },
});


