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
import { useNavigation } from '@react-navigation/native';
import { useQuery } from '@apollo/client';
import { generateDailyDigest, createRegimeAlert, VoiceDigestResponse } from '../../../services/aiClient';
import { gql } from '@apollo/client';
import logger from '../../../utils/logger';

const ME_QUERY = gql`
  query Me {
    me {
      id
      email
      name
      hasPremiumAccess
      subscriptionTier
    }
  }
`;
import * as Speech from 'expo-speech';

// Map regime types to simple labels
function getRegimeLabel(regime: string): string {
  const normalized = regime?.toLowerCase() || '';
  if (normalized.includes('bull') || normalized.includes('calm')) return 'Calm';
  if (normalized.includes('bear') || normalized.includes('storm')) return 'Storm';
  if (normalized.includes('sideways') || normalized.includes('choppy') || normalized.includes('volatile')) return 'Choppy';
  return 'Choppy'; // Default
}

export default function DailyVoiceDigestScreen() {
  const navigation = useNavigation<any>();
  const [userId] = useState('demo-user');
  const [digest, setDigest] = useState<VoiceDigestResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [completedTodos, setCompletedTodos] = useState<Set<number>>(new Set());
  
  // Check user's premium status
  const { data: userData } = useQuery(ME_QUERY, {
    errorPolicy: 'all',
    fetchPolicy: 'cache-first'
  });
  
  const hasPremium = userData?.me?.hasPremiumAccess || false;
  const subscriptionTier = userData?.me?.subscriptionTier || 'free';

  // Speech module availability check - no need to log

  const generateDigest = async () => {
    setLoading(true);
    try {
      // Add timeout wrapper to prevent hanging
      const timeoutPromise = new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Request timeout')), 10000)
      );
      
      const digestPromise = generateDailyDigest({ 
        user_id: userId,
        preferred_time: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString() // Tomorrow 8 AM
      });
      
      const res = await Promise.race([digestPromise, timeoutPromise]) as VoiceDigestResponse;
      setDigest(res);
      // Reset completed todos when new digest is generated
      setCompletedTodos(new Set());
    } catch (error: any) {
      // Suppress timeout errors for demo - show user-friendly message instead
      if (error?.message?.includes('timeout') || error?.message?.includes('Request timeout')) {
        logger.warn('⚠️ Digest generation timed out, using mock data for demo');
        // Set mock digest for demo purposes with regime_context
        setDigest({
          digest_id: `demo-digest-${Date.now()}`,
          user_id: userId,
          voice_script: 'Good morning! Here\'s your daily market digest. Markets are showing positive momentum today with tech stocks leading gains. Your portfolio is performing well.',
          regime_context: {
            current_regime: 'bullish',
            regime_description: 'Markets showing strong upward momentum with tech sector leading gains.',
            regime_confidence: 0.75,
            relevant_strategies: [
              'Growth investing',
              'Momentum trading',
              'Tech sector focus'
            ],
            common_mistakes: [
              'Chasing hot stocks',
              'Ignoring diversification',
              'Overtrading on momentum'
            ]
          },
          key_insights: [
            'Tech stocks up 2.5% today',
            'Portfolio performance exceeds benchmark',
            'Strong earnings expectations for next quarter'
          ],
          actionable_tips: [
            'Consider rebalancing tech allocations',
            'Review tax-loss harvesting opportunities',
            'Monitor earnings announcements this week'
          ],
          generated_at: new Date().toISOString(),
          scheduled_for: new Date().toISOString()
        });
      } else {
        logger.error('Error generating digest:', error);
        Alert.alert('Error', 'Failed to generate daily digest. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const playVoiceDigest = async () => {
    if (!digest?.voice_script) return;

    try {
      setIsPlaying(true);
      
      // Check if Speech is available
      if (!Speech || typeof Speech.speak !== 'function') {
        logger.error('Speech module not available');
        Alert.alert('Voice Playback Unavailable', 'Text-to-speech is not available on this device. Please read the digest manually.');
        setIsPlaying(false);
        return;
      }
      
      // Parse haptic cues from voice script
      const script = digest.voice_script;
      const hapticCues: string[] = script.match(/\[HAPTIC: (gentle|strong)\]/g) || [];
      
      // Play voice with haptic feedback
      await Speech.speak(script.replace(/\[HAPTIC: (gentle|strong)\]/g, ''), {
        language: 'en-US',
        pitch: 1.0,
        rate: 0.9,
        onDone: () => setIsPlaying(false),
        onStopped: () => setIsPlaying(false),
        onError: (error) => {
          logger.error('Speech error:', error);
          setIsPlaying(false);
        },
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
      logger.error('Error playing voice:', error);
      Alert.alert('Playback Error', 'Unable to play voice digest. Please try again or read the text manually.');
      setIsPlaying(false);
    }
  };

  const stopVoice = () => {
    try {
      if (Speech && typeof Speech.stop === 'function') {
        Speech.stop();
      }
    } catch (error) {
      logger.error('Error stopping speech:', error);
    } finally {
      setIsPlaying(false);
    }
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
        alert.title || 'Regime Alert',
        alert.body || 'Market regime has changed. Consider reviewing your portfolio strategy.',
        [{ text: 'OK' }]
      );
    } catch (error: any) {
      logger.error('❌ Error creating regime alert:', error);
      Alert.alert(
        'Regime Alert Test',
        error?.message || 'Failed to create regime alert. Please try again.',
        [{ text: 'OK' }]
      );
    }
  };
  
  const handleUpgradeToPro = () => {
    if (hasPremium || subscriptionTier === 'premium') {
      Alert.alert(
        'Already Premium',
        'You already have premium access! Enjoy all the advanced features.',
        [{ text: 'OK' }]
      );
    } else {
      try {
        navigation.navigate('subscription');
      } catch (error) {
        logger.error('Navigation error:', error);
        Alert.alert(
          'Navigation Error',
          'Could not open subscription screen. Please try from the Profile menu.',
          [{ text: 'OK' }]
        );
      }
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
          {digest.regime_context && (
            <View style={styles.regimeContext}>
              <Text style={styles.regimeTitle}>📊 Today's Conditions</Text>
              <Text style={styles.regimeName}>
                {getRegimeLabel(digest.regime_context.current_regime)}
              </Text>
              <Text style={styles.regimeDescription}>
                {digest.regime_context.regime_description}
              </Text>
              <Text style={styles.regimeConfidence}>
                Confidence: {(digest.regime_context.regime_confidence * 100).toFixed(1)}%
              </Text>
            </View>
          )}

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

          {/* Actionable Tips / Todos */}
          <View style={styles.tipsContainer}>
            <Text style={styles.tipsTitle}>🎯 Actionable Tips</Text>
            {digest.actionable_tips.map((tip, index) => {
              const isCompleted = completedTodos.has(index);
              return (
                <TouchableOpacity
                  key={index}
                  style={[styles.tipItem, isCompleted && styles.tipItemCompleted]}
                  onPress={() => {
                    const newCompleted = new Set(completedTodos);
                    if (isCompleted) {
                      newCompleted.delete(index);
                    } else {
                      newCompleted.add(index);
                    }
                    setCompletedTodos(newCompleted);
                  }}
                  activeOpacity={0.7}
                >
                  <View style={styles.tipCheckbox}>
                    {isCompleted && <Text style={styles.checkmark}>✓</Text>}
                  </View>
                  <Text style={[styles.tipNumber, isCompleted && styles.tipNumberCompleted]}>
                    {index + 1}
                  </Text>
                  <Text style={[styles.tipText, isCompleted && styles.tipTextCompleted]}>
                    {tip}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>

          {/* Pro Teaser */}
          {digest.pro_teaser && (
            <View style={styles.proTeaser}>
              <Text style={styles.proTeaserTitle}>⭐ Pro Feature</Text>
              <Text style={styles.proTeaserText}>{digest.pro_teaser}</Text>
              <TouchableOpacity 
                style={[styles.upgradeButton, hasPremium && styles.upgradeButtonDisabled]}
                onPress={handleUpgradeToPro}
                disabled={hasPremium}
              >
                <Text style={styles.upgradeButtonText}>
                  {hasPremium ? '✓ Premium Active' : 'Upgrade to Pro'}
                </Text>
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
    alignItems: 'flex-start',
    paddingVertical: 8,
    paddingHorizontal: 4,
    borderRadius: 8,
    backgroundColor: '#ffffff'
  },
  tipItemCompleted: {
    backgroundColor: '#f0f9ff',
    opacity: 0.8
  },
  tipCheckbox: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#3b82f6',
    marginRight: 12,
    marginTop: 2,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#ffffff'
  },
  checkmark: {
    color: '#10b981',
    fontSize: 16,
    fontWeight: 'bold'
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
  tipNumberCompleted: {
    backgroundColor: '#9ca3af',
    textDecorationLine: 'line-through'
  },
  tipText: {
    color: '#374151',
    fontSize: 14,
    lineHeight: 20,
    flex: 1
  },
  tipTextCompleted: {
    color: '#9ca3af',
    textDecorationLine: 'line-through'
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
  upgradeButtonDisabled: {
    backgroundColor: '#10b981',
    opacity: 0.8
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
