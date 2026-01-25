/**
 * Breath Check Modal
 * Guided breathing exercise for mindful trading decisions
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  Animated,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/Feather';
import { LinearGradient } from 'expo-linear-gradient';

interface BreathCheckModalProps {
  visible: boolean;
  onClose: () => void;
  onComplete: (suggestion?: { type: 'roundup' | 'dca'; amount: number; instrument: string }) => void;
}

const { width } = Dimensions.get('window');
const BREATH_CYCLE_DURATION = 4000; // 4 seconds per cycle (inhale + exhale)
const TOTAL_CYCLES = 4; // 4 cycles = ~16 seconds

export default function BreathCheckModal({ visible, onClose, onComplete }: BreathCheckModalProps) {
  const [currentCycle, setCurrentCycle] = useState(0);
  const [phase, setPhase] = useState<'inhale' | 'hold' | 'exhale' | 'pause'>('inhale');
  const [timeRemaining, setTimeRemaining] = useState(BREATH_CYCLE_DURATION);
  const scaleAnim = useRef(new Animated.Value(0.8)).current;
  const opacityAnim = useRef(new Animated.Value(0.5)).current;
  const completeTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (completeTimeoutRef.current) {
        clearTimeout(completeTimeoutRef.current);
        completeTimeoutRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!visible) {
      // Reset when modal closes
      setCurrentCycle(0);
      setPhase('inhale');
      setTimeRemaining(BREATH_CYCLE_DURATION);
      scaleAnim.setValue(0.8);
      opacityAnim.setValue(0.5);
      return;
    }

    let interval: NodeJS.Timeout;
    let startTime = Date.now();

    const animateBreathing = () => {
      const elapsed = Date.now() - startTime;
      const cycleProgress = (elapsed % BREATH_CYCLE_DURATION) / BREATH_CYCLE_DURATION;

      // Determine phase
      if (cycleProgress < 0.25) {
        setPhase('inhale');
        // Animate circle growing
        Animated.parallel([
          Animated.timing(scaleAnim, {
            toValue: 1.2,
            duration: 1000,
            useNativeDriver: true,
          }),
          Animated.timing(opacityAnim, {
            toValue: 1,
            duration: 1000,
            useNativeDriver: true,
          }),
        ]).start();
      } else if (cycleProgress < 0.5) {
        setPhase('hold');
      } else if (cycleProgress < 0.75) {
        setPhase('exhale');
        // Animate circle shrinking
        Animated.parallel([
          Animated.timing(scaleAnim, {
            toValue: 0.8,
            duration: 1000,
            useNativeDriver: true,
          }),
          Animated.timing(opacityAnim, {
            toValue: 0.5,
            duration: 1000,
            useNativeDriver: true,
          }),
        ]).start();
      } else {
        setPhase('pause');
      }

      // Update cycle count
      const cycleNumber = Math.floor(elapsed / BREATH_CYCLE_DURATION);
      setCurrentCycle(Math.min(cycleNumber, TOTAL_CYCLES - 1));
      setTimeRemaining(Math.max(0, BREATH_CYCLE_DURATION - (elapsed % BREATH_CYCLE_DURATION)));

      // Check if all cycles complete
      if (cycleNumber >= TOTAL_CYCLES) {
        // Complete the exercise
        if (completeTimeoutRef.current) {
          clearTimeout(completeTimeoutRef.current);
        }
        completeTimeoutRef.current = setTimeout(() => {
          const suggestion = { type: 'dca' as const, amount: 25, instrument: 'VTI' };
          onComplete(suggestion);
          completeTimeoutRef.current = null;
        }, 500);
        return;
      }
    };

    interval = setInterval(animateBreathing, 100);
    animateBreathing();

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [visible, scaleAnim, opacityAnim, onComplete]);

  const getPhaseText = () => {
    switch (phase) {
      case 'inhale':
        return 'Breathe In';
      case 'hold':
        return 'Hold';
      case 'exhale':
        return 'Breathe Out';
      case 'pause':
        return 'Pause';
      default:
        return 'Ready';
    }
  };

  const getPhaseInstruction = () => {
    switch (phase) {
      case 'inhale':
        return 'Fill your lungs slowly';
      case 'hold':
        return 'Feel the stillness';
      case 'exhale':
        return 'Release all tension';
      case 'pause':
        return 'Notice the quiet';
      default:
        return 'Take your time';
    }
  };

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <SafeAreaView style={styles.container}>
        <LinearGradient
          colors={['#F0FDF4', '#ECFDF5', '#D1FAE5']}
          style={styles.gradient}
        >
          {/* Header */}
          <View style={styles.header}>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Icon name="x" size={24} color="#1F2937" />
            </TouchableOpacity>
          </View>

          {/* Content */}
          <View style={styles.content}>
            <Text style={styles.title}>Breath Check</Text>
            <Text style={styles.subtitle}>
              {currentCycle + 1} of {TOTAL_CYCLES} cycles
            </Text>

            {/* Breathing Circle */}
            <View style={styles.circleContainer}>
              <Animated.View
                style={[
                  styles.breathingCircle,
                  {
                    transform: [{ scale: scaleAnim }],
                    opacity: opacityAnim,
                  },
                ]}
              >
                <View style={styles.innerCircle}>
                  <Icon
                    name="wind"
                    size={60}
                    color={phase === 'inhale' ? '#10B981' : phase === 'exhale' ? '#059669' : '#6B7280'}
                  />
                </View>
              </Animated.View>
            </View>

            {/* Phase Text */}
            <Text style={styles.phaseText}>{getPhaseText()}</Text>
            <Text style={styles.instructionText}>{getPhaseInstruction()}</Text>

            {/* Progress Indicator */}
            <View style={styles.progressContainer}>
              {Array.from({ length: TOTAL_CYCLES }).map((_, index) => (
                <View
                  key={index}
                  style={[
                    styles.progressDot,
                    index <= currentCycle && styles.progressDotActive,
                  ]}
                />
              ))}
            </View>

            {/* Skip Button */}
            <TouchableOpacity
              style={styles.skipButton}
              onPress={() => {
                const suggestion = { type: 'dca' as const, amount: 25, instrument: 'VTI' };
                onComplete(suggestion);
              }}
            >
              <Text style={styles.skipButtonText}>Skip to Next Move</Text>
            </TouchableOpacity>
          </View>
        </LinearGradient>
      </SafeAreaView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gradient: {
    flex: 1,
  },
  header: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 8,
    flexDirection: 'row',
    justifyContent: 'flex-end',
  },
  closeButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.8)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  content: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
  },
  title: {
    fontSize: 32,
    fontWeight: '700',
    color: '#1F2937',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#6B7280',
    marginBottom: 48,
  },
  circleContainer: {
    width: width * 0.7,
    height: width * 0.7,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 48,
  },
  breathingCircle: {
    width: width * 0.6,
    height: width * 0.6,
    borderRadius: width * 0.3,
    backgroundColor: '#10B981',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#10B981',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 8,
  },
  innerCircle: {
    width: width * 0.5,
    height: width * 0.5,
    borderRadius: width * 0.25,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  phaseText: {
    fontSize: 24,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 8,
  },
  instructionText: {
    fontSize: 16,
    color: '#6B7280',
    marginBottom: 32,
    textAlign: 'center',
  },
  progressContainer: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 32,
  },
  progressDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#D1D5DB',
  },
  progressDotActive: {
    backgroundColor: '#10B981',
  },
  skipButton: {
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
  },
  skipButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6B7280',
  },
});

