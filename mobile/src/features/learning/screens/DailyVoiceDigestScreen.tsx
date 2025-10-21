import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  TouchableOpacity, 
  StyleSheet, 
  ScrollView, 
  ActivityIndicator, 
  Alert,
  Vibration
} from 'react-native';
import { generateDailyDigest, createRegimeAlert, VoiceDigestResponse } from '../../../services/aiClient';
import { Speech } from 'expo-speech';

export default function DailyVoiceDigestScreen() {
  const [userId] = useState('demo-user');
  const [digest, setDigest] = useState<VoiceDigestResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);

  const generateDigest = async () => {
    setLoading(true);
    try {
      const res = await generateDailyDigest({ 
        user_id: userId,
        preferred_time: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString() // Tomorrow 8 AM
      });
      setDigest(res);
    } catch (error) {
      console.error('Error generating digest:', error);
      Alert.alert('Error', 'Failed to generate daily digest. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const playVoiceDigest = async () => {
    if (!digest?.voice_script) return;

    try {
      setIsPlaying(true);
      
      // Parse haptic cues from voice script
      const script = digest.voice_script;
      const hapticCues = script.match(/\[HAPTIC: (gentle|strong)\]/g) || [];
      
      // Play voice with haptic feedback
      await Speech.speak(script.replace(/\[HAPTIC: (gentle|strong)\]/g, ''), {
        language: 'en-US',
        pitch: 1.0,
        rate: 0.9,
        onDone: () => setIsPlaying(false),
        onStopped: () => setIsPlaying(false),
        onError: () => setIsPlaying(false),
      });

      // Trigger haptic feedback at appropriate times
      hapticCues.forEach((cue, index) => {
        setTimeout(() => {
          if (cue.includes('gentle')) {
            Vibration.vibrate(100);
          } else if (cue.includes('strong')) {
            Vibration.vibrate(200);
          }
        }, index * 15000); // Every 15 seconds
      });

    } catch (error) {
      console.error('Error playing voice:', error);
      setIsPlaying(false);
    }
  };

  const stopVoice = () => {
    Speech.stop();
    setIsPlaying(false);
  };

  const testRegimeAlert = async () => {
    try {
      const alert = await createRegimeAlert({
        user_id: userId,
        regime_change: {
          old_regime: 'sideways_consolidation',
          new_regime: 'early_bull_market',
          confidence: 0.85
        },
        urgency: 'medium'
      });
      
      Alert.alert(
        alert.title,
        alert.body,
        [{ text: 'OK' }]
      );
    } catch (error) {
      console.error('Error creating regime alert:', error);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>🎙️ Daily Voice Digest</Text>
      <Text style={styles.subtitle}>
        Personalized 60-second market briefings that adapt to current conditions
      </Text>

      <TouchableOpacity onPress={generateDigest} style={styles.button} disabled={loading}>
        {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Generate Today's Digest</Text>}
      </TouchableOpacity>

      {digest && (
        <View style={styles.digestContainer}>
          {/* Regime Context */}
          <View style={styles.regimeContext}>
            <Text style={styles.regimeTitle}>📊 Current Market Regime</Text>
            <Text style={styles.regimeName}>
              {digest.regime_context.current_regime.replace('_', ' ').toUpperCase()}
            </Text>
            <Text style={styles.regimeDescription}>
              {digest.regime_context.regime_description}
            </Text>
            <Text style={styles.regimeConfidence}>
              Confidence: {(digest.regime_context.regime_confidence * 100).toFixed(1)}%
            </Text>
          </View>

          {/* Voice Player */}
          <View style={styles.voicePlayer}>
            <Text style={styles.voiceTitle}>🎙️ Voice Briefing</Text>
            <Text style={styles.voiceScript}>{digest.voice_script}</Text>
            
            <View style={styles.voiceControls}>
              {!isPlaying ? (
                <TouchableOpacity onPress={playVoiceDigest} style={styles.playButton}>
                  <Text style={styles.playButtonText}>▶️ Play Digest</Text>
                </TouchableOpacity>
              ) : (
                <TouchableOpacity onPress={stopVoice} style={styles.stopButton}>
                  <Text style={styles.stopButtonText}>⏹️ Stop</Text>
                </TouchableOpacity>
              )}
            </View>
          </View>

          {/* Key Insights */}
          <View style={styles.insightsContainer}>
            <Text style={styles.insightsTitle}>💡 Key Insights</Text>
            {digest.key_insights.map((insight, index) => (
              <View key={index} style={styles.insightItem}>
                <Text style={styles.insightBullet}>•</Text>
                <Text style={styles.insightText}>{insight}</Text>
              </View>
            ))}
          </View>

          {/* Actionable Tips */}
          <View style={styles.tipsContainer}>
            <Text style={styles.tipsTitle}>🎯 Actionable Tips</Text>
            {digest.actionable_tips.map((tip, index) => (
              <View key={index} style={styles.tipItem}>
                <Text style={styles.tipNumber}>{index + 1}</Text>
                <Text style={styles.tipText}>{tip}</Text>
              </View>
            ))}
          </View>

          {/* Pro Teaser */}
          {digest.pro_teaser && (
            <View style={styles.proTeaser}>
              <Text style={styles.proTeaserTitle}>⭐ Pro Feature</Text>
              <Text style={styles.proTeaserText}>{digest.pro_teaser}</Text>
              <TouchableOpacity style={styles.upgradeButton}>
                <Text style={styles.upgradeButtonText}>Upgrade to Pro</Text>
              </TouchableOpacity>
            </View>
          )}

          {/* Test Regime Alert */}
          <TouchableOpacity onPress={testRegimeAlert} style={styles.testButton}>
            <Text style={styles.testButtonText}>🚨 Test Regime Alert</Text>
          </TouchableOpacity>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { 
    flex: 1, 
    backgroundColor: '#f8f9fa', 
    padding: 16 
  },
  title: { 
    color: '#1f2937', 
    fontSize: 24, 
    fontWeight: '800', 
    marginBottom: 8,
    textAlign: 'center'
  },
  subtitle: { 
    color: '#6b7280', 
    fontSize: 16, 
    marginBottom: 24, 
    textAlign: 'center',
    lineHeight: 22
  },
  button: { 
    backgroundColor: '#3b82f6', 
    padding: 16, 
    borderRadius: 12, 
    alignItems: 'center', 
    marginBottom: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3
  },
  buttonText: { 
    color: '#ffffff', 
    fontWeight: '700',
    fontSize: 16
  },
  
  digestContainer: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4
  },
  
  // Regime Context
  regimeContext: {
    backgroundColor: '#f0f9ff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 20,
    borderLeftWidth: 4,
    borderLeftColor: '#3b82f6'
  },
  regimeTitle: { 
    color: '#1e40af', 
    fontSize: 16, 
    fontWeight: '700', 
    marginBottom: 8 
  },
  regimeName: { 
    color: '#1d4ed8', 
    fontSize: 20, 
    fontWeight: '800', 
    marginBottom: 4 
  },
  regimeDescription: { 
    color: '#374151', 
    fontSize: 14, 
    marginBottom: 8,
    lineHeight: 20
  },
  regimeConfidence: { 
    color: '#059669', 
    fontSize: 12, 
    fontWeight: '600'
  },
  
  // Voice Player
  voicePlayer: {
    backgroundColor: '#fef3c7',
    padding: 16,
    borderRadius: 12,
    marginBottom: 20,
    borderLeftWidth: 4,
    borderLeftColor: '#f59e0b'
  },
  voiceTitle: {
    color: '#92400e',
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 12
  },
  voiceScript: {
    color: '#374151',
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 16,
    fontStyle: 'italic'
  },
  voiceControls: {
    alignItems: 'center'
  },
  playButton: {
    backgroundColor: '#10b981',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8
  },
  playButtonText: {
    color: '#ffffff',
    fontWeight: '600',
    fontSize: 16
  },
  stopButton: {
    backgroundColor: '#ef4444',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8
  },
  stopButtonText: {
    color: '#ffffff',
    fontWeight: '600',
    fontSize: 16
  },
  
  // Insights
  insightsContainer: {
    marginBottom: 20
  },
  insightsTitle: {
    color: '#1f2937',
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 12
  },
  insightItem: {
    flexDirection: 'row',
    marginBottom: 8,
    alignItems: 'flex-start'
  },
  insightBullet: {
    color: '#3b82f6',
    fontSize: 16,
    fontWeight: '700',
    marginRight: 8,
    marginTop: 2
  },
  insightText: {
    color: '#374151',
    fontSize: 14,
    lineHeight: 20,
    flex: 1
  },
  
  // Tips
  tipsContainer: {
    marginBottom: 20
  },
  tipsTitle: {
    color: '#1f2937',
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 12
  },
  tipItem: {
    flexDirection: 'row',
    marginBottom: 12,
    alignItems: 'flex-start'
  },
  tipNumber: {
    backgroundColor: '#3b82f6',
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '700',
    width: 24,
    height: 24,
    borderRadius: 12,
    textAlign: 'center',
    lineHeight: 24,
    marginRight: 12,
    marginTop: 2
  },
  tipText: {
    color: '#374151',
    fontSize: 14,
    lineHeight: 20,
    flex: 1
  },
  
  // Pro Teaser
  proTeaser: {
    backgroundColor: '#fef2f2',
    padding: 16,
    borderRadius: 12,
    marginBottom: 20,
    borderLeftWidth: 4,
    borderLeftColor: '#ef4444'
  },
  proTeaserTitle: {
    color: '#dc2626',
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 8
  },
  proTeaserText: {
    color: '#374151',
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 12
  },
  upgradeButton: {
    backgroundColor: '#ef4444',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
    alignSelf: 'flex-start'
  },
  upgradeButtonText: {
    color: '#ffffff',
    fontWeight: '600',
    fontSize: 14
  },
  
  // Test Button
  testButton: {
    backgroundColor: '#f59e0b',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center'
  },
  testButtonText: {
    color: '#ffffff',
    fontWeight: '600',
    fontSize: 14
  }
});
